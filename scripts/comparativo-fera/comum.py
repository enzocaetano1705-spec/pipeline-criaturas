"""Utilidades do ensaio; não contém a solução anatômica de nenhuma tentativa."""
from pathlib import Path
import json
import math
import numpy as np
from PIL import Image, ImageDraw

RAIZ = Path(__file__).resolve().parents[2]
BASE = RAIZ / 'modelos/fera-fera-agil-das-sombras/comparativo-v1'
ENTRADA = BASE / 'entrada'


def gravar(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def ler(nome):
    return json.loads((ENTRADA / nome).read_text(encoding='utf-8'))


def rot_segmento(a, b):
    d = np.array(b, float) - a
    length = float(np.linalg.norm(d))
    return [math.degrees(math.atan2(d[2], math.hypot(d[0], d[1]))), 0,
            math.degrees(math.atan2(-d[0], d[1]))], length


def recorte(tipo):
    return {
        'fur': [(0, .04), (.82, 0), (1, .3), (.76, .72), (.73, 1), (.47, .8), (.3, .98), (.21, .68), (0, .87)],
        'mane': [(.12, .15), (.64, 0), (1, .14), (.83, .55), (.95, .87), (.64, .76), (.53, 1), (.36, .78), (0, .94), (.16, .55)],
        'ribbon': [(0, 0), (.83, .02), (.7, .28), (1, .48), (.68, .54), (.97, .87), (.57, .78), (.3, 1), (.34, .75), (.08, .68)],
        'tabard': [(0, 0), (1, .04), (.91, .64), (.7, 1), (.53, .78), (.29, .96), (.14, .66)],
        'diamond': [(.5, 0), (1, .5), (.5, 1), (0, .5)],
    }.get(tipo)


def tile(cubo, face, size, paleta):
    """Somente cores de bloqueio/recortes para julgar geometria; pintura final adiada."""
    w, h = max(1, size[0]), max(1, size[1])
    role = cubo['role']
    rgb = paleta[role]
    im = Image.new('RGBA', (w, h), rgb)
    d = ImageDraw.Draw(im)
    cut = recorte(cubo.get('cut'))
    if cut:
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.polygon([(round(x * (w - 1)), round(y * (h - 1))) for x, y in cut], fill=rgb)
    if cubo['name'].startswith('tail_') and not cut:
        if face=='north':
            d.polygon([(0,0),(w,0),(w,h*.68),(w*.7,h*.52),(w*.42,h*.78),(0,h*.48)],fill=paleta['cream'])
        elif face in ('east','west'):
            d.polygon([(w*.65,0),(w,0),(w,h),(w*.7,h*.7),(w*.55,h*.34)],fill=paleta['cream'])
    if cubo['name'] in ('chest','ribcage') and face=='north':
        d.polygon([(w*.1,h*.05),(w*.9,h*.05),(w*.84,h*.66),(w*.65,h*.54),
                   (w*.54,h*.95),(w*.35,h*.7),(w*.22,h*.84),(w*.12,h*.53)],fill=paleta['cream'])
    if cubo.get('eye') and face in ('east', 'west', 'north'):
        # Olho estreito e máscara escura na cabeça; não acrescenta orelhas.
        d.polygon([(0,0),(w,0),(w,h*.64),(w*.7,h*.72),(w*.42,h*.57),(0,h*.77)],fill=paleta['cream'])
        d.polygon([(0,h*.12),(w*.88,h*.25),(w*.92,h*.52),(0,h*.4)],fill=paleta['shadow'])
        x0,y0=int(w*.25),int(h*.22)
        d.rectangle((x0,y0,max(x0,int(w*.56)),max(y0,int(h*.4))),fill=paleta['iris'])
        d.rectangle((int(w*.38),y0,int(w*.43),max(y0,int(h*.43))),fill=paleta['shadow'])
        d.line([(0,h*.1),(w*.9,h*.23)],fill=paleta['shadow'],width=max(1,h//8))
        if face=='north':
            # Duas órbitas no frontal; o perfil mantém um olho.
            d.rectangle((0,int(h*.25),max(0,w//3),int(h*.45)),fill=paleta['shadow'])
            d.rectangle((max(0,w-w//3-1),int(h*.25),w-1,int(h*.45)),fill=paleta['shadow'])
            d.point((max(0,w//4),int(h*.3)),fill=paleta['iris'])
            d.point((min(w-1,w-w//4-1),int(h*.3)),fill=paleta['iris'])
    return im


def atlas_face(cubos, paleta, lado=128):
    """Ilhas por face, 1 px/unidade; igual densidade visual entre autores."""
    atlas = Image.new('RGBA', (lado,lado), (0,0,0,0))
    faces = {}
    x = y = row = 0
    for c in cubos:
        dims=[abs(b-a) for a,b in zip(c['from'],c['to'])]
        dims=[max(1,round(v)) for v in dims]
        mapping={'north':(dims[0],dims[1]),'south':(dims[0],dims[1]),
                 'east':(dims[2],dims[1]),'west':(dims[2],dims[1]),
                 'up':(dims[0],dims[2]),'down':(dims[0],dims[2])}
        faces[c['name']]={}
        for face,(w,h) in mapping.items():
            # Um plano tem somente as duas faces que realmente existem.
            zero=next((i for i,v in enumerate(c['to']) if abs(v-c['from'][i])<1e-7),None)
            if zero is not None and face not in ({0:('east','west'),1:('up','down'),2:('north','south')}[zero]):
                continue
            if x+w+2>lado: x,y,row=0,y+row,0
            if y+h+2>lado: raise ValueError('Atlas de bloqueio excedido')
            atlas.paste(tile(c,face,(w,h),paleta),(x+1,y+1))
            faces[c['name']][face]={'uv':[x+1,y+1,x+1+w,y+1+h]}
            x+=w+2
            row=max(row,h+2)
    return atlas,faces
