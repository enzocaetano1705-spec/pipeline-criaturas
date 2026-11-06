"""Aplica no rig as pernas que o usuário recuou no Blockbench e move os pivôs junto.

O usuário moveu os cubos da coxa (+10 em Z) e da canela/pé (+9 em Z) para as pernas não entrarem nos
braços nas animações. Os pivôs dos ossos ficaram no lugar antigo; aqui cada osso da perna anda o mesmo
que o seu cubo (quadril com a coxa, joelho e tornozelo com a canela e o pé). A geometria editada é
guardada em `edicao-pernas.json` (lida da aba aberta, sem salvar por cima de nada).

Uso: uv run python scripts/fera-animacao/pernas_recuadas.py <base.bbmodel> <aba-exportada.bbmodel> <saida.bbmodel>
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import numpy as np

from criaturas import motor

PERNAS = ("leg_left", "leg_right", "shin_left", "shin_right", "foot_left", "foot_right")


def main():
    base, aba, saida = (Path(a).resolve() for a in sys.argv[1:4])
    if saida.exists():
        raise SystemExit(f"{saida} já existe")
    a = json.loads(base.read_text(encoding="utf-8"))
    b = json.loads(aba.read_text(encoding="utf-8"))
    ea = {e["name"]: e for e in a["elements"]}
    eb = {e["name"]: e for e in b["elements"]}
    grupos = {g["name"]: g for g in a["groups"]}
    edicao, ops = {}, []
    for nome in PERNAS:
        cubo_a, cubo_b = ea[nome], eb[nome]
        delta = np.array(cubo_b["origin"], float) - np.array(cubo_a["origin"], float)
        edicao[nome] = {"from": cubo_b["from"], "to": cubo_b["to"], "origin": cubo_b["origin"], "delta": delta.tolist()}
        ops.append({"op": "update_node", "target": cubo_a["uuid"], "from": cubo_b["from"], "to": cubo_b["to"],
                    "origin": cubo_b["origin"]})
        g = grupos[nome]
        novo = (np.array(g["origin"], float) + delta).round(4).tolist()
        ops.append({"op": "update_node", "target": g["uuid"], "origin": novo})
        edicao[nome]["pivo_osso"] = novo
    saida.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(base, saida)
    motor.editar(saida, ops)
    (saida.parent / "edicao-pernas.json").write_text(json.dumps(edicao, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for n, e in edicao.items():
        print(f"{n}: cubo e pivô +{e['delta']} → pivô {e['pivo_osso']}")


if __name__ == "__main__":
    main()
