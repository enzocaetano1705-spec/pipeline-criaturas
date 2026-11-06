"""Roda o esqueleto automático e grava diagnostico-juntas.png + juntas.json.

Uso: uv run python scripts/malha-para-cubos/diagnosticar_juntas.py <pasta malha-vN>
"""

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import esqueleto  # noqa: E402
import vistas  # noqa: E402


def main():
    pasta = Path(sys.argv[1])
    t0 = time.time()
    dados = np.load(pasta / "voxels.npz")
    sobre = pasta / "juntas-corrigidas.json"
    sobrescrever = json.loads(sobre.read_text(encoding="utf-8")) if sobre.exists() else None
    pos = dados["origem"] + (dados["sup_idx"] + 0.5) * float(dados["voxel"])
    esq = esqueleto.detectar(dados["ocupado"], dados["origem"], float(dados["voxel"]), sobrescrever=sobrescrever,
                             cores=(pos, dados["sup_cor"].astype(float)))
    folha = vistas.folha_esqueleto(pos, dados["sup_cor"], esq, titulo=pasta.name)
    folha.save(pasta / "diagnostico-juntas.png")
    saida = {
        "papeis": {p: [round(float(c), 2) for c in esq["pontas"][i]["pos"]] for p, i in esq["papeis"].items()},
        "ramos": {p: round(esq["pontas"][i]["ramo"], 2) for p, i in esq["papeis"].items()},
        "ossos": [{"nome": o["nome"], "pai": o["pai"], "pivo": np.round(o["pivo"], 2).tolist(),
                   "fim": None if o["fim"] is None else np.round(o["fim"], 2).tolist()} for o in esq["ossos"]],
    }
    (pasta / "juntas.json").write_text(json.dumps(saida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"pontas: {len(esq['pontas'])}  papéis: {', '.join(esq['papeis'])}")
    print(f"ossos: {len(esq['ossos'])}  núcleo: {np.round(esq['grade'].pos[esq['nucleo']], 1).tolist()}")
    for p, i in esq["papeis"].items():
        print(f"  {p:14s} pos={np.round(esq['pontas'][i]['pos'], 1).tolist()} ramo={esq['pontas'][i]['ramo']:.1f}")
    print(f"diagnóstico: {pasta / 'diagnostico-juntas.png'} ({folha.size[0]}×{folha.size[1]}) em {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
