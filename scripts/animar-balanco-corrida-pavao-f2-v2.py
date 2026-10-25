"""F2 corrida v2: corpo absorve/impulsiona cada passada, com inércia na coluna e cauda."""
import argparse
import copy
import importlib.util
import json
import math
import shutil
from pathlib import Path

import numpy as np
from criaturas import bbmodelo, motor

RAIZ=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('corrida_v1',RAIZ/'scripts/animar-corrida-pavao-f2.py')
base=importlib.util.module_from_spec(sp);sp.loader.exec_module(base)
v9=base.v9
v4=base.v4
FONTE=base.SAIDA
PASTA=FONTE.parent.parent/'corrida-v2'
SAIDA=PASTA/'criatura-pavao-e2-corrida-v2.bbmodel'
CLIPES=base.CLIPES
ALTERADOS=['run','run_start','run_stop']
PERIODO=base.PERIODO
RUN_DISTANCIA=base.RUN_DISTANCIA
misturar=base.misturar
BASE_Y=-1.9
AMP_Y=1.65


def alvo_pe(m,fase,lado):
    p,ang,apoio=base.alvo_pe(m,fase,lado)
    ph=(fase+(0 if lado=='left' else .5))%1
    if not apoio:
        u=(ph-base.APOIO)/(1-base.APOIO)
        p[1]-=1.2*math.sin(math.pi*u)**2
    return p,ang,apoio


def corrida(m,fase):
    fase%=1; a=2*math.pi*fase
    p=base.corrida(m,fase)
    # Apoio comprime, impulso abre a coluna; os segmentos respondem com atrasos diferentes.
    carga=math.cos(2*a-.55*math.pi)
    altura=math.cos(2*a-.8*math.pi)
    p['body']={'rotacao':[-18-3.2*carga,2.7*math.sin(a),2.8*math.sin(a)],
               'posicao':[.40*math.sin(a),BASE_Y-AMP_Y*altura,.42*math.sin(2*a-.85*math.pi)]}
    p['pelvis']['rotacao']=[-4+2.5*math.cos(2*a-.70*math.pi),3.5*math.sin(a-.28),.9*math.sin(a+.2)]
    p['waist']['rotacao']=[-7+1.8*math.cos(2*a-.40*math.pi),-2.1*math.sin(a-.2),-.7*math.sin(a-.25)]
    p['chest']['rotacao']=[-6-2.8*math.cos(2*a-.25*math.pi),-2.4*math.sin(a-.38),-math.sin(a-.35)]
    # Compensação parcial: cabeça continua olhando à frente, mas sente a passada.
    p['neck_1']['rotacao']=[24+2.8*math.cos(2*a-.45*math.pi),.6*math.sin(a-.1),.3*math.sin(a-.3)]
    p['head']['rotacao']=[11+.8*math.cos(2*a-.62*math.pi),-1.3*math.sin(a-.18),-.8*math.sin(a-.4)]
    p['tail_1']['rotacao']=[10+2.2*math.cos(2*a-.90*math.pi),-5.5*math.sin(a-.5),-2.2*math.sin(a-.4)]
    p['tail_2']['rotacao']=[1.4*math.sin(2*a-1.0),-1.7*math.sin(a-.9),0]
    for lado,s in [('left',1),('right',-1)]:
        p['arm_'+lado]['rotacao']=[10+4.0*s*math.sin(a-.2),0,s*(8+.9*math.cos(2*a-.3))]
        p['forearm_'+lado]['rotacao']=[-18-2.5*s*math.sin(a-.6),0,0]
    # Recalcula as pernas para o novo movimento do quadril, conservando a esteira dos pés.
    parent=bbmodelo.matrizes_ossos(m,p)['waist'];r=parent[:3,:3];o=m.ossos['body'].origem
    for lado in ['left','right']:
        alvo,ang,_=alvo_pe(m,fase,lado)
        rs=v4.perna(m,lado,v9.euler(r),parent[:3,3]-o+r@o,alvo,ang)
        for n,rr in zip(['leg_','shin_','foot_'],rs):p[n+lado]['rotacao']=rr
    return p


