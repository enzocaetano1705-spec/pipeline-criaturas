"""Regressões do cache de textura sem depender do desktop ou de assets do usuário."""
import base64
import io
import json
import shutil
import struct
from types import SimpleNamespace
from pathlib import Path

import pytest

from PIL import Image

from criaturas import exportar
from criaturas.caminhos import RAIZ


def test_exportacao_espera_projeto_abrir_e_usa_arquivo_quando_resposta_excede_limite(tmp_path, monkeypatch):
    fonte, destino = tmp_path / "copia.bbmodel", tmp_path / "resultado.glb"
    destino.write_bytes(b"versao anterior")
    projetos = iter([None, {"name": "outro"}, {"name": fonte.stem}])
    chamadas = []
    monkeypatch.setattr(exportar.desktop, "respondendo", lambda: True)
    monkeypatch.setattr(exportar.desktop, "abrir", lambda *a, **k: None)
    monkeypatch.setattr(exportar.time, "sleep", lambda *a: None)

    def chamar(nome, args=None):
        chamadas.append((nome, args))
        if nome == "get_capabilities":
            return {"content": [{"type": "text", "text": json.dumps({"project": next(projetos)})}]}
        if "path" in args:
            Path(args["path"]).write_bytes(b"nova exportacao")
        return {"content": []}

    monkeypatch.setattr(exportar.desktop, "chamar", chamar)
    assert exportar.exportar_glb(fonte, destino) == {"bytes": 15}
    assert destino.read_bytes() == b"nova exportacao"
    exports = [a for n, a in chamadas if n == "export_model"]
    assert len(exports) == 2 and exports[0]["max_content_length"] == 2_000_000
    assert exports[1]["path"] != str(destino.resolve())  # arquivo antigo não mascara falha


def test_exportacao_sem_arquivo_recusa_resultado_e_preserva_anterior(tmp_path, monkeypatch):
    destino = tmp_path / "resultado.glb"; destino.write_bytes(b"anterior")
    fonte = tmp_path / "copia.bbmodel"
    monkeypatch.setattr(exportar.desktop, "respondendo", lambda: True)
    monkeypatch.setattr(exportar.desktop, "abrir", lambda *a, **k: None)
    monkeypatch.setattr(exportar.desktop, "chamar", lambda nome, args=None: {
        "content": [{"type": "text", "text": json.dumps({"project": {"name": fonte.stem}})}] if nome == "get_capabilities" else []})
    with pytest.raises(exportar.desktop.DesktopErro, match="não gravou"):
        exportar.exportar_glb(fonte, destino)
    assert destino.read_bytes() == b"anterior"


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


def test_material_fosco_preserva_binario_uvs_rig_e_animacoes(tmp_path):
    arquivo = tmp_path / "pbr.glb"
    shutil.copy(RAIZ / "exportacoes/roblox/pavao/Pavao_F2.glb", arquivo)
    antes = arquivo.read_bytes()
    g0 = exportar.json_do_glb(arquivo)
    inicio0 = 28 + struct.unpack("<I", antes[12:16])[0]
    binario0 = antes[inicio0:]
    exportar.material_fosco_glb(arquivo)
    depois = arquivo.read_bytes()
    g1 = exportar.json_do_glb(arquivo)
    inicio1 = 28 + struct.unpack("<I", depois[12:16])[0]
    assert depois[inicio1:inicio1 + len(binario0)] == binario0
    for campo in ("nodes", "meshes", "skins", "accessors", "animations", "scenes"):
        assert g1.get(campo) == g0.get(campo)
    assert g1["images"][:-1] == g0["images"]
    pbr = g1["materials"][0]["pbrMetallicRoughness"]
    indice = pbr["metallicRoughnessTexture"]["index"]
    imagem = g1["images"][g1["textures"][indice]["source"]]
    vista = g1["bufferViews"][imagem["bufferView"]]
    offset = inicio1 + vista["byteOffset"]
    im = Image.open(io.BytesIO(depois[offset:offset + vista["byteLength"]]))
    assert im.size == (4, 4) and im.getpixel((0, 0)) == (255, 255, 0)
    assert pbr["metallicFactor"] == 0 and pbr["roughnessFactor"] == 1


def test_novo_atlas_preserva_amostragem_e_todos_os_dados_exceto_u(tmp_path):
    import numpy as np

    glb = tmp_path / "novo-atlas.glb"
    png = tmp_path / "atlas.png"
    shutil.copy(RAIZ / "exportacoes/roblox/pavao/Pavao_F2.glb", glb)
    shutil.copy(RAIZ / "exportacoes/roblox/pavao/Pavao_F2-textura.png", png)
    antes, g0 = glb.read_bytes(), exportar.json_do_glb(glb)
    pixels0 = np.array(Image.open(png))

    def accessor(blob, g, i):
        a = g["accessors"][i]
        v = g["bufferViews"][a["bufferView"]]
        n = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[a["type"]]
        b = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}[a["componentType"]]
        offset = 28 + struct.unpack("<I", blob[12:16])[0] + v.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = v.get("byteStride", n * b)
        return b"".join(blob[offset+j*stride:offset+j*stride+n*b] for j in range(a["count"]))

    exportar.espelhar_atlas_glb(glb, png)
    depois, g1 = glb.read_bytes(), exportar.json_do_glb(glb)
    for campo in ("nodes", "skins", "meshes", "animations"):
        assert g0[campo] == g1[campo]
    uvs = {p["attributes"]["TEXCOORD_0"] for m in g0["meshes"] for p in m["primitives"]}
    for i in range(len(g0["accessors"])):
        a, b = accessor(antes, g0, i), accessor(depois, g1, i)
        if i in uvs:
            u0, u1 = np.frombuffer(a, "<f4").reshape(-1, 2), np.frombuffer(b, "<f4").reshape(-1, 2)
            assert np.allclose(u1[:, 0], np.clip(1 - u0[:, 0], 0, 1))
            assert np.array_equal(u1[:, 1], u0[:, 1])
        else:
            assert a == b  # posições, normais, índices, skin e canais de animação
    pixels1 = np.array(Image.open(png))
    assert np.array_equal(pixels1, pixels0[:, ::-1])
    h, w = pixels0.shape[:2]
    for u, v in [(0.123, 0.345), (0.456, 0.678), (0.789, 0.111)]:
        assert np.array_equal(pixels0[int(v*h), int(u*w)], pixels1[int(v*h), int((1-u)*w)])
    vista = g1["bufferViews"][g1["images"][0]["bufferView"]]
    inicio = 28 + struct.unpack("<I", depois[12:16])[0] + vista["byteOffset"]
    assert depois[inicio:inicio+vista["byteLength"]] == png.read_bytes()
