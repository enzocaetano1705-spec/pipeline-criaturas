"""Leitura glTF isolada e validação do artefato realmente exportado."""

import io
import json
import struct
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
TYPES = {5120: "i1", 5121: "u1", 5122: "<i2", 5123: "<u2", 5125: "<u4", 5126: "<f4"}
SIZES = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


class GLB:
    def __init__(self, path):
        data = Path(path).read_bytes()
        magic, version, size = struct.unpack_from("<4sII", data)
        if magic != b"glTF" or version != 2 or size != len(data):
            raise ValueError("cabeçalho GLB inválido")
        json_size, kind = struct.unpack_from("<I4s", data, 12)
        if kind != b"JSON":
            raise ValueError("chunk JSON ausente")
        self.g = json.loads(data[20:20+json_size])
        bin_size, kind = struct.unpack_from("<I4s", data, 20+json_size)
        if kind != b"BIN\0":
            raise ValueError("chunk binário ausente")
        self.binary = data[28+json_size:28+json_size+bin_size]

    def accessor(self, index):
        a = self.g["accessors"][index]
        if "sparse" in a:
            raise ValueError("accessor sparse não suportado no perfil Blender v1")
        view = self.g["bufferViews"][a["bufferView"]]
        dtype = np.dtype(TYPES[a["componentType"]])
        width = SIZES[a["type"]]
        offset = view.get("byteOffset", 0)+a.get("byteOffset", 0)
        stride = view.get("byteStride", dtype.itemsize*width)
        result = np.ndarray((a["count"], width), dtype, self.binary, offset, (stride, dtype.itemsize)).copy()
        if a.get("normalized") and a["componentType"] != 5126:
            result = result.astype(float)/np.iinfo(dtype).max
        return result

    def image(self, index=0):
        spec = self.g["images"][index]
        view = self.g["bufferViews"][spec["bufferView"]]
        start = view.get("byteOffset", 0)
        return Image.open(io.BytesIO(self.binary[start:start+view["byteLength"]])).convert("RGBA")

    def world_rest(self):
        from .movimento import transform

        result = {}
        parents = {child: i for i, n in enumerate(self.g["nodes"]) for child in n.get("children", [])}
        def calc(i):
            if i in result:
                return result[i]
            n = self.g["nodes"][i]
            if "matrix" in n:
                local = np.array(n["matrix"]).reshape(4, 4).T
            else:
                x, y, z, w = n.get("rotation", [0, 0, 0, 1])
                rotation = np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
                local = transform(n.get("translation", [0, 0, 0]))
                local[:3, :3] = rotation @ np.diag(n.get("scale", [1, 1, 1]))
            result[i] = calc(parents[i]) @ local if i in parents else local
            return result[i]
        for i in range(len(self.g["nodes"])):
            calc(i)
        return result


