import pytest

from criaturas.cli import main


def test_help_responde(capsys):
    with pytest.raises(SystemExit) as saida:
        main(["--help"])
    assert saida.value.code == 0
    assert "criaturas" in capsys.readouterr().out


def test_sem_argumentos_mostra_ajuda(capsys):
    assert main([]) == 0
    assert "usage" in capsys.readouterr().out
