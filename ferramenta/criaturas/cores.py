"""Cor: sRGB <-> Lab (ΔE) e OKLab/OKLCH (paleta e rampas), e quantização por k-means.

As rampas seguem a ideia de referencia/prototipo-forja/forja/style.py: a sombra puxa o matiz
para o frio, a luz para o quente.
"""

import numpy as np


def _linear(rgb):
    c = np.asarray(rgb, float) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _srgb(lin):
    lin = np.clip(lin, 0, 1)
    c = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)
    return np.clip(np.round(c * 255), 0, 255).astype(np.uint8)


def rgb_para_lab(rgb) -> np.ndarray:
    """CIE Lab (D65), para ΔE76."""
    lin = _linear(rgb)
    m = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = lin @ m.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def delta_e(a, b) -> float:
    return float(np.linalg.norm(rgb_para_lab(a) - rgb_para_lab(b), axis=-1))


_M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566],
                [0.0883024619, 0.2817188376, 0.6299787005]])
_M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099],
                [0.0259040371, 0.7827717662, -0.8086757660]])


def rgb_para_oklab(rgb) -> np.ndarray:
    return np.cbrt(_linear(rgb) @ _M1.T) @ _M2.T


def oklab_para_rgb(lab) -> np.ndarray:
    lms = (np.asarray(lab, float) @ np.linalg.inv(_M2).T) ** 3
    return _srgb(lms @ np.linalg.inv(_M1).T)


def para_hex(rgb) -> str:
    return "#" + "".join(f"{int(v):02x}" for v in rgb[:3])


def de_hex(cor: str) -> np.ndarray:
    cor = cor.lstrip("#")
    return np.array([int(cor[i:i + 2], 16) for i in (0, 2, 4)], np.uint8)


def rampa(rgb, passos: int = 1) -> dict[int, np.ndarray]:
    """{-passos..+passos: rgb}: 0 é a cor; negativo é sombra (mais escura, puxando para o azul), positivo é luz (para o amarelo)."""
    L, a, b = rgb_para_oklab(rgb)
    C, h = np.hypot(a, b), np.arctan2(b, a)
    saida = {0: np.asarray(rgb, np.uint8)}
    frio, quente = np.radians(260), np.radians(80)
    for k in range(1, passos + 1):
        for sinal, alvo, dL in ((-1, frio, -0.075), (1, quente, 0.06)):
            puxar = 0.12 * k * min(1.0, C * 6)  # quase cinza não muda de matiz
            dh = np.arctan2(np.sin(alvo - h), np.cos(alvo - h))
            hh = h + puxar * dh
            CC = C * (0.95 if sinal < 0 else 0.97)
            saida[sinal * k] = oklab_para_rgb([np.clip(L + dL * k, 0, 1), CC * np.cos(hh), CC * np.sin(hh)])
    return saida


def kmeans(pontos: np.ndarray, k: int, iteracoes: int = 25, semente: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """(centros, rótulos). Início pelo ponto mais distante (determinístico)."""
    pontos = np.asarray(pontos, float)
    k = min(k, len(np.unique(pontos.round(4), axis=0)))
    centros = [pontos[np.argmin(np.linalg.norm(pontos - pontos.mean(0), axis=1))]]
    for _ in range(1, k):
        d = np.min(np.linalg.norm(pontos[:, None] - np.array(centros)[None], axis=2), axis=1)
        centros.append(pontos[np.argmax(d)])
    centros = np.array(centros)
    for _ in range(iteracoes):
        rot = np.argmin(np.linalg.norm(pontos[:, None] - centros[None], axis=2), axis=1)
        novos = np.array([pontos[rot == i].mean(0) if np.any(rot == i) else centros[i] for i in range(k)])
        if np.allclose(novos, centros):
            break
        centros = novos
    rot = np.argmin(np.linalg.norm(pontos[:, None] - centros[None], axis=2), axis=1)
    return centros, rot


def paleta(rgbs: np.ndarray, base: int = 5, destaque: int = 2, juntar: float = 0.045) -> tuple[np.ndarray, list[str]]:
    """Paleta de até base + destaque cores. Devolve (cores RGB, papel de cada uma: 'base' ou 'destaque').

    Agrupa em OKLab, junta grupos quase iguais e chama de destaque os grupos menores além das `base` maiores.
    """
    lab = rgb_para_oklab(np.asarray(rgbs, float))
    centros, rot = kmeans(lab, base + destaque)
    contagem = np.bincount(rot, minlength=len(centros)).astype(float)
    # junta centros próximos
    i = 0
    centros, contagem = list(centros), list(contagem)
    while i < len(centros):
        j = i + 1
        while j < len(centros):
            if np.linalg.norm(centros[i] - centros[j]) < juntar:
                total = contagem[i] + contagem[j]
                centros[i] = (centros[i] * contagem[i] + centros[j] * contagem[j]) / total
                contagem[i] = total
                del centros[j], contagem[j]
            else:
                j += 1
        i += 1
    ordem = np.argsort(contagem)[::-1]
    centros = [centros[o] for o in ordem]
    papeis = ["base" if n < base else "destaque" for n in range(len(centros))]
    return np.array([oklab_para_rgb(c) for c in centros]), papeis


def mais_proxima(rgbs: np.ndarray, paleta_rgb: np.ndarray) -> np.ndarray:
    a = rgb_para_oklab(np.asarray(rgbs, float))
    b = rgb_para_oklab(np.asarray(paleta_rgb, float))
    return np.argmin(np.linalg.norm(a[:, None] - b[None], axis=2), axis=1)
