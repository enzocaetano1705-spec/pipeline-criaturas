"""Pavão e1 v3: construção do Koromon como gabarito, medidas e pintura próprias.

Gabarito (estudo em referencias-criaturas/estudos/koromon): 2 volumes de mesma largura, o de baixo avança 1 unidade
e forma a mandíbula; antenas em tira dobrada de planos (sobe, vai para trás, desce, avança para trás) inclinada
−17,5° em X; rosto só pintado; atlas 64×64 a 1 texel por unidade, Box UV.

Adaptação ao pavão (prancha de 21/10, medida em pixels):
- largura/altura 1,41 e profundidade/altura 1,19 → corpo 15 × 11 × 12 (Koromon 12 × 11 × 11).
- olhos a 0,35 da altura a partir do topo, centros a ±0,2 da largura; boca a 0,42 da altura a partir do chão;
  gema entre os olhos, acima deles.
- penas: raiz perto do centro do topo, abrem até ±0,7 da largura, sobem ~4 unidades e passam ~4 atrás das costas.
  A tira dobrada é dividida em esquerda e direita para manter os ossos e os clipes idle/walk aprovados no ensaio.
Nada do arquivo do Koromon é copiado: cubos, UV e pintura são gerados aqui.
"""

import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from criaturas import animar, bbmodelo, motor, ops, render, texturizar

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "estudo-referencias" / "pavao-planos-animado.bbmodel"  # ossos e clipes aprovados
DEST = ROOT / "revisao-v3"
FILE = DEST / "criatura-pavao-e1-v3.bbmodel"
TILT = -8  # o gabarito usa −17,5°; o perfil da prancha pede ~8° (pico a +3,75 sobre o topo)

P = {k: np.frombuffer(bytes.fromhex(v[1:]), dtype=np.uint8) for k, v in {
    "main": "#4bbbba", "light": "#72d3cb", "shade": "#3a9fa2", "deep": "#25747c", "dark": "#13363e",
    "amber": "#d08a2c", "amber_dark": "#8a4a14", "pupil": "#2b1407", "white": "#ffffff",
    "gold": "#efc04e", "gold_dark": "#a8741e", "gold_light": "#fff0b0", "tooth": "#f6f2e2",
    "f_blue": "#2a6976", "f_teal": "#3f9a9a", "f_green": "#4fae7f", "f_green_l": "#8fd09a",
    "oc_navy": "#193652", "oc_blue": "#2d5f8f", "rachis": "#1f4d5e",
}.items()}


def cubos() -> list[dict]:
    c = [
        {"nome": "body_lower", "osso": "body", "from": [-MEIA, 0, FRENTE_INF], "to": [MEIA, 4, 7]},
        {"nome": "body_upper", "osso": "body", "from": [-MEIA, 4, FRENTE_SUP], "to": [MEIA, 11, 7]},
    ]
    for lado, s in (("left", -1), ("right", 1)):
        def x(a, b):
            return sorted([s * a, s * b])
        xs = x(1, 7)
        c.append({"nome": f"feather_{lado}_rise", "osso": f"feather_{lado}_1", "from": [xs[0], 11, -2.5], "to": [xs[1], 16, -2.5]})
        xs = x(4, 12)
        c.append({"nome": f"feather_{lado}_top", "osso": f"feather_{lado}_2", "from": [xs[0], 16, -2.5], "to": [xs[1], 16, 4.5]})
        xs = x(5, 13)
        c.append({"nome": f"feather_{lado}_eye", "osso": f"feather_{lado}_3", "from": [xs[0], 11, 4.5], "to": [xs[1], 17, 4.5]})
        # plano complementar virado para o lado: a pena aparece no perfil como na vista de lado da prancha
        c.append({"nome": f"feather_{lado}_side", "osso": f"feather_{lado}_3", "from": [s * 7.5, 11, -1.5], "to": [s * 7.5, 17, 9.5]})
    return c


