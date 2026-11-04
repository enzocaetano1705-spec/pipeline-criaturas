"""Descrição da malha rígida enviada em lote ao processo Blender."""

from .atlas import FACES


def gerar(job: dict, atlas: dict) -> dict:
    vertices, faces, uvs, weights, pieces = [], [], [], [], []
    lookup = {(i["cubo"], i["face"]): i["retangulo"] for i in atlas["ilhas"]}
    res = atlas["resolucao"]
    for cube in job["plano"]["cubos"]:
        lo, hi = list(cube["from"]), list(cube["to"])
        for axis in range(3):
            if lo[axis] == hi[axis]:
                lo[axis] -= job["limites"]["espessura_planos"] / 2
                hi[axis] += job["limites"]["espessura_planos"] / 2
        start = len(vertices)
        vertices.extend([[hi[a] if i & (1 << a) else lo[a] for a in range(3)] for i in range(8)])
        weights.extend([cube["osso"]] * 8)
        for face, (corners, _) in FACES.items():
            faces.append([start + i for i in corners])
            x, y, w, h = lookup[cube["nome"], face]
            uvs.append([[x/res, 1-(y+h)/res], [x/res, 1-y/res], [(x+w)/res, 1-y/res], [(x+w)/res, 1-(y+h)/res]])
        pieces.append({"nome": cube["nome"], "osso": cube["osso"], "indices": list(range(start, start+8)),
                       "tipo": cube["tipo"]})
    return {"vertices": vertices, "faces": faces, "uvs": uvs, "ossos_vertices": weights, "pecas": pieces}
