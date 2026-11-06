"""Preserva o atlas v11 e faz reparos localizados na revisão editada pelo usuário.

Específico da preguiça rogue. Não usa a simplificação global de retocar.py:
campos de cor novos são restritos ao pano; os olhos e nariz são reparos locais.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

from criaturas import bbmodelo, motor, render
from retocar import faces, preencher, componentes, quadro, sha, vinho


def assinatura_forma(modelo):
    raw = {k: v for k, v in modelo.bruto.items() if k in ("groups", "outliner", "animations", "elements")}
    raw["elements"] = [{k: v for k, v in e.items() if k not in ("faces", "uv_offset")} for e in raw["elements"]]
    return hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest()


def dobrado(Q, cfg):
    """Dobras largas em coordenadas comuns: cores discretas, sem moldura por face."""
    x,y,z = Q[...,0],Q[...,1],Q[...,2]
    d = y-(29.3+.33*np.abs(x)+.10*(z+14.75))
    levels = np.full(x.shape, 3, int)
    levels[d < 0] = 2
    levels[(d > -1.15) & (d < .2)] = 1
    levels[(d >= .2) & (d < 1.2)] = 4
    lower = y-(25.0+.27*np.abs(x)+.08*(z+14.75))
    levels[lower < 0] = 1
    levels[(lower > -.75) & (lower < .15)] = 1
    levels[(lower >= .15) & (lower < .8)] = 3
    return np.asarray(cfg["pano"], np.uint8)[levels]


def recuperar_olho(rgb, face, cfg):
    iris = np.linalg.norm(rgb.astype(float)-[182,120,55],axis=2) < 4
    pupil = np.linalg.norm(rgb.astype(float)-[25,12,8],axis=2) < 4
    feature = iris | pupil
    if not feature.any():
        return rgb,0
    out = preencher(rgb, feature, np.ones(feature.shape,bool))
    if face == "north":
        return out,int(feature.sum())  # elimina só o fragmento duplicado na quina
    yy,xx = np.where(feature)
    center = (feature.shape[1]-1)/2
    delta = int(round(center-(xx.min()+xx.max())/2))
    # Uma margem de um texel deixa o desenho inteiro em uma face lateral.
    delta = int(np.clip(delta,1-int(xx.min()),feature.shape[1]-2-int(xx.max())))
    shifted = np.zeros(feature.shape,bool)
    shifted[yy,xx+delta] = True
    padded = np.pad(shifted,1)
    outline = np.logical_or.reduce([padded[1+dy:1+dy+len(feature),1+dx:1+dx+feature.shape[1]]
                                    for dx,dy in ((0,0),(1,0),(-1,0),(0,1),(0,-1))])
    out[outline & ~shifted] = cfg["mascara_sombra"]
    out[yy,xx+delta] = rgb[yy,xx]
    iy,ix = np.where(iris)
    out[iy,ix+delta] = cfg["iris"]
    if len(iy):
        top = int(iy.min())
        out[iy[iy==top],ix[iy==top]+delta] = cfg["iris_luz"]
    return out,int(np.count_nonzero(np.any(out!=rgb,axis=2)))


def nariz(rgb,cfg):
    out = rgb.copy()
    old = np.linalg.norm(rgb.astype(float)-[74,37,22],axis=2) < 5
    out = preencher(out,old,np.ones(old.shape,bool))
    pattern = cfg["nariz"]["desenho"]
    h,w = len(pattern),len(pattern[0])
    x0,y0 = (rgb.shape[1]-w)//2,cfg["nariz"]["linha"]
    colors = cfg["nariz"]["cores"]
    for y,row in enumerate(pattern):
        for x,s in enumerate(row):
            if s in colors:
                out[y0+y,x0+x] = colors[s]
    return out


def focinho_inteiro(L,cubo,face,cfg):
    """Rinário largo: toda a última peça do focinho recebe pigmentação, não um ponto no bege."""
    p=cfg["focinho"]
    center=(cubo.de+cubo.ate)/2
    size=cubo.ate-cubo.de
    x=(L[...,0]-center[0])/(size[0]/2)
    y=(L[...,1]-cubo.de[1])/size[1]
    z=(L[...,2]-cubo.de[2])/size[2]
    out=np.empty(L.shape,np.uint8);out[:]=p["base"]
    out[y>.64]=p["meio"]
    out[(y>.82)&(np.abs(x)<.68)&(z<.8)]=p["luz"]
    out[y<.23]=p["sombra"]
    if face=="north":
        # Duas narinas, ponte central e reflexão superior, mantendo o desenho em pixels.
        nostrils=(np.abs(np.abs(x)-.46)<.19)&(np.abs(y-.46)<.16)
        out[nostrils]=p["narina"]
        out[(np.abs(x)<.18)&(y>.38)&(y<.68)]=p["meio"]
    return out


def pintar(original,editado,cfg):
    atlas = np.asarray(original.textura).copy()
    source = atlas.copy()
    mats = bbmodelo.matrizes_ossos(editado)
    collar = editado.cubo("scarf_collar_1")
    inverse = np.linalg.inv(bbmodelo.matriz_cubo(editado,collar,mats))
    changed = []
    for c,f,sl,L,W in faces(editado):
        before = atlas[sl].copy()
        rgb,alpha = before[...,:3].copy(),before[...,3].copy()
        Q = bbmodelo.aplicar(inverse,W.reshape(-1,3)).reshape(W.shape)
        cloth = "scarf" in c.nome
        if c.nome == "scarf_collar_1":
            alpha[:] = 255
            rgb = dobrado(Q,cfg)
            # Contorno apenas na barra de tecido, sem contornar cada face do cubo.
            rgb[L[...,1] < collar.de[1]+.55] = cfg["pano"][0]
            if f == "west":
                jewel = cfg["broche"]
                z,y = Q[...,2]-jewel["z"],Q[...,1]-jewel["y"]
                rhombus = np.abs(z)/jewel["raio_z"]+np.abs(y)/jewel["raio_y"]
                rgb[rhombus < 1] = jewel["borda"]
                rgb[(rhombus < .78) & (z < 0)] = jewel["luz"]
                rgb[(rhombus < .78) & (z >= 0)] = jewel["sombra"]
                rgb[(rhombus < .78) & (np.abs(z) < .25)] = jewel["brilho"]
        elif cloth:  # fita: recorte e contorno anterior preservados; dobras no interior
            opaque = alpha > 127
            old_dark = rgb[...,0] < 82
            rgb = dobrado(Q,cfg)
            rgb[old_dark & opaque] = cfg["pano"][0]
        else:
            if c.nome == "head_fur":
                for comp in componentes(alpha > 127):
                    if len(comp) <= 2:
                        yy,xx=np.array(comp).T;alpha[yy,xx]=0
            if cfg.get("pano_somente_scarf",False) and c.nome!="head_3":
                # Material vem do papel da peça. Nunca transformar pelo em pano
                # só porque um campo 3D ou a cor da malha cruzou sua superfície.
                rgb=preencher(rgb,vinho(rgb)&(alpha>127),alpha>127)
            elif c.nome in ("arm_left","leg_left","hand_left"):
                stains = vinho(rgb) & (alpha > 127)
                tiny = np.zeros(stains.shape,bool)
                for comp in componentes(stains):
                    if len(comp) <= 6:
                        yy,xx=np.array(comp).T;tiny[yy,xx]=True
                rgb = preencher(rgb,tiny,alpha>127)
            if c.nome == "head_2" and f in ("east","west","north"):
                rgb,_ = recuperar_olho(rgb,f,cfg)
            if c.nome=="head_3" and cfg.get("focinho_integral",False):
                rgb=focinho_inteiro(L,c,f,cfg)
            elif c.nome == "head_3" and f == "north":
                rgb = nariz(rgb,cfg)
            if not cfg.get("pano_somente_scarf",False) and c.nome in ("neck_1","torso","neck_1_fur","torso_fur"):
                if c.nome == "neck_1":
                    mask=(Q[...,2] >= -16.8)&(Q[...,1] >= collar.de[1])&(Q[...,1] <= collar.ate[1])
                else:
                    mask=(Q[...,2] >= -13)&(Q[...,1] >= 28+.35*np.abs(Q[...,0]))&(Q[...,1] <= collar.ate[1])
                    if c.nome=="torso" and f=="north":mask[:]=False
                    if c.nome.endswith("_fur"):
                        mask|=(W[...,2]>-14.5)&(W[...,2]<-4.5)&(W[...,1]>30.3)&(W[...,1]<38)
                mask |= vinho(rgb) & (alpha > 127)
                rgb[mask] = dobrado(Q,cfg)[mask]
        patch = np.concatenate([rgb,alpha[...,None]],axis=2)
        atlas[sl] = patch
        n=int(np.count_nonzero(np.any(patch!=source[sl],axis=2)))
        if n:changed.append(dict(cubo=c.nome,face=f,pixels=n))
    return Image.fromarray(atlas),changed


def verificar_uv(model):
    cover=np.zeros(model.textura.size[::-1],bool)
    overlaps=[]
    for c,f,sl,L,W in faces(model):
        if cover[sl].any():overlaps.append((c.nome,f,int(cover[sl].sum())))
        cover[sl]=True
    if overlaps:raise RuntimeError(f"Colisões UV inesperadas: {overlaps}")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("original",type=Path);p.add_argument("editado",type=Path)
    p.add_argument("config",type=Path);p.add_argument("saida",type=Path)
    args=p.parse_args();target=args.saida.resolve()
    if target.exists():raise SystemExit("Use outro destino: não sobrescrever versão existente")
    original,edited=bbmodelo.ler(args.original),bbmodelo.ler(args.editado)
    cfg=json.loads(args.config.read_text(encoding="utf-8"))
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(args.editado,target)
    uvops=[dict(op="update_node",target="scarf_collar_1",uv_offset=cfg["colar_uv"])]
    motor.editar(target,uvops)
    current=bbmodelo.ler(target);verificar_uv(current)
    image,changes=pintar(original,current,cfg)
    image.save(target.parent/"textura.png")
    buf=io.BytesIO();image.save(buf,format="PNG")
    texops=[dict(op="update_texture",target=current.bruto["textures"][0]["uuid"],material=None,
                 width=image.width,height=image.height,source="data:image/png;base64,"+base64.b64encode(buf.getvalue()).decode())]
    (target.parent/"ops.json").write_text(json.dumps(dict(operations=uvops+texops))+"\n",encoding="utf-8")
    motor.editar(target,texops)
    after=bbmodelo.ler(target)
    assert assinatura_forma(after)==assinatura_forma(edited)
    assert all(c.faces==edited.cubo(c.nome).faces for c in after.cubos if c.nome!="scarf_collar_1")
    # Não basta uma proporção global dominada por UV vazia: conferir cada face protegida.
    protected={};oldarr=np.asarray(original.textura);newarr=np.asarray(after.textura)
    head_fur_rgb_preserved=True
    for c in original.cubos:
        if c.nome not in cfg["preservar_integral"] and c.nome!="head_fur":continue
        for f,uv in c.faces.items():
            u1,v1,u2,v2=uv["uv"]
            sx,sy=np.asarray(original.textura.size)/original.resolucao
            x0,x1=sorted((round(u1*sx),round(u2*sx)))
            y0,y1=sorted((round(v1*sy),round(v2*sy)))
            sl=(slice(y0,y1),slice(x0,x1))
            if c.nome=="head_fur":
                head_fur_rgb_preserved &= np.array_equal(oldarr[sl][...,:3],newarr[sl][...,:3])
                assert head_fur_rgb_preserved,(c.nome,f)
            else:
                same=np.array_equal(oldarr[sl],newarr[sl]);assert same,(c.nome,f)
        if c.nome!="head_fur":protected[c.nome]=True
    val=motor.validar(target);errors,warnings,_=motor.resumo_validacao(val)
    (target.parent/"validacao.json").write_text(json.dumps(val,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    report=dict(original=str(args.original),entrada_editada=str(args.editado),saida=str(target),
                sha256_original=sha(args.original),sha256_editada=sha(args.editado),sha256_saida=sha(target),
                forma_editada_preservada=True,assinatura_forma=assinatura_forma(after),
                uv_alteradas_apenas_colar=True,uv_colar=cfg["colar_uv"],sobreposicoes_uv=0,
                cores_textura=len(image.getcolors(1000000)),faces_protegidas_integras=protected,
                textura=list(image.size),uv=list(after.resolucao),alteracoes=changes,
                validacao=dict(erros=errors,avisos=warnings),aprovacao_artistica=False)
    # O plano da cabeça conserva suas cores; só quatro texels de alfa órfãos são removidos.
    report["head_fur_rgb_preservado"] = bool(head_fur_rgb_preserved)
    report["alfa_orfao_removido"] = int(np.count_nonzero((oldarr[...,3]>127)&(newarr[...,3]<128)))
    (target.parent/"relatorio.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    shutil.copyfile(args.config,target.parent/"arte.json")
    quadro(edited,after,target.parent/"comparacao.png")
    render.folha(after,lado_px=384,titulo="Textura original recuperada — revisão localizada").save(target.parent/"folha.png")
    print(json.dumps({k:v for k,v in report.items() if k in ("forma_editada_preservada","uv_alteradas_apenas_colar","sobreposicoes_uv","cores_textura","validacao","faces_protegidas_integras")},ensure_ascii=False))


if __name__=="__main__":main()