def ossos() -> list[dict]:
    o = []
    for lado, s in (("left", -1), ("right", 1)):
        o += [{"op": "update_node", "target": f"feather_{lado}_1", "origin": [s * 1.5, 11, -2.5], "rotation": [TILT, 0, 0]},
              {"op": "update_node", "target": f"feather_{lado}_2", "origin": [s * 6.5, 16, -2.5], "rotation": [0, 0, 0]},
              {"op": "update_node", "target": f"feather_{lado}_3", "origin": [s * 9.5, 16, 4.5], "rotation": [0, 0, 0]}]
    o += [{"op": "update_node", "target": "eye_left", "origin": [-4.5, 7, -5.01]},
          {"op": "update_node", "target": "eye_right", "origin": [4.5, 7, -5.01]},
          {"op": "update_node", "target": "mouth", "origin": [0, 3.5, -6.01]},
          {"op": "update_node", "target": "forehead_gem", "origin": [0, 9, -5.01]},
          {"op": "update_node", "target": "loc_eye_left", "position": [-4.5, 7, -5.11]},
          {"op": "update_node", "target": "loc_eye_right", "position": [4.5, 7, -5.11]},
          {"op": "update_node", "target": "loc_top", "position": [0, 15, 0]},
          {"op": "update_node", "target": "loc_center", "position": [0, 5.5, 0]}]
    return o


def _h(*v) -> float:
    """Ruído determinístico 0..1 por texel (mesma textura a cada execução)."""
    n = 0
    for q in v:
        n = (n * 1000003) ^ int(round(q * 8) + 4096)
    return ((n * 2654435761) & 0xFFFFFFFF) / 0xFFFFFFFF


# ---------- corpo ----------
# Medidas do corpo depois da correção à mão do usuário (21/10): cabeça 1 px mais estreita de cada lado, 1 px mais
# funda para trás. MEIA = meia largura; frentes do volume de cima e de baixo (o de baixo avança 1: mandíbula).
MEIA, FRENTE_SUP, FRENTE_INF = 6.5, -5, -6

# Olho 6×5 desenrolado na quina, como no gabarito: 4 colunas na frente e 2 na lateral, e o contorno fecha
# na lateral (não na frente). Colunas de dentro para fora; a pupila fica no meio da parte da frente e o brilho W
# sempre no alto à esquerda do espectador, como no conceito — por isso um padrão para cada olho.
OLHO_DIR = ["_KKKK_", "KWAAAK", "KPPAAK", "KDPDAK", "_KKKK_"]  # olho à direita do espectador (x < 0)
OLHO_ESQ = ["_KKKK_", "KAWAAK", "KPPAAK", "KDPDAK", "_KKKK_"]  # olho à esquerda do espectador (x > 0)
CORES_OLHO = {"K": "dark", "A": "amber", "D": "amber_dark", "P": "pupil", "W": "white"}


def _olho(x: float, y: float, q: float):
    """q: coordenada desenrolada (negativa na frente a partir da quina, positiva na lateral)."""
    if not (5 <= y < 10 and -4 < q < 2):
        return None
    k = (OLHO_DIR if x < 0 else OLHO_ESQ)[int(9 - math.floor(y))][int(math.floor(q + 4))]
    return None if k == "_" else CORES_OLHO[k]


def cor_corpo(cubo: str, face: str, x: float, y: float, z: float):
    # faces chapadas como no gabarito: topo claro, base escura; sem pintinhas soltas
    cor = {"up": "light", "down": "deep"}.get(face, "main")
    if face in ("north", "south", "east", "west"):
        if cubo == "body_upper" and y > 10:
            cor = "light"
        elif cubo == "body_lower" and y < 1:
            cor = "shade"
    ix = int(math.floor(x + MEIA))  # coluna na frente; a do meio é MEIA - 0,5
    meio = int(MEIA - 0.5)
    if cubo == "body_upper":
        if face == "north":
            olho = _olho(x, y, -(MEIA - abs(x)))
        elif face in ("east", "west"):
            olho = _olho(x, y, z - FRENTE_SUP)
        else:
            olho = None
        if olho:
            return olho
        if face == "north":
            gema = {10: [meio], 9: [meio - 1, meio, meio + 1], 8: [meio]}.get(int(math.floor(y)), [])
            if ix in gema:
                return "gold_light" if (ix, int(y)) in ((meio, 10), (meio + 1, 9)) else (
                    "gold_dark" if int(y) == 8 or ix == meio - 1 else "gold")
    if cubo == "body_lower":
        if face == "up" and z < FRENTE_SUP:
            return "dark"  # a boca é a faixa de 1 unidade que avança (sem quebra entre frente e topo)
        if face == "north":
            if 3 <= y < 4:
                return "dark"  # a boca vista de frente continua a faixa escura do topo
            if 2 <= y < 3 and ix in (2, 4, 2 * meio - 4, 2 * meio - 2):
                return "tooth"  # dentes pendurados logo abaixo da boca
            if 1 <= y < 2 and meio - 1 <= ix <= meio + 1:
                return "shade"  # linha do queixo
        if face in ("east", "west") and z < FRENTE_SUP and 3 <= y < 4:
            return "dark"  # a boca dobra a quina
    return cor


