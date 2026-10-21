"""Prancha padrão: conceito à esquerda, frente | lado / costas | 3/4 à direita, divisórias cinza e rótulos."""

import numpy as np
from PIL import Image, ImageDraw

from criaturas import prancha

CORES = {"conceito": (200, 40, 40), "frente": (40, 200, 40), "lado": (40, 40, 200), "costas": (200, 200, 40), "3-4": (40, 200, 200)}


def prancha_sintetica(w=1600, h=800) -> Image.Image:
    im = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(im)
    linha = (211, 213, 217)
    caixas = {"conceito": (0, 0, w // 2, h), "frente": (w // 2, 0, 3 * w // 4, h // 2), "lado": (3 * w // 4, 0, w, h // 2),
              "costas": (w // 2, h // 2, 3 * w // 4, h), "3-4": (3 * w // 4, h // 2, w, h)}
    for nome, (x0, y0, x1, y1) in caixas.items():
        cx, cy, r = (x0 + x1) // 2, (y0 + y1) // 2, (x1 - x0) // 5
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=CORES[nome])
        d.text((x0 + 15, y0 + 10), nome, fill=(90, 90, 90))  # rótulo
    for x in (0, w // 2, 3 * w // 4, w - 2):
        d.line((x, 0, x, h), fill=linha, width=2)
    for y in (0, h - 2):
        d.line((0, y, w, y), fill=linha, width=2)
    d.line((w // 2, h // 2, w, h // 2), fill=linha, width=2)
    return im


def test_corta_cinco_quadros_sem_divisorias_nem_rotulos(tmp_path):
    arq = tmp_path / "prancha.png"
    prancha_sintetica().save(arq)
    quadros = prancha.cortar(arq)
    assert set(quadros) == set(prancha.QUADROS)
    for nome, im in quadros.items():
        a = np.asarray(im.convert("RGB")).astype(int)
        # a cor do próprio quadro aparece e a dos vizinhos não
        for outro, cor in CORES.items():
            presente = (np.abs(a - cor).sum(axis=-1) < 30).any()
            assert presente == (outro == nome), (nome, outro)
        assert not prancha._linha(a).all(axis=0).any() and not prancha._linha(a).all(axis=1).any()
        rh, rw = round(a.shape[0] * prancha.ROTULO[1]), round(a.shape[1] * prancha.ROTULO[0])
        assert (a[:rh, :rw] == 255).all()


def test_proporcoes_diferentes(tmp_path):
    arq = tmp_path / "grande.png"
    prancha_sintetica(2400, 1200).save(arq)
    c = prancha.caixas(Image.open(arq))
    assert abs(c["conceito"][2] - 1200) < 6 and abs(c["frente"][3] - 600) < 6 and abs(c["lado"][0] - 1800) < 6
