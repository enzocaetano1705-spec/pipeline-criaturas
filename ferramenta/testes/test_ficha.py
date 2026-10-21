import shutil

import pytest
from PIL import Image

from criaturas import cli, contratos
from criaturas.caminhos import MODELOS, RAIZ
from criaturas.ficha import ler_ficha

MODELO = RAIZ / "docs" / "criaturas" / "_modelo"

FICHA_OK = """---
tipo: ficha-criatura
nome: raposa-teste
status: pronta-para-modelagem
destino: [roblox, minecraft]
estilo: cobblemon
estagios: 1
---

# Raposa teste

**Ideia em uma frase:** uma raposa com chama na cauda.

**Motivos que atravessam a linhagem (2 ou 3 traços que nunca somem):** chama; orelhas grandes

## Estágio 1 — Faísca
- **Estágio:** 1 de 3
- **Categoria (seu palpite):** quadrúpede › canídeo
- **Categoria confirmada:** Quadrupede > canideo
- **Altura no jogo (blocos):** 0,8
- **Imagens:** e1-conceito.png, e1-frente.png, e1-lado.png
- **O que a imagem não mostra bem:** cauda atrás do corpo
- **Partes finas (viram planos):** orelhas, chama
- **Rosto:** olhos grandes
- **Jeito de se mover:** trota

### Prompt usado
```text
small fox creature with flame tail
```
"""


@pytest.fixture
def pasta_ok(tmp_path):
    pasta = tmp_path / "raposa-teste"
    pasta.mkdir()
    (pasta / "ficha.md").write_text(FICHA_OK, encoding="utf-8")
    for vista in ("conceito", "frente", "lado"):
        Image.new("RGB", (1024, 1024), "white").save(pasta / f"e1-{vista}.png")
    yield pasta
    shutil.rmtree(MODELOS / "raposa-teste", ignore_errors=True)


def test_modelo_aponta_o_que_falta():
    entrada = ler_ficha(MODELO)
    codigos = {e["codigo"] for e in entrada["erros"]}
    assert {"nome_modelo", "sem_conceito", "sem_prompt"} <= codigos
    assert len(entrada["estagios"]) == 3
    assert contratos.problemas("entrada", entrada) == []


def test_cli_modelo_sai_com_erro(capsys):
    try:
        assert cli.main(["ficha", str(MODELO)]) == 1
        texto = capsys.readouterr().out
        assert "falta e1-conceito.png" in texto
        assert len(texto.splitlines()) <= 20
    finally:
        shutil.rmtree(MODELOS / "_modelo", ignore_errors=True)


def test_ficha_completa(pasta_ok):
    entrada = ler_ficha(pasta_ok)
    assert entrada["erros"] == []
    e1 = entrada["estagios"][0]
    assert e1["categoria_confirmada"] == {"plano": "quadrúpede", "nicho": "canídeo"}
    assert e1["altura_blocos"] == 0.8
    assert e1["estagio_tabela"] == "inicial" and e1["estagio_cobblemon"] == "1º de 3"
    assert e1["imagens"]["costas"] is None and e1["imagens"]["lado"] == "e1-lado.png"
    assert e1["prompt"] == "small fox creature with flame tail"
    assert entrada["destino"] == ["roblox", "minecraft"]


def test_cli_grava_entrada(pasta_ok, capsys):
    assert cli.main(["ficha", str(pasta_ok)]) == 0
    assert (MODELOS / "raposa-teste" / "entrada.json").exists()
    assert "quadrúpede › canídeo" in capsys.readouterr().out


def test_imagem_fora_do_tamanho_e_categoria_errada(pasta_ok):
    Image.new("RGB", (600, 400), "white").save(pasta_ok / "e1-conceito.png")
    texto = (pasta_ok / "ficha.md").read_text(encoding="utf-8").replace("Quadrupede > canideo", "voador > canideo")
    (pasta_ok / "ficha.md").write_text(texto, encoding="utf-8")
    entrada = ler_ficha(pasta_ok)
    assert any(a["codigo"] == "tamanho_imagem" for a in entrada["avisos"])
    assert any(e["codigo"] == "categoria_invalida" for e in entrada["erros"])