# ---------- penas (coordenadas locais do plano; |x| cresce para fora) ----------
def _faixa(p, linha):
    """(distância até a polilinha, posição 0..1 ao longo dela)."""
    pts = np.array(linha, float)
    seg = pts[1:] - pts[:-1]
    comp = np.linalg.norm(seg, axis=1)
    total, acum, melhor = comp.sum(), 0.0, (1e9, 0.0)
    for a, d, l in zip(pts[:-1], seg, comp):
        k = float(np.clip(np.dot(np.asarray(p) - a, d) / (l * l), 0, 1))
        dist = float(np.linalg.norm(np.asarray(p) - (a + k * d)))
        if dist < melhor[0]:
            melhor = (dist, (acum + k * l) / total)
        acum += l
    return melhor


def _pena(p, linha, largura, ocelo, r):
    """Pena de pavão num plano: lâmina ao longo da linha (raque escura), que termina num ocelo."""
    d, u = _faixa(p, linha)
    e = ((p[0] - ocelo[0]) / 1.7) ** 2 + ((p[1] - ocelo[1]) / 1.35) ** 2
    if e < 0.3:
        return "oc_navy"
    if e < 0.65:
        return "oc_blue"
    if e < 1.0:
        return "f_teal" if r > 0.2 else "f_green_l"
    w = largura(u)
    if d < w + (0.25 if r > 0.6 else 0):  # borda serrilhada das barbas
        if d < 0.35 and u < 0.7:
            return "rachis"
        if u > 0.55:
            return "f_green" if r > 0.25 else "f_green_l"
        return "f_blue" if r < 0.55 else "f_teal"
    return None


def cor_pena(cubo: str, x: float, y: float, z: float):
    t = abs(x)
    parte = cubo.rsplit("_", 1)[1]
    r = _h(t, y, z)
    sem_ocelo = (99, 99)
    if parte == "rise":  # haste que sai do alto da cabeça, sobe e abre para fora (vista de frente)
        return _pena((t, y), [(1.5, 11), (2.4, 13.4), (4.3, 15.2), (7, 16)], lambda u: 0.5 + 1.0 * u, sem_ocelo, r)
    if parte == "top":  # lâmina vista de cima: diagonal de dentro-frente para fora-trás
        return _pena((t, z), [(5, -2.5), (7.5, 0.5), (10, 4.5)], lambda u: 1.0 + 1.6 * math.sin(math.pi * u), sem_ocelo, r)
    if parte == "eye":  # ponta em folha com o ocelo perto da extremidade (frente e costas)
        return _pena((t, y), [(5, 16.2), (8, 15.6), (11, 14.4), (12.8, 12.8)],
                     lambda u: 0.6 + 2.0 * math.sin(math.pi * min(u, 0.95)) ** 0.7, (10.2, 14.6), r)
    if parte == "side":  # perfil: sobe da frente para trás e cai no ocelo
        return _pena((z, y), [(-1.5, 11.3), (1, 13.8), (4, 15.6), (7, 16.1), (9.3, 14.4)],
                     lambda u: 0.5 + 2.0 * math.sin(math.pi * min(u, 0.95)) ** 0.8, (6.8, 15.0), r)
    raise ValueError(cubo)


def pintar(modelo: bbmodelo.Modelo, res: int) -> np.ndarray:
    tex = np.zeros((res, res, 4), np.uint8)
    ident = np.eye(4)
    for c in modelo.cubos:
        for face in ("north", "south", "east", "west", "up", "down"):
            r = texturizar.texels_da_face(c, face, ident)
            if r is None:
                continue
            uv, pts = r
            for (u, v), (x, y, z) in zip(uv, pts):
                cor = cor_corpo(c.nome, face, x, y, z) if c.nome.startswith("body") else cor_pena(c.nome, x, y, z)
                if cor is not None:
                    tex[int(v) % res, int(u) % res, :3] = P[cor]
                    tex[int(v) % res, int(u) % res, 3] = 255
    return tex


