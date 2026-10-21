"""Small linear-algebra helpers. Conventions match Blockbench (three.js):
Y up, front = -Z (north), creature's right = +X. Euler angles in degrees, order ZYX
(matrix = Rz @ Ry @ Rx), the default for Blockbench's Generic Model format."""
import numpy as np


def euler_matrix(e_deg):
    x, y, z = np.radians(np.asarray(e_deg, float))
    cx, sx = np.cos(x), np.sin(x)
    cy, sy = np.cos(y), np.sin(y)
    cz, sz = np.cos(z), np.sin(z)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rz @ ry @ rx


def T(v):
    m = np.eye(4)
    m[:3, 3] = v
    return m


def R(e):
    m = np.eye(4)
    m[:3, :3] = euler_matrix(e)
    return m


def S(s):
    m = np.eye(4)
    m[0, 0], m[1, 1], m[2, 2] = s
    return m


def apply(m, pts):
    pts = np.asarray(pts, float)
    return pts @ m[:3, :3].T + m[:3, 3]


def ray_obb_nearest(o, d, maxd, c, a, h):
    """Nearest hit distance (inf = miss) for rays o,d (N,3) against oriented boxes:
    centers c (B,3), axes a (B,3,3) as columns, half extents h (B,3)."""
    n = o.shape[0]
    if c.shape[0] == 0:
        return np.full(n, np.inf)
    rel = o[:, None, :] - c[None, :, :]
    lo = np.einsum('nbj,bjk->nbk', rel, a)
    ld = np.einsum('nj,bjk->nbk', d, a)
    ld = np.where(np.abs(ld) < 1e-12, 1e-12, ld)
    inv = 1.0 / ld
    t1 = (-h[None] - lo) * inv
    t2 = (h[None] - lo) * inv
    tmin = np.max(np.minimum(t1, t2), axis=2)
    tmax = np.min(np.maximum(t1, t2), axis=2)
    hit = (tmax >= np.maximum(tmin, 0.0)) & (tmax > 1e-4)
    t = np.where(hit, np.maximum(tmin, 0.0), np.inf)
    t = np.where(t <= maxd, t, np.inf)
    return t.min(axis=1)


def point_obb_dist(p, c, a, h):
    lo = (np.asarray(p, float) - c) @ a
    q = np.clip(lo, -h, h)
    return float(np.linalg.norm(lo - q))


def obb_overlap(c1, a1, h1, c2, a2, h2, tol=0.02):
    """Separating-axis test. True when the boxes intersect or touch (within tol)."""
    axes = [a1[:, i] for i in range(3)] + [a2[:, i] for i in range(3)]
    for i in range(3):
        for j in range(3):
            v = np.cross(a1[:, i], a2[:, j])
            nv = np.linalg.norm(v)
            if nv > 1e-6:
                axes.append(v / nv)
    d = c2 - c1
    for ax in axes:
        r1 = np.sum(h1 * np.abs(a1.T @ ax))
        r2 = np.sum(h2 * np.abs(a2.T @ ax))
        if abs(d @ ax) > r1 + r2 + tol:
            return False
    return True


def convex_hull_2d(pts):
    pts = sorted(set(map(tuple, np.round(np.asarray(pts, float), 5))))
    if len(pts) <= 2:
        return np.array(pts)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return np.array(lower[:-1] + upper[:-1])


def signed_dist_to_hull(p, hull):
    """Positive = inside, distance to the nearest edge. Negative = outside."""
    if len(hull) < 3:
        return -float('inf')
    inside = True
    dmin = float('inf')
    n = len(hull)
    for i in range(n):
        a, b = hull[i], hull[(i + 1) % n]
        e = b - a
        cr = e[0] * (p[1] - a[1]) - e[1] * (p[0] - a[0])
        if cr < 0:
            inside = False
        t = np.clip(np.dot(p - a, e) / max(np.dot(e, e), 1e-12), 0, 1)
        dmin = min(dmin, float(np.linalg.norm(p - (a + t * e))))
    return dmin if inside else -dmin
