"""Combate da preguiça rogue: postura em tripé (patas de trás + cauda) com cara de assassino.

Ideia: o tamanduá-bandeira, ameaçado, fica de pé nas patas de trás apoiado na cauda e abre as garras;
para não virar um urso de pelúcia em pé, a guarda é a de um ninja (Greninja): base baixa, larga e
escalonada, joelhos bem dobrados, o tronco empinado sobre o quadril mas curvado para a frente
(ombros rolados, cabeça baixa e firme no alvo), corpo torcido mostrando o ombro da frente, a garra da
frente baixa apontando para o alvo e a de trás recolhida atrás do quadril (lâmina guardada), o pé de
trás na ponta (pronto para o bote). A cauda apoia no chão atrás como a terceira perna, com a ponta
subindo pouco (erguida demais lembra esquilo). Tudo respira pesado (gordura), pronto para sumir.
"""

from __future__ import annotations

import math

import numpy as np

from clips import FPS, LADOS, Locomocao
from pose import eixo_angulo, matriz, rot_min, rx, suave

GUARDA = dict(
    empina=36.0,  # corpo gira para cima em volta do quadril (o tripé)
    torce=-26.0,  # corpo de lado, ombro esquerdo para o alvo
    inclina=0.0,
    agacha=5.0,  # quadril desce (joelhos bem dobrados)
    recua=1.0,  # quadril vai um pouco para trás (peso na cauda)
    pelve=0.0, cintura=-8.0, peito=-20.0,  # corcunda: o tronco se curva para a frente por cima do quadril
    torce_cintura=6.0, torce_peito=4.0,
    abre=1.3,  # base larga
    passo_left=-6.0, passo_right=3.5,  # pé esquerdo à frente, direito atrás
    ponta_left=6.0,  # o da frente quase chato (calcanhar um tiquinho erguido)
    ponta_right=28.0,  # pé de trás na ponta: calcanhar erguido (graus); a canela não deita no chão
    # garra da frente (esquerda): baixa, à frente, apontando para o alvo
    punho_frente=(-1.0, -7.0, -13.5), garra_frente=(0.05, -0.08, -1.0), giro_frente=-20.0,
    polo_frente=(-0.8, -0.5, 0.3),
    # garra de trás (direita): recolhida atrás do quadril, garras para trás e para baixo (lâmina guardada)
    punho_tras=(2.0, -8.0, 6.0), garra_tras=(0.3, -0.5, 0.8), giro_tras=0.0,
    polo_tras=(0.5, -0.7, 0.6),  # cotovelo para baixo e para trás (para cima vira asa de frango)
    curva_garras=0.35,  # garras abertas e um pouco curvadas
    olhar=-10.0, inclina_cabeca=-6.0,  # cabeça baixa (olha por baixo da testa) e um pouco inclinada
    cauda=(-59.0, -20.0, 6.0, 18.0, 26.0),  # inclinação de mundo de cada gomo: apoia e a ponta sobe pouco
    fita=(10.0, 8.0, 6.0, 5.0, 4.0),  # cachecol caído para trás
)
T_GUARDA = 3.2  # um loop com uma piscada (ritmo natural)


