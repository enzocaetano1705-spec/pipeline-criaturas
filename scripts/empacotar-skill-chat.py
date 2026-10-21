"""Monta skills-chat/criaturas-3d-chat.zip, a versão da skill para o chat do claude.ai (item 9.3).

As referências saem de docs/ na hora de empacotar, para nunca ficarem desatualizadas:
    uv run python scripts/empacotar-skill-chat.py
"""

import re
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
FONTE = RAIZ / "skills-chat" / "criaturas-3d-chat"
SAIDA = RAIZ / "skills-chat" / "criaturas-3d-chat.zip"


def _sem_frontmatter(texto: str) -> str:
    return re.sub(r"^---\n.*?\n---\n", "", texto, count=1, flags=re.S).lstrip()


def _secoes(texto: str, inicio: str, fim: str) -> str:
    """Do título `inicio` (inclusive) até o título `fim` (exclusive)."""
    a = texto.index(inicio)
    b = texto.index(fim, a)
    return texto[a:b].rstrip() + "\n"


def referencias() -> dict[str, str]:
    leia = _sem_frontmatter((RAIZ / "docs" / "criaturas" / "LEIA-ME.md").read_text(encoding="utf-8"))
    leia = leia.replace("docs/criaturas/", "").replace("`_modelo/`", "o modelo de ficha")
    ficha = (RAIZ / "docs" / "criaturas" / "_modelo" / "ficha.md").read_text(encoding="utf-8")
    pesquisa = _sem_frontmatter((RAIZ / "docs" / "pesquisa" / "categorias-criaturas.md").read_text(encoding="utf-8"))
    categorias = "# Categorias de criaturas\n\n" + _secoes(pesquisa, "## Taxonomia", "## Limitações")
    return {"referencias/requisitos-imagens.md": leia, "referencias/ficha-modelo.md": ficha,
            "referencias/categorias.md": categorias}


def empacotar() -> Path:
    with zipfile.ZipFile(SAIDA, "w", zipfile.ZIP_DEFLATED) as z:
        for arq in sorted(FONTE.rglob("*")):
            if arq.is_file():
                z.write(arq, f"criaturas-3d-chat/{arq.relative_to(FONTE).as_posix()}")
        for nome, texto in referencias().items():
            z.writestr(f"criaturas-3d-chat/{nome}", texto)
    return SAIDA


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    saida = empacotar()
    with zipfile.ZipFile(saida) as z:
        print(f"{saida.relative_to(RAIZ).as_posix()}: " + ", ".join(z.namelist()))
