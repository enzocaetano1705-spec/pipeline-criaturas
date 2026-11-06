"""Alinha os pivôs do joelho e do tornozelo aos cubos que o usuário editou (canela e pé recuados).

O usuário moveu os cubos da canela e do pé no Blockbench, mas os pivôs dos ossos (shin_*, foot_*)
ficaram no lugar antigo: ao animar, o pé girava em torno de um ponto 3 unidades à frente dele e se
soltava da canela. Aqui o joelho vai para o topo do cubo da canela e o tornozelo para a base dela, na
altura do topo do pé. Só os pivôs mudam (os cubos ficam onde estão; conferido).

Uso: uv run python scripts/fera-animacao/pivos_pernas.py <entrada.bbmodel> <saida.bbmodel>
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from garras import assinatura_geometria  # noqa: E402

from criaturas import bbmodelo, motor  # noqa: E402


def pontas(c):
    tam = c.ate - c.de
    k = int(np.argmax(tam))
    centro = (c.de + c.ate) / 2
    M = bbmodelo.matriz_rotacao(c.rotacao)
    out = []
    for s in (-1, 1):
        p = centro.copy()
        p[k] += s * tam[k] / 2
        out.append(c.origem + M @ (p - c.origem))
    return sorted(out, key=lambda p: -p[1])  # [topo, base]


def main():
    entrada, saida = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    if saida.exists():
        raise SystemExit(f"{saida} já existe")
    m = bbmodelo.ler(entrada)
    ops, rel = [], {}
    for lado in ("left", "right"):
        canela = next(c for c in m.cubos if c.nome == f"shin_{lado}")
        pe = next(c for c in m.cubos if c.nome == f"foot_{lado}")
        topo, base = pontas(canela)
        topo_pe = float(pe.ate[1])
        joelho = topo
        tornozelo = np.array([base[0], topo_pe, base[2]])
        ops.append({"op": "update_node", "target": f"shin_{lado}", "origin": [round(float(v), 3) for v in joelho]})
        ops.append({"op": "update_node", "target": f"foot_{lado}", "origin": [round(float(v), 3) for v in tornozelo]})
        rel[lado] = {"joelho": np.round(joelho, 2).tolist(), "tornozelo": np.round(tornozelo, 2).tolist()}
    # os alvos 'shin_*'/'foot_*' são grupos e cubos com o mesmo nome: o motor resolve o grupo pelo tipo
    saida.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(entrada, saida)
    grupos = {g["name"]: g["uuid"] for g in json.loads(entrada.read_text(encoding="utf-8"))["groups"]}
    for op in ops:
        op["target"] = grupos[op["target"]]
    motor.editar(saida, ops)
    a = json.loads(entrada.read_text(encoding="utf-8"))
    b = json.loads(saida.read_text(encoding="utf-8"))
    igual = assinatura_geometria(a) == assinatura_geometria(b)
    print(f"pivôs: {rel} · cubos iguais: {igual}")
    if not igual:
        raise SystemExit("os cubos mudaram; abortado")


if __name__ == "__main__":
    main()
