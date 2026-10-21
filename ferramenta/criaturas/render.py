"""Renderizador por software (numpy + Pillow) de .bbmodel: vistas ortográficas sem GPU.

Porte da ideia de referencia/prototipo-forja/forja/render.py, lendo .bbmodel 5.0.
Serve para as imagens de teste das sintéticas e como reserva da folha de vistas.

Vistas (frente da criatura em -Z, lado esquerdo em -X):
  frente  câmera em -Z; o lado esquerdo da criatura aparece à direita da imagem
  lado    câmera em -X (lado esquerdo); a frente da criatura aparece à esquerda da imagem
  costas  câmera em +Z
  direita câmera em +X
  3/4     azimute 35°, elevação 20°, a partir da frente
"""

from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw

from criaturas import bbmodelo

FUNDO = (255, 255, 255)
COR_PADRAO = (170, 170, 178)
LUZ = np.array([0.3, 0.9, -0.6]) / np.linalg.norm([0.3, 0.9, -0.6])

# nome -> (azimute, elevação) em graus; azimute 0 olha a frente (-Z), 90 olha o lado esquerdo (-X)
VISTAS = {"frente": (0, 0), "lado": (90, 0), "costas": (180, 0), "direita": (270, 0), "3/4": (35, 20)}
FOLHA = ("frente", "lado", "costas", "3/4")

# cantos de cada face vistos de fora: [sup. esq., sup. dir., inf. esq., inf. dir.] com (x0|x1, y0|y1, z0|z1).
# Conferido na Fase 5 contra o render do motor: 97–100% de concordância nas faces laterais e no topo.
CANTOS_FACE = {
    "north": ((1, 1, 0), (0, 1, 0), (1, 0, 0), (0, 0, 0)),
    "south": ((0, 1, 1), (1, 1, 1), (0, 0, 1), (1, 0, 1)),
    "east": ((1, 1, 1), (1, 1, 0), (1, 0, 1), (1, 0, 0)),
    "west": ((0, 1, 0), (0, 1, 1), (0, 0, 0), (0, 0, 1)),
    "up": ((0, 1, 0), (1, 1, 0), (0, 1, 1), (1, 1, 1)),
    "down": ((1, 0, 0), (0, 0, 0), (1, 0, 1), (0, 0, 1)),
}
NORMAIS = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0)}


@dataclass
class Projecao:
    """Ortográfica: pixel = ((p·direita) - min_d)·escala + margem, ((max_c - p·cima))·escala + margem."""
    direita: np.ndarray
    cima: np.ndarray
    frente: np.ndarray
    escala: float
    min_d: float
    max_c: float
    margem: int
    tamanho: tuple[int, int]

    def pixel(self, pontos) -> np.ndarray:
        p = np.atleast_2d(np.asarray(pontos, float))
        x = (p @ self.direita - self.min_d) * self.escala + self.margem
        y = (self.max_c - p @ self.cima) * self.escala + self.margem
        return np.stack([x, y], 1)


def camera(azimute: float, elevacao: float):
    """(frente, direita, cima) da câmera; frente aponta da câmera para o modelo."""
    a, e = np.radians(azimute), np.radians(elevacao)
    posicao = np.array([-np.sin(a) * np.cos(e), np.sin(e), -np.cos(a) * np.cos(e)])
    f = -posicao
    up = np.array([0.0, 1.0, 0.0])
    r = np.cross(f, up)
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return f, r, u


def _hex(cor: str) -> tuple[int, int, int]:
    cor = cor.lstrip("#")
    return tuple(int(cor[i:i + 2], 16) for i in (0, 2, 4))


def _quads(modelo, mats):
    for cubo in modelo.cubos:
        m = bbmodelo.matriz_cubo(modelo, cubo, mats)
        a, b = cubo.de - cubo.inflate, cubo.ate + cubo.inflate
        lim = np.stack([a, b])
        for face, cantos in CANTOS_FACE.items():
            pts = np.array([[lim[i, 0], lim[j, 1], lim[k, 2]] for i, j, k in cantos])
            pw = bbmodelo.aplicar(m, pts)
            if np.linalg.norm(np.cross(pw[1] - pw[0], pw[2] - pw[0])) < 1e-9:
                continue  # face de área zero (planos têm só as duas faces largas)
            n = m[:3, :3] @ np.array(NORMAIS[face], float)
            yield cubo, face, pw, n / np.linalg.norm(n)


def _triangulo(img, zb, p, z, cor_fn, ids, ident):
    h, w = zb.shape
    x0, x1 = max(int(np.floor(p[:, 0].min())), 0), min(int(np.ceil(p[:, 0].max())), w - 1)
    y0, y1 = max(int(np.floor(p[:, 1].min())), 0), min(int(np.ceil(p[:, 1].max())), h - 1)
    if x0 > x1 or y0 > y1:
        return
    X, Y = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    (ax, ay), (bx, by), (cx, cy) = p
    den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    if abs(den) < 1e-12:
        return
    w0 = ((by - cy) * (X - cx) + (cx - bx) * (Y - cy)) / den
    w1 = ((cy - ay) * (X - cx) + (ax - cx) * (Y - cy)) / den
    w2 = 1 - w0 - w1
    dentro = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
    zz = w0 * z[0] + w1 * z[1] + w2 * z[2]
    sub = zb[y0:y1 + 1, x0:x1 + 1]
    m = dentro & (zz < sub - 1e-6)
    if not m.any():
        return
    cor, alfa = cor_fn(w0, w1, w2)
    m &= alfa
    sub[m] = zz[m]
    img[y0:y1 + 1, x0:x1 + 1][m] = cor[m]
    ids[y0:y1 + 1, x0:x1 + 1][m] = ident


