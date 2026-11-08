"""Combate da preguiça rogue no conceito "fera de quatro" (escolhido na folha de poses, 07/11/2026).

Retorno da r09: a guarda de lutador em pé e os golpes de espada "não combinam com a criatura" (o walk e
o run aprovados são de bicho: corpo horizontal, pesado, nos nós das mãos). Na folha de poses
(`conceitos_combate.py`) o usuário escolheu a fera de quatro, um carcaju/texugo-do-mel: o combate
continua nos quatro apoios e as garras trabalham como gancho (puxa, rasga, cava), não como lâmina.

Guarda: agachada nos quatro, garras abertas cravadas no chão, cauda baixa (erguida vira esquilo),
cabeça baixa. Golpes saem dela: garrada de uma pata, bote com as duas, e as habilidades (arremesso da
garra levantando só um pouco nas patas de trás, golpes de teleporte em bote, e o frenesi que rasga o
chefe cavando como num cupinzeiro).

Máquina (a mesma da r09): poses-chave (`clipe`) com curvas de tempo e IK de dobradiça; a mão pode estar
solta (punho relativo ao ombro) ou apoiada (ponto do chão, altura resolvida para as garras encostarem),
com `apoio` misturando as duas; cauda livre (sem tripé), longe do chão; cachecol em molas; anatomia dos
braços medida (`anatomia_braco`) e corrigida por chave (`ajustar_chave`) e por quadro (`_desenterrar`).
Coluna reta (dobrar na emenda pelve × peito abre fresta nas costas).
"""

from __future__ import annotations

import math

import numpy as np

from clips import FPS, LADOS, Locomocao
from pose import Mola, eixo_angulo, matriz, rot_min, rx, ry, suave

SUF = {"left": "esq", "right": "dir"}

GUARDA = dict(
    empina=-8.0,  # nariz para baixo, em volta do quadril
    torce=0.0, inclina=0.0,
    agacha=2.0, recua=0.5,  # quadril baixo e um pouco para trás
    avanco=0.0, lateral=0.0, sobe=0.0, salto=0.0,
    pelve=0.0, cintura=0.0, peito=0.0,  # coluna reta (blocos rígidos: dobrar abre fresta nas costas)
    abre=1.15,
    passo_esq=0.0, passo_dir=0.0, ponta_esq=0.0, ponta_dir=0.0, ergue_esq=0.0, ergue_dir=0.0,
    polo_joelho=(0.25, 0.0, -1.0),
    # mãos apoiadas com as garras abertas cravadas no chão; o punho solto vale quando a mão sai do chão
    apoio_esq=1.0, apoio_dir=1.0,
    chao_esq=(-12.0, -22.0), chao_dir=(12.0, -22.0), ergue_mao_esq=0.0, ergue_mao_dir=0.0,
    punho_esq=(-1.5, -6.0, -10.0), punho_dir=(1.5, -6.0, -10.0),
    garra_esq=(-0.12, -0.15, -1.0), garra_dir=(0.12, -0.15, -1.0), giro_esq=0.0, giro_dir=0.0,
    polo_esq=None, polo_dir=None, escapula_esq=(0.0, 0.0, 0.0), escapula_dir=(0.0, 0.0, 0.0),
    curva_esq=0.05, curva_dir=0.05, dobra_esq=0.0, dobra_dir=0.0,
    recolhe=0.0,  # 1 = a garra do meio da mão direita foi arremessada (escondida no antebraço)
    olhar=-6.0, yaw_cabeca=0.0, inclina_cabeca=0.0,
    cauda_livre=(-12.0, -6.0, 0.0, 4.0, 6.0), cauda_yaw=0.0,  # cauda baixa, ponta subindo pouco
    fita=(10.0, 8.0, 6.0, 5.0, 4.0),
)
T_GUARDA = 3.2  # um loop com uma piscada (ritmo natural)
SALTA = {"recolhe"}  # canais que trocam de valor de uma vez (no instante da chave), sem meio-termo

CURVAS = {
    "suave": suave,
    "linear": lambda x: x,
    "solta": lambda x: 1.0 - (1.0 - x) ** 3,  # golpe: sai rápido e freia no fim
    "carrega": lambda x: x ** 2.2,  # antecipação que acelera para o golpe
}


def interpolar(a, b, w):
    out = {}
    for k, va in a.items():
        vb = b.get(k, va)
        if k in SALTA:
            out[k] = vb if w >= 1.0 - 1e-9 else va
        elif va is None or vb is None:
            out[k] = va if vb is None else vb if va is None else va
        elif isinstance(va, (tuple, list, np.ndarray)):
            out[k] = tuple(np.asarray(va, float) * (1 - w) + np.asarray(vb, float) * w)
        else:
            out[k] = va * (1 - w) + vb * w
    return out


def _mao(lado):
    return (f"hand_{lado}",) + tuple(f"claw_{lado}_{n}" for n in (1, 2, 3))


