"""Pálpebras da preguiça para piscar sem escala (o Roblox não anima escala de osso).

Os olhos estão pintados nas laterais do focinho (cubo head_2: face east = olho direito, west = olho
esquerdo). Cada olho ganha duas tiras de pálpebra escondidas RECUO atrás da face do focinho, no mesmo
referencial do cubo (mesma rotação e origem), cada uma no seu osso (filhos de head):
  - eyelid_<lado>: tira de cima (linhas 2-5 da face), pele por cima do olho e, embaixo, a borda escura
    da pálpebra;
  - eyelid_<lado>_lower: tira de baixo (linhas 6-7), pele cobrindo o resto do olho.
A piscada empurra os ossos para fora pela posição (DESLOCA): só a de cima = olho meio fechado; as duas
= fechado. Mostradas, as tiras ficam SAIDA à frente da face, na mesma altura (sem degrau nem borda
aparecendo). A textura delas é feita com os próprios pixels do olho (pele no lugar da íris) e vai para
um canto livre do atlas, com margem; nenhum pixel já usado muda. Olho direito e esquerdo dividem o
mesmo pedaço (um usa a face east, o outro a west).

Uso: uv run python scripts/fera-animacao/palpebras.py <entrada.bbmodel> <saida.bbmodel>
"""

from __future__ import annotations

import base64
import io
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

from criaturas import bbmodelo, motor

CUBO = "head_2"
# As tiras passam um pixel além do contorno do olho (largura toda da face, duas linhas a mais embaixo):
# pela fresta entre a tira mostrada e a face só aparece pele igual à da tira, nunca o contorno escuro.
COLUNAS = (0, 7)  # colunas da face cobertas pelas tiras (pixels)
CIMA = (2, 5)  # linhas da tira de cima (a última é a borda da pálpebra)
BAIXO = (6, 9)  # linhas da tira de baixo
Z_FOLGA = 0.05  # recua as tiras para trás: a ponta não fica no plano da frente do focinho
ESPESSURA = 1.0
RECUO, SAIDA = 0.4, 0.06  # escondida bem atrás da face (sem briga de profundidade); mostrada, rente a ela
DESLOCA = RECUO + SAIDA  # deslocamento do osso para fora ao mostrar a tira
OSSOS = {"upper": "eyelid_{lado}", "lower": "eyelid_{lado}_lower"}


def _px_face(tex, uv, k):
    u1, v1, u2, v2 = uv
    x0, y0, x1, y1 = int(round(min(u1, u2) * k)), int(round(min(v1, v2) * k)), int(round(max(u1, u2) * k)), int(round(max(v1, v2) * k))
    return np.asarray(tex)[y0:y1, x0:x1].copy()


def _desenho(face):
    """(tira de cima, tira de baixo, cores do olho) a partir dos pixels da face com o olho."""
    cor = lambda p: tuple(int(x) for x in p)  # noqa: E731
    H = face.shape[0]
    fora = {cor(face[r, c]) for r in list(range(0, 2)) + list(range(8, H)) for c in range(face.shape[1])}
    dentro = Counter(cor(face[r, c]) for r in range(3, 8) for c in range(face.shape[1]))
    olho = {c for c in dentro if c not in fora}
    contorno = max(olho, key=lambda c: dentro[c])  # a cor do olho mais frequente é o contorno escuro
    iris = olho - {contorno}
    claras = Counter(cor(face[r, c]) for r in range(H) for c in range(face.shape[1]) if int(face[r, c][:3].astype(int).sum()) > 450)
    pele = max(claras, key=claras.get)
    c0, c1 = COLUNAS
    for r in range(H):
        for c in range(face.shape[1]):
            if cor(face[r, c]) in iris and not (c0 <= c <= c1 and CIMA[0] < r <= BAIXO[1]):
                raise SystemExit(f"pixel da íris fora das tiras: linha {r}, coluna {c}")
    cima = face[CIMA[0]:CIMA[1] + 1, c0:c1 + 1].copy()
    baixo = face[BAIXO[0]:BAIXO[1] + 1, c0:c1 + 1].copy()
    for t in (cima, baixo):
        for idx in np.ndindex(t.shape[:2]):
            if cor(t[idx]) in olho:
                t[idx] = pele
    cima[-1, :] = contorno  # borda da pálpebra
    return cima, baixo, {"pele": pele, "contorno": contorno, "iris": sorted(iris)}


