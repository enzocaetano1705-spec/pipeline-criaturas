"""F2 v2: chutes baixos alternados e bicotada curta, feitos para encadear da mesma guarda.

uv run python scripts/animar-ataque-pavao-f2-v2.py [--medir | --refazer]
"""
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
spec=importlib.util.spec_from_file_location('ataque_base',RAIZ/'scripts/animar-ataque-pavao-f2.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
FONTE=base.FONTE
PASTA=FONTE.parent/'ataque-v2'
SAIDA=PASTA/'criatura-pavao-e2-ataque-v2.bbmodel'
FPS=120
CLIPES={'attack_physical':('left',.4),'attack_physical_right':('right',.4),
        'attack_peck':('peck',.3),'attack_chain_preview':('chain',1.1)}


def curva(u, pontos):
    return base.curva(u,pontos)


def geometria_pe(m,lado):
    origem=m.ossos['foot_'+lado].origem
    mats=bbmodelo.matrizes_ossos(m)
    return np.concatenate([bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mats),bbmodelo.cantos(c))-origem
                           for c in m.cubos if c.osso=='foot_'+lado])


def apoio(m,lado,angulo):
    """Ergue o calcanhar mantendo a ponta frontal no mesmo ponto do chão."""
    foot=m.ossos['foot_'+lado].origem
    toe=m.cubo('toe_'+lado+'_1')
    centro=(toe.de+toe.ate)/2
    rot=bbmodelo.matriz_rotacao([angulo,0,0])
    pontos=geometria_pe(m,lado)
    chao=min((geometria_pe(m,lado)+foot)[:,1])
    contato=np.array([centro[0],toe.de[1],toe.de[2]])
    origem=foot.copy()
    origem[1]=chao-(pontos@rot.T)[:,1].min()
    origem[2]=contato[2]-(rot@(contato-foot))[2]
    return origem+rot@(centro-foot)


def entre_vetores(a,b):
    a=a/np.linalg.norm(a);b=b/np.linalg.norm(b)
    v=np.cross(a,b);c=float(np.clip(a@b,-1,1))
    if c<-.999999:
        eixo=np.cross(a,np.eye(3)[int(np.argmin(abs(a)))]);eixo/=np.linalg.norm(eixo)
        return 2*np.outer(eixo,eixo)-np.eye(3)
    k=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
    return np.eye(3)+k+k@k/(1+c)


def ik(m,lado,body_r,body_p,alvo,angulo):
    """IK 3D com joelho na família da dobra original e pé orientado em mundo."""
    hip=m.ossos['leg_'+lado].origem;knee=m.ossos['shin_'+lado].origem;ankle=m.ossos['foot_'+lado].origem
    toe=m.cubo('toe_'+lado+'_1');centro=(toe.de+toe.ate)/2
    rot_pe=bbmodelo.matriz_rotacao([angulo,0,0])
    alvo_ankle=alvo-rot_pe@(centro-ankle)
    body=bbmodelo.matrizes_ossos(m,{'body':{'rotacao':body_r,'posicao':body_p}})['body']
    q=bbmodelo.aplicar(np.linalg.inv(body),[alvo_ankle])[0]-hip
    a,b=knee-hip,ankle-knee
    fixo=a[0]+b[0]
    aa,ab=math.atan2(a[2],a[1]),math.atan2(b[2],b[1])
    l1,l2=np.linalg.norm(a[1:]),np.linalg.norm(b[1:])
    c=(q@q-fixo*fixo-l1*l1-l2*l2)/(2*l1*l2)
    if abs(c)>1.000001:raise ValueError(f'{lado}: fora do alcance, cos={c:.3f}')
    repouso=base.dobrar(ab-aa)
    beta=math.copysign(math.acos(float(np.clip(c,-1,1))),repouso)
    j=base.dobrar(beta-repouso)
    shin=np.degrees([j,0,0]);rj=bbmodelo.matriz_rotacao(shin)
    rh=entre_vetores(a+rj@b,q)
    leg=base.euler(rh)
    parent=body[:3,:3]@rh@rj
    return leg,shin,base.euler(parent.T@rot_pe)


