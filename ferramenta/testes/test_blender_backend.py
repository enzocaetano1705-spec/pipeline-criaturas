"""Invariantes reais do backend. Integração opcional exige Blender já instalado."""

import copy
import json
import os
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from criaturas import cli
from criaturas.blender_backend import atlas, entrada, executar, glb, malha, movimento

FIXTURE = Path(__file__).parent/"sinteticos/blender-bipede.json"


@pytest.fixture
def job():
    return entrada.ler(FIXTURE)


@pytest.mark.parametrize("mutation,match", [
    (lambda j: j.pop("estagio"), "estagio"),
    (lambda j: j.update(tipo="real"), "referências"),
    (lambda j: j["plano"]["ossos"][2].update(pai="head"), "ciclo"),
    (lambda j: j["plano"]["cubos"][0].update(osso="root"), "root"),
    (lambda j: j["plano"]["cubos"][0].update(inflate=.3), "não suportados"),
    (lambda j: j["plano"]["cubos"][0].update(to=[-3, 7, -2.5]), "degenerado"),
    (lambda j: j["textura"]["variantes"]["ambar"].update(bico="#ffffff"), "protegida"),
    (lambda j: j["textura"].update(densidade=0), "densidade"),
    (lambda j: j["animacao"]["eventos"]["attack_physical"].update(HitFrame=2), "eventos"),
    (lambda j: j["plano"]["ossos"][0].update(pivo=[float("nan"), 0, 0]), "JSON"),
])
def test_rejeita_entrada_que_nao_pode_ser_preservada(job, mutation, match):
    mutation(job)
    with pytest.raises(ValueError, match=match):
        entrada.validar(job)


def test_atlas_densidade_margens_sem_sobreposicao_e_falha_de_orcamento(job):
    cfg = job["textura"]
    islands = atlas.ilhas(job["plano"], cfg)
    occupancy = np.zeros((cfg["resolucao"],)*2, dtype=bool)
    for i in islands:
        x, y, w, h = i["retangulo"]
        pad = cfg["margem"]
        region = occupancy[y-pad:y+h+pad, x-pad:x+w+pad]
        assert region.size == (w+2*pad)*(h+2*pad)
        assert not region.any()
        region[:] = True
    cfg["resolucao"] = 16
    with pytest.raises(ValueError, match="insuficiente"):
        atlas.ilhas(job["plano"], cfg)


def test_variantes_mascara_alfa_e_pixel_art_sem_mudar_detalhes(job, tmp_path):
    result = atlas.gerar(job, tmp_path)
    mask = np.array(Image.open(tmp_path/"mascara-regioes.png"))
    base = np.array(Image.open(tmp_path/"textura-base.png"))
    eye = result["ilhas"]
    for variant in ("ambar", "violeta"):
        pixels = np.array(Image.open(tmp_path/f"textura-{variant}.png"))
        assert np.array_equal(base[..., 3], pixels[..., 3])
        assert np.array_equal(base[mask == result["regioes"]["bico"]], pixels[mask == result["regioes"]["bico"]])
        assert np.array_equal(base[mask == result["regioes"]["pes"]], pixels[mask == result["regioes"]["pes"]])
        protected_eye = np.all(base[..., :3] == [20, 25, 36], axis=2)
        assert protected_eye.any() and np.array_equal(base[protected_eye], pixels[protected_eye])
        assert not mask[protected_eye].any()
        assert not np.array_equal(base, pixels)
        enlarged = np.array(Image.open(tmp_path/f"textura-{variant}-roblox.png"))
        assert np.array_equal(enlarged, np.repeat(np.repeat(pixels, 8, axis=0), 8, axis=1))
    cutout = next(i for i in eye if i["cubo"] == "crest_plane" and i["face"] == "north")
    x, y, w, h = cutout["retangulo"]
    assert base[y:y+h, x:x+w, 3].min() == 0 and base[y:y+h, x:x+w, 3].max() == 255
    assert base[y:y+h, x:x+w, :3].min() > 0  # RGB não preto sob o alfa da ilha.