def _ocupacao(raw, res):
    occ = np.zeros((res[1], res[0]), bool)
    for e in raw["elements"]:
        for f in (e.get("faces") or {}).values():
            uv = f.get("uv")
            if not uv:
                continue
            u0, u1 = sorted((uv[0], uv[2]))
            v0, v1 = sorted((uv[1], uv[3]))
            occ[int(np.floor(v0)):int(np.ceil(v1)), int(np.floor(u0)):int(np.ceil(u1))] = True
    return occ


def _livre(occ, alfa, k, w, h, margem=1):
    """Canto do atlas sem face nenhuma (com margem); de preferência ainda transparente."""
    H, W = occ.shape
    for exigir_vazio in (True, False):
        for v in range(margem, H - h - margem):
            for u in range(margem, W - w - margem):
                if occ[v - margem:v + h + margem, u - margem:u + w + margem].any():
                    continue
                if exigir_vazio and alfa[int((v - margem) * k):int((v + h + margem) * k), int((u - margem) * k):int((u + w + margem) * k)].any():
                    continue
                return u, v
    raise SystemExit("sem espaço livre no atlas")


def _layout(u, v, w, h, d):
    """Retângulos da UV de caixa (Bedrock/Blockbench) de um cubo w×h×d com offset (u, v)."""
    return {"east": (u, v + d, u + d, v + d + h), "north": (u + d, v + d, u + d + w, v + d + h),
            "west": (u + d + w, v + d, u + 2 * d + w, v + d + h), "south": (u + 2 * d + w, v + d, u + 2 * d + 2 * w, v + d + h),
            "up": (u + d, v, u + d + w, v + d), "down": (u + d + w, v, u + d + 2 * w, v + d)}


def _dentro(cubo, ponto, folga=1e-6):
    """O ponto (no espaço do modelo, pose de repouso) está dentro do cubo?"""
    R = bbmodelo.matriz_rotacao(cubo.rotacao)
    local = R.T @ (np.asarray(ponto, float) - cubo.origem) + cubo.origem
    return bool(np.all(local >= cubo.de - folga) and np.all(local <= cubo.ate + folga))


def _pintar(img, ret, k, pixels=None, cor=None):
    x0, y0, x1, y1 = (int(round(a * k)) for a in ret)
    if pixels is not None:
        assert pixels.shape[:2] == (y1 - y0, x1 - x0), (pixels.shape, ret)
        img[y0:y1, x0:x1] = pixels
    else:
        img[y0:y1, x0:x1] = cor


