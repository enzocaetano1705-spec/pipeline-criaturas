"""Procedural animation. Motions are functions of time computed from gait patterns,
then baked to keyframes on export. The agent picks a gait; it never writes keyframes."""
import numpy as np

TAU = 2 * np.pi


class Anim:
    def __init__(self, name, length, loop=True, samples=12):
        self.name = name
        self.length = float(length)
        self.loop = loop
        self.samples = samples
        self.tracks = {}

    @staticmethod
    def _bone_name(target):
        from .core import Box, Bone
        if isinstance(target, Box):
            return target.bone.name
        if isinstance(target, Bone):
            return target.name
        return str(target)

    def add(self, target, channel, fn):
        self.tracks.setdefault(self._bone_name(target), {}).setdefault(channel, []).append(fn)
        return self

    def rot(self, target, fn):
        return self.add(target, "rotation", fn)

    def pos(self, target, fn):
        return self.add(target, "position", fn)

    def scale(self, target, fn):
        return self.add(target, "scale", fn)

    def value(self, bone_name, channel, t):
        fns = self.tracks.get(bone_name, {}).get(channel)
        if not fns:
            return None
        if channel == "scale":
            v = np.ones(3)
            for f in fns:
                v = v * np.asarray(f(t), float)
            return v
        return sum(np.asarray(f(t), float) for f in fns)

    def keyframes(self):
        """{bone: {channel: [(time, (x,y,z)), ...]}} sampled over one loop."""
        times = np.linspace(0, self.length, self.samples + 1)
        out = {}
        for bone, chans in self.tracks.items():
            for ch in chans:
                vals = [(float(t), self.value(bone, ch, t)) for t in times]
                neutral = np.ones(3) if ch == "scale" else np.zeros(3)
                if all(np.allclose(v, neutral, atol=1e-3) for _, v in vals):
                    continue
                out.setdefault(bone, {})[ch] = vals
        return out


def _ph(t, period, phase=0.0):
    return TAU * (t / period + phase)


def _bob(amount, period):
    return lambda t: (0, amount * (1 - np.cos(2 * _ph(t, period))) / 2, 0)


def breathe(m, body, period=2.4, amount=0.03, anim="idle"):
    a = m.anim(anim, period, samples=12)
    a.scale(body, lambda t: (1 + amount * np.sin(_ph(t, period)) * 0.6,
                             1 + amount * np.sin(_ph(t, period)),
                             1 + amount * np.sin(_ph(t, period)) * 0.6))
    return a


def sway_chain(a, chain, period, amp=10.0, axis=1, lag=0.12, phase=0.0, grow=1.15):
    for k, seg in enumerate(chain):
        for b in (seg if hasattr(seg, 'r') else [seg]):
            sgn = 1 if getattr(b, 'side', 0) >= 0 else -1
            amp_k = amp * grow ** k

            def f(t, k=k, amp_k=amp_k, sgn=sgn):
                v = [0.0, 0.0, 0.0]
                v[axis] = amp_k * np.sin(_ph(t, period, phase - k * lag)) * (sgn if axis != 0 else 1)
                return v
            a.rot(b, f)


def walk_quadruped(m, rig, period=0.8, swing=26.0, bob=0.5):
    a = m.anim("walk", period, samples=12)
    phase = {"FR": 0.0, "BL": 0.0, "FL": 0.5, "BR": 0.5}
    for key, leg in rig.legs.items():
        a.rot(leg, lambda t, p=phase[key]: (swing * np.sin(_ph(t, period, p)), 0, 0))
    a.pos(rig.body, _bob(bob, period))
    if rig.head is not None:
        a.rot(rig.head, lambda t: (3 * np.sin(2 * _ph(t, period) + 0.6), 0, 0))
    if rig.tail:
        sway_chain(a, rig.tail, period, amp=9, axis=1, lag=0.12)
    if rig.wings is not None:
        for w in rig.wings:
            sg = 1 if w.side > 0 else -1
            a.rot(w, lambda t, sg=sg: (0, 0, sg * 6 * np.sin(2 * _ph(t, period))))
    return a


def idle_quadruped(m, rig, period=2.4):
    a = breathe(m, rig.body, period)
    if rig.head is not None:
        a.rot(rig.head, lambda t: (2.5 * np.sin(_ph(t, period, 0.2)), 4 * np.sin(_ph(t, period / 2 * 2, 0.1)), 0))
    if rig.tail:
        sway_chain(a, rig.tail, period, amp=7, axis=1, lag=0.08)
    if rig.wings is not None:
        for w in rig.wings:
            sg = 1 if w.side > 0 else -1
            a.rot(w, lambda t, sg=sg: (0, 0, sg * 9 * np.sin(_ph(t, period / 2))))
    return a


