"""Onde ficam as coisas no repositório (ver docs/convencoes.md, Pastas e arquivos)."""

import re
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
MODELOS = RAIZ / "modelos"
REFERENCIA = RAIZ / "referencia"
MEDIDAS_JSON = REFERENCIA / "medidas.json"
MOTOR = RAIZ / "externos" / "blockbench-mcp-plugin"


def sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def chave(texto: str) -> str:
    """Forma comparável de um nome: minúsculas, sem acento, só letras e números."""
    return re.sub(r"[^a-z0-9]+", " ", sem_acento(texto).lower()).strip()


def pasta_modelo(nome: str) -> Path:
    return MODELOS / nome


def pasta_estagio(nome: str, estagio: str) -> Path:
    return MODELOS / nome / estagio


def relativo(caminho: Path) -> str:
    """Caminho relativo à raiz do repositório, com barras normais (para relatórios)."""
    try:
        return Path(caminho).resolve().relative_to(RAIZ).as_posix()
    except ValueError:
        return Path(caminho).as_posix()
