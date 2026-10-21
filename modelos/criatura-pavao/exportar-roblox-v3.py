"""Exporta o pavão v3 aprovado (nota 8,5) para o Roblox (.glb), com as funções do `criaturas exportar`.

O modelo aprovado fica fora da pasta padrão do pipeline (revisao-v3/), por isso este atalho.
Saída: modelos/criatura-pavao/export/roblox/criatura-pavao-e1.glb (+ textura-roblox.png ampliada 8×).
"""
import json
from pathlib import Path

from PIL import Image

from criaturas import bbmodelo, exportar

ROOT = Path(__file__).resolve().parent
FILE = ROOT / "revisao-v3" / "criatura-pavao-e1-v3.bbmodel"
SAIDA = ROOT / "export" / "roblox"
BASE = "criatura-pavao-e1"

modelo = bbmodelo.ler(FILE)
SAIDA.mkdir(parents=True, exist_ok=True)
tex = modelo.textura.convert("RGBA")
ampliada = SAIDA / "textura-roblox.png"
tex.resize((tex.width * 8, tex.height * 8), Image.NEAREST).save(ampliada)  # o Roblox filtra: pixel art precisa de 8×
copia = exportar.copia_roblox(FILE, ampliada, SAIDA, BASE)
glb = SAIDA / f"{BASE}.glb"
exportar.exportar_glb(copia, glb)
locs = exportar.acrescentar_locators(glb, modelo)
erros, avisos, resumo = exportar.verificar_glb(glb, modelo)
(SAIDA / "relatorio.json").write_text(json.dumps({"erros": erros, "avisos": avisos, "resumo": resumo, "locators": locs},
                                                 ensure_ascii=False, indent=2), encoding="utf-8")
print(f"{glb.name}: {glb.stat().st_size} bytes; {resumo}")
for e in erros + avisos:
    print(" ", e)