def validar(path: Path, job: dict, atlas: dict) -> dict:
    result = subprocess.run(["node", str(ROOT/"js"/"validar-gltf.mjs"), str(path)],
                            capture_output=True, text=True, encoding="utf-8", timeout=120)
    if result.returncode:
        raise ValueError("validador Khronos indisponível: "+result.stderr[-300:])
    khronos = json.loads(result.stdout.strip().splitlines()[-1])
    reader = GLB(path)
    g = reader.g
    errors = []
    if khronos["erros"]:
        errors.append("validador Khronos")
    meshes = [n for n in g["nodes"] if "mesh" in n]
    if len(meshes) != 1 or len(g.get("skins", [])) != 1 or "skin" not in meshes[0]:
        raise ValueError("GLB exige uma malha com uma skin")
    skin = g["skins"][0]
    joint_names = [g["nodes"][i]["name"] for i in skin["joints"]]
    wanted = {"Raiz", *[b["nome"] for b in job["plano"]["ossos"]]}
    if set(joint_names) != wanted or len(joint_names) != len(wanted):
        errors.append("ossos divergentes")
    by_name = {n.get("name"): i for i, n in enumerate(g["nodes"]) if "mesh" not in n}
    rest_world = reader.world_rest()
    rest_error = 0.
    parents = {child: i for i, n in enumerate(g["nodes"]) for child in n.get("children", [])}
    for b in job["plano"]["ossos"]:
        parent = b["pai"] or "Raiz"
        if by_name.get(b["nome"]) not in g["nodes"][by_name[parent]].get("children", []):
            errors.append("hierarquia: "+b["nome"])
        rest_error = max(rest_error, float(np.linalg.norm(rest_world[by_name[b["nome"]]][:3, 3]*16-np.array(b["pivo"]))))
    for loc in job["plano"]["locators"]:
        if loc["nome"] not in by_name:
            errors.append("locator ausente: "+loc["nome"])
        else:
            rest_error = max(rest_error, float(np.linalg.norm(rest_world[by_name[loc["nome"]]][:3, 3]*16-np.array(loc["posicao"]))))
    if rest_error > .001:
        errors.append("escala/eixos/pivôs/locators de repouso divergentes")
    triangles, uv_min, uv_max, influences = 0, 1., 0., 0
    for mesh in g["meshes"]:
        if len(mesh["primitives"]) != 1:
            errors.append("uma primitiva/material por malha")
        for prim in mesh["primitives"]:
            attrs = prim["attributes"]
            if prim.get("mode", 4) != 4 or not {"POSITION", "NORMAL", "TEXCOORD_0", "JOINTS_0", "WEIGHTS_0"} <= attrs.keys():
                raise ValueError("primitiva incompleta ou não triangulada")
            triangles += len(reader.accessor(prim["indices"]))//3
            uv = reader.accessor(attrs["TEXCOORD_0"])
            uv_min, uv_max = min(uv_min, float(uv.min())), max(uv_max, float(uv.max()))
            weights = reader.accessor(attrs["WEIGHTS_0"])
            joints = reader.accessor(attrs["JOINTS_0"])
            if np.any(~np.isfinite(weights)) or not np.allclose(weights.sum(axis=1), 1., atol=1e-5):
                errors.append("pesos não normalizados")
            influences = max(influences, int((weights>1e-6).sum(axis=1).max()))
            if influences != 1 or not np.allclose(weights.max(axis=1), 1.):
                errors.append("skin deve ser rígida (um osso/peso 1)")
            used = set(joints[weights>1e-6].tolist())
            if any(i >= len(joint_names) or joint_names[i] in ("Raiz", "root") for i in used):
                errors.append("influência em raiz ou joint inválido")
            if any(not np.isfinite(reader.accessor(attrs[k])).all() for k in ("POSITION", "NORMAL", "TEXCOORD_0")):
                errors.append("geometria não finita")
    if uv_min < 0 or uv_max > 1:
        errors.append("UV fora do atlas")
    if triangles > min(20000, job["limites"]["triangulos"]):
        errors.append("orçamento de triângulos")
    if len(g.get("materials", [])) != 1:
        errors.append("material único")
    for mat in g.get("materials", []):
        pbr = mat.get("pbrMetallicRoughness", {})
        if pbr.get("metallicFactor", 1) != 0 or pbr.get("roughnessFactor", 1) != 1:
            errors.append("material fosco PBR divergente")
        if mat.get("alphaMode") not in ("MASK", "BLEND"):
            errors.append("recorte alfa perdido")
    if any(s.get("magFilter") != 9728 or s.get("minFilter") not in (9728, 9984) for s in g.get("samplers", [])):
        errors.append("sampler deve usar NEAREST")
    clips = {}
    mesh_index = g["nodes"].index(meshes[0])
    for anim in g.get("animations", []):
        name = anim.get("name")
        if name in clips or name not in job["animacao"]["duracoes"]:
            errors.append("clipe duplicado/desconhecido")
            continue
        duration = 0.
        for channel in anim["channels"]:
            sampler = anim["samplers"][channel["sampler"]]
            times = reader.accessor(sampler["input"])[:, 0]
            values = reader.accessor(sampler["output"])
            duration = max(duration, float(times.max()))
            if not np.isfinite(values).all() or np.any(np.diff(times) <= 0):
                errors.append("chaves inválidas")
            if sampler.get("interpolation", "LINEAR") != "LINEAR":
                errors.append("interpolação não assada")
            target = channel["target"]
            if target["node"] == mesh_index:
                errors.append("animação move a malha física")
            if target["path"] == "rotation" and not np.allclose(np.linalg.norm(values, axis=1), 1., atol=2e-4):
                errors.append("quaternion não unitário")
            if g["nodes"][target["node"]].get("name") == "Raiz" and not np.allclose(values, values[0], atol=1e-6):
                errors.append("Raiz animada")
        if abs(duration-job["animacao"]["duracoes"][name]) > 1e-4:
            errors.append("duração divergente: "+name)
        clips[name] = {"duracao": round(duration, 6), "canais": len(anim["channels"])}
    if set(clips) != set(job["animacao"]["duracoes"]):
        errors.append("clipes ausentes")
    embedded = np.asarray(reader.image())
    variant = path.stem.removeprefix(job["id"]+"-")
    source = np.asarray(Image.open(path.parent/atlas["imagens"][variant]["roblox"]).convert("RGBA"))
    if embedded.shape != source.shape or not np.array_equal(embedded, source):
        errors.append("PNG embutido difere da textura de entrega")
    return {"ok": not errors, "erros": errors, "khronos": khronos, "triangulos": triangles,
            "uv": [uv_min, uv_max], "influencias_max": influences, "ossos": joint_names,
            "clipes": clips, "textura": list(embedded.shape[:2]), "erro_repouso_unidades": round(rest_error, 7)}