class Combate:
    def __init__(self, loc: Locomocao):
        self.loc, self.r = loc, loc.r
        r = self.r
        self.P = r.piv("body")
        self.quadril = (r.piv("leg_left") + r.piv("leg_right")) / 2
        self.d_garras = {}
        self.cotovelo = {}  # para onde o cotovelo aponta no repouso (fora da linha ombro-punho)
        for lado, _s in LADOS:
            ds = [loc._ponta_garra(f"claw_{lado}_{n}") - r.piv(f"claw_{lado}_{n}") for n in (1, 2, 3)]
            self.d_garras[lado] = np.mean(ds, axis=0)
            o, c, p = r.piv(f"arm_{lado}"), r.piv(f"forearm_{lado}"), r.piv(f"hand_{lado}")
            u = (p - o) / np.linalg.norm(p - o)
            e = (c - o) - ((c - o) @ u) * u
            self.cotovelo[lado] = e / np.linalg.norm(e)
        d = loc._ponta_garra("claw_right_2") - r.piv("claw_right_2")
        self.d_arremesso = d / np.linalg.norm(d)  # garra arremessada (a do meio da mão direita)
        self.gomos = [f"tail_{k}" for k in range(1, 6)]

    # ---------- pedaços ----------

    def ombro(self, pose, lado):
        W = self.r.mats(pose)["torso"]
        return W[:3, :3] @ self.r.piv(f"arm_{lado}") + W[:3, 3]

    def braco(self, pose, lado, s, punho_rel, garra_dir, giro, polo=None, escapula=None):
        """Punho num ponto relativo ao ombro (no mundo), garras apontando para garra_dir. Sem polo, o
        cotovelo aponta para onde aponta no repouso, girado com o tronco. `escapula` desliza o ombro."""
        r = self.r
        W = r.mats(pose)["torso"]
        ombro = W[:3, :3] @ r.piv(f"arm_{lado}") + W[:3, 3]
        alvo = ombro + np.asarray(punho_rel, float)
        if escapula is not None and np.any(np.abs(np.asarray(escapula, float)) > 1e-6):
            pose.setdefault(f"arm_{lado}", {})["posicao"] = np.asarray(escapula, float) * np.array([s, 1.0, 1.0])
        polo = W[:3, :3] @ self.cotovelo[lado] if polo is None else np.asarray(polo, float)
        r.ik(pose, "torso", f"arm_{lado}", f"forearm_{lado}", f"hand_{lado}", alvo, polo, charneira=True)
        d = np.asarray(garra_dir, float)
        d = d / np.linalg.norm(d)
        r.mundo_para_local(pose, f"hand_{lado}", eixo_angulo(d, giro) @ rot_min(self.d_garras[lado], d))

    def mao(self, pose, lado, s, cfg, mov, R):
        """Braço de um lado: mistura o punho solto (relativo ao ombro) com a mão apoiada (ponto do chão, na
        altura em que garras ou nós encostam) pelo `apoio`. Mão solta não entra no corpo (_desenterrar)."""
        X = SUF[lado]
        apoio = float(np.clip(cfg[f"apoio_{X}"], 0.0, 1.0))
        ombro = self.ombro(pose, lado)
        livre = ombro + np.asarray(cfg[f"punho_{X}"], float) + mov
        args = (cfg[f"garra_{X}"], cfg[f"giro_{X}"], cfg[f"polo_{X}"], cfg[f"escapula_{X}"])

        def aplicar(alvo):
            self.braco(pose, lado, s, np.asarray(alvo, float) - ombro, *args)
            self.loc.garras(pose, cfg[f"dobra_{X}"], flex=cfg[f"curva_{X}"], lados=(lado,))

        if apoio <= 1e-3:
            aplicar(livre)
            self._desenterrar(pose, lado, s, cfg, livre - ombro, R)
            return
        cx, cz = cfg[f"chao_{X}"]
        y = self.loc.chao + 3.0
        for _ in range(6):
            aplicar((cx, y, cz))
            falta = self.loc.chao + 0.05 - self._menor_y(pose, _mao(lado))
            if abs(falta) < 1e-3:
                break
            y += falta
        ergue = cfg[f"ergue_mao_{X}"]
        if apoio < 1.0 - 1e-3 or ergue > 1e-3:
            aplicar(livre * (1.0 - apoio) + np.array([cx, y + ergue, cz]) * apoio)
            if apoio < 0.5:
                self._desenterrar(pose, lado, s, cfg, livre * (1.0 - apoio) + np.array([cx, y + ergue, cz]) * apoio - ombro, R)

    def esconder_garra(self, pose):
        """A garra arremessada some: gira para trás, alinhada com o antebraço, e fica dentro dele."""
        r = self.r
        Wf = r.mats(pose)["forearm_right"]
        eixo = Wf[:3, :3] @ (r.piv("hand_right") - r.piv("forearm_right"))
        r.mundo_para_local(pose, "claw_right_2", rot_min(self.d_arremesso, -eixo))

    def pe(self, pose, lado, s, alvo, ponta=0.0, polo=(0.35, 0.0, -1.0), ergue=0.0):
        """Pé plantado (dobradiça); ponta > 0 ergue o calcanhar; ergue > 0 tira o pé do chão. Agachada
        fundo, a canela deitaria no chão: o calcanhar sobe sozinho o mínimo preciso (ponta dos pés, como
        bicho agachado), achado por bisseção para variar suave entre quadros."""
        loc = self.loc
        alvo0 = np.array(alvo, float)
        polo = np.array([polo[0] * s, polo[1], polo[2]])

        def plantar(pt):
            alvo = alvo0.copy()
            for _ in range(4):
                loc.perna(pose, lado, s, alvo, -pt, charneira=True, polo=polo)
                falta = loc.chao - self._menor_y(pose, (f"foot_{lado}",))
                if abs(falta) < 1e-3:
                    break
                alvo[1] += falta
            return alvo

        alvo = plantar(ponta)
        if self._menor_y(pose, (f"shin_{lado}",)) < loc.chao + 0.05:
            lo, hi = ponta, 70.0
            for _ in range(7):
                mid = (lo + hi) / 2
                plantar(mid)
                if self._menor_y(pose, (f"shin_{lado}",)) < loc.chao + 0.05:
                    lo = mid
                else:
                    hi = mid
            ponta = hi
            alvo = plantar(ponta)
        if ergue > 1e-3:
            loc.perna(pose, lado, s, alvo + np.array([0.0, ergue, 0.0]), -ponta - 14.0 * min(1.0, ergue / 2.5),
                      charneira=True, polo=polo)

    # ---------- anatomia do braço (blocos grandes e rígidos) ----------

    def _pontos(self, c, passo=0.75):
        eixos = [np.arange(c.de[k] + passo / 2, c.ate[k], passo) if c.ate[k] - c.de[k] > passo else np.array([(c.de[k] + c.ate[k]) / 2])
                 for k in range(3)]
        g = np.stack(np.meshgrid(*eixos, indexing="ij"), -1).reshape(-1, 3)
        M = self.loc._mat_cubo(c)
        return g @ M[:3, :3].T + M[:3, 3]

    def _dentro_de(self, pts, cubos, mats):
        dentro = np.zeros(len(pts), bool)
        for c in cubos:
            M = mats[c.osso] @ self.loc._mat_cubo(c)
            local = (pts - M[:3, 3]) @ M[:3, :3]
            dentro |= np.all((local >= c.de - 1e-6) & (local <= c.ate + 1e-6), axis=1)
        return dentro

    def _preparar_anatomia(self):
        if hasattr(self, "_anat"):
            return
        solidos = [c for c in self.r.m.cubos if np.all(c.ate - c.de > 0.5)]
        tronco = [c for c in solidos if c.osso in ("torso", "pelvis", "neck_1", "scarf")]  # a gola tapa o ombro
        coxas = [c for c in solidos if c.osso and c.osso.startswith("leg_")]
        repouso = self.r.mats({})
        self._anat = {"tronco": tronco, "coxas": coxas}
        for lado, _s in LADOS:
            for osso in (f"arm_{lado}", f"forearm_{lado}", f"hand_{lado}"):
                c = next(c for c in solidos if c.osso == osso)
                pts = self._pontos(c)
                self._anat[osso] = (pts, self._dentro_de(pts, tronco, repouso))

    def _fora(self, pts, cubos, mats):
        d = np.full(len(pts), np.inf)
        for c in cubos:
            M = mats[c.osso] @ self.loc._mat_cubo(c)
            local = (pts - M[:3, 3]) @ M[:3, :3]
            d = np.minimum(d, np.linalg.norm(local - np.clip(local, c.de, c.ate), axis=1))
        return d

    def anatomia_braco(self, pose, lado):
        """(saliência, enterrado): o quanto (em unidades) a quina do bloco do braço escondida no tronco no
        repouso sai pelo ombro, e a fração do braço visível que entra no tronco ou nas coxas."""
        self._preparar_anatomia()
        mats = self.r.mats(pose)
        saliencia, enterrado, total = 0.0, 0, 0
        for osso in (f"arm_{lado}", f"forearm_{lado}", f"hand_{lado}"):
            pts0, oculto = self._anat[osso]
            W = mats[osso]
            pts = pts0 @ W[:3, :3].T + W[:3, 3]
            dentro = self._dentro_de(pts, self._anat["tronco"] + self._anat["coxas"], mats)
            if osso.startswith("arm_") and oculto.any():
                saliencia = float(np.percentile(self._fora(pts[oculto], self._anat["tronco"], mats), 90))
            enterrado += int((dentro & ~oculto).sum())
            total += int((~oculto).sum())
        return saliencia, enterrado / max(total, 1)

    def _desenterrar(self, pose, lado, s, cfg, punho, R, limite=0.02):
        """Mão solta entrando no tronco ou nas coxas: empurra o punho para a frente e para fora até sair."""
        X = SUF[lado]
        sal, ent = self.anatomia_braco(pose, lado)
        if ent <= limite:
            return
        f = R @ np.array([0.0, 0.0, -1.0])
        f[1] = 0.0
        f /= np.linalg.norm(f)
        o = R @ np.array([s, 0.0, 0.0])
        o[1] = 0.0
        o /= np.linalg.norm(o)
        melhor = None
        for k in (1.5, 3.0, 4.5, 6.0):
            for j in (0.0, 1.5, 3.0):
                p = {n: dict(v) for n, v in pose.items()}
                p.pop(f"arm_{lado}", None)
                self.braco(p, lado, s, punho + k * f + j * o, cfg[f"garra_{X}"], cfg[f"giro_{X}"], cfg[f"polo_{X}"], cfg[f"escapula_{X}"])
                sal2, ent2 = self.anatomia_braco(p, lado)
                custo = 40 * max(0.0, ent2 - limite) + max(0.0, sal2 - max(sal, 1.7)) + 0.05 * (k + j)
                if melhor is None or custo < melhor[0]:
                    melhor = (custo, p)
                if ent2 <= limite and sal2 <= max(sal, 1.7):
                    break
            if melhor and melhor[0] < 0.05 * (k + 3.0) + 1e-9:
                break
        for n in (f"arm_{lado}", f"forearm_{lado}", f"hand_{lado}"):
            pose[n] = melhor[1][n]

    def maos_acima_do_chao(self, pose, folga=0.3, lados=("left", "right")):
        """Mão ou garra encostando no chão: gira o braço no ombro até sair."""
        r = self.r
        for lado in lados:
            for _ in range(4):
                menor, ponto = self._menor_ponto(pose, _mao(lado))
                falta = self.loc.chao + folga - menor
                if falta <= 1e-3:
                    break
                W = r.mats(pose)[f"arm_{lado}"]
                v = ponto - (W[:3, :3] @ r.piv(f"arm_{lado}") + W[:3, 3])
                eixo = np.cross(v, [0.0, 1.0, 0.0])
                ang = math.degrees(math.atan2(falta, max(np.linalg.norm(v), 1.0))) * 1.1
                r.mundo_para_local(pose, f"arm_{lado}", eixo_angulo(eixo, ang) @ W[:3, :3])

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

    # ---------- pose a partir dos parâmetros ----------

    def pose_de(self, cfg, t=0.0, T=T_GUARDA, respira=1.0, fita_extra=None):
        """Pose completa a partir dos parâmetros (GUARDA + mudanças)."""
        cfg = dict(GUARDA, **cfg)
        loc, r = self.loc, self.r
        pose = {}
        fase = t / T
        resp = respira * math.sin(4 * math.pi * fase)  # duas respirações por loop
        R = matriz([cfg["empina"] + 0.9 * resp, cfg["torce"], cfg["inclina"]])
        H = self.quadril + np.array([cfg["lateral"], -cfg["agacha"] + cfg["sobe"] + cfg["salto"] + 0.3 * resp, cfg["recua"] + cfg["avanco"]])
        pose["body"] = {"matriz": R, "posicao": H - self.P - R @ (self.quadril - self.P)}
        pose["pelvis"] = {"rotacao": [cfg["pelve"], 0.0, 0.0]}
        pose["waist"] = {"rotacao": [cfg["cintura"] + 0.3 * respira * math.sin(4 * math.pi * (fase - 0.04)), 0.0, 0.0]}
        pose["torso"] = {"rotacao": [cfg["peito"] + 0.5 * respira * math.sin(4 * math.pi * (fase - 0.08)), 0.0, 0.0]}
        for lado, s in LADOS:
            X = SUF[lado]
            base = r.piv(f"foot_{lado}")
            alvo = np.array([base[0] * cfg["abre"], loc.chao + loc.alt_tornozelo, base[2] + cfg[f"passo_{X}"]])
            self.pe(pose, lado, s, alvo, cfg[f"ponta_{X}"], cfg["polo_joelho"], cfg["salto"] + cfg[f"ergue_{X}"])
        # cauda livre (sem tripé): ângulos locais de cada gomo, curva para o lado em cauda_yaw, longe do chão
        cl = np.asarray(cfg["cauda_livre"], float) + respira * np.array([0, 0, 0, 3.0, 6.0]) * math.sin(2 * math.pi * (fase - 0.3))
        for k, g in enumerate(self.gomos):
            pose[g] = {"matriz": ry(cfg["cauda_yaw"] * (0.6 + 0.2 * k) / 1.4) @ rx(float(cl[k]))}
        loc.cauda_acima_do_chao(pose, 0.3)
        mov = respira * np.array([0.0, 0.3 * math.sin(4 * math.pi * (fase - 0.1)), 0.0])
        for lado, s in LADOS:
            self.mao(pose, lado, s, cfg, mov, R)
        if cfg["recolhe"] >= 0.5:
            self.esconder_garra(pose)
        soltas = tuple(l for l, _s in LADOS if cfg[f"apoio_{SUF[l]}"] < 0.5)
        if soltas:
            self.maos_acima_do_chao(pose, 0.3, soltas)
        loc.cabeca_estavel(pose, pitch=cfg["olhar"] + 0.8 * resp, yaw=cfg["yaw_cabeca"], roll=cfg["inclina_cabeca"], rigidez=0.95)
        extra = fita_extra or [(0.0, 0.0)] * 5
        fita = [[cfg["fita"][k] + 3.0 * respira * math.sin(2 * math.pi * (fase - 0.1 * (k + 1))) + extra[k][0],
                 2.5 * respira * math.sin(2 * math.pi * (fase - 0.12 * k)) + extra[k][1], 0.0] for k in range(5)]
        loc.corrente(pose, [f"scarf_{k}" for k in range(1, 6)], fita)
        return pose

    def pose_guarda(self, cfg=None, t=0.0, T=T_GUARDA):
        """Guarda de quatro no tempo t do loop: respira pesado, joga o peso de um lado para o outro, a
        cabeça vasculha, a mão direita cava o chão uma vez (garras se fecham arrastando e abrem) e a ponta
        da cauda não para."""
        f = t / T
        vida = dict(lateral=0.5 * math.sin(2 * math.pi * f), inclina=2.0 * math.sin(2 * math.pi * (f - 0.05)),
                    yaw_cabeca=6.0 * math.sin(2 * math.pi * (f - 0.1)))
        u = (f - 0.55) / 0.22
        if 0.0 <= u <= 1.0:
            cava = math.sin(math.pi * u)
            vida["curva_dir"] = GUARDA["curva_dir"] + 0.7 * cava
            vida["chao_dir"] = (GUARDA["chao_dir"][0], GUARDA["chao_dir"][1] + 1.6 * cava)
            vida["ergue_mao_dir"] = 0.6 * max(0.0, math.sin(math.pi * (u - 0.5) * 2)) if u > 0.5 else 0.0
        return self.pose_de(dict(cfg or {}, **vida), t, T)

    def guarda(self, T=T_GUARDA, cfg=None):
        n = int(round(T * FPS))
        quadros = [(i * T / n, self.pose_guarda(cfg, i * T / n, T)) for i in range(n)]
        quadros.append((T, quadros[0][1]))
        return T, quadros, {}

    # ---------- poses-chave ----------

    def clipe(self, chaves, respira=0.25, loop=False):
        """chaves = [(t, mudanças sobre GUARDA, curva até esta chave)]; a primeira em t=0, a última em T.
        Parâmetros interpolados com a curva de cada trecho; pose de cada quadro por IK. O cachecol atrasa
        (molas puxadas pela torção, pelo avanço e pelo salto do corpo)."""
        cfgs = [(t, dict(GUARDA, **ov), curva) for t, ov, curva in chaves]
        T = cfgs[-1][0]
        n = int(round(T * FPS))
        por_quadro = []
        for i in range(n + 1):
            t = i * T / n
            k = max(j for j in range(len(cfgs) - 1) if cfgs[j][0] <= t + 1e-9) if t < T else len(cfgs) - 2
            (ta, ca, _), (tb, cb, curva) = cfgs[k], cfgs[k + 1]
            w = CURVAS[curva](min(1.0, max(0.0, (t - ta) / (tb - ta))))
            por_quadro.append((t, interpolar(ca, cb, w)))
        molas = [Mola(3.2, 0.32, 2) for _ in range(5)]
        dt = T / n
        extras = []
        for _volta in range(2 if loop else 1):
            extras = []
            for i, (t, c) in enumerate(por_quadro):
                j = i - 1 if i > 0 else (len(por_quadro) - 2 if loop else 0)
                cp = por_quadro[j][1]
                v_torce = (c["torce"] - cp["torce"]) / dt
                v_avanco = (c["avanco"] - cp["avanco"]) / dt
                v_salto = (c["salto"] - cp["salto"]) / dt
                alvo = np.array([np.clip(0.9 * v_avanco + 0.6 * v_salto, -30, 30), np.clip(-0.06 * v_torce, -30, 30)])
                extras.append([tuple(m.passo(alvo * (0.6 + 0.2 * k), dt)) for k, m in enumerate(molas)])
        quadros = [(t, self.pose_de(c, t, T, respira, extras[i])) for i, (t, c) in enumerate(por_quadro)]
        if loop:
            quadros[-1] = (T, quadros[0][1])
        return T, quadros

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
                Rpe = mats[f"foot_{lado}"][:3, :3]
                alvo = Ai[lado] + (Af[lado] - Ai[lado]) * u + np.array([0.0, altura * no_ar, 0.0])
                self.r.ik(pose, "pelvis", f"leg_{lado}", f"shin_{lado}", f"foot_{lado}", alvo, np.array([GUARDA["polo_joelho"][0] * s, 0.0, -1.0]), charneira=True)
                self.r.mundo_para_local(pose, f"foot_{lado}", rx(-8.0 * no_ar) @ Rpe)
            self.loc.cauda_acima_do_chao(pose)
            self.maos_acima_do_chao(pose, folga=0.0)  # só não deixa entrar no chão (a mão apoiada fica)
            quadros.append((t, pose))
        return quadros

    def entrar(self, idle0, guarda0, T=0.6):
        """Idle → guarda: encolhe e fecha as garras (antecipação), cai nas mãos com as garras abrindo no
        impacto, e assenta pesada."""
        loc = self.loc

        def acento(t, w, pose):
            enc = math.sin(math.pi * min(1.0, t / 0.16))
            queda = -math.sin(math.pi * min(1.0, max(0.0, (t - 0.34) / 0.2)))
            pose["body"]["posicao"] = pose["body"]["posicao"] + np.array([0.0, 0.6 * enc * (t < 0.16) + 0.7 * queda, 0.0])
            pose["body"]["matriz"] = pose["body"]["matriz"] @ rx(3.0 * enc * (t < 0.16))
            fecha = suave(t / 0.14) * (1 - suave((t - 0.3) / 0.08))
            loc.garras(pose, 0.0, flex=GUARDA["curva_esq"] * w + 0.7 * fecha)

        return self._troca(idle0, guarda0, T, acento, pulo=(0.14, 0.4), altura=1.2)

    def sair(self, guarda0, idle0, T=0.7):
        """Guarda → idle: empurra o chão, levanta e solta as garras."""
        loc = self.loc

        def acento(t, w, pose):
            empurra = math.sin(math.pi * min(1.0, max(0.0, (t - 0.08) / 0.3)))
            assenta = -math.sin(math.pi * min(1.0, max(0.0, (t - 0.42) / 0.22)))
            pose["body"]["posicao"] = pose["body"]["posicao"] + np.array([0.0, 1.0 * empurra + 0.4 * assenta, 0.0])
            loc.garras(pose, 0.0, flex=GUARDA["curva_esq"] * (1 - w) + 0.25 * math.sin(math.pi * w))

        return self._troca(guarda0, idle0, T, acento, pulo=(0.1, 0.46), altura=1.4)

    # ---------- golpes ----------

    def ajustar_chave(self, ov, limite_sal=1.5, limite_ent=0.01):
        """Corrige a anatomia do braço solto numa pose-chave (a mão apoiada fica como está): em volta do
        punho pedido, procura punho, cotovelo e deslize da escápula que deixam a quina do ombro dentro do
        tronco e o braço fora do tórax, perto da intenção do golpe."""
        cfg = dict(GUARDA, **ov)
        base = self.pose_de(cfg, respira=0.0)
        rel, novo = {}, dict(ov)
        for lado, s in LADOS:
            X = SUF[lado]
            if cfg[f"apoio_{X}"] >= 0.5:
                continue
            sal0, ent0 = self.anatomia_braco(base, lado)
            if sal0 <= limite_sal + 0.2 and ent0 <= limite_ent + 0.01:
                continue
            p0 = np.asarray(cfg[f"punho_{X}"], float)
            polos = [cfg[f"polo_{X}"], None, (s * 1.0, 0.0, 0.0), (s * 0.7, -0.4, 0.6), (s * 0.5, 0.5, 0.7), (s * 0.9, -0.3, -0.3)]
            escs = [tuple(cfg[f"escapula_{X}"]), (0.0, 0.0, 0.0), (-0.4, 0.5, -0.6), (0.4, 0.3, -0.8), (-0.3, -0.3, 0.6)]
            melhor = None

            def provar(dp, polo, esc):
                nonlocal melhor
                p = {k: dict(v) for k, v in base.items()}
                p.pop(f"arm_{lado}", None)
                self.braco(p, lado, s, p0 + dp, cfg[f"garra_{X}"], cfg[f"giro_{X}"], polo, esc)
                sal, ent = self.anatomia_braco(p, lado)
                custo = max(0.0, sal - limite_sal) + 40 * max(0.0, ent - limite_ent) + 0.02 * float(dp @ dp)
                if melhor is None or custo < melhor[0]:
                    melhor = (custo, sal, ent, tuple(p0 + dp), polo, tuple(esc))

            for dp in np.array(np.meshgrid([-2.0, 0.0, 2.0], [-2.0, 0.0, 2.0], [-2.0, 0.0, 2.0])).reshape(3, -1).T:
                for polo in polos:
                    for esc in escs:
                        provar(dp, polo, esc)
            if melhor[1] > limite_sal + 0.5 or melhor[2] > limite_ent + 0.02:
                rng = np.random.default_rng(7)
                escs2 = escs + [(0.6, 1.0, 0.8), (0.0, 1.2, 0.0), (-0.6, 0.8, 0.4), (0.3, 0.9, -0.5)]
                for _ in range(600):
                    dp = rng.uniform(-4.0, 4.0, 3)
                    esc = escs2[rng.integers(len(escs2))] if rng.random() < 0.6 else tuple(rng.uniform(-1.0, 1.0, 3) * 0.9)
                    provar(dp, polos[rng.integers(len(polos))], esc)
            _c, sal, ent, punho, polo, esc = melhor
            novo[f"punho_{X}"], novo[f"polo_{X}"], novo[f"escapula_{X}"] = punho, polo, esc
            rel[lado] = (round(sal0, 2), round(ent0, 3), round(sal, 2), round(ent, 3))
        return novo, rel

    def golpes(self, ajustar=True, relatorio=None):
        """Clipes de golpe: nome -> (T, quadros, loop, info com os instantes de acerto e marcas)."""
        out = {}
        cache = {}
        for nome, (chaves, info, loop) in GOLPES.items():
            if ajustar:
                novas = []
                for t, ov, curva in chaves:
                    chave = repr(sorted(ov.items()))
                    if chave not in cache:
                        cache[chave] = self.ajustar_chave(ov)
                    ov2, rel = cache[chave]
                    if rel and relatorio is not None:
                        relatorio.setdefault(nome, []).append((t, rel))
                    novas.append((t, ov2, curva))
                chaves = novas
            T, quadros = self.clipe(chaves, respira=0.25 if loop else 0.15, loop=loop)
            out[nome] = (T, quadros, loop, info)
        return out


