"""Folha de poses: três conceitos de combate da preguiça (guarda, golpe principal, momento da habilidade).

Retorno sobre a r09: os golpes e a guarda de lutador "não combinam com a criatura". Antes de animar de novo,
quadros parados de três ideias para o usuário escolher: 1) a preguiça que finge dormir (guarda largada de
olhos meio fechados, garras como gancho, pendurada no chefe como num galho); 2) fera de quatro (carcaju);
3) ameaça de tamanduá (tripé com braços abertos). O bloco cinza faz o papel do chefe.

Uso: uv run python scripts/fera-animacao/conceitos_combate.py [só-esta-pose] [arquivo.png]
"""
import json
import math
import sys
import uuid

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONTE = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 16)
FONTE_T = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 17)

sys.path.insert(0, "scripts/fera-animacao")
from clips import LADOS, Locomocao  # noqa: E402
from combate import Combate  # noqa: E402
from palpebras import DESLOCA  # noqa: E402
from pose import Mola, Rig, eixo_angulo, matriz, rot_min, rx, ry  # noqa: E402

from criaturas import bbmodelo, render  # noqa: E402

S = "modelos/fera-fera-agil-das-sombras/malha-v1/animacoes-v1/conceitos-combate/"
m = bbmodelo.ler("modelos/fera-fera-agil-das-sombras/malha-v1/animacoes-v1/rig-v4/base-rig-v4.bbmodel")
rig = Rig(m)
loc = Locomocao(rig)
cmb = Combate(loc)
CHAO = loc.chao


# ---------- pedaços ----------

def corpo(pose, empina=0.0, torce=0.0, inclina=0.0, d=(0.0, 0.0, 0.0)):
    R = matriz([empina, torce, inclina])
    H = cmb.quadril + np.asarray(d, float)
    pose["body"] = {"matriz": R, "posicao": H - cmb.P - R @ (cmb.quadril - cmb.P)}


def olhos(pose, v):
    cima, baixo = (DESLOCA if v >= 0.5 else 0.0), (DESLOCA if v >= 1.0 else 0.0)
    for lado, s in (("right", 1.0), ("left", -1.0)):
        pose[f"eyelid_{lado}"] = {"posicao": np.array([s * cima, 0.0, 0.0])}
        pose[f"eyelid_{lado}_lower"] = {"posicao": np.array([s * baixo, 0.0, 0.0])}


def ombro(pose, lado):
    W = rig.mats(pose)["torso"]
    return W[:3, :3] @ rig.piv(f"arm_{lado}") + W[:3, 3]


def braco_mundo(pose, lado, s, punho, garra_dir, giro=0.0, polo=None, esc=None):
    cmb.braco(pose, lado, s, np.asarray(punho, float) - ombro(pose, lado), garra_dir, giro, polo, esc)


def braco_rel(pose, lado, s, rel, garra_dir, giro=0.0, polo=None, esc=None):
    cmb.braco(pose, lado, s, np.asarray(rel, float), garra_dir, giro, polo, esc)


def mao_no_chao(pose, lado, s, xz, abertas=True, garra_dir=(0.0, -0.12, -1.0), giro=0.0, polo=None):
    """Mão apoiada: abertas = garras espalmadas no chão; senão nos nós das mãos (garras dobradas)."""
    y = loc.chao + (2.5 if abertas else loc.alt_punho)
    ossos = (f"hand_{lado}",) + tuple(f"claw_{lado}_{n}" for n in (1, 2, 3))
    for _ in range(6):
        alvo = np.array([xz[0], y, xz[1]])
        if abertas:
            braco_mundo(pose, lado, s, alvo, garra_dir, giro, polo)
            loc.garras(pose, 0.0, flex=0.05, lados=(lado,))
        else:
            loc.braco(pose, lado, s, alvo, 0.0)
            loc.garras(pose, 1.0, lados=(lado,))
        menor = cmb._menor_y(pose, ossos)
        if abs(menor - (loc.chao + 0.05)) < 1e-3:
            break
        y += (loc.chao + 0.05) - menor


