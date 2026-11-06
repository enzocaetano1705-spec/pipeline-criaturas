"""Segmentação por osso e cobertura de cada parte com poucos cubos alinhados ao osso.

- Segmentação: Voronoi geodésico dentro do volume (cada voxel vai para o osso mais próximo
  andando por dentro da criatura, então a garra não "pula" para o pé vizinho).
- Cubos pela anatomia: membros com um cubo por osso real (dois só se o volume muda muito), pé
  deitado no chão, tronco com poucos cubos grandes (cintura e neck_2 sem cubo, só para animar),
  cauda/cabeça/fita como correntes no eixo do osso, cada cubo começando 1 unidade dentro do pai.
  Garras pelas pontas: cada garra vai da base comum até a sua ponta. Cachecol: gola numa peça só,
  mais larga que o pescoço, e fita achatada numa corrente de ossos (como no Greninja do Cobblemon). Pares esquerda/direita são
  ajustados juntos e espelhados; partes do meio ficam simétricas em X. No fim, cubos quase
  inteiros dentro de outros são retirados.
"""

from __future__ import annotations

import itertools
import math

import numpy as np

import esqueleto

ESPELHO = np.array([-1.0, 1.0, 1.0])





def base_nome(nome):
    return nome.replace("_left", "").replace("_right", "")


def cremoso(cores):
    """Garras/unhas claras: muito claras e quentes (R ≥ G ≥ B)."""
    c = np.asarray(cores, float)
    return (c.max(1) > 0.72 * 255) & (c[:, 0] >= c[:, 1]) & (c[:, 1] >= c[:, 2])


def vermelho(cores):
    """Tecido vinho (cachecol): R bem acima de G e B."""
    c = np.asarray(cores, float)
    # no vinho o azul acompanha o verde (tom carmim); no marrom o azul fica bem abaixo do verde
    return (c[:, 0] > 1.6 * c[:, 1]) & (c[:, 0] > 1.4 * c[:, 2]) & (c[:, 2] > 0.85 * c[:, 1]) & (c[:, 0] > 60)


def dourado(cores):
    """Metal dourado (broche, fivela): claro, quente e saturado."""
    c = np.asarray(cores, float)
    return (c[:, 0] > 170) & (c[:, 1] > 0.55 * c[:, 0]) & (c[:, 2] < 0.2 * c[:, 0])


def par(nome):
    if "_left" in nome:
        return nome.replace("_left", "_right")
    if "_right" in nome:
        return nome.replace("_right", "_left")
    return None


# ---------------- segmentação ----------------

def segmentar(ocupado, origem, voxel, ossos):
    """Rótulo (índice em `ossos`) de cada voxel ocupado. Devolve (grade, rótulos)."""
    g = esqueleto.Grade(ocupado, origem, voxel)
    fontes, rot_fonte = [], []
    for k, o in enumerate(ossos):
        if o["fim"] is None or o["nome"] == "body":
            continue
        a, b = o["pivo"], o["fim"]
        n = max(2, int(np.linalg.norm(b - a) / (voxel * 0.5)))
        # pula a junta de origem (fica com o pai) e cobre até a ponta
        for t in np.linspace(0.08, 1.0, n):
            p = a + t * (b - a)
            ijk = np.floor((p - g.origem) / voxel).astype(int)
            if np.all(ijk >= 0) and np.all(ijk < ocupado.shape) and g.ids[tuple(ijk)] >= 0:
                fontes.append(int(g.ids[tuple(ijk)]))
                rot_fonte.append(k)
    rot = -np.ones(g.n, np.int64)
    # Dijkstra multi-fonte com propagação do rótulo
    import heapq
    dist = [math.inf] * g.n
    rl = [-1] * g.n
    heap = []
    for f, k in zip(fontes, rot_fonte):
        if dist[f] > 0:
            dist[f] = 0.0
            rl[f] = k
            heap.append((0.0, f))
    heapq.heapify(heap)
    dst, w, ptr = g._dst, g._w, g._ptr
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for e in range(ptr[u], ptr[u + 1]):
            v = dst[e]
            nd = d + w[e]
            if nd < dist[v]:
                dist[v] = nd
                rl[v] = rl[u]
                heapq.heappush(heap, (nd, v))
    rot[:] = rl
    # voxels soltos (componentes sem fonte): osso de segmento mais próximo
    soltos = np.nonzero(rot < 0)[0]
    if len(soltos):
        cand = [k for k, o in enumerate(ossos) if o["fim"] is not None and o["nome"] != "body"]
        for v in soltos:
            p = g.pos[v]
            rot[v] = min(cand, key=lambda k: esqueleto._dist_segmento(p, ossos[k]["pivo"], ossos[k]["fim"]))
    return g, rot


# ---------------- referencial do osso ----------------

def eixo_principal(o, P, no_meio=False, alongamento=1.6):
    """Eixo da massa (PCA) se a parte é alongada; senão o eixo do osso. No meio, PCA só em YZ."""
    eixo = o["fim"] - o["pivo"]
    eixo = eixo / (np.linalg.norm(eixo) or 1)
    if len(P) < 20:
        return eixo
    Q = P - P.mean(0)
    if no_meio:
        Q = Q[:, 1:]
    val, vec = np.linalg.eigh(Q.T @ Q / len(Q))
    if val[-1] < alongamento * max(val[-2], 1e-9):
        return eixo
    v = vec[:, -1]
    if no_meio:
        v = np.array([0.0, v[0], v[1]])
    return v if v @ eixo >= 0 else -v


def referencial(o, eixo=None) -> np.ndarray:
    """Colunas = direções no mundo dos eixos locais (eixo do osso, e2, e3), sem torção arbitrária."""
    if eixo is None:
        eixo = o["fim"] - o["pivo"]
    eixo = eixo / (np.linalg.norm(eixo) or 1)
    for ref in (np.array([0.0, 1.0, 0.0]), np.array([0.0, 0.0, 1.0]), np.array([1.0, 0.0, 0.0])):
        if abs(eixo @ ref) < 0.85:
            break
    e2 = ref - (ref @ eixo) * eixo
    e2 /= np.linalg.norm(e2)
    e3 = np.cross(eixo, e2)
    return np.stack([eixo, e2, e3], axis=1)


def referencial_meio(o, eixo=None) -> np.ndarray:
    """Para partes no plano de simetria: o eixo lateral é exatamente X."""
    eixo = (o["fim"] - o["pivo"]) if eixo is None else np.array(eixo, float)
    eixo[0] = 0.0
    if np.linalg.norm(eixo) < 1e-6:
        eixo = np.array([0.0, 1.0, 0.0])
    eixo = eixo / np.linalg.norm(eixo)
    lateral = np.array([1.0, 0.0, 0.0])
    e2 = np.cross(lateral, eixo)
    return np.stack([eixo, e2, lateral], axis=1)



