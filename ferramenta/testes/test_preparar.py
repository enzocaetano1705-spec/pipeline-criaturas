import json
import shutil

import numpy as np
import pytest
from PIL import Image, ImageDraw

from criaturas import cli, preparar
from criaturas.caminhos import MODELOS


def _criatura(fundo=(240, 240, 240), alfa=False, tamanho=(600, 400)):
    """Retângulo 200×300 (corpo) + quadrado 80×80 (cabeça à esquerda), sobre fundo liso."""
    modo = "RGBA" if alfa else "RGB"
    im = Image.new(modo, tamanho, (0, 0, 0, 0) if alfa else fundo)
    d = ImageDraw.Draw(im)
    d.rectangle([200, 60, 399, 359], fill=(200, 90, 40, 255) if alfa else (200, 90, 40))
    d.rectangle([120, 60, 199, 139], fill=(90, 60, 30, 255) if alfa else (90, 60, 30))
    return im


def test_mascara_por_bordas():
    mascara, metodo = preparar.mascara_da_imagem(_criatura())
    assert metodo == "bordas"
    assert mascara.sum() == 200 * 300 + 80 * 80


def test_mascara_por_alfa():
    mascara, metodo = preparar.mascara_da_imagem(_criatura(alfa=True))
    assert metodo == "alfa"
    assert mascara.sum() == 200 * 300 + 80 * 80


def test_respingo_vira_fundo():
    im = _criatura()
    ImageDraw.Draw(im).rectangle([10, 10, 12, 12], fill=(0, 0, 0))
    mascara, _ = preparar.mascara_da_imagem(im)
    assert not mascara[11, 11]


def test_recorte_na_silhueta_e_escala_comum(tmp_path):
    caminho = tmp_path / "e1-frente.png"
    _criatura().save(caminho)
    v = preparar.preparar_vista(caminho)
    assert v["caixa_original"] == [120, 60, 400, 360]
    assert v["recorte"].height == preparar.ALTURA_COMUM
    assert abs(v["recorte"].width - 280 * preparar.ALTURA_COMUM / 300) <= 1


def test_espelhar(tmp_path):
    caminho = tmp_path / "e1-lado.png"
    _criatura().save(caminho)
    normal = preparar.preparar_vista(caminho)["mascara"]
    espelhada = preparar.preparar_vista(caminho, espelhar=True)["mascara"]
    assert np.array_equal(normal[:, ::-1], espelhada)


def test_grade_ate_768_e_celulas():
    recorte = Image.new("RGBA", (2000, 1000), (255, 0, 0, 255))
    grade, px, celulas = preparar.imagem_com_grade(recorte)
    assert max(grade.size) <= 768
    assert celulas == pytest.approx(64)


def test_cli_preparar(tmp_path, capsys):
    pasta = tmp_path / "_teste-preparar"
    pasta.mkdir()
    _criatura().save(pasta / "e1-frente.png")
    _criatura().save(pasta / "e1-conceito.png")
    destino = MODELOS / "_teste-preparar"
    try:
        assert cli.main(["preparar", str(pasta)]) == 0
        info = json.loads((destino / "e1" / "preparo" / "preparo.json").read_text(encoding="utf-8"))
        assert set(info["vistas"]) == {"conceito", "frente"}
        assert any(a["codigo"] == "sem_lado" for a in info["avisos"])
        for arquivo in ("frente-grade.png", "frente-768.png", "frente-mascara.png", "frente-recorte.png"):
            assert (destino / "e1" / "preparo" / arquivo).exists()
        assert len(capsys.readouterr().out.splitlines()) <= 20
    finally:
        shutil.rmtree(destino, ignore_errors=True)


def test_cli_sem_imagens(tmp_path):
    pasta = tmp_path / "_teste-vazio"
    pasta.mkdir()
    try:
        assert cli.main(["preparar", str(pasta)]) == 1
    finally:
        shutil.rmtree(MODELOS / "_teste-vazio", ignore_errors=True)