def mao_pendurada(pose, lado, s, xz, garra_dir, flex=0.3):
    """Mão pendurada com a ponta das garras encostando no chão (arrastando)."""
    y = loc.chao + 9.0
    ossos = (f"hand_{lado}",) + tuple(f"claw_{lado}_{n}" for n in (1, 2, 3))
    for _ in range(6):
        braco_mundo(pose, lado, s, np.array([xz[0], y, xz[1]]), garra_dir)
        loc.garras(pose, 0.0, flex=flex, lados=(lado,))
        menor = cmb._menor_y(pose, ossos)
        if abs(menor - (loc.chao + 0.05)) < 1e-3:
            break
        y += (loc.chao + 0.05) - menor


def pernas_plantadas(pose, abre=1.1, passo=(0.0, 0.0), ponta=(0.0, 0.0)):
    for (lado, s), dz, pt in zip(LADOS, passo, ponta):
        b = rig.piv(f"foot_{lado}")
        cmb.pe(pose, lado, s, np.array([b[0] * abre, loc.chao + loc.alt_tornozelo, b[2] + dz]), pt, (0.25, 0.0, -1.0))


def perna_mundo(pose, lado, s, alvo, pe_pitch=0.0, polo=(0.3, 0.0, -1.0)):
    loc.perna(pose, lado, s, np.asarray(alvo, float), pe_pitch, charneira=True, polo=np.array([polo[0] * s, polo[1], polo[2]]))


def cauda_local(pose, gomos, chao=True):
    for g, (pitch, yaw) in zip(cmb.gomos, gomos):
        pose[g] = {"matriz": ry(yaw) @ rx(pitch)}
    if chao:
        loc.cauda_acima_do_chao(pose, 0.3)


def fita(pose, base=(10.0, 8.0, 6.0, 5.0, 4.0), yaw=0.0):
    loc.corrente(pose, [f"scarf_{k}" for k in range(1, 6)], [[b, yaw * (0.6 + 0.2 * k), 0.0] for k, b in enumerate(base)])


def caixa(nome, de, ate):
    return bbmodelo.Cubo(nome, str(uuid.uuid4()), "root", np.array(de, float), np.array(ate, float),
                         (np.array(de, float) + np.array(ate, float)) / 2, np.zeros(3), 0.0, {})


# ---------- conceito 1: a preguiça que finge dormir ----------

def c1_guarda():
    pose = {k: dict(v) for k, v in loc.pose_idle(0.0, 4.0, {"tronco": Mola(1.6, 0.3, 1)}, 1 / 30).items()}
    corpo(pose, empina=-6.0, inclina=4.0, d=(0.0, -2.0, 0.8))
    pose["waist"], pose["torso"] = {"rotacao": [0.0, 0.0, 0.0]}, {"rotacao": [0.0, 0.0, 0.0]}
    pernas_plantadas(pose, abre=1.1)
    mao_pendurada(pose, "left", -1.0, (-12.5, -24.0), cmb.d_garras["left"] + np.array([0.0, 0.0, -0.3]), 0.3)
    mao_pendurada(pose, "right", 1.0, (11.0, -20.5), cmb.d_garras["right"], 0.35)
    cauda_local(pose, [(4.0, 14.0), (2.0, 20.0), (0.0, 24.0), (-4.0, 24.0), (-8.0, 20.0)])
    loc.cabeca_estavel(pose, pitch=-16.0, yaw=-22.0, roll=14.0, rigidez=0.7)
    olhos(pose, 0.5)
    fita(pose, (-4.0, -4.0, -4.0, -3.0, -2.0))
    return pose, (28, 14), []


