"""Vistas ortográficas dos voxels coloridos com esqueleto por cima (diagnóstico, até 768 px)."""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

FUNDO = (236, 238, 242)
# (nome, eixo horizontal, sinal, eixo vertical, sinal, eixo de profundidade, sinal mais perto)
VISTAS = {
    "lado (esquerda)": (2, 1, 1, -1, 0, 1),     # câmera em -X: frente (-Z) à esquerda
    "frente": (0, -1, 1, -1, 2, 1),            # câmera em -Z: esquerda da criatura à direita
    "cima": (0, 1, 2, 1, 1, -1),               # câmera em +Y: frente para cima
}


def projetar(pos, cores, lo, hi, vista, escala):
    h, sh, v, sv, d, sd = VISTAS[vista]
    ext = hi - lo
    w_px = int(ext[h] * escala) + 2
    h_px = int(ext[v] * escala) + 2
    img = np.zeros((h_px, w_px, 3), np.uint8)
    img[:] = FUNDO
    u = ((pos[:, h] - lo[h]) if sh > 0 else (hi[h] - pos[:, h])) * escala
    t = ((pos[:, v] - lo[v]) if sv > 0 else (hi[v] - pos[:, v])) * escala
    prof = pos[:, d] * sd
    r = max(1, int(round(escala * 0.5)))
    ordem = np.argsort(-prof)  # do mais longe ao mais perto
    for k in ordem:
        x0, y0 = int(u[k]), int(t[k])
        img[max(0, y0 - r + 1): y0 + r, max(0, x0 - r + 1): x0 + r] = cores[k]
    return Image.fromarray(img), (lambda p: (((p[h] - lo[h]) if sh > 0 else (hi[h] - p[h])) * escala,
                                             ((p[v] - lo[v]) if sv > 0 else (hi[v] - p[v])) * escala))


def cor_osso(nome):
    if nome.endswith("_left") or "_left" in nome:
        return (40, 110, 230)
    if nome.endswith("_right") or "_right" in nome:
        return (225, 50, 50)
    return (250, 200, 0)


def folha_esqueleto(pos, cores, esq, escala=6.0, titulo=""):
    lo, hi = pos.min(0) - 1, pos.max(0) + 1
    paineis = []
    for vista in VISTAS:
        im, proj = projetar(pos, cores, lo, hi, vista, escala)
        d = ImageDraw.Draw(im)
        for o in esq["ossos"]:
            if o["fim"] is None:
                continue
            a, b = proj(o["pivo"]), proj(o["fim"])
            d.line([a, b], fill=cor_osso(o["nome"]), width=2)
            d.ellipse([a[0] - 3, a[1] - 3, a[0] + 3, a[1] + 3], fill=(20, 20, 20))
        for papel, i in esq["papeis"].items():
            p = proj(esq["pontas"][i]["pos"])
            d.ellipse([p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3], outline=(0, 160, 60), width=2)
            d.text((p[0] + 4, p[1] - 6), papel.replace("acessorio_", "a"), fill=(0, 110, 40))
        d.text((4, 2), vista, fill=(60, 60, 70))
        paineis.append(im)
    larg = paineis[0].width + paineis[1].width + 8
    alt = max(paineis[0].height, paineis[1].height) + paineis[2].height + 8
    folha = Image.new("RGB", (larg, alt), (255, 255, 255))
    folha.paste(paineis[0], (0, 0))
    folha.paste(paineis[1], (paineis[0].width + 8, 0))
    folha.paste(paineis[2], (0, max(paineis[0].height, paineis[1].height) + 8))
    if titulo:
        ImageDraw.Draw(folha).text((paineis[2].width + 16, folha.height - 16), titulo, fill=(60, 60, 70))
    if max(folha.size) > 768:
        f = 768 / max(folha.size)
        folha = folha.resize((int(folha.width * f), int(folha.height * f)), Image.LANCZOS)
    return folha
