import json
import shutil

import numpy as np
import pytest
from PIL import Image

from criaturas import bbmodelo, cli, cores, motor, render, sinteticos
from criaturas import texturizar as tx
from criaturas.caminhos import MODELOS


# ---------- unidades ----------

def test_rampa_escurece_para_o_frio_e_clareia_para_o_quente():
    r = cores.rampa(np.array([200, 120, 60]))
    L = {k: cores.rgb_para_oklab(v)[0] for k, v in r.items()}
    assert L[-1] < L[0] < L[1]


def test_paleta_no_limite_e_junta_quase_iguais():
    rng = np.random.default_rng(0)
    base = np.array([[200, 50, 50], [50, 200, 50], [50, 50, 200], [220, 220, 220], [30, 30, 30], [240, 200, 0], [120, 0, 160], [0, 160, 160]])
    pixels = np.concatenate([np.clip(b + rng.normal(0, 2, (40, 3)), 0, 255) for b in base])
    pal, papeis = cores.paleta(pixels)
    assert len(pal) <= 7 and papeis.count("base") <= 5 and papeis.count("destaque") <= 2
    quase = np.concatenate([np.full((50, 3), [200, 50, 50]), np.full((50, 3), [202, 51, 50])])
    assert len(cores.paleta(quase)[0]) == 1


def test_versao_roblox_amplia_e_faz_margem():
    tex = np.zeros((4, 4, 4), np.uint8)
    tex[1, 1] = (255, 0, 0, 255)
    grande = tx.versao_roblox(tex)
    assert grande.shape == (32, 32, 4)
    assert (grande[8:16, 8:16, 3] == 255).all() and tuple(grande[12, 12, :3]) == (255, 0, 0)
    assert tuple(grande[12, 7, :3]) == (255, 0, 0) and grande[12, 7, 3] == 0  # margem: cor da ilha, transparente
    assert tuple(grande[12, 4, :3]) == (0, 0, 0)  # além de 2 px, nada


def test_delta_e_identico_e_diferente():
    assert cores.delta_e([10, 20, 30], [10, 20, 30]) == pytest.approx(0)
    assert cores.delta_e([255, 0, 0], [0, 0, 255]) > 100


# ---------- integração ----------

pytestmark_motor = pytest.mark.skipif(not motor.disponivel(), reason="motor headless não instalado")


@pytest.fixture(scope="module")
def texturizadas():
    sinteticos.construir_todas()
    saida = {}
    for nome in sinteticos.NOMES:
        ficha = sinteticos.pasta_ficha(nome)
        alvo = MODELOS / ficha.name
        shutil.rmtree(alvo, ignore_errors=True)
        assert cli.main(["ficha", str(ficha)]) == 0
        assert cli.main(["preparar", str(ficha)]) == 0
        info = json.loads((alvo / "e1" / "preparo" / "preparo.json").read_text(encoding="utf-8"))
        (alvo / "e1" / "leitura.json").write_text(json.dumps(sinteticos.leitura_da_verdade(nome, info, 1.0, 1)), encoding="utf-8")
        for etapa in ("medir", "cubificar"):
            assert cli.main([etapa, str(ficha)]) == 0
        codigo = cli.main(["texturizar", str(ficha)])
        saida[nome] = (ficha, alvo / "e1", codigo)
    yield saida
    for nome in sinteticos.NOMES:
        shutil.rmtree(MODELOS / sinteticos.pasta_ficha(nome).name, ignore_errors=True)


@pytestmark_motor
@pytest.mark.parametrize("nome", sinteticos.NOMES)
def test_aceite_da_textura(nome, texturizadas):
    """Aceite da Fase 5: sem buraco em volume, cores no limite, ΔE ≤ 10 por parte."""
    _, destino, codigo = texturizadas[nome]
    assert codigo == 0
    rel = json.loads((destino / "relatorio.json").read_text(encoding="utf-8"))["etapas"]["texturizar"]
    assert rel["ok"] and rel["resumo"]["transparentes_volume"] == 0
    assert rel["resumo"]["cores"] <= 7
    assert rel["resumo"]["delta_e"] and max(rel["resumo"]["delta_e"].values()) <= 10, rel["resumo"]["delta_e"]


