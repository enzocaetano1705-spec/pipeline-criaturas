"""Esqueleto automático a partir da grade de voxels (só numpy).

1. Grade de 1 unidade e espessura (erosões sucessivas).
2. Núcleo = ponto mais grosso perto do meio do caminho mais longo.
3. Pontas = pontos mais distantes da árvore, um de cada vez (ramos curtos, como tufos de pelo,
   são descartados por `ramo_minimo`).
4. Papéis para o plano "bípede com cauda": focinho, cauda, mãos, pés; o resto vira acessório
   (cachecol, garras extras, tufos).
5. Juntas ao longo dos caminhos medianos (ombro/quadril pela queda de espessura, cotovelo/joelho
   pela maior curva) e hierarquia com os nomes de docs/convencoes.md (iguais aos do Pavão).
"""

from __future__ import annotations

import heapq
import math

import numpy as np

VIZ26 = np.array([(i, j, k) for i in (-1, 0, 1) for j in (-1, 0, 1) for k in (-1, 0, 1) if (i, j, k) != (0, 0, 0)])
PASSO26 = np.linalg.norm(VIZ26, axis=1)


# ---------------- grade ----------------

class Grade:
    """Voxels ocupados de uma grade densa, com índice linear e vizinhança 26 em CSR."""

    def __init__(self, ocupado: np.ndarray, origem: np.ndarray, voxel: float):
        self.ocupado = ocupado
        self.origem = np.asarray(origem, float)
        self.voxel = float(voxel)
        self.idx = np.argwhere(ocupado)
        self.n = len(self.idx)
        self.ids = -np.ones(ocupado.shape, np.int64)
        self.ids[tuple(self.idx.T)] = np.arange(self.n)
        self.pos = self.origem + (self.idx + 0.5) * self.voxel
        origens, destinos, pesos = [], [], []
        forma = np.array(ocupado.shape)
        for off, w in zip(VIZ26, PASSO26):
            q = self.idx + off
            ok = np.all((q >= 0) & (q < forma), axis=1)
            alvo = np.full(self.n, -1)
            alvo[ok] = self.ids[tuple(q[ok].T)]
            sel = alvo >= 0
            origens.append(np.nonzero(sel)[0])
            destinos.append(alvo[sel])
            pesos.append(np.full(sel.sum(), w * self.voxel))
        o = np.concatenate(origens)
        ordem = np.argsort(o, kind="stable")
        self.dst = np.concatenate(destinos)[ordem]
        self.w = np.concatenate(pesos)[ordem]
        self.ptr = np.concatenate([[0], np.cumsum(np.bincount(o, minlength=self.n))])
        self._dst, self._w, self._ptr = self.dst.tolist(), self.w.tolist(), self.ptr.tolist()

    def espessura(self) -> np.ndarray:
        """Distância aproximada até fora (em unidades), por erosões com vizinhança 6."""
        g = self.ocupado.copy()
        dt = np.zeros(g.shape, float)
        passo = 0
        while g.any():
            passo += 1
            dt[g] = passo * self.voxel
            e = g.copy()
            for eixo in range(3):
                for s in (1, -1):
                    e &= np.roll(g, s, axis=eixo)
            g = e
        return dt[tuple(self.idx.T)]

    def dijkstra(self, fontes, custo_no=None, dist=None, pai=None):
        """Dijkstra multi-fonte. `custo_no` multiplica o passo ao entrar no nó."""
        dist = np.full(self.n, np.inf) if dist is None else dist
        pai = np.full(self.n, -1, np.int64) if pai is None else pai
        dl = dist.tolist()
        pl = pai.tolist()
        cn = None if custo_no is None else custo_no.tolist()
        heap = []
        for f in fontes:
            f = int(f)
            dl[f] = 0.0
            pl[f] = -1
            heap.append((0.0, f))
        heapq.heapify(heap)
        dst, w, ptr = self._dst, self._w, self._ptr
        while heap:
            d, u = heapq.heappop(heap)
            if d > dl[u]:
                continue
            for e in range(ptr[u], ptr[u + 1]):
                v = dst[e]
                nd = d + w[e] * (cn[v] if cn else 1.0)
                if nd < dl[v]:
                    dl[v] = nd
                    pl[v] = u
                    heapq.heappush(heap, (nd, v))
        return np.array(dl), np.array(pl, np.int64)