class Combate:
    def __init__(self, loc: Locomocao):
        self.loc, self.r = loc, loc.r
        r = self.r
        self.P = r.piv("body")
        self.quadril = (r.piv("leg_left") + r.piv("leg_right")) / 2
        self.d_garras = {}
        for lado, _s in LADOS:
            ds = [loc._ponta_garra(f"claw_{lado}_{n}") - r.piv(f"claw_{lado}_{n}") for n in (1, 2, 3)]
            self.d_garras[lado] = np.mean(ds, axis=0)
        # gomos da cauda: direção de repouso de cada um (pivô ao próximo; o último segue o próprio cubo)
        self.gomos = [f"tail_{k}" for k in range(1, 6)]
        self.d_gomo = {}
        for i, g in enumerate(self.gomos):
            if i + 1 < len(self.gomos):
                self.d_gomo[g] = r.piv(self.gomos[i + 1]) - r.piv(g)
            else:
                c = next(c for c in r.m.cubos if c.osso == g)
                self.d_gomo[g] = (c.de + c.ate) / 2 - r.piv(g)

    # ---------- pedaços ----------

    def corpo(self, pose, cfg, extra=np.zeros(3), sobe=0.0):
        R = matriz([cfg["empina"] + extra[0], cfg["torce"] + extra[1], cfg["inclina"] + extra[2]])
        H = self.quadril + np.array([0.0, -cfg["agacha"] + sobe, cfg["recua"]])
        pose["body"] = {"matriz": R, "posicao": H - self.P - R @ (self.quadril - self.P)}

    def braco(self, pose, lado, s, punho_rel, garra_dir, giro, polo):
        """Punho num ponto relativo ao ombro (no mundo), garras apontando para garra_dir."""
        r = self.r
        W = r.mats(pose)["torso"]
        ombro = W[:3, :3] @ r.piv(f"arm_{lado}") + W[:3, 3]
        alvo = ombro + np.asarray(punho_rel, float)
        r.ik(pose, "torso", f"arm_{lado}", f"forearm_{lado}", f"hand_{lado}", alvo, np.asarray(polo, float))
        d = np.asarray(garra_dir, float)
        d = d / np.linalg.norm(d)
        r.mundo_para_local(pose, f"hand_{lado}", eixo_angulo(d, giro) @ rot_min(self.d_garras[lado], d))

    def cauda_tripe(self, pose, angulos, yaw=0.0):
        """Cada gomo com a inclinação de mundo pedida (negativa = desce); escala até a cauda tocar o chão."""
        r = self.r

        def montar(esc):
            for g, beta in zip(self.gomos, angulos):
                pose[g] = {"matriz": np.eye(3)}
                Wp = r.mats(pose)[r.ossos[g].pai][:3, :3]
                d = self.d_gomo[g]
                alvo = math.radians(beta * esc)

                def elev(a):
                    v = Wp @ rx(a) @ d
                    return math.atan2(v[1], math.hypot(v[0], v[2]))

                lo, hi = -120.0, 120.0  # rotação em X positiva baixa o que fica atrás do pivô
                for _ in range(40):
                    mid = (lo + hi) / 2
                    if elev(mid) > alvo:
                        lo = mid
                    else:
                        hi = mid
                pose[g] = {"matriz": rx((lo + hi) / 2) @ matriz([0, yaw, 0])}
            return self._menor_y_cauda(pose)

        lo, hi = 0.0, 1.6
        for _ in range(25):  # o quanto a cauda desce até encostar (folga de 0,05)
            mid = (lo + hi) / 2
            if montar(mid) > self.loc.chao + 0.05:
                lo = mid
            else:
                hi = mid
        montar(lo)

    def pe(self, pose, lado, s, alvo, ponta=0.0):
        """Pé plantado; ponta > 0 ergue o calcanhar (só a ponta no chão), subindo o tornozelo o preciso."""
        loc = self.loc
        alvo = np.array(alvo, float)
        for _ in range(4):
            loc.perna(pose, lado, s, alvo, -ponta)
            falta = loc.chao - self._menor_y(pose, (f"foot_{lado}",))
            if abs(falta) < 1e-3:
                break
            alvo[1] += falta

    def maos_acima_do_chao(self, pose, folga=0.3):
        """Se a mão ou uma garra encostar no chão (nas transições), gira o braço no ombro até sair."""
        r = self.r
        for lado, _s in LADOS:
            ossos = (f"hand_{lado}",) + tuple(f"claw_{lado}_{n}" for n in (1, 2, 3))
            for _ in range(4):
                menor, ponto = self._menor_ponto(pose, ossos)
                falta = self.loc.chao + folga - menor
                if falta <= 1e-3:
                    break
                W = r.mats(pose)[f"arm_{lado}"]
                v = ponto - (W[:3, :3] @ r.piv(f"arm_{lado}") + W[:3, 3])
                eixo = np.cross(v, [0.0, 1.0, 0.0])  # girar em volta deste eixo levanta o ponto
                ang = math.degrees(math.atan2(falta, max(np.linalg.norm(v), 1.0))) * 1.1
                r.mundo_para_local(pose, f"arm_{lado}", eixo_angulo(eixo, ang) @ W[:3, :3])

    def _menor_y_cauda(self, pose):
        return self._menor_y(pose, tuple(self.gomos))

    def _menor_y(self, pose, ossos):
        return self._menor_ponto(pose, ossos)[0]

    def _menor_ponto(self, pose, ossos):
        mats = self.r.mats(pose)
        menor, ponto = np.inf, None
        for c in self.r.m.cubos:
            if c.osso in ossos:
                a, b = c.de, c.ate
                cantos = np.array([[x, y, z] for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])])
                M = mats[c.osso] @ self.loc._mat_cubo(c)
                w = cantos @ M[:3, :3].T + M[:3, 3]
                i = int(np.argmin(w[:, 1]))
                if w[i, 1] < menor:
                    menor, ponto = float(w[i, 1]), w[i]
        return menor, ponto

    # ---------- postura ----------

    def pose_guarda(self, cfg=None, t=0.0, T=T_GUARDA):
        """Guarda em tripé no tempo t do loop: respiração pesada (2 por loop), a garra da frente se
        crispa e estala uma vez, a ponta da cauda e o cachecol não param."""
        cfg = dict(GUARDA, **(cfg or {}))
        loc, r = self.loc, self.r
        pose = {}
        fase = t / T
        resp = math.sin(4 * math.pi * fase)  # duas respirações por loop (~1,6 s cada)
        resp_atr = math.sin(4 * math.pi * (fase - 0.04))
        self.corpo(pose, cfg, extra=np.array([0.9 * resp, 0.0, 0.7 * math.sin(2 * math.pi * (fase - 0.2))]), sobe=0.3 * resp)
        pose["pelvis"] = {"rotacao": [cfg["pelve"], 0.0, 0.0]}
        pose["waist"] = {"rotacao": [cfg["cintura"] + 0.8 * resp_atr, cfg["torce_cintura"], 0.0]}
        pose["torso"] = {"rotacao": [cfg["peito"] + 1.5 * math.sin(4 * math.pi * (fase - 0.08)), cfg["torce_peito"], 0.0]}
        for lado, s in LADOS:
            base = r.piv(f"foot_{lado}")
            alvo = np.array([base[0] * cfg["abre"], loc.chao + loc.alt_tornozelo, base[2] + cfg[f"passo_{lado}"]])
            self.pe(pose, lado, s, alvo, cfg.get(f"ponta_{lado}", 0.0))
        cauda = np.asarray(cfg["cauda"], float) + np.array([0, 0, 0, 3.0, 6.0]) * math.sin(2 * math.pi * (fase - 0.3))
        self.cauda_tripe(pose, cauda, yaw=2.0 * math.sin(2 * math.pi * (fase - 0.45)))
        # garras: a da frente acompanha o peito e desenha um círculo pequeno; a de trás fica armada
        mov = np.array([0.3 * math.cos(2 * math.pi * fase), 0.4 * math.sin(4 * math.pi * (fase - 0.1)), 0.3 * math.sin(2 * math.pi * fase)])
        self.braco(pose, "left", -1.0, np.asarray(cfg["punho_frente"]) + mov, cfg["garra_frente"], cfg["giro_frente"], cfg["polo_frente"])
        self.braco(pose, "right", 1.0, np.asarray(cfg["punho_tras"]) + 0.5 * mov, cfg["garra_tras"], cfg["giro_tras"], cfg["polo_tras"])
        # a garra da frente se fecha devagar e estala aberta (ameaça), uma vez por loop
        u = (t - 0.55 * T) / (0.16 * T)
        crispa = suave(u / 0.7) if u < 0.7 else (1 - suave((u - 0.7) / 0.12)) * 1.0 - 0.25 * math.sin(math.pi * min(1.0, max(0.0, (u - 0.82) / 0.3)))
        crispa = crispa if 0 <= u <= 1.12 else 0.0
        loc.garras(pose, 0.0, flex=cfg["curva_garras"] + 0.6 * crispa, lados=("left",))
        loc.garras(pose, 0.0, flex=cfg["curva_garras"], lados=("right",))
        loc.cabeca_estavel(pose, pitch=cfg["olhar"] + 0.8 * resp, yaw=0.0, roll=cfg["inclina_cabeca"], rigidez=0.95)
        fita = [[cfg["fita"][k] + 3.0 * math.sin(2 * math.pi * (fase - 0.1 * (k + 1))), 2.5 * math.sin(2 * math.pi * (fase - 0.12 * k)), 0.0]
                for k in range(5)]
        loc.corrente(pose, [f"scarf_{k}" for k in range(1, 6)], fita)
        return pose

    def guarda(self, T=T_GUARDA, cfg=None):
        n = int(round(T * FPS))
        quadros = [(i * T / n, self.pose_guarda(cfg, i * T / n, T)) for i in range(n)]
        quadros.append((T, quadros[0][1]))
        return T, quadros, {}

    # ---------- entrar e sair da guarda ----------

    def _tornozelos(self, pose):
        mats = self.r.mats(pose)
        out = {}
        for lado, _s in LADOS:
            W = mats[f"foot_{lado}"]
            out[lado] = W[:3, :3] @ self.r.piv(f"foot_{lado}") + W[:3, 3]
        return out

    def _troca(self, ini, fim, T, acento, pulo=(0.18, 0.62), altura=2.2):
        """Mistura ini → fim; os pés saem do chão no pulo e pousam na base nova (sem patinar)."""
        from clips import misturar

        Ai, Af = self._tornozelos(ini), self._tornozelos(fim)
        n = int(round(T * FPS))
        quadros = []
        for i in range(n + 1):
            t = i * T / n
            w = suave(t / T)
            pose = misturar(ini, fim, w)
            acento(t, w, pose)
            a, b = pulo
            u = suave((t - a) / (b - a))
            no_ar = math.sin(math.pi * min(1.0, max(0.0, (t - a) / (b - a))))
            mats = self.r.mats(pose)
            for lado, s in LADOS:
                Rpe = mats[f"foot_{lado}"][:3, :3]  # orientação do pé misturada (pé chato ↔ na ponta)
                alvo = Ai[lado] + (Af[lado] - Ai[lado]) * u + np.array([0.0, altura * no_ar, 0.0])
                self.r.ik(pose, "pelvis", f"leg_{lado}", f"shin_{lado}", f"foot_{lado}", alvo, np.array([0.35 * s, 0.0, -1.0]))
                self.r.mundo_para_local(pose, f"foot_{lado}", rx(-8.0 * no_ar) @ Rpe)
            self.loc.cauda_acima_do_chao(pose)
            self.maos_acima_do_chao(pose)
            quadros.append((t, pose))
        return quadros

    def entrar(self, idle0, guarda0, T=0.6):
        """Idle → guarda: encolhe e fecha as garras (antecipação), pula de leve, cai na base com a cauda
        batendo no chão e as garras estalando abertas."""
        loc = self.loc

        def acento(t, w, pose):
            # antecipação: o corpo encolhe e recua; depois o pulo sobe o corpo e a queda passa do ponto
            enc = math.sin(math.pi * min(1.0, t / 0.18))
            pulo = math.sin(math.pi * min(1.0, max(0.0, (t - 0.16) / 0.3)))
            assenta = -math.sin(math.pi * min(1.0, max(0.0, (t - 0.42) / 0.18)))
            dy = -0.9 * enc * (t < 0.18) + 2.0 * pulo + 0.8 * assenta
            pose["body"]["posicao"] = pose["body"]["posicao"] + np.array([0.0, dy, 0.0])
            pose["body"]["matriz"] = pose["body"]["matriz"] @ rx(4.0 * enc * (t < 0.18) - 3.0 * assenta)
            fecha = suave(t / 0.16) * (1 - suave((t - 0.38) / 0.08))  # fecha as garras e estala na queda
            estalo = 0.3 * math.sin(math.pi * min(1.0, max(0.0, (t - 0.42) / 0.14)))
            loc.garras(pose, 0.0, flex=GUARDA["curva_garras"] * w + 0.9 * fecha - estalo)

        return self._troca(idle0, guarda0, T, acento)

    def sair(self, guarda0, idle0, T=0.7):
        """Guarda → idle: relaxa, pula de volta para a base de pé e solta as garras."""
        loc = self.loc

        def acento(t, w, pose):
            pulo = math.sin(math.pi * min(1.0, max(0.0, (t - 0.12) / 0.32)))
            assenta = -math.sin(math.pi * min(1.0, max(0.0, (t - 0.44) / 0.22)))
            pose["body"]["posicao"] = pose["body"]["posicao"] + np.array([0.0, 1.4 * pulo + 0.5 * assenta, 0.0])
            loc.garras(pose, 0.0, flex=GUARDA["curva_garras"] * (1 - w) + 0.25 * math.sin(math.pi * w))

        return self._troca(guarda0, idle0, T, acento, pulo=(0.12, 0.5), altura=1.6)
