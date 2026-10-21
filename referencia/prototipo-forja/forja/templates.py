"""Body-plan templates. Each one builds a skeleton-first creature with sensible proportions,
named sockets and procedural animations, and returns a Rig with handles to every part so
the spec can keep adding details (horns, hats, shoes...). Sizes are (width, height, depth)."""
from types import SimpleNamespace
import numpy as np

from . import anim as A


class Rig(SimpleNamespace):
    def __init__(self, **kw):
        base = dict(body=None, head=None, legs={}, arms={}, feet=[], hands=[], tail=[],
                    wings=None, antennae=[], tentacles=[], dirs=[], extras=[], parts={})
        base.update(kw)
        super().__init__(**base)


def _mat(m, preferred, fallback):
    return preferred if (preferred in m.materials or preferred in m.palette) else fallback


# ------------------------------------------------------------------ quadruped
def quadruped(m, body=(10, 8, 14), mat="primary", leg=(3, 5, 3), foot=(4, 2, 5), neck=None,
              head=(8, 7, 8), snout=(6, 3, 4), ears=None, horns=None,
              tail=((4, 4, 4), (3, 3, 4), (2, 2, 4)), tail_droop=14, tail_curl=-9,
              wings=None, spikes=0, face="cute", mouth="smile", blush=True, head_mat=None,
              leg_mat=None, foot_mat=None, horn_mat="horn", wing_mat=None, anims=True):
    """Four legs (dog, cat, dragon, pig...). wings=True adds two-segment wings."""
    rig = Rig()
    b = m.root("body", body, mat=mat)
    rig.body = b
    bw, bh, bl = body
    lw, lh, ld = leg
    xf, zf = 1 - (lw + 1) / bw, 1 - (ld + 1) / bl
    for key, zs in (("F", -1), ("B", 1)):
        pr = m.box(f"leg_{key}", leg, mat=leg_mat or mat).on(b, at=(xf, -1, zs * zf), sink=1, mirror=True)
        rig.legs[key + "R"], rig.legs[key + "L"] = pr.r, pr.l
        if foot:
            fp = m.box(f"foot_{key}", foot, mat=foot_mat or leg_mat or mat, tags=("foot",)).on(
                pr, at="bottom", anchor="bottom", offset=(0, 0, -(foot[2] - ld) / 2), joint=False)
            m.decal(fp, "front", "claws", count=3)
        else:
            fp = pr.tag("foot")
        rig.feet += [fp.r, fp.l]
        m.socket(f"pe_{key}", fp, at="bottom")
    if neck:
        nk = m.box("neck", neck, mat=mat).on(b, at=(0, 1, -0.62), anchor="bottom", sink=1, rot=(-12, 0, 0))
        hd = m.box("head", head, mat=head_mat or mat).on(nk, at="top", anchor=(0, -1, 0.3), sink=1,
                                                          rot=(12, 0, 0))
        rig.parts["neck"] = nk
    else:
        hd = m.box("head", head, mat=head_mat or mat).on(b, at=(0, 0.45, -1), anchor=(0, -0.1, 1), sink=1)
    rig.head = hd
    m.socket("cabeca", hd, at="top")
    if snout:
        sn = m.box("snout", snout, mat=head_mat or mat).on(hd, at=(0, -0.45, -1), sink=0.5, joint=False)
        rig.parts["snout"] = sn
        m.face(hd, "front", eyes=face, mouth=None, blush=blush, eye_y=0.72, eye_gap=0.42)
        m.face(sn, "front", eyes=None, mouth=mouth, mouth_y=0.3)
        m.decal(sn, "front", "nostrils", y=0.25, gap=0.22)
    else:
        m.face(hd, "front", eyes=face, mouth=mouth, blush=blush)
    if ears:
        rig.parts["ears"] = m.box("ear", ears, mat=head_mat or mat).on(
            hd, at=(0.55, 1, 0.2), anchor="bottom", sink=0.5, rot=(0, 0, -15), mirror=True)
    if horns:
        rig.parts["horns"] = m.box("horn", horns, mat=horn_mat).on(
            hd, at=(0.5, 1, 0.45), sink=0.5, rot=(30, 0, -12), joint=False, mirror=True)
    for i in range(spikes):
        z = -0.45 + 0.9 * (i + 0.5) / spikes
        m.box(f"spike{i + 1}", (2, 2, 2), mat=horn_mat).on(b, at=(0, 1, z), sink=1, rot=(45, 0, 0), joint=False)
    if tail:
        rig.tail = m.chain("tail", b, at=(0, 0.25, 1), sizes=tail, dir="back",
                           first=(tail_droop, 0, 0), bend=(tail_curl, 0, 0), mat=mat)
    if wings:
        w1s, w2s = wings if isinstance(wings, (list, tuple)) else ((7, 1, 6), (6, 1, 5))
        wm = wing_mat or _mat(m, "wing", mat)
        w1 = m.box("wing", w1s, mat=wm).on(b, at=(0.45, 1, -0.15), anchor=(-1, -1, 0), sink=0.5,
                                          rot=(0, -12, 32), mirror=True)
        m.box("wingtip", w2s, mat=wm).on(w1, at=(1, 0, 0.15), anchor=(-1, 0, 0), sink=0.5, rot=(0, 0, 18))
        rig.wings = w1
    if anims:
        A.idle_quadruped(m, rig)
        A.walk_quadruped(m, rig)
    m.rig = rig
    return rig


