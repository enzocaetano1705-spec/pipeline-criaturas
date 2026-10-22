"""Atlas original em pixel art para a versão de oito peças. Sem assets de terceiros."""
import json
import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from criaturas import bbmodelo, estado, relatorio, texturizar

root = Path(__file__).resolve().parent
dest = root / 'e1'
file = dest / 'criatura-pavao-e1.bbmodel'
palette = {'main':'#2cb8ae','light':'#53c9bb','shade':'#208f91',
           'deep':'#155e6c','navy':'#112f45','green':'#59aa88',
           'gold':'#e8a62f','cream':'#fff0c3','brown':'#54321b'}
rgb = {k:tuple(bytes.fromhex(v[1:])) for k,v in palette.items()}

model = bbmodelo.ler(file)
batch_path = dest / 'uv-sem-espelho.ops.json'
relatorio.gravar_json(batch_path, {'operations':[
    {'op':'update_node','target':c.nome,'mirror_uv':False} for c in model.cubos]})
subprocess.run(['uv','run','criaturas','aplicar','docs/criaturas/criatura-pavao',str(batch_path),
                '--motivo','UVs independentes para as duas penas e pintura original em pixels'],
               cwd=root.parent.parent,check=True)
plan = json.loads((dest/'plano-cubos.json').read_text(encoding='utf-8'))
for c in plan['cubos']:
    c['mirror_uv'] = False
relatorio.gravar_json(dest/'plano-cubos.json', plan, 'plano_cubos')
model = bbmodelo.ler(file)

# O rosto ocupa uma face de 16x11 texels, como parte da pintura do próprio corpo.
face = Image.new('RGBA',(16,11),rgb['main']+(255,))
draw = ImageDraw.Draw(face)
for xy,role in [((0,0,2,0),'light'),((12,0,15,1),'shade'),
                ((0,6,1,9),'shade'),((14,6,15,9),'shade'),
                ((2,9,5,10),'shade'),((11,9,13,10),'shade')]:
    draw.rectangle(xy,fill=rgb[role])
for x,y in [(2,1),(13,2),(1,5),(14,4),(3,9),(12,9)]:
    draw.point((x,y),fill=rgb['gold'])
eye = ['.DDD.','DHHAD','DBAAD','DBAAD','.DAA.']
symbols={'D':'navy','H':'cream','A':'gold','B':'brown'}
for offset in (2,9):
    for y,row in enumerate(eye):
        for x,symbol in enumerate(row):
            if symbol in symbols:
                draw.point((offset+x,2+y),fill=rgb[symbols[symbol]])
draw.point((7,0),fill=rgb['gold'])
draw.rectangle((7,1,8,2),fill=rgb['gold'])
draw.point((7,1),fill=rgb['cream'])
draw.point((8,3),fill=rgb['gold'])
draw.line([(1,7),(3,8),(6,9),(9,9),(12,8),(14,7)],fill=rgb['navy'],width=1)
for x,y in [(3,8),(5,9),(10,9),(12,8)]:
    draw.point((x,y),fill=rgb['cream'])
face_data = np.asarray(face)

tex = np.zeros((model.resolucao[1],model.resolucao[0],4),dtype=np.uint8)
mats = bbmodelo.matrizes_ossos(model)

def color_at(cube,side,p):
    x,y,z = (float(v) for v in p)
    if cube.osso == 'body':
        if side == 'north' and cube.nome == 'body_cube':
            col = int(np.clip(math.floor(8-x),0,15))
            row = int(np.clip(math.floor(13-y),0,10))
            return tuple(face_data[row,col])
        if cube.nome == 'body_cube_2':
            role='shade' if side in ('north','west','east') else 'main'
            if side == 'north' and y > 1:
                role='main'
        elif side == 'up':
            role='light'
        elif side == 'down':
            role='deep'
        else:
            # Grupos pequenos de pixels, em vez de ruído por texel.
            tile=(math.floor(x/2)*17+math.floor(y/2)*11+math.floor(z/2)*7)%19
            role='shade' if tile in (0,1,2,3) else 'main'
            if tile==6:
                role='light'
            if (round(x)*7+round(y)*11+round(z)*3)%61==0:
                role='gold'
        return rgb[role]+(255,)
    # Cada pena é pintada pela distância à raiz, espelhada em X sem compartilhar UV.
    t=abs(x)
    if cube.osso.endswith('_1'):
        role='deep' if (int(t)+int(y))%3==0 else 'shade'
        return rgb[role]+(255,)
    if cube.osso.endswith('_2'):
        role='deep' if int(t+y)%3==0 else 'main'
        if side == 'up':
            role='light'
        return rgb[role]+(255,)
    # Lâmina e ocelo: folha de cinco por quatro pixels, com ponta recortada.
    col=int(np.clip(math.floor(t-7),0,4))
    row=int(np.clip(math.floor(15-y),0,3))
    pattern=['TTGG.','TDNGG','.DNNG','..GGG']
    symbol=pattern[row][col]
    if symbol=='.':
        return (0,0,0,0)
    return rgb[{'T':'main','G':'green','D':'deep','N':'navy'}[symbol]]+(255,)

for c in model.cubos:
    matrix=bbmodelo.matriz_cubo(model,c,mats)
    for side in ('north','south','east','west','up','down'):
        result=texturizar.texels_da_face(c,side,matrix)
        if result is None:
            continue
        uv,points=result
        for (u,v),point in zip(uv,points):
            tex[int(v)%tex.shape[0],int(u)%tex.shape[1]]=color_at(c,side,point)

Image.fromarray(tex).save(dest/'textura.png')
Image.fromarray(texturizar.versao_roblox(tex)).save(dest/'textura-roblox.png')
texturizar.aplicar_no_modelo(file,tex,model,[])
relatorio.registrar(dest,'criatura-pavao','e1','texturizar',True,
    resumo={'estilo':'pixel art original; oito peças e rosto pintado',
            'paleta_base':[palette[k] for k in ('main','navy','green','brown','gold','cream')],
            'rampa_turquesa':[palette[k] for k in ('light','main','shade','deep')],
            'resolucao':list(model.resolucao)},
    arquivos=[str(dest/'textura.png')],hashes=estado.depois_de_escrever(dest,file))
estado.historico(dest,'ia','Pintura original em pixels: rosto, pelo e ocelos das duas penas')
print('Atlas 64x64: rosto pintado, penas simétricas com UVs próprios; oito peças mantidas.')
