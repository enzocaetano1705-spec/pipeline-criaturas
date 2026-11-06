"""Traz para o rig o que o usuário mudou nos cubos dentro do Blockbench (aba exportada sem salvar).

Compara os cubos pelo uuid e copia from/to/origin/rotation que mudaram. Grupos: pivô mudado é levado
junto; rotação de repouso mudada é recusada (os clipes contam com ossos de rotação zero no repouso).
A diferença fica registrada em <pasta da saída>/<registro>.json.

Uso: uv run python scripts/fera-animacao/trazer_edicao.py <base.bbmodel> <aba-exportada.bbmodel> <saida.bbmodel> [registro]
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from criaturas import motor

CAMPOS = ("from", "to", "origin", "rotation")
ZERO = [0, 0, 0]


def _valor(e, k):
    v = e.get(k)
    return ZERO if v is None and k == "rotation" else v


def _igual(a, b):
    if a is None or b is None:
        return a == b
    return all(abs(float(x) - float(y)) < 1e-6 for x, y in zip(a, b))


def main():
    base, aba, saida = (Path(a).resolve() for a in sys.argv[1:4])
    registro = sys.argv[4] if len(sys.argv) > 4 else "edicao"
    if saida.exists():
        raise SystemExit(f"{saida} já existe")
    a = json.loads(base.read_text(encoding="utf-8"))
    b = json.loads(aba.read_text(encoding="utf-8"))
    eb = {e["uuid"]: e for e in b["elements"]}
    novos = [e["name"] for e in b["elements"] if e["uuid"] not in {x["uuid"] for x in a["elements"]}]
    if novos:
        raise SystemExit(f"a aba tem elementos que a base não tem (não tratado aqui): {novos}")
    ops, diff = [], {}
    for e in a["elements"]:
        f = eb.get(e["uuid"])
        if f is None or e.get("type", "cube") != "cube":
            continue
        mud = {k: _valor(f, k) for k in CAMPOS if not _igual(_valor(e, k), _valor(f, k))}
        if mud:
            ops.append({"op": "update_node", "target": e["uuid"], **mud})
            diff[e["name"]] = {k: {"antes": _valor(e, k), "depois": v} for k, v in mud.items()}
    gb = {g["uuid"]: g for g in b.get("groups", [])}
    for g in a.get("groups", []):
        h = gb.get(g["uuid"])
        if h is None:
            raise SystemExit(f"o grupo {g['name']} sumiu na aba")
        if not _igual(_valor(g, "rotation"), _valor(h, "rotation")):
            raise SystemExit(f"o osso {g['name']} ganhou rotação de repouso {h.get('rotation')}: os clipes contam com zero")
        if not _igual(g.get("origin"), h.get("origin")):
            ops.append({"op": "update_node", "target": g["uuid"], "origin": h["origin"]})
            diff[f"osso {g['name']}"] = {"origin": {"antes": g.get("origin"), "depois": h["origin"]}}
    if not ops:
        raise SystemExit("nenhuma diferença nos cubos ou pivôs")
    saida.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(base, saida)
    motor.editar(saida, ops)
    (saida.parent / f"{registro}.json").write_text(json.dumps(diff, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for nome, campos in diff.items():
        for k, v in campos.items():
            print(f"{nome}: {k} {v['antes']} → {v['depois']}")


if __name__ == "__main__":
    main()
