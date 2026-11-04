"""Orquestração host: entradas -> atlas/malha -> Blender -> validação -> manifesto."""

import hashlib
import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw

from . import atlas, entrada, glb, malha

PACKAGE = Path(__file__).parent
ROOT = PACKAGE.parents[2]


def dump(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def localizar(explicit=None):
    if explicit or os.environ.get("CRIATURAS_BLENDER"):
        path = Path(explicit or os.environ["CRIATURAS_BLENDER"])
        if not path.is_file():
            raise ValueError("Blender configurado não existe: "+str(path))
        return path.resolve()
    found = shutil.which("blender")
    if found:
        return Path(found).resolve()
    base = Path(os.environ.get("ProgramFiles", "C:/Program Files"))/"Blender Foundation"
    candidates = sorted(base.glob("Blender */blender.exe"), reverse=True)
    if candidates:
        return candidates[0]
    raise ValueError("Blender não encontrado; informe --executavel. Instalação exige ação do usuário.")


def worker(exe, mode, dest):
    command = [str(exe), "--background", "--factory-startup", "--disable-autoexec", "--threads", "2",
               "--python-exit-code", "1", "--python", str(PACKAGE/"worker.py"), "--", mode, str(dest)]
    with (dest/f"blender-{mode}.log").open("w", encoding="utf-8") as log:
        proc = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=1200, cwd=ROOT,
                              creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if proc.returncode:
        raise ValueError(f"Blender {mode} falhou (código {proc.returncode}); veja blender-{mode}.log")
    return command


def previews(job, dest):
    names = ("frente", "lado", "costas", "tres-quartos")
    sheet = Image.new("RGB", (768, 440), "#202738")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 8), "BLENDER / FIXTURE SINTETICA / SEM APROVACAO ARTISTICA", fill="white")
    for i, name in enumerate(names):
        image = Image.open(dest/f"vista-{name}.png").convert("RGB").resize((192, 192))
        sheet.paste(image, (i*192, 26))
        draw.text((i*192+6, 220), name, fill="white")
    for i, name in enumerate(job["animacao"]["duracoes"]):
        for j in range(4):
            frame = Image.open(dest/f"previa-{name}-{j*3:02}.png").convert("RGB").resize((96, 96))
            sheet.paste(frame, (j*96+i%2*384, 242+i//2*94))
        draw.text((i%2*384+4, 244+i//2*94), name, fill="white")
        frames = []
        for j in range(12):
            im = Image.open(dest/f"previa-{name}-{j:02}.png").convert("RGB")
            d = ImageDraw.Draw(im)
            d.text((4, 4), "BLENDER / "+name, fill="white")
            frames.append(im)
        frames[0].save(dest/f"previa-{name}.gif", save_all=True, append_images=frames[1:],
                       duration=round(job["animacao"]["duracoes"][name]*1000/12), loop=0, disposal=2)
    sheet.save(dest/"folha.png")


def gates(job, author, reimported):
    errors, warnings = [], []
    lim = job["limites"]
    for name, m in author.items():
        for field in ("erro_skin_unidades", "erro_pe_ik_unidades", "erro_locators_unidades"):
            if m[field] > lim["erro_reimportacao_unidades"]:
                errors.append(f"{name}: {field} = {m[field]}")
        if m["piso_min_unidades"] < -lim["penetracao_piso"]:
            errors.append(f"{name}: piso = {m['piso_min_unidades']}")
        if m["passo_max_por_amostra"] > lim["salto_quadro_unidades"]:
            errors.append(f"{name}: salto entre amostras")
        if name in ("idle", "walk", "run") and m["loop_erro_unidades"] > .001:
            errors.append(f"{name}: loop descontínuo")
        if m["deslizamento_apoio_por_amostra"] > lim["deslizamento_apoio"]:
            errors.append(f"{name}: deslizamento do apoio")
        if m["triagem_obb_penetracao"] > .15:
            errors.append(f"{name}: colisão visual na triagem {m['triagem_pior_par']}")
        if m["projecao_body_fora_apoio_max"] > .1:
            warnings.append(f"{name}: pivô body fora do envelope de apoio aproximado em até {m['projecao_body_fora_apoio_max']} un; revisar dinâmica visual")
    for name, m in reimported["clipes"].items():
        if max(m["erro_superficie_unidades"], m["erro_pivos_unidades"], m["erro_locators_unidades"]) > lim["erro_reimportacao_unidades"]:
            errors.append(f"{name}: reimportação divergente")
    return errors, warnings


def construir(source, dest, executable=None):
    start = time.perf_counter()
    source, dest = Path(source).resolve(), Path(dest).resolve()
    job = entrada.ler(source)
    if dest.exists():
        raise ValueError("saída já existe; escolha uma pasta nova para preservar edições")
    exe = localizar(executable)
    # Antes de qualquer mutação: contrato, orçamento de atlas, Blender e validador disponíveis.
    atlas.ilhas(job["plano"], job["textura"])
    if not (ROOT/"ferramenta/js/node_modules/gltf-validator").is_dir() or not shutil.which("node"):
        raise ValueError("validador Khronos ausente; preparar dependência conforme AGENTS.md")
    dest.mkdir(parents=True, exist_ok=False)
    dump(dest/"entrada-normalizada.json", job)
    shutil.copy2(source, dest/"entrada-original.json")
    dump(dest/"briefing.json", job["briefing"])
    dump(dest/"interpretacao.json", job["interpretacao"])
    dump(dest/"plano-cubos.json", job["plano"])
    try:
        texture = atlas.gerar(job, dest)
        dump(dest/"atlas.json", texture)
        dump(dest/"malha.json", malha.gerar(job, texture))
        prepared = time.perf_counter()
        command = worker(exe, "construir", dest)
        built = time.perf_counter()
        results = {name: glb.validar(dest/f"{job['id']}-{name}.glb", job, texture) for name in texture["imagens"]}
        dump(dest/"validacao-glb.json", results)
        worker(exe, "reimportar", dest)
        author = json.loads((dest/"validacao-autoria.json").read_text(encoding="utf-8"))
        imported = json.loads((dest/"validacao-reimportacao.json").read_text(encoding="utf-8"))
        errors, warnings = gates(job, author, imported)
        errors += [f"GLB {name}: {', '.join(r['erros'])}" for name, r in results.items() if not r["ok"]]
        previews(job, dest)
        animation_meta = {"versao": 1, "animacoes": {n: {"duracao": d, "loop": n in ("idle", "walk", "run")}
                                                    for n, d in job["animacao"]["duracoes"].items()},
                          "golpes": {n: {"eventos": e} for n, e in job["animacao"]["eventos"].items()},
                          "mapa_consumidor": {"idle": "idle", "walk": "walk", "run": "run", "attack_basic": "attack_physical"}}
        dump(dest/"animacoes.json", animation_meta)
        dump(dest/"locators.json", {"unidade": "1/16 stud por unidade", "eixos": "Y-up, frente -Z",
                                    "locators": job["plano"]["locators"], "studio": "criar Attachments nos Bones; empty glTF pode ser descartado"})
        dump(dest/"entrega-roblox.json", {"versao": 1, "id": job["id"], "familia_esqueleto": "bipede",
             "arquivo": f"{job['id']}-base.glb", "textura": texture["imagens"]["base"]["roblox"],
             "animacoes": "animacoes.json", "locators": "locators.json", "escala_studio": 1,
             "altura_repouso_studs": (max(c["to"][1] for c in job["plano"]["cubos"])-min(c["from"][1] for c in job["plano"]["cubos"]))/16,
             "frente_gltf": [0, 0, -1], "importacao": "Rig Type Custom; uma MeshPart com Bones. Conferir orientação da Hitbox pelo bico.",
             "material": {"ResampleMode": "Pixelated", "AlphaMode": "Transparency", "Metalness": 0, "Roughness": 1},
             "status": "fixture; validada em arquivo/Blender; ensaio no Roblox pendente"})
        report = {"ok": not errors, "erros": errors, "avisos": warnings,
                  "validacao": {"automatica": not errors, "artistica": "não avaliada pelo usuário", "roblox": "não ensaiado nesta sessão"},
                  "duracoes_segundos": {"preparo": prepared-start, "processo_construcao": built-prepared,
                                        "validacao_e_previas": time.perf_counter()-built, "total": time.perf_counter()-start}}
        dump(dest/"relatorio.json", report)
        scripts = {p.name: sha(p) for p in sorted(PACKAGE.glob("*.py"))}
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        artifacts = {p.name: sha(p) for p in sorted(dest.iterdir()) if p.is_file() and p.suffix != ".log"}
        dump(dest/"manifesto.json", {"versao": 1, "backend": "blender", "gerado_utc": datetime.now(timezone.utc).isoformat(),
             "entrada_sha256": sha(source), "scripts_sha256": scripts, "git_base": revision,
             "blender_executavel": str(exe), "blender_sha256": sha(exe), "comando": command,
             "seed": None, "artefatos_sha256": artifacts, "semantica_sha256": semantica(dest),
             "uso_harness": {"modelo": "não medido por este comando", "esforco": "não medido", "tokens": None, "creditos": None}})
        return report
    except Exception as exc:
        dump(dest/"falha.json", {"ok": False, "erro": str(exc), "duracao_segundos": time.perf_counter()-start})
        raise


def semantica(dest):
    # Não comparar bytes do .blend (metadados/endereço internos). Cena e poses são comparadas pelo conteúdo.
    names = ["entrada-normalizada.json", "atlas.json", "malha.json", "validacao-autoria.json", "amostras-autoria.json"]
    data = {n: json.loads((dest/n).read_text(encoding="utf-8")) for n in names}
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def conferir(dest):
    dest = Path(dest)
    manifest = json.loads((dest/"manifesto.json").read_text(encoding="utf-8"))
    missing = [n for n, h in manifest["artefatos_sha256"].items() if not (dest/n).is_file() or sha(dest/n) != h]
    if missing:
        raise ValueError("artefatos ausentes/modificados: "+", ".join(missing[:8]))
    changed = [n for n, h in manifest["scripts_sha256"].items() if not (PACKAGE/n).is_file() or sha(PACKAGE/n) != h]
    return {"ok": not missing, "scripts_mudaram": changed, "semantica_sha256": semantica(dest)}


def cmd(args):
    try:
        if args.acao == "conferir":
            report = conferir(args.entrada)
            print("Blender: integridade conferida.")
            if report["scripts_mudaram"]:
                print("Scripts mudaram desde a geração: "+", ".join(report["scripts_mudaram"]))
            return 0
        if args.acao == "comparar":
            if not args.outra:
                raise ValueError("comparar exige duas pastas geradas")
            a, b = Path(args.entrada), Path(args.outra)
            conferir(a)
            conferir(b)
            same = semantica(a) == semantica(b)
            dump(b/"reconstrucao.json", {"ok": same, "primeira": str(a.resolve()), "segunda": str(b.resolve()),
                                       "semantica_a": semantica(a), "semantica_b": semantica(b),
                                       "glb_identico": {p.name: sha(p) == sha(b/p.name) for p in a.glob("*.glb")}})
            print("Reconstrução: "+("mesma geometria, atlas e poses." if same else "DIVERGENTE; veja reconstrucao.json"))
            return 0 if same else 1
        if not args.saida:
            raise ValueError("construir exige --saida nova (nunca sobrescreve)")
        print("Blender: construção em lote sem interface; logs na saída.", flush=True)
        report = construir(args.entrada, args.saida, args.executavel)
        print(f"Blender: {'OK' if report['ok'] else 'FALHOU'}; {len(report['erros'])} erros; {len(report['avisos'])} avisos.")
        print("Saída: "+str(Path(args.saida).resolve()))
        for error in report["erros"][:10]:
            print("  "+error)
        return 0 if report["ok"] else 1
    except (ValueError, KeyError, OSError, subprocess.TimeoutExpired) as exc:
        print("Blender: "+str(exc))
        return 1


def opcoes(parser):
    parser.add_argument("acao", choices=("construir", "conferir", "comparar"))
    parser.add_argument("entrada", help="JSON de entrada, ou pasta gerada para conferir/comparar")
    parser.add_argument("outra", nargs="?", help="segunda pasta para comparar reconstruções")
    parser.add_argument("--saida", help="pasta nova; recusada se já existir")
    parser.add_argument("--executavel", help="caminho do Blender; alternativa: CRIATURAS_BLENDER")
    parser.set_defaults(func=cmd)