def c1_golpe():
    pose = {}
    corpo(pose, empina=-14.0, torce=10.0, inclina=-6.0, d=(0.0, -2.2, -3.0))
    pernas_plantadas(pose, abre=1.1, passo=(0.0, 2.0))
    mao_no_chao(pose, "left", -1.0, (-11.0, -27.0), abertas=False)
    braco_rel(pose, "right", 1.0, (-2.5, 3.5, -11.0), (-0.15, 0.85, -0.5), 0.0, (0.7, -0.4, 0.6))
    loc.garras(pose, 0.0, flex=0.85, lados=("right",))
    cauda_local(pose, [(-14.0, -6.0), (-4.0, -4.0), (0.0, -3.0), (2.0, 0.0), (4.0, 0.0)])
    loc.cabeca_estavel(pose, pitch=-4.0, yaw=-8.0, roll=0.0, rigidez=0.9)
    olhos(pose, 0.0)
    fita(pose, (20.0, 16.0, 12.0, 9.0, 7.0), yaw=-8.0)
    return pose, (35, 12), []


def c1_habilidade():
    chefe = caixa("chefe", (-14.0, 0.0, -62.0), (14.0, 60.0, -26.0))
    pose = {}
    corpo(pose, empina=84.0, d=np.array([0.0, 34.0, -19.5]) - cmb.quadril)
    braco_mundo(pose, "right", 1.0, (10.0, 61.5, -29.0), (0.0, -0.75, -0.65), 0.0, (0.9, 0.0, 0.4))
    braco_mundo(pose, "left", -1.0, (-10.0, 60.5, -29.0), (0.0, -0.85, -0.5), 0.0, (-0.9, 0.0, 0.4))
    loc.garras(pose, 0.0, flex=0.4, lados=("right",))
    loc.garras(pose, 0.0, flex=0.9, lados=("left",))
    for lado, s in LADOS:
        perna_mundo(pose, lado, s, (s * 9.0, 21.0, -27.5), 90.0, (0.8, 0.0, 0.6))
    cauda_local(pose, [(12.0, 10.0), (10.0, 14.0), (8.0, 16.0), (6.0, 16.0), (4.0, 14.0)], chao=False)
    loc.cabeca_estavel(pose, pitch=40.0, yaw=35.0, roll=0.0, rigidez=0.95)
    olhos(pose, 0.0)
    fita(pose, (-10.0, -8.0, -6.0, -4.0, -2.0))
    return pose, (150, 10), [chefe]


# ---------- conceito 2: fera de quatro ----------

def c2_guarda():
    pose = {}
    corpo(pose, empina=-8.0, d=(0.0, -2.0, 0.5))
    pernas_plantadas(pose, abre=1.15)
    for lado, s in LADOS:
        mao_no_chao(pose, lado, s, (s * 12.0, -22.0), abertas=True, garra_dir=(s * 0.12, -0.15, -1.0), giro=0.0)
    cauda_local(pose, [(-12.0, 0.0), (-6.0, 0.0), (0.0, 0.0), (4.0, 0.0), (6.0, 0.0)])
    loc.cabeca_estavel(pose, pitch=-6.0, yaw=0.0, roll=0.0, rigidez=0.9)
    olhos(pose, 0.0)
    fita(pose)
    return pose, (35, 12), []


def c2_golpe():
    pose = {}
    corpo(pose, empina=-2.0, d=(0.0, 3.0, -7.0))
    for lado, s in LADOS:
        braco_rel(pose, lado, s, (s * 1.5, -3.0, -15.0), (s * 0.15, -0.35, -0.92), 0.0)
        b = rig.piv(f"foot_{lado}")
        perna_mundo(pose, lado, s, b + np.array([0.0, 3.0 + 3.0, 9.0 - 7.0]), -60.0)
    loc.garras(pose, 0.0, flex=0.1)
    cauda_local(pose, [(-6.0, 0.0), (-2.0, 0.0), (0.0, 0.0), (2.0, 0.0), (2.0, 0.0)], chao=False)
    loc.cabeca_estavel(pose, pitch=-2.0, yaw=0.0, roll=0.0, rigidez=0.9)
    olhos(pose, 0.0)
    fita(pose, (24.0, 20.0, 16.0, 12.0, 9.0))
    return pose, (60, 10), []