def walk_hexapod(m, rig, period=0.6, sweep=18.0, lift=12.0):
    """Tripod gait: front-right, middle-left, back-right move together."""
    a = m.anim("walk", period, samples=12)
    group_a = {"1R", "2L", "3R"}
    for key, leg in rig.legs.items():
        p = 0.0 if key in group_a else 0.5
        sg = 1 if key.endswith("R") else -1
        a.rot(leg, lambda t, p=p, sg=sg: (0, sg * sweep * np.sin(_ph(t, period, p)),
                                            sg * lift * max(0.0, np.cos(_ph(t, period, p)))))
    a.pos(rig.body, _bob(0.25, period))
    if rig.antennae:
        sway_chain(a, rig.antennae, period, amp=6, axis=0, lag=0.1)
    return a


def idle_hexapod(m, rig, period=2.0):
    a = breathe(m, rig.body, period, amount=0.02)
    if rig.antennae:
        sway_chain(a, rig.antennae, period, amp=8, axis=0, lag=0.15)
    return a


def wave_tentacles(m, rig, name="walk", period=1.2, amp=11.0, lag=0.11, bob=0.6):
    a = m.anim(name, period, samples=12)
    n = len(rig.tentacles)
    for i, (u, chain) in enumerate(zip(rig.dirs, rig.tentacles)):
        for k, seg in enumerate(chain):
            amp_k = amp * (0.6 + 0.4 * k)

            def f(t, k=k, i=i, amp_k=amp_k, u=u):
                al = amp_k * np.sin(_ph(t, period, i / n - k * lag))
                return (-al * u[1], 0.0, al * u[0])
            a.rot(seg, f)
    a.pos(rig.body, _bob(bob, period / 2))
    a.scale(rig.body, lambda t: (1 + 0.025 * np.sin(_ph(t, period)), 1 - 0.03 * np.sin(_ph(t, period)),
                                 1 + 0.025 * np.sin(_ph(t, period))))
    return a


def hop_blob(m, rig, period=1.0, height=4.0, squash=0.2):
    """Slime hop with squash & stretch. The body bone pivots at its bottom."""
    a = m.anim("walk", period, samples=16)

    def air(u):
        return np.sin(np.pi * (u - 0.2) / 0.6) if 0.2 <= u <= 0.8 else 0.0

    def sy(t):
        u = (t / period) % 1.0
        s = 1.0
        s -= squash * np.exp(-((u - 0.08) / 0.07) ** 2)
        s -= squash * 0.8 * np.exp(-((u - 0.92) / 0.06) ** 2)
        s += squash * 0.7 * np.exp(-((u - 0.3) / 0.08) ** 2)
        return s

    a.pos(rig.body, lambda t: (0, height * air((t / period) % 1.0), 0))
    a.scale(rig.body, lambda t: (1 / np.sqrt(sy(t)), sy(t), 1 / np.sqrt(sy(t))))
    if rig.extras:
        sway_chain(a, rig.extras, period, amp=10, axis=2, lag=0.2)
    return a


def jiggle_blob(m, rig, period=1.6):
    a = m.anim("idle", period, samples=12)
    a.scale(rig.body, lambda t: (1 + 0.04 * np.sin(_ph(t, period)), 1 - 0.05 * np.sin(_ph(t, period)),
                                 1 + 0.04 * np.sin(_ph(t, period))))
    if rig.extras:
        sway_chain(a, rig.extras, period, amp=7, axis=2, lag=0.25)
    return a


def walk_biped(m, rig, period=0.9, swing=28.0):
    a = m.anim("walk", period, samples=12)
    for leg in rig.legs.values():
        sg = 1 if leg.side > 0 else -1
        a.rot(leg, lambda t, sg=sg: (sg * swing * np.sin(_ph(t, period)), 0, 0))
    for arm in rig.arms.values():
        sg = 1 if arm.side > 0 else -1
        a.rot(arm, lambda t, sg=sg: (-sg * swing * 0.7 * np.sin(_ph(t, period)), 0, 0))
    a.pos(rig.body, _bob(0.5, period))
    if rig.head is not None:
        a.rot(rig.head, lambda t: (0, 3 * np.sin(_ph(t, period)), 0))
    return a


def idle_biped(m, rig, period=2.6):
    a = breathe(m, rig.body, period, amount=0.02)
    for arm in rig.arms.values():
        sg = 1 if arm.side > 0 else -1
        a.rot(arm, lambda t, sg=sg: (2.5 * np.sin(_ph(t, period)), 0, sg * 2 * np.sin(_ph(t, period))))
    if rig.head is not None:
        a.rot(rig.head, lambda t: (2 * np.sin(_ph(t, period, 0.25)), 0, 0))
    return a