def test_caixas_fechadas_normais_externas_e_lamina_com_volume(job, tmp_path):
    tex = atlas.gerar(job, tmp_path)
    geometry = malha.gerar(job, tex)
    vertices = np.array(geometry["vertices"])
    assert len(vertices) == 8*len(job["plano"]["cubos"])
    for i, piece in enumerate(geometry["pecas"]):
        p = vertices[piece["indices"]]
        assert np.prod(p.max(axis=0)-p.min(axis=0)) > 0
        center = p.mean(axis=0)
        for face in geometry["faces"][i*6:(i+1)*6]:
            a, b, c, d = vertices[face]
            normal = np.cross(b-a, c-a)
            assert np.dot(normal, (a+b+c+d)/4-center) > 0


def test_ik_preserva_comprimento_apoio_e_derivada_de_loop(job):
    rest = {b["nome"]: np.array(b["pivo"]) for b in job["plano"]["ossos"]}
    for name, duration in job["animacao"]["duracoes"].items():
        for t in np.linspace(0, duration, 161):
            world, feet = movimento.pose(job, name, t)
            for side in ("left", "right"):
                chain = [f"{prefix}_{side}" for prefix in ("leg", "shin", "foot")]
                for a, b in zip(chain, chain[1:]):
                    assert np.linalg.norm(world[a][:3, 3]-world[b][:3, 3]) == pytest.approx(np.linalg.norm(rest[a]-rest[b]), abs=1e-7)
                assert world[chain[-1]][:3, 3] == pytest.approx(feet[side]["alvo"], abs=1e-7)
            assert np.allclose(world["root"], np.eye(4))
        if name in ("idle", "walk", "run"):
            dt = 1e-5
            a, _ = movimento.pose(job, name, 0)
            b, _ = movimento.pose(job, name, duration)
            c, _ = movimento.pose(job, name, dt)
            d, _ = movimento.pose(job, name, duration-dt)
            for bone in a:
                assert a[bone] == pytest.approx(b[bone], abs=1e-7)
                assert (c[bone]-a[bone])/dt == pytest.approx((b[bone]-d[bone])/dt, abs=.03)


def test_nao_sobrescreve_saida_e_relata_erro_curto(job, tmp_path, capsys):
    # Contrato CLI é adicional; subcomandos antigos mantêm as mesmas opções.
    assert cli.main(["blender", "construir", str(FIXTURE), "--saida", str(tmp_path)]) == 1
    assert "já existe" in capsys.readouterr().out


@pytest.mark.skipif(os.environ.get("CRIATURAS_TESTAR_BLENDER") != "1", reason="integração Blender opt-in; use CRIATURAS_TESTAR_BLENDER=1")
def test_duas_reconstrucoes_glb_e_reimportacao_reais(tmp_path):
    folders = [tmp_path/"primeira", tmp_path/"segunda"]
    for dest in folders:
        result = executar.construir(FIXTURE, dest)
        assert result["ok"], result["erros"]
        assert executar.conferir(dest)["ok"]
        exported = json.loads((dest/"validacao-glb.json").read_text(encoding="utf-8"))
        assert all(r["ok"] and r["khronos"]["erros"] == 0 for r in exported.values())
        assert all(r["triangulos"] == 168 and r["influencias_max"] == 1 for r in exported.values())
    assert executar.semantica(folders[0]) == executar.semantica(folders[1])
    for path in folders[0].glob("*.glb"):
        assert executar.sha(path) == executar.sha(folders[1]/path.name)
    artifact = folders[1]/"textura-base.png"
    artifact.write_bytes(artifact.read_bytes()+b"alteracao manual")
    with pytest.raises(ValueError, match="modificados"):
        executar.conferir(folders[1])
