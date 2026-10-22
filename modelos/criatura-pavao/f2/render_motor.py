"""Renders pelo motor (bb-render), inclusive num instante de uma animação: `vista(view, clip=None, t=0)`.

Uso pela linha de comando: `python render_motor.py saida.png left back three-quarter`
ou `python render_motor.py saida.png --walk left 8` (8 quadros do walk na vista `left`).
"""

import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from criaturas import motor

ARQ = "criatura-pavao/f2/criatura-pavao-e2.bbmodel"  # relativo a modelos/


def vista(view: str, clip: str | None = None, t: float = 0.0, lado: int = 768, arq: str = ARQ) -> Image.Image:
    args = {"file": arq, "view": view, "width": lado, "height": lado, "lighting": "flat"}
    if clip:
        args.update(clip=clip, time=t)
    r = str(motor.chamar("bbmodel_render", args))
    m = re.search(r'"path":"([^"]+\.png)"', r)
    if not m:
        raise RuntimeError(r[:300])
    return Image.open(json.loads(f'"{m.group(1)}"')).convert("RGB")


def faixa(ims: list[Image.Image], rotulos: list[str], lado: int = 400) -> Image.Image:
    out = Image.new("RGB", (lado * len(ims), lado + 22), "white")
    d = ImageDraw.Draw(out)
    for i, (im, r) in enumerate(zip(ims, rotulos)):
        out.paste(im.resize((lado, lado)), (i * lado, 22))
        d.text((i * lado + 6, 4), r, fill=(40, 40, 40))
    return out


if __name__ == "__main__":
    saida, *resto = sys.argv[1:]
    if resto and resto[0] == "--walk":
        view, n = resto[1], int(resto[2])
        dur = float(resto[3]) if len(resto) > 3 else 1.2
        ts = [round(dur * i / n, 3) for i in range(n)]
        img = faixa([vista(view, "walk", t, 512) for t in ts], [f"walk t={t:.2f}s" for t in ts], 300)
    else:
        img = faixa([vista(v, lado=1024) for v in resto], resto, 700)
    img.save(saida)
    print(saida)
