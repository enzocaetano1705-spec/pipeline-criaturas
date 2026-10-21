import json
import shutil

import numpy as np
import pytest
from PIL import Image

from criaturas import bbmodelo, cli, cubificar, medir, motor, preparar, rig, sinteticos, validar
from criaturas.caminhos import MODELOS


# ---------- unidades ----------

def _p(pid, de, ate, tipo="volume", pai=None, simetria="central", espelho=None, **extra):
    return {"id": pid, "pai": pai, "tipo": tipo, "simetria": simetria, "espelho": espelho,
            "from": list(map(float, de)), "to": list(map(float, ate)), **extra}


def test_arredondar_inteiro_e_simetrico():
    partes = [_p("body", [-2.8, 4.3, -4.6], [3.1, 10.2, 5.4]),
              _p("leg_left", [-3.2, 0, -1.1], [-0.9, 4.3, 1.2], simetria="esquerda", espelho="leg_right", pai="body"),
              _p("leg_right", [1.3, 0.2, -0.8], [3.4, 4.1, 0.9], simetria="direita", espelho="leg_left", pai="body")]
    cubificar.arredondar(partes)
    body, e, d = partes
    assert body["from"][0] == -body["to"][0] == -3.0
    assert all(float(b - a).is_integer() for a, b in zip(body["from"], body["to"]))
    assert d["from"][0] == -e["to"][0] and d["to"][0] == -e["from"][0] and d["from"][1:] == e["from"][1:]


def test_contatos_fecham_vao_e_desfazem_interpenetracao():
    body = _p("body", [-3, 5, -4], [3, 11, 4])
    leg = _p("leg_left", [-3, 0, -1], [-1, 4, 1], pai="body")  # vão de 1 unidade
    head = _p("head", [-3, 9, -9], [3, 15, -3], pai="body")  # entra 1 unidade no corpo em z
    ear = _p("ear_left", [-3, 15, -6], [-1, 18, -6], tipo="plano", pai="head")  # só encosta pela aresta
    avisos = []
    cubificar.resolver_contatos([body, leg, head, ear], avisos)
    assert leg["to"][1] == 5
    assert head["to"][2] == -4
    assert ear["from"][1] == 14


def test_corrente_dividida_afina():
    body = _p("body", [-3, 5, -4], [3, 11, 4])
    cauda = _p("tail_1", [-1.5, 7, 4], [1.5, 10, 12], pai="body", segmentos=4)
    partes = cubificar.dividir_correntes([body, cauda], None, None, [])
    segs = [p for p in partes if p["id"].startswith("tail_")]
    assert [s["id"] for s in segs] == ["tail_1", "tail_2", "tail_3", "tail_4"]
    assert segs[0]["pai"] == "body" and segs[1]["pai"] == "tail_1"
    assert segs[0]["from"][2] == 4 and segs[-1]["to"][2] == 12
    larguras = [s["to"][0] - s["from"][0] for s in segs]
    assert larguras[0] >= larguras[-1] and larguras[-1] >= 1


def test_corrente_sem_segmentos_usa_a_categoria():
    body = _p("body", [-3, 5, -4], [3, 11, 4])
    cauda = _p("tail_1", [-1, 7, 4], [1, 10, 16], pai="body")
    partes = cubificar.dividir_correntes([body, cauda], {"plano": "bípede com cauda", "nicho": "dragão"}, "final", [])
    assert len([p for p in partes if p["id"].startswith("tail_")]) == 6  # dragão final: 6 segmentos


def test_pivo_na_junta():
    body = _p("body", [-3, 5, -4], [3, 11, 4])
    leg = _p("leg_left", [-3, 0, -1], [-1, 5, 1], pai="body")
    head = _p("head", [-3, 8, -10], [3, 14, -4], pai="body")
    assert cubificar.pivo(leg, body) == [-2, 5, 0]
    assert cubificar.pivo(head, body) == [0, 11, -4]


