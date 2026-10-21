"""Model description layer.

The agent never writes world coordinates. It declares parts and *relations*
("this box sits under that one, at its front-left corner") and the solver computes
positions, joints and pivots. Coordinates follow Blockbench: units = pixels,
Y up, front = -Z, the creature's right = +X.
"""
import re
import uuid
import numpy as np

from .mathutil import T, R, S, apply
from .style import PALETTES, Material, resolve_color


class ForjaError(Exception):
    pass


_AXIS_WORDS = {
    "top": (1, 1), "up": (1, 1), "cima": (1, 1), "topo": (1, 1),
    "bottom": (1, -1), "down": (1, -1), "baixo": (1, -1), "base": (1, -1),
    "front": (2, -1), "frente": (2, -1),
    "back": (2, 1), "tras": (2, 1), "atras": (2, 1),
    "right": (0, 1), "direita": (0, 1),
    "left": (0, -1), "esquerda": (0, -1),
}
_CENTER_WORDS = {"center", "centro", "middle", "meio", ""}

SIDE_TO_FACE = {"front": "north", "frente": "north", "back": "south", "tras": "south",
                "right": "east", "direita": "east", "left": "west", "esquerda": "west",
                "top": "up", "cima": "up", "topo": "up", "bottom": "down", "baixo": "down",
                "north": "north", "south": "south", "east": "east", "west": "west",
                "up": "up", "down": "down"}
MIRROR_FACE = {"east": "west", "west": "east"}

DIRS = {"down": (0, -1, 0), "up": (0, 1, 0), "front": (0, 0, -1), "back": (0, 0, 1),
        "right": (1, 0, 0), "left": (-1, 0, 0), "baixo": (0, -1, 0), "cima": (0, 1, 0),
        "frente": (0, 0, -1), "tras": (0, 0, 1), "direita": (1, 0, 0), "esquerda": (-1, 0, 0)}


def P(spec):
    """Parse a point on a box: words ('top front', 'bottom left=0.6'), a tuple (x,y,z)
    with each component in -1..1, or a dict {'y': 1, 'z': -0.5}."""
    if spec is None:
        return None
    if isinstance(spec, (tuple, list, np.ndarray)):
        v = np.array(spec, float)
        if v.shape != (3,):
            raise ForjaError(f"Ponto {spec!r} precisa ter 3 valores (x, y, z)")
        return v
    if isinstance(spec, dict):
        v = np.zeros(3)
        for k, val in spec.items():
            v["xyz".index(k)] = float(val)
        return v
    if isinstance(spec, str):
        v = np.zeros(3)
        for tok in re.split(r"[\s,]+", spec.strip().lower()):
            if tok in _CENTER_WORDS:
                continue
            m = re.match(r"^([a-z]+)(?:[=*:]([0-9.]+))?$", tok)
            if not m or m.group(1) not in _AXIS_WORDS:
                raise ForjaError(
                    f"Ponto desconhecido '{tok}'. Use top/bottom/front/back/left/right/center "
                    f"(ou cima/baixo/frente/tras/esquerda/direita/centro), 'front=0.5' "
                    f"para meio caminho, ou uma tupla (x, y, z) entre -1 e 1.")
            ax, sg = _AXIS_WORDS[m.group(1)]
            v[ax] = sg * (float(m.group(2)) if m.group(2) else 1.0)
        return v
    raise ForjaError(f"Ponto invalido: {spec!r}")


def dominant(v):
    a = np.abs(v)
    if a.max() < 1e-9:
        return np.zeros(3)
    for ax in (1, 0, 2):          # ties: vertical first, then sideways, then depth
        if a[ax] >= a.max() - 1e-9:
            n = np.zeros(3)
            n[ax] = np.sign(v[ax])
            return n


def _mspec(spec):
    if spec is None:
        return None
    v = P(spec).copy()
    v[0] = -v[0]
    return v


def _mvec(v):
    v = np.array(v, float).copy()
    v[0] = -v[0]
    return v


def _mrot(r):
    r = np.array(r, float).copy()
    r[1], r[2] = -r[1], -r[2]
    return r


class Bone:
    def __init__(self, name, parent, pivot, rot):
        self.name = name
        self.parent = parent
        self.pivot = np.array(pivot, float)
        self.rot = np.array(rot, float)
        self.boxes = []
        self.children = []
        self.uuid = str(uuid.uuid4())
        if parent is not None:
            parent.children.append(self)

    def __repr__(self):
        return f"Bone({self.name})"


