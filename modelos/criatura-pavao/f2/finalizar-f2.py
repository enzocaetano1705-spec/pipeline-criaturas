"""Pavão F2 sobre a remodelagem do usuário (23h47): pivôs nas juntas, garras nas mãos, UV, textura e animação.

1. Achata o rig: a rotação de cada osso passa para os cubos (mesmo lugar no mundo, conferido ao final), e os ossos
   ficam sem rotação. Assim os pivôs podem ir para as juntas novas sem mexer na geometria.
2. Pivôs nas juntas: quadril, joelho, tornozelo, ombro, cotovelo, base do pescoço, cabeça, cauda e penas.
3. Garras: 3 por mão, saindo da face da mão mais distante do cotovelo, no mesmo referencial da mão.
4. UV refeito (Box UV, empacotado) e textura pintada pela orientação no mundo: peito creme onde a face olha para
   a frente; faixas douradas na ponta do antebraço e no alto do tarso; garras nas pontas dos dedos; penas em planos
   (asas, crista, leque) pintadas em coordenadas normalizadas a partir da borda presa ao corpo.
5. idle e walk refeitos pelo `animar` para a pose nova.
"""

import importlib.util
import math
import shutil
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image

from criaturas import animar, bbmodelo, motor, ops, render, texturizar

AQUI = Path(__file__).resolve().parent
FILE = AQUI / "criatura-pavao-e2.bbmodel"
_sp = importlib.util.spec_from_file_location("g", AQUI / "gerar-f2.py")
g = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(g)
TEAL, VERDE, CREME, P, _h, plumagem, _pena_f1 = g.TEAL, g.VERDE, g.CREME, g.P, g._h, g.plumagem, g._pena_f1


def euler(r: np.ndarray) -> list[float]:
    """Inverso de bbmodelo.matriz_rotacao (Rz·Ry·Rx), em graus."""
    y = math.asin(max(-1.0, min(1.0, -r[2, 0])))
    if abs(math.cos(y)) > 1e-6:
        x, z = math.atan2(r[2, 1], r[2, 2]), math.atan2(r[1, 0], r[0, 0])
    else:
        x, z = math.atan2(-r[1, 2], r[1, 1]), 0.0
    return [round(math.degrees(v), 5) for v in (x, y, z)]


def mundo(modelo):
    mats = bbmodelo.matrizes_ossos(modelo)
    w = {c.uuid: bbmodelo.matriz_cubo(modelo, c, mats) for c in modelo.cubos}
    for c in modelo.cubos:  # por nome também (o primeiro, quando o nome se repete)
        w.setdefault(c.nome, w[c.uuid])
    return w


def centro(c):
    return (c.de + c.ate) / 2


def pontas(c, w):
    """As duas pontas (no mundo) do eixo mais comprido do cubo."""
    eixo = int(np.argmax(c.ate - c.de))
    a, b = centro(c).copy(), centro(c).copy()
    a[eixo], b[eixo] = c.de[eixo], c.ate[eixo]
    return bbmodelo.aplicar(w, np.array([a, b])), eixo


def ponta_perto(c, w, alvo):
    (a, b), _ = pontas(c, w)
    return a if np.linalg.norm(a - alvo) <= np.linalg.norm(b - alvo) else b


