import numpy as np
import pytest

from criaturas import bbmodelo, roblox_infra


@pytest.fixture
def corpo(tmp_path, monkeypatch):
    arquivo = tmp_path / "fonte.txt"
    arquivo.write_text("fixture")
    osso = bbmodelo.Osso("body", "b", None, np.zeros(3), np.array([0, 0, 30]))
    asa = bbmodelo.Osso("wing_left", "w", "body", np.zeros(3), np.zeros(3))
    def cubo(nome, pai, de, ate):
        return bbmodelo.Cubo(nome, nome, pai, np.array(de, float), np.array(ate, float),
                             np.zeros(3), np.zeros(3), 0, {})
    modelo = bbmodelo.Modelo("teste", (16,16), {"body":osso, "wing_left":asa}, [
        cubo("tronco", "body", [-2,0,-3], [2,6,3]),
        cubo("pena", "body", [-100,50,0], [100,100,0]),
        cubo("asa", "wing_left", [-90,0,-40], [90,90,40]),
    ], [])
    monkeypatch.setattr(bbmodelo, "ler", lambda p: modelo)
    return arquivo, modelo


def test_corpo_fisico_exclui_planos_e_apendices_e_desfaz_giro_do_osso(corpo):
    arquivo, modelo = corpo
    p = roblox_infra.perfil_colisao(arquivo)
    assert p["min"] == [-2,0,-3] and p["max"] == [2,6,3]
    assert p["cubos"] == ["tronco"]
    modelo.cubos[1].ate *= 10
    modelo.cubos[2].ate *= 10
    assert roblox_infra.perfil_colisao(arquivo) == p


def test_perfil_exige_volume_real_e_recusa_configuracao_desconhecida(corpo):
    arquivo, modelo = corpo
    with pytest.raises(ValueError, match="ausentes"):
        roblox_infra.perfil_colisao(arquivo, nomes=["pena"])
    with pytest.raises(ValueError, match="osso"):
        roblox_infra.perfil_colisao(arquivo, osso="inexistente")
    modelo.cubos = []
    with pytest.raises(ValueError, match="nenhum volume"):
        roblox_infra.perfil_colisao(arquivo)


def test_receita_preserva_escala_quando_pedido_e_carrega_perfil(corpo):
    arquivo, _ = corpo
    p = roblox_infra.perfil_colisao(arquivo)
    item = {"id":"Teste_F1", "escala_studio":3, "colisao":p}
    template = 'local NOME = "Pavao_F2"\nlocal ESCALA = nil\nlocal PERFIL_JSON = nil\n'
    mantem = roblox_infra.receita_preparo(template, item, True)
    assert 'local NOME = "Teste_F1"' in mantem and "local ESCALA = nil" in mantem
    assert '"tronco"' in mantem
    assert "local ESCALA = 3" in roblox_infra.receita_preparo(template, item)


def test_receita_recusa_revisao_desatualizada_e_outro_modelo(tmp_path):
    import copy

    (tmp_path / "fonte").write_bytes(b"fonte")
    (tmp_path / "glb").write_bytes(b"malha")
    c = {"nome":"Teste", "fonte":"fonte", "arquivo":"glb"}
    item = {"versao":1, "id":"Teste", "fonte":"fonte", "arquivo":"glb",
            "config_sha256":roblox_infra.hash_config(c),
            "fonte_sha256":roblox_infra.hash_arquivo(tmp_path/"fonte"),
            "glb_sha256":roblox_infra.hash_arquivo(tmp_path/"glb")}
    item["colisao"] = {k:v for k,v in item.items() if k in ("fonte_sha256","glb_sha256")}
    roblox_infra.conferir_manifesto(tmp_path,c,item)
    outro = copy.deepcopy(item); outro["id"] = "Outro"
    with pytest.raises(ValueError, match="outra criatura"):
        roblox_infra.conferir_manifesto(tmp_path,c,outro)
    outro = copy.deepcopy(item); outro["colisao"]["fonte_sha256"] = "velha"
    with pytest.raises(ValueError, match="perfil físico"):
        roblox_infra.conferir_manifesto(tmp_path,c,outro)
    c2 = dict(c,espelhar_atlas=True)
    with pytest.raises(ValueError, match="configuração mudou"):
        roblox_infra.conferir_manifesto(tmp_path,c2,item)
    (tmp_path / "glb").write_bytes(b"malha corrigida")
    with pytest.raises(ValueError, match="exportação mudou"):
        roblox_infra.conferir_manifesto(tmp_path,c,item)
