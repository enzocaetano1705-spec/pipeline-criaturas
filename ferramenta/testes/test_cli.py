import json

import pytest

from criaturas import cli
from criaturas.caminhos import MODELOS


def test_help_responde(capsys):
    with pytest.raises(SystemExit) as saida:
        cli.main(["--help"])
    assert saida.value.code == 0
    texto = capsys.readouterr().out
    for nome, _ in cli.ETAPAS:
        assert nome in texto
    assert "medidas" in texto


def test_sem_argumentos_mostra_ajuda(capsys):
    assert cli.main([]) == 0
    assert "usage" in capsys.readouterr().out


def test_esboco_avisa_e_grava_relatorio(capsys, tmp_path):
    pasta = tmp_path / "_teste-esboco"
    pasta.mkdir()
    destino = MODELOS / "_teste-esboco"
    try:
        assert cli.main(["exportar", str(pasta), "--estagio", "e2"]) == 2
        assert "ainda não implementado" in capsys.readouterr().out
        rel = json.loads((destino / "e2" / "relatorio.json").read_text(encoding="utf-8"))
        assert rel["etapas"]["exportar"]["ok"] is False
    finally:
        import shutil
        shutil.rmtree(destino, ignore_errors=True)


def test_medidas_dragao_final(capsys):
    assert cli.main(["medidas", "dragão", "final"]) == 0
    texto = capsys.readouterr().out
    assert "nicho › dragão — final" in texto
    assert "3.4 / 3.7 / 4.73" in texto
    assert len(texto.splitlines()) <= 20


def test_medidas_aceita_sem_acento_e_estagio_da_ficha(capsys):
    assert cli.main(["medidas", "quadrupede", "1 de 3"]) == 0
    assert "plano › quadrúpede — inicial" in capsys.readouterr().out


def test_medidas_poucos_dados_cai_para_geral(capsys):
    assert cli.main(["medidas", "quadrúpede", "lendário"]) == 0
    assert "poucos dados" in capsys.readouterr().out


def test_medidas_categoria_desconhecida(capsys):
    assert cli.main(["medidas", "unicórnio"]) == 1
    assert "nichos:" in capsys.readouterr().out