# ------------------------------------------------------------------ 1-2: achatar e pivôs
def achatar_e_pivotar(modelo):
    W = mundo(modelo)
    cub = {c.nome: c for c in modelo.cubos}
    lote = []
    for c in modelo.cubos:
        w = W[c.uuid]
        ctr = centro(c)
        d = bbmodelo.aplicar(w, ctr[None])[0] - ctr
        op = {"op": "update_node", "target": c.uuid, "from": (c.de + d).round(5).tolist(), "to": (c.ate + d).round(5).tolist(),
              "origin": (ctr + d).round(5).tolist(), "rotation": euler(w[:3, :3])}
        lote.append(op)
    cw = {n: bbmodelo.aplicar(W[n], centro(cub[n])[None])[0] for n in cub}
    junta = {"body": cw["hips"]}
    for s in ("left", "right"):
        junta[f"leg_{s}"] = ponta_perto(cub[f"thigh_{s}"], W[f"thigh_{s}"], cw["hips"])
        junta[f"shin_{s}"] = ponta_perto(cub[f"shank_{s}"], W[f"shank_{s}"], cw[f"thigh_{s}"])
        junta[f"foot_{s}"] = ponta_perto(cub[f"tarsus_{s}"], W[f"tarsus_{s}"], cw[f"shank_{s}"])
        junta[f"arm_{s}"] = ponta_perto(cub[f"upper_arm_{s}"], W[f"upper_arm_{s}"], cw["shoulders"])
        junta[f"forearm_{s}"] = ponta_perto(cub[f"lower_arm_{s}"], W[f"lower_arm_{s}"], cw[f"upper_arm_{s}"])
        junta[f"wing_{s}"] = junta[f"arm_{s}"]
        junta[f"feather_{s}_1"] = ponta_perto(cub[f"crest_{s}_rise"], W[f"crest_{s}_rise"], cw["skull"])
        junta[f"feather_{s}_2"] = ponta_perto(cub[f"crest_{s}_eye"], W[f"crest_{s}_eye"], cw[f"crest_{s}_rise"])
    junta["neck_1"] = ponta_perto(cub["neck"], W["neck"], cw["shoulders"])
    junta["head"] = ponta_perto(cub["neck"], W["neck"], cw["skull"])
    base_cauda = cw.get("TorsoHips", cw["hips"])
    junta["tail_1"] = ponta_perto(cub["tail_base"], W["tail_base"], base_cauda)
    for n in modelo.ossos:
        if n.startswith("feather_fan_"):
            leque = [c for c in modelo.cubos if c.osso == n]
            if leque:
                junta[n] = ponta_perto(leque[0], W[leque[0].uuid], cw["tail_base"])
    for n, o in modelo.ossos.items():
        op = {"op": "update_node", "target": o.uuid, "rotation": [0, 0, 0]}
        if n in junta:
            op["origin"] = np.round(junta[n], 4).tolist()
        lote.append(op)
    return lote, W


# ------------------------------------------------------------------ 3: garras
def garras(modelo, W):
    cub = {c.nome: c for c in modelo.cubos}
    lote = []
    for s in ("left", "right"):
        mao = cub[f"hand_{s}"]
        cot = bbmodelo.aplicar(W[f"lower_arm_{s}"], centro(cub[f"lower_arm_{s}"])[None])[0]
        ctr = centro(mao)
        melhor = None
        for eixo in range(3):
            for lado in (0, 1):
                p = ctr.copy()
                p[eixo] = (mao.de, mao.ate)[lado][eixo]
                dist = np.linalg.norm(bbmodelo.aplicar(W[mao.nome], p[None])[0] - cot)
                if melhor is None or dist > melhor[0]:
                    melhor = (dist, eixo, lado)
        _, eixo, lado = melhor
        outros = [e for e in range(3) if e != eixo]
        largo = max(outros, key=lambda e: mao.ate[e] - mao.de[e])
        fino = [e for e in outros if e != largo][0]
        sinal = 1 if lado else -1
        face = (mao.de, mao.ate)[lado][eixo]
        for i, f in enumerate((0.15, 0.5, 0.85)):
            de, ate = np.zeros(3), np.zeros(3)
            pos = mao.de[largo] + f * (mao.ate[largo] - mao.de[largo])
            de[largo], ate[largo] = pos - 0.4, pos + 0.4
            meio = mao.de[fino] + 0.3 * (mao.ate[fino] - mao.de[fino])  # do lado da palma
            de[fino], ate[fino] = meio - 0.4, meio + 0.4
            a, b = face - sinal * 0.3, face + sinal * 2.6
            de[eixo], ate[eixo] = min(a, b), max(a, b)
            lote.append({"op": "add_cube", "name": f"claw_{s}_{i}", "parent": f"forearm_{s}", "from": de.round(4).tolist(),
                         "to": ate.round(4).tolist(), "origin": mao.origem.round(5).tolist(),
                         "rotation": [float(v) for v in mao.rotacao], "box_uv": True})
    return lote


