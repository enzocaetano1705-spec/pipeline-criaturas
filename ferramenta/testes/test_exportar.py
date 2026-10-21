import json
import shutil

import pytest

from criaturas import bbmodelo, cli, desktop, exportar, motor, sinteticos
from criaturas.caminhos import MODELOS

pytestmark = pytest.mark.skipif(not motor.disponivel(), reason="motor headless não instalado")
precisa_desktop = pytest.mark.skipif(not desktop.respondendo(), reason="Blockbench desktop fechado ou sem o plugin MCP")


@pytest.fixture(scope="module")
def animada():
    """Bípede com cauda da leitura até o animar, em modelos/_sint-bipede-cauda/."""
    sinteticos.construir_todas()
    ficha = sinteticos.pasta_ficha("bipede-cauda")
    alvo = MODELOS / ficha.name
    shutil.rmtree(alvo, ignore_errors=True)
    assert cli.main(["ficha", str(ficha)]) == 0 and cli.main(["preparar", str(ficha)]) == 0
    info = json.loads((alvo / "e1" / "preparo" / "preparo.json").read_text(encoding="utf-8"))
    (alvo / "e1" / "leitura.json").write_text(json.dumps(sinteticos.leitura_da_verdade("bipede-cauda", info, 1.0, 1)), encoding="utf-8")
    for etapa in ("medir", "cubificar", "texturizar"):
        assert cli.main([etapa, str(ficha)]) == 0, etapa
    assert cli.main(["animar", str(ficha), "--so-base"]) == 0
    yield ficha, alvo
    shutil.rmtree(alvo, ignore_errors=True)


def test_animacoes_bedrock_formato_e_sinais(animada):
    _, alvo = animada
    arquivo = next((alvo / "e1").glob("*.bbmodel"))
    modelo = bbmodelo.ler(arquivo)
    saida = exportar.animacoes_bedrock(modelo, "teste")
    assert saida["format_version"] == "1.8.0"
    walk = saida["animations"]["animation.teste.walk"]
    assert walk["loop"] is True and walk["animation_length"] == pytest.approx(1.5)
    blink = saida["animations"]["animation.teste.blink"]
    assert "loop" not in blink
    chave = next(iter(walk["bones"]["leg_left"]["rotation"].values()))
    assert chave["lerp_mode"] == "catmullrom" and len(chave["post"]) == 3
    # mesma regra de sinal que o bbmodel_convert_legacy do motor (layout 4.x = valores do Bedrock)
    legado = arquivo.with_name("legado.bbmodel")
    motor.chamar("bbmodel_convert_legacy", {"file": motor.relativo(arquivo), "output": motor.relativo(legado)})
    dados = json.loads(legado.read_text(encoding="utf-8"))
    anim = next(a for a in dados["animations"] if a["name"] == "walk")
    k = next(k for an in anim["animators"].values() if an["name"] == "leg_left" for k in an["keyframes"]
             if k["channel"] == "rotation" and abs(float(k["data_points"][0]["x"])) > 1)
    esperado = [float(k["data_points"][0][e]) for e in "xyz"]
    tempo = f"{round(float(k['time']), 4):g}"
    tempo = tempo if "." in tempo else tempo + ".0"
    assert walk["bones"]["leg_left"]["rotation"][tempo]["post"] == pytest.approx(esperado, abs=1e-3)
    legado.unlink()


def test_exporta_minecraft_e_geckolib(animada, capsys):
    ficha, alvo = animada
    assert cli.main(["exportar", str(ficha), "--destino", "minecraft", "--geckolib"]) == 0
    mc = alvo / "export" / "minecraft"
    geo = json.loads((mc / "sint_bipede_cauda_e1.geo.json").read_text(encoding="utf-8"))
    assert geo["minecraft:geometry"][0]["description"]["identifier"] == "geometry.sint_bipede_cauda_e1"
    nomes = {b["name"] for b in geo["minecraft:geometry"][0]["bones"]}
    assert {"root", "body", "head", "tail_3"} <= nomes
    assert (mc / "sint_bipede_cauda_e1.animation.json").exists() and (mc / "sint_bipede_cauda_e1.png").exists()
    for sub in ("geo", "animations", "textures"):
        assert any((alvo / "export" / "geckolib" / sub).iterdir())


@precisa_desktop
def test_exporta_roblox_glb_valido(animada):
    """Aceite da Fase 8: .glb válido (Khronos sem erros), até 20 mil triângulos, ossos e locators com nome."""
    ficha, alvo = animada
    assert cli.main(["exportar", str(ficha), "--destino", "roblox"]) == 0
    glb = alvo / "export" / "roblox" / "sint-bipede-cauda-e1.glb"
    modelo = bbmodelo.ler(next((alvo / "e1").glob("*.bbmodel")))
    erros, avisos, resumo = exportar.verificar_glb(glb, modelo)
    assert erros == [] and resumo["validador"]["erros"] == 0
    assert 0 < resumo["triangulos"] <= exportar.MAX_TRIANGULOS
    nos = {n.get("name") for n in exportar.json_do_glb(glb)["nodes"]}
    assert set(modelo.ossos) - {"root"} <= nos
    assert {loc.nome for loc in modelo.locators} <= nos
    assert resumo["animacoes"] == 3  # --so-base: idle, walk, blink
    # a cópia para o Roblox leva a textura ×8
    copia = bbmodelo.ler(next((alvo / "export" / "roblox").glob("sint-bipede-cauda-e1.*.bbmodel")))
    assert copia.textura.size == (modelo.resolucao[0] * 8, modelo.resolucao[1] * 8)
