"""Criaturas sintéticas com a verdade conhecida (ferramenta/testes/sinteticos/*.json).

Cada definição lista as partes centrais e as do lado esquerdo (-X), em unidades do modelo.
As do lado direito saem espelhadas em X. Uma parte vira um osso (pivô na junta) e um cubo.
"""

import json
from pathlib import Path

from criaturas import motor, ops, relatorio
from criaturas.caminhos import MODELOS, RAIZ

PASTA = RAIZ / "ferramenta" / "testes" / "sinteticos"
SAIDA = MODELOS / "_sinteticos"
NOMES = ("quadrupede", "bipede-cauda", "alado")


def _espelhar_x(v):
    return [-v[0], v[1], v[2]]


def carregar(nome: str) -> dict:
    """Definição com as partes da direita já espelhadas e simetria/espelho preenchidos."""
    d = json.loads((PASTA / f"{nome}.json").read_text(encoding="utf-8"))
    partes = []
    for p in d["partes"]:
        p = dict(p)
        if p["id"].endswith("_left"):
            direita = dict(p)
            direita["id"] = p["id"][: -len("_left")] + "_right"
            if direita["pai"] and direita["pai"].endswith("_left"):
                direita["pai"] = direita["pai"][: -len("_left")] + "_right"
            a, b = _espelhar_x(p["from"]), _espelhar_x(p["to"])
            direita["from"] = [min(a[0], b[0]), a[1], a[2]]
            direita["to"] = [max(a[0], b[0]), b[1], b[2]]
            direita["pivo"] = _espelhar_x(p["pivo"])
            direita["simetria"], direita["espelho"] = "direita", p["id"]
            p["simetria"], p["espelho"] = "esquerda", direita["id"]
            partes += [p, direita]
        else:
            p.setdefault("simetria", "central")
            p.setdefault("espelho", None)
            partes.append(p)
    d["partes"] = partes
    return d


def plano_cubos(definicao: dict) -> dict:
    """Plano de cubos (contrato plano_cubos) de uma definição sintética."""
    cores = definicao["papeis_cor"]
    ossos = [{"nome": "root", "pai": None, "pivo": [0, 0, 0]}]
    cubos = []
    for p in definicao["partes"]:
        ossos.append({"nome": p["id"], "pai": p["pai"] or "root", "pivo": p["pivo"]})
        cubo = {"nome": f"{p['id']}_cube", "osso": p["id"], "parte": p["id"], "tipo": p["tipo"],
                "from": p["from"], "to": p["to"], "cor": cores[p["papel_cor"]]}
        if p["simetria"] == "direita":
            cubo["espelho_de"] = f"{p['espelho']}_cube"
            cubo["mirror_uv"] = True
        cubos.append(cubo)
    offsets, (largura, altura) = ops.distribuir_uv(cubos)
    for c in cubos:
        c["uv_offset"] = offsets[c["nome"]]
        c.pop("espelho_de", None)
    return {"nome": definicao["nome"], "formato": "bedrock", "resolucao": {"largura": largura, "altura": altura},
            "ossos": ossos, "cubos": cubos, "locators": []}


def cores_por_cubo(plano: dict) -> dict[str, str]:
    return {c["nome"]: c["cor"] for c in plano["cubos"] if c.get("cor")}


def construir(nome: str, destino: Path | None = None) -> Path:
    """Gera plano-cubos.json, ops.json, verdade.json e o .bbmodel da sintética. Devolve o .bbmodel."""
    definicao = carregar(nome)
    pasta = Path(destino or SAIDA / nome / "e1")
    plano = plano_cubos(definicao)
    lote = ops.gerar_ops(plano)
    relatorio.gravar_json(pasta / "plano-cubos.json", plano, "plano_cubos")
    relatorio.gravar_json(pasta / "ops.json", {"operations": lote})
    relatorio.gravar_json(pasta / "verdade.json", definicao)
    arquivo = pasta / f"{nome}-e1.bbmodel"
    motor.criar(arquivo, nome, plano["resolucao"]["largura"], plano["resolucao"]["altura"])
    motor.editar(arquivo, lote)
    return arquivo