# ------------------------------------------------------------------ 4: pintura
def _norm(face, w):
    n = w[:3, :3] @ np.array(render.NORMAIS[face], float)
    return n / np.linalg.norm(n)


def _plano_uv(c, w, perto, alvo):
    """Eixos do plano (os 2 de tamanho > 0) e, para cada um, de qual lado fica o alvo (0 = lado `de`)."""
    eixos = [e for e in range(3) if c.ate[e] - c.de[e] > 1e-6]
    lados = []
    for e in eixos:
        a, b = centro(c).copy(), centro(c).copy()
        a[e], b[e] = c.de[e], c.ate[e]
        pa, pb = bbmodelo.aplicar(w, np.array([a, b]))
        lados.append(perto(pa, pb, alvo))
    return eixos, lados


def _rel(c, eixos, lados, ponto):
    """Coordenadas (em unidades) a partir da borda escolhida em cada eixo do plano."""
    out = []
    for e, l in zip(eixos, lados):
        v = ponto[e] - c.de[e]
        out.append(v if l == 0 else (c.ate[e] - c.de[e]) - v)
    return out


def asa(tu, vu, W, H, r):
    """Asa pendurada: penas de 2 unidades lado a lado (tu desde o braço), compridas (vu desde o alto);
    as de fora descem mais, ponta em V, borda creme embaixo e na borda de fora, ocelo nas de fora."""
    fileira = int(tu // 2)
    meio = (fileira + 0.5) * 2
    total = H * (0.55 + 0.45 * min(1.0, tu / W)) + 1.2 * (_h(fileira, 9.1) - 0.5)
    ponta = total - 1.6 * abs(tu - meio)
    if vu > ponta:
        return None
    if vu > ponta - 1.6 or tu > W - 1.2:
        return CREME[5] if r > 0.2 else CREME[4]
    if fileira >= 2:
        ex, ey = (tu - meio) / 1.0, (vu - (total - 4.2)) / 1.6
        e = ex * ex + ey * ey
        if e < 0.35:
            return P["oc_navy"]
        if e < 0.8:
            return P["oc_blue"]
        if e < 1.4:
            return P["f_green"] if r > 0.3 else P["f_green_l"]
    if abs(tu - meio) > 0.75:
        return TEAL[2]
    return VERDE[4] if vu > total * 0.55 else (TEAL[4] if r > 0.25 else TEAL[5])


def leque(u, d, r):
    """Pena da cauda: u de 0 (base) a 1 (ponta), d = distância do eixo; haste, folha, ocelo, borda creme."""
    if u < 0 or u > 1:
        return None
    meia = 1.1 if u < 0.35 else 1.1 + 1.25 * math.sin(math.pi * min(1.0, (u - 0.35) / 0.68)) ** 0.7
    if abs(d) > meia + (0.3 if r > 0.6 else 0):
        return None
    e = ((u - 0.78) * 16 / 1.7) ** 2 + (d / 1.25) ** 2
    if e < 0.3:
        return P["oc_navy"]
    if e < 0.65:
        return P["oc_blue"]
    if e < 1.0:
        return P["f_teal"]
    if u < 0.35:
        return P["rachis"] if abs(d) < 0.35 else (TEAL[3] if r > 0.3 else TEAL[2])  # base cheia, cor do corpo
    if d < -meia + 0.8:
        return CREME[4] if r > 0.3 else CREME[3]
    return VERDE[4] if r > 0.35 else VERDE[5]


def pintar(modelo, res):
    W = mundo(modelo)
    cub = {c.nome: c for c in modelo.cubos}
    cw = {n: bbmodelo.aplicar(W[n], centro(cub[n])[None])[0] for n in cub}
    perto = lambda pa, pb, alvo: 0 if np.linalg.norm(pa - alvo) <= np.linalg.norm(pb - alvo) else 1  # noqa: E731
    acima = lambda pa, pb, _: 0 if pa[1] >= pb[1] else 1  # noqa: E731  (lado de cima)
    abaixo = lambda pa, pb, _: 0 if pa[1] <= pb[1] else 1  # noqa: E731
    tex = np.zeros((res, res, 4), np.uint8)
    for c in modelo.cubos:
        w = W[c.uuid]
        plano = any(c.ate[i] - c.de[i] < 1e-6 for i in range(3))
        nome = c.nome
        if plano:
            if nome.startswith(("wing_", "leg_")) and "feather" in nome:
                s = "left" if "left" in nome else "right"
                e_long = int(np.argmax(c.ate - c.de))
                e_lar = [e for e in range(3) if e != e_long and c.ate[e] - c.de[e] > 1e-6][0]
                a_, b_ = centro(c).copy(), centro(c).copy()
                a_[e_long], b_[e_long] = c.de[e_long], c.ate[e_long]
                pa, pb = bbmodelo.aplicar(w, np.array([a_, b_]))
                ombro = cw[f"upper_arm_{s}"] if nome.startswith("wing_") else cw[f"thigh_{s}"]  # onde a pena prende
                base0 = np.linalg.norm(pa - ombro) <= np.linalg.norm(pb - ombro)
                L = c.ate[e_long] - c.de[e_long]
                mid = (c.de[e_lar] + c.ate[e_lar]) / 2
                mm = (c.ate[e_lar] - c.de[e_lar]) / 2
                pinta = lambda p, r, e_long=e_long, e_lar=e_lar, base0=base0, L=L, mid=mid, mm=mm, c=c: pena_crista(
                    ((p[e_long] - c.de[e_long]) if base0 else (c.ate[e_long] - p[e_long])) / L, p[e_lar] - mid, mm, r, L)
            elif nome.startswith("wing"):
                s = "left" if "left" in nome else "right"
                ombro = cw[f"upper_arm_{s}"]
                eixos, _ = _plano_uv(c, w, perto, ombro)
                # o eixo mais vertical no mundo é o comprimento; o outro, a largura (desde o braço)
                vert = [abs((w[:3, :3] @ np.eye(3)[e])[1]) for e in eixos]
                iv = int(np.argmax(vert))
                ordem = [eixos[1 - iv], eixos[iv]]
                _, lado_l = _plano_uv(c, w, perto, ombro)
                lados = {eixos[0]: lado_l[0], eixos[1]: lado_l[1]}
                _, lado_v = _plano_uv(c, w, acima, None)
                lados[eixos[iv]] = lado_v[iv]
                Wd, Hd = c.ate[ordem[0]] - c.de[ordem[0]], c.ate[ordem[1]] - c.de[ordem[1]]
                pinta = lambda p, r, c=c, o=ordem, l=lados, Wd=Wd, Hd=Hd: asa(*_rel(c, o, [l[o[0]], l[o[1]]], p), Wd, Hd, r)
            elif nome.startswith("fan"):
                e_long = int(np.argmax(c.ate - c.de))
                e_lar = [e for e in range(3) if e != e_long and c.ate[e] - c.de[e] > 1e-6][0]
                a_, b_ = centro(c).copy(), centro(c).copy()
                a_[e_long], b_[e_long] = c.de[e_long], c.ate[e_long]
                pa, pb = bbmodelo.aplicar(w, np.array([a_, b_]))
                base0 = np.linalg.norm(pa - cw["tail_base"]) <= np.linalg.norm(pb - cw["tail_base"])
                L = c.ate[e_long] - c.de[e_long]
                mid = (c.de[e_lar] + c.ate[e_lar]) / 2
                pinta = lambda p, r, e_long=e_long, e_lar=e_lar, base0=base0, L=L, mid=mid, c=c: leque(
                    ((p[e_long] - c.de[e_long]) if base0 else (c.ate[e_long] - p[e_long])) / L, p[e_lar] - mid, r)
            else:  # crista
                s = "left" if "left" in nome else "right"
                eixos = [e for e in range(3) if c.ate[e] - c.de[e] > 1e-6]
                vert = [abs((w[:3, :3] @ np.eye(3)[e])[1]) for e in eixos]
                iv = int(np.argmax(vert))
                eh, ev = eixos[1 - iv], eixos[iv]
                ref = cw["skull"] if nome.endswith("rise") else cw[f"crest_{s}_rise"]
                _, lh = _plano_uv(c, w, perto, ref)
                _, lv = _plano_uv(c, w, abaixo, None)
                lado_h, lado_v = lh[eixos.index(eh)], lv[eixos.index(ev)]
                if nome.endswith("rise"):
                    pinta = lambda p, r, c=c, eh=eh, ev=ev, a=lado_h, b=lado_v: g.cor_plano(
                        "crest_x_rise", "north", 0.5 + _rel(c, [eh], [a], p)[0], 32 + _rel(c, [ev], [b], p)[0], 0)
                else:
                    pinta = lambda p, r, c=c, eh=eh, ev=ev, a=lado_h, b=lado_v: g.cor_plano(
                        "crest_x_eye", "north", 3 + _rel(c, [eh], [a], p)[0], 33 + _rel(c, [ev], [b], p)[0], 0)
        for face in ("north", "south", "east", "west", "up", "down"):
            rr = texturizar.texels_da_face(c, face, np.eye(4))
            if rr is None:
                continue
            nmw = _norm(face, w)
            for (u, v), pt in zip(*rr):
                if not (0 <= u < res and 0 <= v < res):
                    continue
                r = _h(*pt)
                if plano:
                    cor = pinta(pt, r)
                else:
                    cor = cor_solido(c, face, pt, bbmodelo.aplicar(w, pt[None])[0], nmw, W, cub, cw, r)
                if isinstance(cor, str):
                    cor = P[cor] if cor in P else g.v3.P[cor]
                if cor is not None:
                    tex[int(v), int(u), :3] = cor
                    tex[int(v), int(u), 3] = 255
    return tex


def _ao_longo(c, w, pt, alvo):
    """Distância (no eixo comprido do cubo) desde a ponta mais perto do alvo."""
    (pa, pb), e = pontas(c, w)
    if np.linalg.norm(pa - alvo) <= np.linalg.norm(pb - alvo):
        return pt[e] - c.de[e]
    return c.ate[e] - pt[e]


OLHO_LADO = ["KKK", "WPA", "AAD"]  # da frente para trás; linha 0 = sobrancelha
COR_OLHO_LADO = {"K": "dark", "W": "white", "P": "pupil", "A": "amber", "D": "amber_dark"}


def escamas(c, w, pt, alvo, r):
    """Pé de ave: placas em anéis ao longo do comprimento (linha escura a cada 2 unidades), brilho de vez em quando."""
    d = _ao_longo(c, w, pt, alvo)
    anel = int(math.floor(d))
    if d - anel < 0.5 and anel % 2 == 0:
        return TEAL[2]
    if r > 0.85:
        return TEAL[4]
    return TEAL[3]


def pena_crista(u, d, meia_max, r, L=12.0):
    """Pena como as da crista: haste azul, barbas azul/teal que viram verde, ocelo perto da ponta."""
    if u < 0 or u > 1:
        return None
    if u < 0.18:
        meia = 0.35 + 0.15 * meia_max
    else:
        meia = min(meia_max, 0.5 + meia_max * math.sin(math.pi * min(1.0, (u - 0.1) / 0.95)) ** 0.7)
    if abs(d) > meia + (0.3 if r > 0.6 else 0):
        return None
    e = ((u - 0.82) * L / (1.3 * meia_max)) ** 2 + (d / (0.62 * meia_max)) ** 2  # ocelo redondo, em unidades
    if e < 0.25:
        return "oc_navy"
    if e < 0.55:
        return "oc_blue"
    if e < 0.95:
        return "f_teal"
    if abs(d) < 0.35 and u < 0.7:
        return "rachis"
    if u < 0.55:
        return "f_blue" if r < 0.55 else "f_teal"
    return "f_green" if r > 0.3 else "f_green_l"


def cor_solido(c, face, pt, pw, nmw, W, cub, cw, r):
    nome = c.nome
    w = W[c.uuid]
    k = sum(map(ord, nome)) + ord(face[0])
    a, b = g._coords(face, *pt)
    if nome.startswith("claw"):
        return P["claw_l"] if r > 0.7 else P["claw"]
    if nome.startswith("toe"):
        s = "left" if "left" in nome else "right"
        if _ao_longo(c, w, pt, cw[f"tarsus_{s}"]) > (c.ate - c.de).max() - 1.1:
            return P["claw"]
        return escamas(c, w, pt, cw[f"tarsus_{s}"], r)
    if nome.startswith("beak"):
        return P["beak_dark"] if nome == "beak_tip" else (P["beak"] if r > 0.15 else P["beak_dark"])
    if nome.startswith("lower_arm"):
        s = "left" if "left" in nome else "right"
        if 0.4 < _ao_longo(c, w, pt, cw[f"hand_{s}"]) < 1.6:
            return P["gold_light"] if r > 0.75 else P["gold"]
    if nome.startswith("tarsus"):
        s = "left" if "left" in nome else "right"
        if 0.3 < _ao_longo(c, w, pt, cw[f"shank_{s}"]) < 1.4:
            return P["gold_light"] if r > 0.75 else P["gold"]
        return escamas(c, w, pt, cw[f"shank_{s}"], r)
    if nome.startswith("hand"):
        s = "left" if "left" in nome else "right"
        return escamas(c, w, pt, cw[f"lower_arm_{s}"], r)
    if nome == "skull":
        de, ate = c.de, c.ate
        y0 = de[1]
        if face in ("east", "west"):
            # olho de ave na lateral, no terço da frente; sobrancelha escura brava por cima
            col = int(math.floor(pt[2] - de[2] - 1.0))  # 0..2 a partir da frente
            lin = int(math.floor(y0 + 4.6 - pt[1]))  # 0 = sobrancelha
            if 0 <= col < 3 and 0 <= lin < 3:
                kk = OLHO_LADO[lin][col]
                if kk != "_":
                    return P[COR_OLHO_LADO[kk]]
        xm = pt[0] - (de[0] + ate[0]) / 2
        if face == "north" and abs(xm) < 1 and pt[1] >= y0 + 3.6:
            return P["gold_light"] if (xm > 0 and pt[1] > y0 + 4.2) else P["gold"]
        if face == "north" and pt[1] < y0 + 1.6:
            return plumagem(CREME, a, b, 0, k, suave=True)
    frente = float(np.dot(nmw, (0, 0, -1)))
    largura = c.ate[0] - c.de[0]
    xm = abs(pt[0] - (c.de[0] + c.ate[0]) / 2)
    if nome in ("torso", "shoulders", "TorsoHips", "hips", "neck") and frente > 0.35 and xm < 0.34 * largura:
        return plumagem(CREME, a, b, (pw[1] - 24) / 16, k, suave=True)
    valor = {"up": 0.8, "down": -1.6}.get(face, 0) if abs(nmw[1]) > 0.7 else (pw[1] - 22) / 14
    if nmw[1] > 0.7:
        valor = 0.8
    elif nmw[1] < -0.7:
        valor = -1.6
    return plumagem(TEAL, a, b, valor, k)  # sem manchas verdes: só a rampa teal


def acertar_uv_da_textura(arquivo: Path, res: int) -> None:
    """O motor não tem operação para uv_width/uv_height da textura, e o update_texture mantém os antigos: com o
    atlas maior (128 → 256) os UVs passavam a ler fora da imagem. Única edição direta do JSON, só desses campos."""
    import json
    dados = json.loads(arquivo.read_text(encoding="utf-8"))
    for t in dados.get("textures", []):
        t["uv_width"], t["uv_height"] = res, res
    arquivo.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")


# ------------------------------------------------------------------ execução
def main():
    hist = AQUI / "historico"
    hist.mkdir(exist_ok=True)
    shutil.copy2(FILE, hist / f"{datetime.now():%Y%m%d-%H%M}-antes-de-finalizar.bbmodel")
    modelo = bbmodelo.ler(FILE)
    antes = mundo(modelo)
    cantos_antes = {c.uuid: bbmodelo.aplicar(antes[c.uuid], np.array([c.de, c.ate])) for c in modelo.cubos}
    # penas de asa feitas a partir de cópias do leque: passam para o osso da asa do lado certo (ossos sem rotação,
    # então mudar o pai não move nada) e ganham nome próprio
    W0 = mundo(modelo)
    mov, n = [], {"left": 0, "right": 0}
    for c in modelo.cubos:
        if c.osso and c.osso.startswith("feather_fan") and c.nome.startswith("fan"):
            p = bbmodelo.aplicar(W0[c.uuid], centro(c)[None])[0]
            if p[2] < 20:
                s = "left" if p[0] < 0 else "right"
                n[s] += 1
                mov.append({"op": "update_node", "target": c.uuid, "parent": f"wing_{s}", "name": f"wing_{s}_feather_{n[s]}"})
    if mov:
        if any(np.any(o.rotacao) for o in modelo.ossos.values()):
            raise SystemExit("há ossos com rotação: achate antes de reparentar")
        motor.editar(FILE, mov)
        print(f"penas de asa reparentadas: {n}")
        modelo = bbmodelo.ler(FILE)
        antes = mundo(modelo)
        cantos_antes = {c.uuid: bbmodelo.aplicar(antes[c.uuid], np.array([c.de, c.ate])) for c in modelo.cubos}
    lote, W = achatar_e_pivotar(modelo)
    motor.editar(FILE, lote)
    modelo = bbmodelo.ler(FILE)
    depois = mundo(modelo)
    erro = max(float(np.abs(bbmodelo.aplicar(depois[c.uuid], np.array([c.de, c.ate])) - cantos_antes[c.uuid]).max())
               for c in modelo.cubos)
    print(f"rig achatado: maior desvio de canto = {erro:.5f} unidade")
    if erro > 0.01:
        raise SystemExit("o achatamento mudou a geometria; abortado (backup em historico/)")
    velhas = [{"op": "remove_node", "target": c.uuid} for c in modelo.cubos if c.nome.startswith("claw_")]
    motor.editar(FILE, velhas + garras(modelo, depois))  # refeitas na posição atual da mão
    modelo = bbmodelo.ler(FILE)
    lista = [{"nome": c.uuid, "from": c.de.tolist(), "to": c.ate.tolist()} for c in modelo.cubos]  # nomes se repetem
    offsets, (res, _) = ops.distribuir_uv(lista, margem=0, larguras=(64, 128, 256))
    motor.editar(FILE, [{"op": "set_model_properties", "resolution": {"width": res, "height": res}}] +
                 [{"op": "update_node", "target": c.uuid, "uv_offset": offsets[c.uuid]} for c in modelo.cubos])
    modelo = bbmodelo.ler(FILE)
    tex = pintar(modelo, res)
    Image.fromarray(tex).save(AQUI / "textura.png")
    # peças com nome repetido: atribuir pela UUID
    texs = modelo.bruto.get("textures") or []
    if texs:
        nome_t = texs[0]["uuid"]
        op_t = {"op": "update_texture", "target": nome_t, "source": texturizar._data_url(tex), "width": res, "height": res,
                "material": None}
    else:
        nome_t = "textura"
        op_t = {"op": "add_texture", "name": nome_t, "source": texturizar._data_url(tex), "width": res, "height": res}
    motor.editar(FILE, [op_t, {"op": "assign_texture", "targets": [c.uuid for c in modelo.cubos], "texture": nome_t}])
    acertar_uv_da_textura(FILE, res)
    info = animar.animar(FILE, "bípede", "meio", quais=("idle", "walk"))
    modelo = bbmodelo.ler(FILE)
    render.folha(modelo, lado_px=360, titulo="Pavão F2 | remodelagem do usuário + textura").save(AQUI / "folha.png")
    geo = motor.resumo_validacao(motor.validar(FILE.resolve()))
    aerr, awarn, amsg = animar.validar_animacoes(FILE)
    print(f"{len(modelo.cubos)} peças, atlas {res}², geometria {geo[0]} erros/{geo[1]} avisos, "
          f"animações {aerr} erros/{awarn} avisos {sorted(info['clipes'])}")
    for m in [*amsg][:6]:
        print("  ", m)


if __name__ == "__main__":
    main()
