"""Diagnóstico de analogias por partes, sem copiar assets nem dar nota artística.

As caixas são medidas em repouso, sem inflate ou recorte alfa. As métricas de UV
usam faces explícitas e a primeira/única textura incorporada. Nomes são seletores,
nunca correspondências semânticas automáticas. Suporta projetos bbmodel 4/5.
"""
import base64
import hashlib
import io
import itertools
import json
from pathlib import Path

import numpy as np
from PIL import Image

from criaturas import bbmodelo, referencias

LIMITES = [
    "Diferença de uma referência não é defeito: a imagem da criatura decide as proporções.",
    "Caixas e áreas ignoram inflate, recorte alfa, oclusão e animação; não são silhuetas visíveis.",
    "Alfa mede texels por face (inclui faces internas e UVs compartilhados), não buracos externos.",
    "Não mede expressão, posição de olhos/boca, qualidade de pixel art ou aprovação artística.",
    "Inclui todos os cubos selecionados, mesmo ocultos/não exportáveis; selecione apenas as peças relevantes.",
]
EIXOS_FACE = {"north": (0, 1), "south": (0, 1), "east": (2, 1),
              "west": (2, 1), "up": (0, 2), "down": (0, 2)}


def _selecao(cubos, grupos, seletor):
    if not isinstance(seletor, dict) or not seletor:
        raise ValueError("Cada parte precisa de seletor explícito (tipo, ossos ou elementos).")
    if set(seletor) - {"tipo", "ossos", "elementos"}:
        raise ValueError("Seletor aceita somente tipo, ossos e elementos.")
    if seletor.get("tipo", "todos") not in ("todos", "solido", "plano"):
        raise ValueError("tipo deve ser todos, solido ou plano")
    for key in ("ossos", "elementos"):
        if key in seletor and (not isinstance(seletor[key], list) or not seletor[key]
                              or not all(isinstance(x, str) for x in seletor[key])):
            raise ValueError(f"{key} precisa de uma lista não vazia de nomes/UUIDs")
    if "ossos" in seletor:
        conhecidos = set(grupos) | {g["nome"] for g in grupos.values()}
        if set(seletor["ossos"]) - conhecidos:
            raise ValueError("Seletor contém osso inexistente")
    if "elementos" in seletor:
        conhecidos = {c["nome"] for c in cubos} | {c["uuid"] for c in cubos}
        if set(seletor["elementos"]) - conhecidos:
            raise ValueError("Seletor contém elemento inexistente")
    indices = []
    for i, c in enumerate(cubos):
        if seletor.get("tipo", "todos") not in ("todos", c["tipo"]):
            continue
        if "elementos" in seletor and not ({c["nome"], c["uuid"]} & set(seletor["elementos"])):
            continue
        if "ossos" in seletor:
            ancestrais = list(referencias._ancestrais_ids(grupos, c["pai"]))
            nomes = set(ancestrais) | {grupos[g]["nome"] for g in ancestrais}
            if not nomes & set(seletor["ossos"]):
                continue
        indices.append(i)
    if not indices:
        raise ValueError(f"Seletor não encontrou peças: {seletor}")
    return indices


def _caixa(cubos):
    pontos = np.concatenate([c["mundo"] for c in cubos])
    return pontos.min(0), pontos.max(0)