def test_locators_padrao():
    partes = [_p("body", [-3, 5, -4], [3, 11, 4]), _p("head", [-3, 8, -10], [3, 14, -4], pai="body"),
              _p("snout", [-1, 8, -12], [1, 10, -10], pai="head"),
              _p("leg_front_left", [-3, 0, -3], [-1, 5, -1], pai="body"), _p("tail_1", [-1, 8, 4], [1, 10, 9], pai="body"),
              _p("tail_2", [-1, 8, 9], [1, 10, 13], pai="tail_1")]
    locs = {loc["nome"]: loc for loc in rig.locators(partes)}
    assert {"loc_head_look", "loc_mouth", "loc_foot_front_left", "loc_tail_tip", "loc_center", "loc_top", "loc_ground"} <= set(locs)
    assert locs["loc_mouth"]["osso"] == "snout" and locs["loc_mouth"]["posicao"][2] == -12
    assert locs["loc_foot_front_left"]["posicao"][1] == 0
    assert locs["loc_tail_tip"]["posicao"][2] == 13 and locs["loc_tail_tip"]["osso"] == "tail_2"
    assert locs["loc_ground"]["posicao"][1] == 0


# ---------- integração com o motor ----------

pytest_motor = pytest.mark.skipif(not motor.disponivel(), reason="motor headless não instalado")


@pytest.fixture(scope="module")
def cubificadas():
    sinteticos.construir_todas()
    saida = {}
    for nome in sinteticos.NOMES:
        destino = sinteticos.SAIDA / "_teste-cubificar" / nome
        info = preparar.preparar_estagio(sinteticos.pasta_ficha(nome), "e1", destino / "preparo")
        leitura = sinteticos.leitura_da_verdade(nome, info, ruido=1.0, semente=0)
        d = sinteticos.carregar(nome)
        verdade = bbmodelo.ler(sinteticos.SAIDA / nome / "e1" / f"{nome}-e1.bbmodel")
        lo, hi = bbmodelo.limites(verdade)
        med = medir.medir(leitura, medir.carregar_mascaras(destino / "preparo"), float(hi[1] - lo[1]),
                          categoria=d["categoria"], cores=medir.carregar_cores(destino / "preparo"))
        plano, avisos = cubificar.plano_de_cubos(med, f"{nome}-e1", d["papeis_cor"], d["categoria"], d["estagio_tabela"], "1º de 3")
        arquivo, _, _ = cubificar.construir(plano, destino, f"{nome}-e1", {})
        saida[nome] = (arquivo, leitura, plano, verdade)
    yield saida
    shutil.rmtree(sinteticos.SAIDA / "_teste-cubificar", ignore_errors=True)


def _proporcoes(modelo):
    lo, hi = bbmodelo.limites(modelo)
    altura = hi[1] - lo[1]
    tam = {c.nome.removesuffix("_cube"): c.ate - c.de for c in modelo.cubos}
    p = {"cabeca_alt": tam["head"][1] / altura, "cabeca_larg": tam["head"][0] / altura,
         "corpo_alt": tam["body"][1] / altura, "corpo_compr": tam["body"][2] / altura}
    pernas = [k for k in tam if k.startswith("leg_") and k.endswith("_left")]
    if pernas:
        p["perna"] = np.mean([tam[k][1] for k in pernas]) / altura
    return p


@pytest_motor
@pytest.mark.parametrize("nome", sinteticos.NOMES)
def test_valida_com_zero_erros(nome, cubificadas):
    arquivo, leitura, plano, _ = cubificadas[nome]
    r = validar.validar(arquivo, leitura, plano)
    assert r["ok"], r["erros"]
    assert r["motor"]["avisos"] == 0, r["avisos"]


@pytest_motor
@pytest.mark.parametrize("nome", sinteticos.NOMES)
def test_proporcoes_a_ate_10_por_cento_da_verdade(nome, cubificadas):
    """Aceite da Fase 4: cabeça, corpo e membros a até 10% da verdade."""
    arquivo, _, _, verdade = cubificadas[nome]
    feito, certo = _proporcoes(bbmodelo.ler(arquivo)), _proporcoes(verdade)
    for k, v in certo.items():
        assert abs(feito[k] - v) / v <= 0.10 or abs(feito[k] - v) * 16 <= 1.0, (k, feito[k], v)


