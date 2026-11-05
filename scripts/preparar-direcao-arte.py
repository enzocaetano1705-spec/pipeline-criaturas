"""Prepara prompts locais de criação/revisão. Não chama IA, rede nem serviço pago."""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "docs/direcao-arte/prompts"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("briefing", type=Path)
    parser.add_argument("--saida", type=Path, required=True, help="pasta nova; nunca sobrescreve")
    args = parser.parse_args()
    try:
        data = json.loads(args.briefing.read_text(encoding="utf-8"))
        for key in ("versao", "id", "conceitos", "arquetipo_combate", "numero_estagios", "orcamento", "limites_piloto"):
            if key not in data:
                raise ValueError(f"briefing sem {key}")
        stages = data["numero_estagios"]
        if data["versao"] != 1 or (stages is not None and (type(stages) is not int or not 1 <= stages <= 5)):
            raise ValueError("versão ou quantidade de estágios inválida")
        if stages is None and any(data.get("aprovacoes", {}).get(k) for k in ("arte", "vistas")):
            raise ValueError("quantidade de estágios deve estar definida antes de aprovar arte/vistas")
        if not isinstance(data["arquetipo_combate"], str) or not data["arquetipo_combate"].strip():
            raise ValueError("informe o arquétipo de combate no briefing")
        if not isinstance(data["conceitos"], list) or len(data["conceitos"]) < 2 or any(not isinstance(c, str) or not c.strip() for c in data["conceitos"]):
            raise ValueError("informe pelo menos dois conceitos em texto")
        json.dumps(data, allow_nan=False)
        if args.saida.exists():
            raise ValueError("saída já existe; escolha outra pasta para preservar o trabalho")
        templates = sorted(TEMPLATES.glob("*.md"))
        if len(templates) != 4:
            raise ValueError("kit incompleto: quatro prompts são obrigatórios")
        # Validar todos os templates antes de escrever qualquer saída.
        texts = {p.name: p.read_text(encoding="utf-8") for p in templates}
        if any(t.count("{{BRIEFING_JSON}}") != 1 for t in texts.values()):
            raise ValueError("marcador de briefing ausente/duplicado no kit")
        payload = "```json\n" + json.dumps(data, ensure_ascii=False, indent=2) + "\n```"
        args.saida.mkdir(parents=True, exist_ok=False)
        (args.saida/"briefing.json").write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        for name, text in texts.items():
            (args.saida/name).write_text(text.replace("{{BRIEFING_JSON}}", payload), encoding="utf-8")
        manifest = {"versao": 1, "briefing_sha256": sha(args.briefing),
                    "templates_sha256": {p.name: sha(p) for p in templates},
                    "artefatos_sha256": {p.name: sha(p) for p in sorted(args.saida.iterdir())},
                    "gasto": 0, "rede": False, "geracao_executada": False,
                    "proximo_passo": "usar 01-criador em conversa; proposta em 02-revisor; aprovar antes de arte/vistas"}
        (args.saida/"manifesto.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        print(f"Kit preparado: {args.saida.resolve()}")
        print("Quatro prompts, briefing e hashes; nenhuma imagem gerada ou chamada paga.")
        return 0
    except (ValueError, KeyError, OSError) as exc:
        print("Direção de arte: " + str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
