"""Ponte para o motor headless do Blockbench (externos/blockbench-mcp-plugin, GPL-3.0).

Roda o motor como programa separado, pelo `headless/call.ts`: um processo por chamada,
argumentos num arquivo JSON temporário, resultado lido do stdout. Nenhum código do
motor é copiado para cá.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path

from criaturas.caminhos import MODELOS, MOTOR

BUN_DIR = MOTOR / "node_modules" / "bun" / "bin"
CALL_TS = MOTOR / "headless" / "call.ts"
TEMPO_LIMITE = 900


class MotorErro(RuntimeError):
    """O motor devolveu erro ou não rodou. `saida` tem o texto que ele imprimiu."""

    def __init__(self, ferramenta: str, mensagem: str, saida: str = ""):
        super().__init__(f"{ferramenta}: {mensagem}")
        self.ferramenta = ferramenta
        self.saida = saida


def disponivel() -> bool:
    return CALL_TS.exists() and any(BUN_DIR.glob("bun*"))


def _bun() -> Path:
    for nome in ("bun.exe", "bun"):
        if (BUN_DIR / nome).exists():
            return BUN_DIR / nome
    raise MotorErro("motor", f"Bun não encontrado em {BUN_DIR}; rode o item 0.3 do plano")


def relativo(caminho, raiz: Path = MODELOS) -> str:
    """Caminho como o motor espera: relativo à raiz `--root`, com barras normais."""
    p = Path(caminho)
    if p.is_absolute():
        p = p.resolve().relative_to(Path(raiz).resolve())
    return p.as_posix()


def chamar(ferramenta: str, argumentos: dict | None = None, raiz: Path = MODELOS):
    """Chama uma ferramenta do motor. Devolve o JSON da resposta, ou o texto se não for JSON."""
    if not disponivel():
        raise MotorErro(ferramenta, "motor headless não instalado (item 0.3 do plano)")
    ambiente = dict(os.environ)
    # o call.ts sobe o servidor chamando `bun` pelo nome
    ambiente["PATH"] = str(BUN_DIR) + os.pathsep + ambiente.get("PATH", "")
    with tempfile.TemporaryDirectory(prefix="criaturas-motor-") as tmp:
        arq = Path(tmp) / "args.json"
        arq.write_text(json.dumps(argumentos or {}, ensure_ascii=False), encoding="utf-8")
        try:
            proc = subprocess.run(
                [str(_bun()), "run", str(CALL_TS), "--root", str(Path(raiz).resolve()), ferramenta, f"@{arq}"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=TEMPO_LIMITE, env=ambiente, cwd=str(MOTOR),
            )
        except subprocess.TimeoutExpired as e:
            raise MotorErro(ferramenta, f"passou de {TEMPO_LIMITE} s") from e
    saida = (proc.stdout or "").strip()
    if proc.returncode != 0:
        detalhe = saida or (proc.stderr or "").strip() or f"código {proc.returncode}"
        raise MotorErro(ferramenta, detalhe.splitlines()[0][:400], saida + (proc.stderr or ""))
    try:
        return json.loads(saida)
    except json.JSONDecodeError:
        return saida


def criar(arquivo, nome: str, largura: int = 64, altura: int = 64, raiz: Path = MODELOS) -> dict:
    return chamar("bbmodel_create", {"file": relativo(arquivo, raiz), "format": "bedrock", "name": nome,
                                     "resolution": {"width": largura, "height": altura}, "overwrite": True}, raiz)


def editar(arquivo, operacoes: list[dict], raiz: Path = MODELOS) -> dict:
    return chamar("bbmodel_edit", {"file": relativo(arquivo, raiz), "operations": operacoes}, raiz)


def validar(arquivo, raiz: Path = MODELOS, **extras) -> dict:
    return chamar("bbmodel_validate", {"file": relativo(arquivo, raiz), **extras}, raiz)


def validar_animacoes(arquivo, raiz: Path = MODELOS, **extras) -> dict:
    return chamar("bbmodel_validate_animations", {"file": relativo(arquivo, raiz), **extras}, raiz)


def exportar_bedrock(arquivo, saida, raiz: Path = MODELOS) -> dict:
    return chamar("bbmodel_export_bedrock_geometry", {"file": relativo(arquivo, raiz), "output": relativo(saida, raiz)}, raiz)


def folha_de_contato(arquivo, raiz: Path = MODELOS, **extras) -> dict[str, Path]:
    """Render headless: {vista: caminho do PNG} (front, right, back, left, three-quarter, top)."""
    texto = chamar("bbmodel_contact_sheet", {"file": relativo(arquivo, raiz), **extras}, raiz)
    vistas = {}
    for linha in str(texto).splitlines():
        nome, sep, caminho = linha.partition(": ")
        if sep and caminho.lower().endswith(".png"):
            vistas[nome.strip()] = Path(caminho.strip())
    return vistas


def resumo_validacao(resultado: dict) -> tuple[int, int, list[str]]:
    """(erros, avisos, mensagens curtas) de um resultado de bbmodel_validate*."""
    s = resultado.get("summary", {})
    mensagens = []
    for gate in resultado.get("gates", []):
        for v in gate.get("violations", []):
            texto = v.get("message") if isinstance(v, dict) else str(v)
            mensagens.append(f"[{gate.get('severity')}] {gate.get('id')}: {texto}")
    return int(s.get("errors", 0)), int(s.get("warnings", 0)), mensagens