class Socket:
    def __init__(self, name, box, at):
        self.name, self.box, self.at = name, box, P(at)
        self.uuid = str(uuid.uuid4())

    @property
    def point(self):
        return self.box.point(self.at)


class Box:
    """One cube. Create with Model.box(...) and place it with .on(...)."""

    def __init__(self, model, name, size, mat, tags=()):
        self.model = model
        self.name = name
        self.size = np.array(size, float)
        if self.size.shape != (3,) or (self.size < 0).any():
            raise ForjaError(f"Tamanho invalido para '{name}': {size!r} (use (largura, altura, profundidade))")
        self.mat = mat
        self.tags = set(tags)
        self.center = None
        self.bone = None
        self.rot = np.zeros(3)
        self.origin = None
        self.inflate = 0.0
        self.decals = []
        self.side = 0
        self.parent_box = None
        self.uuid = str(uuid.uuid4())

    def __repr__(self):
        return f"Box({self.name})"

    @property
    def frm(self):
        return self.center - self.size / 2

    @property
    def to(self):
        return self.center + self.size / 2

    def point(self, spec):
        return self.center + P(spec) * self.size / 2

    def tag(self, *tags):
        self.tags |= set(tags)
        return self

    def on(self, parent, at="top", anchor=None, sink=0.0, offset=(0, 0, 0), rot=(0, 0, 0),
           joint=True, mirror=False, pivot=None):
        """Place this box touching `parent`.

        at     -- point on the parent (words or (x,y,z) in -1..1)
        anchor -- point on this box that goes to `at` (default: the face opposite to
                  the main direction of `at`, so the box sits outside, flush)
        sink   -- push this box into the parent by N units along the contact normal
        offset -- extra shift in units (x, y, z)
        rot    -- rest rotation in degrees (x, y, z) around the joint
        joint  -- True: new bone with pivot at the contact point (it can animate).
                  False: rigid detail that belongs to the parent's bone.
        mirror -- also create the mirrored copy on the other side (returns a Pair)
        """
        if isinstance(parent, Pair):
            twin = self._clone()
            right = self._attach(parent.r, at, anchor, sink, offset, rot, joint, pivot, side=1)
            left = twin._attach(parent.l, _mspec(at), _mspec(anchor), sink, _mvec(offset),
                                _mrot(rot), joint, _mspec(pivot), side=-1)
            return Pair(right, left)
        if mirror:
            atv = P(at)
            if abs(atv[0]) < 1e-9 and abs(np.array(offset, float)[0]) < 1e-9:
                raise ForjaError(f"mirror=True em '{self.name}' precisa de um 'at' fora do centro (x != 0)")
            sign = 1 if (atv[0] + np.array(offset, float)[0]) > 0 else -1
            twin = self._clone()
            first = self._attach(parent, at, anchor, sink, offset, rot, joint, pivot, side=sign)
            second = twin._attach(parent, _mspec(at), _mspec(anchor), sink, _mvec(offset),
                                  _mrot(rot), joint, _mspec(pivot), side=-sign)
            return Pair(first, second) if sign > 0 else Pair(second, first)
        return self._attach(parent, at, anchor, sink, offset, rot, joint, pivot)

    def _clone(self):
        b = self.model.box(self.name, self.size.copy(), self.mat, self.tags)
        b.inflate = self.inflate
        b.decals = [(k, MIRROR_FACE.get(f, f), dict(p)) for (k, f, p) in self.decals]
        return b

    def _attach(self, parent, at, anchor, sink, offset, rot, joint, pivot, side=0):
        if self.center is not None:
            raise ForjaError(f"'{self.name}' ja foi posicionado")
        if parent.center is None:
            raise ForjaError(f"O pai '{parent.name}' de '{self.name}' ainda nao foi posicionado")
        atv = P(at)
        n = dominant(atv)
        ancv = P(anchor) if anchor is not None else -n
        attach_pt = parent.center + atv * parent.size / 2 + np.array(offset, float) - sink * n
        self.center = attach_pt - ancv * self.size / 2
        if side:
            self.name = f"{self.name}_{'R' if side > 0 else 'L'}"
            self.side = side
        pv = attach_pt if pivot is None else self.point(pivot)
        rot = np.array(rot, float)
        if joint:
            self.bone = self.model._new_bone(self.name, parent.bone, pv, rot)
        else:
            self.bone = parent.bone
            if np.any(np.abs(rot) > 1e-9):
                self.rot = rot
                self.origin = pv
        self.bone.boxes.append(self)
        self.parent_box = parent
        return self


