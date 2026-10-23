"""Exporta para o Roblox as criaturas de exportacoes/roblox/criaturas.json (todas, ou as de nome dado).

    uv run python scripts/exportar-roblox.py            # todas
    uv run python scripts/exportar-roblox.py Pavao_F2   # só uma

Saída: exportacoes/roblox/<especie>/<Nome>.glb e <Nome>-textura.png. Precisa do Blockbench desktop aberto
com o plugin MCP (o .glb sai do exportador glTF dele).
"""
import json
import sys
from pathlib import Path

from criaturas import exportar

RAIZ = Path(__file__).resolve().parents[1]
PASTA = RAIZ / "exportacoes" / "roblox"

registro = json.loads((PASTA / "criaturas.json").read_text(encoding="utf-8"))
pedidas = set(sys.argv[1:])
falhas = 0
for c in registro["criaturas"]:
    if pedidas and c["nome"] not in pedidas:
        continue
    r = exportar.exportar_roblox(RAIZ / c["fonte"], c["nome"], PASTA / c["especie"], c.get("texturas_separadas"),
                               c.get("superamostrar"), material_pbr=c.get("material_pbr", False),
                               espelhar_atlas=c.get("espelhar_atlas", False))
    print(f"{c['nome']}: {r['glb'].relative_to(RAIZ)}  {r['resumo']}")
    for m in r["erros"] + r["avisos"]:
        print("   ", m)
    falhas += bool(r["erros"])
sys.exit(1 if falhas else 0)
