"""Combate da preguiça rogue: guarda em tripé, ataque básico e as duas habilidades.

Guarda: o tamanduá-bandeira, ameaçado, fica de pé nas patas de trás apoiado na cauda e abre as garras;
para não virar um urso de pelúcia em pé, a guarda é a de um lutador (Greninja): base baixa, larga e
escalonada, joelhos dobrados, corpo empinado sobre o quadril e inclinado para a frente, cabeça baixa
e firme no alvo, corpo torcido mostrando o ombro da frente, a garra da frente estendida e baixa
apontando para o alvo, a garra de trás guardada atrás do quadril (lâmina embainhada), o pé de trás na
ponta (pronto para o bote). A cauda apoia no chão atrás como a terceira perna, com a ponta subindo
pouco (erguida demais lembra esquilo). Tudo respira pesado (gordura), pronto para sumir.

Juntas (os blocos são rígidos e grandes): a coluna fica reta (dobrar na emenda pelve × peito abre
fresta nas costas); braços e pernas dobram como dobradiça (`ik(..., charneira=True)`); a base não é
funda demais (a coxa deita e o joelho sobra). Braço para trás: medido com `anatomia_braco` (quanto a
quina do bloco do braço escondida no tronco sai pelo ombro, e quanto do braço entra no tórax); a
garra de trás atrás do quadril sai limpa com o cotovelo para trás e a escápula deslizando um pouco.

Golpes: poses-chave (`clipe`) com curvas de tempo (carrega devagar, solta rápido), quadros do meio
resolvidos por IK; o cachecol segue o corpo com atraso (molas). Os clipes de golpe começam e terminam
na guarda (ou na pose "pronta para sumir" dos teleportes) para encadear.
"""

from __future__ import annotations

import math

import numpy as np

from clips import FPS, LADOS, Locomocao
from pose import Mola, eixo_angulo, matriz, rot_min, rx, suave