def assinatura(arquivo, partes, ancora):
    path = Path(arquivo).resolve()
    raw = path.read_bytes()
    bruto = json.loads(raw.decode("utf-8-sig"))
    if "elements" not in bruto:
        raise ValueError("Comparação requer .bbmodel; converta uma cópia da geometria externa primeiro.")
    if any(e.get("type", "cube") == "mesh" for e in bruto["elements"]):
        raise ValueError("Malhas não são suportadas nesta comparação por cubos/planos.")
    groups, cubes, _, resolution = referencias._normalizar(bruto)
    if not cubes or not partes or ancora not in partes:
        raise ValueError("Modelo, partes e parte âncora precisam estar presentes.")
    mats = referencias._matrizes(groups)
    elements = [e for e in bruto["elements"] if e.get("type", "cube") == "cube" and "from" in e and "to" in e]
    textures = bruto.get("textures", [])
    if len(textures) > 1:
        raise ValueError("Diagnóstico de UV suporta uma textura; modelos com materiais múltiplos exigem inspeção própria.")
    texture = None
    if textures and textures[0].get("source", "").startswith("data:image/"):
        texture = np.asarray(Image.open(io.BytesIO(base64.b64decode(textures[0]["source"].split(",", 1)[1]))).convert("RGBA"))
    ru, rv = resolution.get("width", 0), resolution.get("height", 0)
    if ru <= 0 or rv <= 0:
        raise ValueError("Resolução UV inválida")
    for cube, element in zip(cubes, elements):
        size = cube["ate"] - cube["de"]
        if not np.isfinite(size).all() or (size < -1e-8).any() or sum(size > 1e-8) < 2:
            raise ValueError("Cubo invertido, degenerado ou com coordenadas inválidas")
        cube["tipo"] = "solido" if np.all(size > 1e-8) else "plano"
        cube["uuid"] = element.get("uuid", "")
        if "origin" not in element:
            cube["pivo"] = (cube["de"] + cube["ate"]) / 2
        matrix = mats.get(cube["pai"], np.eye(4)) @ referencias._transformacao(cube["pivo"], cube["rotacao"])
        corners = np.asarray(list(itertools.product(*zip(cube["de"], cube["ate"]))))
        cube["mundo"] = bbmodelo.aplicar(matrix, corners)
        cube["area_projetada"] = np.zeros(3)
        if cube["tipo"] == "plano":
            zero = int(np.argmin(size))
            cube["area_projetada"] = abs(matrix[:3, zero]) * np.prod(size[size > 1e-8])
    selected = {nome: _selecao(cubes, groups, selector) for nome, selector in partes.items()}
    lo, hi = _caixa([cubes[i] for i in selected[ancora]])
    height, center = hi[1]-lo[1], (hi+lo)/2
    if height < 1e-8:
        raise ValueError("Parte âncora precisa ter altura positiva")
    summaries = {}
    for name, indices in selected.items():
        subset = [cubes[i] for i in indices]
        low, high = _caixa(subset)
        dims = (high-low)/height
        projected = sum((c["area_projetada"] for c in subset), np.zeros(3))/height**2
        densities, front_areas, alpha = [], [], []
        faces_without_uv = 0
        for i in indices:
            size = cubes[i]["ate"] - cubes[i]["de"]
            for face, axes in EIXOS_FACE.items():
                area = float(size[axes[0]]*size[axes[1]])
                if area < 1e-8:
                    continue
                definition = elements[i].get("faces", {}).get(face, {})
                if definition.get("texture", 0) is None:
                    continue
                if "uv" not in definition:
                    faces_without_uv += 1
                    continue
                u1, v1, u2, v2 = definition["uv"]
                scale = np.array([texture.shape[1]/ru, texture.shape[0]/rv]) if texture is not None else np.ones(2)
                uvsize = abs(np.array([u2-u1, v2-v1])*scale)
                densities.append(float(np.sqrt(np.prod(uvsize)/area)*height))
                if face == "north":
                    front_areas.append(float(np.prod(uvsize)))
                if texture is not None:
                    x0, x1 = sorted([u1*scale[0], u2*scale[0]])
                    y0, y1 = sorted([v1*scale[1], v2*scale[1]])
                    if x0 < 0 or y0 < 0 or x1 > texture.shape[1] or y1 > texture.shape[0]:
                        raise ValueError("UV fora da textura; repetição não suportada no diagnóstico")
                    patch = texture[int(np.floor(y0)):int(np.ceil(y1)), int(np.floor(x0)):int(np.ceil(x1)), 3]
                    if patch.size:
                        alpha.extend([int(np.count_nonzero(patch > 127)), int(patch.size)])
        summaries[name] = {
            "elementos_selecionados": [{"nome": cubes[i]["nome"], "uuid": cubes[i]["uuid"]} for i in indices],
            "pecas": len(subset), "solidos": sum(c["tipo"] == "solido" for c in subset),
            "planos": sum(c["tipo"] == "plano" for c in subset),
            "dimensoes_por_altura_ancora": dict(zip(("largura", "altura", "profundidade"), dims.tolist())),
            "centro_relativo_ancora": dict(zip(("x", "y", "z"), (((high+low)/2-center)/height).tolist())),
            "area_planos_projetada_por_altura_ancora_quadrada": {"frente":float(projected[2]), "lado":float(projected[0]), "cima":float(projected[1])},
            "textura": {"texels_por_altura_ancora_mediana": float(np.median(densities)) if densities else None,
                        "maior_face_north_texels_area": max(front_areas) if front_areas else None,
                        "fracao_alfa_opaca_por_face": sum(alpha[::2])/sum(alpha[1::2]) if alpha else None,
                        "faces_sem_uv_explicito": faces_without_uv},
        }
    return {"arquivo": str(path), "sha256": hashlib.sha256(raw).hexdigest(),
            "ancora": ancora, "resolucao_uv": [ru,rv],
            "textura_incorporada_px": [texture.shape[1],texture.shape[0]] if texture is not None else None,
            "unidade_densidade": "pixels reais" if texture is not None else "unidades UV (imagem não incorporada)",
            "unidade_area_textura": "pixels quadrados" if texture is not None else "unidades UV quadradas (imagem não incorporada)",
            "partes": summaries}