def pose(m,t,estilo,duracao):
    if estilo=='chain':
        if t<.4:return pose(m,t,'left',.4)
        if t<.7:return pose(m,t-.4,'peck',.3)
        return pose(m,min(.4,t-.7),'right',.4)
    u=float(np.clip(t/duracao,0,1))
    peck=estilo=='peck'
    if peck:
        impulso=curva(u,[(0,0),(.14,-.15),(.38,1),(.55,.15),(.76,-.1),(1,0)])
        bx=0;by=.35-.15*impulso;bz=-.8-2.5*impulso;pitch=-8-6*impulso
        neck=curva(u,[(0,6),(.14,14),(.38,-20),(.55,4),(.76,10),(1,6)])
        cabeca=-pitch-neck-10*max(0,impulso)
        heel=-8*max(0,impulso)
    else:
        impulso=curva(u,[(0,0),(.18,.08),(.36,1),(.56,.72),(.76,.25),(1,0)])
        s=1 if estilo=='left' else -1
        bx=s*3*curva(u,[(0,0),(.18,.8),(.3,1),(.65,1),(.86,.85),(1,0)])
        by=curva(u,[(0,.35),(.18,.6),(.36,.5),(.56,-.4),(.76,.8),(.86,1),(1,.35)])
        bz=curva(u,[(0,-.8),(.18,-1),(.36,-6),(.56,-4.6),(.76,-1.4),(1,-.8)])
        pitch=curva(u,[(0,-8),(.18,-5),(.36,-16),(.56,-10),(.76,-7),(1,-8)])
        neck=6;cabeca=-pitch-neck
        heel=curva(u,[(0,0),(.18,-8),(.36,-25),(.56,-15),(.76,-5),(1,0)])
    br=[pitch,0,0];bp=[bx,by,bz]
    p={'body':{'rotacao':br,'posicao':bp},'neck_1':{'rotacao':[neck,0,0]},'head':{'rotacao':[cabeca,0,0]}}
    for lado,s in [('left',1),('right',-1)]:
        atacando=not peck and lado==estilo
        toe=m.cubo('toe_'+lado+'_1');centro=(toe.de+toe.ate)/2
        if atacando:
            alvo=centro.copy()
            alvo[0]*=1-curva(u,[(0,0),(.18,.1),(.36,1),(.56,1),(.76,.4),(1,0)])
            alvo[1]+=curva(u,[(0,0),(.18,2.2),(.36,9),(.56,1.5),(.76,3.5),(1,0)])
            alvo[2]-=curva(u,[(0,0),(.18,2),(.36,18.4),(.56,12.6),(.76,3),(1,0)])
            angulo=curva(u,[(0,0),(.18,-12),(.36,-10),(.56,-8),(.76,-12),(1,0)])
        else:
            angulo=heel
            alvo=apoio(m,lado,angulo)
        leg,shin,foot=ik(m,lado,br,bp,alvo,angulo)
        p['leg_'+lado]={'rotacao':leg};p['shin_'+lado]={'rotacao':shin};p['foot_'+lado]={'rotacao':foot}
        # Braços de guarda. As penas herdam ombro E cotovelo, sem cancelamento da rotação.
        p['arm_'+lado]={'rotacao':[5+2*impulso,0,-s*2]}
        p['forearm_'+lado]={'rotacao':[3-impulso,0,0]}
        flex=1.2*math.sin(math.pi*u)**2*math.sin(2*math.pi*u-.4)
        p['wing_'+lado]={'rotacao':[flex,s*.5*flex,s*1.5*impulso]}
        for n in [1,2]:p[f'feather_{lado}_{n}']={'rotacao':[1.5*impulso*(1+.3*n),0,0]}
    p['tail_1']={'rotacao':[8+.5*(-pitch-8),-.5*bx,0]}
    for n in range(1,8):p['feather_fan_'+str(n)]={'rotacao':[-impulso,(n-4)*.35*impulso,0]}
    return p


def preparar_rig(m):
    ops=[]
    for lado in ['left','right']:
        ops.append({'op':'update_node','target':'wing_'+lado,'parent':'forearm_'+lado,
                    'origin':m.ossos['forearm_'+lado].origem.tolist()})
    return ops


