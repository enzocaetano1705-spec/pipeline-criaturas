"""Props that snap onto parts: shoes on any foot, crowns on heads, staffs in hands.
They attach through the same relation solver, so a staff is *in* the hand by construction
and follows the hand's bone when it animates."""
from .core import Pair


def _flat(items):
    out = []
    for it in items if isinstance(items, (list, tuple)) else [items]:
        out += [it.r, it.l] if isinstance(it, Pair) else [it]
    return out


def sneakers(m, feet, colors=("shoe",), sole="sole", lace="lace", accent="shoe2", height=None,
             emblem="bolt"):
    """A sneaker on every foot: upper, sole, toe cap, laces, side stripe and an emblem.
    Feet given as boxes or Pairs; colours cycle per pair."""
    feet = _flat(feet)
    m.mat("_sola", sole, noise=0.08, bevel=0.5, ao=0.8)
    for k, c in enumerate(colors):
        m.mat(f"_tenis{k}", c, noise=0.12, bevel=0.6, ao=0.9)
    shoes = []
    for n, f in enumerate(feet):
        fw, fh, fd = f.size
        mat = f"_tenis{(n // 2) % len(colors)}"
        uh = fh + 1 if height is None else height
        up = m.box(f"{f.name}_tenis", (fw + 1, uh, fd + 1), mat=mat, tags=("shoe",)).on(
            f, at="bottom", anchor="bottom", joint=False)
        m.box(f"{f.name}_sola", (fw + 2, 1, fd + 3), mat="_sola", tags=("shoe",)).on(
            up, at="bottom", offset=(0, 0, -0.5), joint=False)
        m.box(f"{f.name}_bico", (fw + 1, 1, 1), mat="_sola", tags=("shoe",)).on(
            up, at=(0, -1, -1), anchor=(0, -1, 1), joint=False)
        m.decal(up, "front", "laces", color=lace, start=0.15)
        outer = "right" if f.center[0] >= 0 else "left"
        m.decal(up, outer, "stripe", color=accent, y=0.55, thickness=0.5)
        if emblem and fd + 1 >= 3:
            m.decal(up, outer, emblem, color=accent, x=0.5, y=0.45)
        shoes.append(up)
    return shoes


def crown(m, head, color="accent", gem="gem", spikes=4):
    hw, _, hd = head.size
    band = m.box("crown", (max(hw - 2, 3), 2, max(hd - 2, 3)), mat=color, tags=("crown",)).on(
        head, at="top", sink=0.5, joint=False)
    bw, _, bd = band.size
    pts = [(-1, -1), (1, -1), (1, 1), (-1, 1), (0, -1), (0, 1), (-1, 0), (1, 0)][:spikes]
    for i, (sx, sz) in enumerate(pts):
        m.box(f"crown_spike{i + 1}", (1, 2, 1), mat=color).on(
            band, at=(sx * (1 - 1 / bw), 1, sz * (1 - 1 / bd)), sink=0.3, joint=False)
    if gem:
        m.decal(band, "front", "rect", color=gem, x=0.4, y=0.2, w=0.2, h=0.6)
    return band


def staff(m, hand, length=16, wood="wood", orb="glow", orb_size=3):
    """A staff gripped by `hand` (the grip point is inside the hand, so it can't float)."""
    if orb not in m.materials:
        m.mat("_orbe", orb, emissive=True, noise=0.0, bevel=0.0, ao=0.0)
        orb = "_orbe"
    shaft = m.box("staff", (1, length, 1), mat=wood, tags=("prop",)).on(
        hand, at=(0, -0.55, 0), anchor=(0, -0.3, 0), joint=False)
    head = m.box("staff_orb", (orb_size, orb_size, orb_size), mat=orb, tags=("prop",)).on(
        shaft, at="top", sink=0.5, joint=False)
    for s in (1, -1):
        m.box(f"staff_prong{'R' if s > 0 else 'L'}", (1, 3, 1), mat=wood).on(
            shaft, at=(s, 1, 0), anchor=(-s, -1, 0), sink=0, rot=(0, 0, -s * 20), joint=False)
    return shaft, head