def _numeros(dados, prefix=""):
    for key, value in dados.items():
        name = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            yield from _numeros(value, name)
        elif isinstance(value, (float, int)):
            yield name, value


def comparar(caso, base=Path.cwd()):
    if caso.get("modo") not in ("analogia", "reconstrucao"):
        raise ValueError("Declare modo analogia ou reconstrucao; não misture as avaliações.")
    results = {}
    for role in ("referencia", "candidato"):
        spec = caso[role]
        results[role] = assinatura(Path(base)/spec["arquivo"], spec["partes"], caso["ancora"])
    if set(results["referencia"]["partes"]) != set(results["candidato"]["partes"]):
        raise ValueError("Referência e candidato precisam mapear os mesmos papéis de partes.")
    left = dict(_numeros(results["referencia"]["partes"]))
    right = dict(_numeros(results["candidato"]["partes"]))
    different_units = results["referencia"]["unidade_densidade"] != results["candidato"]["unidade_densidade"]
    incomparable = [key for key in left.keys() & right.keys() if different_units and
                    key.endswith(("texels_por_altura_ancora_mediana", "maior_face_north_texels_area"))]
    deltas = [{"metrica": key, "referencia": val, "candidato": right[key],
               "delta": right[key]-val,
               "variacao_relativa": (right[key]-val)/abs(val) if abs(val)>1e-8 else None}
              for key,val in left.items() if key in right and key not in incomparable]
    return {"versao": 1, "modo": caso["modo"], "aprovacao_artistica": "nao_avaliada",
            **results, "diferencas": deltas, "limites": LIMITES,
            "metricas_nao_comparaveis": [{"metrica":key, "motivo":"Pixels reais versus unidades UV; falta imagem incorporada em um modelo."} for key in sorted(incomparable)]}


def cmd_comparar(args):
    try:
        config = Path(args.caso).resolve()
        case = json.loads(config.read_text(encoding="utf-8-sig"))
        output = Path(args.saida).resolve()
        if output == config or output in {(config.parent/Path(case[r]["arquivo"])).resolve() for r in ("referencia", "candidato")}:
            raise ValueError("A saída não pode sobrescrever o caso nem os modelos de entrada.")
        result = comparar(case, config.parent)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f"comparar-referencias: {exc}")
        return 1
    print(f"Comparação por partes ({result['modo']}): {len(result['diferencas'])} medidas; arte não avaliada.")
    for name, summary in result["candidato"]["partes"].items():
        if len(result['candidato']['partes']) > 12:
            break
        reference = result["referencia"]["partes"][name]
        print(f"  {name}: {reference['solidos']} volumes/{reference['planos']} planos -> {summary['solidos']} volumes/{summary['planos']} planos")
    print(f"Relatório: {output}")
    return 0
