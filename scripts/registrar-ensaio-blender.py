"""Congela evidência curta de duas reconstruções; não copia modelos do pavão."""

import argparse
import json
import shutil
from pathlib import Path

from criaturas.blender_backend import executar, glb

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("primeira", type=Path)
    parser.add_argument("segunda", type=Path)
    parser.add_argument("--saida", required=True, type=Path)
    parser.add_argument("--preservacao", type=Path)
    args = parser.parse_args()
    for folder in (args.primeira, args.segunda):
        if executar.conferir(folder)["scripts_mudaram"]:
            raise ValueError("scripts mudaram; reconstruir antes de congelar a evidência")
        report = json.loads((folder/"relatorio.json").read_text(encoding="utf-8"))
        if not report["ok"]:
            raise ValueError("ensaio contém erros")
    if executar.semantica(args.primeira) != executar.semantica(args.segunda):
        raise ValueError("reconstrução divergente")
    args.saida.mkdir(parents=True, exist_ok=False)
    copies = ["atlas.json", "relatorio.json", "validacao-autoria.json", "validacao-reimportacao.json", "validacao-glb.json",
              "manifesto.json", "execucao-blender.json", "entrega-roblox.json", "animacoes.json", "locators.json", "folha.png",
              "previa-idle.gif", "previa-walk.gif", "previa-run.gif", "previa-attack_physical.gif", "mascara-regioes.png",
              "textura-base.png", "textura-ambar.png", "textura-violeta.png"]
    for name in copies:
        target = "manifesto-origem.json" if name == "manifesto.json" else name
        shutil.copy2(args.primeira/name, args.saida/target)
    manifests = [json.loads((f/"manifesto.json").read_text(encoding="utf-8")) for f in (args.primeira, args.segunda)]
    reports = [json.loads((f/"relatorio.json").read_text(encoding="utf-8")) for f in (args.primeira, args.segunda)]
    preserved = None
    if args.preservacao:
        snapshot = json.loads(args.preservacao.read_text(encoding="utf-8"))
        changed = [name for name, digest in snapshot.items() if not (ROOT/name).is_file() or executar.sha(ROOT/name) != digest]
        preserved = {"arquivos_conferidos": len(snapshot), "alterados_desde_snapshot": changed,
                     "snapshot_sha256": executar.sha(args.preservacao)}
    audit = {}
    config = json.loads((ROOT/"exportacoes/roblox/criaturas.json").read_text(encoding="utf-8"))
    by_name = {c["nome"]: c for c in config["criaturas"]}
    for file in (ROOT/"exportacoes/roblox/pavao").glob("*.glb"):
        reader = glb.GLB(file)
        coords = [reader.accessor(p["attributes"]["TEXCOORD_0"]) for m in reader.g["meshes"] for p in m["primitives"]]
        uv = [float(min(a.min() for a in coords)), float(max(a.max() for a in coords))]
        audit[file.stem] = {"glb_sha256": executar.sha(file), "uv": uv,
             "dentro_tolerancia_original_0_002": uv[0] >= -.002 and uv[1] <= 1.002,
             "imagens_embutidas": len(reader.g.get("images", [])), "materiais": len(reader.g.get("materials", [])),
             "malhas": len(reader.g.get("meshes", [])), "superamostrar": by_name[file.stem].get("superamostrar"),
             "acao": "somente leitura; sem reexportação"}
    record = {"tipo_custo": "engenharia do backend; não produção recorrente de criatura real",
              "data": "2026-11-04", "harness": {"produto": "Codex desktop", "familia_modelo_contexto": "GPT-6",
              "id_exato_modelo": None, "esforco": None, "contexto": "repositório, pedido anexado, protocolos e documentação oficial",
              "tokens": None, "creditos": None, "custo_monetario": None, "fonte_uso": "não exposto pelo harness"},
              "reconstrucao": {"ok": True, "semantica_sha256": executar.semantica(args.primeira),
                 "pastas": [str(f.resolve()) for f in (args.primeira, args.segunda)],
                 "glbs_identicos": {p.name: executar.sha(p) == executar.sha(args.segunda/p.name) for p in args.primeira.glob("*.glb")}},
              "execucoes": [{"gerado_utc": m["gerado_utc"], "duracoes_segundos": r["duracoes_segundos"],
                             "entrada_sha256": m["entrada_sha256"], "glb_sha256": {n: h for n, h in m["artefatos_sha256"].items() if n.endswith(".glb")}}
                            for m, r in zip(manifests, reports)],
              "preservacao": preserved, "auditoria_pavao": audit,
              "falhas_retrabalho_engenharia": [
                  "Icosphere de exibição criada pelo importador contada inicialmente como segunda malha; conferir malha com armature.",
                  "Frames iniciados em 1 deslocavam timestamps de exportação; autoria ajustada para t=0.",
                  "FPS 24 do processo limpo antes de importar distorcia tempo; configurar FPS antes do importador.",
                  "AABB acusava falso contato ao girar corpo; triagem trocada por SAT de caixas orientadas.",
                  "Amostragem 60 Hz insuficiente para tolerância escolhida no ataque; bake 120 Hz e revisão 240 Hz.",
                  "Máscara genérica incluía olhos; índice 0 agora protege detalhes e regiões incluem margens."],
              "aprovacao_artistica": "pendente; fixture técnica", "teste_roblox": "não executado", "vencedor": None}
    executar.dump(args.saida/"ensaio.json", record)
    print(f"Evidência registrada em {args.saida}; reconstrução idêntica; consumo não medido.")


if __name__ == "__main__":
    main()
