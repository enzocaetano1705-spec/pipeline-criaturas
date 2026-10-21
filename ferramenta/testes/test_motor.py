import json
import shutil

import pytest

from criaturas import motor
from criaturas.caminhos import MODELOS, REFERENCIA

pytestmark = pytest.mark.skipif(not motor.disponivel(), reason="motor headless não instalado (item 0.3)")

PASTA = MODELOS / "_teste-motor"
EXEMPLO = REFERENCIA / "exemplo-headless"


@pytest.fixture(scope="module")
def modelo_fumaca():
    shutil.rmtree(PASTA, ignore_errors=True)
    arquivo = PASTA / "exemplo.bbmodel"
    motor.criar(arquivo, "exemplo")
    ops = json.loads((EXEMPLO / "ops-exemplo.json").read_text(encoding="utf-8"))["operations"]
    motor.editar(arquivo, ops)
    yield arquivo
    shutil.rmtree(PASTA, ignore_errors=True)


def test_recria_fumaca_pela_ponte(modelo_fumaca):
    erros, avisos, _ = motor.resumo_validacao(motor.validar(modelo_fumaca))
    assert (erros, avisos) == (0, 0)
    erros, _, _ = motor.resumo_validacao(motor.validar_animacoes(modelo_fumaca))
    assert erros == 0


def test_exporta_bedrock(modelo_fumaca):
    saida = PASTA / "exemplo.geo.json"
    resultado = motor.exportar_bedrock(modelo_fumaca, saida)
    assert resultado["skipped"] == []
    geo = json.loads(saida.read_text(encoding="utf-8"))
    assert {b["name"] for b in geo["minecraft:geometry"][0]["bones"]} >= {"root", "body", "head"}


def test_erro_do_motor_vira_excecao(modelo_fumaca):
    # o mesmo lote de novo duplica os nomes, e o bbmodel_edit é atômico: deve falhar
    ops = json.loads((EXEMPLO / "ops-exemplo.json").read_text(encoding="utf-8"))["operations"]
    with pytest.raises(motor.MotorErro):
        motor.editar(modelo_fumaca, ops)
