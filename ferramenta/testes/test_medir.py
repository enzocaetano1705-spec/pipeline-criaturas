import json
import shutil

import numpy as np
import pytest

from criaturas import bbmodelo, cli, contratos, medir, motor, preparar, sinteticos
from criaturas.caminhos import MODELOS

pytestmark = pytest.mark.skipif(not motor.disponivel(), reason="motor headless não instalado")


# ---------- unidades ----------

def _mascara():
    m = np.zeros((320, 200), bool)  # 32 células de 10 px
    m[100:320, 50:150] = True  # corpo: x 5..15, y 10..32
    return m


def test_encostar_corrige_ruido_na_silhueta():
    assert medir.encostar([5.8, 9.2, 14.4, 31.5], _mascara()) == [5.0, 10.0, 15.0, 32.0]


def test_encostar_usa_borda_de_cor_dentro_da_silhueta():
    m = _mascara()
    cor = np.full(m.shape + (3,), 255, np.uint8)
    cor[m] = (200, 60, 40)
    cor[150:200, 80:120] = (240, 220, 160)  # mancha x 8..12, y 15..20, dentro do corpo
    assert medir.encostar([7.3, 14.4, 12.6, 20.8], m, cor) == [8.0, 15.0, 12.0, 20.0]


def test_calibrar_pelo_chao_e_topos():
    frente = {"head": [0, 6, 10, 16], "body": [0, 16, 10, 32]}
    # no lado as orelhas somem: a cabeça começa no topo e tudo fica esticado por 32/26
    lado = {"head": [0, 0, 10, 32 - 16 * 32 / 26], "body": [0, 32 - 16 * 32 / 26, 10, 32]}
    assert medir.calibrar(frente, lado) == pytest.approx(26 / 32, rel=0.02)


# ---------- ida e volta (3.4) ----------

@pytest.fixture(scope="module")
def preparadas():
    sinteticos.construir_todas()
    saida = {}
    for nome in sinteticos.NOMES:
        destino = sinteticos.SAIDA / "_teste-medir" / nome
        info = preparar.preparar_estagio(sinteticos.pasta_ficha(nome), "e1", destino)
        modelo = bbmodelo.ler(sinteticos.SAIDA / nome / "e1" / f"{nome}-e1.bbmodel")
        lo, hi = bbmodelo.limites(modelo)
        saida[nome] = (info, destino, float(hi[1] - lo[1]))
    yield saida
    shutil.rmtree(sinteticos.SAIDA / "_teste-medir", ignore_errors=True)


def _medir(nome, preparadas, ruido, semente):
    info, destino, altura = preparadas[nome]
    leitura = sinteticos.leitura_da_verdade(nome, info, ruido=ruido, semente=semente)
    categoria = sinteticos.carregar(nome)["categoria"]
    return medir.medir(leitura, medir.carregar_mascaras(destino), altura, categoria=categoria,
                       cores=medir.carregar_cores(destino))


@pytest.mark.parametrize("nome", sinteticos.NOMES)
def test_sem_ruido_bate_com_a_verdade(nome, preparadas):
    resultado = _medir(nome, preparadas, 0.0, 0)
    assert contratos.problemas("medidas", resultado) == []
    comp = sinteticos.comparar_com_verdade(nome, resultado)
    falhas = {k: v for k, v in comp.items() if not v["ok"]}
    assert len(falhas) <= 1, falhas


def test_ida_e_volta_com_ruido_de_uma_celula(preparadas):
    """Aceite da Fase 3: erro ≤ 1 unidade ou 10% por dimensão em ≥ 90% das partes das 3 sintéticas."""
    total = certas = 0
    for semente in (0, 1, 2):
        for nome in sinteticos.NOMES:
            comp = sinteticos.comparar_com_verdade(nome, _medir(nome, preparadas, 1.0, semente))
            total += len(comp)
            certas += sum(v["ok"] for v in comp.values())
    assert certas / total >= 0.90, f"{certas}/{total}"


def test_espelha_o_lado_direito(preparadas):
    resultado = _medir("quadrupede", preparadas, 0.0, 0)
    por_id = {p["id"]: p for p in resultado["partes"]}
    e, d = por_id["leg_back_left"], por_id["leg_back_right"]
    assert d["simetria"] == "direita"
    assert d["from"][0] == pytest.approx(-e["to"][0]) and d["to"][0] == pytest.approx(-e["from"][0])
    assert e["to"][0] <= 0.5, "o lado esquerdo fica em -X"


def test_planos_e_adesivos_ficam_finos(preparadas):
    resultado = _medir("alado", preparadas, 0.0, 0)
    por_id = {p["id"]: p for p in resultado["partes"]}
    asa = por_id["wing_left"]
    assert asa["from"][2] == asa["to"][2]
    cauda = por_id["tail_1"]
    assert cauda["from"][0] == cauda["to"][0]
    olho, cabeca = por_id["eye_left"], por_id["head"]
    assert olho["from"][2] == olho["to"][2] < cabeca["from"][2]


def test_sem_lado_estima_e_avisa(preparadas):
    info, destino, altura = preparadas["bipede-cauda"]
    leitura = sinteticos.leitura_da_verdade("bipede-cauda", info, ruido=0.0)
    for p in leitura["partes"]:
        p["caixas"].pop("lado", None)
    leitura["partes"] = [p for p in leitura["partes"] if p["caixas"]]
    mascaras = medir.carregar_mascaras(destino)
    mascaras.pop("lado")
    resultado = medir.medir(leitura, mascaras, altura, categoria={"plano": "bípede com cauda", "nicho": "dinossauroide/kaiju"},
                            estagio="meio")
    codigos = {a["codigo"] for a in resultado["avisos"]}
    assert "sem_lado" in codigos
    body = next(p for p in resultado["partes"] if p["id"] == "body")
    assert body["profundidade"] == "tabela"


def test_cli_medir(preparadas, capsys):
    info, _, _ = preparadas["quadrupede"]
    ficha = sinteticos.pasta_ficha("quadrupede")
    nome = ficha.name
    try:
        assert cli.main(["ficha", str(ficha)]) == 0
        assert cli.main(["preparar", str(ficha)]) == 0
        info = json.loads((MODELOS / nome / "e1" / "preparo" / "preparo.json").read_text(encoding="utf-8"))
        leitura = sinteticos.leitura_da_verdade("quadrupede", info, ruido=1.0, semente=3)
        (MODELOS / nome / "e1" / "leitura.json").write_text(json.dumps(leitura, ensure_ascii=False), encoding="utf-8")
        capsys.readouterr()
        assert cli.main(["medir", str(ficha)]) == 0
        texto = capsys.readouterr().out
        assert "13 partes" in texto and len(texto.splitlines()) <= 20
        assert (MODELOS / nome / "e1" / "medidas.json").exists()
    finally:
        shutil.rmtree(MODELOS / nome, ignore_errors=True)
