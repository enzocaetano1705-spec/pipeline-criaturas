"""Mede e renderiza a proposta de ataque já gravada, lendo suas chaves reais."""
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from criaturas import bbmodelo, render

RAIZ=Path(__file__).resolve().parents[1]
PASTA=RAIZ/'modelos/criatura-pavao/f2/ataque-v1'
ARQUIVO=PASTA/'criatura-pavao-e2-ataque-v1.bbmodel'


def main():
    spec=importlib.util.spec_from_file_location('ataque_f2',RAIZ/'scripts/animar-ataque-pavao-f2.py')
    criador=importlib.util.module_from_spec(spec);spec.loader.exec_module(criador)
    m=bbmodelo.ler(ARQUIVO)
    a=next(a for a in m.animacoes if a['name']=='attack_physical')
    trilhas={}
    nomes={b.uuid:n for n,b in m.ossos.items()}
    for uid,animador in a['animators'].items():
        canais={}
        for k in animador.get('keyframes',[]):
            v=k['data_points'][0]
            canais.setdefault(k['channel'],[]).append((k['time'],[float(v[x]) for x in ['x','y','z']]))
        trilhas[nomes[uid]]={canal:sorted(vals) for canal,vals in canais.items()}
    def pose(t):
        p={}
        for osso,canais in trilhas.items():
            for canal,vals in canais.items():
                tt,vv=zip(*vals)
                vetor=np.array([np.interp(t,tt,[v[i] for v in vv]) for i in range(3)])
                p.setdefault(osso,{})[{'rotation':'rotacao','position':'posicao','scale':'escala'}[canal]]=vetor
        return p
    menores=[];maiores=[];erros=[];minimo=(float('inf'),None,None)
    for t in np.linspace(0,1.5,181):
        p=pose(float(t));mats=bbmodelo.matrizes_ossos(m,p)
        lo,hi=bbmodelo.limites(m,mats);menores.append(lo);maiores.append(hi)
        for c in m.cubos:
            y=float(bbmodelo.caixa_mundo(m,c,mats)[0][1])
            if y<minimo[0]:minimo=(y,float(t),c.nome)
        for lado in ['left','right']:
            d=m.cubo('toe_'+lado+'_1');centro=(d.de+d.ate)/2
            esperado,_=criador.pe_alvo(t,lado,centro)
            atual=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,d,mats),[centro])[0]
            apoio=lado=='right' or t<=.06 or .32<=t<=.94 or t>=1.32
            if apoio:erros.append(float(np.linalg.norm(atual-esperado)))
    limites=np.min(menores,axis=0),np.max(maiores,axis=0)
    rel={'amostras':181,'fps_medicao':120,'minimo_y':minimo,'erro_pe_apoio_max_unidades':max(erros),
         'duracao':a['length'],'loop':a['loop'],'chaves':sum(len(v) for c in trilhas.values() for v in c.values()),
         'alvos':list(trilhas),'sem_escala':all('scale' not in c for c in trilhas.values())}
    (PASTA/'medidas-ataque.json').write_text(json.dumps(rel,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # Interpolação entre chaves a 60 Hz: tolerância menor que 1/25 de uma unidade/texel da arte.
    assert max(erros)<.04,'deslize excessivo no apoio'
    assert minimo[0]>=.0874-.02,'geometria abaixo do chão'
    def quadro(t,largura=384,altura=320):
        mats=bbmodelo.matrizes_ossos(m,pose(t))
        im,_,_,_=render.renderizar(m,'3/4',escala=4.4,margem=8,mats=mats,limites=limites)
        im.thumbnail((largura-12,altura-35))
        cel=Image.new('RGB',(largura,altura),(248,249,252))
        cel.paste(im,((largura-im.width)//2,28+(altura-35-im.height)//2))
        d=ImageDraw.Draw(cel)
        fase='prepara' if t<.4 else 'bote' if t<.57 else 'fecha' if t<.74 else 'recupera'
        if t==0 or t>=1.49:fase='repouso'
        d.text((10,8),f'{t:.2f}s - {fase}',fill=(25,35,40))
        return cel
    tempos=[0,.32,.52,.64,.94,1.5]
    folha=Image.new('RGB',(768,448),(248,249,252))
    for i,t in enumerate(tempos):folha.paste(quadro(t,256,224),(i%3*256,i//3*224))
    folha.save(PASTA/'poses-ataque.png')
    frames=[quadro(float(t)) for t in np.linspace(0,1.5,37)]
    frames[0].save(PASTA/'previa-ataque.gif',save_all=True,append_images=frames[1:],duration=[42]*36+[450],loop=0)
    print('Medição: apoio máximo',round(max(erros),6),'unidades; mínimo Y',round(minimo[0],6))
    print('Gravados: medidas-ataque.json, poses-ataque.png (768x448), previa-ataque.gif (384x320).')


if __name__=='__main__':
    main()