def _com(base, **kw):
    return dict(base, **kw)


# ---------- poses de apoio ----------

NO_AR = dict(  # bote: no ar, esticada, garras à frente, patas de trás arrastando para trás
    agacha=1.2, salto=3.0, empina=-2.0, apoio_esq=0.0, apoio_dir=0.0,
    punho_esq=(-1.5, -3.0, -15.0), punho_dir=(1.5, -3.0, -15.0),
    garra_esq=(-0.15, -0.3, -0.94), garra_dir=(0.15, -0.3, -0.94), curva_esq=0.1, curva_dir=0.1,
    passo_esq=5.0, passo_dir=5.0, ponta_esq=40.0, ponta_dir=40.0, ergue_esq=1.0, ergue_dir=1.0,
    cauda_livre=(-4.0, -2.0, 0.0, 2.0, 2.0), olhar=-4.0,
)
CRAVA = dict(  # cai rasgando: as duas garras cravam no chão à frente
    agacha=3.0, salto=0.0, empina=-12.0, apoio_esq=1.0, apoio_dir=1.0,
    chao_esq=(-11.0, -31.0), chao_dir=(11.0, -31.0),
    garra_esq=(-0.1, -0.85, -0.5), garra_dir=(0.1, -0.85, -0.5), curva_esq=0.7, curva_dir=0.7,
    passo_esq=1.0, passo_dir=1.0, cauda_livre=(-14.0, -8.0, -2.0, 4.0, 6.0), olhar=-10.0,  # cauda alta vira esquilo
)
VIGIA = dict(  # habilidade 1: agachada nos quatro, cabeça alta seguindo a garra ricocheteando
    agacha=2.4, empina=-4.0, olhar=4.0, recolhe=1.0,
)
PRONTO = dict(  # habilidade 1: encolhida nos quatro, patas de trás carregadas, pronta para sumir
    agacha=3.6, empina=-12.0, avanco=1.0, olhar=-10.0, ponta_esq=12.0, ponta_dir=12.0, curva_esq=0.3, curva_dir=0.3,
)
CAVA = dict(agacha=2.8, avanco=-3.0, empina=-10.0, olhar=-10.0, chao_esq=(-10.0, -27.0), chao_dir=(10.0, -27.0))
LEVANTA_DIR = dict(apoio_dir=0.0, punho_dir=(1.0, -2.0, -13.0), garra_dir=(0.1, 0.2, -0.97), curva_dir=0.2)
LEVANTA_ESQ = dict(apoio_esq=0.0, punho_esq=(-1.0, -2.0, -13.0), garra_esq=(-0.1, 0.2, -0.97), curva_esq=0.2)
RASGA_DIR = dict(apoio_dir=1.0, garra_dir=(0.1, -0.9, -0.4), curva_dir=0.9)
RASGA_ESQ = dict(apoio_esq=1.0, garra_esq=(-0.1, -0.9, -0.4), curva_esq=0.9)

