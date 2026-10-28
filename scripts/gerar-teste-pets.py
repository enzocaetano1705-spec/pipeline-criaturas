"""Gera configuração e instalador do laboratório local de pets; não publica assets."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "exportacoes/roblox/teste-pets"


def gerar():
    register = json.loads((ROOT / "exportacoes/roblox/criaturas.json").read_text(encoding="utf-8"))
    forms = {}
    all_clips = {}
    for item in register["criaturas"]:
        ident = item["nome"].split("_")[-1]
        model = json.loads((ROOT / item["fonte"]).read_text(encoding="utf-8"))
        clips = {a["name"]: {"Length": a["length"], "Loop": a.get("loop") == "loop"} for a in model["animations"]}
        all_clips[ident] = clips
        manifest = json.loads((ROOT / f"exportacoes/roblox/pavao/{item['nome']}-importacao.json").read_text(encoding="utf-8"))
        # Hash canônico calculado pelo pipeline; não depende da serialização deste script.
        source_hash = manifest.get("fonte_sha256") or manifest.get("colisao", {}).get("fonte_sha256")
        forms[ident] = {"Id": ident, "Name": item["nome"], "Animations": clips,
                        "WalkUnits": 11.111111 if ident == "F2" else 13.333333,
                        "RunUnits": 44.444444 if ident == "F2" else 37.414966,
                        "CombatWalkUnits": 11.111111, "CombatRunUnits": 28.882576,
                        "Range": {"F1": 2.8, "F2": 6.5, "F3": 9.5}[ident],
                        "SourceHash": source_hash}
    meta = json.loads((ROOT / "modelos/criatura-pavao/f3/corrida-v1/animacoes.json").read_text(encoding="utf-8"))
    forms["F3"]["UpperBones"] = meta["camadas"]["ossos"]
    forms["F3"]["Phases"] = {k: v["tempo_destino"] for k, v in meta["corridas"].items() if isinstance(v, dict) and "tempo_destino" in v}
    forms["F3"]["Phases"]["combat_walk_start"] = .30
    forms["F2"]["Phases"] = {"run_start": .432, "run_stop": .8}
    config = {"Version": 1, "WalkSpeed": 16, "RunSpeed": 28, "FollowOffset": [-7, 0, 11],
              "Acceleration": 38, "Deceleration": 55, "DummyRespawn": 3,
              "SkillCooldown": 3, "SkillRadius": 17, "Forms": forms,
              "Dummies": {"Small": {"Name": "AlvoPequeno", "Label": "Alvo pequeno", "Size": [3, 3, 3], "HP": 250, "X": -7, "Z": -32},
                          "Large": {"Name": "AlvoGrande", "Label": "Alvo médio / grande", "Size": [10, 10, 10], "HP": 1200, "X": 9, "Z": -32}},
              "Attacks": {"F1": {"Duration": .7, "Hits": [{"Time": .3, "Damage": 6}]},
                          "attack_stomp": {"Duration": 1.25, "Hits": [{"Time": .575, "Damage": 14}]},
                          "attack_tail_kick": {"Duration": 2.15, "Hits": [{"Time": .762857, "Damage": 24}]},
                          "attack_spin": {"Duration": 1.65, "Area": True, "Hits": [{"Time": .64, "Damage": 22}]},
                          "attack_low": {"Duration": 1.42, "Hits": [{"Time": .54, "Damage": 22}]},
                          "attack_left": {"Duration": 1.32, "Hits": [{"Time": .42538078, "Damage": 28}]},
                          "attack_combo": {"Duration": 2.2, "Hits": [{"Time": .49, "Damage": 22}, {"Time": 1.19, "Damage": 44}]}}}
    payload = json.dumps(config, ensure_ascii=False, separators=(",", ":"))
    (OUT / "Config.luau").write_text('-- Gerado por scripts/gerar-teste-pets.py\nreturn game:GetService("HttpService"):JSONDecode([====[' + payload + ']====])\n', encoding="utf-8")
    (OUT / "animacoes-origem.json").write_text(json.dumps(all_clips, indent=2) + "\n", encoding="utf-8")
    sources = {p.stem: p.read_text(encoding="utf-8") for p in OUT.glob("*.luau") if p.stem != "Instalar"}
    installer = (ROOT / "scripts/templates/instalar-teste-pets.luau").read_text(encoding="utf-8")
    for name in ("Config", "AnimationDriver", "Dummies", "Server", "Client"):
        installer = installer.replace("-- SOURCE:" + name, "[========[" + sources[name] + "]========]")
    (OUT / "Instalar.luau").write_text(installer, encoding="utf-8")
    print(f"Teste de pets: {len(forms)} formas, {sum(map(len, all_clips.values()))} clipes; instalador gerado.")


if __name__ == "__main__":
    gerar()
