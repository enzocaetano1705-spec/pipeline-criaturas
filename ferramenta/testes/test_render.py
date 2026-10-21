import numpy as np
import pytest

from criaturas import bbmodelo, motor, render, sinteticos


@pytest.fixture(scope="module")
def quadrupede():
    if not motor.disponivel():
        pytest.skip("motor headless não instalado")
    destino = sinteticos.SAIDA / "_teste-render"
    arquivo = sinteticos.construir("quadrupede", destino)
    plano = sinteticos.plano_cubos(sinteticos.carregar("quadrupede"))
    return bbmodelo.ler(arquivo), sinteticos.cores_por_cubo(plano), destino


def test_le_ossos_e_hierarquia(quadrupede):
    modelo, _, _ = quadrupede
    assert modelo.ossos["head"].pai == "body"
    assert modelo.ossos["body"].pai == "root"
    assert modelo.cubo("ear_right_cube").mirror_uv
    lo, hi = bbmodelo.limites(modelo)
    assert list(lo) == [-4, 0, -15] and list(hi) == [4, 19, 14]


def test_frente_poe_o_lado_esquerdo_a_direita(quadrupede):
    modelo, cores, _ = quadrupede
    _, mascara, ids, proj = render.renderizar(modelo, "frente", escala=10, cores=cores)
    nomes = [c.nome for c in modelo.cubos]
    # centro da orelha esquerda (-X) cai na metade direita da imagem
    px = proj.pixel([[-2.5, 17, -9]])[0]
    assert px[0] > proj.tamanho[0] / 2
    assert nomes[ids[int(px[1]), int(px[0])]] == "ear_left_cube"


def test_lado_poe_a_frente_a_esquerda(quadrupede):
    modelo, cores, _ = quadrupede
    _, _, ids, proj = render.renderizar(modelo, "lado", escala=10, cores=cores)
    focinho = proj.pixel([[0, 9.5, -14]])[0]
    cauda = proj.pixel([[0, 9, 13]])[0]
    assert focinho[0] < cauda[0]
    nomes = [c.nome for c in modelo.cubos]
    assert nomes[ids[int(focinho[1]), int(focinho[0])]] == "snout_cube"


def test_silhueta_da_frente_tem_a_area_esperada(quadrupede):
    modelo, cores, _ = quadrupede
    _, mascara, _, _ = render.renderizar(modelo, "frente", escala=4, cores=cores, margem=0)
    # vista de frente: cabeça 8×7, orelhas 2×(3×4 fora da cabeça), corpo abaixo da cabeça 6×3,
    # pernas da frente 2×(2×5) (as de trás ficam escondidas atrás delas)
    esperado = (8 * 7 + 2 * 3 * 4 + 6 * 3 + 2 * 2 * 5) * 16
    assert abs(mascara.sum() - esperado) / esperado < 0.03


def test_cor_vem_do_cubo(quadrupede):
    modelo, cores, _ = quadrupede
    im, _, _, proj = render.renderizar(modelo, "frente", escala=10, cores=cores, sombreado=0)
    x, y = proj.pixel([[0, 9.5, -15]])[0].astype(int)
    assert tuple(np.asarray(im)[y, x]) == render._hex(cores["snout_cube"])


def test_folha_ate_768(quadrupede):
    modelo, cores, _ = quadrupede
    folha = render.folha(modelo, cores=cores, titulo="quadrupede")
    assert max(folha.size) <= 768


def test_imagens_de_conceito(quadrupede):
    modelo, cores, destino = quadrupede
    plano = sinteticos.plano_cubos(sinteticos.carregar("quadrupede"))
    saidas = sinteticos.renderizar_conceito(destino / "quadrupede-e1.bbmodel", plano, destino / "conceito")
    from PIL import Image
    for caminho in saidas.values():
        with Image.open(caminho) as im:
            assert max(im.size) <= 1024
