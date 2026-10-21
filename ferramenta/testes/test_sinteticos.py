import json

import pytest

from criaturas import contratos, motor, ops, sinteticos


@pytest.mark.parametrize("nome", sinteticos.NOMES)
def test_direita_espelha_esquerda(nome):
    d = sinteticos.carregar(nome)
    por_id = {p["id"]: p for p in d["partes"]}
    for p in d["partes"]:
        if p["simetria"] == "esquerda":
            q = por_id[p["espelho"]]
            assert q["simetria"] == "direita" and q["espelho"] == p["id"]
            assert q["from"][0] == -p["to"][0] and q["to"][0] == -p["from"][0]
            assert q["from"][1:] == p["from"][1:] and q["to"][1:] == p["to"][1:]
            assert p["to"][0] <= 0, "o lado esquerdo da criatura fica em -X"


@pytest.mark.parametrize("nome", sinteticos.NOMES)
def test_plano_valido_e_uv_sem_sobreposicao(nome):
    plano = sinteticos.plano_cubos(sinteticos.carregar(nome))
    assert contratos.problemas("plano_cubos", plano) == []
    largura = plano["resolucao"]["largura"]
    ocupado = {}
    for c in plano["cubos"]:
        if c.get("mirror_uv"):
            continue
        w, h = ops.tamanho_box_uv(c["from"], c["to"])
        u, v = c["uv_offset"]
        assert u + w <= largura and v + h <= plano["resolucao"]["altura"]
        for x in range(u, u + w):
            for y in range(v, v + h):
                assert (x, y) not in ocupado, f"{c['nome']} sobrepõe {ocupado[(x, y)]}"
                ocupado[(x, y)] = c["nome"]


def test_gerar_ops_recusa_osso_inexistente():
    plano = sinteticos.plano_cubos(sinteticos.carregar("quadrupede"))
    plano["cubos"][0]["osso"] = "nao_existe"
    with pytest.raises(ValueError, match="nao_existe"):
        ops.gerar_ops(plano)


@pytest.mark.skipif(not motor.disponivel(), reason="motor headless não instalado")
@pytest.mark.parametrize("nome", sinteticos.NOMES)
def test_constroi_e_valida_sem_erros(nome, tmp_path):
    destino = sinteticos.SAIDA / f"_teste-{nome}"
    arquivo = sinteticos.construir(nome, destino)
    erros, avisos, mensagens = motor.resumo_validacao(motor.validar(arquivo))
    assert erros == 0 and avisos == 0, mensagens
    modelo = json.loads(arquivo.read_text(encoding="utf-8"))
    n_partes = len(sinteticos.carregar(nome)["partes"])
    assert len([e for e in modelo["elements"] if e.get("type") == "cube"]) == n_partes
    assert (destino / "verdade.json").exists()
