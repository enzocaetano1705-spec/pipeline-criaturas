"""Motor de pose da preguiça: IK de dois ossos, rotações locais para chaves do Blockbench e molas.

Convenção (igual a bbmodelo.matrizes_ossos e ao motor): rotação local em graus, matriz Rz·Ry·Rx,
aplicada em torno do pivô do osso no espaço do pai; todos os ossos têm rotação de repouso zero,
então a chave de rotação é a rotação local inteira. Posição é deslocamento no espaço do pai.
Frente da criatura = -Z, cima = +Y, direita da criatura = +X.
"""

from __future__ import annotations

import math

import numpy as np

from criaturas import bbmodelo


# ---------------- rotações ----------------

def rx(g):
    a = math.radians(g)
    return np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])


def ry(g):
    a = math.radians(g)
    return np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])


def rz(g):
    a = math.radians(g)
    return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])


def matriz(eul):
    return bbmodelo.matriz_rotacao(eul)


def euler(M, perto=None):
    """Graus (x, y, z) com Rz·Ry·Rx = M; entre as duas soluções, a mais próxima de `perto`."""
    sy = -M[2, 0]
    sy = max(-1.0, min(1.0, sy))
    y = math.asin(sy)
    if abs(M[2, 0]) < 0.99999:
        x = math.atan2(M[2, 1], M[2, 2])
        z = math.atan2(M[1, 0], M[0, 0])
    else:
        x = math.atan2(-M[1, 2], M[1, 1])
        z = 0.0
    a = np.degrees([x, y, z])
    b = np.array([a[0] + 180, 180 - a[1], a[2] + 180])  # mesma rotação
    cands = [a, b]
    if perto is None:
        return _envolver(a, np.zeros(3))
    cands = [_envolver(c, perto) for c in cands]
    return min(cands, key=lambda c: float(np.abs(c - perto).sum()))


def _envolver(a, ref):
    """Soma ±360 para ficar perto de `ref` (sem saltos entre quadros)."""
    return a + 360.0 * np.round((ref - a) / 360.0)


def rot_min(a, b):
    """Rotação mínima que leva o vetor a ao vetor b."""
    a = a / (np.linalg.norm(a) or 1)
    b = b / (np.linalg.norm(b) or 1)
    v = np.cross(a, b)
    c = float(np.clip(a @ b, -1, 1))
    s = np.linalg.norm(v)
    if s < 1e-9:
        if c > 0:
            return np.eye(3)
        eixo = np.cross(a, [1, 0, 0])
        if np.linalg.norm(eixo) < 1e-6:
            eixo = np.cross(a, [0, 1, 0])
        return eixo_angulo(eixo, 180.0)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / (s * s))


def alinhar(d0, n0, d1, n1):
    """Rotação que leva d0 em d1 e n0 em n1 (pares perpendiculares, unitários)."""
    F0 = np.column_stack([d0, n0, np.cross(d0, n0)])
    F1 = np.column_stack([d1, n1, np.cross(d1, n1)])
    U, _s, Vt = np.linalg.svd(F1 @ F0.T)  # ortonormaliza (pares quase perpendiculares)
    R = U @ Vt
    if np.linalg.det(R) < 0:
        U[:, -1] *= -1
        R = U @ Vt
    return R


def eixo_angulo(eixo, graus):
    e = np.asarray(eixo, float)
    e = e / (np.linalg.norm(e) or 1)
    a = math.radians(graus)
    K = np.array([[0, -e[2], e[1]], [e[2], 0, -e[0]], [-e[1], e[0], 0]])
    return np.eye(3) + math.sin(a) * K + (1 - math.cos(a)) * K @ K


def fracao(R, s):
    """Rotação parcial: s × o ângulo de R, mesmo eixo (0 = identidade, 1 = R)."""
    ang = math.degrees(math.acos(max(-1.0, min(1.0, (np.trace(R) - 1) / 2))))
    if ang < 1e-6:
        return np.eye(3)
    eixo = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])
    if np.linalg.norm(eixo) < 1e-9:
        w, v = np.linalg.eig(R)
        eixo = np.real(v[:, np.argmin(np.abs(w - 1))])
    return eixo_angulo(eixo, ang * s)


# ---------------- curvas ----------------

def suave(x):
    x = min(1.0, max(0.0, x))
    return x * x * x * (x * (6 * x - 15) + 10)


def onda(t, T, fase=0.0):
    return math.sin(2 * math.pi * (t / T + fase))


# ---------------- rig ----------------

