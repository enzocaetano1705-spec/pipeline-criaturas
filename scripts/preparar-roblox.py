"""Gera catálogo/receitas locais: uv run python scripts/preparar-roblox.py [Nomes] [--preservar-escala]."""
import argparse
import json
import re
from pathlib import Path

from criaturas.roblox_infra import conferir_manifesto, receita_preparo

raiz = Path(__file__).resolve().parents[1]
pasta = raiz / "exportacoes/roblox"
p = argparse.ArgumentParser(description=__doc__)
p.add_argument("nomes", nargs="*")
p.add_argument("--preservar-escala", action="store_true", help="mantém a escala já editada no Studio")
args = p.parse_args()
registro = json.loads((pasta / "criaturas.json").read_text(encoding="utf-8"))
nomes = {c["nome"] for c in registro["criaturas"]}
if set(args.nomes) - nomes:
    p.error("criatura desconhecida: " + ", ".join(sorted(set(args.nomes) - nomes)))
template = (pasta / "preparar-criatura.luau").read_text(encoding="utf-8")
catalogo = []
for c in registro["criaturas"]:
    if args.nomes and c["nome"] not in args.nomes:
        continue
    glb = raiz / c["arquivo"]
    arq_manifesto = glb.with_name(c["nome"] + "-importacao.json")
    if not arq_manifesto.exists():
        p.error(f"falta {arq_manifesto.name}; rode scripts/exportar-roblox.py {c['nome']}")
    item = json.loads(arq_manifesto.read_text(encoding="utf-8"))
    try:
        conferir_manifesto(raiz, c, item)
    except ValueError as e:
        p.error(f"{c['nome']}: {e}")
    receita = glb.with_name(c["nome"] + "-preparar.luau")
    receita.write_text(receita_preparo(template, item, args.preservar_escala), encoding="utf-8")
    catalogo.append(item)
    print(f"{c['nome']}: {receita.relative_to(raiz)} ({len(item['colisao']['cubos'])} volumes no corpo)")
nome_catalogo = "catalogo.json" if not args.nomes else "catalogo-selecao.json"
(pasta / nome_catalogo).write_text(json.dumps({"versao": 1, "criaturas": catalogo}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
gerente = pasta / "gerenciar-criaturas.luau"
if gerente.exists():
    lista = json.dumps(sorted(nomes), ensure_ascii=False)
    gerente.write_text(re.sub(r"local NOMES_CONHECIDOS = .* -- @REGISTRO@",
        lambda m: f'local NOMES_CONHECIDOS = game:GetService("HttpService"):JSONDecode([==[{lista}]==]) -- @REGISTRO@',
        gerente.read_text(encoding="utf-8")), encoding="utf-8")
