"""Helpers numéricos independentes de bpy. Poses assadas, sem constraints no destino."""

import math

import numpy as np


def transform(pos, angles=(0, 0, 0)):
    x, y, z = np.radians(angles)
    cx, cy, cz, sx, sy, sz = math.cos(x), math.cos(y), math.cos(z), math.sin(x), math.sin(y), math.sin(z)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    m = np.eye(4)
    m[:3, :3], m[:3, 3] = rz @ ry @ rx, pos
    return m


def align_down(direction):
    """Rotação mínima de -Y para direction, estável para a cadeia da fixture."""
    a = np.array([0., -1., 0.])
    b = np.asarray(direction, float)
    b /= np.linalg.norm(b)
    v, c = np.cross(a, b), float(np.dot(a, b))
    if c < -.999999:
        raise ValueError("singularidade IK: perna invertida")
    k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + k + k @ k / (1 + c)


def ik(hip, ankle, upper, lower):
    d = np.asarray(ankle) - hip
    length = np.linalg.norm(d)
    if not abs(upper - lower) + 1e-5 < length < upper + lower - 1e-5:
        raise ValueError(f"IK fora de alcance: {length:.4f} para {upper:.4f}+{lower:.4f}")
    direction = d / length
    pole = np.array([0., 0., -1.])
    pole -= direction * np.dot(pole, direction)
    pole /= np.linalg.norm(pole)
    a = (upper * upper - lower * lower + length * length) / (2 * length)
    return hip + direction * a + pole * math.sqrt(max(0., upper * upper - a * a))


def smooth(x):
    x = max(0., min(1., x))
    return x*x*x*(10 + x*(-15 + 6*x))


def foot_path(phase, stance, stride, lift):
    """Apoio com velocidade constante; balanço Hermite C1 e altura sem quina."""
    p = phase % 1
    if p < stance:
        return -stride/2 + stride*p/stance, 0., True
    u = (p-stance)/(1-stance)
    # Velocidade igual à do apoio nos dois extremos, inclusive na volta do loop.
    tangent = stride * (1-stance)/stance
    z = (2*u**3-3*u*u+1)*stride/2 + (u**3-2*u*u+u)*tangent
    z += (-2*u**3+3*u*u)*(-stride/2) + (u**3-u*u)*tangent
    return z, lift * math.sin(math.pi*u)**2, False


def ordered(bones):
    result, pending = [], list(bones)
    while pending:
        ready = [b for b in pending if b["pai"] is None or b["pai"] in {v["nome"] for v in result}]
        if not ready:
            raise ValueError("ciclo no rig")
        result.extend(ready)
        pending = [b for b in pending if b not in ready]
    return result


def pose(job, clip, t):
    """Matrizes mundo, âncoras e apoios em unidades canônicas Y-up, frente -Z."""
    cfg = job["animacao"]
    duration = cfg["duracoes"][clip]
    u = min(1., max(0., t/duration))
    phase = 2*math.pi*u
    bones = ordered(job["plano"]["ossos"])
    rest = {b["nome"]: np.array(b["pivo"], float) for b in bones}
    offset = np.array([0., -.32 + .08*math.sin(phase), 0.])
    angles, swing, attack = [0., 0., 0.], 0., 0.
    if clip in ("walk", "run"):
        running = clip == "run"
        # Peso migra para a perna de apoio; não apenas alternar membros sob corpo parado.
        offset = np.array([-(1.15 if running else 1.25)*math.sin(phase),
                           (-.60 if running else -.42) + (.20 if running else .10)*math.cos(2*phase), 0.])
        angles = [(-10 if running else -3) + 2*math.sin(2*phase), 2*math.sin(phase), 0.]
        swing = (28 if running else 16)*math.sin(phase)
    elif clip == "attack_physical":
        # Antecipação -> investida/cabeçada -> recuperação suave. Sem root motion.
        if u <= .25:
            attack = -.4*smooth(u/.25)
        elif u <= .4:
            attack = -.4 + 1.4*smooth((u-.25)/.15)
        elif u <= .5:
            attack = 1. - .15*smooth((u-.4)/.1)
        else:
            attack = .85*(1-smooth((u-.5)/.5))
        offset = np.array([0., -.35 - .20*max(0, attack), -1.0*attack])
        angles = [-13*attack, 0., 0.]
    world = {}
    for bone in bones:
        n, parent = bone["nome"], bone["pai"]
        local = transform(rest[n] - (rest[parent] if parent else 0))
        if n == "body":
            local = transform(rest[n]-rest[parent]+offset, angles)
        elif n == "head":
            local = local @ transform([0, 0, 0], [3*math.sin(phase+.4) if clip == "idle" else -4*attack, 0, 0])
        elif n.startswith("tail_"):
            local = local @ transform([0, 0, 0], [2*math.sin(phase-.5), 5*math.sin(phase-.4), 0])
        elif n.startswith("arm_"):
            local = local @ transform([0, 0, 0], [swing*(-1 if n.endswith("left") else 1)-12*attack, 0, 0])
        world[n] = world[parent] @ local if parent else local
    feet = {}
    for i, side in enumerate(("left", "right")):
        leg, shin, foot = [f"{prefix}_{side}" for prefix in ("leg", "shin", "foot")]
        target = rest[foot].copy()
        contact = True
        if clip in ("walk", "run"):
            z, height, contact = foot_path(u + i*.5, cfg[f"apoio_{clip}"], cfg[f"passo_{clip}"], cfg[f"altura_{clip}"])
            target[1] += height
            target[2] += z
        hip = world[leg][:3, 3].copy()
        upper = float(np.linalg.norm(rest[shin] - rest[leg]))
        lower = float(np.linalg.norm(rest[foot] - rest[shin]))
        knee = ik(hip, target, upper, lower)
        world[leg] = transform(hip)
        world[leg][:3, :3] = align_down(knee - hip)
        world[shin] = transform(knee)
        world[shin][:3, :3] = align_down(target - knee)
        world[foot] = transform(target)
        feet[side] = {"alvo": target.tolist(), "apoio": contact}
    return world, feet
