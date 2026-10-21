"""Comparações agregadas com exemplos próprios; nenhuma referência externa."""
import argparse
import base64
from copy import deepcopy
import io
import json

import numpy as np
from PIL import Image
import pytest

from criaturas import comparar_referencias as comparar


PARTES = {"corpo": {"elementos": ["tronco"]}, "apendice": {"ossos": ["fin"]}}


def gravar(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def projeto():
    return {
        "meta": {"format_version": "5.0", "model_format": "bedrock", "box_uv": False},
        "resolution": {"width": 8, "height": 8},
        "elements": [
            {"uuid": "c1", "name": "tronco", "from": [0, 0, 0], "to": [4, 6, 2],
             "origin": [0, 0, 0], "faces": {"north": {"uv": [0, 0, 4, 6], "texture": 0}}},
            {"uuid": "c2", "name": "lamina", "from": [4, 2, 1], "to": [8, 4, 1],
             "origin": [4, 2, 1], "faces": {"north": {"uv": [0, 0, 4, 2], "texture": 0}}},
        ],
        "groups": [{"uuid": "g1", "name": "body", "origin": [0, 0, 0], "rotation": [0, 90, 0]},
                   {"uuid": "g2", "name": "fin", "origin": [4, 2, 1]}],
        "outliner": [{"uuid": "g1", "children": ["c1", {"uuid": "g2", "children": ["c2"]}]}],
        "textures": [],
    }


def assinatura(tmp_path, data, name="modelo.bbmodel", partes=PARTES):
    return comparar.assinatura(gravar(tmp_path / name, data), partes, "corpo")


def textura(data, rgba):
    buf = io.BytesIO()
    Image.fromarray(rgba.astype(np.uint8), "RGBA").save(buf, "PNG")
    data["textures"] = [{"source": "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()}]


def assert_medidas_iguais(left, right):
    for name in left["partes"]:
        a, b = left["partes"][name], right["partes"][name]
        for key in ("pecas", "solidos", "planos"):
            assert a[key] == b[key]
        for key in ("dimensoes_por_altura_ancora", "centro_relativo_ancora",
                    "area_planos_projetada_por_altura_ancora_quadrada", "textura"):
            assert a[key] == pytest.approx(b[key])


def test_medidas_normalizadas_invariantes_a_escala_uniforme_e_translacao(tmp_path):
    original = projeto()
    transformed = deepcopy(original)
    deslocamento = np.array([31, -17, 9])
    for node in transformed["elements"] + transformed["groups"]:
        for campo in ("from", "to", "origin"):
            if campo in node:
                node[campo] = (3.25 * np.array(node[campo]) + deslocamento).tolist()
    a = assinatura(tmp_path, original, "antes.bbmodel")
    b = assinatura(tmp_path, transformed, "depois.bbmodel")
    assert_medidas_iguais(a, b)
    assert a["partes"]["corpo"]["textura"]["texels_por_altura_ancora_mediana"] == pytest.approx(6)
    assert a["sha256"] != b["sha256"]


def test_bb4_e_bb5_equivalem_e_rotacao_do_pai_altera_medidas_em_mundo(tmp_path):
    novo = projeto()
    antigo = deepcopy(novo)
    antigo["meta"]["format_version"] = "4.10"
    root, fin = antigo.pop("groups")
    antigo["outliner"] = [{**root, "children": ["c1", {**fin, "children": ["c2"]}]}]
    a = assinatura(tmp_path, novo, "novo.bbmodel")
    b = assinatura(tmp_path, antigo, "antigo.bbmodel")
    assert_medidas_iguais(a, b)
    assert a["partes"]["corpo"]["dimensoes_por_altura_ancora"] == pytest.approx(
        {"largura": 1/3, "altura": 1, "profundidade": 2/3})
    fin = a["partes"]["apendice"]
    assert fin["area_planos_projetada_por_altura_ancora_quadrada"] == pytest.approx(
        {"frente": 0, "lado": 2/9, "cima": 0}, abs=1e-12)
    assert fin["centro_relativo_ancora"] == pytest.approx({"x": 0, "y": 0, "z": -2/3}, abs=1e-12)


@pytest.mark.parametrize("selector", [
    {"tipoo": "solido"}, {"tipo": "cuboo"}, {"ossos": ["finn"]},
    {"elementos": ["tronco", "inexistente"]}, {"ossos": []},
    {"elementos": "tronco"}, {}, {"tipo": "plano", "elementos": ["tronco"]},
])
def test_seletor_invalido_ou_que_nao_encontra_pecas_falha(tmp_path, selector):
    with pytest.raises(ValueError):
        assinatura(tmp_path, projeto(), partes={"corpo": selector})


def test_seletor_de_osso_inclui_descendentes_e_uuid_seleciona_elemento(tmp_path):
    a = assinatura(tmp_path, projeto(), partes={"corpo": {"ossos": ["body"]},
                                               "apendice": {"elementos": ["c2"]}})
    assert a["partes"]["corpo"]["pecas"] == 2
    assert a["partes"]["apendice"]["planos"] == 1


def test_alfa_e_densidade_usam_pixels_reais_e_ignoram_face_desativada(tmp_path):
    data = projeto()
    # Imagem tem o dobro da resolução UV: o retângulo 4x6 cobre 8x12 pixels.
    rgba = np.zeros((16, 16, 4), np.uint8)
    rgba[:6, :8] = [70, 170, 120, 255]
    textura(data, rgba)
    data["elements"][0]["faces"]["south"] = {"uv": [-100, -100, 100, 100], "texture": None}
    a = assinatura(tmp_path, data)
    t = a["partes"]["corpo"]["textura"]
    assert a["textura_incorporada_px"] == [16, 16]
    assert a["unidade_densidade"] == "pixels reais"
    assert t["fracao_alfa_opaca_por_face"] == pytest.approx(0.5)
    assert t["maior_face_north_texels_area"] == 96
    assert t["texels_por_altura_ancora_mediana"] == pytest.approx(12)
    assert t["faces_sem_uv_explicito"] == 4


def test_uv_espelhado_tem_mesma_area_densidade_e_alfa(tmp_path):
    data = projeto()
    rgba = np.zeros((8, 8, 4), np.uint8)
    rgba[:3, :4] = [1, 2, 3, 255]
    textura(data, rgba)
    a = assinatura(tmp_path, data, "normal.bbmodel")
    data["elements"][0]["faces"]["north"]["uv"] = [4, 6, 0, 0]
    data["elements"][1]["faces"]["north"]["uv"] = [4, 2, 0, 0]
    b = assinatura(tmp_path, data, "espelhado.bbmodel")
    assert_medidas_iguais(a, b)


@pytest.mark.parametrize("uv", [[-1, 0, 3, 6], [0, 0, 9, 6]])
def test_uv_externo_falha_sem_truncar_silenciosamente(tmp_path, uv):
    data = projeto()
    textura(data, np.full((8, 8, 4), 255, np.uint8))
    data["elements"][0]["faces"]["north"]["uv"] = uv
    with pytest.raises(ValueError, match="UV fora"):
        assinatura(tmp_path, data)


def caso(tmp_path):
    gravar(tmp_path / "referencia.bbmodel", projeto())
    novo = projeto()
    novo["elements"][1]["to"][2] = 2  # plano -> sólido, mesma função semântica.
    gravar(tmp_path / "candidato.bbmodel", novo)
    return {"modo": "analogia", "ancora": "corpo",
            "referencia": {"arquivo": "referencia.bbmodel", "partes": PARTES},
            "candidato": {"arquivo": "candidato.bbmodel", "partes": PARTES}}


def test_zero_na_referencia_nao_produz_infinito_e_arte_permanece_nao_avaliada(tmp_path):
    result = comparar.comparar(caso(tmp_path), tmp_path)
    metric = next(d for d in result["diferencas"] if d["metrica"] == "apendice.solidos")
    assert metric == {"metrica": "apendice.solidos", "referencia": 0, "candidato": 1,
                      "delta": 1, "variacao_relativa": None}
    assert result["aprovacao_artistica"] == "nao_avaliada"
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("target", ["caso.json", "referencia.bbmodel", "candidato.bbmodel"])
def test_cli_impede_saida_sobre_qualquer_entrada(tmp_path, capsys, target):
    config = gravar(tmp_path / "caso.json", caso(tmp_path))
    path = tmp_path / target
    before = path.read_bytes()
    args = argparse.Namespace(caso=str(config), saida=str(path))
    assert comparar.cmd_comparar(args) == 1
    assert "sobrescrever" in capsys.readouterr().out
    assert path.read_bytes() == before


def test_cli_resolve_modelos_relativos_ao_caso_e_grava_apenas_relatorio(tmp_path, capsys):
    config = gravar(tmp_path / "caso.json", caso(tmp_path))
    originals = {p: p.read_bytes() for p in tmp_path.glob("*.bbmodel")}
    out = tmp_path / "resultados" / "medidas.json"
    assert comparar.cmd_comparar(argparse.Namespace(caso=str(config), saida=str(out))) == 0
    assert len(capsys.readouterr().out.splitlines()) <= 20
    result = json.loads(out.read_text(encoding="utf-8"))
    assert result["modo"] == "analogia"
    for path, before in originals.items():
        assert path.read_bytes() == before
    dumped = json.dumps(result)
    for forbidden in ('"from"', '"to"', '"source"', '"uv"', '"data_points"'):
        assert forbidden not in dumped


def test_nao_compara_uv_nominal_com_pixels_reais(tmp_path):
    config = caso(tmp_path)
    data = projeto()
    textura(data, np.full((16, 16, 4), 255, np.uint8))
    gravar(tmp_path / "candidato.bbmodel", data)
    result = comparar.comparar(config, tmp_path)
    excluded = {m['metrica'] for m in result['metricas_nao_comparaveis']}
    assert 'corpo.textura.texels_por_altura_ancora_mediana' in excluded
    assert 'corpo.textura.maior_face_north_texels_area' in excluded
    assert not excluded.intersection(m['metrica'] for m in result['diferencas'])
    assert any(m['metrica'] == 'corpo.pecas' for m in result['diferencas'])


def test_nomes_repetidos_deixam_explicitas_as_ocorrencias_selecionadas(tmp_path):
    data = projeto()
    for e in data['elements']:
        e['name'] = 'cube'
    result = assinatura(tmp_path, data, partes={'corpo': {'elementos': ['cube']}})
    assert result['partes']['corpo']['elementos_selecionados'] == [
        {'nome': 'cube', 'uuid': 'c1'}, {'nome': 'cube', 'uuid': 'c2'}]


def test_rotacao_sem_pivo_explicito_usa_centro_do_cubo(tmp_path):
    data = projeto()
    cube = data['elements'][1]
    cube.pop('origin')
    cube['rotation'] = [20, 0, 35]
    inferred = assinatura(tmp_path, data, 'implicito.bbmodel')
    cube['origin'] = ((np.array(cube['from'])+cube['to'])/2).tolist()
    explicit = assinatura(tmp_path, data, 'explicito.bbmodel')
    assert_medidas_iguais(inferred, explicit)
