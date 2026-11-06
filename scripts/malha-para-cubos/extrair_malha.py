"""Blender headless: FBX/GLB/OBJ -> grade de voxels sólida com cor de superfície (.npz).

Uso:
  blender -b --factory-startup -P extrair_malha.py -- <malha> <saida.npz> [--comprimento 64] [--voxel 0.5]

Converte para os eixos do Blockbench (Y para cima, frente em -Z, direita da criatura em +X),
escala para que o comprimento (frente-trás) tenha `--comprimento` unidades, põe o chão em y=0
e centraliza X e Z. Ocupação por paridade de raios nos três eixos (voto 2 de 3), o que tolera
malhas com pequenos furos. Cada voxel de superfície recebe a cor da textura no ponto mais
próximo da malha.
"""

import json
import sys
import time
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:]
entrada, saida = Path(argv[0]), Path(argv[1])
opcoes = {"--comprimento": 64.0, "--voxel": 0.5}
for i, a in enumerate(argv):
    if a in opcoes:
        opcoes[a] = float(argv[i + 1])
COMPRIMENTO, H = opcoes["--comprimento"], opcoes["--voxel"]
t0 = time.time()

bpy.ops.wm.read_factory_settings(use_empty=True)
ext = entrada.suffix.lower()
if ext == ".fbx":
    bpy.ops.import_scene.fbx(filepath=str(entrada))
elif ext in (".glb", ".gltf"):
    bpy.ops.import_scene.gltf(filepath=str(entrada))
elif ext == ".obj":
    bpy.ops.wm.obj_import(filepath=str(entrada))
else:
    raise SystemExit(f"formato não suportado: {ext}")

objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
if not objs:
    raise SystemExit("nenhuma malha no arquivo")

# ---------- junta todas as malhas em triângulos com UV ----------
verts, tris, uvs, imgs_tri = [], [], [], []
imagens = []
for o in objs:
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.transform(o.matrix_world)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    uv_layer = bm.loops.layers.uv.active
    base = len(verts)
    verts.extend([v.co.copy() for v in bm.verts])
    mats = o.data.materials
    for f in bm.faces:
        tris.append([base + v.index for v in f.verts])
        uvs.append([tuple(l[uv_layer].uv) if uv_layer else (0.0, 0.0) for l in f.loops])
        img = None
        if f.material_index < len(mats) and mats[f.material_index] and mats[f.material_index].node_tree:
            for n in mats[f.material_index].node_tree.nodes:
                if n.type == "TEX_IMAGE" and n.image:
                    img = n.image
                    break
        if img is not None and img not in imagens:
            imagens.append(img)
        imgs_tri.append(imagens.index(img) if img is not None else -1)
    bm.free()

V = np.array([tuple(v) for v in verts], float)
T = np.array(tris, int)
UV = np.array(uvs, float)
IMG = np.array(imgs_tri, int)