def reduzir(ocupado: np.ndarray, origem, voxel: float, fator: int = 2, minimo: int = 3):
    """Grade mais grossa: célula ocupada se ao menos `minimo` de fator³ sub-voxels estão ocupados."""
    s = np.array(ocupado.shape)
    s2 = (s + fator - 1) // fator
    pad = np.zeros(s2 * fator, bool)
    pad[: s[0], : s[1], : s[2]] = ocupado
    soma = pad.reshape(s2[0], fator, s2[1], fator, s2[2], fator).sum(axis=(1, 3, 5))
    return soma >= minimo, np.asarray(origem, float), voxel * fator


def maior_componente(g: Grade) -> np.ndarray:
    """Máscara dos nós no maior componente conexo."""
    rot = -np.ones(g.n, np.int64)
    c = 0
    tamanhos = []
    for s in range(g.n):
        if rot[s] >= 0:
            continue
        pilha = [s]
        rot[s] = c
        t = 0
        while pilha:
            u = pilha.pop()
            t += 1
            for e in range(g._ptr[u], g._ptr[u + 1]):
                v = g._dst[e]
                if rot[v] < 0:
                    rot[v] = c
                    pilha.append(v)
        tamanhos.append(t)
        c += 1
    return rot == int(np.argmax(tamanhos))


def caminho(pai: np.ndarray, no: int, parar=None) -> list[int]:
    out = [int(no)]
    while pai[out[-1]] >= 0 and not (parar is not None and parar[out[-1]]):
        out.append(int(pai[out[-1]]))
    return out


def comprimento(pts: np.ndarray) -> np.ndarray:
    """Comprimento acumulado de uma polilinha."""
    if len(pts) < 2:
        return np.zeros(len(pts))
    return np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])


def suavizar(pts: np.ndarray, janela: int = 2) -> np.ndarray:
    if len(pts) < 3:
        return pts
    out = pts.copy()
    for i in range(len(pts)):
        a, b = max(0, i - janela), min(len(pts), i + janela + 1)
        out[i] = pts[a:b].mean(0)
    return out


def ponto_em(pts: np.ndarray, s: np.ndarray, alvo: float) -> np.ndarray:
    alvo = float(np.clip(alvo, 0, s[-1]))
    i = int(np.searchsorted(s, alvo))
    if i <= 0:
        return pts[0].copy()
    if i >= len(s):
        return pts[-1].copy()
    t = (alvo - s[i - 1]) / max(s[i] - s[i - 1], 1e-9)
    return pts[i - 1] + t * (pts[i] - pts[i - 1])


# ---------------- esqueleto ----------------

