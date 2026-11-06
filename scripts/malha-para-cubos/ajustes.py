"""Ajustes do usuário reaplicados depois de cada conversão (arquivo <pasta>/ajustes.json).

A conversão parte da malha; correções artísticas que o usuário fez no Blockbench (ou pediu) ficam
aqui para não se perderem quando o modelo é gerado de novo. Exemplo:

{
  "transladar": [{"a_partir_de": "tail_1", "manter_primeiro_cubo": true, "delta": [0, 4, 2]}],
  "girar_membros": [{"osso": "arm", "eixo": [0, 0, 1], "graus": 18}]
}

- transladar: move a subárvore (cubos, planos, locators e pivôs dos ossos filhos). O pivô do osso
  de partida fica no lugar; com manter_primeiro_cubo o 1º cubo dele (a ligação com o corpo) sobe
  só metade, para a junção não virar um degrau grande.
- girar_membros: gira <osso>_left e <osso>_right (e tudo abaixo) em torno do pivô; graus positivos
  fecham o membro na direção do meio do corpo (o lado direito usa o espelho).
- substituir_cubos: {nome: {from, to, origin, rotation}} com a geometria exata que o usuário deixou
  no Blockbench (pose final); vale enquanto o conversor gerar o cubo com o mesmo nome.

Os ajustes entram antes de distribuir a UV (tamanhos podem mudar); a textura projetada usa o
caminho de volta guardado em cada cubo movido para buscar a cor na pose da malha.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import cubos as cb


def _subarvore(ossos, raiz):
    filhos = {}
    for o in ossos:
        filhos.setdefault(o["pai"], []).append(o["nome"])
    saida, pilha = [], [raiz]
    while pilha:
        n = pilha.pop()
        saida.append(n)
        pilha += filhos.get(n, [])
    return saida


def _rot_eixo(eixo, graus):
    e = np.asarray(eixo, float)
    e /= np.linalg.norm(e)
    a = np.radians(graus)
    K = np.array([[0, -e[2], e[1]], [e[2], 0, -e[0]], [-e[1], e[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


def _mover_cubo(c, R, P, delta):
    """Transformação rígida p -> R (p - P) + P + delta aplicada a um cubo (from/to/origin/rotation).

    Guarda em c["inv"] = (A, b) o caminho de volta (pose final -> pose da malha): a textura projetada
    busca a cor de cada pixel no lugar onde o cubo estava na malha.
    """
    t = P - R @ P + delta
    A, b = c.get("inv", (np.eye(3), np.zeros(3)))
    c["inv"] = (A @ R.T, A @ (-R.T @ t) + b)
    o = np.asarray(c["origin"], float)
    o_novo = R @ (o - P) + P + delta
    c["from"] = np.asarray(c["from"], float) + (o_novo - o)
    c["to"] = np.asarray(c["to"], float) + (o_novo - o)
    c["origin"] = o_novo
    if not np.allclose(R, np.eye(3)):
        c["rotation"] = cb.rot_limpa(np.round(cb.euler_de(R @ cb.matriz(c["rotation"])), 2))
    if "fonte_pos" in c:  # pontos-fonte dos planos acompanham (o recorte já foi pintado)
        c["fonte_pos"] = (np.asarray(c["fonte_pos"]) - P) @ R.T + P + delta


def aplicar(pasta, cubos, ossos, locs):
    """Aplica <pasta>/ajustes.json. Devolve a lista de mensagens do que foi feito."""
    arq = Path(pasta) / "ajustes.json"
    if not arq.exists():
        return []
    cfg = json.loads(arq.read_text(encoding="utf-8"))
    por_nome = {o["nome"]: o for o in ossos}
    feitos = []
    for t in cfg.get("transladar", []):
        raiz = t["a_partir_de"]
        if raiz not in por_nome:
            continue
        delta = np.asarray(t["delta"], float)
        grupo = set(_subarvore(ossos, raiz))
        for c in cubos:
            if c["osso"] not in grupo:
                continue
            if t.get("manter_primeiro_cubo") and c["nome"] == raiz:
                # a ligação com o corpo sobe só metade: dois degraus pequenos em vez de um grande
                _mover_cubo(c, np.eye(3), np.zeros(3), delta * 0.5)
            else:
                _mover_cubo(c, np.eye(3), np.zeros(3), delta)
        for n in grupo:
            o = por_nome[n]
            if n != raiz:
                o["pivo"] = o["pivo"] + delta
            if o["fim"] is not None:
                o["fim"] = o["fim"] + delta
        for loc in locs:
            if loc["osso"] in grupo:
                loc["posicao"] = (np.asarray(loc["posicao"], float) + delta).round(4).tolist()
        feitos.append(f"{raiz} e filhos movidos {delta.tolist()}")
    for gm in cfg.get("girar_membros", []):
        for lado, sinal in (("left", 1.0), ("right", -1.0)):
            raiz = f"{gm['osso']}_{lado}"
            if raiz not in por_nome:
                continue
            P = np.asarray(por_nome[raiz]["pivo"], float).copy()
            R = _rot_eixo(gm.get("eixo", [0, 0, 1]), sinal * float(gm["graus"]))
            grupo = set(_subarvore(ossos, raiz))
            for c in cubos:
                if c["osso"] in grupo:
                    _mover_cubo(c, R, P, np.zeros(3))
            for n in grupo:
                o = por_nome[n]
                o["pivo"] = R @ (o["pivo"] - P) + P
                if o["fim"] is not None:
                    o["fim"] = R @ (o["fim"] - P) + P
            for loc in locs:
                if loc["osso"] in grupo:
                    p = np.asarray(loc["posicao"], float)
                    loc["posicao"] = (R @ (p - P) + P).round(4).tolist()
        feitos.append(f"{gm['osso']} fechado {gm['graus']}°")
    # cubos editados à mão no Blockbench: geometria exata (pose final), copiada da aba do usuário
    subst = cfg.get("substituir_cubos", {})
    por_cubo = {c["nome"]: c for c in cubos}
    trocados = []
    for nome, geo in subst.items():
        c = por_cubo.get(nome)
        if c is None:
            continue
        for k in ("from", "to", "origin", "rotation"):
            if k in geo:
                c[k] = np.asarray(geo[k], float)
        c.pop("inv", None)  # cor buscada onde o cubo está agora
        trocados.append(nome)
    # espelho só reaproveita a ilha de UV se ficou do mesmo tamanho que o original
    for c in cubos:
        fonte = por_cubo.get(c.get("espelho_de"))
        if fonte is not None:
            ta = np.abs(np.asarray(c["to"]) - np.asarray(c["from"]))
            tb = np.abs(np.asarray(fonte["to"]) - np.asarray(fonte["from"]))
            if not np.allclose(ta, tb, atol=1e-3):
                c.pop("espelho_de")
    if trocados:
        feitos.append("cubos editados à mão: " + ", ".join(trocados))
    return feitos
