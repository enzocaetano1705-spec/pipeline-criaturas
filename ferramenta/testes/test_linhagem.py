import json
import shutil

import pytest
from PIL import Image

from criaturas import bbmodelo, cli, linhagem, motor, sinteticos
from criaturas.caminhos import MODELOS

pytestmark = pytest.mark.skipif(not motor.disponivel(), reason="motor headless não instalado")


def _estagios(arquivos):
    return [{"id": e, "modelo": bbmodelo.ler(a), "estagio_cobblemon": sinteticos.COBBLEMON[e]} for e, a in arquivos.items()]


@pytest.fixture(scope="module")
def linhagens():
    return {"normal": sinteticos.construir_linhagem(False), "invertida": sinteticos.construir_linhagem(True)}


def test_linhagem_normal_passa(linhagens):
    r = linhagem.avaliar(_estagios(linhagens["normal"]), "canídeo")
    assert r["veredito"] == "ok", r["avisos"]
    assert all(p["itens"]["cabeca_vol_delta"] < 0 for p in r["pares"])


def test_linhagem_invertida_da_erro(linhagens):
    """Aceite da Fase 7: uma linhagem sintética invertida dá erro."""
    r = linhagem.avaliar(_estagios(linhagens["invertida"]), "canídeo")
    assert r["veredito"] == "erro"
    assert any(e["codigo"] == "altura" for e in r["erros"])


def test_cabeca_que_cresce_avisa_mas_peixe_e_excecao():
    a = {"altura": 10, "cabeca_vol": 0.3, "olho_alt": 0.1, "cubos": 20, "andar_s": 1.33, "ereto": 1}
    b = {"altura": 18, "cabeca_vol": 0.35, "olho_alt": 0.08, "cubos": 26, "andar_s": 1.5, "ereto": 1}
    assert any(m["codigo"] == "cabeca" for m in linhagem.comparar(a, b, "1º de 3 → 2º de 3", "canídeo")["avisos"])
    assert not any(m["codigo"] == "cabeca" for m in linhagem.comparar(a, b, "1º de 3 → 2º de 3", "peixe/aquático")["avisos"])


def test_andar_mais_rapido_avisa():
    a = {"altura": 10, "cabeca_vol": 0.3, "olho_alt": 0.1, "cubos": 20, "andar_s": 1.5, "ereto": 1}
    b = {"altura": 18, "cabeca_vol": 0.2, "olho_alt": 0.08, "cubos": 26, "andar_s": 1.0, "ereto": 1}
    assert any(m["codigo"] == "andar" for m in linhagem.comparar(a, b, None)["avisos"])


def test_sobreposicao_de_paleta():
    assert linhagem.sobreposicao(["#d9772b", "#5a3520"], ["#da782c", "#5b3621", "#ffffff"]) == 1.0
    assert linhagem.sobreposicao(["#d9772b", "#5a3520"], ["#2040ff"]) == 0.0
    assert linhagem.sobreposicao([], ["#2040ff"]) is None


def test_cli_linhagem_grava_relatorio_e_imagem(linhagens, tmp_path, capsys):
    pasta = tmp_path / "_teste-linhagem"
    pasta.mkdir()
    destino = MODELOS / "_teste-linhagem"
    shutil.rmtree(destino, ignore_errors=True)
    try:
        estagios = []
        for eid, arquivo in linhagens["normal"].items():
            (destino / eid).mkdir(parents=True)
            shutil.copy(arquivo, destino / eid / arquivo.name)
            estagios.append({"id": eid, "estagio": f"{eid[1]} de 3", "estagio_tabela": None,
                             "estagio_cobblemon": sinteticos.COBBLEMON[eid], "imagens": {}})
        entrada = {"nome": "teste-linhagem", "status": "pronta-para-modelagem", "destino": ["roblox"],
                   "estilo": "cobblemon", "pasta": "x", "estagios": estagios}
        (destino / "entrada.json").write_text(json.dumps(entrada, ensure_ascii=False), encoding="utf-8")
        assert cli.main(["linhagem", str(pasta)]) == 0
        texto = capsys.readouterr().out
        assert "OK" in texto and len(texto.splitlines()) <= 20
        r = json.loads((destino / "linhagem.json").read_text(encoding="utf-8"))
        assert r["veredito"] == "ok" and len(r["pares"]) == 2
        with Image.open(destino / "linhagem.png") as im:
            assert im.height == 360 and im.width > 360
    finally:
        shutil.rmtree(destino, ignore_errors=True)
