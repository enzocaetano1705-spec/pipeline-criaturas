import json
import shutil

import numpy as np
import pytest

from criaturas import animar, bbmodelo, cli, motor, sinteticos
from criaturas.caminhos import MODELOS

pytestmark = pytest.mark.skipif(not motor.disponivel(), reason="motor headless não instalado")


@pytest.fixture(scope="module")
def cubificadas():
    """As 3 sintéticas da leitura (ruído ±1) até o cubificar, em modelos/_sint-<nome>/."""
    sinteticos.construir_todas()
    saida = {}
    for nome in sinteticos.NOMES:
        ficha = sinteticos.pasta_ficha(nome)
        alvo = MODELOS / ficha.name
        shutil.rmtree(alvo, ignore_errors=True)
        assert cli.main(["ficha", str(ficha)]) == 0 and cli.main(["preparar", str(ficha)]) == 0
        info = json.loads((alvo / "e1" / "preparo" / "preparo.json").read_text(encoding="utf-8"))
        (alvo / "e1" / "leitura.json").write_text(json.dumps(sinteticos.leitura_da_verdade(nome, info, 1.0, 1)), encoding="utf-8")
        assert cli.main(["medir", str(ficha)]) == 0 and cli.main(["cubificar", str(ficha)]) == 0
        saida[nome] = (ficha, next((alvo / "e1").glob("*.bbmodel")))
    yield saida
    for nome in sinteticos.NOMES:
        shutil.rmtree(MODELOS / sinteticos.pasta_ficha(nome).name, ignore_errors=True)


def test_rig_le_os_papeis(cubificadas):
    rig = animar.Rig.do_modelo(bbmodelo.ler(cubificadas["quadrupede"][1]))
    assert set(rig.pernas) == {"leg_front_left", "leg_front_right", "leg_back_left", "leg_back_right"}
    assert rig.cauda == ["tail_1", "tail_2"] and rig.head == "head" and len(rig.olhos) == 2
    alado = animar.Rig.do_modelo(bbmodelo.ler(cubificadas["alado"][1]))
    assert set(alado.asas) == {"wing_left", "wing_right"}


def test_chaves_assadas_loop_sem_emenda(cubificadas):
    modelo = bbmodelo.ler(cubificadas["bipede-cauda"][1])
    rig = animar.Rig.do_modelo(modelo)
    clip = animar.walk(rig, "bípede com cauda", 1.5)
    chaves = animar.assar(clip, modelo)
    for osso, canais in chaves.items():
        for canal, lista in canais.items():
            assert lista[0][1] == lista[-1][1], (osso, canal)
            assert all(isinstance(x, float) for _, v in lista for x in v)  # números: nada de Molang
            assert lista[-1][0] == pytest.approx(1.5)
            assert max(b[0] - a[0] for a, b in zip(lista, lista[1:])) <= 0.1 + 1e-6


def test_walk_mantem_o_pe_no_chao(cubificadas):
    modelo = bbmodelo.ler(cubificadas["quadrupede"][1])
    clip = animar.walk(animar.Rig.do_modelo(modelo), "quadrúpede", 1.33)
    chaves = animar.assar(clip, modelo)
    nomes = {"rotation": "rotacao", "position": "posicao", "scale": "escala"}
    n = len(next(iter(next(iter(chaves.values())).values())))
    for i in range(n):
        pose = {o: {nomes[c]: np.array(v[i][1]) for c, v in cs.items()} for o, cs in chaves.items()}
        assert animar._minimo_y(modelo, pose) == pytest.approx(0.0, abs=0.02)


@pytest.mark.parametrize("nome", sinteticos.NOMES)
def test_idle_walk_blink_sem_erros(nome, cubificadas):
    """Aceite da Fase 6: idle, walk e blink com 0 erros nas 3 sintéticas."""
    ficha, arquivo = cubificadas[nome]
    assert cli.main(["animar", str(ficha)]) == 0
    modelo = bbmodelo.ler(arquivo)
    nomes = {a["name"] for a in modelo.animacoes}
    assert {"idle", "walk", "blink"} <= nomes
    erros, avisos, mensagens = animar.validar_animacoes(arquivo)
    assert erros == 0 and avisos == 0, mensagens
    walk = next(a for a in modelo.animacoes if a["name"] == "walk")
    chaves = [k for an in walk["animators"].values() for k in an["keyframes"]]
    assert chaves and all(k["interpolation"] == "catmullrom" for k in chaves)
    assert (arquivo.parent / "animacoes.json").exists()


def test_alado_tem_fly_e_animar_de_novo_nao_duplica(cubificadas):
    ficha, arquivo = cubificadas["alado"]
    assert cli.main(["animar", str(ficha)]) == 0
    assert cli.main(["animar", str(ficha)]) == 0
    nomes = [a["name"] for a in bbmodelo.ler(arquivo).animacoes]
    assert "fly" in nomes and nomes.count("walk") == 1


def test_validador_pega_o_pe_afundando(cubificadas):
    """O walk do protótipo afundava o pé 0,6 unidade: a validação tem que acusar."""
    _, arquivo = cubificadas["quadrupede"]
    motor.editar(arquivo, [{"op": "add_animation", "name": "walk_ruim", "length": 1, "loop": "loop"},
                           {"op": "set_keyframe", "animation": "walk_ruim", "bone": "body", "channel": "position", "time": 0, "value": [0, 0, 0]},
                           {"op": "set_keyframe", "animation": "walk_ruim", "bone": "body", "channel": "position", "time": 0.1, "value": [0, -0.6, 0]},
                           {"op": "set_keyframe", "animation": "walk_ruim", "bone": "body", "channel": "position", "time": 1, "value": [0, 0, 0]}])
    _, _, mensagens = animar.validar_animacoes(arquivo)
    assert any("ground_sink" in m and "walk_ruim" in m for m in mensagens), mensagens
    motor.editar(arquivo, [{"op": "remove_animation", "animation": "walk_ruim"}])


def test_sem_olhos_nao_tem_blink():
    rig = animar.Rig()
    lista, avisos = animar.clipes(rig, "cabeça-corpo", "inicial", ("blink",))
    assert lista == [] and avisos[0]["codigo"] == "sem_olhos"


def test_rig_reposiciona_locator_e_respeita_edicao_a_mao(cubificadas):
    from criaturas import rig

    ficha, arquivo = cubificadas["bipede-cauda"]
    motor.editar(arquivo, [{"op": "remove_node", "target": "loc_mouth"}])
    assert cli.main(["rig", str(ficha)]) == 1  # o arquivo mudou fora do pipeline: a CLI não mexe
    r = rig.sincronizar(arquivo)
    assert r["criados"] == ["loc_mouth"]
    assert "loc_mouth" in {loc.nome for loc in bbmodelo.ler(arquivo).locators}