# ---------- penugem procedural (laterais, costas, topo e base) ----------
# Rampas de valor em pixel art: uma puxada para o azul e outra para o verde; cada pena escolhe uma.
RAMPA_AZUL = ["#163f4c", "#1f6271", "#2b8590", "#3aa4a8", "#4bbbba", "#68cdc8", "#93e0d6"]
RAMPA_VERDE = ["#174746", "#20696a", "#2d8c8a", "#3ca7a2", "#4fbcb3", "#6dcdc2", "#98dfd2"]  # só um pouco mais verde
RAMPAS = [[np.frombuffer(bytes.fromhex(c[1:]), np.uint8) for c in r] for r in (RAMPA_AZUL, RAMPA_VERDE)]
BASE = 4  # índice da cor média (o "main" do conceito)


def _plano_da_face(face: str, x: float, y: float, z: float):
    """(a, b): coordenadas na face, com b crescendo para baixo (as penas se sobrepõem de cima para baixo)."""
    if face in ("east", "west"):
        return (z if face == "west" else -z), -y
    if face == "south":
        return x, -y
    if face == "north":
        return -x, -y
    return x, z  # up/down: as penas apontam para trás


def _ruido(a: float, b: float, escala: float, semente: float) -> float:
    """Ruído de valor suave (0..1): manchas grandes e irregulares."""
    fa, fb = a / escala, b / escala
    ia, ib = math.floor(fa), math.floor(fb)
    ta, tb = fa - ia, fb - ib
    ta, tb = ta * ta * (3 - 2 * ta), tb * tb * (3 - 2 * tb)
    c = [[_h(ia + i, ib + j, semente) for j in (0, 1)] for i in (0, 1)]
    return (c[0][0] * (1 - ta) + c[1][0] * ta) * (1 - tb) + (c[0][1] * (1 - ta) + c[1][1] * ta) * tb


# tufo de pena (b cresce para baixo): brilho em cima, miolo, "v" de sombra embaixo
TUFO = {(0, -1): +1, (-1, 0): -1, (1, 0): -1, (0, 1): -1}
BAYER = [[0.0, 0.5], [0.75, 0.25]]


def penugem(cubo: str, face: str, x: float, y: float, z: float, suave: bool = False) -> np.ndarray:
    """Penugem em pixel art sem padrão fixo: tufos espalhados em grade irregular, degradê de volume com
    pontilhado e manchas suaves de cor (um pouco mais verdes ou mais claras) em pontos aleatórios.

    `suave`: só o degradê e metade dos tufos, um tom de contraste, para o fundo do rosto.
    """
    a, b = _plano_da_face(face, x, y, z)
    ia, ib = math.floor(a), math.floor(b)
    k = ord(face[0])
    # volume: claro em cima, escuro embaixo, sombra sob o volume de cima, costas mais escuras
    valor = 0.0
    if face == "up":
        valor = 1.0
    elif face == "down":
        valor = -2.0
    else:
        valor = (y - 5.5) / 6.0  # -0,9 embaixo .. +0,9 no alto
        if cubo == "body_lower" and y > 3:
            valor -= 0.8
        if face in ("east", "west") and z > 4:
            valor -= 0.35
    valor += (_ruido(a, b, 5, k) - 0.5) * 1.1  # manchas leves de tom
    rampa = RAMPAS[1 if _ruido(a, b, 6, k + 50) > 0.68 else 0]  # áreas um pouco mais verdes
    if suave:
        valor *= 0.4
    nivel = BASE + math.floor(valor + BAYER[ib % 2][ia % 2])  # pontilhado entre os tons
    # tufos: no máximo um por célula 3×3, posição sorteada, ~60% das células
    for ca in range(math.floor((ia - 1) / 3), math.floor((ia + 1) / 3) + 1):
        for cb in range(math.floor((ib - 1) / 3), math.floor((ib + 1) / 3) + 1):
            if _h(ca, cb, k, 1.7) > (0.3 if suave else 0.6):
                continue
            sa, sb = ca * 3 + math.floor(_h(ca, cb, k, 2.9) * 3), cb * 3 + math.floor(_h(ca, cb, k, 4.3) * 3)
            d = TUFO.get((ia - sa, ib - sb))
            if d is not None:
                if suave and d > 0:
                    continue
                nivel += d
                if d > 0 and face != "down" and y > 5 and _h(ca, cb, k, 8.8) < 0.1 and not suave:
                    return np.frombuffer(bytes.fromhex("e9be55"), np.uint8)  # pintinha dourada no brilho de alguns tufos
                break
        else:
            continue
        break
    lim = (BASE - 1, BASE) if suave else (0, len(rampa) - 1)
    return rampa[int(np.clip(nivel, *lim))]