@pytest_motor
def test_mesmas_partes_e_locators(cubificadas):
    arquivo, _, plano, verdade = cubificadas["quadrupede"]
    modelo = bbmodelo.ler(arquivo)
    assert {c.nome for c in modelo.cubos} == {c.nome for c in verdade.cubos}
    assert modelo.ossos["head"].pai == "body" and modelo.ossos["body"].pai == "root"
    assert {loc.nome for loc in modelo.locators} >= {"loc_head_look", "loc_mouth", "loc_center", "loc_tail_tip"}
    assert modelo.cubo("leg_back_right_cube").mirror_uv


@pytest_motor
def test_nao_sobrescreve_edicao_a_mao(cubificadas):
    _, _, plano, _ = cubificadas["alado"]
    tmp_path = sinteticos.SAIDA / "_teste-cubificar" / "_hash"  # o motor só escreve dentro de modelos/
    shutil.rmtree(tmp_path, ignore_errors=True)
    arquivo, aviso, h = cubificar.construir(plano, tmp_path, "alado-e1", {})
    assert aviso is None
    hashes = {arquivo.name: h}
    arquivo2, aviso2, _ = cubificar.construir(plano, tmp_path, "alado-e1", hashes)
    assert arquivo2 == arquivo and aviso2 is None  # não mudou: pode regravar
    dados = json.loads(arquivo.read_text(encoding="utf-8"))
    dados["name"] = "editado"
    arquivo.write_text(json.dumps(dados), encoding="utf-8")
    arquivo3, aviso3, _ = cubificar.construir(plano, tmp_path, "alado-e1", hashes)
    assert arquivo3.name == "alado-e1.v2.bbmodel" and "editado à mão" in aviso3
    assert json.loads(arquivo.read_text(encoding="utf-8"))["name"] == "editado"


@pytest_motor
def test_validar_pega_assimetria_e_parte_faltando(cubificadas, tmp_path):
    arquivo, leitura, plano, _ = cubificadas["quadrupede"]
    modelo = bbmodelo.ler(arquivo)
    for c in modelo.cubos:
        if c.nome == "leg_front_right_cube":
            c.ate[0] += 1
    leitura = json.loads(json.dumps(leitura))
    leitura["partes"].append({"id": "horn_left", "pai": "head", "tipo": "volume", "simetria": "esquerda", "caixas": {"frente": [0, 0, 1, 1]}})
    erros, _, _ = validar.verificacoes_proprias(modelo, leitura, plano)
    codigos = {e["codigo"] for e in erros}
    assert {"simetria", "parte_faltando"} <= codigos


@pytest_motor
def test_cli_do_preparo_a_folha(capsys):
    ficha = sinteticos.pasta_ficha("alado")
    nome = ficha.name
    try:
        assert cli.main(["ficha", str(ficha)]) == 0
        assert cli.main(["preparar", str(ficha)]) == 0
        destino = MODELOS / nome / "e1"
        info = json.loads((destino / "preparo" / "preparo.json").read_text(encoding="utf-8"))
        (destino / "leitura.json").write_text(json.dumps(sinteticos.leitura_da_verdade("alado", info, 1.0, 2)), encoding="utf-8")
        for etapa in ("medir", "cubificar", "validar", "folha"):
            assert cli.main([etapa, str(ficha)]) == 0, etapa
        texto = capsys.readouterr().out
        assert "PARE" not in texto  # sintética não para na folha
        with Image.open(destino / "folha.png") as im:
            assert max(im.size) <= 768
        rel = json.loads((destino / "relatorio.json").read_text(encoding="utf-8"))
        assert all(rel["etapas"][e]["ok"] for e in ("preparar", "medir", "cubificar", "validar", "folha"))
        assert rel["hashes"]
    finally:
        shutil.rmtree(MODELOS / nome, ignore_errors=True)