def c2_habilidade():
    chefe = caixa("chefe", (-16.0, 0.0, -36.0), (16.0, 24.0, 22.0))
    loc.chao = 25.0
    try:
        pose = {}
        corpo(pose, empina=-16.0, d=(0.0, 24.0 - 2.0, -2.0))
        pernas_plantadas(pose, abre=1.15)
        braco_mundo(pose, "right", 1.0, (8.0, 27.5, -26.0), (0.1, -0.9, -0.4), 0.0)
        braco_mundo(pose, "left", -1.0, (-9.0, 33.0, -18.0), (0.0, -0.6, -0.8), 0.0)
        loc.garras(pose, 0.0, flex=0.7, lados=("right",))
        loc.garras(pose, 0.0, flex=0.4, lados=("left",))
        cauda_local(pose, [(-12.0, 0.0), (-6.0, 0.0), (0.0, 0.0), (4.0, 0.0), (6.0, 0.0)])
        loc.cabeca_estavel(pose, pitch=-12.0, yaw=0.0, roll=0.0, rigidez=0.9)
        olhos(pose, 0.0)
        fita(pose, (16.0, 12.0, 9.0, 7.0, 5.0))
    finally:
        loc.chao = CHAO
    return pose, (40, 18), [chefe]


# ---------- conceito 3: ameaça de tamanduá de verdade ----------

def c3_guarda():
    pose = {}
    corpo(pose, empina=52.0, d=(0.0, -1.0, 1.5))
    pernas_plantadas(pose, abre=1.2)
    cmb.cauda_tripe(pose, (-70.0, -40.0, -10.0, 5.0, 15.0))
    braco_rel(pose, "left", -1.0, (-9.0, 1.0, -5.0), (-0.7, 0.3, -0.6), 20.0)
    braco_rel(pose, "right", 1.0, (9.0, 1.0, -5.0), (0.7, 0.3, -0.6), -20.0)
    loc.garras(pose, 0.0, flex=0.2)
    loc.cabeca_estavel(pose, pitch=4.0, yaw=0.0, roll=0.0, rigidez=0.95)
    olhos(pose, 0.0)
    fita(pose)
    return pose, (25, 8), []


def c3_golpe():
    pose = {}
    corpo(pose, empina=40.0, d=(0.0, -1.6, -1.0))
    pernas_plantadas(pose, abre=1.2)
    cmb.cauda_tripe(pose, (-70.0, -40.0, -10.0, 5.0, 15.0))
    braco_rel(pose, "left", -1.0, (5.0, -4.0, -11.0), (0.75, -0.45, -0.45), 0.0)
    braco_rel(pose, "right", 1.0, (-5.0, -4.0, -11.0), (-0.75, -0.45, -0.45), 0.0)
    loc.garras(pose, 0.0, flex=0.8)
    loc.cabeca_estavel(pose, pitch=-6.0, yaw=0.0, roll=0.0, rigidez=0.95)
    olhos(pose, 0.0)
    fita(pose, (14.0, 11.0, 8.0, 6.0, 4.0))
    return pose, (35, 10), []


def c3_habilidade():
    chefe = caixa("chefe", (-8.0, 0.0, -46.0), (8.0, 52.0, -30.0))
    pose = {}
    corpo(pose, empina=58.0, d=(0.0, 0.0, -4.0))
    pernas_plantadas(pose, abre=1.2)
    cmb.cauda_tripe(pose, (-70.0, -40.0, -10.0, 5.0, 15.0))
    braco_mundo(pose, "left", -1.0, (-10.5, 33.0, -40.0), (0.85, -0.1, -0.5), 0.0)
    braco_mundo(pose, "right", 1.0, (10.5, 33.0, -40.0), (-0.85, -0.1, -0.5), 0.0)
    loc.garras(pose, 0.0, flex=0.85)
    loc.cabeca_estavel(pose, pitch=8.0, yaw=0.0, roll=0.0, rigidez=0.95)
    olhos(pose, 0.0)
    fita(pose)
    return pose, (40, 12), [chefe]


