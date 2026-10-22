"""Regressões do cache de textura sem depender do desktop ou de assets do usuário."""
import base64
import io
import json
from types import SimpleNamespace

from PIL import Image

from criaturas import exportar


def test_reexportacao_recupera_atlas_das_uvs_em_cache(tmp_path, monkeypatch):
    original = SimpleNamespace(textura=Image.new("RGBA", (8, 8), "red"))
    preparado = SimpleNamespace(textura=None)
    fonte = tmp_path / "fonte.bbmodel"
    copia = tmp_path / "copia.bbmodel"
    copia.write_text(json.dumps({"textures": [{"uuid": "tex"}]}))
    monkeypatch.setattr(exportar.bbmodelo, "ler", lambda p: original if p == fonte else preparado)
    monkeypatch.setattr(exportar, "uv_fora_do_atlas", lambda m: [])
    monkeypatch.setattr(exportar, "copia_roblox", lambda *a: copia)
    monkeypatch.setattr(exportar, "superamostrar", lambda *a: Image.new("RGBA", (8, 8), "blue"))

    def editar(p, ops):
        for op in ops:
            if op["op"] == "update_texture":
                preparado.textura = Image.open(io.BytesIO(base64.b64decode(op["source"].split(",")[1]))).copy()

    monkeypatch.setattr(exportar.motor, "editar", editar)
    for nome in ("exportar_glb", "acrescentar_locators", "renomear_glb", "trocar_imagens_glb"):
        monkeypatch.setattr(exportar, nome, lambda *a: None)
    monkeypatch.setattr(exportar, "verificar_glb", lambda *a: ([], [], {}))
    destino = tmp_path / "saida"
    for _ in range(2):
        exportar.exportar_roblox(fonte, "Teste", destino, superamostra={"ossos": ["head"], "fator": 4})
        with Image.open(destino / "Teste-textura.png") as tex:
            assert tex.getpixel((0, 0)) == (0, 0, 255, 255)
            assert tex.tobytes() == preparado.textura.tobytes()


def test_cache_invalida_quando_so_a_textura_muda_e_preserva_copias(tmp_path, monkeypatch):
    fonte = tmp_path / "modelo.bbmodel"
    fonte.write_text(json.dumps({"textures": [], "outliner": [], "animations": []}))
    textura = tmp_path / "textura.png"
    monkeypatch.setattr(exportar.motor, "editar", lambda *a: None)
    Image.new("RGBA", (8, 8), "red").save(textura)
    primeira = exportar.copia_roblox(fonte, textura, tmp_path / "copias", "Teste")
    Image.new("RGBA", (8, 8), "blue").save(textura)
    segunda = exportar.copia_roblox(fonte, textura, tmp_path / "copias", "Teste")
    assert primeira != segunda
    assert primeira.exists() and segunda.exists()
    assert fonte.read_text() == primeira.read_text() == segunda.read_text()