# -------------------------------------------------------------------- hexapod
def hexapod(m, body=(10, 3, 13), shell=(5, 4, 9), pronotum=(8, 4, 4), head=(6, 3, 4),
            upper=(4, 2, 2), lower=(2, 5, 2), horn=((2, 3, 2), (2, 3, 2)),
            antennae=((1, 3, 1), (1, 3, 1)), mat="primary", belly_mat="belly", leg_mat=None,
            horn_mat="horn", face="cute", mouth="smile", blush=True, anims=True):
    """Six-legged insect (beetle, ant, bug). Shell halves are separate bones (can open)."""
    rig = Rig()
    leg_mat = leg_mat or _mat(m, "leg", belly_mat)
    b = m.root("body", body, mat=belly_mat)
    rig.body = b
    pr = m.box("pronotum", pronotum, mat=mat).on(b, at=(0, 1, -1), anchor=(0, -1, -1), joint=False)
    el = m.box("elytron", shell, mat=mat).on(b, at=(0.5, 1, 1), anchor=(0, -1, 1), mirror=True)
    for side, edge in ((el.r, "left"), (el.l, "right")):
        m.decal(side, "top", "seam", at=edge)
        m.decal(side, "back", "seam", at=edge)
    rig.parts.update(pronotum=pr, shell=el)
    hd = m.box("head", head, mat=mat).on(pr, at=(0, -0.3, -1), sink=0.5)
    rig.head = hd
    m.face(hd, "front", eyes=face, mouth=mouth, blush=blush, eye_y=0.6, eye_gap=0.5)
    m.socket("cabeca", hd, at="top")
    if horn:
        rig.parts["horn"] = m.chain("horn", hd, at=(0, 1, -0.5), sizes=horn, dir="up",
                                    first=(-35, 0, 0), bend=(40, 0, 0), mat=horn_mat)
    if antennae:
        rig.antennae = m.chain("antenna", hd, at=(0.65, 1, 0.3), sizes=antennae, dir="up",
                               first=(-25, 0, -22), bend=(-25, 0, 0), mat=leg_mat, mirror=True)
    for k, zf in enumerate((-0.62, 0.0, 0.62)):
        ry = (22, 0, -22)[k]
        up = m.box(f"leg{k + 1}", upper, mat=leg_mat).on(b, at=(1, -0.2, zf), sink=0.5,
                                                         rot=(0, ry, 24), mirror=True)
        lo = m.box(f"shin{k + 1}", lower, mat=leg_mat, tags=("foot",)).on(
            up, at=(1, -1, 0), anchor=(1, 1, 0), rot=(0, 0, -14))
        rig.legs[f"{k + 1}R"], rig.legs[f"{k + 1}L"] = up.r, up.l
        rig.feet += [lo.r, lo.l]
        m.socket(f"pe{k + 1}", lo, at="bottom")
    if anims:
        A.idle_hexapod(m, rig)
        A.walk_hexapod(m, rig)
    m.rig = rig
    return rig


