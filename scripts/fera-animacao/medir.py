"""Mede um clipe: oscilações por passada de cada parte, amplitude, frestas nas juntas e perna × braço.

Uso: uv run python scripts/fera-animacao/medir.py <base-rig.bbmodel> <clipe>
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from clips import Locomocao  # noqa: E402
from pose import Rig, chaves  # noqa: E402

from criaturas import bbmodelo  # noqa: E402


def pontos(m, mats, ossos, passo=1.0):
    out = []
    for c in m.cubos:
        if c.osso not in ossos:
            continue
        a, b = c.de, c.ate
        eixos = [np.arange(a[k] + passo / 2, b[k], passo) if b[k] - a[k] > passo else np.array([(a[k] + b[k]) / 2]) for k in range(3)]
        g = np.stack(np.meshgrid(*eixos, indexing="ij"), -1).reshape(-1, 3)
        M = np.eye(4)
        if np.any(c.rotacao):
            R = bbmodelo.matriz_rotacao(c.rotacao)
            M[:3, :3], M[:3, 3] = R, c.origem - R @ c.origem
        W = mats[c.osso] @ M
        out.append(g @ W[:3, :3].T + W[:3, 3])
    return np.concatenate(out) if out else np.zeros((0, 3))


def main():
    rig = Rig(bbmodelo.ler(sys.argv[1]))
    loc = Locomocao(rig)
    T, q, _ = getattr(loc, sys.argv[2])()
    q = q[:-1]
    series = {}
    ant = None
    for _t, pose in q:
        ch = chaves(pose, ant)
        ant = ch
        for osso, e in ch.items():
            for canal in ("rotacao", "posicao"):
                if canal in e:
                    for k, eixo in enumerate("xyz"):
                        series.setdefault(f"{osso}.{canal[:3]}.{eixo}", []).append(e[canal][k])
    linhas = []
    for nome, v in series.items():
        v = np.asarray(v)
        if np.ptp(v) < 1.0 and ".pos." not in nome:
            continue
        if ".pos." in nome and np.ptp(v) < 0.05:
            continue
        F = np.abs(np.fft.rfft(v - v.mean()))
        F[0] = 0
        linhas.append((nome, int(np.argmax(F)), float(np.ptp(v))))
    fora = [l for l in linhas if l[1] != 1]
    print(f"{len(linhas)} canais animados; fora do ritmo da passada: {[(n, h) for n, h, _ in fora][:12] or 'nenhum'}")
    for n, h, a in sorted(linhas, key=lambda l: -l[2])[:8]:
        print(f"   {n:24s} {h} ciclo(s)/passada  amplitude {a:.1f}")
    trans = [n for n in series if ".pos." in n and not n.startswith("body.")]
    print("ossos com translação além do body:", sorted({n.split('.')[0] for n in trans}) or "nenhum")
    # frestas: menor distância entre os cubos de cada osso e os do pai (com cubos)
    pares = []
    for nome, o in rig.ossos.items():
        pai = o.pai
        while pai and not any(c.osso == pai for c in rig.m.cubos):
            pai = rig.ossos[pai].pai
        if pai and any(c.osso == nome for c in rig.m.cubos):
            pares.append((nome, pai))
    pior = {}
    for _t, pose in q[::2]:
        mats = rig.mats(pose)
        for filho, pai in pares:
            A, B = pontos(rig.m, mats, {filho}), pontos(rig.m, mats, {pai})
            if len(A) > 600:
                A = A[:: len(A) // 600 + 1]
            if len(B) > 600:
                B = B[:: len(B) // 600 + 1]
            d = float(np.sqrt(((A[:, None] - B[None]) ** 2).sum(-1)).min())
            pior[filho] = max(pior.get(filho, 0), d)
    frestas = sorted(((d, n) for n, d in pior.items() if d > 1.2), reverse=True)
    print("frestas nas juntas (> 1,2):", [(n, round(d, 1)) for d, n in frestas] or "nenhuma")
    # perna × braço: amostras no centro de células de 1 unidade, então < 1,0 = cubos se tocando ou entrando
    pernas = {f"{o}_{l}" for o in ("leg", "shin", "foot") for l in ("left", "right")}
    bracos = {f"{o}_{l}" for o in ("arm", "forearm", "hand") for l in ("left", "right")}
    bracos |= {n for n in rig.ossos if n.startswith("claw_")}
    dist = []
    for t, pose in q:
        mats = rig.mats(pose)
        A, B = pontos(rig.m, mats, pernas), pontos(rig.m, mats, bracos)
        dist.append((float(np.sqrt(((A[:, None] - B[None]) ** 2).sum(-1)).min()), t))
    dmin, tmin = min(dist)
    encosta = sum(1 for d, _t in dist if d < 1.0)
    print(f"perna × braço: menor distância {dmin:.1f} (t={tmin:.2f}s); quadros encostando: {encosta}/{len(dist)}")


if __name__ == "__main__":
    main()
