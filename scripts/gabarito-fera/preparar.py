"""Capturas fornecidas -> máscaras/grade, sem consultar ou extrair o serviço pago."""
from pathlib import Path
from hashlib import sha256
import json,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'modelos/fera-fera-agil-das-sombras/gabarito-v1'
FILES={'perfil_direito':'37b44ef9-eb4d-4397-ac98-6108f226abf5','frente':'ddece7eb-631a-4bcd-ae66-06ca94ad0cab',
       'perfil_esquerdo':'50598c86-6128-42c3-bbf4-31ab3e2292c5','superior':'751ad35d-0676-41db-98b6-e96f2ebc746c',
       'costas':'e692b1e2-1e02-46a3-8a80-964334c8e628','inferior':'aeb799dc-c5cb-4418-86a1-904af4634dd3'}


def main():
    folder=BASE/'entrada';folder.mkdir(parents=True,exist_ok=True)
    records={}
    for view,ident in FILES.items():
        src=Path.home()/'AppData/Local/Temp'/('codex-clipboard-'+ident+'.png')
        dst=folder/(view+'.png')
        if dst.exists():
            assert sha256(dst.read_bytes()).digest()==sha256(src.read_bytes()).digest(),'Fonte mudou: criar outra entrada'
        else:shutil.copy2(src,dst)
        im=Image.open(src).convert('RGB');rgb=np.array(im,dtype=float)
        corners=np.concatenate([rgb[:12,:12].reshape(-1,3),rgb[:12,-12:].reshape(-1,3),rgb[-12:,:12].reshape(-1,3),rgb[-12:,-12:].reshape(-1,3)])
        bg=np.median(corners,axis=0)
        # A captura tem vinheta/gradiente: cor fixa confunde fundo com criatura.
        yy0,xx0=np.indices(rgb.shape[:2]);x=2*xx0/(im.width-1)-1;y=2*yy0/(im.height-1)-1
        design=np.stack([np.ones_like(x),x,y,x*y,x*x,y*y],axis=-1)
        border=(xx0<10)|(xx0>=im.width-10)|(yy0<10)|(yy0>=im.height-10)
        coeff=np.linalg.lstsq(design[border],rgb[border],rcond=None)[0]
        background=design@coeff
        distance=np.linalg.norm(rgb-background,axis=2)
        mask=distance>30
        yy,xx=np.where(mask)
        bbox=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]
        Image.fromarray(mask.astype('uint8')*255).save(folder/(view+'-mascara.png'))
        guide=im.copy();d=ImageDraw.Draw(guide)
        for x in range(0,im.width,40):
            d.line((x,0,x,im.height),fill=(110,150,165));d.text((x+2,2),str(x),fill='white')
        for y in range(0,im.height,40):
            d.line((0,y,im.width,y),fill=(110,150,165));d.text((2,y+2),str(y),fill='white')
        guide.save(folder/(view+'-grade.png'))
        records[view]={'arquivo':dst.name,'sha256':sha256(dst.read_bytes()).hexdigest(),'tamanho':list(im.size),'bbox':bbox,'area_mascara':int(mask.sum()),'fundo_rgb':bg.tolist(),'modelo_fundo':'quadrático ajustado às bordas sem modelo','erro_borda_max':float(distance[border].max()),'limiar_distancia_rgb':30,'rotulo_camera':'provisório; estimar projeção antes de medir em 3D'}
    manifest={'fontes':records,'forma_dominante':'capturas fornecidas do mesmo modelo; perfil esquerdo como âncora','cores':'ilustrações originais; nenhuma textura nesta revisão','estado':'calibração e reconstrução em estudo','estagio':'3 de 3','base':'preguiça gigante','arquetipo':'rogue','incertezas':['projeção/FOV/elevação não fornecidos','rótulos superior/inferior são provisórios','mesmo objeto entre vistas ajuda consistência, mas não fornece geometria oculta ou câmera exata'],'aprovacao_modelo_anterior':'r05 orgânico rejeitado por silhueta e textura'}
    (folder/'manifesto.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for view,r in records.items():print(view,r['tamanho'],'bbox',r['bbox'])


if __name__=='__main__':main()
