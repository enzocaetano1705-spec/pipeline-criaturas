import pytest

from criaturas import tabelas


def test_resolve_prefixo_unico():
    assert tabelas.resolver_categoria("roedor") == ("nicho", "roedor/pequeno mamífero")
    assert tabelas.resolver_categoria("Bípede com cauda") == ("plano", "bípede com cauda")


def test_humanoide_existe_como_plano_e_nicho():
    # o nome exato resolve para o plano primeiro
    assert tabelas.resolver_categoria("humanoide")[0] == "plano"


def test_estagios_da_ficha():
    assert tabelas.resolver_estagio("2 de 3") == "meio"
    assert tabelas.resolver_estagio("bebê (pré-estágio)") == "inicial"
    assert tabelas.resolver_estagio("lendário") == "lendário"
    assert tabelas.estagio_cobblemon("3 de 3") == "3º de 3"
    with pytest.raises(KeyError):
        tabelas.resolver_estagio("quinto")


def test_mediana_cai_para_geral_com_poucos_dados():
    assert tabelas.mediana("quadrúpede", "lendário", "altura_blocos") == tabelas.faixas("quadrúpede")["altura_blocos"][1]
    assert tabelas.mediana("dragão", "final", "altura_blocos") == 3.7
