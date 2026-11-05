"""Audita metadados públicos, sem baixar imagens, preparar treino ou fazer upload."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from urllib.request import Request, urlopen

URL = "https://worldofmiscrits.com/miscrits.json"
PREFIXOS = ("Dark ", "Light ", "Blighted ", "Foil ", "Elite ")


def auditar(data):
    if not isinstance(data, list) or any(not isinstance(c, dict) or type(c.get("id")) is not int
        or not isinstance(c.get("names"), list) or not c["names"]
        or any(not isinstance(n, str) or not n.strip() for n in c["names"]) for c in data):
        raise ValueError("catálogo inválido: lista de registros com names não vazio esperada")
    if len({c["id"] for c in data}) != len(data):
        raise ValueError("catálogo inválido: IDs repetidos")
    first = {c["names"][0].casefold(): c["id"] for c in data}
    groups, counts, matched = [], Counter(), []
    for c in data:
        name, base_id, found = c["names"][0], c["id"], None
        for prefix in PREFIXOS:
            if name.casefold().startswith(prefix.casefold()):
                counts[prefix.strip()] += 1
                found = prefix.strip()
                base = name[len(prefix):]
                if base.casefold() in first:
                    base_id = first[base.casefold()]
                    matched.append({"id": c["id"], "nome": name, "base_id": base_id, "base_nome": base, "prefixo": found})
                break
        groups.append({"id": c["id"], "nomes": c["names"], "elemento": c.get("element"),
                       "grupo_por_nome": base_id, "prefixo_candidato": found})
    summary = {"fonte": URL, "registros_linhagens": len(data),
               "entradas_de_estagio": sum(len(c["names"]) for c in data),
               "contagem_formas": dict(Counter(len(c["names"]) for c in data)),
               "prefixos_candidatos": dict(counts), "variantes_com_base_identificada_por_nome": len(matched),
               "grupos_distintos_por_nome": len({g["grupo_por_nome"] for g in groups}),
               "exemplos_variantes": matched[:8],
               "limites": "Agrupamento por nome/prefixo, não duplicidade visual ou autoria/licença. Sem baixar imagens, treino ou upload."}
    return summary, groups


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True, help="pasta nova; manter biblioteca de terceiros fora do repositório")
    parser.add_argument("--arquivo", type=Path, help="catálogo JSON local para repetir a auditoria sem rede")
    args = parser.parse_args()
    try:
        if args.saida.exists():
            raise ValueError("saída já existe; escolha outra pasta")
        if args.arquivo:
            raw = args.arquivo.read_bytes()
        else:
            with urlopen(Request(URL, headers={"User-Agent": "pipeline-criaturas-estudo/1.0"}), timeout=45) as response:
                raw = response.read()
        summary, groups = auditar(json.loads(raw))
        summary["catalogo_sha256"] = hashlib.sha256(raw).hexdigest()
        args.saida.mkdir(parents=True, exist_ok=False)
        (args.saida/"catalogo-publico.json").write_bytes(raw)
        for name, value in (("resumo.json", summary), ("inventario-metadados.json", groups)):
            (args.saida/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        print(f"Catálogo: {summary['registros_linhagens']} linhagens / {summary['entradas_de_estagio']} estágios.")
        print(f"Agrupamento: {summary['variantes_com_base_identificada_por_nome']} variantes com base por nome; {summary['grupos_distintos_por_nome']} grupos.")
        print("Sem imagens baixadas, treino, upload ou cobrança.")
        print(f"Saída: {args.saida.resolve()}")
        return 0
    except (ValueError, KeyError, OSError) as exc:
        print("Auditoria Miscrits: "+str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
