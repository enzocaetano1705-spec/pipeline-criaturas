"""Copia skills/ para .claude/skills/ (Claude Code) e .agents/skills/ (Codex e Antigravity).

Edite só skills/. Rode depois de mudar uma skill:
    uv run python scripts/sincronizar-skills.py
Cada skill de destino é substituída pela de skills/; skills de destino que não existem mais em
skills/ só são apagadas se tiverem a marca deste script (nada criado à mão é apagado).
"""

import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ORIGEM = RAIZ / "skills"
DESTINOS = [RAIZ / ".claude" / "skills", RAIZ / ".agents" / "skills"]
MARCA = ".sincronizada"


def sincronizar() -> list[str]:
    linhas = []
    skills = sorted(p for p in ORIGEM.iterdir() if p.is_dir() and (p / "SKILL.md").exists())
    for destino in DESTINOS:
        destino.mkdir(parents=True, exist_ok=True)
        for skill in skills:
            alvo = destino / skill.name
            if alvo.exists():
                if not (alvo / MARCA).exists():
                    linhas.append(f"pulei {alvo.relative_to(RAIZ)}: existe e não foi criada por este script")
                    continue
                shutil.rmtree(alvo)
            shutil.copytree(skill, alvo)
            (alvo / MARCA).write_text("copiada de skills/ por scripts/sincronizar-skills.py; edite a original\n", encoding="utf-8")
            linhas.append(f"{skill.name} -> {alvo.relative_to(RAIZ).as_posix()}")
        nomes = {s.name for s in skills}
        for velha in destino.iterdir():
            if velha.is_dir() and velha.name not in nomes and (velha / MARCA).exists():
                shutil.rmtree(velha)
                linhas.append(f"removida {velha.relative_to(RAIZ).as_posix()} (não existe mais em skills/)")
    return linhas


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("\n".join(sincronizar()) or "nenhuma skill em skills/")
