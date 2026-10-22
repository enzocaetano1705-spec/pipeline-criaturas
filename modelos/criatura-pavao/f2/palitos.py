"""Diagrama de palitos do walk, de lado e com câmera fixa: quadril, joelho, tornozelo e dedo de cada perna, mais o
chão. Serve para conferir o passo quadro a quadro (pé plantado no apoio, pé subindo no balanço, corpo sem pular)."""

import importlib.util
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from criaturas import bbmodelo

AQUI = Path(__file__).resolve().parent
_sp = importlib.util.spec_from_file_location("r3", AQUI / "rodada3.py")
r3 = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(r3)
fin = r3.fin


def poses(modelo, clip, n):
    from criaturas import animar
    chaves = animar.assar(clip, modelo)
    for t in np.linspace(0, clip.duracao, n, endpoint=False):
        pose = {}
        for o, cs in chaves.items():
            for canal, k in (("rotation", "rotacao"), ("position", "posicao")):
                if canal in cs:
                    tt = [a for a, _ in cs[canal]]
                    pose.setdefault(o, {})[k] = np.array([np.interp(t, tt, [v[i] for _, v in cs[canal]]) for i in range(3)])
        yield t, pose


def desenhar(modelo, clip, n=12, saida=None, escala=9):
    cor = {"left": (40, 160, 220), "right": (230, 120, 40)}
    quadros = []
    for t, pose in poses(modelo, clip, n):
        mats = bbmodelo.matrizes_ossos(modelo, pose)
        im = Image.new("RGB", (330, 300), "white")
        d = ImageDraw.Draw(im)
        chao = 270
        d.line((0, chao, 330, chao), fill=(120, 120, 120))
        pz = lambda p: (165 + p[2] * escala, chao - p[1] * escala)  # frente (−z) à esquerda  # noqa: E731
        for s in ("right", "left"):
            pts = []
            for osso in (f"leg_{s}", f"shin_{s}", f"foot_{s}"):
                o = modelo.ossos[osso]
                pts.append(bbmodelo.aplicar(mats[osso], o.origem[None])[0])
            dedo = next(c for c in modelo.cubos if c.nome == f"toe_{s}_1")
            (pa, pb), _ = fin.pontas(dedo, bbmodelo.matriz_cubo(modelo, dedo, mats))
            pts.append(min((pa, pb), key=lambda p: p[2]))  # ponta do dedo (à frente)
            d.line([pz(p) for p in pts], fill=cor[s], width=4)
            for p in pts:
                x, y = pz(p)
                d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=cor[s])
        corpo = bbmodelo.aplicar(mats["body"], modelo.ossos["body"].origem[None])[0]
        x, y = pz(corpo)
        d.rectangle((x - 5, y - 5, x + 5, y + 5), outline=(0, 0, 0))
        d.text((6, 6), f"t={t:.2f}s", fill=(0, 0, 0))
        quadros.append(im)
    cols = 6
    out = Image.new("RGB", (330 * cols, 300 * ((len(quadros) + cols - 1) // cols)), "white")
    for i, q in enumerate(quadros):
        out.paste(q, ((i % cols) * 330, (i // cols) * 300))
    if saida:
        out.save(saida)
    return out


if __name__ == "__main__":
    m = bbmodelo.ler(r3.FILE)
    desenhar(m, r3.walk(m), 12, sys.argv[1])