class Rig:
    def __init__(self, modelo):
        self.m = modelo
        self.ossos = modelo.ossos
        self.chao = 1.0  # base dos pés no repouso

    def piv(self, nome):
        return self.ossos[nome].origem.copy()

    def mats(self, pose):
        """Matriz de mundo 4×4 de cada osso; a pose aceita 'matriz' (3×3) ou 'rotacao' (Euler) e 'posicao'."""
        feitas = {}

        def mat(n):
            if n in feitas:
                return feitas[n]
            o = self.ossos[n]
            e = pose.get(n, {})
            if "matriz" in e:
                R = e["matriz"]
            elif "rotacao" in e:
                R = matriz(e["rotacao"])
            else:
                R = np.eye(3)
            L = np.eye(4)
            L[:3, :3] = R
            L[:3, 3] = o.origem - R @ o.origem
            if "posicao" in e:
                T = np.eye(4)
                T[:3, 3] = e["posicao"]
                L = T @ L
            W = (mat(o.pai) if o.pai else np.eye(4)) @ L
            feitas[n] = W
            return W

        for n in self.ossos:
            mat(n)
        return feitas

    def ik(self, pose, cima, a, b, c, alvo, polo, charneira=False):
        """IK de dois ossos (a -> b -> c, pivôs de repouso). Grava rotações locais de a e b em `pose`.

        `cima` = osso pai de `a` (já posado). Devolve a rotação de mundo do osso b (para o efetor).
        charneira=True: além da direção, leva o eixo da junta do repouso (normal do plano a-b-c) para
        o eixo novo, então a e b dobram em volta do mesmo eixo, como dobradiça (joelho/cotovelo não
        torcem para fora do próprio bloco). Sem isso, a rotação mínima deixa o giro em volta do osso solto.
        """
        W = self.mats(pose)[cima]
        pa, pb, pc = self.piv(a), self.piv(b), self.piv(c)
        S = W[:3, :3] @ pa + W[:3, 3]
        L1, L2 = np.linalg.norm(pb - pa), np.linalg.norm(pc - pb)
        v = np.asarray(alvo, float) - S
        d = float(np.clip(np.linalg.norm(v), abs(L1 - L2) + 1e-3, L1 + L2 - 1e-3))
        dv = v / (np.linalg.norm(v) or 1)
        aa = (L1 * L1 - L2 * L2 + d * d) / (2 * d)
        h = math.sqrt(max(L1 * L1 - aa * aa, 0.0))
        p = np.asarray(polo, float)
        p = p - (p @ dv) * dv
        p = p / (np.linalg.norm(p) or 1)
        K = S + dv * aa + p * h
        T = S + dv * d
        Rp = W[:3, :3]
        n0 = np.cross(pb - pa, pc - pb)
        n1 = np.cross(K - S, T - K)
        if charneira and np.linalg.norm(n0) > 1e-6 and np.linalg.norm(n1) > 1e-6:
            n0, n1 = n0 / np.linalg.norm(n0), n1 / np.linalg.norm(n1)
            RA = alinhar((pb - pa) / L1, n0, (K - S) / L1, n1)
            RB = alinhar((pc - pb) / L2, n0, (T - K) / L2, n1)
        else:
            RA = rot_min(Rp @ ((pb - pa) / L1), (K - S) / L1) @ Rp
            RB = rot_min(RA @ ((pc - pb) / L2), (T - K) / L2) @ RA
        self._gravar(pose, a, Rp.T @ RA)
        self._gravar(pose, b, RA.T @ RB)
        return RB

    def mundo_para_local(self, pose, osso, R_mundo):
        """Rotação local de `osso` para que sua rotação de mundo seja R_mundo (pai já posado)."""
        pai = self.ossos[osso].pai
        Rp = self.mats(pose)[pai][:3, :3] if pai else np.eye(3)
        self._gravar(pose, osso, Rp.T @ R_mundo)

    @staticmethod
    def _gravar(pose, osso, R):
        pose.setdefault(osso, {})["matriz"] = R


def chaves(pose, anterior=None):
    """Converte a pose (matrizes) em rotações Euler sem salto em relação à pose anterior."""
    out = {}
    for osso, v in pose.items():
        ent = {}
        if "matriz" in v:
            ref = anterior.get(osso, {}).get("rotacao") if anterior else None
            ent["rotacao"] = euler(v["matriz"], ref)
        elif "rotacao" in v:
            ent["rotacao"] = np.asarray(v["rotacao"], float)
        if "posicao" in v:
            ent["posicao"] = np.asarray(v["posicao"], float)
        out[osso] = ent
    return out


def para_bbmodelo(pose):
    """Pose no formato de bbmodelo.matrizes_ossos (rotação em Euler)."""
    out = {}
    for osso, v in pose.items():
        e = {}
        if "matriz" in v:
            e["rotacao"] = euler(v["matriz"])
        elif "rotacao" in v:
            e["rotacao"] = v["rotacao"]
        if "posicao" in v:
            e["posicao"] = v["posicao"]
        out[osso] = e
    return out


class Mola:
    """Seguidor amortecido (gordura, cauda, pano): x'' = k (alvo - x) - c x'."""

    def __init__(self, freq=3.0, amort=0.35, dim=3):
        self.k = (2 * math.pi * freq) ** 2
        self.c = 2 * amort * math.sqrt(self.k)
        self.x = np.zeros(dim)
        self.v = np.zeros(dim)

    def passo(self, alvo, dt):
        a = self.k * (np.asarray(alvo, float) - self.x) - self.c * self.v
        self.v += a * dt
        self.x += self.v * dt
        return self.x.copy()
