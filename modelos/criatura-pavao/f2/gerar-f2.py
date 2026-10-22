"""Pavão F2 (estágio 2 de 3, avinídeo): construção por partes a partir de gabaritos da biblioteca.

Gabaritos (só a solução construtiva; nada copiado):
- Harpymon (Digimod, champions): ave bípede de braços-asas. Pernas coxa→canela→pé com 3 garras para a frente e
  1 para trás; asa = plano grande pendurado no braço; cauda em planos encadeados; corpo quadril/tronco/ombros.
- Pavão F1 aprovado (caso 1, nota 8,5): crista em plumas com ocelo, plumagem em escama, olhos que dobram a quina,
  gema na testa, 1 texel por unidade.
Medidas: prancha `prancha.webp` (frente e lado), altura até o alto da cabeça ≈ 32 unidades (2 blocos).
Ossos com os nomes do `animar` (body, neck_1, head, arm_*, wing_*, leg_*, tail_1, feather_*) para idle e walk.
"""

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from criaturas import animar, bbmodelo, motor, ops, render, texturizar

AQUI = Path(__file__).resolve().parent
FILE = AQUI / "criatura-pavao-e2.bbmodel"

# reaproveita paleta, ruído e o desenho de pena do caso 1
_sp = importlib.util.spec_from_file_location("v3", AQUI.parent / "revisao-v3-koromon.py")
v3 = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(v3)
_h, _ruido, _pena_f1 = v3._h, v3._ruido, v3._pena


def rgb(c):
    return np.frombuffer(bytes.fromhex(c.lstrip("#")), np.uint8)


TEAL = [rgb(c) for c in v3.RAMPA_AZUL]
VERDE = [rgb(c) for c in ("#174a3c", "#1f6b52", "#2f8f63", "#43a86f", "#5cbd7f", "#86d39a", "#b4e6bd")]
CREME = [rgb(c) for c in ("#8f7f5c", "#b3a37a", "#cfc298", "#e6dcb6", "#f3ecd0", "#fbf6e6", "#ffffff")]
P = {k: rgb(v) for k, v in {
    "dark": "#13363e", "amber": "#e0a12b", "amber_dark": "#9a5a12", "pupil": "#2b1407", "white": "#ffffff",
    "gold": "#efc04e", "gold_dark": "#a8741e", "gold_light": "#fff0b0", "claw": "#262a2e", "claw_l": "#4a5157",
    "beak": "#e8c35a", "beak_dark": "#a87a24", "oc_navy": "#193652", "oc_blue": "#2d5f8f", "rachis": "#1f4d5e",
    "f_blue": "#2a6976", "f_teal": "#3f9a9a", "f_green": "#4fae7f", "f_green_l": "#8fd09a",
}.items()}


# ---------------------------------------------------------------- geometria
def S(s, a, b):
    """Intervalo em x espelhado pelo lado (s = −1 esquerda da criatura, +1 direita)."""
    return sorted([s * a, s * b])


