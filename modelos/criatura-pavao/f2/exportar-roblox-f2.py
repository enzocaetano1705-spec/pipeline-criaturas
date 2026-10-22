"""Exporta o pavão F2 aprovado para o Roblox (.glb), com as funções do `criaturas exportar`.

Saída: modelos/criatura-pavao/export/roblox-f2/criatura-pavao-e2.glb (+ textura ampliada).
O atlas é 256: a textura vai ampliada para 1024 (×4, sem suavizar), o máximo que o Roblox aceita sem reduzir.
"""
import json
from pathlib import Path

from PIL import Image

from criaturas import bbmodelo, exportar

AQUI = Path(__file__).resolve().parent
FILE = AQUI / "criatura-pavao-e2.bbmodel"
SAIDA = AQUI.parent / "export" / "roblox-f2"
BASE = "criatura-pavao-e2"
MAX_ROBLOX = 1024

modelo = bbmodelo.ler(FILE)
fora = exportar.uv_fora_do_atlas(modelo)
if fora:  # o Roblox dá a volta no atlas
    raise SystemExit(f"UV fora da textura: {fora[:3]}")
SAIDA.mkdir(parents=True, exist_ok=True)
tex = modelo.textura.convert("RGBA")
fator = max(1, MAX_ROBLOX // tex.width)
ampliada = SAIDA / "textura-roblox.png"
tex.resize((tex.width * fator, tex.height * fator), Image.NEAREST).save(ampliada)
copia = exportar.copia_roblox(FILE, ampliada, SAIDA, BASE)
glb = SAIDA / f"{BASE}.glb"
exportar.exportar_glb(copia, glb)
locs = exportar.acrescentar_locators(glb, modelo)
erros, avisos, resumo = exportar.verificar_glb(glb, modelo)
(SAIDA / "relatorio.json").write_text(json.dumps({"erros": erros, "avisos": avisos, "resumo": resumo, "locators": locs,
                                                 "textura": f"{tex.width}×{fator} = {tex.width * fator}"},
                                                ensure_ascii=False, indent=2), encoding="utf-8")
print(f"{glb.name}: {glb.stat().st_size // 1024} KB; textura ×{fator}; {resumo}")
for e in erros + avisos:
    print(" ", e)
