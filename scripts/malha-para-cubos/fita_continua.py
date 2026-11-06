"""Refaz o recorte dos planos da fita do cachecol como uma fita só (sem emendas soltas).

Uso:
  uv run python scripts/malha-para-cubos/fita_continua.py <modelo.bbmodel> <voxels.npz> <arte.json> <saida.bbmodel>

Cada plano `scarf_N` tinha o recorte só dos pontos do próprio trecho: o contorno escuro aparecia
também na emenda com o vizinho (a fita parecia pedaços voando) e o 1º plano herdava o pano que fica
sobre o ombro (uma lâmina atravessando o corpo). Aqui o recorte de todos os planos vem de uma fita
única: pano vinho da malha que está no ar (fora dos cubos sólidos do corpo) e perto de algum plano.
O contorno escuro fica só na borda real da fita.

Só a textura muda: geometria, UV, ossos e animações ficam idênticos (conferido no fim). Não
sobrescreve arquivos: a saída precisa ser nova.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import cubos as cb  # noqa: E402
import esqueleto  # noqa: E402
import textura as tx  # noqa: E402
from criaturas import bbmodelo, motor, render  # noqa: E402


def assinatura(bruto):
    raw = {k: v for k, v in bruto.items() if k in ("groups", "outliner", "animations", "elements")}
    raw["elements"] = [{k: v for k, v in e.items() if k != "faces"} for e in raw["elements"]]
    return hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest()


def dentro_de(c, pts, folga):
    M = bbmodelo.matriz_rotacao(c.rotacao)
    loc = (pts - c.origem) @ M + c.origem
    return np.all((loc >= c.de - folga) & (loc <= c.ate + folga), axis=1)


def main():
    entrada, voxels, arte, saida = (Path(a).resolve() for a in sys.argv[1:5])
    if saida.exists():
        raise SystemExit(f"{saida} já existe; escolha uma saída nova")
    cfg = json.loads(arte.read_text(encoding="utf-8"))
    pano = np.asarray(cfg.get("pano", [[71, 20, 31], [88, 23, 37], [116, 28, 44]]), float)
    base, contorno = pano[min(2, len(pano) - 1)], pano[0]

    modelo = bbmodelo.ler(entrada)
    mats = bbmodelo.matrizes_ossos(modelo)
    dados = np.load(voxels)
    vx = float(dados["voxel"])
    sup_pos = dados["origem"] + (dados["sup_idx"] + 0.5) * vx
    sup_cor = dados["sup_cor"].astype(float)

    fitas = [c for c in modelo.cubos if c.nome.startswith("scarf_") and "collar" not in c.nome
             and np.min(c.ate - c.de) < 1e-6]
    solidos = [c for c in modelo.cubos if np.min(c.ate - c.de) > 1e-6]
    # fita única: pano vinho no ar (fora dos cubos sólidos) e perto do plano de algum trecho;
    # volume inteiro do pano (só a superfície deixaria o recorte rendado)
    g = esqueleto.Grade(dados["ocupado"], dados["origem"], vx)
    cor_vol = cb.cores_volume(g, dados["sup_idx"], sup_cor)
    P = g.pos[cb.vermelho(cor_vol) | tx.pano_por_matiz(cor_vol)]
    no_ar = np.ones(len(P), bool)
    for c in solidos:
        no_ar &= ~dentro_de(c, P, 0.5)
    perto = np.zeros(len(P), bool)
    for c in fitas:
        M = bbmodelo.matriz_cubo(modelo, c, mats)
        inv = np.linalg.inv(M)
        loc = bbmodelo.aplicar(inv, P)
        perto |= np.all((loc >= c.de - 1.0) & (loc <= c.ate + 1.0), axis=1)
    fita = P[no_ar & perto]

    atlas = np.asarray(modelo.textura).copy()
    fator = atlas.shape[1] // modelo.resolucao[0]
    mudou = {}
    for c in fitas:
        M = bbmodelo.matriz_cubo(modelo, c, mats)
        lim = np.stack([c.de, c.ate])
        for face, cantos in render.CANTOS_FACE.items():
            uvf = c.faces.get(face, {}).get("uv")
            if not uvf or abs(uvf[2] - uvf[0]) < 1e-6 or abs(uvf[3] - uvf[1]) < 1e-6:
                continue
            u1, v1, u2, v2 = uvf
            TL, TR, BL, _ = (np.array([lim[i, 0], lim[j, 1], lim[k, 2]]) for i, j, k in cantos)
            px0, px1 = int(round(min(u1, u2) * fator)), int(round(max(u1, u2) * fator))
            py0, py1 = int(round(min(v1, v2) * fator)), int(round(max(v1, v2) * fator))
            S = ((np.arange(px0, px1) + 0.5) / fator - u1) / (u2 - u1)
            T = ((np.arange(py0, py1) + 0.5) / fator - v1) / (v2 - v1)
            SS, TT = np.meshgrid(S, T)
            W = bbmodelo.aplicar(M, (TL + SS[..., None] * (TR - TL) + TT[..., None] * (BL - TL)).reshape(-1, 3))
            dist = np.full(len(W), np.inf)
            for i in range(0, len(W), 2048):
                d2 = ((W[i:i + 2048, None, :] - fita[None]) ** 2).sum(-1)
                dist[i:i + 2048] = np.sqrt(d2.min(1))
            forma = (py1 - py0, px1 - px0)
            opaco = tx.limpar_recorte((dist < 0.7).reshape(forma))
            # contorno só onde a fita acaba de verdade (a borda do retângulo não conta como borda)
            borda = opaco & ~np.logical_and.reduce(tx._vizinhos(opaco, True))
            rgb = np.empty(forma + (3,))
            rgb[:] = base
            rgb[borda] = contorno
            bloco = np.concatenate([rgb, np.where(opaco, 255, 0)[..., None]], -1).astype(np.uint8)
            antes = atlas[py0:py1, px0:px1].copy()
            atlas[py0:py1, px0:px1] = bloco
            mudou[f"{c.nome}.{face}"] = int((antes != bloco).any(-1).sum())

    img = Image.fromarray(atlas, "RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    saida.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(entrada, saida)
    motor.editar(saida, [{"op": "update_texture", "target": 0,
                          "source": "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(),
                          "width": img.width, "height": img.height}])
    img.save(saida.parent / "textura.png")
    a = json.loads(entrada.read_text(encoding="utf-8"))
    b = json.loads(saida.read_text(encoding="utf-8"))
    igual = assinatura(a) == assinatura(b)
    erros, avisos, _ = motor.resumo_validacao(motor.validar(saida))
    rel = {"entrada": entrada.name, "saida": saida.name, "pontos_da_fita": int(len(fita)),
           "geometria_uv_ossos_iguais": igual, "pixels_alterados": mudou, "validacao": {"erros": erros, "avisos": avisos}}
    (saida.parent / "relatorio.json").write_text(json.dumps(rel, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"fita: {len(fita)} pontos · geometria/UV/ossos iguais: {igual} · {erros} erros, {avisos} avisos")
    print(f"saída: {saida}")


if __name__ == "__main__":
    main()
