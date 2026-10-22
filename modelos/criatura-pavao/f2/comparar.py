"""Folha: prancha do usuário em cima, modelo embaixo (frente, lado, costas, 3/4)."""
from pathlib import Path
from PIL import Image, ImageDraw
from criaturas import bbmodelo, render
AQUI = Path(__file__).resolve().parent
m = bbmodelo.ler(AQUI / "criatura-pavao-e2.bbmodel")
f = render.folha(m, lado_px=420)
q = f.width // 2
ren = {"frente": f.crop((0, 0, q, q)), "lado": f.crop((q, 0, 2 * q, q)), "costas": f.crop((0, q, q, 2 * q)), "3-4": f.crop((q, q, 2 * q, 2 * q))}
L = 380
out = Image.new("RGB", (4 * L, 2 * L), "white")
for i, k in enumerate(("frente", "lado", "costas", "3-4")):
    v = Image.open(AQUI / "vistas" / f"{k}.png").convert("RGB")
    v.thumbnail((L, L))
    out.paste(v, (i * L + (L - v.width) // 2, (L - v.height) // 2))
    out.paste(ren[k].resize((L, L)), (i * L, L))
out.save(AQUI / "comparacao-prancha.png")