GUARDA = dict(
    empina=26.0,  # corpo gira para cima em volta do quadril (o tripé)
    torce=-24.0,  # corpo de lado, ombro esquerdo para o alvo (só o corpo inteiro torce: sem fresta)
    inclina=0.0,
    agacha=3.0,  # quadril desce (joelhos dobrados; mais fundo, a coxa deita e o joelho sobra)
    recua=1.0,  # quadril vai um pouco para trás (peso na cauda)
    avanco=0.0, lateral=0.0, sobe=0.0, salto=0.0,  # deslocamentos do quadril (golpes)
    # coluna reta: qualquer dobra na emenda pelve × peito abre fresta nas costas (blocos rígidos)
    pelve=0.0, cintura=0.0, peito=0.0,
    abre=1.25,  # base larga
    passo_left=-6.0, passo_right=3.5,  # pé esquerdo à frente, direito atrás
    ponta_left=6.0,  # o da frente quase chato (calcanhar um tiquinho erguido)
    ponta_right=28.0,  # pé de trás na ponta: calcanhar erguido (graus); a canela não deita no chão
    ergue_left=0.0, ergue_right=0.0,  # pé no ar (passo)
    polo_joelho=(0.22, 0.0, -1.0),  # joelho para a frente, pouco para fora (× lado)
    # garra da frente (esquerda): estendida e baixa, apontando para o alvo
    punho_frente=(-0.5, -5.0, -12.0), garra_frente=(0.05, -0.15, -1.0), giro_frente=-20.0,
    polo_frente=None, escapula_frente=(0.0, 0.0, 0.0),  # cotovelo como no repouso, girado com o tronco
    # garra de trás (direita): guardada atrás do quadril, garras para trás e para baixo. Busca de
    # anatomia: punho bem atrás e abaixo, cotovelo para trás, escápula desliza para dentro, para cima e
    # para a frente → a quina do ombro sai 0,4 (o walk aprovado chega a 1,5) e o braço não entra no tórax
    punho_tras=(4.0, -13.0, 9.0), garra_tras=(0.3, -0.5, 0.8), giro_tras=0.0,
    polo_tras=(0.4, -0.4, 0.9), escapula_tras=(-0.4, 0.5, -0.6),
    curva_frente=0.35, curva_tras=0.35, crispa=0.0,  # garras abertas e um pouco curvadas
    recolhe=0.0,  # 1 = a garra do meio da mão direita foi arremessada (escondida no antebraço)
    olhar=-8.0, yaw_cabeca=0.0, inclina_cabeca=-6.0,  # cabeça baixa (olha por baixo da testa)
    cauda=(-59.0, -20.0, 6.0, 18.0, 26.0),  # inclinação de mundo de cada gomo: apoia e a ponta sobe pouco
    cauda_yaw=0.0, cauda_solta=0.0,  # cauda_solta: sobe do chão (no ar, golpes)
    fita=(10.0, 8.0, 6.0, 5.0, 4.0),  # cachecol caído para trás
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

    def braco(self, pose, lado, s, punho_rel, garra_dir, giro, polo=None, escapula=None):
        """Punho num ponto relativo ao ombro (no mundo), garras apontando para garra_dir.

        Sem polo, o cotovelo aponta para onde aponta no repouso, girado junto com o tronco: o braço
        dobra do jeito natural do bloco (sem ombro "invertido" em relação ao cotovelo). `escapula`
        desliza o ombro (no referencial do tronco), como a escápula faz quando o braço vai para trás."""
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

    def esconder_garra(self, pose):
        """A garra arremessada some: gira para trás, alinhada com o antebraço, e fica dentro dele
        (antebraço 14 de comprido e 4×5 de seção; a garra tem 10 por 2×2)."""
        r = self.r
        mats = r.mats(pose)
        Wf = mats["forearm_right"]
        eixo = Wf[:3, :3] @ (r.piv("hand_right") - r.piv("forearm_right"))  # do cotovelo para o punho
        r.mundo_para_local(pose, "claw_right_2", rot_min(self.d_arremesso, -eixo))

    def cauda_tripe(self, pose, angulos, yaw=0.0, folga=0.0):
        """Cada gomo com a inclinação de mundo pedida (negativa = desce); escala até a cauda tocar o chão
        (ou ficar `folga` acima dele, no ar)."""
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
            if montar(mid) > self.loc.chao + 0.05 + folga:
                lo = mid
            else:
                hi = mid
        montar(lo)

    def pe(self, pose, lado, s, alvo, ponta=0.0, polo=(0.35, 0.0, -1.0), ergue=0.0):
        """Pé plantado; ponta > 0 ergue o calcanhar (só a ponta no chão), subindo o tornozelo o preciso.
        A perna dobra como dobradiça. ergue > 0 tira o pé do chão (dedos apontando para baixo)."""
        loc = self.loc
        alvo = np.array(alvo, float)
        polo = np.array([polo[0] * s, polo[1], polo[2]])
        for _ in range(4):
            loc.perna(pose, lado, s, alvo, -ponta, charneira=True, polo=polo)
            falta = loc.chao - self._menor_y(pose, (f"foot_{lado}",))
            if abs(falta) < 1e-3:
                break
            alvo[1] += falta
        if ergue > 1e-3:
            loc.perna(pose, lado, s, alvo + np.array([0.0, ergue, 0.0]), -ponta - 14.0 * min(1.0, ergue / 2.5),
                      charneira=True, polo=polo)

    # ---------- anatomia do braço (blocos grandes e rígidos) ----------

    def _pontos(self, c, passo=0.75):
        """Pontos de grade dentro do cubo, no espaço de repouso (com a rotação própria do cubo)."""
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
        """Distância de cada ponto até o cubo mais próximo da lista (0 se estiver dentro de algum)."""
        d = np.full(len(pts), np.inf)
        for c in cubos:
            M = mats[c.osso] @ self.loc._mat_cubo(c)
            local = (pts - M[:3, 3]) @ M[:3, :3]
            d = np.minimum(d, np.linalg.norm(local - np.clip(local, c.de, c.ate), axis=1))
        return d

    def anatomia_braco(self, pose, lado):
        """(saliência, enterrado): o quanto (em unidades) a quina do bloco do braço que no repouso fica
        dentro do tronco sai para fora dele (ombro "estourado"), e a fração da parte visível de braço,
        antebraço e mão que entra no tronco ou nas coxas (braço enterrado no tórax)."""
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

    def _desenterrar(self, pose, lado, s, suf, cfg, punho, R, limite=0.02):
        """Se o braço entrar no tronco ou nas coxas, empurra o punho para a frente e para fora (no sentido
        para onde o corpo olha) até sair: o golpe faz o arco por fora do corpo em vez de atravessá-lo."""
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
                self.braco(p, lado, s, punho + k * f + j * o, cfg[f"garra_{suf}"], cfg[f"giro_{suf}"], cfg[f"polo_{suf}"], cfg[f"escapula_{suf}"])
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

    def maos_acima_do_chao(self, pose, folga=0.3):
        """Se a mão ou uma garra encostar no chão, gira o braço no ombro até sair."""
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

    # ---------- pose a partir dos parâmetros ----------

    def pose_de(self, cfg, t=0.0, T=T_GUARDA, respira=1.0, fita_extra=None):
        """Pose completa a partir dos parâmetros (GUARDA + mudanças). `respira` liga a respiração e o
        movimento miúdo da garra da frente; `fita_extra` = [(pitch, yaw)] do cachecol (molas)."""
        cfg = dict(GUARDA, **cfg)
        loc, r = self.loc, self.r
        pose = {}
        fase = t / T
        resp = respira * math.sin(4 * math.pi * fase)  # duas respirações por loop (~1,6 s cada)
        R = matriz([cfg["empina"] + 0.9 * resp, cfg["torce"], cfg["inclina"] + respira * 0.7 * math.sin(2 * math.pi * (fase - 0.2))])
        H = self.quadril + np.array([cfg["lateral"], -cfg["agacha"] + cfg["sobe"] + cfg["salto"] + 0.3 * resp, cfg["recua"] + cfg["avanco"]])
        pose["body"] = {"matriz": R, "posicao": H - self.P - R @ (self.quadril - self.P)}
        pose["pelvis"] = {"rotacao": [cfg["pelve"], 0.0, 0.0]}
        pose["waist"] = {"rotacao": [cfg["cintura"] + 0.3 * respira * math.sin(4 * math.pi * (fase - 0.04)), 0.0, 0.0]}
        pose["torso"] = {"rotacao": [cfg["peito"] + 0.5 * respira * math.sin(4 * math.pi * (fase - 0.08)), 0.0, 0.0]}
        for lado, s in LADOS:
            base = r.piv(f"foot_{lado}")
            alvo = np.array([base[0] * cfg["abre"], loc.chao + loc.alt_tornozelo, base[2] + cfg[f"passo_{lado}"]])
            self.pe(pose, lado, s, alvo, cfg[f"ponta_{lado}"], cfg["polo_joelho"], cfg["salto"] + cfg[f"ergue_{lado}"])
        cauda = np.asarray(cfg["cauda"], float) + respira * np.array([0, 0, 0, 3.0, 6.0]) * math.sin(2 * math.pi * (fase - 0.3))
        self.cauda_tripe(pose, cauda, yaw=cfg["cauda_yaw"] + 2.0 * respira * math.sin(2 * math.pi * (fase - 0.45)),
                         folga=cfg["salto"] + 6.0 * cfg["cauda_solta"])
        mov = respira * np.array([0.3 * math.cos(2 * math.pi * fase), 0.4 * math.sin(4 * math.pi * (fase - 0.1)), 0.3 * math.sin(2 * math.pi * fase)])
        for lado, s, suf, m_ in (("left", -1.0, "frente", mov), ("right", 1.0, "tras", 0.5 * mov)):
            punho = np.asarray(cfg[f"punho_{suf}"], float) + m_
            self.braco(pose, lado, s, punho, cfg[f"garra_{suf}"], cfg[f"giro_{suf}"], cfg[f"polo_{suf}"], cfg[f"escapula_{suf}"])
            self._desenterrar(pose, lado, s, suf, cfg, punho, R)
        loc.garras(pose, 0.0, flex=cfg["curva_frente"] + 0.6 * cfg["crispa"], lados=("left",))
        loc.garras(pose, 0.0, flex=cfg["curva_tras"], lados=("right",))
        if cfg["recolhe"] >= 0.5:
            self.esconder_garra(pose)
        loc.cabeca_estavel(pose, pitch=cfg["olhar"] + 0.8 * resp, yaw=cfg["yaw_cabeca"], roll=cfg["inclina_cabeca"], rigidez=0.95)
        extra = fita_extra or [(0.0, 0.0)] * 5
        fita = [[cfg["fita"][k] + 3.0 * respira * math.sin(2 * math.pi * (fase - 0.1 * (k + 1))) + extra[k][0],
                 2.5 * respira * math.sin(2 * math.pi * (fase - 0.12 * k)) + extra[k][1], 0.0] for k in range(5)]
        loc.corrente(pose, [f"scarf_{k}" for k in range(1, 6)], fita)
        if cfg["salto"] > 0.05:
            self.maos_acima_do_chao(pose)
        return pose

    def pose_guarda(self, cfg=None, t=0.0, T=T_GUARDA):
        """Guarda em tripé no tempo t do loop: respiração pesada (2 por loop), a garra da frente se
        crispa e estala uma vez, a ponta da cauda e o cachecol não param."""
        u = (t - 0.55 * T) / (0.16 * T)
        crispa = suave(u / 0.7) if u < 0.7 else (1 - suave((u - 0.7) / 0.12)) - 0.25 * math.sin(math.pi * min(1.0, max(0.0, (u - 0.82) / 0.3)))
        crispa = crispa if 0 <= u <= 1.12 else 0.0
        return self.pose_de(dict(cfg or {}, crispa=crispa), t, T)

    def guarda(self, T=T_GUARDA, cfg=None):
        n = int(round(T * FPS))
        quadros = [(i * T / n, self.pose_guarda(cfg, i * T / n, T)) for i in range(n)]
        quadros.append((T, quadros[0][1]))
        return T, quadros, {}

    # ---------- poses-chave ----------

    def clipe(self, chaves, respira=0.25, loop=False):
        """chaves = [(t, mudanças sobre GUARDA, curva até esta chave)]; a primeira em t=0, a última em T.
        Os parâmetros (punhos, direção das garras, torção, avanço, salto, cauda...) são interpolados
        com a curva de cada trecho e a pose de cada quadro é resolvida por IK. O cachecol atrasa (molas
        puxadas pela torção, pelo avanço e pelo salto do corpo)."""
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
        # cachecol: molas puxadas pela velocidade do corpo (atrasa na torção, esvoaça no avanço e no salto)
        molas = [Mola(3.2, 0.32, 2) for _ in range(5)]
        dt = T / n
        extras = []
        for voltas in range(2 if loop else 1):
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
                Rpe = mats[f"foot_{lado}"][:3, :3]  # orientação do pé misturada (pé chato ↔ na ponta)
                alvo = Ai[lado] + (Af[lado] - Ai[lado]) * u + np.array([0.0, altura * no_ar, 0.0])
                self.r.ik(pose, "pelvis", f"leg_{lado}", f"shin_{lado}", f"foot_{lado}", alvo, np.array([GUARDA["polo_joelho"][0] * s, 0.0, -1.0]), charneira=True)
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
            enc = math.sin(math.pi * min(1.0, t / 0.18))
            pulo = math.sin(math.pi * min(1.0, max(0.0, (t - 0.16) / 0.3)))
            assenta = -math.sin(math.pi * min(1.0, max(0.0, (t - 0.42) / 0.18)))
            dy = -0.9 * enc * (t < 0.18) + 2.0 * pulo + 0.8 * assenta
            pose["body"]["posicao"] = pose["body"]["posicao"] + np.array([0.0, dy, 0.0])
            pose["body"]["matriz"] = pose["body"]["matriz"] @ rx(4.0 * enc * (t < 0.18) - 3.0 * assenta)
            fecha = suave(t / 0.16) * (1 - suave((t - 0.38) / 0.08))  # fecha as garras e estala na queda
            estalo = 0.3 * math.sin(math.pi * min(1.0, max(0.0, (t - 0.42) / 0.14)))
            loc.garras(pose, 0.0, flex=GUARDA["curva_frente"] * w + 0.9 * fecha - estalo)

        return self._troca(idle0, guarda0, T, acento)

    def sair(self, guarda0, idle0, T=0.7):
        """Guarda → idle: relaxa, pula de volta para a base de pé e solta as garras."""
        loc = self.loc

        def acento(t, w, pose):
            pulo = math.sin(math.pi * min(1.0, max(0.0, (t - 0.12) / 0.32)))
            assenta = -math.sin(math.pi * min(1.0, max(0.0, (t - 0.44) / 0.22)))
            pose["body"]["posicao"] = pose["body"]["posicao"] + np.array([0.0, 1.4 * pulo + 0.5 * assenta, 0.0])
            loc.garras(pose, 0.0, flex=GUARDA["curva_frente"] * (1 - w) + 0.25 * math.sin(math.pi * w))

        return self._troca(guarda0, idle0, T, acento, pulo=(0.12, 0.5), altura=1.6)

    # ---------- golpes ----------

    def ajustar_chave(self, ov, limite_sal=1.5, limite_ent=0.01):
        """Corrige a anatomia dos braços numa pose-chave: em volta do punho pedido (até 2 unidades),
        procura punho, direção do cotovelo e deslize da escápula que deixam a quina do ombro dentro do
        tronco (saliência) e o braço fora do tórax (enterrado), ficando perto da intenção do golpe.
        Devolve as mudanças corrigidas e o relatório (antes → depois)."""
        cfg = dict(GUARDA, **ov)
        base = self.pose_de(cfg, respira=0.0)
        rel, novo = {}, dict(ov)
        for lado, s, sufixo in (("left", -1.0, "frente"), ("right", 1.0, "tras")):
            sal0, ent0 = self.anatomia_braco(base, lado)
            if sal0 <= limite_sal + 0.2 and ent0 <= limite_ent + 0.01:
                continue
            p0 = np.asarray(cfg[f"punho_{sufixo}"], float)
            polos = [cfg[f"polo_{sufixo}"], None, (s * 1.0, 0.0, 0.0), (s * 0.7, -0.4, 0.6), (s * 0.5, 0.5, 0.7), (s * 0.9, -0.3, -0.3)]
            escs = [tuple(cfg[f"escapula_{sufixo}"]), (0.0, 0.0, 0.0), (-0.4, 0.5, -0.6), (0.4, 0.3, -0.8), (-0.3, -0.3, 0.6)]
            melhor = None

            def provar(dp, polo, esc):
                nonlocal melhor
                p = {k: dict(v) for k, v in base.items()}
                p.pop(f"arm_{lado}", None)
                self.braco(p, lado, s, p0 + dp, cfg[f"garra_{sufixo}"], cfg[f"giro_{sufixo}"], polo, esc)
                sal, ent = self.anatomia_braco(p, lado)
                custo = max(0.0, sal - limite_sal) + 40 * max(0.0, ent - limite_ent) + 0.02 * float(dp @ dp)
                if melhor is None or custo < melhor[0]:
                    melhor = (custo, sal, ent, tuple(p0 + dp), polo, tuple(esc))

            for dp in np.array(np.meshgrid([-2.0, 0.0, 2.0], [-2.0, 0.0, 2.0], [-2.0, 0.0, 2.0])).reshape(3, -1).T:
                for polo in polos:
                    for esc in escs:
                        provar(dp, polo, esc)
            if melhor[1] > limite_sal + 0.5 or melhor[2] > limite_ent + 0.02:
                # segunda passada, mais larga: punho até 4 unidades e escápula subindo/recuando (braço no alto
                # ou atrás, como num arremesso)
                rng = np.random.default_rng(7)
                escs2 = escs + [(0.6, 1.0, 0.8), (0.0, 1.2, 0.0), (-0.6, 0.8, 0.4), (0.3, 0.9, -0.5)]
                for _ in range(600):
                    dp = rng.uniform(-4.0, 4.0, 3)
                    esc = escs2[rng.integers(len(escs2))] if rng.random() < 0.6 else tuple(rng.uniform(-1.0, 1.0, 3) * 0.9)
                    provar(dp, polos[rng.integers(len(polos))], esc)
            _c, sal, ent, punho, polo, esc = melhor
            novo[f"punho_{sufixo}"], novo[f"polo_{sufixo}"], novo[f"escapula_{sufixo}"] = punho, polo, esc
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


# Poses de apoio dos golpes (mudanças sobre a GUARDA)
VIGIA = dict(  # habilidade 1: acompanha a garra ricocheteando, garra da frente apontando
    torce=-12.0, agacha=2.4, empina=30.0, punho_frente=(-0.5, -2.0, -14.0), garra_frente=(0.0, 0.05, -1.0),
    punho_tras=(3.5, -12.0, 7.0), recolhe=1.0, olhar=-4.0,
)
PRONTO = dict(  # habilidade 1: agachada, pronta para sumir no teleporte (começo e fim de cada golpe)
    agacha=4.2, empina=22.0, torce=-18.0, punho_frente=(-2.0, -8.5, -10.0), garra_frente=(-0.1, -0.4, -0.9),
    olhar=-12.0, curva_frente=0.2, curva_tras=0.2,
)
POLO_ALTO = (0.7, -0.4, 0.6)  # cotovelo direito para fora e para trás quando a garra vem para a frente


def _com(base, **kw):
    return dict(base, **kw)


GOLPES = {
    # Ataque básico 1: saque da garra de trás (iaido) — sai de trás do quadril, sobe em diagonal pela
    # frente até o alto do outro lado, com o corpo girando para dentro do golpe e um passo de avanço.
    "attack_1": ([
        (0.00, {}, "suave"),
        (0.12, dict(torce=-34.0, agacha=3.6, punho_tras=(4.5, -13.5, 10.5), garra_tras=(0.25, -0.55, 0.8),
                    punho_frente=(-0.5, -4.0, -13.0), olhar=-11.0, cauda_yaw=3.0), "suave"),
        (0.20, dict(torce=-8.0, avanco=-1.2, agacha=3.3, punho_tras=(3.0, -10.0, -3.0), garra_tras=(0.25, -0.6, -0.76),
                    polo_tras=POLO_ALTO, punho_frente=(0.5, -5.0, -9.0)), "carrega"),
        (0.26, dict(torce=16.0, avanco=-2.4, agacha=2.6, empina=30.0, punho_tras=(-3.5, 3.0, -13.0),
                    garra_tras=(-0.45, 0.55, -0.7), giro_tras=-30.0, polo_tras=POLO_ALTO,
                    punho_frente=(2.0, -6.0, -5.5), garra_frente=(0.3, -0.3, -0.9), olhar=-9.0, cauda_yaw=-8.0), "solta"),
        (0.36, dict(torce=22.0, avanco=-2.6, agacha=2.7, empina=31.0, punho_tras=(-5.0, 5.0, -10.5),
                    garra_tras=(-0.6, 0.6, -0.5), giro_tras=-40.0, polo_tras=POLO_ALTO,
                    punho_frente=(2.0, -6.0, -5.5), garra_frente=(0.3, -0.3, -0.9), cauda_yaw=-10.0), "solta"),
        (0.62, {}, "suave"),
    ], {"golpes_s": [0.26], "garra": "direita"}, False),
    # Ataque básico 2: corte horizontal da garra da frente, da esquerda para a direita, girando o corpo.
    "attack_2": ([
        (0.00, {}, "suave"),
        (0.10, dict(torce=-12.0, agacha=3.3, punho_frente=(-6.0, -2.0, -10.0), garra_frente=(-0.6, 0.1, -0.8),
                    giro_frente=-40.0, olhar=-10.0, cauda_yaw=-4.0), "suave"),  # recuo para o lado (para trás estoura o ombro)
        (0.18, dict(torce=-40.0, avanco=-2.0, agacha=2.8, punho_frente=(5.0, -4.5, -12.5), garra_frente=(0.75, -0.1, -0.65),
                    giro_frente=10.0, cauda_yaw=8.0), "solta"),
        (0.28, dict(torce=-46.0, avanco=-2.2, agacha=2.9, punho_frente=(8.0, -5.5, -8.0), garra_frente=(0.85, -0.2, -0.45),
                    giro_frente=20.0, cauda_yaw=9.0), "solta"),
        (0.56, {}, "suave"),
    ], {"golpes_s": [0.18], "garra": "esquerda"}, False),
    # Habilidade 1, parte 1: arremesso de lado da garra do meio da mão direita (ela some no antebraço
    # no instante de soltar; o jogo cria o projétil que ricocheteia a partir da mão direita).
    "skill1_throw": ([
        (0.00, {}, "suave"),
        # o arremesso sai da bainha (garra guardada atrás do quadril): o corpo enrola mais e o braço só
        # vai um pouco mais para trás; erguer o braço para trás e para cima estoura o ombro do bloco
        (0.22, dict(torce=-42.0, agacha=3.6, empina=28.0, punho_tras=(4.5, -11.0, 10.5), garra_tras=(0.3, -0.3, 0.9),
                    punho_frente=(-1.0, -1.0, -14.0), garra_frente=(0.0, 0.1, -1.0),
                    olhar=-6.0, cauda_yaw=6.0), "suave"),
        (0.34, dict(torce=8.0, avanco=-1.6, agacha=2.8, empina=30.0, punho_tras=(-1.5, -1.0, -15.0), garra_tras=(-0.1, 0.0, -1.0),
                    polo_tras=(0.6, -0.6, 0.5), punho_frente=(1.5, -6.0, -6.0), recolhe=1.0, cauda_yaw=-6.0), "solta"),
        (0.46, dict(torce=16.0, avanco=-1.8, agacha=2.6, empina=30.0, punho_tras=(-4.0, -6.0, -12.0), garra_tras=(-0.3, -0.4, -0.85),
                    polo_tras=(0.6, -0.6, 0.5), punho_frente=(1.0, -6.0, -6.0), recolhe=1.0, cauda_yaw=-8.0), "solta"),
        (0.80, VIGIA, "suave"),
    ], {"marcas_s": {"solta": 0.34}, "projetil": "sai de hand_right (garra claw_right_2) em 'solta'"}, False),
    # Habilidade 1, parte 2 (loop): acompanha a garra ricocheteando de inimigo em inimigo.
    "skill1_wait": ([
        (0.0, VIGIA, "suave"),
        (0.3, _com(VIGIA, yaw_cabeca=18.0, punho_frente=(1.5, -2.0, -13.5)), "suave"),
        (0.7, _com(VIGIA, yaw_cabeca=-16.0, punho_frente=(-2.5, -2.0, -13.5)), "suave"),
        (1.2, VIGIA, "suave"),
    ], {"nota": "tocar em loop enquanto a garra ricocheteia"}, True),
    # Habilidade 1, parte 3: a garra volta e ela pega (a garra reaparece na mão em 'pega'); termina
    # agachada, pronta para sumir no primeiro teleporte.
    "skill1_catch": ([
        (0.00, VIGIA, "suave"),
        (0.14, _com(VIGIA, torce=-2.0, punho_tras=(-1.0, 1.0, -13.0), garra_tras=(0.0, 0.2, -1.0), polo_tras=(0.6, -0.6, 0.5)), "suave"),
        (0.18, _com(VIGIA, torce=0.0, punho_tras=(0.5, 0.0, -10.0), garra_tras=(0.05, 0.1, -1.0), polo_tras=(0.6, -0.6, 0.5), recolhe=0.0), "solta"),
        (0.26, _com(VIGIA, torce=-6.0, agacha=3.2, punho_tras=(2.5, -4.0, -6.0), garra_tras=(0.1, -0.2, -0.97), polo_tras=(0.6, -0.6, 0.5), recolhe=0.0), "solta"),
        (0.50, PRONTO, "suave"),
    ], {"marcas_s": {"pega": 0.18}}, False),
    # Habilidade 1, parte 4: golpe curto em cada marcado (o jogo teleporta antes de cada um). Começa e
    # termina na pose PRONTO para encadear; a e b alternam as garras.
    "skill1_strike_a": ([
        (0.00, PRONTO, "suave"),
        (0.08, _com(PRONTO, salto=1.5, agacha=2.0, torce=-30.0, punho_tras=(3.0, 6.0, 2.0), garra_tras=(0.1, 0.9, -0.4),
                    polo_tras=POLO_ALTO, cauda_solta=0.5), "solta"),
        (0.14, _com(PRONTO, salto=0.8, agacha=3.0, torce=10.0, avanco=-1.5, punho_tras=(-4.0, -8.0, -12.0),
                    garra_tras=(-0.3, -0.7, -0.65), polo_tras=POLO_ALTO, cauda_solta=0.3), "solta"),
        (0.22, _com(PRONTO, agacha=4.0, torce=14.0, avanco=-1.5, punho_tras=(-5.0, -10.0, -9.0), garra_tras=(-0.35, -0.8, -0.5),
                    polo_tras=POLO_ALTO), "solta"),
        (0.42, PRONTO, "suave"),
    ], {"golpes_s": [0.14], "teleporte": "o jogo teleporta o modelo antes de tocar; começa e termina em PRONTO"}, False),
    "skill1_strike_b": ([
        (0.00, PRONTO, "suave"),
        (0.08, _com(PRONTO, agacha=4.6, torce=-6.0, punho_frente=(4.0, -10.0, -6.0), garra_frente=(0.5, -0.5, -0.7)), "carrega"),
        (0.14, _com(PRONTO, salto=1.2, agacha=2.2, torce=-40.0, avanco=-1.2, punho_frente=(-3.5, 1.5, -12.5),
                    garra_frente=(-0.4, 0.65, -0.65), giro_frente=-30.0, cauda_solta=0.4), "solta"),
        (0.22, _com(PRONTO, salto=0.6, agacha=3.0, torce=-44.0, avanco=-1.2, punho_frente=(-4.0, 2.0, -11.0),
                    garra_frente=(-0.5, 0.7, -0.5), cauda_solta=0.2), "solta"),
        (0.42, PRONTO, "suave"),
    ], {"golpes_s": [0.14], "teleporte": "o jogo teleporta o modelo antes de tocar; começa e termina em PRONTO"}, False),
    # Habilidade 2: sequência no chefe — encolhe, bote com estocada, três cortes alternados, X com as
    # duas garras, pulo com as garras no alto e golpe de cima para baixo com as duas; segura o impacto e
    # volta para a guarda.
    "skill2": ([
        (0.00, {}, "suave"),
        (0.16, dict(agacha=4.4, empina=22.0, torce=-30.0, olhar=-12.0, punho_frente=(-1.5, -8.0, -9.0),
                    punho_tras=(4.5, -13.0, 10.0)), "suave"),
        (0.30, dict(agacha=2.6, torce=-2.0, avanco=-3.2, punho_tras=(-1.0, -3.0, -15.0), garra_tras=(-0.05, 0.0, -1.0),
                    polo_tras=POLO_ALTO, punho_frente=(1.5, -6.0, -6.0), cauda_yaw=-5.0), "solta"),
        (0.42, dict(agacha=2.7, torce=-40.0, avanco=-3.4, punho_frente=(5.0, -4.0, -12.0), garra_frente=(0.75, -0.1, -0.65),
                    giro_frente=10.0, punho_tras=(3.0, -10.0, 4.0), cauda_yaw=7.0), "solta"),
        (0.54, dict(agacha=2.7, torce=12.0, avanco=-3.4, punho_tras=(-3.5, 2.0, -13.0), garra_tras=(-0.45, 0.55, -0.7),
                    giro_tras=-30.0, polo_tras=POLO_ALTO, punho_frente=(1.5, -6.0, -6.0), cauda_yaw=-7.0), "solta"),
        (0.66, dict(agacha=2.6, torce=-36.0, avanco=-3.5, salto=0.6, punho_frente=(-4.0, 3.0, -12.0), garra_frente=(-0.4, 0.7, -0.6),
                    giro_frente=-30.0, punho_tras=(3.0, -10.0, 4.0), cauda_yaw=6.0, cauda_solta=0.3), "solta"),
        (0.84, dict(agacha=3.8, torce=-20.0, avanco=-3.0, punho_frente=(-7.0, -2.0, -7.0), garra_frente=(-0.7, 0.0, -0.7),
                    punho_tras=(7.0, -2.0, -2.0), garra_tras=(0.7, 0.0, -0.7), polo_tras=POLO_ALTO), "suave"),
        (0.96, dict(agacha=2.6, torce=-20.0, avanco=-3.6, punho_frente=(4.0, -6.0, -12.5), garra_frente=(0.6, -0.2, -0.75),
                    punho_tras=(-4.0, -6.0, -12.5), garra_tras=(-0.6, -0.2, -0.75), polo_tras=POLO_ALTO), "solta"),
        (1.20, dict(agacha=4.6, empina=20.0, torce=-16.0, avanco=-3.0, punho_frente=(-1.0, -8.0, -8.0),
                    punho_tras=(1.0, -8.0, -8.0), garra_tras=(0.05, -0.4, -0.9), polo_tras=POLO_ALTO), "suave"),
        # chaves do meio na subida e na descida: as garras passam pela frente (direto de baixo para o
        # alto, o bloco do braço gira demais e a quina do ombro aparece)
        (1.30, dict(salto=3.0, agacha=2.0, empina=30.0, torce=-12.0, avanco=-3.2, punho_frente=(-1.0, 3.0, -10.0),
                    garra_frente=(0.0, 0.6, -0.8), punho_tras=(1.0, 3.0, -10.0), garra_tras=(0.0, 0.6, -0.8),
                    polo_tras=(0.6, -0.4, 0.7), cauda_solta=0.6, olhar=-6.0), "solta"),
        (1.42, dict(salto=6.0, agacha=1.0, empina=34.0, torce=-10.0, avanco=-3.5, punho_frente=(-1.0, 8.0, -4.0),
                    garra_frente=(0.0, 0.9, -0.4), punho_tras=(1.0, 8.0, -4.0), garra_tras=(0.0, 0.9, -0.4),
                    polo_tras=(0.6, -0.4, 0.7), cauda_solta=1.0, olhar=-4.0), "suave"),
        (1.52, dict(salto=3.0, agacha=2.5, empina=26.0, torce=-12.0, avanco=-3.8, punho_frente=(-1.0, 2.0, -12.0),
                    garra_frente=(0.0, 0.2, -1.0), punho_tras=(1.0, 2.0, -12.0), garra_tras=(0.0, 0.2, -1.0),
                    polo_tras=(0.6, -0.4, 0.7), cauda_solta=0.6, olhar=-10.0), "carrega"),
        (1.62, dict(agacha=4.8, empina=18.0, torce=-12.0, avanco=-4.0, punho_frente=(-1.5, -10.0, -10.0),
                    garra_frente=(0.0, -0.8, -0.6), punho_tras=(1.5, -10.0, -10.0), garra_tras=(0.0, -0.8, -0.6),
                    polo_tras=(0.6, -0.4, 0.7), olhar=-14.0), "carrega"),
        (1.95, dict(agacha=4.6, empina=19.0, torce=-12.0, avanco=-4.0, punho_frente=(-1.5, -9.5, -10.0),
                    garra_frente=(0.0, -0.8, -0.6), punho_tras=(1.5, -9.5, -10.0), garra_tras=(0.0, -0.8, -0.6),
                    polo_tras=(0.6, -0.4, 0.7), olhar=-12.0), "suave"),
        (2.50, {}, "suave"),
    ], {"golpes_s": [0.30, 0.42, 0.54, 0.66, 0.96, 1.62], "nota": "o último acerto (1,62 s) é o golpe de cima com as duas garras"}, False),
}