# ----------------------------------------------------------------- cephalopod
def cephalopod(m, mantle=(12, 10, 11), skirt=(10, 3, 9), segs=((2, 3, 2), (2, 3, 2), (2, 2, 2)),
               splay=40, relax=(-18, -18), mat="primary", dome=True, face="cute", mouth="smile",
               blush=True, anims=True):
    """Octopus / squid: a mantle with 8 jointed tentacles on a ring. The tips are feet."""
    rig = Rig()
    b = m.root("mantle", mantle, mat=mat)
    rig.body = b
    if dome:
        d1 = m.box("dome", (mantle[0] - 2, 2, mantle[2] - 2), mat=mat).on(b, at="top", joint=False)
        m.box("dome_top", (max(mantle[0] - 6, 2), 1, max(mantle[2] - 6, 2)), mat=mat).on(d1, at="top", joint=False)
    sk = m.box("skirt", skirt, mat=mat).on(b, at="bottom", sink=0.5, joint=False)
    rig.parts["skirt"] = sk
    m.face(b, "front", eyes=face, mouth=None, blush=blush, eye_y=0.36, eye_gap=0.42)
    if mouth:
        m.face(sk, "front", eyes=None, mouth=mouth, mouth_y=0.62)
    rig.head = b
    m.socket("cabeca", d1 if dome else b, at="top")
    sw, _, sd = skirt
    ax, az = 1 - (segs[0][0] + 1) / sw, 1 - (segs[0][2] + 1) / sd
    ring = [("F", 0, -1), ("FR", 1, -1), ("R", 1, 0), ("BR", 1, 1),
            ("B", 0, 1), ("BL", -1, 1), ("L", -1, 0), ("FL", -1, -1)]
    for name, sx, sz in ring:
        u = np.array([sx * ax * sw / 2, sz * az * sd / 2])
        u = u / np.linalg.norm(u)
        rots = [(-splay * u[1], 0, splay * u[0])] + [(-r * u[1], 0, r * u[0]) for r in relax]
        ch = m.chain(f"tent_{name}_", sk, at=(sx * ax, -1, sz * az), sizes=segs, dir="down",
                     rots=rots, mat=mat, sink=0.5, tip_tags=("foot",))
        rig.tentacles.append(ch)
        rig.dirs.append(u)
        rig.feet.append(ch[-1])
        m.socket(f"pe_{name}", ch[-1], at="bottom")
    if anims:
        A.wave_tentacles(m, rig, name="idle", period=2.4, amp=6, bob=0.3)
        A.wave_tentacles(m, rig, name="walk", period=1.2, amp=12, bob=0.7)
    m.rig = rig
    return rig


