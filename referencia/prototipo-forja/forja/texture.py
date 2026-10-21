"""Texture baking. The texture is a pure function of geometry + materials + palette, so it is
rebuilt on every build and can never drift out of sync with the model.

Pipeline: hide faces buried inside the same bone -> pack every visible face into a power-of-two
atlas (per-face UV, 1 px padding) -> for every texel compute its 3D position -> ambient
occlusion by casting rays against all boxes (+ ground) -> 3D patterns (continuous across faces)
-> tone in a palette ramp with ordered dithering -> pixel-art decals (eyes, laces, ...)."""
from dataclasses import dataclass
import numpy as np

from .mathutil import ray_obb_nearest
from .style import make_ramp, resolve_color, BASE, N_TONES

FACES = ("north", "east", "south", "west", "up", "down")
NORMALS = {"east": (1, 0, 0), "west": (-1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0),
           "south": (0, 0, 1), "north": (0, 0, -1)}
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], float) / 16.0


def face_corners(f, t, key):
    """Corner order identical to Blockbench's cube geometry; UV (u1,v1) maps to corner 0,
    (u2,v1) to corner 1, (u1,v2) to corner 2, (u2,v2) to corner 3."""
    fx, fy, fz = f
    tx, ty, tz = t
    return np.array({
        "east": [[tx, ty, tz], [tx, ty, fz], [tx, fy, tz], [tx, fy, fz]],
        "west": [[fx, ty, fz], [fx, ty, tz], [fx, fy, fz], [fx, fy, tz]],
        "up": [[fx, ty, fz], [tx, ty, fz], [fx, ty, tz], [tx, ty, tz]],
        "down": [[fx, fy, tz], [tx, fy, tz], [fx, fy, fz], [tx, fy, fz]],
        "south": [[fx, ty, tz], [tx, ty, tz], [fx, fy, tz], [tx, fy, tz]],
        "north": [[tx, ty, fz], [fx, ty, fz], [tx, fy, fz], [fx, fy, fz]],
    }[key], float)


@dataclass
class TexResult:
    image: np.ndarray          # (S, S, 4) uint8
    rects: dict                # (box.uuid, face) -> (x, y, w, h) | None
    size: int
    culled: int
    texels: int


# ------------------------------------------------------------------ noise
def _hash(ix, iy, iz, seed):
    h = (ix.astype(np.int64) * 374761393 + iy.astype(np.int64) * 668265263
         + iz.astype(np.int64) * 1274126177 + int(seed) * 144269504) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFFFF).astype(float) / float(0x1000000)


def vnoise(p, seed=0):
    pi = np.floor(p)
    f = p - pi
    pi = pi.astype(np.int64)
    u = f * f * (3 - 2 * f)
    out = np.zeros(len(p))
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                h = _hash(pi[:, 0] + dx, pi[:, 1] + dy, pi[:, 2] + dz, seed)
                w = (u[:, 0] if dx else 1 - u[:, 0]) * (u[:, 1] if dy else 1 - u[:, 1]) \
                    * (u[:, 2] if dz else 1 - u[:, 2])
                out += h * w
    return out


def fbm(p, octaves=3, seed=0):
    s, amp, tot = np.zeros(len(p)), 0.5, 0.0
    for o in range(octaves):
        s += amp * vnoise(p * (2 ** o), seed + 17 * o)
        tot += amp
        amp *= 0.5
    return s / tot


def worley(p, seed=0):
    pi = np.floor(p).astype(np.int64)
    best = np.full(len(p), 9.0)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                cx, cy, cz = pi[:, 0] + dx, pi[:, 1] + dy, pi[:, 2] + dz
                fx = cx + _hash(cx, cy, cz, seed)
                fy = cy + _hash(cx, cy, cz, seed + 1)
                fz = cz + _hash(cx, cy, cz, seed + 2)
                d = np.sqrt((p[:, 0] - fx) ** 2 + (p[:, 1] - fy) ** 2 + (p[:, 2] - fz) ** 2)
                best = np.minimum(best, d)
    return best


# --------------------------------------------------------------- packing
def _covered(box, key, same_bone):
    if np.any(box.rot):
        return False
    k = {"east": 0, "west": 0, "up": 1, "down": 1, "south": 2, "north": 2}[key]
    s = NORMALS[key][k]
    f, t = box.frm, box.to
    probe = (t[k] if s > 0 else f[k]) + s * 0.01
    tang = [i for i in range(3) if i != k]
    for ob in same_bone:
        if ob is box or np.any(ob.rot):
            continue
        of, ot = ob.frm - ob.inflate, ob.to + ob.inflate
        if not (of[k] < probe < ot[k]):
            continue
        if all(of[i] <= f[i] + 1e-4 and ot[i] >= t[i] - 1e-4 for i in tang):
            return True
    return False


