"""Atlas por face, densidade explícita, margens, recorte alfa e máscaras de região."""

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageColor

# Cantos de cada face em índices XYZ binários; winding externo, UV em pixels top-left.
FACES = {
    "north": ([0, 2, 3, 1], (0, 1)),
    "south": ([5, 7, 6, 4], (0, 1)),
    "west": ([4, 6, 2, 0], (2, 1)),
    "east": ([1, 3, 7, 5], (2, 1)),
    "up": ([2, 6, 7, 3], (0, 2)),
    "down": ([4, 0, 1, 5], (0, 2)),
}


def ilhas(plano: dict, config: dict) -> list[dict]:
    """Empacotamento shelf determinístico; falha em vez de reduzir densidade."""
    res, pad, density = config["resolucao"], config["margem"], config["densidade"]
    islands = []
    for cube in plano["cubos"]:
        dims = [b - a for a, b in zip(cube["from"], cube["to"])]
        for face, (_, axes) in FACES.items():
            # Planos são convertidos em lâminas com espessura explícita no worker.
            size = [max(1, math.ceil(dims[i] * density)) for i in axes]
            islands.append({"cubo": cube["nome"], "face": face, "tamanho": size,
                            "regiao": cube["regiao"], "densidade": density})
    islands.sort(key=lambda i: (-i["tamanho"][1], -i["tamanho"][0], i["cubo"], i["face"]))
    x = y = row = 0
    for island in islands:
        w, h = island["tamanho"]
        if x + w + 2 * pad > res:
            x, y, row = 0, y + row, 0
        if w + 2 * pad > res or y + h + 2 * pad > res:
            raise ValueError("atlas insuficiente: aumente a resolução ou revise a densidade no plano")
        island["retangulo"] = [x + pad, y + pad, w, h]
        x += w + 2 * pad
        row = max(row, h + 2 * pad)
    return islands


def gerar(job: dict, destino: Path) -> dict:
    cfg = job["textura"]
    res, pad, scale = cfg["resolucao"], cfg["margem"], cfg["escala_exportacao"]
    islands = ilhas(job["plano"], cfg)
    cubes = {c["nome"]: c for c in job["plano"]["cubos"]}
    region_ids = {name: i + 1 for i, name in enumerate(cfg["regioes"])}
    mask = np.zeros((res, res), dtype=np.uint8)
    # Cada variante recolore só os papéis solicitados, antes de pintar detalhes protegidos.
    variants = {"base": {}, **cfg["variantes"]}
    images = {}
    for variant, overrides in variants.items():
        pixels = np.zeros((res, res, 4), dtype=np.uint8)
        for island in islands:
            x, y, w, h = island["retangulo"]
            cube, face = cubes[island["cubo"]], island["face"]
            role = island["regiao"]
            color = np.array(ImageColor.getrgb(overrides.get(role, cfg["regioes"][role]["cor"])), float)
            factor = 1.08 if face == "up" else 0.78 if face == "down" else 1.0
            tile = np.empty((h, w, 4), dtype=np.uint8)
            tile[..., :3] = np.clip(np.round(color * factor), 0, 255).astype(np.uint8)
            tile[..., 3] = 255
            tile_mask = np.full((h, w), region_ids[role], dtype=np.uint8)
            if cube.get("recorte") == "losango" and face in ("north", "south"):
                yy, xx = np.mgrid[:h, :w]
                tile[..., 3] = np.where(abs((xx + .5) / w * 2 - 1) + abs((yy + .5) / h * 2 - 1) <= 1.3, 255, 0)
            if cube.get("pintura") == "olhos" and face == "north":
                # Arte da fixture, nunca aplicada implicitamente a uma criatura real.
                for col in (max(0, w // 4 - 1), min(w - 1, 3 * w // 4)):
                    tile[max(0, h // 3):max(1, h // 3 + 2), col:col + 1] = (20, 25, 36, 255)
                    tile_mask[max(0, h // 3):max(1, h // 3 + 2), col:col + 1] = 0
                island["detalhes_protegidos"] = True
            pixels[y:y + h, x:x + w] = tile
            # Margem RGBA duplicada: evita mistura entre ilhas. Mantém alfa dos recortes.
            pixels[y-pad:y+h+pad, x-pad:x+w+pad] = np.pad(tile, ((pad, pad), (pad, pad), (0, 0)), mode="edge")
            # Índice zero também protege olhos; margens acompanham a região para recoloração futura.
            mask[y-pad:y+h+pad, x-pad:x+w+pad] = np.pad(tile_mask, ((pad, pad), (pad, pad)), mode="edge")
        im = Image.fromarray(pixels)
        base = f"textura-{variant}.png"
        im.save(destino / base)
        export = f"textura-{variant}-roblox.png"
        im.resize((res * scale, res * scale), Image.Resampling.NEAREST).save(destino / export)
        images[variant] = {"base": base, "roblox": export}
    Image.fromarray(mask).save(destino / "mascara-regioes.png")
    return {"resolucao": res, "escala_exportacao": scale, "margem": pad, "densidade": cfg["densidade"],
            "ocupacao_util": round(sum(i["tamanho"][0]*i["tamanho"][1] for i in islands)/(res*res), 5),
            "regioes": region_ids, "imagens": images, "ilhas": islands}