def detectar(ocupado, origem, voxel, ramo_minimo_frac=0.08, max_pontas=18, sobrescrever=None, cores=None):
    """Devolve dict com pontas, papéis, caminhos e ossos (nome, pai, pivô, fim)."""
    occ1, org1, vx1 = reduzir(ocupado, origem, voxel)
    g = Grade(occ1, org1, vx1)
    viva = maior_componente(g)
    dt = g.espessura()
    dt[~viva] = 0
    lo, hi = g.pos[viva].min(0), g.pos[viva].max(0)
    tamanho = float(np.max(hi - lo))
    altura = hi[1] - lo[1]

    # núcleo: ponto mais grosso perto do meio do caminho mais longo
    qualquer = int(np.nonzero(viva)[0][0])
    d0, _ = g.dijkstra([qualquer])
    d0[~viva] = -1
    a = int(np.argmax(d0))
    da, pa = g.dijkstra([a])
    da[~viva] = -1
    b = int(np.argmax(da))
    cam = caminho(pa, b)
    meio = g.pos[cam[len(cam) // 2]]
    perto = viva & (np.linalg.norm(g.pos - meio, axis=1) < 0.25 * tamanho)
    nucleo = int(np.argmax(np.where(perto, dt, -1)))

    # custo mediano: andar por partes finas custa mais
    custo = 1.0 + 3.0 / np.maximum(dt, g.voxel)
    custo[~viva] = 1e6
    _dm, pai_med = g.dijkstra([nucleo], custo_no=custo)

    # pontas sucessivas
    na_arvore = np.zeros(g.n, bool)
    na_arvore[nucleo] = True
    dist, _ = g.dijkstra([nucleo])
    pontas = []
    ramo_minimo = ramo_minimo_frac * tamanho
    for _ in range(max_pontas):
        dd = np.where(viva, dist, -1)
        e = int(np.argmax(dd))
        if dd[e] < ramo_minimo:
            break
        cam = caminho(pai_med, e, parar=na_arvore)
        juncao = int(pai_med[cam[-1]]) if pai_med[cam[-1]] >= 0 else cam[-1]
        pontas.append({"no": e, "pos": g.pos[e], "ramo": float(dd[e]), "juncao": juncao})
        na_arvore[cam] = True
        dist, _ = g.dijkstra(cam, dist=dist)

    papeis = atribuir_papeis(pontas, lo, hi)
    if sobrescrever:
        for papel, pos in sobrescrever.get("pontas", {}).items():
            alvo = np.asarray(pos, float)
            no = int(np.argmin(np.where(viva, np.linalg.norm(g.pos - alvo, axis=1), np.inf)))
            pontas.append({"no": no, "pos": g.pos[no], "ramo": 0.0, "juncao": nucleo})
            papeis[papel] = len(pontas) - 1

    def cam_pts(i):
        c = caminho(pai_med, pontas[i]["no"])  # ponta -> núcleo
        return np.array(c), suavizar(g.pos[c])

    caminhos = {p: cam_pts(i) for p, i in papeis.items() if not p.startswith("acessorio")}
    ossos, juntas = montar_ossos(g, dt, caminhos, nucleo, papeis, pontas, cam_pts)
    if cores is not None:
        sup_pos, sup_cor = cores
        for cad in juntas["_cadeias"]:
            perto = np.linalg.norm(sup_pos - cad["pontos"][1], axis=1) < 3.0
            r, gg, b = sup_cor[perto].mean(0) if perto.any() else (0, 0, 0)
            cad["nome"] = "scarf" if (r > 1.3 * gg and r > 1.2 * b and r > 70) else "appendage"
        ossos = recompor(None, juntas)
    if sobrescrever:
        for nome, pos in sobrescrever.get("juntas", {}).items():
            juntas[nome] = np.asarray(pos, float)
        ossos = recompor(ossos, juntas)
    return {
        "grade": g, "viva": viva, "dt": dt, "nucleo": nucleo, "pontas": pontas, "papeis": papeis,
        "caminhos": caminhos, "ossos": ossos, "juntas": juntas, "limites": (lo, hi), "altura": altura,
    }


def atribuir_papeis(pontas, lo, hi) -> dict[str, int]:
    """Plano bípede com cauda. Frente = -Z, esquerda da criatura = -X."""
    alt = hi[1] - lo[1]
    comp = hi[2] - lo[2]
    pos = np.array([p["pos"] for p in pontas])
    livres = set(range(len(pontas)))
    papeis = {}

    def tomar(nome, cand, chave):
        cand = [i for i in cand if i in livres]
        if not cand:
            return
        i = min(cand, key=chave)
        papeis[nome] = i
        livres.discard(i)

    ramo_max = max(p["ramo"] for p in pontas)
    longos = {i for i in livres if pontas[i]["ramo"] >= 0.25 * ramo_max}
    tomar("cauda", livres, lambda i: -pos[i][2])
    altos = [i for i in livres if pos[i][1] > lo[1] + 0.45 * alt]
    tomar("focinho", altos, lambda i: pos[i][2] - 0.3 * pos[i][1])
    # mãos: ramos longos mais à frente de cada lado (abaixo de 60% da altura)
    medios = [i for i in longos if pos[i][1] < lo[1] + 0.6 * alt and pos[i][2] < lo[2] + 0.6 * comp]
    for lado, sinal in (("left", -1), ("right", 1)):
        tomar(f"mao_{lado}", [i for i in medios if sinal * pos[i][0] > 0], lambda i: pos[i][2])
    # pés: ramos longos que tocam o chão, o mais longo de cada lado
    baixos = [i for i in longos if pos[i][1] < lo[1] + 0.2 * alt]
    for lado, sinal in (("left", -1), ("right", 1)):
        tomar(f"pe_{lado}", [i for i in baixos if sinal * pos[i][0] > 0], lambda i: -pontas[i]["ramo"])
    for n, i in enumerate(sorted(livres)):
        papeis[f"acessorio_{n}"] = i
    return papeis


def _cruzamento_espessura(g, dt, c, pts, s):
    """Índice (ao longo do caminho ponta->núcleo) onde o membro entra no corpo."""
    esp = dt[c]
    n = len(c)
    membro = np.median(esp[: max(3, int(0.5 * n))])
    corpo = esp[-1]
    limiar = (membro + corpo) / 2
    for i in range(int(0.3 * n), n):
        if esp[i] >= limiar:
            return i
    return int(0.75 * n)




def curva_central(g, a, b, raio=4.5, passo=1.0):
    """Centro do volume em fatias perpendiculares ao segmento a→b (só voxels perto do eixo)."""
    ab = b - a
    n = np.linalg.norm(ab)
    if n < 1e-6:
        return np.array([a])
    u = ab / n
    rel = g.pos - a
    t = rel @ u
    perto = np.linalg.norm(rel - np.outer(t, u), axis=1) < raio
    pts = []
    for tt in np.arange(0, n + 1e-6, passo):
        sel = perto & (np.abs(t - tt) < 0.5 * passo + 0.25)
        if sel.sum() >= 3:
            pts.append(g.pos[sel].mean(0))
    return np.array(pts) if pts else np.array([a, b])


def _dobra(trecho: np.ndarray, frac_padrao: float) -> np.ndarray:
    """Junta do meio (joelho/cotovelo): o ponto que mais se afasta da reta entre as pontas do trecho.

    Se o membro está quase reto, usa a fração padrão do comprimento.
    """
    if len(trecho) < 3:
        return trecho[len(trecho) // 2].copy()
    a, b = trecho[0], trecho[-1]
    ab = b - a
    n = np.linalg.norm(ab) or 1.0
    t = np.clip((trecho - a) @ ab / (n * n), 0, 1)
    desvio = np.linalg.norm(trecho - (a + t[:, None] * ab), axis=1)
    miolo = (t > 0.2) & (t < 0.8)
    if miolo.any() and desvio[miolo].max() > max(1.0, 0.08 * n):
        i = int(np.argmax(np.where(miolo, desvio, -1)))
        return trecho[i].copy()
    s = comprimento(trecho)
    return ponto_em(trecho, s, frac_padrao * s[-1])


def abertura(occ: np.ndarray, passos: int) -> np.ndarray:
    """Abertura morfológica (erosão e dilatação com vizinhança 6): some com o que é mais fino que o raio."""
    e = occ.copy()
    for _ in range(passos):
        n = e.copy()
        for ax in range(3):
            for s in (1, -1):
                n &= np.roll(e, s, ax)
        e = n
    for _ in range(passos):
        n = e.copy()
        for ax in range(3):
            for s in (1, -1):
                n |= np.roll(e, s, ax)
        e = n
    return e & occ


def montar_ossos(g, dt, caminhos, nucleo, papeis, pontas, cam_pts):
    J = {}
    centro = g.pos[nucleo]
    # massa do corpo: o que sobra quando se apagam as partes mais finas que ~55% da espessura do núcleo
    raio = max(1, int(round(0.55 * dt[nucleo] / g.voxel)))
    corpo = abertura(g.ocupado, raio)[tuple(g.idx.T)]
    J["_raio_corpo"] = raio * g.voxel

    def entrada_no_corpo(c, pts, s):
        for i in range(len(c)):
            if corpo[c[i]]:
                return i
        return _cruzamento_espessura(g, dt, c, pts, s)

    def membro(papel, nomes, frac_meio=0.45, frac_ponta=0.78):
        if papel not in caminhos:
            return
        c, pts = caminhos[papel]
        s = comprimento(pts)
        k = entrada_no_corpo(c, pts, s)
        raiz = pts[k]
        sub = pts[: k + 1][::-1]  # raiz -> ponta
        ss = comprimento(sub)
        J[nomes[0]] = raiz
        J[nomes[3]] = sub[-1]
        if perna:
            # tornozelo: onde o caminho sai do chão (o pé corre deitado); joelho: onde a perna dobra
            chao, topo = sub[-1][1], raiz[1]
            alto = chao + max(2.5, 0.22 * (topo - chao))
            i_t = max((i for i in range(len(sub)) if sub[i][1] > alto), default=int(0.8 * (len(sub) - 1)))
            J[nomes[2]] = sub[i_t]
            # o joelho segue o centro do volume (a coxa peluda puxa para a frente), não o caminho mediano
            curva = curva_central(g, raiz, sub[i_t])
            J[nomes[1]] = _dobra(curva, frac_meio) if len(curva) >= 3 else _dobra(sub[: i_t + 1], frac_meio)
        else:
            J[nomes[2]] = ponto_em(sub, ss, frac_ponta * ss[-1])
            i_p = int(np.searchsorted(ss, frac_ponta * ss[-1]))
            J[nomes[1]] = _dobra(sub[: max(i_p, 2) + 1], frac_meio)
        return k

    for lado in ("left", "right"):
        perna = False
        membro(f"mao_{lado}", [f"arm_{lado}", f"forearm_{lado}", f"hand_{lado}", f"hand_{lado}_fim"], 0.4, 0.68)
        perna = True
        membro(f"pe_{lado}", [f"leg_{lado}", f"shin_{lado}", f"foot_{lado}", f"foot_{lado}_fim"], 0.5, 0.8)

    # simetria: se os dois lados concordam (pose simétrica), usa a média espelhada
    for base in ("arm", "forearm", "hand", "hand_{}_fim", "leg", "shin", "foot", "foot_{}_fim"):
        nl = base.format("left") if "{}" in base else f"{base}_left"
        nr = base.format("right") if "{}" in base else f"{base}_right"
        if nl in J and nr in J:
            m = J[nr] * [-1, 1, 1]
            if np.linalg.norm(J[nl] - m) < 6.0:
                media = (J[nl] + m) / 2
                J[nl], J[nr] = media, media * [-1, 1, 1]

    # tronco: quadris -> peito
    quadris = [J[k] for k in ("leg_left", "leg_right") if k in J]
    ombros = [J[k] for k in ("arm_left", "arm_right") if k in J]
    hip_c = np.mean(quadris, 0) if quadris else centro
    hip_c[0] = 0.0
    ch_c = np.mean(ombros, 0) if ombros else centro
    ch_c[0] = 0.0
    J["body"] = hip_c
    J["waist"] = hip_c + 0.35 * (ch_c - hip_c)
    J["torso"] = hip_c + 0.6 * (ch_c - hip_c)
    J["chest"] = ch_c

    if "focinho" in caminhos:
        c, pts = caminhos["focinho"]
        s = comprimento(pts)
        # do focinho até o ponto do caminho mais próximo do peito
        k = int(np.argmin(np.linalg.norm(pts - ch_c, axis=1)))
        sub = pts[: k + 1][::-1]  # peito -> focinho
        ss = comprimento(sub)
        J["neck_1"] = ponto_em(sub, ss, 0.3 * ss[-1])
        J["neck_2"] = ponto_em(sub, ss, 0.43 * ss[-1])
        J["head"] = ponto_em(sub, ss, 0.55 * ss[-1])
        J["head_fim"] = sub[-1]
        for n in ("neck_1", "neck_2", "head"):
            J[n][0] = 0.0
    if "cauda" in caminhos:
        c, pts = caminhos["cauda"]
        k = int(np.argmin(np.linalg.norm(pts - hip_c, axis=1)))
        sub = pts[: k + 1][::-1]  # quadril -> ponta
        ss = comprimento(sub)
        # 5 segmentos: mais ossos = cauda que curva suave na animação
        for n, f in enumerate((0.1, 0.28, 0.45, 0.62, 0.79), start=1):
            J[f"tail_{n}"] = ponto_em(sub, ss, f * ss[-1])
        J["tail_fim"] = sub[-1]
        for n in ("tail_1",):
            J[n][0] = 0.0

    # acessórios longos (cachecol, capa, antena…) ganham uma cadeia de 2 ossos; os curtos
    # (tufos, garras extras) ficam no osso mais próximo na segmentação
    tamanho = float(np.max(g.pos.max(0) - g.pos.min(0)))
    cadeias = []
    for papel, i in papeis.items():
        if not papel.startswith("acessorio") or pontas[i]["ramo"] < 0.25 * tamanho:
            continue
        c, pts = cam_pts(i)
        s = comprimento(pts)
        k = entrada_no_corpo(c, pts, s)
        sub = pts[: k + 1][::-1]
        ss = comprimento(sub)
        # um osso a cada ~5 unidades (3 a 7), como a corrente do cachecol do Greninja
        n = int(np.clip(round(ss[-1] / 5.0), 3, 7))
        cadeias.append({"papel": papel, "pontos": [ponto_em(sub, ss, f * ss[-1]) for f in np.linspace(0, 1, n + 1)]})
    J["_cadeias"] = cadeias
    return recompor(None, J), J


HIERARQUIA = [
    # nome, pai, junta do pivô, junta do fim
    ("root", None, None, None),
    ("body", "root", "body", "waist"),
    ("pelvis", "body", "body", "waist"),
    ("leg_left", "pelvis", "leg_left", "shin_left"),
    ("shin_left", "leg_left", "shin_left", "foot_left"),
    ("foot_left", "shin_left", "foot_left", "foot_left_fim"),
    ("leg_right", "pelvis", "leg_right", "shin_right"),
    ("shin_right", "leg_right", "shin_right", "foot_right"),
    ("foot_right", "shin_right", "foot_right", "foot_right_fim"),
    ("tail_1", "pelvis", "tail_1", "tail_2"),
    ("tail_2", "tail_1", "tail_2", "tail_3"),
    ("tail_3", "tail_2", "tail_3", "tail_4"),
    ("tail_4", "tail_3", "tail_4", "tail_5"),
    ("tail_5", "tail_4", "tail_5", "tail_fim"),
    ("waist", "pelvis", "waist", "torso"),
    ("torso", "waist", "torso", "chest"),
    ("arm_left", "torso", "arm_left", "forearm_left"),
    ("forearm_left", "arm_left", "forearm_left", "hand_left"),
    ("hand_left", "forearm_left", "hand_left", "hand_left_fim"),
    ("arm_right", "torso", "arm_right", "forearm_right"),
    ("forearm_right", "arm_right", "forearm_right", "hand_right"),
    ("hand_right", "forearm_right", "hand_right", "hand_right_fim"),
    ("neck_1", "torso", "neck_1", "neck_2"),
    ("neck_2", "neck_1", "neck_2", "head"),
    ("head", "neck_2", "head", "head_fim"),
]


def recompor(_ossos, J) -> list[dict]:
    out = []
    for nome, pai, a, b in HIERARQUIA:
        if nome == "root":
            out.append({"nome": "root", "pai": None, "pivo": np.zeros(3), "fim": None})
            continue
        if a not in J or b not in J:
            continue
        if pai and not any(o["nome"] == pai for o in out):
            pai = "torso" if any(o["nome"] == "torso" for o in out) else "root"
        out.append({"nome": nome, "pai": pai, "pivo": np.asarray(J[a], float), "fim": np.asarray(J[b], float)})
    for n, cad in enumerate(J.get("_cadeias", []), start=1):
        base = cad.get("nome", f"appendage_{n}")
        pts = [np.asarray(p, float) for p in cad["pontos"]]
        pai = min((o for o in out if o["fim"] is not None and not o["nome"].startswith(base)),
                  key=lambda o: _dist_segmento(pts[0], o["pivo"], o["fim"]))["nome"]
        # osso-base sem segmento próprio (no cachecol, guarda a gola); a corrente pendura nele
        out.append({"nome": base, "pai": pai, "pivo": pts[0], "fim": None})
        anterior = base
        for i in range(len(pts) - 1):
            out.append({"nome": f"{base}_{i + 1}", "pai": anterior, "pivo": pts[i], "fim": pts[i + 1]})
            anterior = f"{base}_{i + 1}"
    return out


def _dist_segmento(p, a, b):
    ab = b - a
    t = float(np.clip((p - a) @ ab / max(ab @ ab, 1e-9), 0, 1))
    return float(np.linalg.norm(p - (a + t * ab)))
