"""The judge: automatic checks that replace most "look, the arm is floating" chat turns.
Output is a few lines of text; details only when something is wrong."""
import numpy as np

from .mathutil import obb_overlap, point_obb_dist, convex_hull_2d, signed_dist_to_hull


class Report:
    def __init__(self, name):
        self.name = name
        self.lines, self.errors, self.warnings, self.fixed = [], [], [], []
        self.stats = {}

    def ok(self, msg):
        self.lines.append("OK    " + msg)

    def err(self, msg):
        self.errors.append(msg)
        self.lines.append("ERRO  " + msg)

    def warn(self, msg):
        self.warnings.append(msg)
        self.lines.append("AVISO " + msg)

    def fix(self, msg):
        self.fixed.append(msg)
        self.lines.append("FIX   " + msg)

    @property
    def text(self):
        return "\n".join(self.lines)


def _short(names, n=6):
    names = list(names)
    return ", ".join(names[:n]) + (f" (+{len(names) - n})" if len(names) > n else "")


def fix_zfighting(model, rep):
    """Coplanar faces pointing the same way flicker. Inflate the smaller box a hair.
    Faces that are buried inside another box of the same bone are hidden anyway: skipped."""
    from .texture import _covered
    by_bone = {}
    for b in model.boxes:
        by_bone.setdefault(b.bone, []).append(b)

    def hidden(box, k, positive):
        key = {(0, True): "east", (0, False): "west", (1, True): "up", (1, False): "down",
               (2, True): "south", (2, False): "north"}[(k, positive)]
        return _covered(box, key, by_bone[box.bone])

    mats = model.bone_matrices()
    aabb = []
    for b in model.boxes:
        w = model.box_matrix(b, mats)
        axis_aligned = np.allclose(np.abs(w[:3, :3]), np.round(np.abs(w[:3, :3])), atol=1e-6)
        c = model.corners(b, mats)
        aabb.append((c.min(0), c.max(0)) if axis_aligned else None)
    fixed = []
    n = len(model.boxes)
    for i in range(n):
        for j in range(i + 1, n):
            if aabb[i] is None or aabb[j] is None:
                continue
            (lo1, hi1), (lo2, hi2) = aabb[i], aabb[j]
            for k in range(3):
                t = [a for a in range(3) if a != k]
                ov = all(min(hi1[a], hi2[a]) - max(lo1[a], lo2[a]) > 1e-3 for a in t)
                if not ov:
                    continue
                a, b = model.boxes[i], model.boxes[j]
                same = False
                for positive, v1, v2 in ((True, hi1[k], hi2[k]), (False, lo1[k], lo2[k])):
                    if abs(v1 - v2) < 1e-4 and not (hidden(a, k, positive) or hidden(b, k, positive)):
                        same = True
                if same:
                    small = a if np.prod(a.size) <= np.prod(b.size) else b
                    if small.inflate < 0.02:
                        small.inflate = 0.02
                        fixed.append(f"{a.name}/{b.name}")
                    break
    if fixed:
        rep.fix(f"z-fighting corrigido em {len(fixed)} par(es): {_short(fixed, 4)}")
    else:
        rep.ok("z-fighting: 0")