@pytestmark_motor
@pytest.mark.parametrize("nome", sinteticos.NOMES)
def test_textura_embutida_e_modelo_valido(nome, texturizadas):
    ficha, destino, _ = texturizadas[nome]
    arquivo = next(destino.glob("*.bbmodel"))
    modelo = bbmodelo.ler(arquivo)
    assert modelo.textura is not None and modelo.textura.size == modelo.resolucao
    assert all(f.get("texture") is not None for c in modelo.cubos for f in c.faces.values())
    erros, avisos, _ = motor.resumo_validacao(motor.validar(arquivo))
    assert erros == 0
    with Image.open(destino / "textura-roblox.png") as im:
        assert im.size == (modelo.resolucao[0] * 8, modelo.resolucao[1] * 8)
    # texturizar de novo troca a textura em vez de acumular
    assert cli.main(["texturizar", str(ficha)]) == 0
    assert len(json.loads(arquivo.read_text(encoding="utf-8"))["textures"]) == 1


@pytestmark_motor
def test_folha_usa_a_textura(texturizadas):
    ficha, destino, _ = texturizadas["quadrupede"]
    assert cli.main(["folha", str(ficha)]) == 0
    with Image.open(destino / "folha.png") as im:
        a = np.asarray(im.convert("RGB"))
    laranja = (a[..., 0] > 150) & (a[..., 1] > 70) & (a[..., 1] < 130) & (a[..., 2] < 70)
    assert laranja[:, 384:].sum() > 500  # as vistas do modelo (metade direita) saem com a cor da criatura


@pytestmark_motor
def test_olho_pintado_tira_os_adesivos(texturizadas):
    ficha, destino, _ = texturizadas["bipede-cauda"]
    assert cli.main(["texturizar", str(ficha), "--olho-pintado"]) == 0
    arquivo = next(destino.glob("*.bbmodel"))
    modelo = bbmodelo.ler(arquivo)
    assert not any(c.nome.startswith("eye_") for c in modelo.cubos)
    # o olho (amarelo) ficou pintado na face da frente da cabeça
    cabeca = modelo.cubo("head_cube")
    u1, v1, u2, v2 = cabeca.faces["north"]["uv"]
    tex = np.asarray(modelo.textura)
    face = tex[int(min(v1, v2)):int(max(v1, v2)), int(min(u1, u2)):int(max(u1, u2)), :3].reshape(-1, 3)
    amarelo = (face[:, 0] > 150) & (face[:, 1] > 110) & (face[:, 2] < 80)
    assert amarelo.sum() >= 2


@pytestmark_motor
def test_plano_recortado_pela_silhueta():
    """Plano retangular cuja parte na imagem é um triângulo: metade dos texels fica transparente."""
    pasta = MODELOS / "_teste-recorte"
    shutil.rmtree(pasta, ignore_errors=True)
    arquivo = pasta / "plano.bbmodel"
    motor.criar(arquivo, "plano", 32, 32)
    motor.editar(arquivo, [{"op": "add_group", "name": "root", "origin": [0, 0, 0]},
                           {"op": "add_group", "name": "body", "origin": [0, 0, 0], "parent": "root"},
                           {"op": "add_cube", "name": "body_cube", "from": [-4, 0, -2], "to": [4, 8, 2], "parent": "body", "box_uv": True, "uv_offset": [0, 0]},
                           {"op": "add_group", "name": "fin", "origin": [0, 8, 0], "parent": "body"},
                           {"op": "add_cube", "name": "fin_cube", "from": [-4, 7, 0], "to": [4, 15, 0], "parent": "fin", "box_uv": True, "uv_offset": [0, 16]}])
    modelo = bbmodelo.ler(arquivo)
    u = 16 / 32  # altura 16 unidades
    proj = tx.projecao_da_vista("frente", {"centro": 8.0, "fator": 1.0}, u, (512, 1024))
    _, _, ids, _ = render.renderizar(modelo, projecao=proj, usar_textura=False)
    img = np.zeros((1024, 512, 4), np.uint8)
    img[ids >= 0] = (200, 60, 40, 255)
    # nadadeira: só o triângulo abaixo da diagonal aparece (o resto é fundo)
    ys, xs = np.mgrid[0:1024, 0:512]
    fora = (ids == 1) & (xs > ys - 32)
    img[fora] = 0
    vista = tx.Vista("frente", Image.fromarray(img, "RGBA"), proj, ids)
    pintura = tx.pintar(modelo, {"frente": vista}, {})
    tex = pintura["textura"]
    u1, v1, u2, v2 = modelo.cubo("fin_cube").faces["north"]["uv"]
    alfa = tex[int(min(v1, v2)):int(max(v1, v2)), int(min(u1, u2)):int(max(u1, u2)), 3]
    assert 0.2 < (alfa == 0).mean() < 0.8
    corpo = modelo.cubo("body_cube").faces["north"]["uv"]
    assert (tex[int(corpo[1]):int(corpo[3]), int(min(corpo[0], corpo[2])):int(max(corpo[0], corpo[2])), 3] == 255).all()
    shutil.rmtree(pasta, ignore_errors=True)
