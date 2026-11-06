"""Tira ilhas soltas dos planos recortados (pelo e fita) de um .bbmodel pronto.

Uso: uv run python scripts/malha-para-cubos/limpar_ilhas.py <modelo.bbmodel> <saida.bbmodel>

Um tufo da juba/cauda é mantido se algum pixel dele encosta (até 0,75) num cubo sólido do corpo;
tufos que não encostam em nada ficam boiando no ar e viram transparentes. Na fita do cachecol cada
plano guarda só o pedaço principal. Só o alfa desses pixels muda: geometria, UV e ossos ficam
idênticos (conferido). A saída precisa ser um arquivo novo.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import shutil
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

from criaturas import bbmodelo, motor, render


def componentes(mask):
    h, w = mask.shape
    rot = -np.ones((h, w), int)
    grupos = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and rot[y, x] < 0:
                fila, pts = deque([(y, x)]), []
                rot[y, x] = len(grupos)
                while fila:
                    a, b = fila.popleft()
                    pts.append((a, b))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            yy, xx = a + dy, b + dx
                            if 0 <= yy < h and 0 <= xx < w and mask[yy, xx] and rot[yy, xx] < 0:
                                rot[yy, xx] = len(grupos)
                                fila.append((yy, xx))
                grupos.append(np.array(pts))
    return grupos


def assinatura(bruto):
    raw = {k: v for k, v in bruto.items() if k in ("groups", "outliner", "animations", "elements")}
    raw["elements"] = [{k: v for k, v in e.items() if k != "faces"} for e in raw["elements"]]
    return hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest()


def main():
    entrada, saida = (Path(a).resolve() for a in sys.argv[1:3])
    if saida.exists():
        raise SystemExit(f"{saida} já existe; escolha uma saída nova")
    modelo = bbmodelo.ler(entrada)
    mats = bbmodelo.matrizes_ossos(modelo)
    atlas = np.asarray(modelo.textura).copy()
    fator = atlas.shape[1] // modelo.resolucao[0]
    solidos = [(c, np.linalg.inv(bbmodelo.matriz_cubo(modelo, c, mats))) for c in modelo.cubos
               if np.min(c.ate - c.de) > 1e-6]

    def encosta(pts):
        for c, inv in solidos:
            loc = bbmodelo.aplicar(inv, pts)
            if np.any(np.all((loc >= c.de - 0.75) & (loc <= c.ate + 0.75), axis=1)):
                return True
        return False

    removidos = {}
    for c in modelo.cubos:
        if np.min(c.ate - c.de) > 1e-6:
            continue  # só planos
        M = bbmodelo.matriz_cubo(modelo, c, mats)
        lim = np.stack([c.de, c.ate])
        fita = c.nome.startswith("scarf_")
        for face, cantos in render.CANTOS_FACE.items():
            uvf = c.faces.get(face, {}).get("uv")
            if not uvf or abs(uvf[2] - uvf[0]) < 1e-6 or abs(uvf[3] - uvf[1]) < 1e-6:
                continue
            u1, v1, u2, v2 = uvf
            TL, TR, BL, _ = (np.array([lim[i, 0], lim[j, 1], lim[k, 2]]) for i, j, k in cantos)
            px0, px1 = int(round(min(u1, u2) * fator)), int(round(max(u1, u2) * fator))
            py0, py1 = int(round(min(v1, v2) * fator)), int(round(max(v1, v2) * fator))
            alfa = atlas[py0:py1, px0:px1, 3] > 127
            grupos = sorted(componentes(alfa), key=len, reverse=True)
            if len(grupos) < 2:
                continue
            tirar = []
            for i, g in enumerate(grupos):
                if fita:
                    if i > 0:
                        tirar.append(g)  # fita: só o pedaço principal de cada trecho
                    continue
                yy, xx = g[:, 0], g[:, 1]
                U = (px0 + xx + 0.5) / fator
                V = (py0 + yy + 0.5) / fator
                S, T = (U - u1) / (u2 - u1), (V - v1) / (v2 - v1)
                W = bbmodelo.aplicar(M, TL + S[:, None] * (TR - TL) + T[:, None] * (BL - TL))
                if len(g) < 12 or not encosta(W):
                    tirar.append(g)  # tufo boiando no ar (ou poeira de pixels)
            for g in tirar:
                atlas[py0 + g[:, 0], px0 + g[:, 1], 3] = 0
            if tirar:
                removidos[f"{c.nome}.{face}"] = [int(len(g)) for g in tirar]

    img = Image.fromarray(atlas, "RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    saida.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(entrada, saida)
    motor.editar(saida, [{"op": "update_texture", "target": 0,
                          "source": "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(),
                          "width": img.width, "height": img.height}])
    img.save(saida.parent / "textura.png")
    igual = assinatura(json.loads(entrada.read_text(encoding="utf-8"))) == \
        assinatura(json.loads(saida.read_text(encoding="utf-8")))
    erros, avisos, _ = motor.resumo_validacao(motor.validar(saida))
    rel = {"entrada": entrada.name, "saida": saida.name, "ilhas_removidas": removidos,
           "geometria_uv_ossos_iguais": igual, "validacao": {"erros": erros, "avisos": avisos}}
    (saida.parent / "relatorio.json").write_text(json.dumps(rel, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"ilhas removidas: {sum(len(v) for v in removidos.values())} em {len(removidos)} faces · "
          f"geometria/UV/ossos iguais: {igual} · {erros} erros, {avisos} avisos")
    for k, v in removidos.items():
        print(f"  {k}: {v}")
    print(f"saída: {saida}")


if __name__ == "__main__":
    main()
