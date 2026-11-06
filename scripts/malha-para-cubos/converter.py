"""Malha 3D (voxels.npz do extrair_malha.py) -> .bbmodel cubificado com ossos e locators.

Uso:
  uv run python scripts/malha-para-cubos/converter.py <pasta malha-vN> [--nome fera-sombras-e3] [--garras 3]

Lê <pasta>/voxels.npz e, se existir, <pasta>/juntas-corrigidas.json (correções manuais de pontas
ou juntas). Grava na mesma pasta: <nome>.bbmodel, ops.json, textura-bloqueio.png,
diagnostico-juntas.png, diagnostico-partes.png, folha.png e relatorio.json.
A textura é só de bloqueio (cor mediana da malha por face); a pintura final é do texturizar.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import ajustes  # noqa: E402
import comparar  # noqa: E402
import textura  # noqa: E402
import cubos as cb  # noqa: E402
import esqueleto  # noqa: E402
import vistas  # noqa: E402
from criaturas import cubificar, folha, motor, ops  # noqa: E402

FACES = {  # face: (eixo, lado)  lado 1 = max, 0 = min
    "east": (0, 1), "west": (0, 0), "up": (1, 1), "down": (1, 0), "south": (2, 1), "north": (2, 0),
}


def r4(v, passo=0.25):
    return (np.round(np.asarray(v, float) / passo) * passo).round(4).tolist()


def cores_das_faces(cubo, sup_pos, sup_cor):
    M = cb.matriz(cubo["rotation"])
    loc = (sup_pos - cubo["origin"]) @ M + cubo["origin"]
    a, b = cubo["from"], cubo["to"]
    dentro_larga = np.all((loc >= a - 1.5) & (loc <= b + 1.5), axis=1)
    geral = np.median(sup_cor[dentro_larga], 0) if dentro_larga.any() else np.array([150, 150, 150])
    out = {}
    for face, (eixo, lado) in FACES.items():
        outros = [k for k in range(3) if k != eixo]
        dentro = np.all((loc[:, outros] >= a[outros] - 0.5) & (loc[:, outros] <= b[outros] + 0.5), axis=1)
        plano = b[eixo] if lado else a[eixo]
        dist = (loc[:, eixo] - plano) * (1 if lado else -1)
        sel = dentro & (dist > -1.5) & (dist < 3.0)
        out[face] = np.median(sup_cor[sel], 0) if sel.sum() >= 3 else geral
    return out


def retangulos_box_uv(u, v, w, h, d):
    return {
        "east": (u, v + d, d, h), "north": (u + d, v + d, w, h), "west": (u + d + w, v + d, d, h),
        "south": (u + 2 * d + w, v + d, w, h), "up": (u + d, v, w, d), "down": (u + d + w, v, w, d),
    }


def textura_bloqueio(cubos, offsets, lado, sup_pos, sup_cor):
    img = np.zeros((lado, lado, 4), np.uint8)
    for c in cubos:
        if c.get("espelho_de"):
            continue
        u, v = offsets[c["nome"]]
        w, h, d = (int(round(x)) for x in (np.asarray(c["to"]) - np.asarray(c["from"])))
        # gola/fita só pegam o pano vinho e garras só o osso claro, não o pelo vizinho
        filtro = cb.vermelho(sup_cor) if "scarf" in c["nome"] else cb.cremoso(sup_cor) if "claw" in c["nome"] else None
        if filtro is not None and filtro.sum() >= 3:
            cores = cores_das_faces(c, sup_pos[filtro], sup_cor[filtro])
        else:
            cores = cores_das_faces(c, sup_pos, sup_cor)
        for face, (x, y, ww, hh) in retangulos_box_uv(u, v, w, h, d).items():
            img[y:y + hh, x:x + ww, :3] = np.clip(cores[face], 0, 255).astype(np.uint8)
            img[y:y + hh, x:x + ww, 3] = 255
    return Image.fromarray(img, "RGBA")


def locators(esq, g, rot, ossos):
    J = esq["juntas"]
    idx = {o["nome"]: k for k, o in enumerate(ossos)}

    def centro(*nomes):
        sel = np.isin(rot, [idx[n] for n in nomes if n in idx])
        return g.pos[sel].mean(0) if sel.any() else np.zeros(3)

    locs = [("loc_ground", "root", [0, 0, 0]), ("loc_center", "torso", centro("pelvis", "waist", "torso"))]
    if "head" in idx:
        cab = g.pos[rot == idx["head"]]
        hc = cab.mean(0)
        locs += [("loc_head_look", "head", hc), ("loc_mouth", "head", J["head_fim"] + [0, -1.0, 1.0]),
                 ("loc_top", "head", [0, cab[:, 1].max() + 3, hc[2]])]
    for lado in ("left", "right"):
        if f"hand_{lado}" in idx:
            locs.append((f"loc_hand_{lado}", f"hand_{lado}", J[f"hand_{lado}"] + 0.4 * (J[f"hand_{lado}_fim"] - J[f"hand_{lado}"])))
        if f"foot_{lado}" in idx:
            p = np.array(J[f"foot_{lado}_fim"], float)
            locs.append((f"loc_foot_{lado}", f"foot_{lado}", [p[0], 0.0, (p[2] + J[f"foot_{lado}"][2]) / 2]))
    ultima = max((n for n in idx if n.startswith("tail_")), key=lambda n: int(n.split("_")[1]), default=None)
    if ultima:
        locs.append(("loc_tail_tip", ultima, J["tail_fim"]))
    return [{"nome": n, "osso": o, "posicao": r4(p)} for n, o, p in locs]


def gerar_ops(nome, ossos, cubos, offsets, lado, textura_png, locs):
    buf = io.BytesIO()
    textura_png.save(buf, format="PNG")
    uri = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    lote = [{"op": "set_model_properties", "name": nome, "resolution": {"width": lado, "height": lado}},
            {"op": "add_texture", "name": "cores_malha", "source": uri,
             "width": textura_png.width, "height": textura_png.height}]
    for o in ossos:
        op = {"op": "add_group", "name": o["nome"], "origin": r4(o["pivo"])}
        if o["pai"]:
            op["parent"] = o["pai"]
        lote.append(op)
    for c in cubos:
        op = {"op": "add_cube", "name": c["nome"], "parent": c["osso"], "from": r4(c["from"]), "to": r4(c["to"]),
              "origin": r4(c["origin"]), "rotation": [round(float(x), 2) for x in c["rotation"]],
              "box_uv": True, "texture": "cores_malha", "uv_offset": [int(x) for x in offsets[c["nome"]]]}
        if c.get("espelho_de"):
            op["mirror_uv"] = True
        lote.append(op)
    for l in locs:
        lote.append({"op": "add_locator", "name": l["nome"], "parent": l["osso"], "position": l["posicao"]})
    return lote


def metricas(cubos, ocupado, origem, voxel):
    idx = np.argwhere(np.ones(ocupado.shape, bool))
    pts = origem + (idx + 0.5) * voxel
    dentro = np.zeros(len(pts), bool)
    for c in cubos:
        dentro |= cb.pontos_dentro(c, pts)
    occ = ocupado.reshape(-1)
    inter = int((dentro & occ).sum())
    uniao = int((dentro | occ).sum())
    return {"iou_3d": round(inter / max(uniao, 1), 3), "malha_coberta": round(inter / max(int(occ.sum()), 1), 3),
            "cubo_dentro_da_malha": round(inter / max(int(dentro.sum()), 1), 3)}


def folha_partes(dados, esq, g, rot, ossos):
    pos = dados["origem"] + (dados["sup_idx"] + 0.5) * float(dados["voxel"])
    ids = g.ids[tuple(dados["sup_idx"].T)]
    rng = np.random.default_rng(7)
    paleta = rng.integers(40, 235, size=(len(ossos), 3)).astype(np.uint8)
    cores = np.where(ids[:, None] >= 0, paleta[rot[np.maximum(ids, 0)]], 128).astype(np.uint8)
    return vistas.folha_esqueleto(pos, cores, esq, titulo="partes por osso")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta")
    ap.add_argument("--nome", default=None)
    ap.add_argument("--garras", type=int, default=3, help="garras por mão (identidade da ficha)")
    ap.add_argument("--estilo", choices=("equilibrio", "anatomia"), default="equilibrio",
                    help="equilibrio: silhueta da v4 com estrutura limpa (padrão); anatomia: v6 inteira")
    ap.add_argument("--textura", choices=("projetada", "bloqueio"), default="projetada",
                    help="projetada: cada pixel puxa a cor da malha (paleta curta); bloqueio: cor por face")
    ap.add_argument("--fator-textura", type=int, default=2, help="pixels de textura por unidade (Pavão: 2)")
    ap.add_argument("--sem-pelo", action="store_true", help="não cria planos de juba/tufos")
    args = ap.parse_args()
    pasta = Path(args.pasta).resolve()  # o motor resolve caminhos relativos a modelos/
    nome = args.nome or f"{pasta.parent.name}-{pasta.name}"
    t0 = time.time()
    dados = np.load(pasta / "voxels.npz")
    ocupado, origem, voxel = dados["ocupado"], dados["origem"], float(dados["voxel"])
    sup_pos = origem + (dados["sup_idx"] + 0.5) * voxel
    sup_cor = dados["sup_cor"].astype(float)
    corr = pasta / "juntas-corrigidas.json"
    sobrescrever = json.loads(corr.read_text(encoding="utf-8")) if corr.exists() else None

    esq = esqueleto.detectar(ocupado, origem, voxel, sobrescrever=sobrescrever, cores=(sup_pos, sup_cor))
    ossos = esq["ossos"]
    vistas.folha_esqueleto(sup_pos, dados["sup_cor"], esq, titulo=nome).save(pasta / "diagnostico-juntas.png")

    ajustar = cb.ajustar_anatomia if args.estilo == "anatomia" else cb.ajustar
    extra = {} if args.estilo == "anatomia" else {"pelo": not args.sem_pelo}
    cubos, g, rot, removidos = ajustar(ocupado, origem, voxel, ossos, dados["sup_idx"], sup_cor,
                                       n_garras=args.garras, **extra)
    folha_partes(dados, esq, g, rot, ossos).save(pasta / "diagnostico-partes.png")

    locs = locators(esq, g, rot, ossos)
    # ajustes do usuário (pose e cubos editados à mão) antes da UV: tamanhos podem mudar; a textura
    # projetada busca a cor de cada cubo movido no lugar onde ele estava na malha
    feitos_ajustes = ajustes.aplicar(pasta, cubos, ossos, locs)
    offsets, (lado, _) = ops.distribuir_uv(cubos, margem=0, larguras=(64, 128, 256, 512))
    bloqueio = textura_bloqueio(cubos, offsets, lado, sup_pos, sup_cor)
    bloqueio.save(pasta / "textura-bloqueio.png")
    lote = gerar_ops(nome, ossos, cubos, offsets, lado, bloqueio, locs)
    (pasta / "ops.json").write_text(json.dumps({"operations": lote}, ensure_ascii=False) + "\n", encoding="utf-8")

    # regrava o próprio arquivo gerado; se alguém editou à mão, sai uma versão nova (.v2, .v3…)
    anterior = json.loads((pasta / "relatorio.json").read_text(encoding="utf-8")) if (pasta / "relatorio.json").exists() else {}
    hashes = {anterior.get("arquivo"): anterior.get("sha256")} if anterior.get("arquivo") else {}
    arquivo, aviso_versao = cubificar.destino_bbmodel(pasta, nome, hashes)
    motor.criar(arquivo, nome, lado, lado)
    motor.editar(arquivo, lote)
    fator = 1
    if args.textura == "projetada":
        # 2ª passada: com as UVs que o motor gravou, pinta cada pixel com a cor da malha e regrava
        mapa = textura.mapa_superficie(ocupado.shape, dados["sup_idx"])
        pal = textura.paleta_com_destaques(sup_cor, k=16)
        info = {c["nome"]: c for c in cubos}
        fator = max(1, args.fator_textura)
        destaque = cb.vermelho(sup_cor) | cb.dourado(sup_cor)
        mapa_corpo = textura.mapa_superficie(ocupado.shape, dados["sup_idx"][~destaque])
        # rosto: tons e olhos tirados da malha na região dos cubos da cabeça
        cab = [c for c in cubos if c["osso"] == "head" and not c.get("plano")]
        rosto = None
        if cab:
            cantos = np.concatenate([[c["from"], c["to"]] for c in cab])
            rosto = textura.rosto_da_malha(sup_pos, sup_cor, cantos.min(0) - 1.5, cantos.max(0) + 1.5)
        pintada = textura.pintar(arquivo, info, fator, origem, voxel, mapa, sup_cor, pal,
                                 sup_pos=sup_pos, filtro_pano=cb.vermelho(sup_cor),
                                 mapa_corpo=mapa_corpo, cores_corpo=sup_cor[~destaque], rosto=rosto,
                                 ocupado=ocupado)
        pintada.save(pasta / "textura-projetada.png")
        lote = gerar_ops(nome, ossos, cubos, offsets, lado, pintada, locs)
        (pasta / "ops.json").write_text(json.dumps({"operations": lote}, ensure_ascii=False), encoding="utf-8")
        motor.criar(arquivo, nome, lado, lado)
        motor.editar(arquivo, lote)
        tex = json.loads(arquivo.read_text(encoding="utf-8"))["textures"][0]
        if tex.get("uv_width") not in (None, lado):
            raise SystemExit(f"textura {tex.get('width')} com uv_width {tex.get('uv_width')} (esperado {lado})")
    validacao = motor.validar(arquivo)
    erros, avisos, linhas_val = motor.resumo_validacao(validacao)

    m = metricas(cubos, ocupado, origem, voxel)
    conceito = None
    for c in ("conceito.png",):
        if (pasta / "entrada" / c).exists():
            conceito = Image.open(pasta / "entrada" / c).convert("RGB")
    try:
        vistas_img = folha.vistas_do_motor(arquivo)
    except motor.MotorErro:
        vistas_img = folha.vistas_proprias(arquivo, None)
    folha.montar(conceito, vistas_img, titulo=arquivo.stem).save(pasta / "folha.png")

    # cópia com o hash no nome: o Blockbench reaproveita a aba de um caminho já aberto sem reler o
    # disco (decisão 0002), então cada versão nova precisa de um nome novo para abrir na hora
    abrir = pasta / "abrir"
    abrir.mkdir(exist_ok=True)
    preservadas = []
    for velho in abrir.glob(f"{nome}.*.bbmodel"):
        # só apaga cópias intactas (o nome leva o hash do conteúdo); cópia salva pelo usuário fica
        if cubificar.sha256(velho)[:8] == velho.stem.split(".")[-1]:
            velho.unlink()
        else:
            preservadas.append(velho.name)
    copia = abrir / f"{nome}.{cubificar.sha256(arquivo)[:8]}.bbmodel"
    copia.write_bytes(arquivo.read_bytes())

    # vistas em fundo claro (renderizador próprio), mais fáceis de ler que o render escuro do motor
    from criaturas import bbmodelo, render
    modelo = bbmodelo.ler(arquivo)
    lo_m, hi_m = bbmodelo.limites(modelo)
    ims = [render.renderizar(modelo, v, escala=8, limites=(lo_m, hi_m))[0] for v in ("frente", "lado", "3/4")]
    claras = Image.new("RGB", (sum(i.width for i in ims) + 16, max(i.height for i in ims)), (240, 240, 244))
    x = 0
    for im in ims:
        claras.paste(im, (x, (claras.height - im.height) // 2))
        x += im.width + 8
    f = min(1.0, 1024 / max(claras.size))
    claras.resize((int(claras.width * f), int(claras.height * f)), Image.LANCZOS).save(pasta / "vistas-claras.png")

    renders = pasta / "entrada" / "renders"
    if (renders / "malha-lado.png").exists() and (renders / "malha-34.png").exists():
        comparar.gerar(pasta, arquivo, renders / "malha-lado.png", renders / "malha-34.png")

    rel = {"arquivo": arquivo.name, "sha256": cubificar.sha256(arquivo), "aviso_versao": aviso_versao,
           "cubos": len(cubos), "ossos": len(ossos), "locators": len(locs),
           "textura": [lado * fator, lado * fator], "uv": [lado, lado], "tipo_textura": args.textura,
           "garras": args.garras, "estilo": args.estilo, **m,
           "planos": [c["nome"] for c in cubos if c.get("plano")], "ajustes_do_usuario": feitos_ajustes,
           "removidos_na_limpeza": removidos, "validacao": {"erros": erros, "avisos": avisos},
           "por_osso": {o["nome"]: sum(1 for c in cubos if c["osso"] == o["nome"]) for o in ossos},
           "segundos": round(time.time() - t0, 1)}
    (pasta / "relatorio.json").write_text(json.dumps(rel, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    n_planos = sum(1 for c in cubos if c.get("plano"))
    print(f"{arquivo.name}: {len(cubos) - n_planos} cubos + {n_planos} planos, {len(ossos)} ossos, {len(locs)} locators, "
          f"textura {lado * fator}² (UV {lado}²)")
    print(f"IoU 3D {m['iou_3d']:.0%} · malha coberta {m['malha_coberta']:.0%} · cubo dentro da malha {m['cubo_dentro_da_malha']:.0%}")
    print(f"validação: {erros} erros, {avisos} avisos")
    for linha in linhas_val[:6]:
        print("  " + linha)
    print("por osso: " + ", ".join(f"{k}={v}" for k, v in rel["por_osso"].items() if v))
    print(f"folha: {pasta / 'folha.png'}  ({rel['segundos']} s)")
    print(f"para abrir no Blockbench: {copia}")
    for n in preservadas:
        print(f"aviso: {n} foi editado à mão no Blockbench e ficou guardado em abrir/ (não apagado)")
    for f_ in feitos_ajustes:
        print(f"ajuste do usuário: {f_}")


if __name__ == "__main__":
    main()