RAMPA_FRENTE = {tuple(RAMPAS[i][j]) for i in (0, 1) for j in (BASE - 1, BASE)}  # para poder repintar


def protegido(cubo: str, face: str, x: float, y: float, z: float) -> bool:
    """Rosto e boca (já aprovados e retocados à mão pelo usuário) não são repintados."""
    if face == "north":
        return True
    if cubo == "body_lower" and (face == "up" and z < FRENTE_SUP or face in ("east", "west") and z < FRENTE_SUP and y >= 3):
        return True
    if cubo == "body_upper" and face in ("east", "west") and _olho(x, y, z - FRENTE_SUP):
        return True
    return False


def so_penugem():
    """Pinta a penugem procedural no corpo, mantendo rosto, boca e penas como estão no .bbmodel."""
    import datetime
    hist = DEST / "historico"
    hist.mkdir(exist_ok=True)
    carimbo = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    shutil.copy2(FILE, hist / f"{carimbo}-antes-da-penugem.bbmodel")
    modelo = bbmodelo.ler(FILE)
    res = int(modelo.bruto["resolution"]["width"])
    tex = np.array(modelo.textura.convert("RGBA"))
    ident = np.eye(4)
    pintados = 0
    fundo = {tuple(P["main"]), tuple(P["light"])}  # no rosto, só o fundo liso recebe a penugem suave
    for c in modelo.cubos:
        if not c.nome.startswith("body"):
            continue
        for face in ("north", "south", "east", "west", "up", "down"):
            r = texturizar.texels_da_face(c, face, ident)
            if r is None:
                continue
            for (u, v), (x, y, z) in zip(*r):
                if not (0 <= u < res and 0 <= v < res):
                    continue
                if face == "north":
                    if tuple(tex[int(v), int(u), :3]) in fundo or tuple(tex[int(v), int(u), :3]) in RAMPA_FRENTE:
                        tex[int(v), int(u), :3] = penugem(c.nome, face, x, y, z, suave=True)                             if not (c.nome == "body_upper" and y > 10) else P["light"]
                    continue
                if not protegido(c.nome, face, x, y, z):
                    tex[int(v), int(u), :3] = penugem(c.nome, face, x, y, z)
                    tex[int(v), int(u), 3] = 255
                    pintados += 1
    Image.fromarray(tex).save(DEST / "textura.png")
    Image.fromarray(tex).save(ROOT / "textura.png")
    nome = modelo.bruto["textures"][0].get("name") or "textura"
    motor.editar(FILE, [{"op": "update_texture", "target": nome, "source": texturizar._data_url(tex), "width": res,
                         "height": res, "material": None}])
    modelo = bbmodelo.ler(FILE)
    render.folha(modelo, lado_px=360, titulo="Pavão e1 | v3 + penugem").save(DEST / "folha.png")
    geo = motor.resumo_validacao(motor.validar(FILE.resolve()))
    print(f"penugem: {pintados} texels pintados; geometria {geo[0]} erros/{geo[1]} avisos")


