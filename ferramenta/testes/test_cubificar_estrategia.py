from copy import deepcopy

import numpy as np
import pytest

from criaturas import contratos, cubificar


def parte(pid, de, ate, *, pai=None, tipo="volume", simetria="central", espelho=None, **extra):
    return {"id": pid, "pai": pai, "tipo": tipo, "simetria": simetria, "espelho": espelho,
            "from": list(de), "to": list(ate), **extra}


def medidas_com_fatias():
    return {"partes": [
        parte("body", [-4, 0, -3], [4, 12, 3], fatias=[
            {"x": [-3, 3], "y": [0, 4], "z": [-2, 2]},
            {"x": [-4, 4], "y": [4, 8], "z": [-3, 3]},
            {"x": [-3, 3], "y": [8, 12], "z": [-2, 2]},
        ]),
        parte("eye_left", [-3, 7, -3.01], [-1, 9, -3.01], pai="body", tipo="adesivo",
              simetria="esquerda", espelho="eye_right"),
        parte("eye_right", [1, 7, -3.01], [3, 9, -3.01], pai="body", tipo="adesivo",
              simetria="direita", espelho="eye_left"),
        parte("crest", [-1, 12, 0], [1, 15, 0], pai="body", tipo="plano"),
    ]}


def test_poucas_formas_nao_fatia_e_nao_altera_as_medidas():
    medidas = medidas_com_fatias()
    antes = deepcopy(medidas)
    padrao, _ = cubificar.plano_de_cubos(medidas, "sintetica")
    simples, _ = cubificar.plano_de_cubos(medidas, "sintetica", poucas_formas=True)

    assert sum(c["parte"] == "body" for c in padrao["cubos"]) == 3
    corpos = [c for c in simples["cubos"] if c["parte"] == "body"]
    assert len(corpos) == 1
    assert corpos[0]["from"] == [-4, 0, -3]
    assert corpos[0]["to"] == [4, 12, 3]
    assert medidas == antes


def test_poucas_formas_preserva_apendice_adesivos_e_espelho():
    plano, _ = cubificar.plano_de_cubos(medidas_com_fatias(), "sintetica", poucas_formas=True)
    por_parte = {c["parte"]: c for c in plano["cubos"]}
    assert set(por_parte) == {"body", "eye_left", "eye_right", "crest"}
    esquerda, direita = por_parte["eye_left"], por_parte["eye_right"]
    assert direita["mirror_uv"] is True
    assert direita["from"][0] == -esquerda["to"][0]
    assert direita["to"][0] == -esquerda["from"][0]
    assert direita["from"][1:] == esquerda["from"][1:]
    assert esquerda["from"][2] == esquerda["to"][2] == pytest.approx(-3.01)
    crest = por_parte["crest"]
    assert crest["tipo"] == "plano"
    assert np.count_nonzero(np.array(crest["to"]) - crest["from"] == 0) == 1
    pais = {o["nome"]: o["pai"] for o in plano["ossos"]}
    assert pais["crest"] == pais["eye_left"] == pais["eye_right"] == "body"


def leitura():
    return {"vistas": {"frente": {"imagem": "preparo/frente-grade.png"}},
            "partes": [{"id": "body", "pai": None, "tipo": "volume", "simetria": "central",
                        "caixas": {"frente": [0, 0, 16, 32]}}]}


def test_estrategia_e_opcional_e_aceita_apenas_metadados():
    antiga = leitura()
    contratos.validar("leitura", antiga)
    nova = deepcopy(antiga)
    nova["modelagem"] = {"abordagem": "poucas_formas", "justificativa": "Grandes volumes e rosto pintado",
                         "referencias": [{"nome": "referencia-sintetica", "papel": "corpo",
                                          "caminho": "biblioteca/modelo.bbmodel"}]}
    contratos.validar("leitura", nova)
    nova["modelagem"]["abordagem"] = "silhueta_fatiada"
    contratos.validar("leitura", nova)
    nova["modelagem"]["referencias"][0]["geometria"] = {"cubos": []}
    with pytest.raises(contratos.ContratoInvalido):
        contratos.validar("leitura", nova)


def test_estrategia_desconhecida_e_rejeitada():
    dados = leitura()
    dados["modelagem"] = {"abordagem": "copiar_modelo"}
    with pytest.raises(contratos.ContratoInvalido):
        contratos.validar("leitura", dados)