def pack(rects, pad=1):
    items = sorted(rects, key=lambda r: (-r[2], -r[1]))
    area = sum((w + 2 * pad) * (h + 2 * pad) for _, w, h in items)
    size = 16
    while size * size < area:
        size *= 2
    while True:
        pos, x, y, shelf, ok = {}, 0, 0, 0, True
        for rid, w, h in items:
            ww, hh = w + 2 * pad, h + 2 * pad
            if ww > size:
                ok = False
                break
            if x + ww > size:
                x, y, shelf = 0, y + shelf, 0
            if y + hh > size:
                ok = False
                break
            pos[rid] = (x + pad, y + pad)
            x += ww
            shelf = max(shelf, hh)
        if ok:
            return size, pos
        size *= 2


# ---------------------------------------------------------------- baking
def _hemisphere(k):
    i = np.arange(k) + 0.5
    u = i / k
    phi = i * np.pi * (3 - np.sqrt(5))
    r = np.sqrt(u)
    return np.stack([r * np.cos(phi), r * np.sin(phi), np.sqrt(1 - u)], 1)


def _ambient_occlusion(pw, nw, model, mats, radius, rays=40, chunk=600, seed=3):
    c, a, h = model.obbs(mats)
    hs = _hemisphere(rays)
    occ = np.zeros(len(pw))
    rng = np.random.default_rng(seed)
    for s in range(0, len(pw), chunk):
        p = pw[s:s + chunk]
        n = nw[s:s + chunk]
        m = len(p)
        helper = np.where(np.abs(n[:, 1:2]) < 0.9, np.array([[0, 1, 0]]), np.array([[1, 0, 0]]))
        tx = np.cross(n, helper)
        tx /= np.linalg.norm(tx, axis=1, keepdims=True)
        ty = np.cross(n, tx)
        ang = rng.uniform(0, 2 * np.pi, m)
        ca, sa = np.cos(ang)[:, None], np.sin(ang)[:, None]
        lx = hs[None, :, 0] * ca - hs[None, :, 1] * sa
        ly = hs[None, :, 0] * sa + hs[None, :, 1] * ca
        d = lx[..., None] * tx[:, None] + ly[..., None] * ty[:, None] + hs[None, :, 2:3] * n[:, None]
        o = np.repeat(p + n * 0.03, rays, axis=0)
        d = d.reshape(-1, 3)
        t = ray_obb_nearest(o, d, radius, c, a, h)
        w = np.where(np.isfinite(t), (1 - np.minimum(t, radius) / radius) ** 1.3, 0.0)
        if model.ground_ao:
            with np.errstate(divide='ignore', invalid='ignore'):
                tg = np.where(d[:, 1] < -1e-6, -o[:, 1] / d[:, 1], np.inf)
            tg = np.where((tg > 0) & (tg <= radius), tg, np.inf)
            wg = np.where(np.isfinite(tg), (1 - np.minimum(tg, radius) / radius) ** 1.3, 0.0)
            w = np.maximum(w, float(model.ground_ao) * 0.45 * wg)
        occ[s:s + m] = w.reshape(m, rays).mean(1)
    return occ


