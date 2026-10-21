import json
from pathlib import Path

import pytest

from criaturas import contratos

EXEMPLOS = Path(__file__).parent / "exemplos"


@pytest.mark.parametrize("nome", contratos.NOMES)
def test_exemplo_valido(nome):
    dados = json.loads((EXEMPLOS / f"{nome}.json").read_text(encoding="utf-8"))
    assert contratos.problemas(nome, dados) == []


def test_invalido_aponta_o_campo():
    dados = json.loads((EXEMPLOS / "leitura.json").read_text(encoding="utf-8"))
    dados["partes"][0]["tipo"] = "esfera"
    with pytest.raises(contratos.ContratoInvalido, match="partes/0/tipo"):
        contratos.validar("leitura", dados)


def test_checklist_exige_todos_os_itens():
    dados = json.loads((EXEMPLOS / "checklist.json").read_text(encoding="utf-8"))
    del dados["itens"]["cauda"]
    assert any("cauda" in p for p in contratos.problemas("checklist", dados))


def test_contrato_desconhecido():
    with pytest.raises(KeyError):
        contratos.validar("nada", {})
