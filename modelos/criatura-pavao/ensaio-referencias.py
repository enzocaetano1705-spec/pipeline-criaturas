"""Ensaio próprio: técnicas de planos e movimento aprendidas no estudo estrutural."""
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from criaturas import animar, bbmodelo, motor, referencias, render, texturizar

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT/'e1'/'criatura-pavao-e1.bbmodel'
DEST = ROOT/'estudo-referencias'
DEST.mkdir(exist_ok=True)
FILE = DEST/'pavao-planos-animado.bbmodel'
if FILE.exists():
    raise SystemExit('O ensaio já existe; preservar revisões. Use outro nome para refazer.')
shutil.copy2(SOURCE,FILE)
old = bbmodelo.ler(FILE)
operations = []
for c in old.cubos:
    if c.osso.startswith('feather_'):
        de,ate = c.de.tolist(),c.ate.tolist()
        de[2]=ate[2]=0
        operations.append({'op':'update_node','target':c.nome,'from':de,'to':ate})
for name in ('feather_left_1','feather_right_1'):
    operations.append({'op':'update_node','target':name,'rotation':[15,0,0]})
(DEST/'planos.ops.json').write_text(json.dumps({'operations':operations},indent=2),encoding='utf-8')
motor.editar(FILE,operations)
new = bbmodelo.ler(FILE)
old_cubes = {c.nome:c for c in old.cubos}
old_mats,new_mats = bbmodelo.matrizes_ossos(old),bbmodelo.matrizes_ossos(new)
source_tex = np.asarray(old.textura)
tex = np.zeros_like(source_tex)
mask = np.asarray(Image.open(ROOT/'e1/preparo/frente-mascara.png').convert('L'))>127
measures = json.loads((ROOT/'e1/medidas.json').read_text(encoding='utf-8'))
mapping = measures['mapeamento']['frente']
u = measures['unidades_por_celula']
for c in new.cubos:
    previous = old_cubes[c.nome]
    for side in ('north','south','east','west','up','down'):
        a=texturizar.texels_da_face(previous,side,bbmodelo.matriz_cubo(old,previous,old_mats))
        b=texturizar.texels_da_face(c,side,bbmodelo.matriz_cubo(new,c,new_mats))
        if a is None or b is None:
            continue
        old_uv,old_points=a
        new_uv,_=b
        if len(old_uv)!=len(new_uv):
            continue  # faces reduzidas a aresta não transportam área pintada
        for (su,sv),(du,dv),point in zip(old_uv,new_uv,old_points):
            color=source_tex[int(sv)%64,int(su)%64].copy()
            if c.osso.startswith('feather_') and side in ('north','south'):
                x,y,_=point
                col=int((mapping['centro']-x/u)*mask.shape[0]/32)
                row=int((32-y/u)*mask.shape[0]/32)
                if not (0<=row<mask.shape[0] and 0<=col<mask.shape[1] and mask[row,col]):
                    color[3]=0
            tex[int(dv)%64,int(du)%64]=color
Image.fromarray(tex).save(DEST/'textura.png')
texturizar.aplicar_no_modelo(FILE,tex,new,[])
result=animar.animar(FILE,'cabeça-corpo','inicial',('idle','walk','blink'))
errors,warnings,messages=animar.validar_animacoes(FILE)
summary=referencias.inspecionar(FILE)
summary['ensaio']={'clipes':result['clipes'],'avisos':result['avisos'],
                  'validacao_animacoes':{'erros':errors,'avisos':warnings,'mensagens':messages},
                  'origem_movimento':'Funções procedurais próprias assadas em chaves numéricas; sem chaves copiadas de terceiros.'}
(DEST/'estudo.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
assert errors==0,messages

# A prévia usa exatamente os valores assados pelo gerador, em enquadramento fixo.
model=bbmodelo.ler(FILE)
rig=animar.Rig.do_modelo(model)
clips,_=animar.clipes(rig,'cabeça-corpo','inicial',('idle','walk'))
lo,hi=bbmodelo.limites(model)
bounds=(lo-np.array([1,0,1]),hi+np.array([1,4,1]))
frames=[]
labels={'rotation':'rotacao','position':'posicao','scale':'escala'}
for clip in clips:
    baked=animar.assar(clip,model)
    count=len(next(iter(next(iter(baked.values())).values())))
    for i in range(count-1):
        pose={bone:{labels[channel]:keys[i][1] for channel,keys in channels.items()}
              for bone,channels in baked.items()}
        mats=bbmodelo.matrizes_ossos(model,pose)
        shot=render.renderizar(model,'3/4',escala=12,mats=mats,limites=bounds,fundo=(242,245,247))[0]
        frame=Image.new('RGB',(512,360),(242,245,247))
        frame.paste(shot,((512-shot.width)//2,35+(300-shot.height)//2))
        draw=ImageDraw.Draw(frame)
        draw.text((16,12),f'Pavao | {clip.nome} | 2 volumes + 6 planos',fill=(30,52,66))
        draw.text((16,340),'Movimento proprio, assado; rosto pintado, sem blink.',fill=(65,80,90))
        frames.append(frame)
frames[0].save(DEST/'previa-movimento.gif',save_all=True,append_images=frames[1:],duration=100,loop=0,disposal=2)
print(f'Ensaio: {summary["contagem"]}; clipes {list(result["clipes"])}; animacoes {errors} erros, {warnings} avisos.')
print(FILE)
print(DEST/'previa-movimento.gif')