def bake(model, rays=40):
    model.finalize()
    texel = model.texel
    mats = model.bone_matrices()
    pal = model.palette
    by_bone = {}
    for b in model.boxes:
        by_bone.setdefault(b.bone, []).append(b)

    faces, rects, culled = [], {}, 0
    for bi, b in enumerate(model.boxes):
        for key in FACES:
            c = face_corners(b.frm, b.to, key)
            ul, vl = np.linalg.norm(c[1] - c[0]), np.linalg.norm(c[2] - c[0])
            if ul < 1e-6 or vl < 1e-6 or _covered(b, key, by_bone[b.bone]):
                rects[(b.uuid, key)] = None
                culled += 1
                continue
            w, h = max(1, int(round(ul * texel))), max(1, int(round(vl * texel)))
            faces.append(dict(box=b, key=key, corners=c, w=w, h=h))
    size, pos = pack([(i, F["w"], F["h"]) for i, F in enumerate(faces)])
    for i, F in enumerate(faces):
        F["x"], F["y"] = pos[i]
        rects[(F["box"].uuid, F["key"])] = (F["x"], F["y"], F["w"], F["h"])

    # ---- per-texel geometry
    fid, ii, jj = [], [], []
    for k, F in enumerate(faces):
        jg, ig = np.mgrid[0:F["h"], 0:F["w"]]
        fid.append(np.full(F["w"] * F["h"], k))
        ii.append(ig.ravel())
        jj.append(jg.ravel())
    fid, ii, jj = np.concatenate(fid), np.concatenate(ii), np.concatenate(jj)
    fw = np.array([F["w"] for F in faces])[fid]
    fh = np.array([F["h"] for F in faces])[fid]
    c0 = np.array([F["corners"][0] for F in faces])[fid]
    du = np.array([F["corners"][1] - F["corners"][0] for F in faces])[fid]
    dv = np.array([F["corners"][2] - F["corners"][0] for F in faces])[fid]
    pf = c0 + ((ii + 0.5) / fw)[:, None] * du + ((jj + 0.5) / fh)[:, None] * dv
    wm = np.array([model.box_matrix(F["box"], mats) for F in faces])
    nf = np.array([NORMALS[F["key"]] for F in faces], float)
    nwf = np.einsum('fij,fj->fi', wm[:, :3, :3], nf)
    nwf /= np.linalg.norm(nwf, axis=1, keepdims=True)
    pw = np.einsum('nij,nj->ni', wm[fid][:, :3, :3], pf) + wm[fid][:, :3, 3]
    nw, nfl = nwf[fid], nf[fid]

    dims = model.dims(mats)
    height = max(dims[1], 1.0)
    radius = float(np.clip(0.2 * dims.max(), 2.5, 7.0))
    occ = _ambient_occlusion(pw, nw, model, mats, radius, rays=rays)

    # ---- tone & colour role per texel
    bay = BAYER[jj % 4, ii % 4]
    mat_names = sorted({F["box"].mat for F in faces})
    mat_of_face = np.array([mat_names.index(F["box"].mat) for F in faces])
    mid = mat_of_face[fid]
    box_lo = np.array([F["box"].frm for F in faces])[fid]
    box_sz = np.maximum(np.array([F["box"].size for F in faces])[fid], 1e-6)
    rel = (pf - box_lo) / box_sz
    tone = np.zeros(len(pw))
    role2 = np.zeros(len(pw), bool)
    emis = np.zeros(len(pw), bool)
    base_noise = fbm(pw * 0.45, 3, seed=11)

    for mi, name in enumerate(mat_names):
        mt = model.material(name)
        sel = mid == mi
        if not sel.any():
            continue
        p, nn, r, b_ = pw[sel], nfl[sel], rel[sel], bay[sel]
        t = -model.ao * mt.ao * occ[sel] ** 0.85
        t += 0.32 * nw[sel][:, 1] + 0.25 * (p[:, 1] / height - 0.5)
        t += mt.noise * (base_noise[sel] - 0.5) * 2.2
        r2 = np.zeros(sel.sum(), bool)
        pat = mt.pattern
        if pat == "noise":
            t += 0.6 * (fbm(p / max(mt.scale, 0.1), 3, seed=5) - 0.5) * 2
        elif pat == "spots":
            dd = worley(p / max(mt.scale, 0.1), seed=21)
            r2 = dd < mt.amount * 0.62 + (b_ - 0.5) * 0.1
        elif pat == "stripes":
            ax = "xyz".index(mt.axis)
            s = np.sin(2 * np.pi * p[:, ax] / max(mt.scale, 0.1) + 2.2 * fbm(p * 0.22, 2, seed=8))
            r2 = s > 1 - 2 * mt.amount + (b_ - 0.5) * 0.15
        elif pat == "belly":
            r2 = (nn[:, 1] < -0.5) | ((nn[:, 1] < 0.5) & (r[:, 1] + (b_ - 0.5) * 0.14 < mt.amount))
        elif pat == "top":
            r2 = (nn[:, 1] > 0.5) | ((nn[:, 1] > -0.5) & (r[:, 1] - (b_ - 0.5) * 0.14 > 1 - mt.amount))
        elif pat == "gradient":
            r2 = r[:, 1] + (b_ - 0.5) * 0.3 < mt.amount
        elif pat == "speckle":
            hh = _hash((p[:, 0] * texel * 7).astype(np.int64), (p[:, 1] * texel * 7).astype(np.int64),
                       (p[:, 2] * texel * 7).astype(np.int64), 31)
            r2 = hh < mt.amount * 0.3
        elif pat == "patches":
            r2 = fbm(p / max(mt.scale, 0.1), 3, seed=41) > 1 - mt.amount * 0.9 + (b_ - 0.5) * 0.06
        elif pat == "scales":
            i_, j_ = ii[sel], jj[sel]
            row = j_ // 3
            col_i = (i_ + (row % 2) * 2) % 4
            t += np.where(j_ % 3 == 2, -0.9, 0.0) + np.where((col_i == 1) & (j_ % 3 == 0), 0.55, 0.0)
        if mt.second is None:
            r2[:] = False
        bev = model.bevel if mt.bevel is None else mt.bevel
        if bev:
            i_, j_, w_, h_ = ii[sel], jj[sel], fw[sel], fh[sel]
            big = (w_ >= 3) & (h_ >= 3)
            side = np.abs(nn[:, 1]) < 0.5
            up = nn[:, 1] > 0.5
            edge = (i_ == 0) | (i_ == w_ - 1) | (j_ == 0) | (j_ == h_ - 1)
            t += np.where(big & side & (j_ == 0), bev, 0.0)
            t -= np.where(big & side & (j_ == h_ - 1), 0.6 * bev, 0.0)
            t += np.where(big & up & edge, 0.6 * bev, 0.0)
        if mt.emissive:
            t = 0.6 + 0.3 * (b_ - 0.5)
            emis[sel] = True
        tone[sel] = t
        role2[sel] = r2

    idx = np.clip(np.floor(BASE + tone + 0.5 + (bay - 0.5) * model.dither), 0, N_TONES - 1).astype(int)
    ramps = {}
    for name in mat_names:
        mt = model.material(name)
        ramps[name] = (make_ramp(resolve_color(pal, mt.color)),
                       make_ramp(resolve_color(pal, mt.second or mt.color)))
    rgb = np.zeros((len(pw), 3), np.uint8)
    for mi, name in enumerate(mat_names):
        sel = mid == mi
        r1, r2_ = ramps[name]
        rgb[sel] = np.where(role2[sel][:, None], r2_[idx[sel]], r1[idx[sel]])

    img = np.zeros((size, size, 4), np.uint8)
    fx = np.array([F["x"] for F in faces])[fid] + ii
    fy = np.array([F["y"] for F in faces])[fid] + jj
    img[fy, fx, :3] = rgb
    img[fy, fx, 3] = 255

    for F in faces:
        for kind, key, params in F["box"].decals:
            if key == F["key"]:
                draw_decal(img, (F["x"], F["y"], F["w"], F["h"]), kind, params, pal, texel)
    for F in faces:
        _dilate(img, F["x"], F["y"], F["w"], F["h"])
    return TexResult(img, rects, size, culled, int(len(pw)))


