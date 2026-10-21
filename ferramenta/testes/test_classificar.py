import json
import shutil

import pytest

from criaturas import classificar as cl
from criaturas import cli, contratos
from criaturas.caminhos import MODELOS

BASE = {
    "postura": "quadrúpede", "pernas": 4, "bracos": 0, "asas": 0, "cauda": 0, "nadadeiras": 0,
    "pescoco": "curto", "cabeca": {"frac_alt": 0.4}, "focinho": "médio", "orelhas": "médias",
    "olhos": {"frac_alt": 0.12}, "cobertura": "pelo", "extras": [],
}


def checklist(**itens):
    """Checklist com todos os itens visíveis; valores de `itens` substituem a base."""
    valores = {**BASE, **itens}
    return {"itens": {k: {"valor": v, "certeza": "visível", "fonte": "imagem"} for k, v in valores.items()}}


CASOS = {
    "canídeo": (checklist(focinho={"razao_cranio": 0.52}, orelhas={"razao_cranio": 1.0},
                          cauda={"comprimento_alt": 0.62, "grossura": "grossa", "segmentos": 4}, pernas={"n": 4, "frac_alt": 0.45}),
                ("quadrúpede", "canídeo")),
    "felino": (checklist(focinho={"razao_cranio": 0.27}, orelhas={"razao_cranio": 1.0}, extras=["bigodes"],
                         cauda={"comprimento_alt": 0.7, "grossura": "fina", "segmentos": 6}, pernas={"n": 4, "frac_alt": 0.45}),
               ("quadrúpede", "felino")),
    "ungulado": (checklist(focinho={"razao_cranio": 0.58}, orelhas={"razao_cranio": 0.6}, extras=["cascos"],
                           cauda={"comprimento_alt": 0.35, "grossura": "fina", "segmentos": 2}, pernas={"n": 4, "frac_alt": 0.47}),
                 ("quadrúpede", "ungulado")),
    "dragão": (checklist(postura="bípede", pernas=2, bracos=2, cobertura="escama", extras=["chifres"],
                         asas={"pares": 1, "envergadura_alt": 0.8, "tipo": "membrana"}, pescoco={"segmentos": 3},
                         focinho={"razao_cranio": 0.8}, olhos={"frac_alt": 0.08},
                         cauda={"comprimento_alt": 0.8, "grossura": "grossa", "segmentos": 5}),
               ("bípede com cauda", "dragão")),
    "dinossauroide": (checklist(postura="bípede", pernas=2, bracos=2, cobertura="escama", pescoco={"segmentos": 2},
                                focinho={"razao_cranio": 1.1}, corpo={"compr_alt": 0.53},
                                cauda={"comprimento_alt": 0.66, "grossura": "grossa", "segmentos": 4}),
                      ("bípede com cauda", "dinossauroide/kaiju")),
    "ave": (checklist(postura="bípede", pernas=2, asas={"pares": 1, "envergadura_alt": 2.5, "tipo": "penas"},
                      focinho="bico", cobertura="pena", orelhas="nenhuma",
                      cauda={"comprimento_alt": 0.6, "leque": True}),
            ("alado", "ave")),
    "morcego": (checklist(postura="bípede", pernas=2, asas={"pares": 1, "envergadura_alt": 3.4, "tipo": "membrana"},
                          orelhas={"razao_cranio": 1.45}, focinho={"razao_cranio": 0.39}, cabeca={"frac_alt": 0.5}),
                ("alado", "morcego")),
    "peixe": (checklist(postura="nadando", pernas=0, nadadeiras=3, cobertura="escama", orelhas="nenhuma",
                        cabeca={"frac_alt": 0.6}, cauda={"comprimento_alt": 1.3, "segmentos": 3}),
              ("peixe", "peixe/aquático")),
    "serpente": (checklist(postura="rastejante", pernas=0, cobertura="escama", orelhas="nenhuma", olhos={"frac_alt": 0.17},
                           focinho={"razao_cranio": 1.0}, corpo={"compr_alt": 0.9}, cauda={"comprimento_alt": 0.8}),
                 ("serpentiforme", "serpente/verme")),
    "humanoide": (checklist(postura="bípede", pernas=2, bracos=2, cobertura="pele", olhos={"frac_alt": 0.08},
                            cauda="nenhuma", focinho={"razao_cranio": 0.6}),
                  ("humanoide", "humanoide")),
    "inseto": (checklist(postura="rastejante", pernas=6, cobertura="carapaça", extras=["antenas"],
                         asas={"pares": 2, "tipo": "inseto"}, olhos={"frac_alt": 0.18}),
               ("inseto", "inseto/artrópode")),
}


@pytest.mark.parametrize("caso", CASOS)
def test_sugestao_1_correta(caso):
    dados, esperado = CASOS[caso]
    sugestoes = cl.pontuar(dados)
    assert (sugestoes[0]["plano"], sugestoes[0]["nicho"]) == esperado, sugestoes