def rasterizar_local(pts_local, cel):
    """Pontos locais -> grade local (com 8 sub-amostras e fechamento)."""
    sub = np.array([(i, j, k) for i in (-0.25, 0.25) for j in (-0.25, 0.25) for k in (-0.25, 0.25)]) * cel
    p = (pts_local[:, None, :] + sub[None]).reshape(-1, 3)
    lo = np.floor(p.min(0) / cel) - 1
    ijk = np.floor(p / cel - lo).astype(int)
    forma = ijk.max(0) + 2
    occ = np.zeros(forma, bool)
    occ[tuple(ijk.T)] = True
    # fechamento 1 célula (tapa furos da rotação)
    d = occ.copy()
    for ax in range(3):
        for s in (1, -1):
            d |= np.roll(occ, s, ax)
    e = d.copy()
    for ax in range(3):
        for s in (1, -1):
            e &= np.roll(d, s, ax)
    return e | occ, lo


# ---------------- caixa -> cubo do Blockbench ----------------

def euler_de(M):
    """Graus (x, y, z) tais que Rz·Ry·Rx = M (convenção de bbmodelo.matriz_rotacao)."""
    y = -math.asin(max(-1.0, min(1.0, M[2, 0])))
    if abs(M[2, 0]) < 0.9999:
        x = math.atan2(M[2, 1], M[2, 2])
        z = math.atan2(M[1, 0], M[0, 0])
    else:
        x = math.atan2(-M[1, 2], M[1, 1])
        z = 0.0
    return np.degrees([x, y, z])


def matriz(graus):
    x, y, z = np.radians(graus)
    rx = np.array([[1, 0, 0], [0, math.cos(x), -math.sin(x)], [0, math.sin(x), math.cos(x)]])
    ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]])
    rz = np.array([[math.cos(z), -math.sin(z), 0], [math.sin(z), math.cos(z), 0], [0, 0, 1]])
    return rz @ ry @ rx


def para_cubo(R, centro_local, tam_local, pivo, passo_angulo=2.5):
    """Caixa no referencial R (colunas) -> (from, to, origin, rotation) com a menor rotação possível."""
    melhor = None
    for perm in itertools.permutations(range(3)):
        for sinais in itertools.product((1, -1), repeat=3):
            M = np.stack([R[:, perm[i]] * sinais[i] for i in range(3)], axis=1)
            if np.linalg.det(M) < 0:
                continue
            tr = np.trace(M)
            if melhor is None or tr > melhor[0]:
                melhor = (tr, M, perm)
    _, M, perm = melhor
    tam = np.array([tam_local[perm[i]] for i in range(3)])
    tam = np.maximum(1, np.round(tam))
    rot = euler_de(M)
    rot = np.round(rot / passo_angulo) * passo_angulo
    rot = np.where(np.abs(rot) < 1e-9, 0.0, rot)
    centro = pivo + R @ centro_local
    return centro - tam / 2, centro + tam / 2, centro, rot


# ---------------- perfil ao longo do eixo ----------------

def perfil(occ, max_trechos, lateral=None, centro_lateral=None, frac_min=0.04, ganho_min=0.3, min_len=4,
           pct=(5, 95)):
    """Divide a parte em trechos ao longo do eixo local 0 onde a seção muda; um cubo por trecho.

    Seção de cada fatia = extensão com percentis 5–95 (ignora tufos). O cubo do trecho usa a
    mediana das seções. Os trechos ficam encostados no eixo: sem caixas cruzadas.
    """
    nx = occ.shape[0]
    cont = occ.reshape(nx, -1).sum(1)
    if cont.max() == 0:
        return []
    validos = np.nonzero(cont >= max(3, frac_min * cont.max()))[0]
    i_ini, i_fim = int(validos[0]), int(validos[-1]) + 1
    ext = np.full((nx, 4), np.nan)
    for i in range(i_ini, i_fim):
        cel = np.argwhere(occ[i])
        if len(cel) < 3:
            continue
        ext[i] = [np.percentile(cel[:, 0], pct[0]), np.percentile(cel[:, 0], pct[1]) + 1,
                  np.percentile(cel[:, 1], pct[0]), np.percentile(cel[:, 1], pct[1]) + 1]
    seg_ext = ext[i_ini:i_fim]
    ok = ~np.isnan(seg_ext[:, 0])
    if not ok.any():
        return []
    for k in range(len(seg_ext)):  # preenche fatias vazias com a vizinha válida mais próxima
        if not ok[k]:
            j = np.nonzero(ok)[0]
            seg_ext[k] = seg_ext[j[np.argmin(np.abs(j - k))]]
    ext[i_ini:i_fim] = seg_ext

    def custo(i0, i1):
        s = ext[i0:i1]
        med = np.median(s, 0)
        return float(np.abs(s - med).sum()), med

    trechos = [(i_ini, i_fim)]
    while len(trechos) < max_trechos:
        melhor = None
        for t, (i0, i1) in enumerate(trechos):
            c0, _ = custo(i0, i1)
            for m in range(i0 + min_len, i1 - min_len + 1):
                red = c0 - (custo(i0, m)[0] + custo(m, i1)[0])
                if melhor is None or red > melhor[0]:
                    melhor = (red, t, m, c0)
        if melhor is None or melhor[0] < ganho_min * melhor[3] or melhor[0] < 0.5 * min_len:
            break
        _, t, m, _ = melhor
        i0, i1 = trechos.pop(t)
        trechos += [(i0, m), (m, i1)]
    caixas = []
    for i0, i1 in sorted(trechos):
        _, med = custo(i0, i1)
        y0, y1, z0, z1 = np.floor(med[0]), np.ceil(med[1]), np.floor(med[2]), np.ceil(med[3])
        lo3, hi3 = np.array([i0, y0, z0], float), np.array([i1, y1, z1], float)
        if lateral is not None:
            c = centro_lateral if centro_lateral is not None else occ.shape[lateral] / 2
            meia = max(c - lo3[lateral], hi3[lateral] - c)
            lo3[lateral], hi3[lateral] = c - meia, c + meia
        caixas.append((lo3, hi3))
    return caixas


# ---------------- cor dentro do volume ----------------

def cores_volume(g, sup_idx, sup_cor):
    """Cor de cada voxel ocupado = cor do voxel de superfície mais próximo (andando por dentro)."""
    from collections import deque

    cor = np.zeros((g.n, 3))
    feito = np.zeros(g.n, bool)
    ids = g.ids[tuple(np.asarray(sup_idx).T)]
    q = deque()
    for n, i in enumerate(ids):
        if i >= 0 and not feito[i]:
            feito[i] = True
            cor[i] = sup_cor[n]
            q.append(int(i))
    dst, ptr = g._dst, g._ptr
    while q:
        u = q.popleft()
        for e in range(ptr[u], ptr[u + 1]):
            v = dst[e]
            if not feito[v]:
                feito[v] = True
                cor[v] = cor[u]
                q.append(v)
    return cor


# ---------------- garras ----------------

def caixa_orientada(P, folga=0.5, pmin=3, pmax=97):
    """Caixa pela PCA dos pontos: (R colunas no mundo, centro no mundo, tamanho)."""
    c = P.mean(0)
    Q = P - c
    _val, V = np.linalg.eigh(Q.T @ Q / max(len(Q), 1))
    V = V[:, ::-1].copy()
    if np.linalg.det(V) < 0:
        V[:, 2] = -V[:, 2]
    proj = Q @ V
    a, b = np.percentile(proj, pmin, axis=0), np.percentile(proj, pmax, axis=0)
    return V, c + V @ ((a + b) / 2), (b - a) + folga




# ---------------- limpeza ----------------