class Pair:
    """A mirrored right/left pair. Attaching to a Pair attaches to both sides."""

    def __init__(self, r, l):
        self.r, self.l = r, l

    def __iter__(self):
        yield self.r
        yield self.l

    def __repr__(self):
        return f"Pair({self.r.name}, {self.l.name})"

    @property
    def name(self):
        return self.r.name[:-2]

    def tag(self, *tags):
        for b in self:
            b.tag(*tags)
        return self


def _items(x):
    if isinstance(x, Pair):
        return [x.r, x.l]
    if isinstance(x, (list, tuple)):
        out = []
        for i in x:
            out += _items(i)
        return out
    return [x]


class Model:
    def __init__(self, name, palette="default", texel=2, bevel=0.45, ao=2.4, dither=1.0,
                 ground_ao=True):
        self.name = name
        if isinstance(palette, dict):
            self.palette = dict(PALETTES["default"], **palette)
        else:
            if palette not in PALETTES:
                raise ForjaError(f"Paleta '{palette}' nao existe: {', '.join(PALETTES)}")
            self.palette = dict(PALETTES["default"], **PALETTES[palette])
        self.texel = int(texel)
        self.bevel = bevel
        self.ao = ao
        self.dither = dither
        self.ground_ao = ground_ao
        self.boxes = []
        self.bones = []
        self.materials = {}
        self.anims = []
        self.sockets = []
        self.rig = None
        self._final = False

    # ---------------------------------------------------------------- parts
    def box(self, name, size, mat="primary", tags=()):
        b = Box(self, name, size, mat, tags)
        self.boxes.append(b)
        return b

    def root(self, name, size, mat="primary", pivot="center", tags=()):
        """The first part. Everything else attaches to it (directly or not)."""
        b = self.box(name, size, mat, tags)
        b.center = np.zeros(3)
        b.bone = self._new_bone(name, None, b.point(pivot), (0, 0, 0))
        b.bone.boxes.append(b)
        return b

    def chain(self, name, parent, at, sizes, dir="down", first=(0, 0, 0), bend=(0, 0, 0),
              rots=None, sink=0.5, mat="primary", mirror=False, tags=(), tip_tags=()):
        """A jointed chain (tail, tentacle, neck, antenna). Each segment gets its own bone.
        dir: growth direction. first: rotation at the base joint. bend: rotation added at
        every following joint (curls the chain). rots: explicit list, one per segment."""
        d = np.array(DIRS[dir], float)
        out, prev = [], parent
        for i, s in enumerate(sizes):
            r = rots[i] if rots is not None else (first if i == 0 else bend)
            b = self.box(f"{name}{i + 1}", s, mat, tags)
            if i == len(sizes) - 1:
                b.tag(*tip_tags)
            if i == 0:
                prev = b.on(prev, at=at, anchor=-d, sink=sink, rot=r, mirror=mirror)
            else:
                prev = b.on(prev, at=d, anchor=-d, sink=sink, rot=r)
            out.append(prev)
        return out

    def _new_bone(self, name, parent, pivot, rot):
        b = Bone(name, parent, pivot, rot)
        self.bones.append(b)
        return b

    # ------------------------------------------------------------ materials
    def mat(self, name, color="primary", second=None, pattern=None, **kw):
        resolve_color(self.palette, color)
        if second is not None:
            resolve_color(self.palette, second)
        self.materials[name] = Material(name, color, second, pattern, **kw)
        return self.materials[name]

    def material(self, name):
        if name not in self.materials:
            if name in self.palette or (isinstance(name, str) and name.startswith('#')):
                self.materials[name] = Material(name, name)
            else:
                raise ForjaError(f"Material '{name}' nao definido. Use m.mat('{name}', ...) ou um "
                                 f"papel da paleta: {', '.join(sorted(self.palette))}")
        return self.materials[name]

    # --------------------------------------------------------- decorations
    def face(self, box, side="front", eyes="round", mouth="smile", blush=False, eye_y=0.6,
             eye_gap=0.36, eye_size=None, mouth_y=0.25, mouth_w=None, brows=None,
             eye_color="eye", count=2):
        """Pixel-art face on one side of a box: eyes, mouth, blush, brows."""
        p = dict(eyes=eyes, mouth=mouth, blush=blush, eye_y=eye_y, eye_gap=eye_gap,
                 eye_size=eye_size, mouth_y=mouth_y, mouth_w=mouth_w, brows=brows,
                 eye_color=eye_color, count=count)
        return self.decal(box, side, "face", **p)

    def decal(self, box, side, kind, **params):
        """Flat details painted on one face: laces, stripe, bolt, star, heart, shine,
        nostrils, claws, rect, seam, face."""
        key = SIDE_TO_FACE[side]
        if isinstance(box, Pair):
            box.r.decals.append((kind, key, dict(params)))
            box.l.decals.append((kind, MIRROR_FACE.get(key, key), dict(params)))
        else:
            for b in _items(box):
                b.decals.append((kind, key, dict(params)))
        return box

    def socket(self, name, box, at="bottom"):
        """Named attachment point (exported as a Blockbench locator)."""
        if isinstance(box, Pair):
            self.sockets.append(Socket(name + "_R", box.r, at))
            self.sockets.append(Socket(name + "_L", box.l, _mspec(at)))
        else:
            self.sockets.append(Socket(name, box, at))

    def anim(self, name, length, loop=True, samples=12):
        from .anim import Anim
        for a in self.anims:
            if a.name == name:
                return a
        a = Anim(name, length, loop, samples)
        self.anims.append(a)
        return a

    # ------------------------------------------------------------- solving
    def bone_matrices(self, anim=None, t=0.0):
        mats = {}
        for b in self.bones:
            rot, pos, scl = b.rot.copy(), np.zeros(3), np.ones(3)
            if anim is not None:
                v = anim.value(b.name, "rotation", t)
                if v is not None:
                    rot = rot + v
                v = anim.value(b.name, "position", t)
                if v is not None:
                    pos = v
                v = anim.value(b.name, "scale", t)
                if v is not None:
                    scl = v
            local = b.pivot - (b.parent.pivot if b.parent is not None else 0)
            ml = T(local + pos) @ R(rot) @ S(scl)
            mats[b] = mats[b.parent] @ ml if b.parent is not None else ml
        return mats

    def box_matrix(self, box, mats):
        mb = mats[box.bone]
        if box.origin is not None and np.any(box.rot):
            return mb @ T(box.origin - box.bone.pivot) @ R(box.rot) @ T(-box.origin)
        return mb @ T(-box.bone.pivot)

    def corners(self, box, mats, inflate=True):
        h = box.size / 2 + (box.inflate if inflate else 0)
        sgn = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], float)
        return apply(self.box_matrix(box, mats), box.center + sgn * h)

    def obbs(self, mats, boxes=None):
        boxes = self.boxes if boxes is None else boxes
        c, a, h = [], [], []
        for b in boxes:
            w = self.box_matrix(b, mats)
            c.append(apply(w, b.center[None])[0])
            ax = w[:3, :3]
            a.append(ax / np.linalg.norm(ax, axis=0, keepdims=True))
            h.append(np.maximum(b.size / 2 * np.linalg.norm(ax, axis=0) + b.inflate, 1e-3))
        return np.array(c).reshape(-1, 3), np.array(a).reshape(-1, 3, 3), np.array(h).reshape(-1, 3)

    def finalize(self):
        """Check placement, make names unique and stand the model on y=0."""
        if self._final:
            return self
        loose = [b.name for b in self.boxes if b.center is None]
        if loose:
            raise ForjaError("Pecas sem posicao (faltou .on(...)): " + ", ".join(loose))
        for b in self.boxes:
            self.material(b.mat)
        seen = {}
        for coll in (self.boxes, self.bones):
            seen.clear()
            for item in coll:
                base = item.name
                if base in seen:
                    seen[base] += 1
                    item.name = f"{base}{seen[base]}"
                else:
                    seen[base] = 1
        mats = self.bone_matrices()
        allv = np.concatenate([self.corners(b, mats) for b in self.boxes])
        zc = (allv[:, 2].min() + allv[:, 2].max()) / 2
        shift = np.array([0.0, -allv[:, 1].min(), -np.round(zc * 2) / 2])
        for b in self.boxes:
            b.center = b.center + shift
            if b.origin is not None:
                b.origin = b.origin + shift
        for bone in self.bones:
            bone.pivot = bone.pivot + shift
        self._final = True
        return self

    def dims(self, mats=None):
        mats = self.bone_matrices() if mats is None else mats
        allv = np.concatenate([self.corners(b, mats) for b in self.boxes])
        return allv.max(0) - allv.min(0)