def esqueleto():
    """(ossos, cubos). Osso: nome, pai, pivô, rotação. Cubo: nome, osso, de, até, [rotação, origem]."""
    O, C = [], []

    def osso(n, pai, piv, rot=(0, 0, 0)):
        O.append({"nome": n, "pai": pai, "pivo": list(piv), "rot": list(rot)})

    def cubo(n, o, de, ate, rot=None, origem=None):
        c = {"nome": n, "osso": o, "from": list(de), "to": list(ate)}
        if rot:
            c["rot"], c["origem"] = list(rot), list(origem)
        C.append(c)

    osso("body", None, (0, 13, 0))
    cubo("hips", "body", (-3.5, 11, -3), (3.5, 15, 3))
    cubo("torso", "body", (-4, 15, -3.5), (4, 22, 3))
    cubo("shoulders", "body", (-5, 21, -3), (5, 24, 3))
    osso("neck_1", "body", (0, 23.5, -0.5), (-12, 0, 0))
    cubo("neck", "neck_1", (-2, 23, -2.5), (2, 28, 1.5))
    osso("head", "neck_1", (0, 27.5, -1), (12, 0, 0))
    cubo("skull", "head", (-3, 27, -4), (3, 32, 2))
    cubo("beak", "head", (-1, 28, -7), (1, 30, -4))
    cubo("beak_tip", "head", (-1, 27, -7), (1, 28, -6))
    for lado, s in (("left", -1), ("right", 1)):
        # crista: haste + ponta com ocelo (caso 1)
        osso(f"feather_{lado}_1", "head", (s * 1, 32, -1), (-10, 0, 0))
        x = S(s, 0.5, 5)
        cubo(f"crest_{lado}_rise", f"feather_{lado}_1", (x[0], 32, -1), (x[1], 37, -1))
        osso(f"feather_{lado}_2", f"feather_{lado}_1", (s * 4.5, 37, -1), (0, -s * 30, 0))
        x = S(s, 3, 12)
        cubo(f"crest_{lado}_eye", f"feather_{lado}_2", (x[0], 33, -1), (x[1], 39, -1))
        # braço com asa pendurada (Harpymon)
        osso(f"arm_{lado}", "body", (s * 5, 22.5, 0), (0, 0, s * 8))
        x = S(s, 4, 6)
        cubo(f"upper_arm_{lado}", f"arm_{lado}", (x[0], 16, -1), (x[1], 23, 1))
        osso(f"forearm_{lado}", f"arm_{lado}", (s * 5, 16.5, 0), (-15, 0, 0))
        cubo(f"lower_arm_{lado}", f"forearm_{lado}", (x[0], 11, -1), (x[1], 17, 1))
        cubo(f"hand_{lado}", f"forearm_{lado}", (x[0], 9, -1.5), (x[1], 11, 1))
        for i in range(3):  # 3 garras penduradas da mão
            cx = s * (4.35 + 0.65 * i)
            cubo(f"claw_{lado}_{i}", f"forearm_{lado}", (cx - 0.3, 7.5, -1.4), (cx + 0.3, 9, -0.6))
        osso(f"wing_{lado}", f"arm_{lado}", (s * 5.5, 22, 1), (0, -s * 28, 0))
        x = S(s, 5, 13)
        cubo(f"wing_{lado}_panel", f"wing_{lado}", (x[0], 4, 1.2), (x[1], 22, 1.2))
        # perna de ave (Harpymon): coxa, canela, tarso com tornozeleira, 3 dedos à frente e 1 atrás
        osso(f"leg_{lado}", "body", (s * 2.5, 12, 0))
        x = S(s, 0.5, 4.5)
        cubo(f"thigh_{lado}", f"leg_{lado}", (x[0], 7.5, -2.25), (x[1], 13, 2.25))
        osso(f"shin_{lado}", f"leg_{lado}", (s * 2.5, 8.5, 0), (12, 0, 0))
        x = S(s, 1.25, 3.75)
        cubo(f"shank_{lado}", f"shin_{lado}", (x[0], 4, -1.25), (x[1], 9, 1.25))
        osso(f"foot_{lado}", f"shin_{lado}", (s * 2.5, 4.5, 0), (-12, 0, 0))
        x = S(s, 1.75, 3.25)
        cubo(f"tarsus_{lado}", f"foot_{lado}", (x[0], 1, -0.75), (x[1], 5, 0.75))
        for i, giro in enumerate((-22, 0, 22)):
            cubo(f"toe_{lado}_{i}", f"foot_{lado}", (s * 2.5 - 0.5, 0, -4), (s * 2.5 + 0.5, 1, 0),
                 rot=(0, giro, 0), origem=(s * 2.5, 0.5, 0))
        cubo(f"toe_{lado}_back", f"foot_{lado}", (s * 2.5 - 0.5, 0, 0), (s * 2.5 + 0.5, 1, 2))
    # cauda: base e leque de 5 penas em planos laterais (aparecem de lado; de costas pelo giro em Y)
    osso("tail_1", "body", (0, 13.5, 3))
    cubo("tail_base", "tail_1", (-1.5, 12, 2.5), (1.5, 15.5, 6))
    for i, (pitch, yaw) in enumerate(((-35, 18), (-15, -18), (5, 18), (25, -18), (45, 0))):
        osso(f"feather_fan_{i + 1}", "tail_1", (0, 13.75, 5.5), (pitch, yaw, 0))
        cubo(f"fan_{i + 1}", f"feather_fan_{i + 1}", (0, 10.75, 5.5), (0, 16.75, 21.5))
    return O, C