def pontos_do_cubo(c, passo=0.5):
    a, b = np.asarray(c["from"]), np.asarray(c["to"])
    eixos = [np.arange(a[k] + passo / 2, b[k], passo) if b[k] - a[k] > passo else np.array([(a[k] + b[k]) / 2])
             for k in range(3)]
    grade = np.stack(np.meshgrid(*eixos, indexing="ij"), -1).reshape(-1, 3)
    M = matriz(c["rotation"])
    return (grade - c["origin"]) @ M.T + c["origin"]


def limpar(cubos, limite=0.8, protegidos=("claw", "scarf")):
    """Tira cubos que ficam quase inteiros dentro de outros (sobras que só criam frestas)."""
    removidos = []
    while True:
        pior = None
        for c in cubos:
            if c.get("espelho_de") or any(p in c["nome"] for p in protegidos):
                continue
            pts = pontos_do_cubo(c)
            dentro = np.zeros(len(pts), bool)
            for o in cubos:
                # camadas externas (gola, garras) não "engolem" o corpo: só cubos de massa contam
                if o is c or o.get("espelho_de") == c["nome"] or any(p in o["nome"] for p in protegidos):
                    continue
                dentro |= pontos_dentro(o, pts, folga=0.25)
            frac = dentro.mean()
            if frac >= limite and (pior is None or frac > pior[0]):
                pior = (frac, c)
        if pior is None:
            break
        alvo = pior[1]
        cubos = [c for c in cubos if c is not alvo and c.get("espelho_de") != alvo["nome"]]
        removidos.append((alvo["nome"], round(float(pior[0]), 2)))
    return cubos, removidos


# ---------------- tudo junto ----------------

# Anatomia: membros de mamífero têm poucos ossos, então um cubo por osso real (no máximo dois se
# o volume muda muito). Cauda, cabeça e fita são correntes com vários cubos.
MASSA = {"pelvis": 1, "torso": 2}          # tronco: poucos cubos grandes, numa linha de coluna só
TRONCO_TRECHOS = 3
SEM_CUBO = {"waist", "neck_2"}             # ossos só para animar; o volume vai para o vizinho
MEMBROS = {"arm", "forearm", "hand", "leg", "shin"}
PASSO = {"neck": 99.0, "head": 3.5, "tail": 3.5}
SECAO = {"arm": (12, 88), "forearm": (12, 88), "leg": (6, 94), "shin": (8, 92),
         "hand": (8, 92), "foot": (8, 92), "neck": (10, 90), "head": (6, 94), "tail": (4, 96)}
SOBRA_JUNTA = 1.0  # quanto o primeiro cubo entra no pai (esconde a junta ao dobrar)


def familia(nome):
    b = base_nome(nome)
    for chave in ("tail", "neck", "scarf", "appendage"):
        if b.startswith(chave):
            return chave
    return b


def _secao(loc, sel, pct, lateral_simetrico):
    Q = loc[sel, 1:]
    a, b = np.percentile(Q, pct[0], axis=0), np.percentile(Q, pct[1], axis=0)
    if lateral_simetrico:
        m = max(abs(a[1]), abs(b[1]))
        a[1], b[1] = -m, m
    return (a + b) / 2, np.maximum(b - a, 1.0)


def cadeia(P, o, R, terminal, passo, pct, lateral_simetrico=False, inicio=None, cobre_tudo=False,
           adaptativo=False, fim_extra=0.0):
    """Cubos ao longo do osso: começam 1 unidade dentro do pai e terminam na junta seguinte.

    `adaptativo`: 1 cubo, ou 2 se as metades têm seções muito diferentes (membros).
    Devolve [(centro no referencial R, tamanho)].
    """
    L = float(np.linalg.norm(o["fim"] - o["pivo"]))
    loc = (P - o["pivo"]) @ R
    s = loc[:, 0]
    s0 = -SOBRA_JUNTA if inicio is None else inicio
    s1 = max(L, float(np.percentile(s, 98))) if terminal else L + 0.5 + fim_extra
    if cobre_tudo:  # juba/pelo que o osso recebeu fora do trecho entre as juntas
        s0 = min(s0, float(np.percentile(s, 3)))
        s1 = max(s1, float(np.percentile(s, 97)))
    if adaptativo:
        meio = (s0 + s1) / 2
        A = (s >= s0 - 0.5) & (s < meio)
        B = (s >= meio) & (s < s1 + 0.5)
        n = 1
        if A.sum() >= 6 and B.sum() >= 6:
            _, ta = _secao(loc, A, pct, lateral_simetrico)
            _, tb = _secao(loc, B, pct, lateral_simetrico)
            razao = (ta[0] * ta[1]) / (tb[0] * tb[1])
            n = 2 if (razao < 0.4 or razao > 2.5) else 1  # membro: 2 cubos só se o volume muda muito
    else:
        n = int(np.clip(round((s1 - s0) / passo), 1, 5))
    bordas = np.linspace(s0, s1, n + 1)
    saida, ant = [], None
    for i in range(n):
        sel = (s >= bordas[i] - 0.5) & (s < bordas[i + 1] + 0.5)
        if sel.sum() < 6:
            if ant is None:
                continue
            c2, t2 = ant
        else:
            c2, t2 = _secao(loc, sel, pct, lateral_simetrico)
            if ant is not None:
                lim = 0.35 * np.minimum(t2, ant[1])
                c2 = ant[0] + np.clip(c2 - ant[0], -lim, lim)
        comp = bordas[i + 1] - bordas[i] + 0.25
        saida.append((np.array([(bordas[i] + bordas[i + 1]) / 2, c2[0], c2[1]]), np.array([comp, t2[0], t2[1]])))
        ant = (c2, t2)
    return saida


