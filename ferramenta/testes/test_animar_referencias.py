"""Regressões de rigs estudados nas referências; sem motor ou assets externos."""
import numpy as np
import pytest

from criaturas import animar, bbmodelo


def modelo_com_partes(partes=(), visibilidade=None):
    pais = {"root": None, "body": "root", "eye_left": "body", "eyelid_left": "eye_left",
            "eye_patch": "eye_left", "feather_left_1": "body", "feather_left_2": "feather_left_1",
            "feather_right_1": "body", "feather_empty": "body"}
    ossos = {n: bbmodelo.Osso(n, n, p, np.array([0., 2., 0.]), np.zeros(3))
             for n, p in pais.items()}
    ossos["root"].origem = np.zeros(3)
    cubos = []
    for i, osso in enumerate(("body",) + tuple(partes)):
        # Olhos e penas podem ser planos; continuam sendo superfícies visíveis.
        de = np.array([-2., 0., -1.]) if osso == "body" else np.array([-1., 2., -1.01])
        ate = np.array([2., 4., 1.]) if osso == "body" else np.array([0., 3., -1.01])
        cubos.append(bbmodelo.Cubo(f"piece_{i}", f"piece_{i}", osso, de, ate,
                                  np.array([0., 2., 0.]), np.zeros(3), 0., {}))
    bruto = {"elements": [{"uuid": c.uuid, "visibility": (visibilidade or {}).get(c.osso, True)}
                          for c in cubos]}
    return bbmodelo.Modelo("sintetico", (32, 32), ossos, cubos, [], bruto=bruto)


def test_olho_vazio_nao_promete_blink_visivel():
    rig = animar.Rig.do_modelo(modelo_com_partes())
    assert animar.blink(rig) is None
    clips, avisos = animar.clipes(rig, "cabeça-corpo", "inicial", ("blink",))
    assert clips == []
    assert any(a["codigo"] == "sem_olhos" and "geometria" in a["texto"] for a in avisos)


@pytest.mark.parametrize("osso", ["eye_left", "eye_patch"])
def test_olho_com_superficie_direta_ou_descendente_pisca(osso):
    rig = animar.Rig.do_modelo(modelo_com_partes((osso,)))
    clip = animar.blink(rig)
    assert clip is not None and "eye_left" in clip.trilhas
    # A pálpebra vazia não pode esconder a escolha do olho que tem geometria.
    assert "eyelid_left" not in clip.trilhas
    assert clip.valor("eye_left", "scale", clip.duracao / 2)[1] < 0.2


def test_olho_oculto_nao_entra_na_piscada():
    rig = animar.Rig.do_modelo(modelo_com_partes(("eye_left",), {"eye_left": False}))
    assert animar.blink(rig) is None


def test_penas_so_animam_superficies_e_nao_habilitam_voo():
    rig = animar.Rig.do_modelo(modelo_com_partes(("feather_left_2",)))
    assert set(rig.penas) == {"feather_left_1", "feather_left_2"}
    assert animar.fly(rig) is None
    for clip in (animar.idle(rig, "cabeça-corpo"), animar.walk(rig, "cabeça-corpo", 1.33)):
        assert "feather_empty" not in clip.trilhas
        assert "feather_right_1" not in clip.trilhas
        assert {"feather_left_1", "feather_left_2"} <= set(clip.trilhas)


@pytest.mark.parametrize("tipo", ["idle", "walk"])
def test_balanco_das_penas_tem_chaves_numericas_discretas_e_loop_fechado(tipo):
    modelo = modelo_com_partes(("feather_left_1", "feather_left_2"))
    rig = animar.Rig.do_modelo(modelo)
    clip = animar.idle(rig, "cabeça-corpo") if tipo == "idle" else animar.walk(rig, "cabeça-corpo", 1.33)
    chaves = animar.assar(clip, modelo)
    for osso in rig.penas:
        lista = chaves[osso]["rotation"]
        valores = np.array([v for _, v in lista])
        assert lista[0][1] == lista[-1][1]
        assert all(isinstance(x, float) for _, v in lista for x in v)
        assert np.isfinite(valores).all()
        assert 0 < np.abs(valores).max() <= 3.01
        assert not valores[:, 1].any()


def test_regenerar_sem_olho_remove_blink_antigo(monkeypatch, tmp_path):
    modelo = modelo_com_partes()
    modelo.animacoes = [{"name": "blink"}]
    lotes = []
    monkeypatch.setattr(bbmodelo, "ler", lambda _: modelo)
    monkeypatch.setattr(animar.motor, "editar", lambda _, lote: lotes.extend(lote))
    resultado = animar.animar(tmp_path / "sintetico.bbmodel", "cabeça-corpo", "inicial", ("blink",))
    assert resultado["clipes"] == {}
    assert {"op": "remove_animation", "animation": "blink"} in lotes
    assert not any(op["op"] == "add_animation" for op in lotes)
