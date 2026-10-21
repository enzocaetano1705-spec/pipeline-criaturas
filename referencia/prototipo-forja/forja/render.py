"""Tiny software renderer (numpy + Pillow) so the agent can *see* the model.
It uses the exact face/UV conventions of the exporter, so what it shows is what
Blockbench shows. No GPU, no Blender needed."""
import numpy as np
from PIL import Image, ImageDraw

from .mathutil import apply
from .texture import FACES, NORMALS, face_corners

BG = np.array([226, 230, 236], float)
VIEWS = [("3/4", 35, 22), ("frente", 0, 0), ("lado", 90, 0), ("topo", 0, 90)]
LIGHT = np.array([0.35, 1.0, -0.55]) / np.linalg.norm([0.35, 1.0, -0.55])


def camera(yaw, pitch):
    y, p = np.radians(yaw), np.radians(pitch)
    c = np.array([np.cos(p) * np.sin(y), np.sin(p), -np.cos(p) * np.cos(y)])
    f = -c
    up = np.array([0.0, 1.0, 0.0]) if abs(f[1]) < 0.99 else np.array([0.0, 0.0, -1.0])
    r = np.cross(f, up)
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return f, r, u


def _quads(model, tex, mats):
    out = []
    for b in model.boxes:
        w = model.box_matrix(b, mats)
        f, t = b.frm - b.inflate, b.to + b.inflate
        for key in FACES:
            rect = tex.rects.get((b.uuid, key))
            if rect is None:
                continue
            c = apply(w, face_corners(f, t, key))
            n = w[:3, :3] @ np.array(NORMALS[key], float)
            nl = np.linalg.norm(n)
            out.append((c, n / (nl if nl > 1e-9 else 1), rect))
    return out


def _bounds(model, mats_list):
    pts = []
    for mats in mats_list:
        for b in model.boxes:
            pts.append(model.corners(b, mats))
    pts = np.concatenate(pts)
    ctr = (pts.min(0) + pts.max(0)) / 2
    rad = np.linalg.norm(pts - ctr, axis=1).max()
    return ctr, max(rad, 1.0)


def _tri(img, zb, p, z, uv, tex, rect, shade):
    hh, ww = zb.shape
    xmin, xmax = max(int(np.floor(p[:, 0].min())), 0), min(int(np.ceil(p[:, 0].max())), ww - 1)
    ymin, ymax = max(int(np.floor(p[:, 1].min())), 0), min(int(np.ceil(p[:, 1].max())), hh - 1)
    if xmin > xmax or ymin > ymax:
        return
    xs = np.arange(xmin, xmax + 1) + 0.5
    ys = np.arange(ymin, ymax + 1) + 0.5
    X, Y = np.meshgrid(xs, ys)
    (x0, y0), (x1, y1), (x2, y2) = p
    den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if abs(den) < 1e-9:
        return
    w0 = ((y1 - y2) * (X - x2) + (x2 - x1) * (Y - y2)) / den
    w1 = ((y2 - y0) * (X - x2) + (x0 - x2) * (Y - y2)) / den
    w2 = 1 - w0 - w1
    inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
    zz = w0 * z[0] + w1 * z[1] + w2 * z[2]
    sub = zb[ymin:ymax + 1, xmin:xmax + 1]
    m = inside & (zz < sub)
    if not m.any():
        return
    u = w0 * uv[0, 0] + w1 * uv[1, 0] + w2 * uv[2, 0]
    v = w0 * uv[0, 1] + w1 * uv[1, 1] + w2 * uv[2, 1]
    rx, ry, rw, rh = rect
    tx = np.clip(np.floor(u).astype(int), rx, rx + rw - 1)
    ty = np.clip(np.floor(v).astype(int), ry, ry + rh - 1)
    col = tex[ty, tx]
    m &= col[..., 3] > 127
    sub[m] = zz[m]
    view = img[ymin:ymax + 1, xmin:xmax + 1]
    view[m] = col[..., :3][m] * shade


