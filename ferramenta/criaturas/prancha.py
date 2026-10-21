"""Prancha padrão do usuário: uma imagem com o conceito à esquerda e frente, lado, costas e 3/4 numa grade 2×2 à direita.

As divisórias são linhas cinza-claras (~#d3d5d9). Localizamos as linhas; se não acharmos, usamos as proporções do
padrão (conceito = metade esquerda). O rótulo no canto superior esquerdo de cada quadro é apagado.
"""

from pathlib import Path

import numpy as np
from PIL import Image

# ordem do padrão: conceito à esquerda; à direita, linha de cima frente | lado, linha de baixo costas | 3/4
QUADROS = ("conceito", "frente", "lado", "costas", "3-4")
ROTULO = (0.30, 0.10)  # fração (largura, altura) do quadro apagada no canto superior esquerdo


def _linha(a: np.ndarray) -> np.ndarray:
    """Pixels da cor das divisórias: cinza claro, pouca saturação."""
    mx, mn = a.max(axis=-1), a.min(axis=-1)
    return (mn >= 185) & (mx <= 232) & (mx - mn <= 14)


def _divisorias(frac: np.ndarray, minimo: float) -> list[int]:
    """Centros das faixas contínuas acima de `minimo` (uma linha de 2–3 px vira um índice)."""
    idx = np.flatnonzero(frac >= minimo)
    grupos, atual = [], []
    for i in idx:
        if atual and i != atual[-1] + 1:
            grupos.append(atual)
            atual = []
        atual.append(int(i))
    if atual:
        grupos.append(atual)
    return [(g[0] + g[-1]) // 2 for g in grupos]


def _perto(valores: list[int], alvo: float, tol: float) -> int | None:
    melhores = [v for v in valores if abs(v - alvo) <= tol]
    return min(melhores, key=lambda v: abs(v - alvo)) if melhores else None


def caixas(im: Image.Image) -> dict[str, tuple[int, int, int, int]]:
    """(x0, y0, x1, y1) de cada quadro, sem as divisórias."""
    a = np.asarray(im.convert("RGB")).astype(int)
    h, w = a.shape[:2]
    m = _linha(a)
    xs = _divisorias(m.mean(axis=0), 0.85)
    xm = _perto(xs, w / 2, w * 0.08) or w // 2
    direita = m[:, xm + 3:]
    xd = _perto(_divisorias(direita[: h // 2].mean(axis=0), 0.85), (w - xm) / 2, w * 0.06)
    xd = xm + 3 + xd if xd is not None else (xm + w) // 2
    yd = _perto(_divisorias(direita.mean(axis=1), 0.85), h / 2, h * 0.08) or h // 2
    b = 3  # margem para tirar a própria linha e o borrão de compressão
    return {
        "conceito": (b, b, xm - b, h - b),
        "frente": (xm + b, b, xd - b, yd - b),
        "lado": (xd + b, b, w - b, yd - b),
        "costas": (xm + b, yd + b, xd - b, h - b),
        "3-4": (xd + b, yd + b, w - b, h - b),
    }


def cortar(origem: Path | str) -> dict[str, Image.Image]:
    with Image.open(origem) as im:
        im = im.convert("RGB")
        saida = {}
        for nome, caixa in caixas(im).items():
            q = im.crop(caixa).convert("RGBA")
            a = np.array(q)
            rh, rw = round(a.shape[0] * ROTULO[1]), round(a.shape[1] * ROTULO[0])
            a[:rh, :rw, :3] = 255
            saida[nome] = Image.fromarray(a)
        return saida