def run(model, tex=None):
    rep = Report(model.name)
    mats = model.bone_matrices()
    boxes = model.boxes
    c, a, h = model.obbs(mats)
    dims = model.dims(mats)
    nb = len([b for b in model.bones])
    rep.stats.update(cubes=len(boxes), bones=nb, dims=dims)
    head = (f"[{model.name}] {len(boxes)} cubos, {nb} ossos"
            + (f", textura {tex.size}x{tex.size} ({tex.culled} faces ocultas removidas)" if tex else "")
            + (f", animacoes: {', '.join(an.name for an in model.anims)}" if model.anims else ""))
    rep.lines.append(head)
    rep.lines.append(f"      dimensoes L x A x C = {dims[0]:.1f} x {dims[1]:.1f} x {dims[2]:.1f}")

    # 1. connectivity: every box must touch the rest
    parent = list(range(len(boxes)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if find(i) != find(j) and obb_overlap(c[i], a[i], h[i], c[j], a[j], h[j], tol=0.06):
                parent[find(i)] = find(j)
    root = find(0)
    loose = [boxes[i].name for i in range(len(boxes)) if find(i) != root]
    if loose:
        rep.err(f"pecas soltas (nao encostam em nada): {_short(loose)}")
    else:
        rep.ok("pecas soltas: 0")

    # 2. joints: pivot must sit where parent and child meet
    bad = []
    for bone in model.bones:
        if bone.parent is None or not bone.boxes or not bone.parent.boxes:
            continue
        pv = (mats[bone] @ np.append(np.zeros(3), 1))[:3]
        idx_own = [boxes.index(b) for b in bone.boxes]
        idx_par = [boxes.index(b) for b in bone.parent.boxes]
        d_own = min(point_obb_dist(pv, c[i], a[i], h[i]) for i in idx_own)
        d_par = min(point_obb_dist(pv, c[i], a[i], h[i]) for i in idx_par)
        if d_own > 0.75 or d_par > 0.75:
            bad.append(f"{bone.name} (pivo a {max(d_own, d_par):.1f} da junta)")
    if bad:
        rep.err(f"pivos fora da junta (vai descolar ao animar): {_short(bad, 4)}")
    else:
        rep.ok(f"juntas: {sum(1 for b in model.bones if b.parent is not None)} pivos no ponto de contato")

    # 3. symmetry of _R/_L pairs
    by_name = {b.name: b for b in boxes}
    pairs, asym = 0, []
    cmap = {b.name: c[i] for i, b in enumerate(boxes)}
    for name, b in by_name.items():
        if name.endswith("_R") and name[:-2] + "_L" in by_name:
            pairs += 1
            l = by_name[name[:-2] + "_L"]
            pr, pl = cmap[name], cmap[l.name]
            if abs(pr[0] + pl[0]) > 0.05 or abs(pr[1] - pl[1]) > 0.05 or abs(pr[2] - pl[2]) > 0.05 \
                    or not np.allclose(b.size, l.size):
                asym.append(name[:-2])
    if asym:
        rep.err(f"pares assimetricos: {_short(asym)}")
    elif pairs:
        rep.ok(f"simetria: {pairs} pares espelhados")

    # 4. ground support & balance
    support, pts = [], []
    for i, b in enumerate(boxes):
        cc = model.corners(b, mats)
        low = cc[cc[:, 1] < 0.06]
        if len(low):
            support.append(b.name)
            pts.extend(low[:, [0, 2]])
    vol = np.array([max(np.prod(b.size), 0.05) for b in boxes])
    com = (c[:, [0, 2]] * vol[:, None]).sum(0) / vol.sum()
    if not support:
        rep.err("nada encosta no chao")
    else:
        hull = convex_hull_2d(np.array(pts))
        margin = signed_dist_to_hull(com, hull) if len(hull) >= 3 else -1.0
        tag = f"apoios: {_short(support, 8)}"
        if margin < 0:
            rep.warn(f"centro de massa fora da base ({-margin:.1f} unid.), tombaria. {tag}")
        else:
            rep.ok(f"equilibrio: centro de massa dentro da base (margem {margin:.1f}). {tag}")

    # 5. budget
    if len(boxes) > 150:
        rep.warn(f"{len(boxes)} cubos: pesado para mobile; tente juntar detalhes")
    if tex is not None and tex.size > 1024:
        rep.warn(f"textura {tex.size}px: acima do limite de 1024 do Roblox; reduza texel")
    small = [b.name for b in boxes if (b.size > 0).all() and b.size.min() * model.texel < 1]
    if small:
        rep.warn(f"pecas mais finas que 1 pixel de textura: {_short(small)}")
    return rep


def check_series(models):
    """Evolution stages must grow: taller or bulkier, and never lose parts."""
    lines, ok = [], True
    vols = [sum(float(np.prod(np.maximum(b.size, 0.05))) for b in m.boxes) for m in models]
    hs = [float(m.dims()[1]) for m in models]
    ns = [len(m.boxes) for m in models]
    for i in range(1, len(models)):
        if vols[i] <= vols[i - 1] * 1.05:
            ok = False
            lines.append(f"ERRO  estagio {i + 1} ({models[i].name}) nao e maior que o {i} (volume {vols[i]:.0f} vs {vols[i - 1]:.0f})")
        if ns[i] < ns[i - 1]:
            ok = False
            lines.append(f"ERRO  estagio {i + 1} perdeu pecas ({ns[i]} < {ns[i - 1]})")
    if ok:
        lines.append("OK    evolucao em ordem: " + " < ".join(
            f"{m.name} (alt {h:.0f}, {n} cubos)" for m, h, n in zip(models, hs, ns)))
    return "\n".join(lines)