GOLPES = {
    # Ataque 1, garrada: a pata direita sai do chão, abre por fora e rasga para dentro e para baixo
    # (gancho de urso/carcaju), com o corpo avançando atrás dela; depois volta a apoiar.
    "attack_1": ([
        (0.00, {}, "suave"),
        (0.10, dict(avanco=1.2, lateral=-1.0, empina=-5.0, inclina=-3.0, apoio_dir=0.0, punho_dir=(4.5, -4.0, -4.0),
                    garra_dir=(0.6, 0.1, -0.8), curva_dir=0.1, olhar=-8.0, cauda_yaw=-6.0), "suave"),
        (0.18, dict(avanco=-2.5, lateral=-0.4, empina=2.0, inclina=2.0, torce=10.0, apoio_dir=0.0, punho_dir=(-3.0, -6.5, -13.0),
                    garra_dir=(-0.6, -0.55, -0.55), curva_dir=0.6, olhar=-6.0, cauda_yaw=8.0), "solta"),
        (0.26, dict(avanco=-2.8, lateral=-0.2, empina=1.0, torce=14.0, apoio_dir=0.0, punho_dir=(-6.0, -8.0, -10.0),
                    garra_dir=(-0.7, -0.6, -0.3), curva_dir=0.9, cauda_yaw=10.0), "solta"),
        (0.42, dict(avanco=-1.0, torce=4.0, apoio_dir=1.0, chao_dir=(10.0, -24.0), curva_dir=0.3, ergue_mao_dir=0.0), "suave"),
        (0.56, {}, "suave"),
    ], {"golpes_s": [0.18], "garra": "direita"}, False),
    # Ataque 2, bote curto: encolhe, pula com as duas garras à frente e cai rasgando o chão; recua com um
    # pulinho de volta para a guarda.
    "attack_2": ([
        (0.00, {}, "suave"),
        (0.12, dict(agacha=3.4, avanco=1.4, empina=-11.0, olhar=-9.0, curva_esq=0.15, curva_dir=0.15, ponta_esq=10.0, ponta_dir=10.0), "suave"),
        (0.22, _com(NO_AR, avanco=-3.0), "solta"),
        (0.30, _com(CRAVA, avanco=-3.5), "carrega"),
        (0.42, _com(CRAVA, avanco=-3.5, agacha=2.8, empina=-10.0, chao_esq=(-11.0, -28.0), chao_dir=(11.0, -28.0),
                    curva_esq=0.95, curva_dir=0.95), "suave"),
        (0.62, dict(salto=1.0, avanco=-1.5, ergue_mao_esq=2.0, ergue_mao_dir=2.0, chao_esq=(-11.5, -25.0), chao_dir=(11.5, -25.0),
                    ergue_esq=0.6, ergue_dir=0.6), "suave"),
        (0.86, {}, "suave"),
    ], {"golpes_s": [0.30], "garra": "as duas"}, False),
    # Habilidade 1, arremesso: levanta só um pouco nas patas de trás, a pata direita vai para trás e
    # chicoteia de lado soltando a garra do meio (some no antebraço em 'solta'; o jogo cria o projétil
    # que ricocheteia a partir da mão direita); volta aos quatro apoios vigiando.
    "skill1_throw": ([
        (0.00, {}, "suave"),
        (0.16, dict(empina=14.0, agacha=1.0, avanco=1.0, torce=-10.0, apoio_dir=0.0, punho_dir=(5.0, -5.0, 1.0),
                    garra_dir=(0.5, 0.0, 0.85), curva_dir=0.2, olhar=-2.0, cauda_yaw=-8.0), "suave"),
        (0.26, dict(empina=10.0, agacha=1.4, avanco=-1.5, torce=14.0, apoio_dir=0.0, punho_dir=(-3.0, -2.0, -15.0),
                    garra_dir=(-0.2, 0.0, -1.0), curva_dir=0.1, recolhe=1.0, cauda_yaw=8.0), "solta"),
        (0.36, dict(empina=4.0, agacha=1.8, avanco=-1.8, torce=16.0, apoio_dir=0.0, punho_dir=(-5.0, -7.0, -12.0),
                    garra_dir=(-0.4, -0.5, -0.75), recolhe=1.0, cauda_yaw=10.0), "solta"),
        (0.62, VIGIA, "suave"),
    ], {"marcas_s": {"solta": 0.26}, "projetil": "sai de hand_right (garra claw_right_2) em 'solta'"}, False),
    # Habilidade 1, espera (loop): vigia a garra ricocheteando, cabeça indo de um lado para o outro.
    "skill1_wait": ([
        (0.0, VIGIA, "suave"),
        (0.3, _com(VIGIA, yaw_cabeca=18.0, lateral=0.4, cauda_yaw=6.0), "suave"),
        (0.7, _com(VIGIA, yaw_cabeca=-16.0, lateral=-0.4, cauda_yaw=-6.0), "suave"),
        (1.2, VIGIA, "suave"),
    ], {"nota": "tocar em loop enquanto a garra ricocheteia"}, True),
    # Habilidade 1, captura: levanta a pata direita e pega a garra no ar (reaparece em 'pega'); encolhe
    # nos quatro, pronta para sumir no primeiro teleporte.
    "skill1_catch": ([
        (0.00, VIGIA, "suave"),
        (0.12, _com(VIGIA, empina=10.0, apoio_dir=0.0, punho_dir=(-1.0, 2.0, -13.0), garra_dir=(0.0, 0.3, -0.95), curva_dir=0.0), "suave"),
        (0.16, _com(VIGIA, empina=8.0, apoio_dir=0.0, punho_dir=(0.0, 0.5, -11.0), garra_dir=(0.05, 0.2, -0.98), curva_dir=0.6, recolhe=0.0), "solta"),
        (0.24, _com(VIGIA, empina=2.0, apoio_dir=0.4, punho_dir=(2.0, -5.0, -9.0), curva_dir=0.4, recolhe=0.0), "solta"),
        (0.46, PRONTO, "suave"),
    ], {"marcas_s": {"pega": 0.16}}, False),
    # Habilidade 1, golpes de teleporte (o jogo teleporta antes de cada um; começam e terminam em PRONTO):
    # a) bote curto rasgando de cima com a pata direita; b) garrada lateral com a pata esquerda.
    "skill1_strike_a": ([
        (0.00, PRONTO, "suave"),
        (0.07, _com(PRONTO, salto=2.4, agacha=1.0, avanco=-2.0, empina=-4.0, apoio_dir=0.0, punho_dir=(2.0, 3.0, -12.0),
                    garra_dir=(0.1, 0.6, -0.8), curva_dir=0.1, apoio_esq=0.0, punho_esq=(-1.5, -4.0, -13.0),
                    passo_esq=4.0, passo_dir=4.0, ergue_esq=1.0, ergue_dir=1.0, ponta_esq=40.0, ponta_dir=40.0), "solta"),
        (0.14, _com(PRONTO, salto=0.6, agacha=2.4, avanco=-3.0, empina=-10.0, apoio_dir=0.0, punho_dir=(-3.0, -8.0, -13.0),
                    garra_dir=(-0.4, -0.75, -0.5), curva_dir=0.7, chao_esq=(-12.0, -27.0)), "solta"),
        (0.22, _com(PRONTO, agacha=3.2, avanco=-3.0, chao_dir=(11.0, -28.0), chao_esq=(-12.0, -27.0), curva_dir=0.9), "suave"),
        (0.32, _com(PRONTO, avanco=-1.0, salto=0.8, ergue_mao_esq=1.5, ergue_mao_dir=1.5, chao_dir=(11.5, -25.0),
                    chao_esq=(-12.0, -24.5), ergue_esq=0.5, ergue_dir=0.5), "suave"),
        (0.42, PRONTO, "suave"),
    ], {"golpes_s": [0.14], "teleporte": "o jogo teleporta o modelo antes de tocar; começa e termina em PRONTO"}, False),
    # b) garrada da esquerda: o espelho da garrada do ataque 1, saindo da pose encolhida (o gancho
    # rasteiro da r10 encolhia demais para o ombro não estourar e não lia como golpe)
    "skill1_strike_b": ([
        (0.00, PRONTO, "suave"),
        (0.06, _com(PRONTO, avanco=1.6, lateral=1.0, empina=-9.0, inclina=3.0, apoio_esq=0.0, punho_esq=(-4.5, -4.0, -4.0),
                    garra_esq=(-0.6, 0.1, -0.8), curva_esq=0.1, olhar=-12.0, cauda_yaw=6.0), "suave"),
        (0.14, _com(PRONTO, avanco=-2.5, lateral=0.4, empina=-6.0, inclina=-2.0, torce=-10.0, apoio_esq=0.0,
                    punho_esq=(3.0, -6.5, -13.0), garra_esq=(0.6, -0.55, -0.55), curva_esq=0.6, olhar=-10.0, cauda_yaw=-8.0), "solta"),
        (0.22, _com(PRONTO, avanco=-2.8, lateral=0.2, empina=-7.0, torce=-14.0, apoio_esq=0.0, punho_esq=(6.0, -8.0, -10.0),
                    garra_esq=(0.7, -0.6, -0.3), curva_esq=0.9, cauda_yaw=-10.0), "solta"),
        (0.32, _com(PRONTO, avanco=-1.0, torce=-4.0, apoio_esq=1.0, chao_esq=(-10.0, -24.0), curva_esq=0.3), "suave"),
        (0.42, PRONTO, "suave"),
    ], {"golpes_s": [0.14], "garra": "esquerda", "teleporte": "o jogo teleporta o modelo antes de tocar; começa e termina em PRONTO"}, False),
    # Habilidade 2, frenesi no chefe: encolhe, bote cravando as duas garras, rasga cavando alternando as
    # patas (como abrindo um cupinzeiro, o corpo balança de um lado para o outro), empina um pouco com as
    # duas garras no alto e desce rasgando com as duas; segura o impacto e volta com um pulinho.
    "skill2": ([
        (0.00, {}, "suave"),
        (0.16, dict(agacha=3.6, avanco=1.4, empina=-12.0, olhar=-10.0, ponta_esq=12.0, ponta_dir=12.0), "suave"),
        (0.28, _com(NO_AR, salto=2.6, avanco=-2.5), "solta"),
        (0.36, _com(CRAVA, avanco=-3.0, chao_esq=(-11.0, -30.0), chao_dir=(11.0, -30.0)), "carrega"),
        (0.44, {**CAVA, "inclina": 3.0, **LEVANTA_DIR, **RASGA_ESQ, "curva_esq": 0.7}, "solta"),
        (0.50, dict(CAVA, inclina=-3.0, **RASGA_DIR, **LEVANTA_ESQ), "solta"),
        (0.58, dict(CAVA, inclina=3.0, **RASGA_ESQ, **LEVANTA_DIR), "solta"),
        (0.66, dict(CAVA, inclina=-3.0, **RASGA_DIR, **LEVANTA_ESQ), "solta"),
        (0.74, dict(CAVA, inclina=2.0, **RASGA_ESQ, curva_dir=0.5), "solta"),
        (0.92, dict(empina=16.0, agacha=1.0, avanco=-1.0, apoio_esq=0.0, apoio_dir=0.0, punho_esq=(-2.0, 4.0, -8.0),
                    punho_dir=(2.0, 4.0, -8.0), garra_esq=(-0.1, 0.8, -0.6), garra_dir=(0.1, 0.8, -0.6), curva_esq=0.2,
                    curva_dir=0.2, cauda_livre=(-10.0, -5.0, 0.0, 4.0, 6.0), olhar=-4.0), "suave"),
        (1.08, _com(CRAVA, empina=-16.0, agacha=3.6, avanco=-3.5, chao_esq=(-10.0, -31.0), chao_dir=(10.0, -31.0),
                    curva_esq=0.9, curva_dir=0.9, cauda_livre=(-16.0, -9.0, -2.0, 4.0, 6.0), olhar=-12.0), "carrega"),
        (1.40, _com(CRAVA, empina=-14.0, agacha=3.4, avanco=-3.5, chao_esq=(-10.0, -30.0), chao_dir=(10.0, -30.0),
                    curva_esq=0.95, curva_dir=0.95, olhar=-11.0), "suave"),
        (1.62, dict(salto=1.0, avanco=-1.5, ergue_mao_esq=2.0, ergue_mao_dir=2.0, chao_esq=(-11.5, -26.0), chao_dir=(11.5, -26.0),
                    ergue_esq=0.6, ergue_dir=0.6), "suave"),
        (1.86, {}, "suave"),
    ], {"golpes_s": [0.36, 0.50, 0.58, 0.66, 0.74, 1.08], "nota": "o último acerto (1,08 s) é a descida com as duas garras"}, False),
}