@pytest.mark.parametrize("par", [("canídeo", "felino"), ("dragão", "dinossauroide"), ("ave", "morcego"),
                                 ("peixe", "serpente"), ("canídeo", "ungulado")])
def test_pares_que_se_confundem(par):
    """Os dois lados de cada par saem diferentes: ninguém cai no nicho do vizinho."""
    a, b = (cl.pontuar(CASOS[x][0])[0]["nicho"] for x in par)
    assert a != b
    assert a == CASOS[par[0]][1][1] and b == CASOS[par[1]][1][1]


def test_saida_segue_o_contrato_e_soma_100():
    resultado = cl.classificar(CASOS["canídeo"][0])
    assert contratos.problemas("classificacao", resultado) == []
    assert len(resultado["sugestoes"]) == 3
    assert sum(s["confianca"] for s in resultado["sugestoes"]) == pytest.approx(1.0, abs=0.01)
    assert all(len(s["tracos"]) <= 3 for s in resultado["sugestoes"])


def test_estagio_aparente_pela_cabeca():
    inicial = cl.estagio_aparente(checklist(cabeca={"frac_alt": 0.45}, olhos={"frac_alt": 0.17}), "quadrúpede")
    final = cl.estagio_aparente(checklist(cabeca={"frac_alt": 0.18}, olhos={"frac_alt": 0.06}), "quadrúpede")
    assert inicial["estagio_tabela"] == "inicial"
    assert final["estagio_tabela"] == "final"


def test_item_da_tabela_nao_pesa():
    dados = CASOS["felino"][0]
    dados["itens"]["extras"] = {"valor": ["bigodes"], "certeza": "oculto", "fonte": "tabela"}
    norm = cl.normalizar(dados)
    assert norm["peso"]["extras"] == 0.0


# ---------- CLI ----------

@pytest.fixture
def pasta_real(tmp_path):
    pasta = tmp_path / "raposa-cl"
    pasta.mkdir()
    (pasta / "ficha.md").write_text("---\nnome: raposa-cl\nstatus: pronta-para-modelagem\ndestino: [roblox]\nestagios: 1\n---\n\n"
                                    "# Raposa\n\n## Estágio 1 — Faísca\n- **Estágio:** 1 de 3\n- **Categoria confirmada:**\n\n"
                                    "### Prompt usado\n```text\nfox\n```\n", encoding="utf-8")
    destino = MODELOS / "raposa-cl" / "e1"
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "checklist.json").write_text(json.dumps(CASOS["canídeo"][0], ensure_ascii=False), encoding="utf-8")
    yield pasta
    shutil.rmtree(MODELOS / "raposa-cl", ignore_errors=True)


def test_criatura_real_sem_categoria_para(pasta_real, capsys):
    assert cli.main(["ficha", str(pasta_real)]) == 1  # sem imagens: erro, mas grava entrada.json
    capsys.readouterr()
    assert cli.main(["classificar", str(pasta_real)]) == 3
    texto = capsys.readouterr().out
    assert "PARE" in texto and "1. quadrúpede › canídeo" in texto
    assert len(texto.splitlines()) <= 20
    ficha = (pasta_real / "ficha.md").read_text(encoding="utf-8")
    assert "## Classificação sugerida" in ficha and "### e1" in ficha
    # rodar de novo troca a subseção em vez de duplicar
    cli.main(["classificar", str(pasta_real)])
    assert (pasta_real / "ficha.md").read_text(encoding="utf-8").count("### e1") == 1


def test_registrar_escolha_diferente(pasta_real, tmp_path, monkeypatch, capsys):
    arquivo = tmp_path / "correcoes.jsonl"
    monkeypatch.setattr(cl, "CORRECOES", arquivo)
    monkeypatch.setattr(cl.registrar_correcao, "__defaults__", (arquivo,))
    cli.main(["ficha", str(pasta_real)])
    assert cli.main(["classificar", str(pasta_real), "--registrar-escolha", "quadrúpede › felino"]) == 0
    linha = json.loads(arquivo.read_text(encoding="utf-8").splitlines()[0])
    assert linha["escolha"] == {"plano": "quadrúpede", "nicho": "felino"}
    assert linha["sugestoes"][0]["nicho"] == "canídeo"
    assert "categoria usada: quadrúpede › felino (confirmada)" in capsys.readouterr().out


def test_sem_checklist_explica(tmp_path, capsys):
    pasta = tmp_path / "_teste-sem-checklist"
    pasta.mkdir()
    try:
        assert cli.main(["classificar", str(pasta)]) == 1
        assert "classificar.md" in capsys.readouterr().out
    finally:
        shutil.rmtree(MODELOS / "_teste-sem-checklist", ignore_errors=True)
