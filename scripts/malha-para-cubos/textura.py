"""Textura projetada: cada pixel de cada face puxa a cor da malha original (voxel de superfície mais
próximo), reduzida a uma paleta curta (visual de pixel art). Planos recebem recorte por transparência
na forma dos pontos-fonte (fita do cachecol, juba).

Serve para conferir a conversão contra a referência; a pintura final continua sendo do pipeline.
"""

from __future__ import annotations

import numpy as np
from PIL import Image

from criaturas import bbmodelo, render


def mapa_superficie(forma, sup_idx, iteracoes=60):
    """Grade inteira -> índice do voxel de superfície mais próximo (propagação por vizinhança 6)."""
    mapa = -np.ones(forma, np.int32)
    mapa[tuple(np.asarray(sup_idx).T)] = np.arange(len(sup_idx), dtype=np.int32)
    for _ in range(iteracoes):
        mudou = False
        for ax in range(3):
            for s in (1, -1):
                desl = np.roll(mapa, s, ax)
                borda = [slice(None)] * 3
                borda[ax] = 0 if s == 1 else -1
                desl[tuple(borda)] = -1  # sem dar a volta na grade
                f = (mapa < 0) & (desl >= 0)
                if f.any():
                    mapa[f] = desl[f]
                    mudou = True
        if not mudou:
            break
    return mapa


def paleta(cores, k=16, iteracoes=20, semente=0):
    """k-médias simples nas cores de superfície."""
    rng = np.random.default_rng(semente)
    c = np.asarray(cores, float)
    amostra = c[rng.choice(len(c), min(len(c), 6000), replace=False)]
    centros = amostra[rng.choice(len(amostra), k, replace=False)]
    for _ in range(iteracoes):
        grupo = np.argmin(((amostra[:, None] - centros[None]) ** 2).sum(-1), axis=1)
        novos = np.array([amostra[grupo == i].mean(0) if (grupo == i).any() else centros[i] for i in range(k)])
        if np.allclose(novos, centros, atol=0.5):
            break
        centros = novos
    return centros