# ---------------------------------------------------------------- pintura
BAYER = [[0.0, 0.5], [0.75, 0.25]]


def plumagem(rampa, a, b, valor, k, suave=False):
    """Escama de pena do caso 1 (penas de 4, fileiras de 2, deslocadas meia pena) sobre um valor de volume."""
    ia, ib = math.floor(a), math.floor(b)
    fila = ib // 2
    v = ib - 2 * fila
    desloc = (fila % 2) * 2 + (1 if _h(fila, k, 7.1) > 0.8 else 0)
    col = (ia + desloc) // 4
    u = (ia + desloc) - 4 * col
    tom = _h(col, fila, k)
    valor += (_ruido(a, b, 6, k) - 0.5) * 0.6 + (0.45 if tom > 0.85 else -0.45 if tom < 0.12 else 0)
    nivel = 4 + math.floor(valor + 0.5 + (BAYER[ib % 2][ia % 2] - 0.375) * 0.35)
    if v == 0 and u in (0, 3):
        if _h((ia + ((fila - 1) % 2) * 2) // 4, fila - 1, k, 3.1) > 0.12:
            nivel -= 1 if suave else 2
    elif v == 0:
        nivel += 1 if (u == 1) == (tom > 0.5) else 0
    elif u in (0, 3):
        nivel -= 1
    return rampa[int(np.clip(nivel, 2 if suave else 0, len(rampa) - 1))]


def _coords(face, x, y, z):
    if face in ("east", "west"):
        return (z if face == "west" else -z), -y
    if face == "south":
        return x, -y
    if face == "north":
        return -x, -y
    return x, z


OLHO = ["KKK_", "APAK", "_AA_"]  # desenrolado na quina: 2 colunas na frente, 2 na lateral (de dentro para fora)
COR_OLHO = {"K": "dark", "A": "amber", "P": "pupil"}


def cor_corpo(nome, face, x, y, z, lim):
    """Cor de um texel das partes sólidas. `lim` = (de, até) do cubo."""
    de, ate = lim
    altura = (y - de[1]) / max(ate[1] - de[1], 1e-6)
    a, b = _coords(face, x, y, z)
    k = sum(map(ord, nome)) + ord(face[0])
    valor = {"up": 0.8, "down": -1.6}.get(face, (altura - 0.5) * 1.2)
    if face in ("east", "west") and z > 1.5:
        valor -= 0.3
    rampa = VERDE if _ruido(a, b, 7, k + 50) > 0.7 else TEAL
    # garras e bico
    if nome.startswith("claw") or (nome.startswith("toe") and (z < -3 or z > 1.2)):
        return P["claw_l"] if face == "up" else P["claw"]
    if nome.startswith("beak"):
        return P["beak_dark"] if (nome == "beak_tip" or y < 28.5 and face == "north") else P["beak"]
    # faixas douradas: pulso e tornozelo
    if (nome.startswith("lower_arm") and 15 <= y < 16.2) or (nome.startswith("tarsus") and 3.5 <= y < 4.6):
        return P["gold_light"] if face == "up" or (face == "north" and _h(x, y) > 0.7) else P["gold"]
    if nome.startswith(("tarsus", "toe", "hand")):
        return TEAL[3 if face != "down" else 2]
    # peito e garganta creme (frente do tronco, do pescoço e a parte de baixo do rosto)
    creme = (face == "north" and ((nome in ("torso", "hips") and abs(x) < 2.6 - 0.15 * max(0, 21 - y))
                                  or (nome == "neck") or (nome == "skull" and y < 28.6 and abs(x) < 2.6)
                                  or (nome == "shoulders" and abs(x) < 2.5)))
    if nome == "neck" and face in ("east", "west") and z < -1.5:
        creme = True
    if nome == "skull":
        # rosto: olhos com sobrancelha brava, gema
        if face == "north":
            q = -(3 - abs(x))
        elif face in ("east", "west"):
            q = z + 4
        else:
            q = None
        if q is not None and -2 < q < 2 and 28.6 <= y < 31.6:
            kk = OLHO[int(31 - math.floor(y))][int(math.floor(q + 2))]
            if kk != "_":
                return P[COR_OLHO[kk]]
        if face == "north" and abs(x) < 1 and 30.6 <= y < 32:
            return P["gold_light"] if (x > 0 and y > 31) else P["gold"]
    if creme:
        return plumagem(CREME, a, b, valor * 0.6, k, suave=True)
    return plumagem(rampa, a, b, valor, k)


def cor_plano(nome, face, x, y, z):
    """Penas em planos: crista, asas e leque da cauda (alfa = None)."""
    r = _h(x, y, z)
    if nome.startswith("crest"):
        t = abs(x)
        if nome.endswith("rise"):
            return _pena_f1((t, y), [(0.8, 32), (1.6, 34.5), (3.2, 36.3), (5, 37)], lambda u: 0.5 + 1.0 * u, (99, 99), r)
        return _pena_f1((t, y), [(3.5, 37.2), (6.5, 37.4), (9.5, 36.4), (11.6, 34.5)],
                        lambda u: 0.6 + 2.0 * math.sin(math.pi * min(u, 0.95)) ** 0.7, (9.0, 36.6), r)
    if nome.startswith("fan"):
        # pena da cauda ao longo de z (da base para a ponta), largura em y; ocelo perto da ponta
        # haste fina na base, folha que alarga até o ocelo, borda de baixo creme (como no conceito)
        u = (z - 5.5) / 16.0
        d = y - 13.75
        if u < 0 or u > 1:
            return None
        meia = 0.45 if u < 0.35 else 0.45 + 1.9 * math.sin(math.pi * min(1.0, (u - 0.35) / 0.68)) ** 0.7
        if abs(d) > meia + (0.3 if r > 0.6 else 0):
            return None
        e = ((z - 18.0) / 1.7) ** 2 + (d / 1.25) ** 2
        if e < 0.3:
            return "oc_navy"
        if e < 0.65:
            return "oc_blue"
        if e < 1.0:
            return "f_teal"
        if u < 0.35:
            return "rachis"
        if d < -meia + 0.8:
            return CREME[4] if r > 0.3 else CREME[3]
        return VERDE[4] if r > 0.35 else VERDE[5]
    if nome.startswith("wing"):
        # asa pendurada: penas longas lado a lado (de dentro para fora), ponta em V, borda de baixo creme,
        # ocelos nas penas de fora; a base junto ao braço é teal
        t = abs(x) - 5  # 0 junto ao braço .. 8 na borda
        fileira = int(t // 2)  # penas de 2 texels
        comprimento = 7 + 2.0 * fileira + 1.5 * _h(fileira, 9.1)  # as de fora descem mais
        topo = 22 - 0.6 * fileira
        fundo = topo - comprimento - 4 - 0.8 * fileira
        meio = (fileira + 0.5) * 2
        v_ponta = fundo + 1.6 * abs(t - meio)  # ponta em V
        if y > topo or y < v_ponta:
            return None
        if y < v_ponta + 1.6:
            return CREME[5] if r > 0.2 else CREME[4]
        if fileira >= 2:
            ex, ey = (t - meio) / 1.0, (y - (fundo + 4.2)) / 1.6
            e = ex * ex + ey * ey
            if e < 0.35:
                return P["oc_navy"]
            if e < 0.8:
                return P["oc_blue"]
            if e < 1.4:
                return P["f_green"] if r > 0.3 else P["f_green_l"]
        if t > 7.2:
            return CREME[4] if r > 0.3 else CREME[5]  # borda de fora creme, como no conceito
        if abs(t - meio) > 0.75:  # borda entre penas
            return TEAL[2]
        return VERDE[4] if y < fundo + 7 else (TEAL[4] if r > 0.25 else TEAL[5])
    raise ValueError(nome)


# ---------------------------------------------------------------- montagem
def montar():
    ossos, cubos = esqueleto()
    lista = [{"nome": c["nome"], "from": c["from"], "to": c["to"]} for c in cubos]
    offsets, (res, _) = ops.distribuir_uv(lista, margem=0, larguras=(64, 128, 256))
    FILE.unlink(missing_ok=True)
    motor.criar(FILE, "criatura-pavao-e2", res, res)
    lote = []
    for o in ossos:
        op = {"op": "add_group", "name": o["nome"], "origin": o["pivo"]}
        if any(o["rot"]):
            op["rotation"] = o["rot"]
        if o["pai"]:
            op["parent"] = o["pai"]
        lote.append(op)
    for c in cubos:
        op = {"op": "add_cube", "name": c["nome"], "parent": c["osso"], "from": c["from"], "to": c["to"],
              "box_uv": True, "uv_offset": offsets[c["nome"]]}
        if "rot" in c:
            op["rotation"], op["origin"] = c["rot"], c["origem"]
        if c["from"][0] == c["to"][0] or c["from"][1] == c["to"][1] or c["from"][2] == c["to"][2]:
            op["inflate"] = 0.01
        lote.append(op)
    (AQUI / "geometria.ops.json").write_text(json.dumps({"operations": lote}, indent=1), encoding="utf-8")
    motor.editar(FILE, lote)
    modelo = bbmodelo.ler(FILE)
    lim = {c["nome"]: (c["from"], c["to"]) for c in cubos}
    tex = np.zeros((res, res, 4), np.uint8)
    for c in modelo.cubos:
        plano = any(abs(float(c.ate[i] - c.de[i])) < 1e-6 for i in range(3))
        for face in ("north", "south", "east", "west", "up", "down"):
            r = texturizar.texels_da_face(c, face, np.eye(4))
            if r is None:
                continue
            for (u, v), (x, y, z) in zip(*r):
                cor = cor_plano(c.nome, face, x, y, z) if plano else cor_corpo(c.nome, face, x, y, z, lim[c.nome])
                if isinstance(cor, str):  # nomes de cor do desenho de pena do caso 1
                    cor = P[cor] if cor in P else v3.P[cor]
                if cor is not None and 0 <= u < res and 0 <= v < res:
                    tex[int(v), int(u), :3] = cor
                    tex[int(v), int(u), 3] = 255
    Image.fromarray(tex).save(AQUI / "textura.png")
    texturizar.aplicar_no_modelo(FILE, tex, modelo, [])
    info = animar.animar(FILE, "bípede", "meio", quais=("idle", "walk"))
    modelo = bbmodelo.ler(FILE)
    render.folha(modelo, lado_px=360, titulo="Pavão F2 | v1 (gabarito Harpymon + caso 1)").save(AQUI / "folha.png")
    geo = motor.resumo_validacao(motor.validar(FILE.resolve()))
    aerr, awarn, _ = animar.validar_animacoes(FILE)
    print(f"{FILE.name}: {len(modelo.cubos)} peças, {len(modelo.ossos)} ossos, atlas {res}², "
          f"geometria {geo[0]} erros/{geo[1]} avisos, animações {aerr}/{awarn} {sorted(info['clipes'])}")
    for m in geo[2][:12]:
        print("  ", m)


if __name__ == "__main__":
    montar()