def main():
    entrada, saida = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    if saida.exists():
        raise SystemExit(f"{saida} já existe")
    m = bbmodelo.ler(entrada)
    raw = json.loads(entrada.read_text(encoding="utf-8"))
    if any(o.startswith("eyelid_") for o in m.ossos):
        raise SystemExit("o modelo já tem pálpebras")
    cubo = m.cubo(CUBO)
    tex = m.textura
    k = tex.size[0] / m.resolucao[0]  # pixels por unidade de UV (= por unidade do modelo, UV de caixa)
    de, ate = cubo.de, cubo.ate
    desenhos, faces = {}, {}
    for lado, face in (("right", "east"), ("left", "west")):
        faces[lado] = _px_face(tex, cubo.faces[face]["uv"], k)
        desenhos[lado] = _desenho(faces[lado])
    c0, c1 = COLUNAS
    z_east = (ate[2] - (c1 + 1) / k, ate[2] - c0 / k)  # east: coluna 0 da UV fica atrás (+Z)
    z_west = (de[2] + c0 / k, de[2] + (c1 + 1) / k)  # west: coluna 0 fica na frente (-Z)
    assert np.allclose(z_east, z_west), (z_east, z_west)
    z_east = (z_east[0] + Z_FOLGA, z_east[1] + Z_FOLGA)
    y_cima = (ate[1] - (CIMA[1] + 1) / k, ate[1] - CIMA[0] / k)
    y_baixo = (ate[1] - (BAIXO[1] + 1) / k, ate[1] - BAIXO[0] / k)
    d = z_east[1] - z_east[0]
    h_cima, h_baixo = y_cima[1] - y_cima[0], y_baixo[1] - y_baixo[0]
    for t in (d, h_cima, h_baixo, ESPESSURA):
        assert abs(t - round(t)) < 1e-9, "a UV de caixa precisa de medidas inteiras"
    w, d, h_cima, h_baixo = int(ESPESSURA), int(round(d)), int(round(h_cima)), int(round(h_baixo))

    occ = _ocupacao(raw, m.resolucao)
    img = np.asarray(tex).copy()
    alfa = img[..., 3] > 0
    u, v = _livre(occ, alfa, k, 2 * d + 2 * w, d + h_cima + d + h_baixo)
    uv_cima, uv_baixo = (u, v), (u, v + d + h_cima)
    for (uu, vv), h, parte in ((uv_cima, h_cima, 0), (uv_baixo, h_baixo, 1)):
        L = _layout(uu, vv, w, h, d)
        dr, dl = desenhos["right"][parte], desenhos["left"][parte]
        _pintar(img, L["east"], k, dr)
        _pintar(img, L["west"], k, dl)
        # bordas transparentes (como os planos de pelo): mostrada, a tira é só a face sobre o olho, sem
        # filete de borda pegando luz
        for f in ("north", "south", "up", "down"):
            _pintar(img, L[f], k, cor=np.zeros(4, np.uint8))

    # osso no centro do olho, sobre a face (pivô não importa para translação, mas fica no lugar certo)
    M = bbmodelo.matriz_rotacao(cubo.rotacao)
    zc, yc = (z_east[0] + z_east[1]) / 2, (y_cima[1] + y_baixo[0]) / 2
    grupos = {g["name"]: g["uuid"] for g in raw["groups"]}
    ops = []
    for lado, x_face, sinal in (("right", ate[0], 1.0), ("left", de[0], -1.0)):
        p = np.array([x_face, yc, zc])
        piv = cubo.origem + M @ (p - cubo.origem)
        for nome, (y0, y1), uvo in (("upper", y_cima, uv_cima), ("lower", y_baixo, uv_baixo)):
            osso = OSSOS[nome].format(lado=lado)
            ops.append({"op": "add_group", "name": osso, "origin": [round(float(a), 4) for a in piv], "parent": grupos["head"]})
            frente = x_face - sinal * RECUO
            xs = sorted((frente, frente - sinal * ESPESSURA))
            ops.append({"op": "add_cube", "name": f"eyelid_{lado}_{nome}_lid", "parent": osso,
                        "from": [round(xs[0], 4), round(y0, 4), round(z_east[0], 4)],
                        "to": [round(xs[1], 4), round(y1, 4), round(z_east[1], 4)],
                        "origin": [float(a) for a in cubo.origem], "rotation": [float(a) for a in cubo.rotacao],
                        "box_uv": True, "uv_offset": list(uvo), "texture": 0})
    buf = io.BytesIO()
    Image.fromarray(img, "RGBA").save(buf, "PNG")
    ops.append({"op": "update_texture", "target": 0, "source": "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(),
                "width": int(img.shape[1]), "height": int(img.shape[0])})
    saida.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(entrada, saida)
    motor.editar(saida, ops)

    # conferências: UV calculada pelo motor = a que foi pintada; tiras escondidas dentro do focinho
    novo = bbmodelo.ler(saida)
    for lado in ("right", "left"):
        for nome, uvo, h in (("upper", uv_cima, h_cima), ("lower", uv_baixo, h_baixo)):
            c = novo.cubo(f"eyelid_{lado}_{nome}_lid")
            L = _layout(uvo[0], uvo[1], w, h, d)
            for f in ("east", "west"):
                uvf = c.faces[f]["uv"]
                ret = (min(uvf[0], uvf[2]), min(uvf[1], uvf[3]), max(uvf[0], uvf[2]), max(uvf[1], uvf[3]))
                assert np.allclose(ret, L[f]), (c.nome, f, uvf, L[f])
            # escondida: cada canto dentro do focinho ou do crânio (a ponta de trás entra no crânio)
            cantos = np.array([[x, y, z] for x in (c.de[0], c.ate[0]) for y in (c.de[1], c.ate[1]) for z in (c.de[2], c.ate[2])])
            mundo = (cantos - c.origem) @ bbmodelo.matriz_rotacao(c.rotacao).T + c.origem
            for q in mundo:
                assert any(_dentro(novo.cubo(n), q) for n in (CUBO, "head")), f"{c.nome}: canto {q.round(2)} aparece"
    antes = np.asarray(tex)
    depois = np.asarray(novo.textura)
    mudou = np.argwhere(np.any(antes != depois, axis=-1))
    assert not any(occ[int(y / k), int(x / k)] for y, x in mudou), "pintou pixel de face existente"
    rel = {"uv_tira_cima": list(uv_cima), "uv_tira_baixo": list(uv_baixo), "pixels_novos": int(len(mudou)),
           "desloca": DESLOCA, "cores": {k2: [list(c) for c in v2] if k2 == "iris" else list(v2) for k2, v2 in desenhos["right"][2].items()}}
    print(json.dumps(rel, ensure_ascii=False))


if __name__ == "__main__":
    main()
