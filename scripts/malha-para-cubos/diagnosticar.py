"""Confere o .bbmodel contra a malha original: silhuetas na mesma câmera, erro por osso, juntas.

Uso: uv run python scripts/malha-para-cubos/diagnosticar.py <pasta malha-vN> [arquivo.bbmodel]

Grava <pasta>/diagnostico.png (malha | cubos | sobreposição, por vista) e <pasta>/diagnostico.json.
Na sobreposição: cinza = os dois, azul = falta cubo, laranja = cubo sobrando.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import cubos as cb  # noqa: E402
from criaturas import bbmodelo, render  # noqa: E402

VISTAS = ("frente", "lado", "costas", "3/4")


def splat(pos, cores, proj, voxel, fundo=(255, 255, 255)):
    """Pontos coloridos (voxels de superfície) na mesma projeção do renderizador."""
    w, h = proj.tamanho
    img = np.zeros((h, w, 3), np.uint8)
    img[:] = fundo
    mask = np.zeros((h, w), bool)
    px = proj.pixel(pos)
    prof = pos @ proj.frente
    meio = 0.5 * voxel * proj.escala * 1.15  # meio lado do voxel na tela (com folga para não deixar fresta)
    luz = 0.75 + 0.25 * np.clip((pos - pos.mean(0)) @ np.array([0.0, 1.0, 0.0]) / (np.ptp(pos[:, 1]) or 1), -1, 1)
    for k in np.argsort(-prof):
        x, y = px[k]
        y0, y1 = max(0, int(np.floor(y - meio))), min(h, int(np.ceil(y + meio)))
        x0, x1 = max(0, int(np.floor(x - meio))), min(w, int(np.ceil(x + meio)))
        if y0 >= y1 or x0 >= x1:
            continue
        img[y0:y1, x0:x1] = np.clip(cores[k] * luz[k], 0, 255)
        mask[y0:y1, x0:x1] = True
    return Image.fromarray(img), mask


def sobreposicao(m_malha, m_cubo):
    h, w = m_malha.shape
    img = np.full((h, w, 3), 255, np.uint8)
    img[m_malha & m_cubo] = (175, 175, 182)
    img[m_malha & ~m_cubo] = (40, 120, 235)
    img[~m_malha & m_cubo] = (245, 140, 30)
    iou = (m_malha & m_cubo).sum() / max((m_malha | m_cubo).sum(), 1)
    return Image.fromarray(img), float(iou)


def pontos_dos_cubos(modelo, mats, passo=0.5):
    """Pontos amostrados dentro de cada cubo, no mundo: {nome do cubo: (n, 3)}."""
    out = {}
    for c in modelo.cubos:
        a, b = c.de, c.ate
        eixos = [np.arange(a[k] + passo / 2, b[k], passo) if b[k] - a[k] > passo else np.array([(a[k] + b[k]) / 2])
                 for k in range(3)]
        g = np.stack(np.meshgrid(*eixos, indexing="ij"), -1).reshape(-1, 3)
        out[c.nome] = bbmodelo.aplicar(bbmodelo.matriz_cubo(modelo, c, mats), g)
    return out


def main():
    pasta = Path(sys.argv[1]).resolve()
    rel = json.loads((pasta / "relatorio.json").read_text(encoding="utf-8"))
    arquivo = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else pasta / rel["arquivo"]
    dados = np.load(pasta / "voxels.npz")
    voxel = float(dados["voxel"])
    sup_pos = dados["origem"] + (dados["sup_idx"] + 0.5) * voxel
    sup_cor = dados["sup_cor"].astype(float)
    modelo = bbmodelo.ler(arquivo)
    mats = bbmodelo.matrizes_ossos(modelo)
    lo, hi = bbmodelo.limites(modelo, mats)
    lo, hi = np.minimum(lo, sup_pos.min(0)), np.maximum(hi, sup_pos.max(0))

    paineis, ious = [], {}
    lado_px = 320
    for vista in VISTAS:
        raio = float(np.linalg.norm(hi - lo))
        escala = (lado_px - 16) / max(raio, 1.0)
        im_c, m_c, _ids, proj = render.renderizar(modelo, vista, escala=escala, limites=(lo, hi), mats=mats)
        im_m, m_m = splat(sup_pos, sup_cor, proj, voxel)
        im_o, iou = sobreposicao(m_m, m_c)
        ious[vista] = round(iou, 3)
        paineis.append((vista, im_m, im_c, im_o))
    W = max(p[1].width for p in paineis)
    H = max(p[1].height for p in paineis)
    folha = Image.new("RGB", (W * 3 + 16, (H + 4) * len(paineis)), (255, 255, 255))
    d = ImageDraw.Draw(folha)
    for i, (vista, a, b, c) in enumerate(paineis):
        for j, im in enumerate((a, b, c)):
            folha.paste(im, (j * (W + 8), i * (H + 4)))
        d.text((4, i * (H + 4) + 2), f"{vista}  IoU {ious[vista]:.0%}", fill=(40, 40, 50))
    if max(folha.size) > 1100:
        f = 1100 / max(folha.size)
        folha = folha.resize((int(folha.width * f), int(folha.height * f)), Image.LANCZOS)
    folha.save(pasta / "diagnostico.png")

    # erro por osso: voxels da malha perto dos cubos do osso × volume dos cubos fora da malha
    occ = dados["ocupado"]
    org = dados["origem"]

    def dentro_malha(p):
        ijk = np.floor((p - org) / voxel).astype(int)
        ok = np.all((ijk >= 0) & (ijk < occ.shape), axis=1)
        out = np.zeros(len(p), bool)
        out[ok] = occ[tuple(ijk[ok].T)]
        return out

    pts = pontos_dos_cubos(modelo, mats)
    por_osso = {}
    for c in modelo.cubos:
        fora = 1 - dentro_malha(pts[c.nome]).mean()
        por_osso.setdefault(c.osso, []).append((c.nome, round(float(fora), 2)))
    # juntas: menor distância entre os cubos de um osso e os do pai (lacuna se > 0,75)
    lacunas = []
    for nome, o in modelo.ossos.items():
        if o.pai is None:
            continue
        meus = [pts[c.nome] for c in modelo.cubos if c.osso == nome]
        pai = o.pai
        while pai and not any(c.osso == pai for c in modelo.cubos):
            pai = modelo.ossos[pai].pai
        dele = [pts[c.nome] for c in modelo.cubos if c.osso == pai] if pai else []
        if not meus or not dele:
            continue
        A, B = np.concatenate(meus), np.concatenate(dele)
        if len(A) > 4000:
            A = A[:: len(A) // 4000 + 1]
        if len(B) > 4000:
            B = B[:: len(B) // 4000 + 1]
        dmin = float(np.min(np.linalg.norm(A[:, None] - B[None], axis=2)))
        if dmin > 0.75:
            lacunas.append((nome, pai, round(dmin, 2)))
    multi = [c.nome for c in modelo.cubos if np.sum(np.abs(c.rotacao) > 0.01) >= 2]
    sobrando = sorted(((n, f) for v in por_osso.values() for n, f in v), key=lambda x: -x[1])[:10]
    resumo = {"iou_por_vista": ious, "lacunas_juntas": lacunas, "cubos_com_rotacao_em_2_ou_3_eixos": len(multi),
              "cubos_mais_fora_da_malha": sobrando}
    (pasta / "diagnostico.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # referência × malha × cubos, de lado (a arte de referência é desenho, não projeção exata)
    refs = sorted((pasta / "entrada").glob("conceito-lado.*"))
    malha_lado = pasta / "entrada" / "renders" / "malha-lado.png"
    if refs and malha_lado.exists():
        im_c, _m, _i, _p = render.renderizar(modelo, "lado", escala=10, mats=mats)
        paineis_r = [("referência", Image.open(refs[0]).convert("RGBA")), ("malha do Tripo", Image.open(malha_lado)),
                     ("cubos", im_c.convert("RGBA"))]
        alto = 300
        tiras = []
        for titulo, im in paineis_r:
            caixa = im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox() if im.mode == "RGBA" else None
            fundo_branco = Image.new("RGBA", im.size, (255, 255, 255, 255))
            fundo_branco.alpha_composite(im)
            im = fundo_branco.convert("RGB")
            if caixa:
                im = im.crop(caixa)
            claro = np.asarray(im).min(-1) < 250  # recorta o fundo branco também
            ys, xs = np.nonzero(claro)
            if len(xs):
                im = im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
            im = im.resize((int(im.width * alto / im.height), alto), Image.LANCZOS)
            quadro = Image.new("RGB", (im.width + 16, alto + 24), (255, 255, 255))
            quadro.paste(im, (8, 20))
            ImageDraw.Draw(quadro).text((8, 4), titulo, fill=(40, 40, 50))
            tiras.append(quadro)
        ref_img = Image.new("RGB", (sum(t.width for t in tiras), max(t.height for t in tiras)), (255, 255, 255))
        x = 0
        for t in tiras:
            ref_img.paste(t, (x, 0))
            x += t.width
        f = min(1.0, 1400 / ref_img.width)
        ref_img.resize((int(ref_img.width * f), int(ref_img.height * f)), Image.LANCZOS).save(pasta / "referencia.png")
    print("IoU por vista:", ", ".join(f"{k} {v:.0%}" for k, v in ious.items()))
    print("lacunas nas juntas:", lacunas or "nenhuma")
    print(f"cubos com rotação em 2+ eixos: {len(multi)} de {len(modelo.cubos)}")
    print("mais fora da malha:", ", ".join(f"{n} {f:.0%}" for n, f in sobrando[:6]))
    print(f"diagnóstico: {pasta / 'diagnostico.png'} {folha.size}")


if __name__ == "__main__":
    main()
