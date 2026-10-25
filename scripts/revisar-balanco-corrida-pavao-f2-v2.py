"""Confere corrida v2, continuidade e mudança efetiva na resposta do corpo."""
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image
from criaturas import bbmodelo, motor

RAIZ=Path(__file__).resolve().parents[1]
def carregar(nome,arquivo):
    s=importlib.util.spec_from_file_location(nome,RAIZ/'scripts'/arquivo)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
g=carregar('balanco_f2','animar-balanco-corrida-pavao-f2-v2.py')
r=carregar('revisor_corrida_v1','revisar-corrida-pavao-f2.py')
r.g=g
r.preservar=lambda m:g.preservados(bbmodelo.ler(g.FONTE),m)


def medidas_corpo(m,s):
    src=bbmodelo.ler(g.FONTE);old=g.v9.v5.leitor_linear(src,'run');out={}
    for n in ['body','pelvis','chest','neck_1','head','tail_1']:
        rows=[]
        for fn in [old,s.fn['run']]:
            xyz=[];pitch=[];yaw=[];roll=[]
            for t in np.linspace(0,g.PERIODO,241):
                mat=bbmodelo.matrizes_ossos(m,fn(float(t)))[n]
                xyz.append(bbmodelo.aplicar(mat,[m.ossos[n].origem])[0])
                e=g.v9.euler(mat[:3,:3]);pitch.append(e[0]);yaw.append(e[1]);roll.append(e[2])
            rows.append({'curso_pivo_xyz':np.ptp(xyz,axis=0).tolist(),'pitch_graus':float(np.ptp(pitch)),
                         'yaw_graus':float(np.ptp(yaw)),'roll_graus':float(np.ptp(roll))})
        out[n]={'v1':rows[0],'v2':rows[1]}
    assert out['body']['v2']['curso_pivo_xyz'][1]>out['body']['v1']['curso_pivo_xyz'][1]*1.4
    assert out['chest']['v2']['pitch_graus']>out['chest']['v1']['pitch_graus']*3
    assert out['head']['v2']['pitch_graus']>out['head']['v1']['pitch_graus']*2
    return out


def comparacao(m,s):
    old=g.v9.v5.leitor_linear(bbmodelo.ler(g.FONTE),'run');cur=s.fn['run']
    tt=np.arange(0,g.PERIODO,.02)
    bounds=lambda t:old(t) if t<=g.PERIODO else cur(t-g.PERIODO)
    proj=r.pv.projetor(m,bounds,np.linspace(0,2*g.PERIODO,73),'lado',384,300)
    frames=[]
    for t in tt:
        im=Image.new('RGB',(768,327),'white')
        im.paste(r.pv.quadro(m,old,t,proj,'v1 - anterior 1x'),(0,0))
        im.paste(r.pv.quadro(m,cur,t,proj,'v2 - corpo acompanha 1x'),(384,0));frames.append(im)
    frames[0].save(g.PASTA/'comparacao-v1-v2.gif',save_all=True,append_images=frames[1:],duration=20,loop=0)


def main():
    m=bbmodelo.ler(g.SAIDA);s=r.Salvo(m);rel=r.conferir(m,s)
    rel['resposta_corporal']=medidas_corpo(m,s)
    (g.PASTA/'medidas-corrida.json').write_text(json.dumps(rel,indent=2)+'\n',encoding='utf-8')
    for nome,fn,args in [('estrutura',motor.validar,dict(gates=['outliner','unlisted_nodes','degenerate'])),
                         ('locomocao',motor.validar_animacoes,dict(animations=g.ALTERADOS,sample_rate=120,ground_y=g.v4.CHAO,sink_tolerance=.025,detach_gap=1.0))]:
        vv=fn(g.SAIDA,**args);vv['fonte_sha256']=g.v9.sha(g.SAIDA)
        (g.PASTA/('validacao-'+nome+'.json')).write_text(json.dumps(vv,indent=2)+'\n',encoding='utf-8')
        err,warn,msg=motor.resumo_validacao(vv);print(nome,err,'erros',warn,'avisos',msg[:2]);assert err==0
    print('Piso/penas/apoios/loops/encaixes conferidos; preservados:',', '.join(rel['preservados']))
    print('Pitch peito:',rel['resposta_corporal']['chest']);print('Resposta cabeça:',rel['resposta_corporal']['head'])
    r.imagens(m,s);comparacao(m,s);print('Prévias a 1× e comparação v1/v2 geradas.')


if __name__=='__main__':main()