def so_textura():
    """Repinta só o corpo no .bbmodel atual (com as edições à mão do usuário), sem mexer na geometria.

    Os pixels das penas ficam como estão. Antes, guarda o modelo e a textura em revisao-v3/historico/.
    Se uma ilha do corpo sai da textura (v < 0), ela volta para dentro: é mudança de UV, não de forma.
    """
    import datetime
    hist = DEST / "historico"
    hist.mkdir(exist_ok=True)
    carimbo = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    shutil.copy2(FILE, hist / f"{carimbo}-antes-da-textura.bbmodel")
    externa = ROOT / "textura.png"  # o .bbmodel aponta para ../textura.png
    if externa.exists():
        shutil.copy2(externa, hist / f"{carimbo}-textura-externa.png")
    modelo = bbmodelo.ler(FILE)
    res = int(modelo.bruto["resolution"]["width"])
    corrigir = []
    for c in modelo.cubos:
        if c.nome.startswith("body") and any(min(f["uv"][1], f["uv"][3]) < 0 or min(f["uv"][0], f["uv"][2]) < 0
                                             for f in c.faces.values() if "uv" in f):
            corrigir.append({"op": "update_node", "target": c.nome, "uv_offset": [0, 0]})
    if corrigir:
        motor.editar(FILE, corrigir)
        modelo = bbmodelo.ler(FILE)
    tex = np.array(modelo.textura.convert("RGBA")) if modelo.textura is not None else np.zeros((res, res, 4), np.uint8)
    ident = np.eye(4)
    for c in modelo.cubos:
        if not c.nome.startswith("body"):
            continue
        for face in ("north", "south", "east", "west", "up", "down"):
            r = texturizar.texels_da_face(c, face, ident)
            if r is None:
                continue
            for (u, v), (x, y, z) in zip(*r):
                if 0 <= u < res and 0 <= v < res:
                    tex[int(v), int(u), :3] = P[cor_corpo(c.nome, face, x, y, z)]
                    tex[int(v), int(u), 3] = 255
    Image.fromarray(tex).save(DEST / "textura.png")
    Image.fromarray(tex).save(externa)
    # a textura do usuário foi renomeada para "textura.png": troca pelo nome, não pelo índice
    nome = modelo.bruto["textures"][0].get("name") or "textura"
    motor.editar(FILE, [{"op": "update_texture", "target": nome, "source": texturizar._data_url(tex), "width": res, "height": res,
                               "material": None}])  # o Blockbench grava group "" e o motor lê como material
    modelo = bbmodelo.ler(FILE)
    render.folha(modelo, lado_px=360, titulo="Pavão e1 | v3 + edições do usuário").save(DEST / "folha.png")
    geo = motor.resumo_validacao(motor.validar(FILE))
    aerr, awarn, _ = animar.validar_animacoes(FILE)
    print(f"textura do corpo repintada ({len(corrigir)} ilha(s) de UV reposicionada(s)); "
          f"geometria {geo[0]} erros/{geo[1]} avisos, animações {aerr} erros/{awarn} avisos")


def main():
    if "--penugem" in sys.argv:
        return so_penugem()
    if "--so-textura" in sys.argv:
        return so_textura()
    if DEST.exists() and "--refazer" not in sys.argv:
        raise SystemExit("revisao-v3 já existe; use --refazer para gerar de novo (só a v3 é sobrescrita).")
    DEST.mkdir(exist_ok=True)
    shutil.copy2(SOURCE, FILE)
    lista = cubos()
    offsets, (res, _) = ops.distribuir_uv(lista, margem=0)
    antigo = bbmodelo.ler(FILE)
    lote = [{"op": "remove_node", "target": c.nome} for c in antigo.cubos]
    lote.append({"op": "set_model_properties", "resolution": {"width": res, "height": res}})
    lote += ossos()
    for c in lista:
        lote.append({"op": "add_cube", "name": c["nome"], "parent": c["osso"], "from": c["from"], "to": c["to"],
                     "box_uv": True, "uv_offset": offsets[c["nome"]],
                     **({"inflate": 0.01} if "feather" in c["nome"] else {})})
    (DEST / "geometria.ops.json").write_text(json.dumps({"operations": lote}, ensure_ascii=False, indent=1), encoding="utf-8")
    motor.editar(FILE, lote)
    modelo = bbmodelo.ler(FILE)
    tex = pintar(modelo, res)
    Image.fromarray(tex).save(DEST / "textura.png")
    texturizar.aplicar_no_modelo(FILE, tex, modelo, [])
    modelo = bbmodelo.ler(FILE)
    render.folha(modelo, lado_px=360, titulo="Pavão e1 | v3 (gabarito Koromon)").save(DEST / "folha.png")
    geo = motor.resumo_validacao(motor.validar(FILE))
    aerr, awarn, amsg = animar.validar_animacoes(FILE)
    rel = {"pecas": len(modelo.cubos), "volumes": 2, "planos": len(modelo.cubos) - 2, "ossos": len(modelo.ossos),
           "atlas": [res, res], "validacao_geometria": {"erros": geo[0], "avisos": geo[1], "mensagens": geo[2]},
           "validacao_animacoes": {"erros": aerr, "avisos": awarn, "mensagens": amsg},
           "gabarito": "the-digimod/blockbench/babies2/koromon.bbmodel (só a construção; nada copiado)"}
    (DEST / "relatorio.json").write_text(json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{FILE.name}: {len(modelo.cubos)} peças, atlas {res}², geometria {geo[0]} erros/{geo[1]} avisos, "
          f"animações {aerr} erros/{awarn} avisos")


if __name__ == "__main__":
    main()