# ----------------------------------------------------------------------- blob
def blob(m, body=(12, 8, 12), mat="primary", top=True, cap=True, puddle=True, drips=3,
         antennae=0, face="cute", mouth="open", blush=True, shine=True, anims=True):
    """Slime / jelly. The body bone pivots at its base so squash & stretch stays grounded."""
    rig = Rig()
    b = m.root("body", body, mat=mat, pivot="bottom")
    rig.body = b
    bw, bh, bd = body
    t = b
    if top:
        t = m.box("top", (bw - 2, 2, bd - 2), mat=mat).on(b, at="top", joint=False)
        if cap and bw >= 8:
            t = m.box("cap", (bw - 6, 1, bd - 6), mat=mat).on(t, at="top", joint=False)
    rig.head = b
    m.socket("cabeca", t, at="top")
    if puddle:
        m.box("puddle", (bw + 2, 1, bd + 2), mat=mat).on(b, at="bottom", sink=0.5, joint=False)
    spots = [(-0.55, -1, "front"), (1, 0.3, "right"), (-1, -0.2, "left"), (0.4, 1, "back"), (0.6, -1, "front")]
    for i in range(min(drips, len(spots))):
        fx, fz, side = spots[i]
        if side in ("front", "back"):
            at, size = (fx, -0.45, -1 if side == "front" else 1), (2, 3, 1)
        else:
            at, size = (1 if side == "right" else -1, -0.5, fz), (1, 3, 2)
        m.box(f"drip{i + 1}", size, mat=mat).on(b, at=at, sink=0.5, joint=False)
    m.face(b, "front", eyes=face, mouth=mouth, blush=blush, eye_y=0.58, eye_gap=0.4, mouth_y=0.3)
    if shine:
        m.decal(b, "front", "shine", x=0.1, y=0.12, size=1.5)
        if top:
            m.decal(t, "top", "shine", x=0.15, y=0.15, size=1)
    for i in range(antennae):
        sgn = 1 if i % 2 == 0 else -1
        stalk = m.box(f"stalk{i + 1}", (1, 2, 1), mat=mat).on(t, at=(sgn * 0.5, 1, 0), sink=0.3,
                                                             rot=(0, 0, -sgn * 12))
        m.box(f"ball{i + 1}", (2, 2, 2), mat=mat).on(stalk, at="top", sink=0.3, joint=False)
        rig.extras.append(stalk)
    if anims:
        A.jiggle_blob(m, rig)
        A.hop_blob(m, rig, height=max(3.0, bh * 0.45))
    m.rig = rig
    return rig


# --------------------------------------------------------------------- biped
def biped(m, torso=(8, 9, 5), head=(8, 8, 8), arm=(3, 5, 3), forearm=(3, 5, 3), leg=(4, 7, 4),
          foot=(4, 2, 5), mat="primary", head_mat=None, arm_mat=None, leg_mat=None, foot_mat=None,
          face="round", mouth="smile", blush=False, anims=True):
    """Two legs, two arms (zombie, knight, wizard...). Hands have sockets for props."""
    rig = Rig()
    t = m.root("torso", torso, mat=mat)
    rig.body = t
    hd = m.box("head", head, mat=head_mat or mat).on(t, at="top", sink=0.5)
    rig.head = hd
    m.socket("cabeca", hd, at="top")
    if face:
        m.face(hd, "front", eyes=face, mouth=mouth, blush=blush, eye_y=0.55)
    ua = m.box("arm", arm, mat=arm_mat or mat).on(t, at=(1, 1, 0), anchor=(-1, 1, 0), mirror=True)
    fa = m.box("forearm", forearm, mat=arm_mat or mat).on(ua, at="bottom", sink=0.5, rot=(-10, 0, 0))
    rig.arms = {"R": ua.r, "L": ua.l}
    rig.hands = [fa.r, fa.l]
    m.socket("mao", fa, at="bottom")
    lg = m.box("leg", leg, mat=leg_mat or mat).on(t, at=(0.5, -1, 0), sink=0.5, mirror=True)
    rig.legs = {"R": lg.r, "L": lg.l}
    if foot:
        ft = m.box("foot", foot, mat=foot_mat or leg_mat or mat, tags=("foot",)).on(
            lg, at="bottom", anchor="bottom", offset=(0, 0, -(foot[2] - leg[2]) / 2), joint=False)
    else:
        ft = lg.tag("foot")
    rig.feet = [ft.r, ft.l]
    m.socket("pe", ft, at="bottom")
    if anims:
        A.idle_biped(m, rig)
        A.walk_biped(m, rig)
    m.rig = rig
    return rig
