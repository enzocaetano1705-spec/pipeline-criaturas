"""Locators padrão (docs/convencoes.md, Locators) posicionados a partir das partes medidas.

Cada parte é {id, from, to}; o osso de cada locator é a parte de onde ele sai.
"""

import re

import numpy as np


def _centro(p):
    return (np.asarray(p["from"], float) + np.asarray(p["to"], float)) / 2


def _min(p):
    return np.minimum(p["from"], p["to"]).astype(float)


def _max(p):
    return np.maximum(p["from"], p["to"]).astype(float)


def _r(v):
    return [round(float(x), 2) for x in v]


def locators(partes: list[dict]) -> list[dict]:
    """[{nome, osso, posicao}] para as partes que existirem."""
    por_id = {p["id"]: p for p in partes}
    saida = []

    def add(nome, osso, pos):
        if osso in por_id:
            saida.append({"nome": nome, "osso": osso, "posicao": _r(pos)})

    head = por_id.get("head")
    body = por_id.get("body")
    if head:
        add("loc_head_look", "head", _centro(head))
        boca = next((por_id[k] for k in ("mouth", "jaw", "beak", "snout") if k in por_id), None)
        if boca:
            c = _centro(boca)
            add("loc_mouth", boca["id"], [c[0], c[1], _min(boca)[2]])
        else:
            c = _centro(head)
            add("loc_mouth", "head", [c[0], _min(head)[1] + (_max(head)[1] - _min(head)[1]) / 3, _min(head)[2]])
    for lado in ("left", "right"):
        olho = por_id.get(f"eye_{lado}")
        if olho:
            add(f"loc_eye_{lado}", olho["id"], _centro(olho) + [0, 0, -0.1])
        mao = next((por_id[k] for k in (f"hand_{lado}", f"forearm_{lado}", f"arm_{lado}") if k in por_id), None)
        if mao:
            c = _centro(mao)
            add(f"loc_hand_{lado}", mao["id"], [c[0], _min(mao)[1], c[2]])
    # pés: o segmento mais baixo de cada perna, no chão
    pernas = {}
    for pid in por_id:
        m = re.match(r"^(leg|shin|foot)_(.+)$", pid)
        if m:
            sufixo = m.group(2)
            if sufixo not in pernas or _min(por_id[pid])[1] < _min(por_id[pernas[sufixo]])[1]:
                pernas[sufixo] = pid
    for sufixo, pid in sorted(pernas.items()):
        c = _centro(por_id[pid])
        add(f"loc_foot_{sufixo}", pid, [c[0], _min(por_id[pid])[1], c[2]])
    caudas = sorted((pid for pid in por_id if re.match(r"^tail_\d+$", pid)), key=lambda s: int(s.split("_")[1]))
    if caudas:
        ponta = por_id[caudas[-1]]
        c = _centro(ponta)
        base = _centro(por_id[caudas[0]])
        direcao = c - base
        if np.linalg.norm(direcao) < 1e-6:
            direcao = np.array([0, 0, 1.0])
        eixo = int(np.argmax(np.abs(direcao)))
        pos = c.copy()
        pos[eixo] = _max(ponta)[eixo] if direcao[eixo] > 0 else _min(ponta)[eixo]
        add("loc_tail_tip", ponta["id"], pos)
    if body:
        c = _centro(body)
        add("loc_center", "body", c)
        topo = max(_max(p)[1] for p in partes)
        ref = _centro(head) if head else c
        add("loc_top", "head" if head else "body", [ref[0], topo + 2, ref[2]])
        add("loc_ground", "body", [c[0], 0.0, c[2]])
    return saida
