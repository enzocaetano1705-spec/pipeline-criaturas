"""Fluxo pelo chat: imagens anexadas -> criatura -> folha; ajustes por código; edições à mão adotadas."""

import base64
import json
import shutil

import pytest
from PIL import Image

from criaturas import bbmodelo, chat, cli, estado, motor, sinteticos
from criaturas.caminhos import MODELOS
from criaturas.ficha import ler_ficha

pytestmark = pytest.mark.skipif(not motor.disponivel(), reason="motor headless não instalado")
NOME = "zz-teste-chat"


@pytest.fixture(scope="module")
def criatura(tmp_path_factory):
    """Cria a criatura como o chat faria (imagens soltas, de outro lugar) e roda até o animar."""
    sinteticos.construir_todas()
    origem = sinteticos.pasta_ficha("alado")
    downloads = tmp_path_factory.mktemp("downloads")
    anexos = {}
    for vista in ("conceito", "frente", "lado"):  # como viriam do chat: nomes quaisquer, outro formato
        arq = downloads / f"Gemini_Generated_{vista}.webp"
        Image.open(origem / f"e1-{vista}.png").save(arq, lossless=True)
        anexos[vista] = str(arq)
    raiz = tmp_path_factory.mktemp("docs-criaturas")
    antigo = chat.CRIATURAS
    chat.CRIATURAS = raiz  # não escreve em docs/criaturas de verdade
    shutil.rmtree(MODELOS / NOME, ignore_errors=True)
    assert cli.main(["nova", NOME, "--conceito", anexos["conceito"], "--frente", anexos["frente"], "--lado", anexos["lado"],
                     "--estagio-texto", "1 de 3", "--categoria", "alado › ave", "--prompt", "blue bird, plain background"]) == 0
    pasta = raiz / NOME
    assert cli.main(["tudo", str(pasta), "--ate", "preparar"]) in (0, 3)
    destino = MODELOS / NOME / "e1"
    info = json.loads((destino / "preparo" / "preparo.json").read_text(encoding="utf-8"))
    (destino / "leitura.json").write_text(json.dumps(sinteticos.leitura_da_verdade("alado", info, 1.0, 0)), encoding="utf-8")
    assert cli.main(["tudo", str(pasta), "--ate", "folha"]) == 3  # criatura real: para na folha
    assert cli.main(["tudo", str(pasta), "--ate", "animar", "--folha-aprovada"]) == 0
    yield pasta, destino
    chat.CRIATURAS = antigo
    shutil.rmtree(MODELOS / NOME, ignore_errors=True)


def test_nova_monta_pasta_e_ficha(criatura):
    pasta, _ = criatura
    for vista in ("conceito", "frente", "lado"):
        assert (pasta / f"e1-{vista}.png").exists()
    entrada = ler_ficha(pasta)
    assert entrada["status"] == "pronta-para-modelagem" and entrada["erros"] == []
    e1 = entrada["estagios"][0]
    assert e1["categoria_confirmada"] == {"plano": "alado", "nicho": "ave"} and e1["prompt"] == "blue bird, plain background"


def test_nova_acrescenta_estagio_sem_perder_o_primeiro(criatura, tmp_path):
    pasta, _ = criatura
    copia = tmp_path / NOME
    shutil.copytree(pasta, copia)
    antigo = chat.CRIATURAS
    chat.CRIATURAS = tmp_path
    try:
        assert cli.main(["nova", NOME, "--estagio", "e2", "--conceito", str(pasta / "e1-conceito.png"), "--estagio-texto", "2 de 3"]) == 0
    finally:
        chat.CRIATURAS = antigo
    estagios = ler_ficha(copia)["estagios"]
    assert [e["id"] for e in estagios] == ["e1", "e2"]
    assert estagios[0]["prompt"] == "blue bird, plain background"


def test_nova_nao_mexe_em_rascunho(tmp_path):
    (tmp_path / "rasc").mkdir()
    (tmp_path / "rasc" / "ficha.md").write_text("---\nnome: rasc\nstatus: rascunho\n---\n", encoding="utf-8")
    antigo = chat.CRIATURAS
    chat.CRIATURAS = tmp_path
    try:
        assert cli.main(["nova", "rasc", "--conceito", "x.png"]) == 1
    finally:
        chat.CRIATURAS = antigo


def test_ver_e_quadro(criatura, capsys):
    pasta, destino = criatura
    assert cli.main(["ver", str(pasta)]) == 0
    texto = capsys.readouterr().out
    assert "wing_left" in texto and len(texto.splitlines()) <= 20
    with Image.open(destino / "ver.png") as im:
        assert im.size == (768, 384)
    assert cli.main(["quadro", str(pasta), "--anim", "walk", "--tempo", "0.5"]) == 0
    assert (destino / "quadro-walk-0_50.png").exists()
    assert "ponto mais baixo" in capsys.readouterr().out
    assert cli.main(["quadro", str(pasta), "--anim", "nao-existe"]) == 1