# Blender (frente -Y, cima +Z, direita da criatura -X) -> Blockbench (frente -Z, cima +Y, direita +X)
V = np.stack([-V[:, 0], V[:, 2], V[:, 1]], axis=1)
lo, hi = V.min(0), V.max(0)
escala = COMPRIMENTO / (hi[2] - lo[2])
V = (V - [(lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2]) * escala
lo, hi = V.min(0), V.max(0)

# ---------- texturas em numpy (reduzidas para 1024 no máximo) ----------
texturas = []
for img in imagens:
    w, h = img.size
    if max(w, h) > 1024:
        img.scale(min(w, 1024), min(h, 1024))
        w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    texturas.append((px.reshape(h, w, 4)[:, :, :3] * 255).clip(0, 255).astype(np.uint8))


def cor_no_ponto(tri, p):
    a, b, c = V[T[tri]]
    v0, v1, v2 = b - a, c - a, p - a
    d00, d01, d11 = v0 @ v0, v0 @ v1, v1 @ v1
    d20, d21 = v2 @ v0, v2 @ v1
    den = d00 * d11 - d01 * d01 or 1e-12
    w1 = (d11 * d20 - d01 * d21) / den
    w2 = (d00 * d21 - d01 * d20) / den
    bary = np.clip([1 - w1 - w2, w1, w2], 0, 1)
    bary /= bary.sum() or 1
    if IMG[tri] < 0:
        return (180, 180, 180)
    u, v = bary @ UV[tri]
    tex = texturas[IMG[tri]]
    hh, ww = tex.shape[:2]
    x = int((u % 1.0) * ww) % ww
    y = int((v % 1.0) * hh) % hh
    return tuple(int(c) for c in tex[y, x])


# ---------- voxelização por paridade ----------
bvh = BVHTree.FromPolygons([tuple(v) for v in V], T.tolist(), all_triangles=True, epsilon=0.0)
origem = lo - H
dims = np.ceil((hi - lo) / H).astype(int) + 3
centros = [origem[k] + (np.arange(dims[k]) + 0.5) * H for k in range(3)]


def paridade(eixo):
    """Voxels dentro segundo raios ao longo de `eixo` (pares entrada/saída)."""
    dentro = np.zeros(dims, bool)
    a, b = [k for k in range(3) if k != eixo]
    d = Vector([1.0 if k == eixo else 0.0 for k in range(3)])
    inicio = origem[eixo] - H
    comprimento = (dims[eixo] + 2) * H
    for i, ca in enumerate(centros[a]):
        for j, cb in enumerate(centros[b]):
            p = [0.0, 0.0, 0.0]
            p[a], p[b], p[eixo] = ca, cb, inicio
            o = Vector(p)
            hits, andou = [], 0.0
            while True:
                loc, _n, _i, dist = bvh.ray_cast(o, d, comprimento - andou)
                if loc is None:
                    break
                hits.append(loc[eixo])
                o = loc + d * 1e-4
                andou += dist + 1e-4
            if len(hits) < 2:
                continue
            hits.sort()
            # remove toques duplicados (raio passando por aresta)
            limpos = [hits[0]]
            for hval in hits[1:]:
                if hval - limpos[-1] > 1e-3:
                    limpos.append(hval)
            for k in range(0, len(limpos) - 1, 2):
                c = centros[eixo]
                sel = (c > limpos[k]) & (c < limpos[k + 1])
                idx = [slice(None)] * 3
                idx[a], idx[b] = i, j
                linha = dentro[tuple(idx)]
                linha[sel] = True
    return dentro


votos = paridade(0).astype(np.uint8) + paridade(1) + paridade(2)
ocupado = votos >= 2

# ---------- superfície e cor ----------
viz = np.zeros_like(ocupado)
for eixo in range(3):
    for passo in (1, -1):
        viz |= ~np.roll(ocupado, passo, axis=eixo)
superficie = ocupado & viz
sup_idx = np.argwhere(superficie)
sup_cor = np.zeros((len(sup_idx), 3), np.uint8)
for n, (i, j, k) in enumerate(sup_idx):
    p = Vector((centros[0][i], centros[1][j], centros[2][k]))
    loc, _nrm, tri, _d = bvh.find_nearest(p)
    sup_cor[n] = cor_no_ponto(tri, np.array(loc))

tri_cor = np.array([cor_no_ponto(t, V[T[t]].mean(0)) for t in range(len(T))], np.uint8)

saida.parent.mkdir(parents=True, exist_ok=True)
np.savez_compressed(saida, ocupado=ocupado, origem=origem, voxel=H, sup_idx=sup_idx, sup_cor=sup_cor,
                    verts=V.astype(np.float32), tris=T.astype(np.int32), tri_cor=tri_cor)
meta = {"entrada": entrada.name, "comprimento": COMPRIMENTO, "voxel": H, "escala_aplicada": escala,
        "limites": [lo.round(3).tolist(), hi.round(3).tolist()], "dims": dims.tolist(),
        "voxels_ocupados": int(ocupado.sum()), "voxels_superficie": int(len(sup_idx)),
        "triangulos": int(len(T)), "texturas": len(texturas), "segundos": round(time.time() - t0, 1)}
saida.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# ---------- renders de referência da malha (lado e 3/4) para a folha de comparação ----------
renders = (saida.parent / "entrada" / "renders").resolve()  # o Blender lê caminho relativo como relativo ao .blend
renders.mkdir(parents=True, exist_ok=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"
sc.display.shading.color_type = "TEXTURE"
sc.render.resolution_x = sc.render.resolution_y = 512
sc.render.film_transparent = True
pts = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
bmin = Vector([min(p[k] for p in pts) for k in range(3)])
bmax = Vector([max(p[k] for p in pts) for k in range(3)])
centro_b = (bmin + bmax) / 2
tam_b = max(bmax - bmin) * 1.1
cam_data = bpy.data.cameras.new("cam")
cam_data.type = "ORTHO"
cam_data.ortho_scale = tam_b
cam = bpy.data.objects.new("cam", cam_data)
sc.collection.objects.link(cam)
sc.camera = cam
for nome_r, d in {"malha-lado": Vector((1, 0, 0)), "malha-34": Vector((0.7, -0.7, 0.35))}.items():
    d = d.normalized()
    cam.location = centro_b + d * tam_b * 3
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = str(renders / f"{nome_r}.png")
    bpy.ops.render.render(write_still=True)
print("EXTRAIR", json.dumps(meta, ensure_ascii=False))