CONCEITOS = [
    ("1 · A preguiça que finge dormir", [("guarda: pendurada, olhos meio fechados", c1_guarda),
                                          ("golpe: gancho que rasga de baixo", c1_golpe),
                                          ("habilidade: agarrada no chefe como num galho", c1_habilidade)]),
    ("2 · Fera de quatro", [("guarda: nos quatro, garras cravadas, cauda erguida", c2_guarda),
                            ("golpe: bote com as duas garras", c2_golpe),
                            ("habilidade: em cima do chefe, rasgando", c2_habilidade)]),
    ("3 · Ameaça de tamanduá", [("guarda: tripé, braços abertos (X)", c3_guarda),
                                ("golpe: abraço para dentro", c3_golpe),
                                ("habilidade: abraço no chefe", c3_habilidade)]),
]


def main():
    so = sys.argv[1] if len(sys.argv) > 1 else ""
    celulas = []
    for titulo, poses in CONCEITOS:
        linha = []
        for rotulo, fn in poses:
            if so and so not in fn.__name__:
                continue
            pose, vista, extras = fn()
            mats = rig.mats(pose)
            met = [np.round(cmb.anatomia_braco(pose, l), 2).tolist() for l in ("left", "right")]
            menor = min(cmb._menor_y(pose, tuple(o for o in rig.ossos)) for _ in [0])
            print(f"{fn.__name__:14s} anatomia esq {met[0]} dir {met[1]} · ponto mais baixo {menor:.2f}")
            m.cubos.extend(extras)
            try:
                lo, hi = bbmodelo.limites(m, mats)
                lo = np.minimum(lo, -6.0)
                lo[1] = 0.0
                im = render.renderizar(m, vista, escala=1.0, limites=(lo - 2, hi + 2), mats=mats)[0]
                esc = min(470 / im.width, 400 / im.height)
                im = render.renderizar(m, vista, escala=esc, limites=(lo - 2, hi + 2), mats=mats,
                                       cores={"chefe": "#8a8f9c"}, fundo=(236, 238, 242))[0]
            finally:
                for e in extras:
                    m.cubos.remove(e)
            if fn.__name__ == "c1_guarda":  # close do olho: meio fechado (o olhar entediado de predador)
                W = mats["eyelid_left"]
                olho = W[:3, :3] @ rig.piv("eyelid_left") + W[:3, 3]
                close = render.renderizar(m, (75, 6), escala=22.0, limites=(olho - 5.0, olho + 5.0), mats=mats, fundo=(250, 250, 252))[0]
                close = close.resize((122, int(close.height * 122 / close.width)))
                guarda = im.resize((int(im.width * 0.86), int(im.height * 0.86)))
                cel = Image.new("RGB", (470, max(guarda.height, close.height + 30)), (236, 238, 242))
                cel.paste(guarda, (0, (cel.height - guarda.height) // 2))
                x0, y0 = guarda.width + 8, (cel.height - close.height - 24) // 2
                ImageDraw.Draw(cel).rectangle([x0 - 2, y0 - 2, x0 + close.width + 1, y0 + close.height + 23], fill=(40, 44, 52))
                cel.paste(close, (x0, y0))
                ImageDraw.Draw(cel).text((x0 + 4, y0 + close.height + 1), "meio fechado", fill=(255, 255, 255), font=FONTE)
                im = cel
            linha.append((rotulo, im))
        if linha:
            celulas.append((titulo, linha))
    W, H = 490, 440
    folha = Image.new("RGB", (W * 3, sum(H + 30 for _ in celulas)), (255, 255, 255))
    d = ImageDraw.Draw(folha)
    y = 0
    for titulo, linha in celulas:
        d.rectangle([0, y, W * 3, y + 26], fill=(40, 44, 52))
        d.text((10, y + 3), titulo, fill=(255, 255, 255), font=FONTE_T)
        y += 30
        for k, (rotulo, im) in enumerate(linha):
            x = k * W
            folha.paste(im, (x + (W - im.width) // 2, y + 8))
            d.text((x + 10, y + H - 26), rotulo, fill=(30, 30, 40), font=FONTE)
        y += H
    saida = sys.argv[2] if len(sys.argv) > 2 else "folha-conceitos.png"
    folha.save(S + saida)
    print(folha.size)


if __name__ == "__main__":
    main()
