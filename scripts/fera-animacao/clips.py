"""Animações de locomoção da preguiça rogue (idle, walk, run, run_start, run_stop).

Ideia: preguiça-gigante pesada, com camada de gordura, mas muito veloz. Parada fica de pé, curvada,
lenta. Andando e correndo vira quadrúpede apoiada nos nós das mãos, com as garras dobradas para
dentro (como tamanduás e preguiças-gigantes). O peso aparece sem escala (o Roblox não anima escala de
osso): tronco e pescoço atrasam e passam do ponto (molas), o corpo quica e assenta, cauda e cachecol
seguem em onda. A cabeça fica estável, focada (leitura de predador).
"""

from __future__ import annotations

import math

import numpy as np

from pose import Mola, Rig, eixo_angulo, fracao, matriz, onda, rot_min, rx, ry, rz, suave

FPS = 30
LADOS = (("left", -1.0), ("right", 1.0))


class Locomocao:
    def __init__(self, rig: Rig):
        self.r = rig
        p = rig.piv
        self.chao = rig.chao
        # altura do tornozelo e do punho acima do ponto de apoio (pé chato / nó da mão)
        self.alt_tornozelo = p("foot_left")[1] - self.chao
        self.alt_punho = 5.1
        self.dobra = {}  # rotação local de cada garra dobrada (para dentro, contra a palma)
        for lado, s in LADOS:
            for n in (1, 2, 3):
                nome = f"claw_{lado}_{n}"
                if nome not in rig.ossos:
                    continue
                base = p(nome)
                ponta = self._ponta_garra(nome)
                d0 = ponta - base
                medial = np.array([-s, 0.0, 0.0])  # para o meio do corpo
                alvo = 0.28 * medial + 0.8 * np.array([0, 1.0, 0]) + 0.55 * np.array([0, 0, 1.0])  # rente ao antebraço
                alvo += 0.12 * (n - 2) * np.array([s, 0, 0])  # leque leve, sem empilhar
                self.dobra[nome] = rot_min(d0, alvo)

    def _ponta_garra(self, nome):
        c = next(c for c in self.r.m.cubos if c.osso == nome)
        tam = c.ate - c.de
        k = int(np.argmax(tam))
        centro = (c.de + c.ate) / 2
        M = matriz(c.rotacao)
        pontas = []
        for s in (-1, 1):
            q = centro.copy()
            q[k] += s * tam[k] / 2
            pontas.append(c.origem + M @ (q - c.origem))
        base = self.r.piv(nome)
        return max(pontas, key=lambda q: np.linalg.norm(q - base))

    # ---------- pedaços de pose ----------

    def garras(self, pose, dobra=1.0, flex=0.0):
        """dobra: 0 = garras soltas (repouso), 1 = dobradas para dentro. flex: curva leve no idle."""
        for nome, R in self.dobra.items():
            Rf = fracao(R, min(1.0, max(0.0, dobra)))
            if flex:
                lado = 1.0 if "right" in nome else -1.0
                Rf = Rf @ rx(-18 * flex) @ rz(4 * flex * lado)
            pose[nome] = {"matriz": Rf}

    def perna(self, pose, lado, s, alvo_tornozelo, pe_pitch=0.0):
        polo = np.array([0.35 * s, 0.0, -1.0])  # joelho para a frente (mamífero) e um pouco para fora
        self.r.ik(pose, "pelvis", f"leg_{lado}", f"shin_{lado}", f"foot_{lado}", alvo_tornozelo, polo)
        self.r.mundo_para_local(pose, f"foot_{lado}", rx(pe_pitch))

    def plantar_pernas(self, pose):
        """Nas transições (pose misturada), nenhum pé afunda no chão: refaz a IK onde precisar."""
        for lado, s in LADOS:
            W = self.r.mats(pose)[f"foot_{lado}"]
            A = W[:3, :3] @ self.r.piv(f"foot_{lado}") + W[:3, 3]
            minimo = self.chao + self.alt_tornozelo
            if A[1] < minimo + 2.0:  # perto do chão: pé chato e tornozelo nunca abaixo do apoio
                self.perna(pose, lado, s, np.array([A[0], max(A[1], minimo), A[2]]), 0.0)

    def braco(self, pose, lado, s, alvo_punho, mao_pitch=0.0):
        polo = np.array([0.6 * s, 0.25, 1.0])  # cotovelo para trás e para fora
        self.r.ik(pose, "torso", f"arm_{lado}", f"forearm_{lado}", f"hand_{lado}", alvo_punho, polo)
        self.r.mundo_para_local(pose, f"hand_{lado}", rx(mao_pitch))

    def cabeca_estavel(self, pose, pitch=0.0, yaw=0.0, roll=0.0, rigidez=0.85):
        """Pescoço e cabeça compensam o tronco: a cabeça fica quase parada no mundo."""
        W = self.r.mats(pose)["torso"][:3, :3]
        alvo = ry(yaw) @ rx(pitch) @ rz(roll)
        comp = fracao(W.T @ alvo, rigidez)
        pose["neck_1"] = {"matriz": fracao(comp, 0.45)}
        W2 = self.r.mats(pose)["neck_1"][:3, :3]
        pose["neck_2"] = {"matriz": fracao(W2.T @ alvo, rigidez * 0.5)}
        W3 = self.r.mats(pose)["neck_2"][:3, :3]
        pose["head"] = {"matriz": fracao(W3.T @ alvo, rigidez)}

    def cauda_acima_do_chao(self, pose, folga=0.4):
        """Se a cauda (com o pelo) encostar no chão, ergue a base dela até sair."""
        cubos = [c for c in self.r.m.cubos if c.osso and c.osso.startswith("tail_")]
        for _ in range(4):
            mats = self.r.mats(pose)
            menor, ponto = np.inf, None
            for c in cubos:
                a, b = c.de, c.ate
                cantos = np.array([[x, y, z] for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])])
                M = mats[c.osso] @ self._mat_cubo(c)
                w = cantos @ M[:3, :3].T + M[:3, 3]
                i = int(np.argmin(w[:, 1]))
                if w[i, 1] < menor:
                    menor, ponto = w[i, 1], w[i]
            falta = self.chao + folga - menor
            if falta <= 0:
                return
            base = mats["tail_1"][:3, :3] @ self.r.piv("tail_1") + mats["tail_1"][:3, 3]
            dist = max(np.linalg.norm((ponto - base)[[1, 2]]), 3.0)
            ang = math.degrees(math.atan2(falta, dist)) + 1.0
            e = pose.setdefault("tail_1", {})
            if "matriz" in e:
                e["matriz"] = e["matriz"] @ rx(-ang)
            else:
                e["rotacao"] = np.asarray(e.get("rotacao", [0, 0, 0]), float) + np.array([-ang, 0.0, 0.0])

    def piscar(self):
        """Piscada sem escala: as tiras de pálpebra saem de dentro do focinho pela posição dos ossos.

        Meio fechado (só a tira de cima), fechado (as duas, 2 quadros), meio, aberto: 0,17 s. Só mexe em
        eyelid_*, para tocar como camada por cima de idle, walk e run sem brigar com eles.
        """
        from palpebras import DESLOCA as D

        passos = [(0, 0), (D, 0), (D, D), (D, D), (D, 0), (0, 0)]  # (tira de cima, tira de baixo)
        quadros = []
        for i, (cima, baixo) in enumerate(passos):
            pose = {}
            for lado, s in (("right", 1.0), ("left", -1.0)):
                pose[f"eyelid_{lado}"] = {"posicao": np.array([s * cima, 0.0, 0.0])}
                pose[f"eyelid_{lado}_lower"] = {"posicao": np.array([s * baixo, 0.0, 0.0])}
            quadros.append((i / FPS, pose))
        return (len(passos) - 1) / FPS, quadros, {}

    @staticmethod
    def _mat_cubo(c):
        M = np.eye(4)
        if np.any(c.rotacao):
            R = matriz(c.rotacao)
            M[:3, :3] = R
            M[:3, 3] = c.origem - R @ c.origem
        return M

    def corrente(self, pose, ossos, angs):
        for nome, a in zip(ossos, angs):
            if nome in self.r.ossos:
                pose[nome] = {"rotacao": np.asarray(a, float)}

    # ---------- passada ----------

    @staticmethod
    def passo(u, duty, curso, altura):
        """(deslocamento em z, altura) de um apoio na fase u ∈ [0,1): apoio de frente para trás, voo com arco."""
        if u < duty:
            s = u / duty
            return -curso / 2 + curso * s, 0.0
        s = (u - duty) / (1 - duty)
        return curso / 2 - curso * suave(s), altura * math.sin(math.pi * s)

    def pose_marcha(self, t, T, cfg, molas, dt):
        """Pose de quatro apoios no tempo t (walk ou run conforme cfg)."""
        r = self.r
        pose = {}
        fase = t / T
        # corpo: agachado e inclinado para a frente + quique e balanço
        bob = cfg["bob"](fase)
        pitch = cfg["pitch0"] + cfg["pitch"](fase)
        roll = cfg["roll"](fase)
        yaw = cfg["yaw"](fase)
        pose["body"] = {"rotacao": [pitch, yaw, roll], "posicao": [0.0, cfg["altura"] + bob, cfg["avanco"]]}
        # coluna: pelve × peito (flexão do galope) + gordura atrasada (molas)
        flex = cfg["flex"](fase)
        alvo_gordura = np.array([pitch + flex, yaw, roll, bob])
        g = molas["tronco"].passo(alvo_gordura, dt)
        atraso = g - alvo_gordura  # quanto o tronco ficou para trás
        pose["pelvis"] = {"rotacao": [-0.5 * flex, 0.0, 0.0]}
        pose["waist"] = {"rotacao": [0.5 * flex + 0.6 * atraso[0], 0.4 * atraso[1], 0.6 * atraso[2]],
                         "posicao": [0.0, 0.45 * atraso[3], 0.0]}
        pose["torso"] = {"rotacao": [cfg["torso0"] + 0.5 * flex + 0.9 * atraso[0], 0.6 * atraso[1], 0.9 * atraso[2]],
                         "posicao": [0.0, 0.7 * atraso[3], 0.0]}
        # patas de trás
        for lado, s in LADOS:
            u = (fase - cfg["fases"][f"pe_{lado}"]) % 1.0
            dz, h = self.passo(u, cfg["duty"], cfg["curso"], cfg["alt_pe"])
            base = r.piv(f"foot_{lado}")
            # patas de trás relativas ao tornozelo de repouso (acompanham as pernas que o usuário recuou)
            alvo = np.array([base[0] * cfg["abre_pe"], self.chao + self.alt_tornozelo + h, base[2] + cfg["dz_pe"] + dz])
            em_voo = u >= cfg["duty"]
            pe_pitch = (-25 * math.sin(math.pi * (u - cfg["duty"]) / (1 - cfg["duty"])) if em_voo else 0.0)
            self.perna(pose, lado, s, alvo, pe_pitch)
        # patas da frente (nós das mãos, garras dobradas)
        for lado, s in LADOS:
            u = (fase - cfg["fases"][f"mao_{lado}"]) % 1.0
            dz, h = self.passo(u, cfg["duty"], cfg["curso"], cfg["alt_mao"])
            alvo = np.array([s * cfg["x_mao"], self.chao + self.alt_punho + h, cfg["z_mao"] + dz])
            em_voo = u >= cfg["duty"]
            mao_pitch = (35 * math.sin(math.pi * (u - cfg["duty"]) / (1 - cfg["duty"])) if em_voo else 0.0)
            self.braco(pose, lado, s, alvo, mao_pitch)
        self.garras(pose, 1.0)
        # cabeça firme, com um leve atraso de gordura no pescoço
        pesc = molas["pescoco"].passo(np.array([bob, pitch]), dt)
        self.cabeca_estavel(pose, pitch=cfg["olhar"], yaw=0.0, roll=0.0, rigidez=0.9)
        R1 = pose["neck_1"]["matriz"]
        pose["neck_1"] = {"matriz": R1 @ rx(-1.6 * (pesc[1] - pitch)), "posicao": [0.0, 0.5 * (pesc[0] - bob), 0.0]}
        # cauda: contrapeso em onda (atrasa da raiz para a ponta)
        cauda = []
        for k in range(5):
            atrasok = fase - 0.07 * (k + 1)
            cauda.append([cfg["cauda_pitch"] * onda(atrasok * cfg["cauda_freq"], 1.0, 0.25) - (pitch - cfg["pitch0"]) * 0.4 * (k == 0),
                          cfg["cauda_yaw"] * onda(atrasok, 1.0) * (1 + 0.25 * k),
                          0.0])
        cauda[0][0] += cfg["cauda_ergue"]  # rotação negativa em X ergue o que fica atrás do pivô
        self.corrente(pose, [f"tail_{k}" for k in range(1, 6)], cauda)
        self.cauda_acima_do_chao(pose)
        # cachecol: onda correndo da gola para a ponta
        fita = []
        for k in range(5):
            a = fase * cfg["fita_freq"] - 0.11 * (k + 1)
            fita.append([cfg["fita_amp"] * onda(a, 1.0) * (0.6 + 0.2 * k), cfg["fita_amp"] * 0.6 * onda(a, 1.0, 0.25), 0.0])
        self.corrente(pose, [f"scarf_{k}" for k in range(1, 6)], fita)
        return pose

    def ciclo(self, T, cfg, aquecer=3):
        """Quadros de um ciclo em regime (molas aquecidas por alguns ciclos antes), fechando o loop."""
        n = int(round(T * FPS))
        dt = T / n
        molas = {"tronco": Mola(cfg["mola_freq"], cfg["mola_amort"], 4), "pescoco": Mola(cfg["mola_freq"] * 1.3, 0.4, 2)}
        quadros = []
        for c in range(aquecer + 1):
            for i in range(n):
                t = i * dt
                pose = self.pose_marcha(t, T, cfg, molas, dt)
                if c == aquecer:
                    quadros.append((t, pose))
        quadros.append((T, quadros[0][1]))  # loop sem emenda
        return quadros

    # ---------- clipes ----------

    def walk(self):
        T = 1.6
        cfg = dict(
            duty=0.7, curso=8.5, alt_pe=2.4, alt_mao=3.2, abre_pe=1.0, dz_pe=-2.9, x_mao=11.0, z_mao=-17.5,
            altura=-2.6, avanco=-0.5, pitch0=-7.0, torso0=-6.0, olhar=4.0,
            fases={"pe_left": 0.0, "mao_left": 0.25, "pe_right": 0.5, "mao_right": 0.75},
            bob=lambda f: 0.45 * math.cos(4 * math.pi * f),
            pitch=lambda f: 1.2 * math.cos(4 * math.pi * f + 0.6),
            roll=lambda f: 3.2 * math.sin(2 * math.pi * f),
            yaw=lambda f: 2.2 * math.sin(2 * math.pi * f + 0.9),
            flex=lambda f: 0.0,
            mola_freq=2.2, mola_amort=0.28,
            cauda_pitch=3.0, cauda_freq=2.0, cauda_yaw=7.0, cauda_ergue=-6.0,
            fita_freq=2.0, fita_amp=7.0,
        )
        return T, self.ciclo(T, cfg), {"curso": cfg["curso"] / cfg["duty"]}

    def run(self):
        """Galope pesado com UM ritmo: tudo que balança (corpo, coluna, gordura, cabeça, cauda,
        cachecol) está travado na fase da passada — nada oscila na própria frequência."""
        T = 0.66
        cfg = dict(
            duty=0.30, curso=9.0, alt_pe=3.6, alt_mao=4.0, abre_pe=1.05, dz_pe=-1.9, x_mao=10.5, z_mao=-19.0,
            altura=-1.6, avanco=-1.0, pitch0=-9.0, torso0=-4.0, olhar=6.0,
            # galope rotativo: trás esq., trás dir., frente dir., frente esq.; depois o voo recolhido
            fases={"pe_left": 0.0, "pe_right": 0.10, "mao_right": 0.42, "mao_left": 0.52},
            mao_pitch=20.0, pe_pitch=-22.0,
        )
        n = int(round(T * FPS))
        quadros = [(i * T / n, self.pose_galope(i / n, cfg)) for i in range(n)]
        # cauda: uma elevação fixa (calculada no ciclo todo) em vez de correções quadro a quadro
        falta = max(self.falta_cauda(p) for _t, p in quadros)
        if falta > 0:
            quadros = [(i * T / n, self.pose_galope(i / n, cfg, ergue_extra=falta)) for i in range(n)]
        quadros.append((T, quadros[0][1]))
        return T, quadros, {"curso": cfg["curso"] / cfg["duty"]}

    def pose_galope(self, f, cfg, ergue_extra=0.0):
        """Pose do galope na fase f ∈ [0,1). Só o `body` translada (sobe e desce); o resto gira."""
        r = self.r
        tau = 2 * math.pi
        pose = {}
        # corpo: um quique por passada (mais alto no voo recolhido, mais baixo quando as patas de trás
        # chegam e amortecem) + cadeira de balanço (nariz sobe no impulso de trás, desce na chegada da frente)
        y = 1.05 * math.cos(tau * (f - 0.9)) + 0.22 * math.cos(2 * tau * (f - 0.45))
        pitch = 5.0 * math.sin(tau * (f - 0.05))
        roll = 1.0 * math.sin(tau * (f - 0.2))
        pose["body"] = {"rotacao": [cfg["pitch0"] + pitch, 0.0, roll], "posicao": [0.0, cfg["altura"] + y, cfg["avanco"]]}
        # coluna: estica quando as patas da frente alcançam, encolhe quando as de trás chegam por baixo
        ext = 7.0 * math.cos(tau * (f - 0.5))
        # gordura: o peito segue o balanço do corpo com atraso (mesma frequência, fase atrasada)
        atraso = 0.45 * (5.0 * math.sin(tau * (f - 0.05 - 0.09)) - pitch)
        pose["pelvis"] = {"rotacao": [-0.6 * ext, 0.0, 0.0]}
        pose["waist"] = {"rotacao": [0.25 * ext + 0.4 * atraso, 0.0, -0.5 * roll]}
        pose["torso"] = {"rotacao": [cfg["torso0"] + 0.35 * ext + 0.6 * atraso, 0.0, -0.4 * roll]}
        for lado, s in LADOS:
            u = (f - cfg["fases"][f"pe_{lado}"]) % 1.0
            dz, h = self.passo(u, cfg["duty"], cfg["curso"], cfg["alt_pe"])
            base = r.piv(f"foot_{lado}")
            alvo = np.array([base[0] * cfg["abre_pe"], self.chao + self.alt_tornozelo + h, base[2] + cfg["dz_pe"] + dz])
            voo = (u - cfg["duty"]) / (1 - cfg["duty"]) if u >= cfg["duty"] else -1
            self.perna(pose, lado, s, alvo, cfg["pe_pitch"] * math.sin(math.pi * voo) if voo >= 0 else 0.0)
        for lado, s in LADOS:
            u = (f - cfg["fases"][f"mao_{lado}"]) % 1.0
            dz, h = self.passo(u, cfg["duty"], cfg["curso"], cfg["alt_mao"])
            alvo = np.array([s * cfg["x_mao"], self.chao + self.alt_punho + h, cfg["z_mao"] + dz])
            voo = (u - cfg["duty"]) / (1 - cfg["duty"]) if u >= cfg["duty"] else -1
            self.braco(pose, lado, s, alvo, cfg["mao_pitch"] * math.sin(math.pi * voo) if voo >= 0 else 0.0)
        self.garras(pose, 1.0)
        # cabeça firme (predador focado); o pescoço absorve um pouco do balanço, atrasado
        self.cabeca_estavel(pose, pitch=cfg["olhar"], yaw=0.0, roll=0.0, rigidez=0.85)
        R1 = pose["neck_1"]["matriz"]
        pose["neck_1"] = {"matriz": R1 @ rx(-0.5 * atraso)}
        # cauda: contrapeso em onda, uma vez por passada, da base para a ponta
        cauda = []
        for k in range(5):
            onda_k = math.sin(tau * (f - 0.3 - 0.07 * k))
            cauda.append([5.0 * (0.8 + 0.15 * k) * onda_k - 0.5 * pitch * (k == 0), 1.8 * math.sin(tau * (f - 0.2 - 0.07 * k)), 0.0])
        cauda[0][0] += -9.0 - ergue_extra
        self.corrente(pose, [f"tail_{k}" for k in range(1, 6)], cauda)
        # cachecol: a fita esvoaça para trás no mesmo ritmo (uma onda por passada)
        fita = []
        for k in range(5):
            a = tau * (f - 0.1 - 0.08 * (k + 1))
            fita.append([8.0 * (0.6 + 0.15 * k) * math.sin(a), 4.0 * math.sin(a + 1.2), 0.0])
        self.corrente(pose, [f"scarf_{k}" for k in range(1, 6)], fita)
        return pose

    def falta_cauda(self, pose, folga=0.6):
        """Quanto (em graus na base) a cauda precisa subir para não tocar o chão nessa pose."""
        teste = {k: dict(v) for k, v in pose.items()}
        antes = np.asarray(teste["tail_1"]["rotacao"], float).copy()
        self.cauda_acima_do_chao(teste, folga)
        depois = np.asarray(teste["tail_1"]["rotacao"], float)
        return float(antes[0] - depois[0])

    def pose_idle(self, t, T, molas, dt):
        """De pé, curvada, lenta: respira, olha devagar, mexe as garras."""
        pose = {}
        resp = math.sin(2 * math.pi * t / T)
        pose["body"] = {"posicao": [0.0, 0.28 * resp, 0.0], "rotacao": [0.8 * resp, 0.0, 0.0]}
        g = molas["tronco"].passo(np.array([0.28 * resp]), dt)
        pose["waist"] = {"rotacao": [1.0 * resp, 0.0, 0.0]}
        pose["torso"] = {"rotacao": [1.6 * math.sin(2 * math.pi * (t / T - 0.08)), 0.0, 0.0],
                         "posicao": [0.0, 0.6 * (g[0] - 0.28 * resp), 0.0]}
        # pés plantados (o corpo respira, as pernas compensam)
        for lado, s in LADOS:
            self.perna(pose, lado, s, self.r.piv(f"foot_{lado}"), 0.0)
        # braços pendurados acompanhando a respiração com atraso
        for lado, s in LADOS:
            pose[f"arm_{lado}"] = {"rotacao": [1.5 * math.sin(2 * math.pi * (t / T - 0.15)), 0.0, 0.0]}
            pose[f"forearm_{lado}"] = {"rotacao": [2.0 * math.sin(2 * math.pi * (t / T - 0.25)), 0.0, 0.0]}
        # olhar lento: vira para um lado, volta, espia o outro
        olhar = 14 * suave(min(1, t / (0.35 * T))) * (1 - suave(max(0, (t - 0.45 * T) / (0.2 * T))))
        olhar -= 8 * suave(max(0, (t - 0.68 * T) / (0.12 * T))) * (1 - suave(max(0, (t - 0.86 * T) / (0.12 * T))))
        self.cabeca_estavel(pose, pitch=1.5 * resp, yaw=olhar, roll=0.0, rigidez=0.35)
        # garras: dobra leve e volta (preguiça se espreguiçando)
        flex = math.sin(math.pi * min(1.0, max(0.0, (t - 0.55 * T) / (0.3 * T)))) ** 2
        self.garras(pose, 0.0, flex=flex)
        cauda = [[1.5 * math.sin(2 * math.pi * (t / T - 0.1 * k)), 3.5 * math.sin(2 * math.pi * (t / T - 0.12 * (k + 1))), 0.0]
                 for k in range(5)]
        self.corrente(pose, [f"tail_{k}" for k in range(1, 6)], cauda)
        fita = [[3.0 * math.sin(2 * math.pi * (2 * t / T - 0.12 * (k + 1))), 2.0 * math.sin(2 * math.pi * (2 * t / T - 0.12 * k)), 0.0]
                for k in range(5)]
        self.corrente(pose, [f"scarf_{k}" for k in range(1, 6)], fita)
        return pose

    def idle(self):
        T = 4.0
        n = int(round(T * FPS))
        dt = T / n
        molas = {"tronco": Mola(1.6, 0.3, 1)}
        quadros = []
        for c in range(3):
            for i in range(n):
                pose = self.pose_idle(i * dt, T, molas, dt)
                if c == 2:
                    quadros.append((i * dt, pose))
        quadros.append((T, quadros[0][1]))
        return T, quadros, {}


def misturar(a, b, w):
    """Pose intermediária (rotações por fração do caminho, posições lineares)."""
    out = {}
    for osso in set(a) | set(b):
        ea, eb = a.get(osso, {}), b.get(osso, {})
        Ra = ea["matriz"] if "matriz" in ea else matriz(ea.get("rotacao", [0, 0, 0]))
        Rb = eb["matriz"] if "matriz" in eb else matriz(eb.get("rotacao", [0, 0, 0]))
        pa = np.asarray(ea.get("posicao", [0, 0, 0]), float)
        pb = np.asarray(eb.get("posicao", [0, 0, 0]), float)
        out[osso] = {"matriz": Ra @ fracao(Ra.T @ Rb, w), "posicao": pa * (1 - w) + pb * w}
    return out


def transicao(inicio, fim, T, extra=None):
    """Quadros de `inicio` para `fim` com curva suave; `extra(t, w, pose)` acrescenta acentos."""
    n = int(round(T * FPS))
    quadros = []
    for i in range(n + 1):
        t = i * T / n
        w = suave(t / T)
        pose = misturar(inicio, fim, w)
        if extra:
            extra(t, w, pose)
        quadros.append((t, pose))
    return quadros
