"""Cria os ossos das garras (claw_<lado>_<n>) numa cópia do modelo aprovado, sem mexer na geometria.

Cada cubo `hand_<lado>_claw_<n>` passa a ficar dentro de um osso próprio com o pivô na base da garra
(a ponta do cubo mais perto da palma). Assim a garra pode dobrar para dentro (andar nos nós das
mãos) e ser recolhida no arremesso. Geometria, UV e textura ficam idênticas (conferido).

Uso: uv run python scripts/fera-animacao/garras.py <entrada.bbmodel> <saida.bbmodel>
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

import numpy as np

from criaturas import bbmodelo, motor


def assinatura_geometria(bruto):
    els = sorted(({k: v for k, v in e.items() if k in ("name", "from", "to", "origin", "rotation", "faces", "uv_offset")}
                  for e in bruto["elements"]), key=lambda e: e["name"])
    return hashlib.sha256(json.dumps(els, sort_keys=True).encode()).hexdigest()


def base_da_garra(c, hand_pivo):
    """Ponta do eixo longo do cubo mais perto do pivô da mão (em coordenadas do modelo)."""
    tam = c.ate - c.de
    k = int(np.argmax(tam))
    centro = (c.de + c.ate) / 2
    M = bbmodelo.matriz_rotacao(c.rotacao)
    pontas = []
    for s in (-1, 1):
        p = centro.copy()
        p[k] += s * tam[k] / 2
        pontas.append(c.origem + M @ (p - c.origem))
    return min(pontas, key=lambda p: np.linalg.norm(p - hand_pivo))


def main():
    entrada, saida = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    if saida.exists():
        raise SystemExit(f"{saida} já existe")
    m = bbmodelo.ler(entrada)
    ops = []
    for c in m.cubos:
        r = re.fullmatch(r"hand_(left|right)_claw_(\d+)", c.nome)
        if not r:
            continue
        lado, n = r.groups()
        mao = m.ossos[f"hand_{lado}"].origem
        base = base_da_garra(c, mao)
        nome = f"claw_{lado}_{n}"
        ops.append({"op": "add_group", "name": nome, "origin": [round(float(v), 3) for v in base], "parent": f"hand_{lado}"})
        ops.append({"op": "update_node", "target": c.nome, "parent": nome})
    saida.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(entrada, saida)
    motor.editar(saida, ops)
    a = json.loads(entrada.read_text(encoding="utf-8"))
    b = json.loads(saida.read_text(encoding="utf-8"))
    igual = assinatura_geometria(a) == assinatura_geometria(b)
    erros, avisos, _ = motor.resumo_validacao(motor.validar(saida))
    print(f"ossos de garra: {len(ops) // 2} · geometria/UV iguais: {igual} · {erros} erros, {avisos} avisos")
    if not igual:
        raise SystemExit("a geometria mudou; abortado")


if __name__ == "__main__":
    main()
