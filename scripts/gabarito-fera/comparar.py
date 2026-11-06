"""Sobreposição do render real; sem compor o fundo no render nem deformar partes."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'modelos/fera-fera-agil-das-sombras/gabarito-v1'
REV=sys.argv[1] if len(sys.argv)>1 else 'r01'


def main():
    folder=BASE/REV
    reports={}
    views=[('perfil','perfil_esquerdo'),('frente','frente'),('costas','costas')]
    if (folder/'superior.png').exists():
        views += [('perfil_oposto','perfil_direito'),('superior','superior'),('inferior','inferior')]
    for view,ref in views:
        a=np.array(Image.open(BASE/'entrada'/(ref+'-mascara.png')).convert('L'))>127
        im=Image.open(folder/(view+'.png')).convert('RGBA')
        b=np.array(im)[...,3]>127
        assert a.shape==b.shape
        intersection=int((a&b).sum());union=int((a|b).sum())
        reports[view]={'intersecao':intersection,'uniao':union,'iou':intersection/union,
                       'referencia_area':int(a.sum()),'render_area':int(b.sum()),'falta':int((a&~b).sum()),'excesso':int((b&~a).sum()),
                       'alinhamento':'câmera do blend, sem ajuste pós-render','camera_original_conhecida':False,
                       'enquadramento_estimado':view!='perfil' and (folder/'calibracao-enquadramento.json').exists()}
        rgb=np.full((*a.shape,3),245,np.uint8)
        rgb[a&b]=(95,104,111);rgb[a&~b]=(44,162,218);rgb[b&~a]=(234,115,55)
        Image.fromarray(rgb).save(folder/(view+'-sobreposicao.png'))
    (folder/'comparacao-silhuetas.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # Crops are diagnostics only, not semantic part segmentation or a quality grade.
    a=np.array(Image.open(BASE/'entrada/perfil_esquerdo-mascara.png'))>127
    b=np.array(Image.open(folder/'perfil.png').convert('RGBA'))[...,3]>127
    regions={}
    for name,(x0,y0,x1,y1) in {'cabeca_juba':(112,77,358,211),'braco_mao':(110,220,296,367),'perna_pe':(230,274,344,396),'cauda':(399,235,635,390)}.items():
        r=a[y0:y1,x0:x1];m=b[y0:y1,x0:x1]
        regions[name]={'iou_recorte':float((r&m).sum()/max(1,(r|m).sum())),'nota':'recortes podem sobrepor partes/oclusões; não são máscaras anatômicas isoladas'}
    (folder/'diagnostico-regioes.json').write_text(json.dumps(regions,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',13)
    small=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',11)
    sheet=Image.new('RGB',(768,768),'#f5f5f5');d=ImageDraw.Draw(sheet)
    def put(path,x,y,w,h,title):
        im=Image.open(path).convert('RGBA');im.thumbnail((w-10,h-30),Image.Resampling.LANCZOS)
        bg=Image.new('RGBA',im.size,'#f5f5f5');bg.alpha_composite(im)
        sheet.paste(bg.convert('RGB'),(x+(w-im.width)//2,y+26+(h-30-im.height)//2));d.text((x+7,y+5),title,font=font,fill='#333333')
    put(BASE/'entrada/perfil_esquerdo.png',0,0,384,240,'Perfil fornecido')
    put(folder/'perfil.png',384,0,384,240,'Reconstrução por seções')
    put(folder/'perfil-sobreposicao.png',0,240,768,270,f'Perfil · IoU {reports["perfil"]["iou"]:.1%} · azul: falta / laranja: excesso')
    put(folder/'3-4.png',0,510,256,258,'Geometria em 3/4')
    put(folder/'frente-sobreposicao.png',256,510,256,258,f'Frente · IoU {reports["frente"]["iou"]:.1%}')
    put(folder/'costas-sobreposicao.png',512,510,256,258,f'Costas · IoU {reports["costas"]["iou"]:.1%}')
    sheet.save(folder/'folha-auditoria.png')
    for view,r in reports.items():print(view,f'IoU {r["iou"]:.3f}',f'falta {r["falta"]}',f'excesso {r["excesso"]}')


if __name__=='__main__':main()