def _dilate(img, x, y, w, h):
    s = img.shape[0]
    if y > 0:
        img[y - 1, x:x + w] = img[y, x:x + w]
    if y + h < s:
        img[y + h, x:x + w] = img[y + h - 1, x:x + w]
    if x > 0:
        img[max(y - 1, 0):min(y + h + 1, s), x - 1] = img[max(y - 1, 0):min(y + h + 1, s), x]
    if x + w < s:
        img[max(y - 1, 0):min(y + h + 1, s), x + w] = img[max(y - 1, 0):min(y + h + 1, s), x + w - 1]


# ---------------------------------------------------------------- decals
def _rgb(pal, role):
    return (np.array([int(resolve_color(pal, role).lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)])
            .astype(np.uint8))


STAMPS = {
    "bolt": ["...##", "..##.", ".####", "..##.", ".##..", "##...", "#...."],
    "star": ["..#..", "..#..", "#####", ".###.", ".#.#."],
    "heart": [".#.#.", "#####", "#####", ".###.", "..#.."],
    "paw": ["#.#.#", ".....", ".###.", "#####", ".###."],
    "skull": [".###.", "#.#.#", "#####", ".#.#."],
}


def _ellipse(cx, cy, rx, ry):
    pts = []
    for j in range(int(np.floor(cy - ry)) - 1, int(np.ceil(cy + ry)) + 1):
        for i in range(int(np.floor(cx - rx)) - 1, int(np.ceil(cx + rx)) + 1):
            if ((i + 0.5 - cx) / max(rx, 0.5)) ** 2 + ((j + 0.5 - cy) / max(ry, 0.5)) ** 2 <= 1.0001:
                pts.append((i, j))
    return pts


