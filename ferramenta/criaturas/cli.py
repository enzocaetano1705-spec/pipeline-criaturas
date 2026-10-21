"""Linha de comando `criaturas`. Os subcomandos chegam na Fase 1 (item 1.2)."""

import argparse
import sys

from criaturas import __version__


def montar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="criaturas",
        description="Pipeline de criaturas 3D: conceito -> modelo cubificado, textura, rig e animações.",
    )
    parser.add_argument("--version", action="version", version=f"criaturas {__version__}")
    return parser


def _saida_utf8() -> None:
    # No Windows o console usa cp1252 por padrão e os acentos saem quebrados.
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    _saida_utf8()
    parser = montar_parser()
    parser.parse_args(argv)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
