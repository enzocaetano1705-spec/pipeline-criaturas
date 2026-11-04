"""Validação antes de iniciar Blender; contrato compartilhado + extensão isolada."""

import copy
import json
import math
import re
from pathlib import Path

from criaturas import contratos, rig


def validar(job: dict) -> dict:
    job = copy.deepcopy(job)
    for key in ("versao", "tipo", "id", "estagio", "categoria", "briefing", "interpretacao", "plano", "textura", "animacao", "limites"):
        if key not in job:
            raise ValueError(f"entrada Blender: falta {key}")
    if job["versao"] != 1 or job["tipo"] != "sintetica":
        raise ValueError("backend v1 habilitado para fixtures sintéticas; criatura real exige referências e aprovações do protocolo")
    if not re.fullmatch(r"[a-z][a-z0-9_]*", job["id"]):
        raise ValueError("id inválido")
    if not re.fullmatch(r"e[1-9][0-9]*", job["estagio"]) or not all(job["categoria"].get(k) for k in ("plano", "nicho")):
        raise ValueError("estágio e categoria são obrigatórios")
    # Rejeitar NaN/Infinity inclusive em campos adicionais.
    json.dumps(job, allow_nan=False)
    plan = job["plano"]
    contratos.validar("plano_cubos", plan)
    bones = {b["nome"]: b for b in plan["ossos"]}
    if len(bones) != len(plan["ossos"]) or "Raiz" in bones or "root" not in bones or "body" not in bones:
        raise ValueError("ossos duplicados/reservados ou root/body ausentes")
    if bones["root"]["pai"] is not None or bones["root"]["pivo"] != [0, 0, 0] or bones["body"]["pai"] != "root":
        raise ValueError("rig exige root na origem e body filho de root")
    if any(b["pai"] == "root" and b["nome"] != "body" for b in bones.values()):
        raise ValueError("só body pode ser filho direto de root")
    for name, bone in bones.items():
        seen = {name}
        parent = bone["pai"]
        while parent is not None:
            if parent not in bones or parent in seen:
                raise ValueError("hierarquia inválida ou ciclo: " + name)
            seen.add(parent)
            parent = bones[parent]["pai"]
        if any(bone.get("rotacao", [0, 0, 0])):
            raise ValueError("v1 requer repouso sem rotação óssea; oriente volumes no plano, não descarte a rotação")
    cfg = job["textura"]
    for key in ("resolucao", "margem", "escala_exportacao"):
        if not isinstance(cfg[key], int) or cfg[key] < (2 if key == "margem" else 1):
            raise ValueError("textura: resolução/escala inteiras positivas e margem >= 2")
    if cfg["resolucao"] & (cfg["resolucao"] - 1) or cfg["resolucao"] * cfg["escala_exportacao"] > 4096:
        raise ValueError("textura: resolução potência de dois e exportação <= 4096")
    if cfg["densidade"] <= 0 or cfg["densidade"] > 16:
        raise ValueError("densidade fora de (0,16]")
    if len(cfg["regioes"]) > 254 or not cfg["regioes"]:
        raise ValueError("regiões: entre 1 e 254")
    for role in cfg["regioes"].values():
        if not isinstance(role.get("mutavel"), bool) or not re.fullmatch(r"#[0-9a-fA-F]{6}", role.get("cor", "")):
            raise ValueError("região exige mutavel booleano e cor #RRGGBB")
    if any(not re.fullmatch(r"[a-z][a-z0-9_]*", n) or n == "base" for n in cfg["variantes"]):
        raise ValueError("nome de variante inválido/reservado")
    for changes in cfg["variantes"].values():
        if any(r not in cfg["regioes"] or not cfg["regioes"][r]["mutavel"] for r in changes):
            raise ValueError("variante altera região protegida")
        if any(not re.fullmatch(r"#[0-9a-fA-F]{6}", color) for color in changes.values()):
            raise ValueError("cor de variante deve ser #RRGGBB")
    cubes = plan["cubos"]
    if len({c["nome"] for c in cubes}) != len(cubes):
        raise ValueError("cubos duplicados")
    for cube in cubes:
        if cube["osso"] not in bones or cube["osso"] == "root":
            raise ValueError("cubo sem osso válido ou com influência em root")
        if cube.get("regiao") not in cfg["regioes"]:
            raise ValueError("cubo sem região de cor")
        dims = [b - a for a, b in zip(cube["from"], cube["to"])]
        if min(dims) < 0 or sum(d > 0 for d in dims) < 2 or (0 in dims and cube.get("tipo") != "plano"):
            raise ValueError("cubo degenerado; plano requer exatamente duas dimensões positivas")
        unsupported = set(cube) - {"nome", "osso", "parte", "tipo", "from", "to", "regiao", "pintura", "recorte"}
        if unsupported:
            raise ValueError("campos de cubo não suportados (não serão ignorados): " + ", ".join(sorted(unsupported)))
        if cube.get("pintura") not in (None, "olhos") or cube.get("recorte") not in (None, "losango"):
            raise ValueError("pintura/recorte desconhecido")
    limits = job["limites"]
    if any(not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0 for v in limits.values()):
        raise ValueError("limites devem ser positivos e finitos")
    if len(cubes) > limits["cubos"] or len(cubes) * 12 > min(20000, limits["triangulos"]):
        raise ValueError("orçamento de geometria excedido")
    if "locators" not in plan:
        parts = []
        for name in bones:
            own = [c for c in cubes if c["osso"] == name]
            if own:
                parts.append({"id": name, "from": [min(c["from"][i] for c in own) for i in range(3)],
                              "to": [max(c["to"][i] for c in own) for i in range(3)]})
        plan["locators"] = rig.locators(parts)
        # Sombra/seleção seguem a raiz, sem bob do body.
        for loc in plan["locators"]:
            if loc["nome"] == "loc_ground":
                loc["osso"] = "root"
    names = [l["nome"] for l in plan["locators"]]
    if len(set(names)) != len(names) or not {"loc_top", "loc_center", "loc_ground"} <= set(names):
        raise ValueError("locators obrigatórios ausentes/duplicados")
    if any(l["osso"] not in bones for l in plan["locators"]):
        raise ValueError("locator sem osso")
    anim = job["animacao"]
    required = {"idle", "walk", "run", "attack_physical"}
    if anim["helper"] != "bipede_ik_v1" or set(anim["duracoes"]) != required:
        raise ValueError("v1: helper bipede_ik_v1 e quatro clipes explícitos")
    for side in ("left", "right"):
        chain = ["body", f"leg_{side}", f"shin_{side}", f"foot_{side}"]
        if any(n not in bones for n in chain) or any(bones[b]["pai"] != a for a, b in zip(chain, chain[1:])):
            raise ValueError("helper requer cadeia body/leg/shin/foot de ambos os lados")
        points = [bones[n]["pivo"] for n in chain[1:]]
        if any(abs(p[0] - points[0][0]) > 1e-6 or abs(p[2] - points[0][2]) > 1e-6 for p in points):
            raise ValueError("helper v1 requer pernas verticais no repouso")
        if not points[0][1] > points[1][1] > points[2][1] > 0:
            raise ValueError("pivôs da perna fora de ordem")
    if not isinstance(anim["fps"], int) or not 24 <= anim["fps"] <= 120:
        raise ValueError("fps deve estar entre 24 e 120")
    for name, duration in anim["duracoes"].items():
        if not .4 <= duration <= 10 or abs(round(duration * anim["fps"]) - duration * anim["fps"]) > 1e-6:
            raise ValueError("duração deve ser positiva e múltipla do frame")
    for mode in ("walk", "run"):
        if not .5 <= anim[f"apoio_{mode}"] < .9 or anim[f"passo_{mode}"] <= 0 or anim[f"altura_{mode}"] <= 0:
            raise ValueError("parâmetros de passada inválidos")
    events = anim["eventos"]
    if set(events) != {"attack_physical"} or set(events["attack_physical"]) != {"HitFrame", "CancelOpen", "RecoveryStart"}:
        raise ValueError("eventos obrigatórios do ataque ausentes")
    ev = events["attack_physical"]
    if not 0 < ev["HitFrame"] < ev["RecoveryStart"] <= ev["CancelOpen"] < anim["duracoes"]["attack_physical"]:
        raise ValueError("eventos fora do clipe ou ordem inválida")
    contratos.validar("plano_cubos", plan)
    return job


def ler(path: Path) -> dict:
    return validar(json.loads(path.read_text(encoding="utf-8")))