def pe_chato(P, o):
    """Pé como um cubo deitado e apoiado no chão (gira só em torno de Y)."""
    frente = o["fim"] - o["pivo"]
    frente[1] = 0.0
    if np.linalg.norm(frente) < 1e-6:
        frente = np.array([0.0, 0.0, -1.0])
    frente /= np.linalg.norm(frente)
    cima = np.array([0.0, 1.0, 0.0])
    R = np.stack([frente, cima, np.cross(frente, cima)], axis=1)
    loc = (P - o["pivo"]) @ R
    s0, s1 = np.percentile(loc[:, 0], 3), np.percentile(loc[:, 0], 98)
    y0 = max(-o["pivo"][1], np.percentile(loc[:, 1], 3))  # não afunda no chão
    if y0 - (-o["pivo"][1]) < 1.0:
        y0 = -o["pivo"][1]  # encosta no chão
    y1 = float(np.clip(np.percentile(loc[:, 1], 90), y0 + 1.0, y0 + 3.0))  # pé chato (o usuário prefere 2–3)
    z0, z1 = np.percentile(loc[:, 2], 14), np.percentile(loc[:, 2], 86)
    centro = np.array([(s0 + s1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return R, [(centro, np.maximum([s1 - s0, y1 - y0, z1 - z0], 1.0))]


def referencial_pca_perp(o, P):
    """Eixo = osso; e2 = direção mais larga da seção (fita achatada); e3 = espessura."""
    eixo = (o["fim"] - o["pivo"]) / (np.linalg.norm(o["fim"] - o["pivo"]) or 1)
    Q = P - P.mean(0)
    Q = Q - np.outer(Q @ eixo, eixo)
    _val, V = np.linalg.eigh(Q.T @ Q / max(len(Q), 1))
    e2 = V[:, -1] - (V[:, -1] @ eixo) * eixo
    e2 /= np.linalg.norm(e2) or 1
    return np.stack([eixo, e2, np.cross(eixo, e2)], axis=1)


def garras_por_pontas(P, o, n):
    """Garras pelas pontas: separa as pontas (onde as garras já estão afastadas), liga cada uma à
    base comum e põe uma caixa fina da base até a ponta. [(R colunas, centro no mundo, tamanho)]."""
    if len(P) < 12:
        return []
    eixo = (o["fim"] - o["pivo"]) / (np.linalg.norm(o["fim"] - o["pivo"]) or 1)
    s = (P - o["pivo"]) @ eixo
    distal = P[s >= np.percentile(s, 80)]
    base = P[s <= np.percentile(s, 15)].mean(0)
    # plano perpendicular ao osso para separar as pontas
    u = np.cross(eixo, [0.0, 1.0, 0.0])
    if np.linalg.norm(u) < 1e-6:
        u = np.cross(eixo, [1.0, 0.0, 0.0])
    u /= np.linalg.norm(u)
    w = np.cross(eixo, u)
    xy = np.stack([(distal - base) @ u, (distal - base) @ w], 1)
    # k-médias 2D com início pelos pontos mais afastados
    centros = [xy[np.argmax(np.linalg.norm(xy - xy.mean(0), axis=1))]]
    while len(centros) < n:
        d = np.min(np.linalg.norm(xy[:, None] - np.array(centros)[None], axis=2), axis=1)
        centros.append(xy[int(np.argmax(d))])
    centros = np.array(centros, float)
    for _ in range(30):
        grupo = np.argmin(np.linalg.norm(xy[:, None] - centros[None], axis=2), axis=1)
        novos = np.array([xy[grupo == k].mean(0) if (grupo == k).any() else centros[k] for k in range(n)])
        if np.allclose(novos, centros):
            break
        centros = novos
    pontas = [distal[grupo == k].mean(0) for k in range(n) if (grupo == k).any()]
    # cada voxel claro vai para a garra (segmento base→ponta) mais próxima
    dist = np.stack([[esqueleto._dist_segmento(p, base, t) for t in pontas] for p in P])
    dono = np.argmin(dist, axis=1)
    saida = []
    for k, ponta in enumerate(pontas):
        Pk = P[dono == k]
        if len(Pk) < 4:
            continue
        a = ponta - base
        a /= np.linalg.norm(a) or 1
        b = np.cross(a, w)
        b /= np.linalg.norm(b) or 1
        c = np.cross(a, b)
        R = np.stack([a, b, c], axis=1)
        if np.linalg.det(R) < 0:
            R[:, 2] = -R[:, 2]
        loc = (Pk - base) @ R
        a0, a1 = min(np.percentile(loc[:, 0], 2), 0.0) - 0.5, np.percentile(loc[:, 0], 99) + 0.25
        larg = float(np.clip(np.percentile(loc[:, 1], 90) - np.percentile(loc[:, 1], 10), 1.0, 2.0))
        esp = float(np.clip(np.percentile(loc[:, 2], 90) - np.percentile(loc[:, 2], 10), 1.0, 2.0))
        centro_l = np.array([(a0 + a1) / 2, np.median(loc[:, 1]), np.median(loc[:, 2])])
        saida.append((R, base + R @ centro_l, np.array([a1 - a0, larg, esp])))
    return saida


def gola_unica(P_pano, P_pescoco, Rn, pivo, folga=1.5, altura=4.0):
    """Gola como uma peça só, bem mais larga que o pescoço (esquema do Greninja)."""
    lp = (P_pescoco - pivo) @ Rn
    loc = (P_pano - pivo) @ Rn
    a, b = np.percentile(lp, 10, axis=0), np.percentile(lp, 90, axis=0)
    a[1:] -= folga
    b[1:] += folga
    m = max(abs(a[2]), abs(b[2]))  # simétrico em X (eixo local 2)
    a[2], b[2] = -m, m
    s = float(np.median(loc[:, 0]))
    a[0], b[0] = s - altura / 2, s + altura / 2
    return [((a + b) / 2, b - a)]


def ajustar_anatomia(ocupado, origem, voxel, ossos, sup_idx, sup_cor, cel=0.5, n_garras=3):
    """Estilo anatomia (v6): um cubo por osso real nos membros, pé no chão, tronco numa coluna."""
    g, rot = segmentar(ocupado, origem, voxel, ossos)
    cor = cores_volume(g, sup_idx, sup_cor)
    por_nome = {o["nome"]: o for o in ossos}
    idx = {o["nome"]: k for k, o in enumerate(ossos)}
    filhos = {o["pai"] for o in ossos if o["pai"] and o["fim"] is not None and o["nome"] not in SEM_CUBO}
    corpo = [k for k, o in enumerate(ossos) if o["fim"] is not None and o["nome"] != "body"
             and o["nome"] not in SEM_CUBO and familia(o["nome"]) not in ("scarf", "appendage")]

    def mais_proximo(v):
        p = g.pos[v]
        return min(corpo, key=lambda k: esqueleto._dist_segmento(p, ossos[k]["pivo"], ossos[k]["fim"]))

    # fita que "roubou" corcunda/juba e ossos sem cubo devolvem os voxels ao corpo
    pano = np.isin(rot, [k for k, o in enumerate(ossos) if familia(o["nome"]) == "scarf"])
    sem = np.isin(rot, [idx[n] for n in SEM_CUBO if n in idx])
    for v in np.nonzero((pano & ~vermelho(cor)) | sem)[0]:
        rot[v] = mais_proximo(v)
    # o que ficou atrás de uma junta pertence ao pai (ombro/corcunda -> tronco, quadril -> pelve)
    for k in reversed(range(len(ossos))):
        o = ossos[k]
        if o["fim"] is None or o["nome"] in MASSA or o["nome"] in SEM_CUBO \
                or familia(o["nome"]) in ("scarf", "appendage", "head"):
            continue
        pai = o["pai"]
        while pai in SEM_CUBO:
            pai = por_nome[pai]["pai"]
        if pai not in idx or por_nome[pai]["fim"] is None or pai == "body":
            pai = "pelvis" if "pelvis" in idx else None
        if pai is None:
            continue
        eixo = (o["fim"] - o["pivo"]) / (np.linalg.norm(o["fim"] - o["pivo"]) or 1)
        meus = np.nonzero(rot == k)[0]
        rot[meus[(g.pos[meus] - o["pivo"]) @ eixo < -SOBRA_JUNTA]] = idx[pai]
    nos = {o["nome"]: np.nonzero(rot == k)[0] for k, o in enumerate(ossos)}
    cubos = []
    feitos = set()

    def emitir(nome, outro, simetrico, partes, pivo, prefixo=None):
        for n, (Rw, centro, tam) in enumerate(partes):
            frm, to, origin, rotacao = para_cubo(Rw, centro, tam, pivo)
            nome_c = (f"{prefixo}_{n + 1}" if prefixo else (nome if n == 0 else f"{nome}_{n + 1}"))
            cubos.append({"nome": nome_c, "osso": nome, "from": frm, "to": to,
                          "origin": origin, "rotation": rot_limpa(rotacao)})
            if simetrico:
                a, b = espelhar_from(frm, to)
                cubos.append({"nome": nome_c.replace(nome, outro), "osso": outro, "from": a, "to": b,
                              "origin": origin * ESPELHO, "rotation": rot_limpa(rotacao * [1, -1, -1]),
                              "espelho_de": nome_c})

    if all(n in idx for n in ("pelvis", "torso")):
        a_col = por_nome["tail_1"]["pivo"] if "tail_1" in idx else por_nome["pelvis"]["pivo"]
        b_col = por_nome["neck_1"]["pivo"] if "neck_1" in idx else por_nome["torso"]["fim"]
        eixo = (b_col - a_col) * [0.0, 1.0, 1.0]
        tronco = np.concatenate([nos["pelvis"], nos["torso"]])
        P = g.pos[tronco]
        P = np.concatenate([P, P * ESPELHO])
        ref = a_col * [0.0, 1.0, 1.0]
        R = referencial_meio({"pivo": ref, "fim": ref + eixo}, eixo)
        occ, lo = rasterizar_local((P - ref) @ R, cel)
        corte = float((por_nome["waist"]["pivo"] if "waist" in idx else por_nome["torso"]["pivo"]) @ R[:, 0]
                      - ref @ R[:, 0])
        caixas = {"pelvis": [], "torso": []}
        for a, b in perfil(occ, TRONCO_TRECHOS, lateral=2, centro_lateral=-lo[2], ganho_min=0.25,
                           min_len=int(4.0 / cel)):  # trecho de tronco com pelo menos 4 unidades
            lmin, lmax = (a + lo) * cel, (b + lo) * cel
            lmin[0] -= 0.25
            lmax[0] += 0.25
            dono = "pelvis" if (lmin[0] + lmax[0]) / 2 < corte else "torso"
            # centro em relação ao pivô do osso dono (para_cubo devolve posição no mundo)
            centro_w = ref + R @ ((lmin + lmax) / 2)
            caixas[dono].append((R, R.T @ (centro_w - por_nome[dono]["pivo"]), lmax - lmin))
        for dono, partes in caixas.items():
            emitir(dono, None, False, partes, por_nome[dono]["pivo"])
            feitos.add(dono)

    for o in ossos:
        nome = o["nome"]
        if o["fim"] is None or nome == "body" or nome in SEM_CUBO or nome in feitos or len(nos[nome]) == 0:
            continue
        outro = par(nome)
        simetrico = outro in por_nome and np.allclose(por_nome[outro]["pivo"], o["pivo"] * ESPELHO, atol=1e-3)
        no_meio = abs(o["pivo"][0]) < 1e-6 and abs(o["fim"][0]) < 1e-6
        if simetrico and "_right" in nome:
            continue  # o lado esquerdo já cria os dois
        P, C = g.pos[nos[nome]], cor[nos[nome]]
        if simetrico:
            P = np.concatenate([P, g.pos[nos[outro]] * ESPELHO])
            C = np.concatenate([C, cor[nos[outro]]])
        elif no_meio:
            P, C = np.concatenate([P, P * ESPELHO]), np.concatenate([C, C])
        fam = familia(nome)
        claras = cremoso(C) if fam == "hand" else np.zeros(len(P), bool)
        if claras.sum() < 12:
            claras[:] = False
        massa = P[~claras] if (~claras).sum() >= 12 else P
        terminal = nome not in filhos
        partes = []
        if nome in MASSA:
            eixo = eixo_principal(o, massa, no_meio)
            R = referencial_meio(o, eixo) if no_meio else referencial(o, eixo)
            occ, lo = rasterizar_local((massa - o["pivo"]) @ R, cel)
            for a, b in perfil(occ, MASSA[nome], lateral=2 if no_meio else None, centro_lateral=-lo[2],
                               ganho_min=0.35, min_len=4):
                lmin, lmax = (a + lo) * cel, (b + lo) * cel
                lmin[0] -= 0.25
                lmax[0] += 0.25
                partes.append((R, (lmin + lmax) / 2, lmax - lmin))
        elif fam in ("scarf", "appendage"):
            R = referencial_pca_perp(o, massa)
            for centro, tam in cadeia(massa, o, R, terminal, 99.0, (5, 95), inicio=-0.5):
                tam[2] = max(1.0, min(tam[2], 2.0))  # pano é fino
                partes.append((R, centro, tam))
        elif fam == "foot":
            R, cs = pe_chato(massa, o)
            partes = [(R, c, t) for c, t in cs]
        else:
            R = referencial_meio(o) if no_meio else referencial(o)
            inicio = None
            if fam == "head":  # a nuca fica atrás do pivô
                s = ((massa - o["pivo"]) @ R)[:, 0]
                inicio = float(np.clip(np.percentile(s, 3), -6.0, -SOBRA_JUNTA))
            for centro, tam in cadeia(massa, o, R, terminal, PASSO.get(fam, 3.5), SECAO.get(fam, (8, 92)),
                                      lateral_simetrico=no_meio, inicio=inicio, cobre_tudo=(fam == "neck"),
                                      adaptativo=(fam in MEMBROS)):
                if fam == "hand" and claras.any():  # a palma termina onde as garras começam
                    tam[0] = min(tam[0], 4.0)
                    centro[0] = -SOBRA_JUNTA + tam[0] / 2
                partes.append((R, centro, tam))
                if fam == "hand":
                    break
        emitir(nome, outro, simetrico, partes, o["pivo"])
        if claras.any():
            gs = [(Rk, Rk.T @ (cw - o["pivo"]), tam) for Rk, cw, tam in garras_por_pontas(P[claras], o, n_garras)]
            emitir(nome, outro, simetrico, gs, o["pivo"], prefixo=f"{nome}_claw")
        feitos.add(nome)
        if simetrico:
            feitos.add(outro)

    # gola do cachecol: uma peça só, bem mais larga que o pescoço
    if "scarf" in por_nome and "neck_1" in por_nome and "torso" in por_nome:
        torso = por_nome["torso"]
        alvo = np.isin(rot, [idx[n] for n in ("neck_1", "torso") if n in idx])
        sel = alvo & vermelho(cor) & (g.pos[:, 1] >= torso["fim"][1] - 3)
        pesc_nos = nos.get("neck_1", np.array([], int))
        if sel.sum() >= 20 and len(pesc_nos) >= 20:
            pivo = por_nome["scarf"]["pivo"] * [0.0, 1.0, 1.0]  # simetria em torno de x = 0
            Rn = referencial_meio(por_nome["neck_1"])
            P_pano = np.concatenate([g.pos[sel], g.pos[sel] * ESPELHO])
            P_pesc = np.concatenate([g.pos[pesc_nos], g.pos[pesc_nos] * ESPELHO])
            emitir("scarf", None, False, [(Rn, c, t) for c, t in gola_unica(P_pano, P_pesc, Rn, pivo)],
                   pivo, prefixo="scarf_collar")

    cubos, removidos = limpar(cubos)
    return cubos, g, rot, removidos


# ---------------- estilo "equilíbrio" (padrão) ----------------
# Silhueta da v4 com estrutura limpa: o que fica atrás de uma junta vai para o pai (sem cubos
# gigantes atravessando ombro e quadril), membros presos nas juntas, tronco numa linha de coluna,
# cauda em corrente de 5 ossos, garras pelas pontas, pé no chão, gola em volta do pescoço,
# fita do cachecol e juba como planos recortados (textura com transparência).
SEM_CUBO_EQUILIBRIO = {"waist", "neck_2"}  # ossos só para animar; o volume vai para o vizinho
SECAO_EQ = {"arm": (12, 88), "forearm": (10, 90), "leg": (6, 94), "shin": (8, 92), "hand": (8, 92),
            "neck": (6, 94), "tail": (4, 96)}
CADEIA_ATRAS = ("arm", "forearm", "hand", "leg", "shin", "foot", "neck", "tail", "head")


def frame_sem_torcao(direcao, passo_angulo=2.5):
    """Cubo de membro girado só em X e Z (Rz·Rx), com o eixo Y do cubo seguindo o osso.

    Devolve (R com colunas [ao longo do osso, X do cubo, Z do cubo], rotação [x, 0, z] em graus).
    """
    d = np.asarray(direcao, float)
    d /= np.linalg.norm(d) or 1
    alfa = np.degrees(np.arcsin(np.clip(-d[2], -1, 1)))
    gama = np.degrees(np.arctan2(d[0], -d[1]))
    alfa, gama = (np.round(np.array([alfa, gama]) / passo_angulo) * passo_angulo)
    M = matriz([alfa, 0.0, gama])
    R = np.stack([-M[:, 1], M[:, 0], M[:, 2]], axis=1)
    return R, np.array([alfa, 0.0, gama])


def suavizar_degraus(partes, razao=1.4):
    """Degraus seguidos (crânio -> focinho) sem salto brusco: o do meio fica entre os vizinhos e
    nenhum lado muda mais que `razao` de um degrau para o outro (o menor cresce)."""
    if len(partes) < 2:
        return partes
    tams = [np.array(t, float) for _R, _c, t in partes]
    for k in (1, 2):
        for i in range(1, len(tams) - 1):
            lo_, hi_ = sorted((tams[i - 1][k], tams[i + 1][k]))
            tams[i][k] = float(np.clip(tams[i][k], lo_, hi_))
        for i in range(len(tams) - 1):
            a, b = tams[i][k], tams[i + 1][k]
            if max(a, b) > razao * min(a, b):
                if a < b:
                    tams[i][k] = b / razao
                else:
                    tams[i + 1][k] = a / razao
    return [(R, c, t) for (R, c, _t), t in zip(partes, tams)]


def planos_da_fita(cadeia_ossos, P_por_osso, C_por_osso):
    """Fita como planos recortados: um plano por osso, deitado na largura do pano naquele trecho.

    A normal de cada trecho vem da largura do pano (direção mais espalhada perpendicular ao osso);
    as normais vizinhas são suavizadas para os planos continuarem emendados quando a fita torce.
    Devolve [(nome do osso, R colunas [comprimento, largura, normal], centro no mundo,
    tamanho [w, h, 0], pontos-fonte, cores-fonte)].
    """
    trechos = [o for o in cadeia_ossos if len(P_por_osso[o["nome"]]) >= 4]
    if not trechos:
        return []
    eixos, normais = [], []
    for o in trechos:
        P = P_por_osso[o["nome"]]
        a = o["fim"] - o["pivo"]
        a /= np.linalg.norm(a) or 1
        Q = P - P.mean(0)
        Q = Q - np.outer(Q @ a, a)
        _val, V = np.linalg.eigh(Q.T @ Q / len(Q))
        largura = V[:, -1] - (V[:, -1] @ a) * a
        largura /= np.linalg.norm(largura) or 1
        n = np.cross(a, largura)
        if normais and n @ normais[-1] < 0:
            n = -n  # mesmo lado do trecho anterior
        eixos.append(a)
        normais.append(n)
    suaves = []
    for i in range(len(normais)):
        viz = normais[max(0, i - 1): i + 2]
        pes = [1, 2, 1][(0 if i > 0 else 1): (3 if i < len(normais) - 1 else 2)]
        n = sum(w * v for w, v in zip(pes, viz))
        n = n - (n @ eixos[i]) * eixos[i]
        suaves.append(n / (np.linalg.norm(n) or 1))
    saida = []
    for k, (o, a, normal) in enumerate(zip(trechos, eixos, suaves)):
        nome = o["nome"]
        P, C = P_por_osso[nome], C_por_osso[nome]
        e = np.cross(normal, a)
        R = np.stack([a, e, normal], axis=1)
        loc = (P - o["pivo"]) @ R
        # trechos vizinhos se sobrepõem (sem fresta ao dobrar); o primeiro entra na gola
        s0 = min(-0.5, np.percentile(loc[:, 0], 1)) - (1.5 if k == 0 else 0.75)
        s1 = np.percentile(loc[:, 0], 99) + 0.75
        t0, t1 = np.percentile(loc[:, 1], 1) - 0.5, np.percentile(loc[:, 1], 99) + 0.5
        w, h = float(np.ceil(s1 - s0)), float(np.ceil(t1 - t0))
        centro = o["pivo"] + R @ np.array([(s0 + s1) / 2, (t0 + t1) / 2, float(np.median(loc[:, 2]))])
        saida.append((nome, R, centro, np.array([w, h, 0.0]), P, C))
    return saida


def cubo_plano(nome, osso, R, centro, tam, fonte_pos, fonte_cor, passo_angulo=2.5):
    """Cubo de espessura zero com a rotação exata de R (sem permutar eixos: a normal fica em Z)."""
    rot = np.round(euler_de(R) / passo_angulo) * passo_angulo
    return {"nome": nome, "osso": osso, "from": centro - tam / 2, "to": centro + tam / 2, "origin": centro,
            "rotation": rot_limpa(rot), "plano": True, "fonte_pos": fonte_pos, "fonte_cor": fonte_cor}


def gola_em_volta(pesc, osso_pescoco, P_pano, folga=1.0, altura=3.0):
    """Gola: mesma rotação do cubo do pescoço, 1,5 maior de cada lado, na altura do pano vinho."""
    M = matriz(pesc["rotation"])
    tam = np.asarray(pesc["to"]) - np.asarray(pesc["from"])
    centro = np.asarray(pesc["origin"])
    d = osso_pescoco["fim"] - osso_pescoco["pivo"]
    k = int(np.argmax(np.abs(M.T @ d)))  # eixo do cubo que segue o pescoço
    eixo = M[:, k] * np.sign(M[:, k] @ d)
    s = float(np.median((P_pano - centro) @ eixo)) if len(P_pano) else -tam[k] / 2 + altura / 2
    s = float(np.clip(s, -tam[k] / 2 + altura / 2, tam[k] / 2 - altura / 2))
    novo = tam + 2 * folga
    novo[k] = altura
    c = centro + eixo * s
    return {"nome": "scarf_collar_1", "osso": "scarf", "from": c - novo / 2, "to": c + novo / 2, "origin": c,
            "rotation": np.asarray(pesc["rotation"], float), "so_vermelho": True}


def planos_de_pelo(cubos, g, rot, cor, ossos, nomes, faixa=2.5, area_min=6.0):
    """Juba/tufos: o que a malha tem no meio do corpo (|x| <= faixa) e os cubos não cobrem vira um
    plano em x = 0 por osso, recortado na forma dos tufos (perfil lateral)."""
    solidos = [c for c in cubos if not c.get("plano")]
    no_meio = np.abs(g.pos[:, 0]) <= faixa
    cand = np.nonzero(no_meio)[0]
    coberto = np.zeros(len(cand), bool)
    for c in solidos:
        coberto |= pontos_dentro(c, g.pos[cand], folga=0.25)
    falta = cand[~coberto]
    saida = []
    idx = {o["nome"]: k for k, o in enumerate(ossos)}
    for nome in nomes:
        if nome not in idx:
            continue
        meus = falta[rot[falta] == idx[nome]]
        if len(meus) == 0:
            continue
        P = g.pos[meus]
        # área no perfil (células de 0,5 no plano YZ)
        cel = np.unique(np.floor(P[:, 1:] / 0.5).astype(int), axis=0)
        if len(cel) * 0.25 < area_min:
            continue
        y0, y1 = P[:, 1].min() - 0.25, P[:, 1].max() + 0.25
        z0, z1 = P[:, 2].min() - 0.25, P[:, 2].max() + 0.25
        h, d = float(np.ceil(y1 - y0)), float(np.ceil(z1 - z0))
        centro = np.array([0.0, (y0 + y1) / 2, (z0 + z1) / 2])
        tam = np.array([0.0, h, d])
        fc = cor[meus].copy()
        estranho = vermelho(fc) | dourado(fc)  # pano do cachecol e broche caídos sobre o pelo
        if estranho.any() and (~estranho).any():
            bom = np.nonzero(~estranho)[0]
            for i in np.nonzero(estranho)[0]:
                fc[i] = fc[bom[np.argmin(((P[bom] - P[i]) ** 2).sum(1))]]
        saida.append({"nome": f"{nome}_fur", "osso": nome, "from": centro - tam / 2, "to": centro + tam / 2,
                      "origin": centro, "rotation": np.zeros(3), "plano": True,
                      "fonte_pos": P * [0.0, 1.0, 1.0], "fonte_cor": fc})
    return saida


def ajustar(ocupado, origem, voxel, ossos, sup_idx, sup_cor, cel=0.5, n_garras=3, pelo=True):
    """Estilo equilíbrio. Devolve cubos, grade, rótulos e relatório de limpeza."""
    g, rot = segmentar(ocupado, origem, voxel, ossos)
    cor = cores_volume(g, sup_idx, sup_cor)
    por_nome = {o["nome"]: o for o in ossos}
    idx = {o["nome"]: k for k, o in enumerate(ossos)}
    corpo = [k for k, o in enumerate(ossos) if o["fim"] is not None and o["nome"] != "body"
             and o["nome"] not in SEM_CUBO_EQUILIBRIO and familia(o["nome"]) not in ("scarf", "appendage")]

    def mais_proximo(v):
        p = g.pos[v]
        return min(corpo, key=lambda k: esqueleto._dist_segmento(p, ossos[k]["pivo"], ossos[k]["fim"]))

    # 1. a fita só fica com o pano vinho; ossos sem cubo devolvem o volume ao vizinho
    pano = np.isin(rot, [k for k, o in enumerate(ossos) if familia(o["nome"]) == "scarf"])
    sem = np.isin(rot, [idx[n] for n in SEM_CUBO_EQUILIBRIO if n in idx])
    for v in np.nonzero((pano & ~vermelho(cor)) | sem)[0]:
        rot[v] = mais_proximo(v)
    # 2. o que ficou atrás de uma junta pertence ao pai (ombro/corcunda -> tronco, quadril -> pelve)
    for k in reversed(range(len(ossos))):
        o = ossos[k]
        if o["fim"] is None or familia(o["nome"]) not in CADEIA_ATRAS:
            continue
        pai = o["pai"]
        while pai in SEM_CUBO_EQUILIBRIO:
            pai = por_nome[pai]["pai"]
        if pai not in idx or por_nome[pai]["fim"] is None or pai == "body":
            pai = "pelvis" if "pelvis" in idx else None
        if pai is None:
            continue
        eixo = (o["fim"] - o["pivo"]) / (np.linalg.norm(o["fim"] - o["pivo"]) or 1)
        meus = np.nonzero(rot == k)[0]
        rot[meus[(g.pos[meus] - o["pivo"]) @ eixo < -SOBRA_JUNTA]] = idx[pai]
    filhos = {o["pai"] for o in ossos if o["pai"] and o["fim"] is not None and o["nome"] not in SEM_CUBO_EQUILIBRIO}
    nos = {o["nome"]: np.nonzero(rot == k)[0] for k, o in enumerate(ossos)}
    cubos = []
    feitos = set()

    def emitir(nome, outro, simetrico, partes, pivo, prefixo=None):
        for n, parte in enumerate(partes):
            Rw, centro, tam = parte[:3]
            if len(parte) == 4:  # membro: rotação fixa sem torção; tam = [osso, X, Z]
                origin = pivo + Rw @ centro
                lados = np.maximum(1, np.round(np.array([tam[1], tam[0], tam[2]])))
                frm, to, rotacao = origin - lados / 2, origin + lados / 2, parte[3]
            else:
                frm, to, origin, rotacao = para_cubo(Rw, centro, tam, pivo)
            nome_c = (f"{prefixo}_{n + 1}" if prefixo else (nome if n == 0 else f"{nome}_{n + 1}"))
            cubos.append({"nome": nome_c, "osso": nome, "from": frm, "to": to,
                          "origin": origin, "rotation": rot_limpa(rotacao)})
            if simetrico:
                a, b = espelhar_from(frm, to)
                cubos.append({"nome": nome_c.replace(nome, outro), "osso": outro, "from": a, "to": b,
                              "origin": origin * ESPELHO, "rotation": rot_limpa(rotacao * [1, -1, -1]),
                              "espelho_de": nome_c})

    # 3. tronco inteiro numa linha de coluna (base da cauda -> base do pescoço)
    if all(n in idx for n in ("pelvis", "torso")):
        a_col = por_nome["tail_1"]["pivo"] if "tail_1" in idx else por_nome["pelvis"]["pivo"]
        b_col = por_nome["neck_1"]["pivo"] if "neck_1" in idx else por_nome["torso"]["fim"]
        eixo = (b_col - a_col) * [0.0, 1.0, 1.0]
        tronco = np.concatenate([nos["pelvis"], nos["torso"]])
        P = np.concatenate([g.pos[tronco], g.pos[tronco] * ESPELHO])
        ref = a_col * [0.0, 1.0, 1.0]
        R = referencial_meio({"pivo": ref, "fim": ref + eixo}, eixo)
        occ, lo = rasterizar_local((P - ref) @ R, cel)
        corte = float((por_nome["waist"]["pivo"] if "waist" in idx else por_nome["torso"]["pivo"]) @ R[:, 0]
                      - ref @ R[:, 0])
        caixas = {"pelvis": [], "torso": []}
        for a, b in perfil(occ, 2, lateral=2, centro_lateral=-lo[2], ganho_min=0.25, min_len=int(4.0 / cel),
                           pct=(7, 93)):  # pelve + peito; sem estufar os cantos (ombro arredondado na malha)
            lmin, lmax = (a + lo) * cel, (b + lo) * cel
            lmin[0] -= 0.25
            lmax[0] += 0.25
            dono = "pelvis" if (lmin[0] + lmax[0]) / 2 < corte else "torso"
            centro_w = ref + R @ ((lmin + lmax) / 2)
            caixas[dono].append((R, R.T @ (centro_w - por_nome[dono]["pivo"]), lmax - lmin))
        for dono, partes in caixas.items():
            emitir(dono, None, False, partes, por_nome[dono]["pivo"])
            feitos.add(dono)

    # 4. demais partes
    fita, cauda = [], []
    for o in ossos:
        nome = o["nome"]
        if o["fim"] is None or nome == "body" or nome in SEM_CUBO_EQUILIBRIO or nome in feitos \
                or len(nos[nome]) == 0:
            continue
        fam = familia(nome)
        if fam in ("scarf", "appendage"):
            fita.append(o)
            continue
        outro = par(nome)
        simetrico = outro in por_nome and np.allclose(por_nome[outro]["pivo"], o["pivo"] * ESPELHO, atol=1e-3)
        no_meio = abs(o["pivo"][0]) < 1e-6 and abs(o["fim"][0]) < 1e-6
        if simetrico and "_right" in nome:
            continue  # o lado esquerdo já cria os dois
        P, C = g.pos[nos[nome]], cor[nos[nome]]
        if simetrico:
            P = np.concatenate([P, g.pos[nos[outro]] * ESPELHO])
            C = np.concatenate([C, cor[nos[outro]]])
        elif no_meio:
            P, C = np.concatenate([P, P * ESPELHO]), np.concatenate([C, C])
        claras = cremoso(C) if fam == "hand" else np.zeros(len(P), bool)
        if claras.sum() < 12:
            claras[:] = False
        massa = P[~claras] if (~claras).sum() >= 12 else P
        terminal = nome not in filhos
        partes = []
        if fam == "head":  # crânio -> focinho em degraus, no eixo do osso
            R = referencial_meio(o) if no_meio else referencial(o)
            occ, lo = rasterizar_local((massa - o["pivo"]) @ R, cel)
            for a, b in perfil(occ, 3, lateral=2 if no_meio else None, centro_lateral=-lo[2],
                               min_len=int(3.0 / cel)):
                lmin, lmax = (a + lo) * cel, (b + lo) * cel
                lmin[0] -= 0.25
                lmax[0] += 0.25
                partes.append((R, (lmin + lmax) / 2, lmax - lmin))
            partes = suavizar_degraus(partes)
        elif fam == "foot":
            R, cs = pe_chato(massa, o)
            partes = [(R, c, t) for c, t in cs]
        else:
            R = referencial_meio(o) if no_meio else referencial(o)
            L = float(np.linalg.norm(o["fim"] - o["pivo"]))
            passo = (L + 3.0) / 2 if nome == "tail_1" else 99.0  # tail_1: ligação com a pelve + corpo
            inicio = -2.5 if nome == "tail_1" else None  # a base da cauda entra na pelve (sem fresta)
            rot_fixa = None
            if fam in ("arm", "forearm", "leg", "shin", "hand"):  # um osso real = um cubo, sem torção
                R, rot_fixa = frame_sem_torcao(o["fim"] - o["pivo"])
            extra = 0.0
            if fam == "shin":  # a canela desce até o topo do pé chato (sem fresta no tornozelo)
                extra = max(0.0, float(o["fim"][1]) - 3.0)
            for centro, tam in cadeia(massa, o, R, terminal, passo, SECAO_EQ.get(fam, (8, 92)),
                                      lateral_simetrico=no_meio, cobre_tudo=(fam == "neck"), inicio=inicio,
                                      fim_extra=extra):
                if fam == "hand" and claras.any():  # a palma termina onde as garras começam
                    tam[0] = min(tam[0], 4.0)
                    centro[0] = -SOBRA_JUNTA + tam[0] / 2
                partes.append((R, centro, tam) if rot_fixa is None else (R, centro, tam, rot_fixa))
                if fam == "hand":
                    break
        if fam == "tail":
            cauda.append((nome, o, partes))
            feitos.add(nome)
            continue
        emitir(nome, outro, simetrico, partes, o["pivo"])
        if claras.any():
            gs = [(Rk, Rk.T @ (cw - o["pivo"]), tam) for Rk, cw, tam in garras_por_pontas(P[claras], o, n_garras)]
            emitir(nome, outro, simetrico, gs, o["pivo"], prefixo=f"{nome}_claw")
        feitos.add(nome)
        if simetrico:
            feitos.add(outro)

    # cauda: seções suavizadas ao longo de toda a corrente (afina sem degrau brusco)
    if cauda:
        seq = [tam for _n, _o, partes in cauda for _R, _c, tam in partes]
        bruto = np.array([t[1:].copy() for t in seq])
        for i, t in enumerate(seq):
            viz = bruto[max(0, i - 1): i + 2]
            pesos = np.array([0.25, 0.5, 0.25])[(0 if i > 0 else 1): (3 if i < len(seq) - 1 else 2)]
            t[1:] = np.maximum(1.0, (viz * pesos[:, None]).sum(0) / pesos.sum())
        for nome, o, partes in cauda:
            emitir(nome, None, False, partes, o["pivo"])

    # 5. fita do cachecol: planos recortados (forma de chama da malha)
    if fita:
        P_osso = {o["nome"]: g.pos[nos[o["nome"]]] for o in fita}
        C_osso = {o["nome"]: cor[nos[o["nome"]]] for o in fita}
        for nome, R, centro, tam, P, C in planos_da_fita(fita, P_osso, C_osso):
            cubos.append(cubo_plano(nome, nome, R, centro, tam, P, C))

    # 6. gola: em volta do cubo do pescoço
    pesc = next((c for c in cubos if c["osso"] == "neck_1"), None)
    if "scarf" in por_nome and pesc is not None:
        perto = np.isin(rot, [idx[n] for n in ("neck_1", "torso") if n in idx]) & vermelho(cor)
        cubos.append(gola_em_volta(pesc, por_nome["neck_1"], g.pos[perto]))

    cubos, removidos = limpar(cubos, protegidos=("claw", "scarf", "tail"))
    # 7. juba e tufos do meio do corpo como planos (o que a malha tem e os cubos não cobrem)
    if pelo:
        meio = [o["nome"] for o in ossos if o["fim"] is not None and abs(o["pivo"][0]) < 1.5
                and familia(o["nome"]) in ("head", "neck", "torso", "pelvis", "tail")]
        cubos += planos_de_pelo(cubos, g, rot, cor, ossos, meio)
    return cubos, g, rot, removidos

def rot_limpa(r):
    r = np.asarray(r, float)
    r = (r + 180) % 360 - 180
    return np.where(np.abs(r) < 1e-9, 0.0, r)


def espelhar_from(frm, to):
    a, b = frm * ESPELHO, to * ESPELHO
    return np.minimum(a, b), np.maximum(a, b)


def pontos_dentro(cubo, pts, folga=0.0):
    """Máscara dos pontos dentro do cubo girado."""
    M = matriz(cubo["rotation"])
    loc = (pts - cubo["origin"]) @ M + cubo["origin"]  # desfaz a rotação em torno da origem
    return np.all((loc >= cubo["from"] - folga) & (loc <= cubo["to"] + folga), axis=1)
