"""Estima enquadramento global das vistas secundárias; não altera a geometria."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'modelos/fera-fera-agil-das-sombras/gabarito-v1'


def bbox(mask):
    y,x=np.where(mask);return np.array([x.min(),y.min(),x.max(),y.max()])


def main():
    rev=sys.argv[1];folder=BASE/rev;fits={};extra='--extras' in sys.argv
    views={'perfil_oposto':'perfil_direito','superior':'superior','inferior':'inferior'} if extra else {'frente':'frente','costas':'costas'}
    for view,refname in views.items():
        ref=np.array(Image.open(BASE/'entrada'/(refname+'-mascara.png')).convert('L'))>127
        src=Image.open(folder/(view+'.png')).convert('RGBA').getchannel('A')
        w,h=src.size;a=np.array(src)>127;bb=bbox(a);rr=bbox(ref)
        best=(-1,None)
        for factor in np.linspace(.83,1.12,16):
            scaled=src.resize((round(w*factor),round(h*factor)),Image.Resampling.BILINEAR)
            center_delta=(rr[:2]+rr[2:])/2-((bb[:2]+bb[2:])/2-np.array([w/2,h/2]))*factor-np.array([w/2,h/2])
            for ox in range(-12,13,4):
                for oy in range(-16,17,4):
                    dx,dy=center_delta+[ox,oy]
                    canvas=Image.new('L',(w,h));canvas.paste(scaled,(round((w-scaled.width)/2+dx),round((h-scaled.height)/2+dy)))
                    mask=np.array(canvas)>127
                    union=(ref|mask).sum();score=(ref&mask).sum()/max(1,union)
                    if score>best[0]:best=(float(score),{'fator_escala_global':float(factor),'translacao_pixel':[float(dx),float(dy)]})
        fits[view]={'iou_previsto_calibracao_2d':best[0],**best[1],
                    'metodo':'uma escala uniforme e translação por câmera; sem deformação de partes','projecao_original_conhecida':False}
    (folder/('calibracao-extras.json' if extra else 'calibracao-enquadramento.json')).write_text(json.dumps(fits,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for name,data in fits.items():print(name,round(data['iou_previsto_calibracao_2d'],3),data['fator_escala_global'],data['translacao_pixel'])


if __name__=='__main__':main()
