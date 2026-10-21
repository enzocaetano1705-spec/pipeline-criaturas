"""Ponte para o servidor MCP do Blockbench desktop (plugin MCP), pelo cliente ferramenta/js/mcp-desktop.ts.

O app precisa estar aberto com o plugin carregado; `abrir` usa o blockbench_launch do motor headless
para abrir um arquivo e esperar o servidor responder.
"""

import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

from criaturas import motor
from criaturas.caminhos import RAIZ

URL = os.environ.get("BLOCKBENCH_MCP_URL", "http://localhost:3000/bb-mcp")
CLIENTE = RAIZ / "ferramenta" / "js" / "mcp-desktop.ts"


class DesktopErro(RuntimeError):
    pass


def respondendo(url: str = URL, tempo: float = 2.0) -> bool:
    pedido = urllib.request.Request(url, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "sonda", "version": "0"}}}).encode(),
        headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"})
    try:
        with urllib.request.urlopen(pedido, timeout=tempo) as r:
            return r.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def chamar(ferramenta: str, argumentos: dict | None = None, url: str = URL) -> dict:
    """Resultado da ferramenta ({content, isError}); levanta DesktopErro se falhar."""
    bun = motor._bun()
    with tempfile.TemporaryDirectory(prefix="criaturas-desktop-") as tmp:
        arq = Path(tmp) / "args.json"
        arq.write_text(json.dumps(argumentos or {}, ensure_ascii=False), encoding="utf-8")
        proc = subprocess.run([str(bun), "run", str(CLIENTE), url, ferramenta, f"@{arq}"], capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=900, cwd=str(RAIZ))
    if proc.returncode not in (0, 1) or not proc.stdout.strip():
        raise DesktopErro(f"{ferramenta}: {(proc.stderr or proc.stdout).strip()[:400]}")
    resultado = json.loads(proc.stdout.strip().splitlines()[-1])
    if resultado.get("isError"):
        texto = " ".join(c.get("text", "") for c in resultado.get("content", []) if c.get("type") == "text")
        raise DesktopErro(f"{ferramenta}: {texto[:400]}")
    return resultado


def ferramentas(url: str = URL) -> list[str]:
    bun = motor._bun()
    proc = subprocess.run([str(bun), "run", str(CLIENTE), url, "--list"], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=120, cwd=str(RAIZ))
    if proc.returncode != 0:
        raise DesktopErro(proc.stderr.strip()[:400])
    return json.loads(proc.stdout.strip().splitlines()[-1])


def texto(resultado: dict) -> str:
    return "\n".join(c.get("text", "") for c in resultado.get("content", []) if c.get("type") == "text")


def abrir(arquivo: Path, esperar_ms: int = 60000) -> str:
    """Abre o arquivo no Blockbench desktop (abre o app se estiver fechado) e espera o MCP responder."""
    r = motor.chamar("blockbench_launch", {"file": motor.relativo(arquivo), "wait_for_mcp_ms": esperar_ms})
    return json.dumps(r) if not isinstance(r, str) else r