def renderizar(modelo: bbmodelo.Modelo, vista: str = "frente", *, escala: float = 16.0, margem: int = 8,
               cores: dict[str, str] | None = None, usar_textura: bool = True, sombreado: float = 0.25,
               mats=None, limites=None, fundo=FUNDO, projecao: "Projecao | None" = None):
    """Renderiza uma vista. Devolve (imagem RGB, máscara bool, ids de cubo por pixel, Projecao).

    `escala` em pixels por unidade. `cores` = {nome do cubo: '#rrggbb'}; sem cor nem textura usa cinza.
    `limites` = (min, max) em mundo, para enquadrar várias vistas ou poses na mesma escala.
    `projecao` fixa o enquadramento (para casar pixel a pixel com uma imagem do conceito).
    """
    mats = mats if mats is not None else bbmodelo.matrizes_ossos(modelo)
    if projecao is not None:
        proj = projecao
        f, r, u = proj.frente, proj.direita, proj.cima
        largura, altura = proj.tamanho
    else:
        azimute, elevacao = VISTAS[vista] if isinstance(vista, str) else vista
        f, r, u = camera(azimute, elevacao)
        lo, hi = limites if limites is not None else bbmodelo.limites(modelo, mats)
        cantos = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
        min_d, max_d = (cantos @ r).min(), (cantos @ r).max()
        min_c, max_c = (cantos @ u).min(), (cantos @ u).max()
        largura = int(np.ceil((max_d - min_d) * escala)) + 2 * margem
        altura = int(np.ceil((max_c - min_c) * escala)) + 2 * margem
        proj = Projecao(r, u, f, escala, min_d, max_c, margem, (largura, altura))

    img = np.zeros((altura, largura, 3), float)
    img[:] = fundo
    zb = np.full((altura, largura), np.inf)
    ids = np.full((altura, largura), -1, int)
    tex = np.asarray(modelo.textura, float) if (usar_textura and modelo.textura is not None) else None
    res_u, res_v = modelo.resolucao
    indice = {c.uuid: i for i, c in enumerate(modelo.cubos)}

    for cubo, face, pw, n in _quads(modelo, mats):
        if n @ f > -1e-6:
            continue
        luz = (1 - sombreado) + sombreado * max(0.0, float(n @ LUZ))
        sp = proj.pixel(pw)
        dz = pw @ f
        uv_face = cubo.faces.get(face, {}).get("uv")
        if tex is not None and uv_face is not None:
            u1, v1, u2, v2 = uv_face
            sx, sy = tex.shape[1] / res_u, tex.shape[0] / res_v
            uvs = np.array([[u1, v1], [u2, v1], [u1, v2], [u2, v2]], float) * [sx, sy]
        else:
            uvs = None
            rgb = np.array(_hex(cores[cubo.nome]) if cores and cubo.nome in cores else COR_PADRAO, float) * luz
        for tri in ((0, 2, 1), (2, 3, 1)):
            if uvs is not None:
                t = uvs[list(tri)]

                def cor_fn(w0, w1, w2, t=t, luz=luz):
                    uu = w0 * t[0, 0] + w1 * t[1, 0] + w2 * t[2, 0]
                    vv = w0 * t[0, 1] + w1 * t[1, 1] + w2 * t[2, 1]
                    tx = np.clip(np.floor(uu).astype(int), 0, tex.shape[1] - 1)
                    ty = np.clip(np.floor(vv).astype(int), 0, tex.shape[0] - 1)
                    amostra = tex[ty, tx]
                    return amostra[..., :3] * luz, amostra[..., 3] > 127
            else:
                def cor_fn(w0, w1, w2, rgb=rgb):
                    cor = np.empty(w0.shape + (3,))
                    cor[:] = rgb
                    return cor, np.ones(w0.shape, bool)
            _triangulo(img, zb, sp[list(tri)], dz[list(tri)], cor_fn, ids, indice[cubo.uuid])

    mascara = np.isfinite(zb)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)), mascara, ids, proj


def folha(modelo: bbmodelo.Modelo, *, lado_px: int = 384, cores=None, titulo: str | None = None,
          vistas=FOLHA, mats=None) -> Image.Image:
    """Folha 2×2 com as vistas na mesma escala; até 768 px com lado_px=384."""
    mats = mats if mats is not None else bbmodelo.matrizes_ossos(modelo)
    lo, hi = bbmodelo.limites(modelo, mats)
    raio = float(np.linalg.norm(hi - lo))
    escala = (lado_px - 24) / max(raio, 1.0)
    folha_img = Image.new("RGB", (lado_px * 2, lado_px * 2), FUNDO)
    d = ImageDraw.Draw(folha_img)
    for k, vista in enumerate(vistas):
        im, _, _, _ = renderizar(modelo, vista, escala=escala, cores=cores, mats=mats, limites=(lo, hi))
        x, y = (k % 2) * lado_px, (k // 2) * lado_px
        folha_img.paste(im, (x + (lado_px - im.width) // 2, y + (lado_px - im.height) // 2))
        d.text((x + 6, y + 4), vista, fill=(80, 84, 96))
    d.line([(lado_px, 0), (lado_px, 2 * lado_px)], fill=(214, 216, 222))
    d.line([(0, lado_px), (2 * lado_px, lado_px)], fill=(214, 216, 222))
    if titulo:
        d.text((6, 2 * lado_px - 14), titulo, fill=(80, 84, 96))
    return folha_img
