"""plano-cubos.json -> lote de operações do bbmodel_edit (ops.json).

O código nunca escreve .bbmodel à mão (docs/convencoes.md): tudo vira operações do motor.
"""

import math

from criaturas import contratos


def tamanho_box_uv(frm, to) -> tuple[int, int]:
    """(largura, altura) da ilha de Box UV de um cubo: 2·(d+w) × (d+h), arredondado para cima."""
    w, h, d = (abs(b - a) for a, b in zip(frm, to))
    return math.ceil(2 * (d + w)), math.ceil(d + h)


def distribuir_uv(cubos: list[dict], margem: int = 0, larguras=(64, 128, 256)) -> tuple[dict[str, list[int]], tuple[int, int]]:
    """Empacota as ilhas de Box UV em prateleiras. Devolve ({cubo: [u, v]}, (largura, altura)).

    Cubos com `espelho_de` reaproveitam a ilha do cubo original (mirror_uv).
    Escolhe a menor textura quadrada (64, 128, 256) onde tudo cabe.
    """
    proprios = [c for c in cubos if not c.get("espelho_de")]
    ordem = sorted(proprios, key=lambda c: (-tamanho_box_uv(c["from"], c["to"])[1], -tamanho_box_uv(c["from"], c["to"])[0]))
    for lado in larguras:
        offsets, x, y, alt_linha, coube = {}, 0, 0, 0, True
        for c in ordem:
            w, h = tamanho_box_uv(c["from"], c["to"])
            w, h = max(w, 1) + margem, max(h, 1) + margem
            if w > lado:
                coube = False
                break
            if x + w > lado:
                x, y, alt_linha = 0, y + alt_linha, 0
            if y + h > lado:
                coube = False
                break
            offsets[c["nome"]] = [x, y]
            x += w
            alt_linha = max(alt_linha, h)
        if coube:
            for c in cubos:
                if c.get("espelho_de"):
                    offsets[c["nome"]] = list(offsets[c["espelho_de"]])
            return offsets, (lado, lado)
    raise ValueError(f"as ilhas de UV não cabem em {larguras[-1]}×{larguras[-1]}")


def gerar_ops(plano: dict) -> list[dict]:
    """Operações do bbmodel_edit para um plano de cubos (contrato plano_cubos)."""
    contratos.validar("plano_cubos", plano)
    nomes = {o["nome"] for o in plano["ossos"]}
    ops = [{"op": "set_model_properties", "name": plano["nome"],
            "resolution": {"width": plano["resolucao"]["largura"], "height": plano["resolucao"]["altura"]}}]
    for osso in plano["ossos"]:
        if osso["pai"] is not None and osso["pai"] not in nomes:
            raise ValueError(f"osso {osso['nome']}: pai {osso['pai']} não existe")
        op = {"op": "add_group", "name": osso["nome"], "origin": osso["pivo"]}
        if osso.get("rotacao") and any(osso["rotacao"]):
            op["rotation"] = osso["rotacao"]
        if osso["pai"]:
            op["parent"] = osso["pai"]
        ops.append(op)
    for cubo in plano["cubos"]:
        if cubo["osso"] not in nomes:
            raise ValueError(f"cubo {cubo['nome']}: osso {cubo['osso']} não existe")
        op = {"op": "add_cube", "name": cubo["nome"], "from": cubo["from"], "to": cubo["to"],
              "parent": cubo["osso"], "box_uv": True}
        if "uv_offset" in cubo:
            op["uv_offset"] = cubo["uv_offset"]
        if cubo.get("mirror_uv"):
            op["mirror_uv"] = True
        if cubo.get("inflate"):
            op["inflate"] = cubo["inflate"]
        ops.append(op)
    for loc in plano.get("locators", []):
        ops.append({"op": "add_locator", "name": loc["nome"], "parent": loc["osso"], "position": loc["posicao"]})
    return ops