def paleta_com_destaques(cores, k=16, extras=4, distancia=55.0):
    """Paleta principal + cores de destaque raras que a média engoliria (broche dourado, olho âmbar)."""
    pal = paleta(cores, k)
    c = np.asarray(cores, float)
    d = np.sqrt(((c[:, None] - pal[None]) ** 2).sum(-1)).min(1)
    raras = c[d > distancia]
    if len(raras) >= 12:
        pal = np.concatenate([pal, paleta(raras, min(extras, max(1, len(raras) // 12)))])
    return pal


def quantizar(c, pal):
    c = np.asarray(c, float)
    return pal[indices(c, pal)]


def indices(c, pal):
    return np.argmin(((np.asarray(c, float)[..., None, :] - pal) ** 2).sum(-1), axis=-1)


def _vizinhos(a, borda):
    """As 9 versões deslocadas (3×3) de uma grade 2D, com a borda repetida."""
    p = np.pad(a, 1, mode="edge") if borda == "edge" else np.pad(a, 1, constant_values=borda)
    h, w = a.shape
    return [p[1 + dy:1 + dy + h, 1 + dx:1 + dx + w] for dy in (-1, 0, 1) for dx in (-1, 0, 1)]


def moda(pid, opaco, k):
    """Filtro de maioria 3×3 nos índices de paleta: tira os pontinhos soltos da textura da IA."""
    contagem = np.zeros(pid.shape + (k,), np.int16)
    for v, o in zip(_vizinhos(pid, "edge"), _vizinhos(opaco, False)):
        contagem[np.arange(pid.shape[0])[:, None], np.arange(pid.shape[1])[None], v] += o
    melhor = contagem.argmax(-1)
    forte = contagem.max(-1) >= 4  # só troca se a vizinhança concorda
    return np.where(forte & opaco, melhor, pid)


def limpar_recorte(opaco):
    """Fecha furinhos e tira pixels soltos do recorte dos planos."""
    fechado = np.logical_or.reduce(_vizinhos(opaco, False)) & (np.sum(_vizinhos(opaco, False), 0) >= 5) | opaco
    return np.sum(_vizinhos(fechado, False), 0) >= 4


def pano_por_matiz(cores):
    """Pano vinho pelo matiz (vermelho-magenta, inclusive as partes desbotadas/rosadas); o marrom do
    pelo tem matiz alaranjado (12–30°) e fica de fora."""
    c = np.asarray(cores, float) / 255.0
    mx, mn = c.max(-1), c.min(-1)
    d = np.maximum(mx - mn, 1e-6)
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    sat = (mx - mn) / np.maximum(mx, 1e-6)
    return ((h >= 335) | (h <= 7)) & (sat > 0.3) & (mx > 0.25)


def _borda(opaco):
    """Pixels opacos que encostam num transparente (contorno do recorte)."""
    return opaco & ~np.logical_and.reduce(_vizinhos(opaco, False))


def _anel(forma, largura=1):
    """Moldura de `largura` pixels na borda de uma face."""
    a = np.zeros(forma, bool)
    a[:largura, :] = a[-largura:, :] = a[:, :largura] = a[:, -largura:] = True
    return a


def _sub_paleta(pid, opaco, pal, quantas=4):
    """Rosto limpo: só as `quantas` cores mais usadas na face (+ a mais escura, para olho e nariz)."""
    cont = np.bincount(pid[opaco].ravel(), minlength=len(pal))
    manter = list(np.argsort(-cont)[:quantas])
    presentes = [k for k in range(len(pal)) if cont[k] >= 2]
    if presentes:
        escura = min(presentes, key=lambda k: pal[k].sum())
        if escura not in manter:
            manter.append(escura)
    manter = np.array(manter)
    d = ((pal[:, None, :] - pal[manter][None]) ** 2).sum(-1)
    destino = manter[np.argmin(d, axis=1)]
    return destino[pid]


def rosto_da_malha(sup_pos, sup_cor, caixa_lo, caixa_hi):
    """Tons do rosto (creme da máscara, pelo, escuro) e posição dos olhos (pupilas pretas), da malha."""
    dentro = np.all((sup_pos >= caixa_lo) & (sup_pos <= caixa_hi), axis=1)
    P, C = sup_pos[dentro], sup_cor[dentro]
    if len(P) < 20:
        return None
    lum = C.mean(1)
    creme_m = (lum > 150) & (C[:, 2] > 80)
    escuro_m = lum < 70
    pelo_m = ~creme_m & ~escuro_m
    tons = [np.median(C[m], 0) if m.sum() >= 3 else d for m, d in
            ((creme_m, np.array([235.0, 200, 150])), (pelo_m, np.median(C, 0)), (escuro_m, np.array([60.0, 30, 20])))]
    olhos = []
    preto = P[lum < 45]
    esquerda = preto[preto[:, 0] < -0.5]
    if len(esquerda) >= 2:
        e = esquerda.mean(0)
        olhos = [e, e * [-1.0, 1.0, 1.0]]
    ambar = C[(C[:, 0] > 150) & (C[:, 1] > 90) & (C[:, 2] < 80)]
    iris = np.median(ambar, 0) if len(ambar) >= 3 else np.array([215.0, 140, 50])
    frente = P[P[:, 2] <= P[:, 2].min() + 1.0]  # ponta do focinho (frente = -Z)
    nariz = frente.mean(0) if len(frente) else None
    if nariz is not None:
        nariz[0] = 0.0
    return {"tons": np.array(tons), "olhos": olhos, "iris": iris, "pupila": np.array([25.0, 12, 8]), "nariz": nariz}


def pintar(arquivo, info, fator, origem, voxel, mapa, sup_cor, pal, raio_plano=0.65, sup_pos=None, filtro_pano=None,
           mapa_corpo=None, cores_corpo=None, rosto=None, ocupado=None):
    """Imagem RGBA (resolução UV × fator) pintada a partir da malha, lendo as UVs do .bbmodel.

    - Cubos movidos por ajustes do usuário buscam a cor onde estavam na malha (c["inv"]).
    - `mapa_corpo`/`cores_corpo`: superfície sem pano e sem metal, usada nos cubos que não são do
      cachecol (o vinho caído no ombro ou da tanga na coxa vira mancha num cubo de pelo).
    - Cubos do meio do corpo são simétricos (cada pixel = média com o espelho em X).
    - Rosto: paleta curta por face e filtro de maioria extra (sem manchas soltas).
    - Cachecol: vinho chapado com contorno escuro (fita) ou moldura escura (gola).
    """
    modelo = bbmodelo.ler(arquivo)
    mats = bbmodelo.matrizes_ossos(modelo)
    res_u, res_v = modelo.resolucao
    img = np.zeros((res_v * fator, res_u * fator, 4), np.uint8)
    forma = np.array(mapa.shape)
    mediana = np.median(sup_cor, 0)
    if filtro_pano is not None and filtro_pano.any():
        vinho = np.median(sup_cor[filtro_pano], 0)
    else:
        vinho = np.array([120.0, 30.0, 36.0])
    vinho_escuro = vinho * 0.6

    def amostrar(W, usar_corpo, normal=None):
        """Cor da malha para cada ponto W. Com `normal`, projeta ao longo dela (como um bake):
        o raio sai 3 unidades para fora da face e pega a primeira superfície da malha; sem acerto,
        usa o voxel de superfície mais próximo."""
        alvo = W
        if normal is not None and ocupado is not None:
            passos = np.arange(0.0, 9.01, 0.25)
            amostras = (W + 3.0 * normal)[:, None, :] - passos[None, :, None] * normal  # (n, k, 3)
            ijk_r = np.floor((amostras - origem) / voxel).astype(int)
            ok = np.all((ijk_r >= 0) & (ijk_r < forma), axis=2)
            cheio = np.zeros(ok.shape, bool)
            cheio[ok] = ocupado[tuple(ijk_r[ok].T)]
            acertou = cheio.any(1)
            primeiro = np.argmax(cheio, axis=1)
            alvo = np.where(acertou[:, None], amostras[np.arange(len(W)), primeiro], W)
        ijk = np.clip(np.floor((alvo - origem) / voxel).astype(int), 0, forma - 1)
        if usar_corpo and mapa_corpo is not None:
            ids, base = mapa_corpo[tuple(ijk.T)], cores_corpo
        else:
            ids, base = mapa[tuple(ijk.T)], sup_cor
        return np.where(ids[:, None] >= 0, base[np.maximum(ids, 0)], mediana)

    for cubo in modelo.cubos:
        dados = info.get(cubo.nome, {})
        if dados.get("espelho_de"):
            continue  # o espelhado usa a mesma ilha (mirror_uv)
        M = bbmodelo.matriz_cubo(modelo, cubo, mats)
        lim = np.stack([cubo.de - cubo.inflate, cubo.ate + cubo.inflate])
        A, b = dados.get("inv", (np.eye(3), np.zeros(3)))
        pano = "scarf" in cubo.nome
        cabeca = cubo.osso == "head" and not dados.get("plano")
        centro_orig = A @ ((cubo.de + cubo.ate) / 2) + b
        no_meio = abs(centro_orig[0]) < 0.6 and not pano and not dados.get("plano")
        for face, cantos in render.CANTOS_FACE.items():
            uvf = cubo.faces.get(face, {}).get("uv")
            if not uvf:
                continue
            u1, v1, u2, v2 = uvf
            if abs(u2 - u1) < 1e-6 or abs(v2 - v1) < 1e-6:
                continue
            TL, TR, BL, _BR = (np.array([lim[i, 0], lim[j, 1], lim[k, 2]]) for i, j, k in cantos)
            px0, px1 = int(round(min(u1, u2) * fator)), int(round(max(u1, u2) * fator))
            py0, py1 = int(round(min(v1, v2) * fator)), int(round(max(v1, v2) * fator))
            if px1 <= px0 or py1 <= py0:
                continue
            S = ((np.arange(px0, px1) + 0.5) / fator - u1) / (u2 - u1)
            T = ((np.arange(py0, py1) + 0.5) / fator - v1) / (v2 - v1)
            SS, TT = np.meshgrid(S, T)
            local = TL + SS[..., None] * (TR - TL) + TT[..., None] * (BL - TL)
            W = bbmodelo.aplicar(M, local.reshape(-1, 3))
            Ws = W @ A.T + b  # onde esse pixel estava na malha
            n_face = M[:3, :3] @ np.array(render.NORMAIS[face], float)
            n_face = A @ (n_face / (np.linalg.norm(n_face) or 1))  # normal na pose da malha
            forma_f = (py1 - py0, px1 - px0)
            if dados.get("plano"):
                fonte, fc = dados["fonte_pos"], dados["fonte_cor"]
                perto = np.empty(len(W), int)
                dist = np.empty(len(W))
                for i in range(0, len(W), 2048):
                    d2 = ((W[i:i + 2048, None, :] - fonte[None]) ** 2).sum(-1)
                    perto[i:i + 2048] = np.argmin(d2, 1)
                    dist[i:i + 2048] = np.sqrt(d2[np.arange(len(d2)), perto[i:i + 2048]])
                opaco = limpar_recorte((dist < raio_plano).reshape(forma_f))
                if pano:  # fita: vinho chapado com contorno escuro
                    rgb = np.empty(forma_f + (3,))
                    rgb[:] = vinho
                    rgb[_borda(opaco)] = vinho_escuro
                else:
                    pid = moda(moda(indices(fc[perto], pal).reshape(forma_f), opaco, len(pal)), opaco, len(pal))
                    rgb = pal[pid]
            elif dados.get("so_vermelho"):  # gola: vinho chapado com moldura escura
                opaco = np.ones(forma_f, bool)
                rgb = np.empty(forma_f + (3,))
                rgb[:] = vinho
                rgb[_anel(forma_f, max(1, fator // 2))] = vinho_escuro
            else:
                cor = amostrar(Ws, usar_corpo=not pano, normal=n_face)
                if no_meio:  # simétrico: média com o espelho
                    cor = (cor + amostrar(Ws * [-1.0, 1.0, 1.0], usar_corpo=not pano,
                                          normal=n_face * [-1.0, 1.0, 1.0])) / 2
                capa = None
                if cubo.osso in ("torso", "neck_1", "arm_left", "arm_right") and mapa_corpo is not None:
                    bruto = amostrar(Ws, usar_corpo=False, normal=n_face)
                    capa = pano_por_matiz(bruto).reshape(forma_f)
                    if no_meio:
                        espelho = amostrar(Ws * [-1.0, 1.0, 1.0], usar_corpo=False, normal=n_face * [-1.0, 1.0, 1.0])
                        capa |= pano_por_matiz(espelho).reshape(forma_f)
                    for _ in range(2):
                        capa = moda(capa.astype(int), np.ones(forma_f, bool), 2).astype(bool)
                opaco = np.ones(forma_f, bool)
                if cabeca and rosto is not None:
                    # rosto em 3 tons limpos (creme da máscara, pelo, escuro) + olhos desenhados
                    tons = rosto["tons"]
                    tom = np.argmin(((cor[:, None, :] - tons[None]) ** 2).sum(-1), axis=1).reshape(forma_f)
                    for _ in range(3):
                        tom = moda(tom, opaco, 3)
                    rgb = tons[tom].astype(float)
                    nf = n_face / (np.linalg.norm(n_face) or 1)
                    for E in rosto["olhos"]:
                        rel = W - E
                        prof = rel @ nf  # distância do olho ao plano desta face
                        if np.median(np.abs(prof)) > 1.5 or nf @ (E - centro_orig) < 0:
                            continue  # o olho fica em outra face
                        no_plano = rel - np.outer(prof, nf)
                        d = no_plano * [1.0, 1.7, 1.0]  # olho estreito (expressão brava da arte)
                        r = np.sqrt((d ** 2).sum(1)).reshape(forma_f)
                        acima = (W[:, 1] > E[1]).reshape(forma_f)
                        rgb[(r < 1.6) & acima] = tons[2]           # contorno/sobrancelha escura
                        rgb[r < 1.2] = rosto["iris"]
                        rgb[r < 0.6] = rosto["pupila"]
                    N = rosto.get("nariz")
                    if N is not None and nf[2] < -0.7:  # face da frente perto da ponta do focinho
                        prof_n = (W - N) @ nf
                        if np.median(np.abs(prof_n)) < 1.6:
                            rgb[:] = tons[0]  # ponta do focinho creme (o queixo escuro não vaza)
                            no_plano = (W - N) - np.outer(prof_n, nf)
                            topo = W[:, 1].max()
                            centro_n = np.array([0.0, min(N[1] + 0.3, topo - 0.9), 0.0])
                            dx = no_plano[:, 0] / 1.5
                            dy = (W[:, 1] - centro_n[1]) / 0.95
                            rgb[(np.sqrt(dx ** 2 + dy ** 2) < 1.0).reshape(forma_f)] = tons[2] * 0.75  # nariz
                else:
                    pid = indices(cor, pal).reshape(forma_f)
                    pid = moda(moda(pid, opaco, len(pal)), opaco, len(pal))
                    rgb = pal[pid].astype(float)
                    if capa is not None and capa.any():  # o cachecol caído sobre ombros e costas
                        rgb[capa] = vinho
                        rgb[capa & ~np.logical_and.reduce(_vizinhos(capa, True))] = vinho_escuro
            alfa = np.where(opaco, 255, 0)
            bloco = np.concatenate([np.clip(rgb, 0, 255), alfa[..., None]], -1)
            img[py0:py1, px0:px1] = bloco.astype(np.uint8)
    return Image.fromarray(img, "RGBA")
