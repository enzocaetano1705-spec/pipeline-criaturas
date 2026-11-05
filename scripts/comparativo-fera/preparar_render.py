"""Lê o resultado A só depois de a geometria B estar congelada; não cria autoria B."""
import hashlib
import json
import sys
import numpy as np
from criaturas import bbmodelo, render
from comum import BASE, gravar


def preparar():
    rev=sys.argv[1] if len(sys.argv)>1 else 'v1'
    bdir=BASE/('blender-'+rev)
    adir=BASE/('blockbench-'+rev)
    bfile=bdir/'geometria-autoria.json'
    b=json.loads(bfile.read_text(encoding='utf-8'))
    gravar(bdir/'autoria-congelada.json',{'sha256':hashlib.sha256(bfile.read_bytes()).hexdigest(),
           'fonte':'entrada comum; congelada antes de ler a geometria Blockbench para renderização'})
    a_path=next(adir.glob('*.bbmodel'))
    model=bbmodelo.ler(a_path)
    mats=bbmodelo.matrizes_ossos(model)
    patches=[]
    for c,face,points,n in render._quads(model,mats):
        uv=c.faces.get(face,{}).get('uv')
        if uv is None: continue
        patches.append({'name':c.nome,'face':face,'vertices':points.tolist(),'uv':uv,'normal':n.tolist()})
    gravar(adir/'render-malha.json',{'patches':patches,'origem':str(a_path),
           'fonte_sha256':hashlib.sha256(a_path.read_bytes()).hexdigest(),'resolucao':model.resolucao})
    # Representação de faces da autoria B para o seu próprio worker, sem bbmodel intermediário.
    patches=[]
    for c in b['cubos']:
        R=bbmodelo.matriz_rotacao(c['rotation'])
        O=np.array(c['origin'])
        lim=np.array([c['from'],c['to']])
        for face,corners in render.CANTOS_FACE.items():
            if face not in b['faces'][c['name']]: continue
            pts=np.array([[lim[i,0],lim[j,1],lim[k,2]] for i,j,k in corners])
            if np.linalg.norm(np.cross(pts[1]-pts[0],pts[2]-pts[0]))<1e-8:continue
            pts=(pts-O)@R.T+O
            patches.append({'name':c['name'],'bone':c['bone'],'face':face,'vertices':pts.tolist(),
                            'uv':b['faces'][c['name']][face]['uv'],'normal':(R@render.NORMAIS[face]).tolist()})
    gravar(bdir/'render-malha.json',{'patches':patches,'ossos':b['ossos'],'resolucao':[128,128],
           'autoria_sha256':hashlib.sha256(bfile.read_bytes()).hexdigest()})
    print('Malhas para o render comum preparadas; autoria B congelada antes da leitura A.')


if __name__=='__main__':preparar()