class Familia(base.Familia):
    def __init__(self,m):
        self.m=m
        self.walk=v9.v5.leitor_linear(m,'walk_blend')
        self.idle=v9.v5.leitor_linear(m,'idle_blend')

    def blend(self,fase,w):
        p=misturar(self.m,self.walk((fase%1)*1.2),corrida(self.m,fase),w)
        p['body']['posicao'][1]+=max(0,v4.CHAO-self.suporte(p))
        return p

    def pose(self,nome,t):
        if nome=='run':return corrida(self.m,t/PERIODO)
        if nome=='walk_blend':return self.walk(t)
        if nome=='idle_blend':return self.idle(t)
        return self.transicao(nome,t)


def preservados(m,novo):
    for campo in ['elements','textures','groups','outliner']:assert m.bruto[campo]==novo.bruto[campo],campo
    out=[]
    for a in m.animacoes:
        if a['name'] in ALTERADOS:continue
        b=copy.deepcopy(a)
        for c in b.get('animators',{}).values():c.setdefault('keyframes',[])
        assert b==next(c for c in novo.animacoes if c['uuid']==a['uuid']),a['name']
        out.append(a['name'])
    return out


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--medir',action='store_true');ap.add_argument('--refazer',action='store_true');args=ap.parse_args()
    m=bbmodelo.ler(FONTE);f=Familia(m);PASTA.mkdir(exist_ok=True)
    for ph in np.linspace(0,1,481):corrida(m,float(ph))
    if args.medir:
        sp=importlib.util.spec_from_file_location('r4',RAIZ/'scripts/revisar-combate-pavao-f2-v4.py')
        r=importlib.util.module_from_spec(sp);sp.loader.exec_module(r)
        med={n:r.medir(m,lambda t:f.pose(n,t),CLIPES[n],240) for n in ALTERADOS}
        (PASTA/'bloqueio-medidas.json').write_text(json.dumps(med,indent=2)+'\n',encoding='utf-8')
        for n,v in med.items():print(n,'piso',v['minimo_y_visivel'],'penas/pernas',v['nova_penetracao_pena_perna'])
        return
    sha=v9.sha;original=sha(FONTE);prov=PASTA/'proveniencia.json'
    if SAIDA.exists():
        old=json.loads(prov.read_text()) if prov.exists() else {}
        if not args.refazer or old.get('saida_sha256')!=sha(SAIDA) or old.get('fonte_sha256')!=original:raise SystemExit('Saída existente/editada preservada; criar outra versão.')
    ops=[{'op':'remove_animation','animation':n} for n in ALTERADOS]
    ops.extend(op for op in base.operacoes(m,f) if op.get('name',op.get('animation')) in ALTERADOS)
    (PASTA/'balanco.ops.json').write_text(json.dumps(ops,separators=(',',':'))+'\n',encoding='utf-8')
    shutil.copy2(FONTE,SAIDA);motor.editar(SAIDA,ops)
    novo=bbmodelo.ler(SAIDA);mantidos=preservados(m,novo);assert sha(FONTE)==original
    prov.write_text(json.dumps({'fonte':FONTE.relative_to(RAIZ).as_posix(),'fonte_sha256':original,'saida_sha256':sha(SAIDA),'operacoes':len(ops),'clipes_alterados':ALTERADOS,'clipes_preservados':mantidos,'rig_geometria_uv_atlas_preservados':True},indent=2)+'\n',encoding='utf-8')
    for nome in ['animacoes.json','locomocao.json']:shutil.copy2(FONTE.parent/nome,PASTA/nome)
    print('Corrida v2 criada com corpo articulado;',len(ops),'operações; preservados:',', '.join(mantidos))


if __name__=='__main__':main()
