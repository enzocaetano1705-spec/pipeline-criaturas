"""Relatório de cada etapa (relatorio.json) e o resumo curto que vai para o terminal."""

import json
from datetime import datetime
from pathlib import Path

from criaturas import contratos

MAX_LINHAS = 20


def msg(codigo: str, texto: str, parte: str | None = None) -> dict:
    m = {"codigo": codigo, "texto": texto}
    if parte:
        m["parte"] = parte
    return m


def ler_json(caminho: Path):
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


def gravar_json(caminho: Path, dados, contrato: str | None = None) -> Path:
    """Grava `dados` em JSON legível; valida antes se houver contrato."""
    if contrato:
        contratos.validar(contrato, dados)
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return caminho


def registrar(pasta: Path, criatura: str, estagio: str | None, etapa: str, ok: bool, *,
              erros=(), avisos=(), arquivos=(), resumo=None, hashes=None) -> Path:
    """Atualiza a entrada `etapa` de `pasta/relatorio.json`, mantendo as outras."""
    caminho = Path(pasta) / "relatorio.json"
    dados = ler_json(caminho) if caminho.exists() else {"criatura": criatura, "estagio": estagio, "etapas": {}}
    dados["etapas"][etapa] = {
        "ok": bool(ok),
        "quando": datetime.now().isoformat(timespec="seconds"),
        "erros": list(erros),
        "avisos": list(avisos),
        "arquivos": [str(a) for a in arquivos],
        "resumo": resumo or {},
    }
    if hashes:
        dados.setdefault("hashes", {}).update(hashes)
    return gravar_json(caminho, dados, "relatorio")


def imprimir(linhas: list[str]) -> None:
    """Imprime no máximo MAX_LINHAS; o resto fica no JSON em disco."""
    if len(linhas) > MAX_LINHAS:
        corte = len(linhas) - (MAX_LINHAS - 1)
        linhas = linhas[: MAX_LINHAS - 1] + [f"… mais {corte} linha(s) no relatório em disco"]
    for linha in linhas:
        print(linha)


def linhas_mensagens(titulo: str, mensagens, limite: int = 6) -> list[str]:
    mensagens = list(mensagens)
    if not mensagens:
        return []
    saida = [f"{titulo} ({len(mensagens)}):"]
    saida += [f"  - {m['texto']}" for m in mensagens[:limite]]
    if len(mensagens) > limite:
        saida.append(f"  … e mais {len(mensagens) - limite}")
    return saida