def draw_decal(img, rect, kind, p, pal, texel):
    x0, y0, w, h = rect

    def put(i, j, col):
        i, j = int(i), int(j)
        if 0 <= i < w and 0 <= j < h:
            img[y0 + j, x0 + i, :3] = col
            img[y0 + j, x0 + i, 3] = 255

    if kind == "face":
        _draw_face(put, w, h, p, pal, texel)
    elif kind == "laces":
        col = _rgb(pal, p.get("color", "lace"))
        lo, hi = int(round(w * 0.22)), int(round(w * 0.78))
        start = int(p.get("start", 0.2) * h)
        for j in range(max(start, 1), h - 1, 2):
            for i in range(lo, max(hi, lo + 1)):
                put(i, j, col)
    elif kind == "stripe":
        col = _rgb(pal, p.get("color", "accent"))
        y = p.get("y", 0.5)
        th = max(1, int(round(p.get("thickness", 1) * texel)))
        j0 = int(round(y * h - th / 2))
        for j in range(j0, j0 + th):
            for i in range(w):
                put(i, j, col)
    elif kind in STAMPS:
        col = _rgb(pal, p.get("color", "accent"))
        st = STAMPS[kind]
        sc = max(1, int(p.get("scale", 1)))
        sh, sw = len(st) * sc, len(st[0]) * sc
        cx = int(round(p.get("x", 0.5) * w - sw / 2))
        cy = int(round(p.get("y", 0.5) * h - sh / 2))
        flip = p.get("flip", False)
        for j, row in enumerate(st):
            for i, ch in enumerate(row[::-1] if flip else row):
                if ch == "#":
                    for a in range(sc):
                        for bb in range(sc):
                            put(cx + i * sc + a, cy + j * sc + bb, col)
    elif kind == "shine":
        col = _rgb(pal, p.get("color", "eye_white"))
        cx, cy = int(p.get("x", 0.22) * w), int(p.get("y", 0.2) * h)
        sz = max(1, int(p.get("size", 1) * texel / 2))
        for i in range(cx, cx + 2 * sz):
            for j in range(cy, cy + sz):
                put(i, j, col)
        for i in range(cx, cx + sz):
            for j in range(cy + sz, cy + 2 * sz):
                put(i, j, col)
    elif kind == "nostrils":
        col = _rgb(pal, p.get("color", "dark"))
        gap = max(1, int(round(w * p.get("gap", 0.2))))
        j = int(round(h * p.get("y", 0.25)))
        for i in (w // 2 - gap - 1 + (w % 2), w // 2 + gap):
            put(i, j, col)
    elif kind == "claws":
        col = _rgb(pal, p.get("color", "horn"))
        n = int(p.get("count", 3))
        ln = max(1, int(round(p.get("length", 0.5) * texel)))
        for k in range(n):
            i = int(round((k + 1) * w / (n + 1) - 0.5))
            for j in range(h - ln, h):
                put(i, j, col)
    elif kind == "rect":
        col = _rgb(pal, p.get("color", "accent"))
        for j in range(int(p["y"] * h), int(round((p["y"] + p["h"]) * h))):
            for i in range(int(p["x"] * w), int(round((p["x"] + p["w"]) * w))):
                put(i, j, col)
    elif kind == "seam":
        col = _rgb(pal, p.get("color", "dark"))
        at = p.get("at", "left")
        for j in range(h):
            if at in ("left", "both"):
                put(0, j, col)
            if at in ("right", "both"):
                put(w - 1, j, col)
    else:
        raise ValueError(f"Decal desconhecido: {kind}")


def _draw_face(put, w, h, p, pal, texel):
    dark = _rgb(pal, p.get("eye_color") or "eye")
    white = _rgb(pal, "eye_white")
    blush = _rgb(pal, "blush")
    glow = _rgb(pal, "glow")
    style = p.get("eyes")
    d = p.get("eye_size")
    d = max(2, int(round(min(w, h) * 0.22))) if d is None else max(1, int(round(d * texel)))
    cy = (1 - p.get("eye_y", 0.6)) * h
    gap = p.get("eye_gap", 0.36) * w / 2
    count = p.get("count", 2)
    centers = [w / 2] if count == 1 else [w / 2 - gap, w / 2 + gap]
    if count == 3:
        centers = [w / 2 - gap, w / 2, w / 2 + gap]
    for n_eye, cx in enumerate(centers):
        inner = 1 if cx < w / 2 else -1
        if style in ("round", "cute", "big", "angry"):
            rx = d / 2
            ry = d / 2 + (0.6 if style == "cute" else 0)
            if style == "big":
                for (i, j) in _ellipse(cx, cy, rx + 1, ry + 1):
                    put(i, j, white)
                for (i, j) in _ellipse(cx + inner * 0.5, cy + 0.3, rx * 0.8, ry * 0.8):
                    put(i, j, dark)
            else:
                for (i, j) in _ellipse(cx, cy, rx, ry):
                    put(i, j, dark)
            if d >= 3 or style == "cute":
                hx, hy = int(np.floor(cx - rx * 0.45)), int(np.floor(cy - ry * 0.5))
                put(hx, hy, white)
                if d >= 5:
                    put(hx + 1, hy, white)
                    put(hx, hy + 1, white)
                    put(int(np.floor(cx + rx * 0.4)), int(np.floor(cy + ry * 0.45)), white)
            if style == "angry" or p.get("brows") == "angry":
                by = int(np.floor(cy - ry - 1))
                for k in range(int(d) + 1):
                    i = int(np.floor(cx - inner * (d / 2) + inner * k))
                    put(i, by + (k * 2) // (int(d) + 1), dark)
        elif style == "dot":
            s = max(1, d // 2)
            for i in range(s):
                for j in range(s):
                    put(int(cx - s / 2) + i, int(cy - s / 2) + j, dark)
        elif style in ("happy", "sleepy"):
            half = max(1, d // 2)
            base = int(np.floor(cy))
            for k in range(-half, half + 1):
                lift = 0 if abs(k) < half else 1
                yy = base - (lift if style == "happy" else -lift)
                put(int(np.floor(cx)) + k, yy, dark)
        elif style == "glow":
            for (i, j) in _ellipse(cx, cy, d / 2, d / 2 + 0.4):
                put(i, j, glow)
            put(int(np.floor(cx)), int(np.floor(cy)), white)
        elif style == "x":
            half = max(1, d // 2)
            for k in range(-half, half + 1):
                put(int(np.floor(cx)) + k, int(np.floor(cy)) + k, dark)
                put(int(np.floor(cx)) + k, int(np.floor(cy)) - k, dark)
        if p.get("blush"):
            bw = max(2, int(round(w * 0.1)))
            bx = int(np.floor(cx - inner * (d / 2 + bw * 0.6) - bw / 2))
            byy = int(np.floor(cy + d / 2 + 1))
            for i in range(bx, bx + bw):
                put(i, byy, blush)
                if texel >= 2:
                    put(i, byy + 1, blush)
    mouth = p.get("mouth")
    if mouth:
        mw = p.get("mouth_w")
        mw = max(3, int(round(w * 0.22))) if mw is None else max(2, int(round(mw * texel)))
        my = int(round((1 - p.get("mouth_y", 0.25)) * h))
        x0 = int(round(w / 2 - mw / 2))
        if mouth == "smile":
            for i in range(x0 + 1, x0 + mw - 1):
                put(i, my, dark)
            put(x0, my - 1, dark)
            put(x0 + mw - 1, my - 1, dark)
        elif mouth == "flat":
            for i in range(x0, x0 + mw):
                put(i, my, dark)
        elif mouth == "open":
            mh = max(2, int(round(mw * 0.55)))
            for i in range(x0, x0 + mw):
                for j in range(my - mh // 2, my - mh // 2 + mh):
                    put(i, j, dark)
            for i in range(x0 + 1, x0 + mw - 1):
                put(i, my - mh // 2 + mh - 1, blush)
        elif mouth == "fangs":
            for i in range(x0, x0 + mw):
                put(i, my, dark)
            for tx in (x0 + 1, x0 + mw - 2):
                put(tx, my + 1, white)
                if texel >= 2:
                    put(tx, my + 2, white)
        elif mouth == "o":
            s = max(2, mw // 2)
            for i in range(s):
                for j in range(s):
                    put(int(w / 2 - s / 2) + i, my - s // 2 + j, dark)
        elif mouth == "w":
            for i, dj in zip(range(x0, x0 + 5), (0, 1, 0, 1, 0)):
                put(i, my + dj, dark)