def medir(m):
    saida={}
    for nome,(estilo,duracao) in CLIPES.items():
        minimo=(float('inf'),None,None);beak=[];pes=[]
        for t in np.linspace(0,duracao,int(duracao*120)+1):
            p=pose(m,float(t),estilo,duracao);mat=bbmodelo.matrizes_ossos(m,p)
            for c in m.cubos:
                lo,hi=bbmodelo.caixa_mundo(m,c,mat)
                if lo[1]<minimo[0]:minimo=(float(lo[1]),float(t),c.nome)
                if c.nome in ['beak','beak_tip']:beak.extend([lo.tolist(),hi.tolist()])
                if c.nome.startswith('toe_'):pes.extend([lo.tolist(),hi.tolist()])
        saida[nome]={'minimo':minimo,'bico_min':np.min(beak,axis=0).tolist(),'bico_max':np.max(beak,axis=0).tolist(),
                     'dedos_min':np.min(pes,axis=0).tolist(),'dedos_max':np.max(pes,axis=0).tolist(),'duracao':duracao}
    return saida


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--medir',action='store_true');parser.add_argument('--refazer',action='store_true')
    args=parser.parse_args();m=bbmodelo.ler(FONTE)
    # A medição usa a mesma hierarquia final, sem gravar ou mover geometria.
    for lado in ['left','right']:
        m.ossos['wing_'+lado].pai='forearm_'+lado
        m.ossos['wing_'+lado].origem=m.ossos['forearm_'+lado].origem.copy()
    medidas=medir(m)
    if args.medir:
        for n,r in medidas.items():print(n,r)
        return
    original=base.sha(FONTE);prov=PASTA/'proveniencia.json'
    if SAIDA.exists():
        anterior=json.loads(prov.read_text(encoding='utf-8')) if prov.exists() else {}
        if not args.refazer or anterior.get('saida_sha256')!=base.sha(SAIDA) or anterior.get('fonte_sha256')!=original:
            raise SystemExit('Proposta existente/editada preservada; criar nova versão.')
    if min(r['minimo'][0] for r in medidas.values()) < .0874-.05:
        raise SystemExit('Proposta cruza o chão; corrigir antes de gravar.')
    PASTA.mkdir(exist_ok=True)
    ops=preparar_rig(m)
    for nome,(estilo,duracao) in CLIPES.items():
        ops.append({'op':'add_animation','name':nome,'length':duracao,'loop':'loop' if estilo=='chain' else 'once','snapping':FPS})
        tempos=np.linspace(0,duracao,int(round(duracao*FPS))+1)
        poses=[pose(m,float(t),estilo,duracao) for t in tempos]
        for osso in m.ossos:
            for canal,campo in [('rotation','rotacao'),('position','posicao')]:
                if canal=='position' and osso!='body':continue
                vs=[np.array(p.get(osso,{}).get(campo,[0,0,0])) for p in poses]
                inds=[0,len(tempos)-1] if np.max(np.abs(np.array(vs)-vs[0]))<1e-9 else range(len(tempos))
                for i in inds:ops.append({'op':'set_keyframe','animation':nome,'bone':osso,'channel':canal,
                    'time':round(float(tempos[i]),6),'value':vs[i].round(6).tolist(),'interpolation':'linear'})
    (PASTA/'ataque.ops.json').write_text(json.dumps(ops,separators=(',',':'))+'\n',encoding='utf-8')
    shutil.copy2(FONTE,SAIDA);motor.editar(SAIDA,ops)
    novo=bbmodelo.ler(SAIDA);antes=bbmodelo.ler(FONTE)
    assert novo.bruto['elements']==antes.bruto['elements'] and novo.bruto['textures']==antes.bruto['textures']
    novos={c.uuid:c for c in novo.cubos}
    for c in antes.cubos:np.testing.assert_allclose(bbmodelo.caixa_mundo(antes,c),bbmodelo.caixa_mundo(novo,novos[c.uuid]))
    for a in antes.animacoes:
        esperado=copy.deepcopy(a)
        for animador in esperado.get('animators',{}).values():animador.setdefault('keyframes',[])
        assert esperado==next(b for b in novo.animacoes if b['uuid']==a['uuid'])
    assert base.sha(FONTE)==original
    prov.write_text(json.dumps({'fonte':FONTE.relative_to(RAIZ).as_posix(),'fonte_sha256':original,
        'saida_sha256':base.sha(SAIDA),'fps':FPS,'clipes':CLIPES,'operacoes':len(ops),'rig':'wing_* sob forearm_*, pivô no cotovelo'},indent=2)+'\n',encoding='utf-8')
    (PASTA/'medidas-planejadas.json').write_text(json.dumps(medidas,indent=2)+'\n',encoding='utf-8')
    marcadores={}
    for nome,(estilo,duracao) in CLIPES.items():
        if estilo=='chain':continue
        marcadores[nome]={'HitFrame':round(duracao*(.38 if estilo=='peck' else .36),3),
            'RecoveryStart':round(duracao*.6,3),'CancelOpen':round(duracao*.76,3),
            'observacao':'Proposta para avaliação. Chute acerta também no arco descendente; nenhum dano integrado ao jogo.'}
    (PASTA/'animacoes.json').write_text(json.dumps(marcadores,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{SAIDA.relative_to(RAIZ)}: {len(CLIPES)} clipes, {FPS} Hz, {len(ops)} operações')
    for n,r in medidas.items():print(n,'duração',r['duracao'],'mínimo Y',round(r['minimo'][0],4))


if __name__=='__main__':main()
