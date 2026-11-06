"""Folha de comparação: render da malha original (Blender) × render do .bbmodel (motor Blockbench).

Uso: uv run python scripts/malha-para-cubos/comparar.py <pasta> <arquivo.bbmodel> <png malha lado> <png malha 3/4>
Grava <pasta>/comparacao.png (até 768 px).
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw

from criaturas import motor


def caber(im, lado):
    im = im.convert("RGBA")
    bbox = im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox() if im.mode == "RGBA" else None
    if bbox:
        im = im.crop(bbox)
    f = lado / max(im.size)
    im = im.resize((max(1, int(im.width * f)), max(1, int(im.height * f))), Image.LANCZOS)
    fundo = Image.new("RGB", (lado, lado), (240, 241, 245))
    fundo.paste(im, ((lado - im.width) // 2, (lado - im.height) // 2), im)
    return fundo


def main():
    gerar(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), sys.argv[3], sys.argv[4])


def gerar(pasta, arquivo, png_lado, png_34):
    malha_lado, malha_34 = Image.open(png_lado), Image.open(png_34)
    vistas = motor.folha_de_contato(arquivo)
    lado = 380
    paineis = [("malha: lado", malha_lado), ("cubos: lado", Image.open(vistas["left"])),
               ("malha: 3/4", malha_34), ("cubos: 3/4", Image.open(vistas["three-quarter"]))]
    folha = Image.new("RGB", (lado * 2 + 8, lado * 2 + 8), (255, 255, 255))
    d = ImageDraw.Draw(folha)
    for k, (titulo, im) in enumerate(paineis):
        x, y = (k % 2) * (lado + 8), (k // 2) * (lado + 8)
        folha.paste(caber(im, lado), (x, y))
        d.text((x + 6, y + 4), titulo, fill=(60, 60, 70))
    folha = folha.resize((768, 768), Image.LANCZOS)
    folha.save(pasta / "comparacao.png")
    print(f"comparação: {pasta / 'comparacao.png'}")


if __name__ == "__main__":
    main()