def test_edicao_a_mao_e_adotada_e_protegida(criatura, capsys):
    pasta, destino = criatura
    arquivo = next(destino.glob("*.bbmodel"))
    modelo = bbmodelo.ler(arquivo)
    perna = modelo.cubo("leg_left_cube")
    # o "usuário" no Blockbench: move a perna, muda o idle e repinta a textura
    motor.editar(arquivo, [{"op": "update_node", "target": "leg_left_cube", "from": (perna.de + [0, 0, 1]).tolist(), "to": (perna.ate + [0, 0, 1]).tolist()},
                           {"op": "set_keyframe", "animation": "idle", "bone": "head", "channel": "rotation", "time": 0.5, "value": [30, 0, 0]},
                           {"op": "update_texture", "target": 0, "source": "data:image/png;base64," + base64.b64encode(_png_vermelho()).decode(), "width": 64, "height": 64}])
    capsys.readouterr()
    assert cli.main(["adotar", str(pasta)]) == 0
    texto = capsys.readouterr().out
    assert "leg_left_cube: movido" in texto and "animação idle alterada" in texto and "textura alterada" in texto
    prot = estado.protegido(destino)
    assert prot["textura"] and "idle" in prot["animacoes"]
    assert cli.main(["texturizar", str(pasta)]) == 1  # não repinta por cima da pintura à mão
    assert cli.main(["animar", str(pasta), "--so-base"]) == 0
    assert "não regero idle" in capsys.readouterr().out
    idle = next(a for a in bbmodelo.ler(arquivo).animacoes if a["name"] == "idle")
    assert any(k["time"] == 0.5 and float(k["data_points"][0]["x"]) == 30
               for an in idle["animators"].values() for k in an["keyframes"])
    assert bbmodelo.ler(arquivo).cubo("leg_left_cube").de[2] == perna.de[2] + 1  # a perna continua onde o usuário pôs
    hist = estado.ler_historico(destino)
    assert any(h["origem"] == "mao" for h in hist)


def test_aplicar_correcao_por_codigo(criatura, tmp_path, capsys):
    pasta, destino = criatura
    ops = tmp_path / "ops.json"
    # "falta uma crista": a IA escreve o lote e aplica
    ops.write_text(json.dumps([{"op": "add_group", "name": "crest", "origin": [0, 16, -2], "parent": "head"},
                               {"op": "add_cube", "name": "crest_cube", "from": [-0.5, 15, -3], "to": [0.5, 18, 0], "parent": "crest", "box_uv": True}]),
                   encoding="utf-8")
    capsys.readouterr()
    assert cli.main(["aplicar", str(pasta), str(ops), "--motivo", "faltava a crista"]) == 0
    texto = capsys.readouterr().out
    assert "cubo novo crest_cube" in texto and "0 erros" in texto
    hist = estado.ler_historico(destino, 1)[0]
    assert hist["origem"] == "ia" and hist["texto"] == "faltava a crista"
    assert (MODELOS / NOME / "e1" / hist["lote"].split("/e1/")[1]).exists()
    assert cli.main(["adotar", str(pasta)]) == 0
    assert "nada a adotar" in capsys.readouterr().out  # o que o pipeline escreveu já é o estado conhecido
    ruim = tmp_path / "ruim.json"
    ruim.write_text(json.dumps([{"op": "remove_node", "target": "nao_existe"}]), encoding="utf-8")
    assert cli.main(["aplicar", str(pasta), str(ruim)]) == 1
    assert "nada foi mudado" in capsys.readouterr().out


def _png_vermelho() -> bytes:
    import io

    buf = io.BytesIO()
    Image.new("RGBA", (64, 64), (255, 0, 0, 255)).save(buf, "PNG")
    return buf.getvalue()


def test_nova_aceita_prancha(tmp_path, capsys):
    from test_prancha import prancha_sintetica

    arq = tmp_path / "prancha.webp"
    prancha_sintetica().save(arq, lossless=True)
    antigo = chat.CRIATURAS
    chat.CRIATURAS = tmp_path / "criaturas"
    try:
        assert cli.main(["nova", "zz-prancha", "--prancha", str(arq), "--estagio-texto", "1 de 3"]) == 0
    finally:
        chat.CRIATURAS = antigo
    pasta = tmp_path / "criaturas" / "zz-prancha"
    for v in ("conceito", "frente", "lado", "costas", "3-4"):
        assert (pasta / f"e1-{v}.png").exists()
    assert "e1-3-4.png" in (pasta / "ficha.md").read_text(encoding="utf-8")
