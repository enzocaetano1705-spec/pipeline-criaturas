"""Retoque sem reprojetar a geometria: atlas existente + regras semânticas por criatura.

Escreve uma versão nova pelo motor Blockbench. A fonte, seus ossos, UVs e locators
permanecem intactos. Configurações desta preguiça não viram regras de outras espécies.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import shutil
from collections import Counter, deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from criaturas import bbmodelo, motor, render


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def assinatura(model):
    """Tudo que pode afetar geometria, ossos, UV, locators e animação; exclui só a textura."""
    keys = ("elements", "groups", "outliner", "animations", "resolution")
    data = {k: model.bruto.get(k) for k in keys}
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def componentes(mask):
    seen = np.zeros(mask.shape, bool)
    for y, x in np.argwhere(mask):
        if seen[y, x]:
            continue
        seen[y, x] = True
        todo, out = deque([(int(y), int(x))]), []
        while todo:
            q, p = todo.popleft()
            out.append((q, p))
            for v, u in ((q-1, p), (q+1, p), (q, p-1), (q, p+1)):
                if 0 <= v < mask.shape[0] and 0 <= u < mask.shape[1] and mask[v, u] and not seen[v, u]:
                    seen[v, u] = True
                    todo.append((v, u))
        yield out


def vinho(rgb):
    a = rgb.astype(float)
    return (a[..., 0] > a[..., 1]*1.35) & (a[..., 2] > a[..., 1]*.88) & (a[..., 0] > 55)


def preencher(rgb, mask, valid):
    """Inpainting discreto, sem blur: só cores dos vizinhos válidos na mesma ilha UV."""
    out, pending = rgb.copy(), mask.copy()
    for _ in range(sum(mask.shape)):
        changes = []
        for y, x in np.argwhere(pending):
            cs = [tuple(out[v, u]) for v, u in ((y-1,x),(y+1,x),(y,x-1),(y,x+1))
                  if 0 <= v < len(mask) and 0 <= u < mask.shape[1] and valid[v,u] and not pending[v,u]]
            if cs:
                changes.append((y, x, Counter(cs).most_common(1)[0][0]))
        if not changes:
            out[pending] = (123, 59, 31)
            break
        for y, x, c in changes:
            out[y,x], pending[y,x] = c, False
    return out


def limpar(rgb, opaque, area=3):
    out, count = rgb.copy(), 0
    colors = np.unique(rgb[opaque], axis=0)
    for color in colors:
        mask = np.all(rgb == color, axis=2) & opaque
        for comp in componentes(mask):
            if len(comp) > area:
                continue
            patch = np.zeros(mask.shape, bool)
            yy, xx = np.array(comp).T
            patch[yy,xx] = True
            # Não eliminar um detalhe se não houver uma borda de material vizinho.
            new = preencher(out, patch, opaque)
            count += int(np.count_nonzero(np.any(out != new, axis=2)))
            out = new
    return out, count


def faces(model):
    mats = bbmodelo.matrizes_ossos(model)
    sx, sy = np.asarray(model.textura.size) / model.resolucao
    used = set()
    for cube in model.cubos:
        M = bbmodelo.matriz_cubo(model, cube, mats)
        lim = np.stack([cube.de-cube.inflate, cube.ate+cube.inflate])
        for face, corners in render.CANTOS_FACE.items():
            uv = cube.faces.get(face, {}).get("uv")
            if not uv or abs(uv[2]-uv[0]) < 1e-5 or abs(uv[3]-uv[1]) < 1e-5:
                continue
            u1,v1,u2,v2 = uv
            x0,x1 = sorted((round(u1*sx),round(u2*sx)))
            y0,y1 = sorted((round(v1*sy),round(v2*sy)))
            key = (x0,y0,x1,y1)
            if key in used:
                continue  # os membros espelhados compartilham ilhas UV
            used.add(key)
            s = ((np.arange(x0,x1)+.5)/sx-u1)/(u2-u1)
            t = ((np.arange(y0,y1)+.5)/sy-v1)/(v2-v1)
            ss,tt = np.meshgrid(s,t)
            tl,tr,bl,_ = (np.array([lim[i,0],lim[j,1],lim[k,2]]) for i,j,k in corners)
            L = tl+ss[...,None]*(tr-tl)+tt[...,None]*(bl-tl)
            W = bbmodelo.aplicar(M,L.reshape(-1,3)).reshape(L.shape)
            yield cube,face,(slice(y0,y1),slice(x0,x1)),L,W


def pano(W, cfg):
    palette = cfg["paleta"]
    rgb = np.empty(W.shape, np.uint8)
    rgb[:] = palette["vinho"]
    # Dobras em coordenadas do modelo, não molduras repetidas por face.
    y,z = W[...,1],W[...,2]
    rgb[(z > -13) & (y < 29)] = palette["vinho_sombra"]
    rgb[(y > 32) & (z < -10)] = palette["vinho_luz"]
    return rgb


def cabeca(cube, face, L, rgb, cfg):
    p = cfg["paleta"]
    x,y,z = L[...,0],L[...,1],L[...,2]
    rgb[:] = p["creme"]
    if cube.nome == "head":
        fur = (y > 31.7) | (z > -22.2)
        rgb[fur] = p["pelo"]
        rgb[fur & (y > 32.7)] = p["pelo_luz"]
        rgb[y < 26.5] = p["pelo_sombra"]
    elif cube.nome == "head_2":
        rgb[(y > 30.0) & (z > -27.5)] = p["pelo"]
        rgb[y < 25.7] = p["creme_sombra"]
        # Um olho inteiro por face lateral, afastado das quinas do cubo.
        if face in ("east", "west"):
            eye = cfg["olho"]
            sprite = eye["desenho"]
            h,w = len(sprite),len(sprite[0])
            density = eye["pixels_por_unidade"]
            col = np.floor((z-eye["z"])*density+w/2).astype(int)
            row = np.floor((eye["y"]-y)*density+h/2).astype(int)
            inside = (col >= 0) & (col < w) & (row >= 0) & (row < h)
            pattern = np.array([list(line) for line in sprite])
            samples = pattern[np.clip(row,0,h-1),np.clip(col,0,w-1)]
            for symbol,color in (("D","escuro"),("A","ambar"),("P","pupila")):
                rgb[inside & (samples == symbol)] = p[color]
    else:  # focinho: nariz no alto, sem o retângulo escuro que parecia uma boca aberta
        rgb[y < 24.65] = p["creme_sombra"]
        if face == "north":
            center = (cube.de[0]+cube.ate[0])/2
            dy = (27.8-y)/1.55
            nose = (dy >= 0) & (dy < 1) & (np.abs(x-center) < 1.65*(1-.48*dy))
            rgb[nose] = p["escuro"]
            rgb[nose & (y > 27.35)] = p["nariz_luz"]
            rgb[nose & (np.abs(x-center) > .8) & (y < 27.4)] = p["pupila"]
    return rgb


def retocar(model, cfg):
    atlas = np.asarray(model.textura).copy()
    original = atlas.copy()
    changes = []
    scarf = model.cubo("scarf_collar_1")
    inv_scarf = np.linalg.inv(bbmodelo.matriz_cubo(model,scarf,bbmodelo.matrizes_ossos(model)))
    for cube,face,sl,L,W in faces(model):
        patch = atlas[sl].copy()
        rgb,alpha = patch[...,:3].copy(),patch[...,3].copy()
        opaque = alpha > 127
        if not opaque.any():
            continue
        planar = np.min(cube.tamanho) < 1e-6
        special = cube.osso == "head" and not planar
        cloth = "scarf" in cube.nome
        removed = 0
        if not cloth and not special and "claw" not in cube.nome:
            rgb = preencher(rgb,vinho(rgb) & opaque,opaque)
            rgb,removed = limpar(rgb,opaque,cfg["limpeza_area"])
        if planar:
            for comp in componentes(opaque):
                if len(comp) <= cfg["recorte_area"]:
                    yy,xx = np.array(comp).T
                    alpha[yy,xx] = 0
        if special:
            rgb = cabeca(cube,face,L,rgb,cfg)
        if cloth:
            rgb = pano(W,cfg)
        elif cube.nome in ("neck_1","neck_1_fur","torso","torso_fur"):
            Q = bbmodelo.aplicar(inv_scarf,W.reshape(-1,3)).reshape(W.shape)
            if cube.nome == "neck_1":
                mask = (Q[...,2] >= -16.8) & (Q[...,1] >= 22.4) & (Q[...,1] <= 35.8)
            else:
                mask = ((Q[...,2] >= -13) & (Q[...,1] >= 28+.35*np.abs(Q[...,0]))
                        & (Q[...,1] <= 35.8))
                if cube.nome == "torso" and face == "north":
                    mask[:] = False  # peito é pelo, não uma projeção do pano das costas
                if planar:
                    # A lâmina central de pelo atravessa a gola: a parte dentro do
                    # manto recebe o mesmo tecido, inclusive acima da borda do cubo.
                    mask |= ((W[...,2] > -14.5) & (W[...,2] < -4.5)
                             & (W[...,1] > 30.3) & (W[...,1] < 38))
            rgb[mask] = pano(W,cfg)[mask]
        if cube.nome == "arm_left":
            # Uma marca contínua em 3D atravessa as UVs do ombro; não salpicos por face.
            old_cream = (rgb[...,0] > 168) & (rgb[...,1] > 105) & opaque
            rgb = preencher(rgb,old_cream,opaque)
            stripe = np.abs(L[...,2]-(-10.6+.13*(L[...,1]-23))) < (1.45+.18*np.cos(L[...,1]*1.7))
            stripe &= (L[...,0] < -10.8) & (L[...,1] > 18.6)
            rgb[stripe] = cfg["paleta"]["creme"]
        patch[...,:3],patch[...,3] = rgb,alpha
        atlas[sl] = patch
        n = int(np.count_nonzero(np.any(patch!=original[sl],axis=2)))
        if n:
            changes.append(dict(cubo=cube.nome,face=face,pixels=n,ruido_limpo=removed))
    return Image.fromarray(atlas), changes


def quadro(before,after,path):
    """Uma folha de até 768 px: detalhes nas mesmas câmeras, antes/depois."""
    out = Image.new("RGB",(768,768),(241,243,246))
    d = ImageDraw.Draw(out)
    d.text((8,6),"ANTES                                      RETOQUE",fill=(30,35,45))
    cases = [((105,12),{"head","head_2","head_3"},"Olho de perfil"),
             ((35,12),{"head","head_2","head_3"},"Focinho / nariz"),
             ((155,28),{"neck_1","scarf_collar_1","torso"},"Costas do cachecol"),
             ((35,-18),{"neck_1","scarf_collar_1","arm_left"},"Peito / ombro / emendas")]
    for row,(angle,names,label) in enumerate(cases):
        a=render.renderizar(before,angle,escala=18,fundo=(241,243,246))
        b=render.renderizar(after,angle,escala=18,projecao=a[3],fundo=(241,243,246))
        ids=[i for i,c in enumerate(before.cubos) if c.nome in names]
        yy,xx=np.where(np.isin(a[2],ids))
        box=(max(0,int(xx.min())-12),max(0,int(yy.min())-12),min(a[0].width,int(xx.max())+13),min(a[0].height,int(yy.max())+13))
        for col,item in enumerate((a,b)):
            im=item[0].crop(box)
            im.thumbnail((376,160),Image.Resampling.NEAREST)
            out.paste(im,(col*384+(384-im.width)//2,34+row*184+(160-im.height)//2))
        d.text((8,24+row*184),label,fill=(30,35,45))
    out.save(path)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fonte",type=Path)
    parser.add_argument("config",type=Path)
    parser.add_argument("saida",type=Path)
    args=parser.parse_args()
    source=args.fonte.resolve(strict=True)
    target=args.saida.resolve()
    if target.exists():
        raise SystemExit("Saída existe: use outra versão, não sobrescreva pintura do usuário")
    target.parent.mkdir(parents=True,exist_ok=True)
    model=bbmodelo.ler(source)
    image,changes=retocar(model,json.loads(args.config.read_text(encoding="utf-8")))
    image.save(target.parent/"textura.png")
    buf=io.BytesIO();image.save(buf,format="PNG")
    ops=[dict(op="update_texture",target=model.bruto["textures"][0]["uuid"],material=None,
              source="data:image/png;base64,"+base64.b64encode(buf.getvalue()).decode(),width=image.width,height=image.height)]
    (target.parent/"ops.json").write_text(json.dumps(dict(operations=ops),ensure_ascii=False)+"\n",encoding="utf-8")
    shutil.copyfile(source,target)
    motor.editar(target,ops)
    after=bbmodelo.ler(target)
    if assinatura(after)!=assinatura(model):
        raise RuntimeError("Motor alterou geometria/UV/hierarquia: resultado recusado")
    validation=motor.validar(target)
    errors,warnings,_=motor.resumo_validacao(validation)
    (target.parent/"validacao.json").write_text(json.dumps(validation,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    report=dict(fonte=str(source),sha256_fonte=sha(source),saida=str(target),sha256_saida=sha(target),
                assinatura_geometria=assinatura(model),geometria_uv_ossos_locators_identicos=True,
                textura=list(image.size),cubos=len(model.cubos),ossos=len(model.ossos),locators=len(model.locators),
                pixels_alterados=int(np.count_nonzero(np.any(np.asarray(model.textura)!=np.asarray(image),axis=2))),
                faces=changes,validacao=dict(erros=errors,avisos=warnings),aprovacao_artistica=False)
    (target.parent/"relatorio.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    quadro(model,after,target.parent/"comparacao.png")
    # Vista geral em quatro ângulos, preservando alfa e as margens originais da UV.
    render.folha(after,lado_px=384,titulo="Preguiça rogue — retoque de textura").save(target.parent/"folha.png")
    print(json.dumps({k:v for k,v in report.items() if k not in ("faces","fonte","saida")},ensure_ascii=False))


if __name__=="__main__":
    main()