def render(model, tex, yaw, pitch, size=384, mats=None, frame=None, outline=True, ground=True):
    mats = model.bone_matrices() if mats is None else mats
    ctr, rad = frame if frame is not None else _bounds(model, [mats])
    f, r, u = camera(yaw, pitch)
    scale = size * 0.46 / rad
    img = np.tile(BG, (size, size, 1))
    zb = np.full((size, size), np.inf)

    def proj(pts):
        return np.stack([(pts - ctr) @ r * scale + size / 2, size / 2 - (pts - ctr) @ u * scale], 1)

    if ground and pitch < 60:
        gy = int(round(size / 2 - (np.array([0, 0, 0]) - ctr) @ u * scale))
        if pitch < 5 and 0 <= gy < size:
            img[gy:gy + 2, :] = BG * 0.82
    teximg = tex.image
    for c, n, rect in _quads(model, tex, mats):
        if n @ f > -1e-4:
            continue
        shade = 0.62 + 0.38 * max(0.0, float(n @ LIGHT))
        sp = proj(c)
        dz = c @ f
        x, y, w, h = rect
        uvs = np.array([[x, y], [x + w, y], [x, y + h], [x + w, y + h]], float)
        _tri(img, zb, sp[[0, 2, 1]], dz[[0, 2, 1]], uvs[[0, 2, 1]], teximg, rect, shade)
        _tri(img, zb, sp[[2, 3, 1]], dz[[2, 3, 1]], uvs[[2, 3, 1]], teximg, rect, shade)
    if outline:
        mask = np.isfinite(zb)
        er = mask.copy()
        er[1:, :] &= mask[:-1, :]
        er[:-1, :] &= mask[1:, :]
        er[:, 1:] &= mask[:, :-1]
        er[:, :-1] &= mask[:, 1:]
        edge = mask & ~er
        zf = np.where(mask, zb, 1e9)
        jump = np.zeros_like(mask)
        thr = 1.2
        jump[:, 1:] |= (np.abs(zf[:, 1:] - zf[:, :-1]) > thr) & (zf[:, 1:] > zf[:, :-1])
        jump[:, :-1] |= (np.abs(zf[:, 1:] - zf[:, :-1]) > thr) & (zf[:, :-1] > zf[:, 1:])
        jump[1:, :] |= (np.abs(zf[1:, :] - zf[:-1, :]) > thr) & (zf[1:, :] > zf[:-1, :])
        jump[:-1, :] |= (np.abs(zf[1:, :] - zf[:-1, :]) > thr) & (zf[:-1, :] > zf[1:, :])
        img[edge] *= 0.35
        img[jump & mask & ~edge] *= 0.7
    return np.clip(img, 0, 255).astype(np.uint8)


def contact_sheet(model, tex, size=384, mats=None, title=None):
    mats = model.bone_matrices() if mats is None else mats
    frame = _bounds(model, [mats])
    sheet = Image.new("RGB", (size * 2, size * 2), tuple(BG.astype(int)))
    d = ImageDraw.Draw(sheet)
    for k, (label, yaw, pitch) in enumerate(VIEWS):
        im = Image.fromarray(render(model, tex, yaw, pitch, size, mats, frame))
        x, y = (k % 2) * size, (k // 2) * size
        sheet.paste(im, (x, y))
        d.text((x + 8, y + 6), label, fill=(70, 74, 86))
    d.line([(size, 0), (size, 2 * size)], fill=(200, 204, 212))
    d.line([(0, size), (2 * size, size)], fill=(200, 204, 212))
    if title:
        d.text((8, 2 * size - 16), title, fill=(70, 74, 86))
    return sheet


def anim_gif(model, tex, anim, path, size=300, frames=None, yaw=35, pitch=18):
    frames = frames or max(8, min(24, int(round(anim.length * 20))))
    times = [anim.length * i / frames for i in range(frames)]
    mats_list = [model.bone_matrices(anim, t) for t in times]
    frame = _bounds(model, mats_list)
    ims = [Image.fromarray(render(model, tex, yaw, pitch, size, m, frame)) for m in mats_list]
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=int(1000 * anim.length / frames),
                loop=0, disposal=2)
    return path


def series_sheet(models_and_tex, size=300, labels=None):
    """Side-by-side 3/4 renders at the SAME scale (to compare evolution stages)."""
    mats = [m.bone_matrices() for m, _ in models_and_tex]
    rad = max(_bounds(m, [mm])[1] for (m, _), mm in zip(models_and_tex, mats))
    sheet = Image.new("RGB", (size * len(models_and_tex), size), tuple(BG.astype(int)))
    d = ImageDraw.Draw(sheet)
    for k, ((m, tex), mm) in enumerate(zip(models_and_tex, mats)):
        ctr, _ = _bounds(m, [mm])
        ctr = ctr.copy()
        ctr[1] = rad * 0.9
        im = Image.fromarray(render(m, tex, 35, 18, size, mm, (ctr, rad)))
        sheet.paste(im, (k * size, 0))
        d.text((k * size + 8, 6), (labels[k] if labels else m.name), fill=(70, 74, 86))
    return sheet
