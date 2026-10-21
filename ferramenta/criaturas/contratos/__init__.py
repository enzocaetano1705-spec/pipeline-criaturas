"""Esquemas JSON dos arquivos que o pipeline lê e grava, e a validação deles."""

import json
from functools import cache
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

PASTA = Path(__file__).parent
NOMES = ("entrada", "checklist", "classificacao", "leitura", "medidas", "plano_cubos", "relatorio")


class ContratoInvalido(ValueError):
    """Os dados não seguem o esquema. A mensagem lista até 10 problemas."""


@cache
def _registro() -> Registry:
    recursos = []
    for arquivo in PASTA.glob("*.schema.json"):
        esquema = json.loads(arquivo.read_text(encoding="utf-8"))
        recursos.append((esquema["$id"], Resource.from_contents(esquema)))
    return Registry().with_resources(recursos)


@cache
def _validador(nome: str) -> Draft202012Validator:
    if nome not in NOMES:
        raise KeyError(f"contrato desconhecido: {nome} (conhecidos: {', '.join(NOMES)})")
    esquema = _registro().contents(f"{nome}.schema.json")
    return Draft202012Validator(esquema, registry=_registro())


def problemas(nome: str, dados) -> list[str]:
    """Lista os problemas de `dados` contra o contrato `nome` (vazia se válido)."""
    erros = sorted(_validador(nome).iter_errors(dados), key=lambda e: list(e.absolute_path))
    return [f"{'/'.join(str(p) for p in e.absolute_path) or '(raiz)'}: {e.message}" for e in erros]


def validar(nome: str, dados) -> None:
    """Levanta ContratoInvalido se `dados` não segue o contrato `nome`."""
    lista = problemas(nome, dados)
    if lista:
        raise ContratoInvalido(f"{nome}: " + "; ".join(lista[:10]))
