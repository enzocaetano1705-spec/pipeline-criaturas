"""F2 v3: bote baixo com patas sincronizadas e ação do corpo inteiro.

uv run python scripts/animar-bote-pavao-f2-v3.py [--medir | --refazer]
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
spec=importlib.util.spec_from_file_location('ataque_v2',RAIZ/'scripts/animar-ataque-pavao-f2-v2.py')
v2=importlib.util.module_from_spec(spec);spec.loader.exec_module(v2)
FONTE=v2.FONTE
PASTA=FONTE.parent/'ataque-v3'
SAIDA=PASTA/'criatura-pavao-e2-ataque-v3.bbmodel'
NOME='attack_physical'
DURACAO=1.2
FPS=120
SAIDA_MIN=.08741
DECOLAGEM=.32
POUSO=.80


def curva(t,pontos):
    """Hermite monótona: preserva velocidade nos marcos intermediários do gesto."""
    ts=np.array([p[0] for p in pontos]);vs=np.array([p[1] for p in pontos],float)
    if t<=ts[0]:return float(vs[0])
    if t>=ts[-1]:return float(vs[-1])
    ds=np.diff(vs)/np.diff(ts);slopes=np.zeros(len(ts))
    for k in range(1,len(ts)-1):
        if ds[k-1]*ds[k]>0:
            h0,h1=ts[k]-ts[k-1],ts[k+1]-ts[k]
            w0,w1=2*h1+h0,h1+2*h0
            slopes[k]=(w0+w1)/(w0/ds[k-1]+w1/ds[k])
    i=int(np.searchsorted(ts,t)-1);h=ts[i+1]-ts[i];u=(t-ts[i])/h
    return float((2*u**3-3*u**2+1)*vs[i]+(u**3-2*u**2+u)*h*slopes[i]
                 +(-2*u**3+3*u**2)*vs[i+1]+(u**3-u**2)*h*slopes[i+1])


def preparar_rig(m):
    ops=v2.preparar_rig(m)
    for lado in ['left','right']:
        m.ossos['wing_'+lado].pai='forearm_'+lado
        m.ossos['wing_'+lado].origem=m.ossos['forearm_'+lado].origem.copy()
        nome='leg_plumage_'+lado;pivo=m.ossos['shin_'+lado].origem.copy()
        m.ossos[nome]=bbmodelo.Osso(nome,'virtual_'+nome,'leg_'+lado,pivo,np.zeros(3))
        ops.append({'op':'add_group','name':nome,'parent':'leg_'+lado,'origin':pivo.tolist()})
        for c in m.cubos:
            if c.nome.startswith('leg_'+lado+'_feather_'):
                c.osso=nome;ops.append({'op':'update_node','target':c.uuid,'parent':nome})
    return ops


def alvo_pe(m,t,lado):
    """Dois pés compartilham os tempos e o arco; conservam a assimetria da geometria."""
    ang=curva(t,[(0,0),(.16,0),(.24,-8),(.32,-25),(.43,-48),(.51,-38),(.59,-28),(.66,-12),(.73,-7),(.80,0),(1.2,0)])
    toe=m.cubo('toe_'+lado+'_1');centro=(toe.de+toe.ate)/2
    if t<=DECOLAGEM:return v2.apoio(m,lado,ang),ang,True
    if t>=POUSO:return centro.copy(),ang,True
    saida=v2.apoio(m,lado,-25);alvo=centro.copy()
    convergir=curva(t,[(.32,0),(.43,.3),(.51,1),(.59,1),(.66,.7),(.73,.2),(.80,0)])
    alvo[0]*=1-.46*convergir
    alvo[1]=curva(t,[(.32,saida[1]),(.43,7.5),(.49,8),(.56,5.5),(.60,2.8),(.67,3.6),(.73,2.9),(.80,centro[1])])
    alvo[2]-=curva(t,[(.32,centro[2]-saida[2]),(.43,2.5),(.51,9),(.59,12),(.66,8),(.73,2.5),(.80,0)])
    return alvo,ang,False


def ik(m,lado,br,bp,alvo,angulo):
    """Dois segmentos com polo anatômico: o joelho mantém o lado anterior da ave."""
    hip=m.ossos['leg_'+lado].origem;knee=m.ossos['shin_'+lado].origem;ankle=m.ossos['foot_'+lado].origem
    toe=m.cubo('toe_'+lado+'_1');centro=(toe.de+toe.ate)/2
    rp=bbmodelo.matriz_rotacao([angulo,0,0])
    body=bbmodelo.matrizes_ossos(m,{'body':{'rotacao':br,'posicao':bp}})['body']
    q=bbmodelo.aplicar(np.linalg.inv(body),[alvo-rp@(centro-ankle)])[0]-hip
    a,b=knee-hip,ankle-knee;l1,l2=np.linalg.norm(a[1:]),np.linalg.norm(b[1:])
    c=(q@q-(a[0]+b[0])**2-l1*l1-l2*l2)/(2*l1*l2)
    if abs(c)>1.000001:raise ValueError(f'{lado}: pé fora do alcance ({c:.3f})')
    rest=v2.base.dobrar(math.atan2(b[2],b[1])-math.atan2(a[2],a[1]))
    j=v2.base.dobrar(math.copysign(math.acos(float(np.clip(c,-1,1))),rest)-rest)
    shin=np.degrees([j,0,0]);rj=bbmodelo.matriz_rotacao(shin)
    rh=v2.entre_vetores(a+rj@b,q)
    # A rotação mais curta sozinha pode torcer a perna 180 graus durante o recolhimento.
    # O polo usa a dobra original e mantém a orientação da face anterior do joelho.
    eixo=q/np.linalg.norm(q)
    # Mantém o plano de flexão da perna. Um polo anterior fixo troca de lado
    # quando o pé é recolhido acima/à frente do quadril, torcendo a coxa.
    desejado=np.cross(-np.cross(a,b),eixo)
    atual=rh@a;atual-=eixo*(atual@eixo)
    atual/=np.linalg.norm(atual);desejado/=np.linalg.norm(desejado)
    giro=math.atan2(eixo@np.cross(atual,desejado),float(atual@desejado))
    x,y,z=eixo;k=np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
    rh=(np.eye(3)+math.sin(giro)*k+(1-math.cos(giro))*(k@k))@rh
    return v2.base.euler(rh),shin,v2.base.euler((body[:3,:3]@rh@rj).T@rp)


def pose(m,t):
    pitch=curva(t,[(0,0),(.10,-5),(.24,-20),(.32,-24),(.44,-30),(.57,-35),(.64,-28),(.80,-14),(.88,-10),(1.08,-2),(1.2,0)])
    by=curva(t,[(0,0),(.12,-.5),(.24,-3.5),(.32,-.2),(.44,5.2),(.50,4.6),(.60,1),(.73,-1),(.80,-3.2),(.87,-3.8),(.98,-1.3),(1.2,0)])
    bz=curva(t,[(0,0),(.24,-1),(.32,-2),(.44,-5.5),(.57,-8),(.64,-7),(.73,-2),(.80,-.8),(.90,-.3),(1.2,0)])
    br=[pitch,0,0];bp=[0,by,bz]
    neck=curva(t,[(0,0),(.09,-12),(.24,-8),(.36,16),(.48,26),(.59,32),(.67,18),(.80,8),(1.05,2),(1.2,0)])
    olhar=curva(t,[(0,0),(.09,-16),(.24,-18),(.44,-50),(.59,-62),(.68,-35),(.80,-12),(1.08,-4),(1.2,0)])
    p={'body':{'rotacao':br,'posicao':bp},'neck_1':{'rotacao':[neck,0,0]},
       'head':{'rotacao':[olhar-pitch-neck,0,0]}}
    ombro=curva(t,[(0,0),(.24,8),(.36,22),(.46,28),(.59,32),(.67,12),(.80,6),(.92,10),(1.2,0)])
    cotovelo=curva(t,[(0,0),(.24,14),(.36,-5),(.47,-8),(.59,-20),(.67,6),(.80,6),(.94,3),(1.2,0)])
    abrir=curva(t,[(0,0),(.22,8),(.35,21),(.46,18),(.59,-8),(.68,-4),(.80,9),(.94,3),(1.2,0)])
    lag=max(0,t-.055)
    flex=curva(lag,[(0,0),(.24,-5),(.40,5),(.56,-4),(.68,5),(.82,-6),(1.02,3),(1.145,0)])
    for lado,s in [('left',1),('right',-1)]:
        alvo,ang,_=alvo_pe(m,t,lado)
        leg,shin,foot=ik(m,lado,br,bp,alvo,ang)
        p['leg_'+lado]={'rotacao':leg};p['shin_'+lado]={'rotacao':shin};p['foot_'+lado]={'rotacao':foot}
        p['leg_plumage_'+lado]={'rotacao':[curva(t,[(0,0),(.24,-55),(.40,-15),(.58,-8),(.68,-43),(.73,-55),(.80,-45),(.90,-50),(1.2,0)]),0,0]}
        p['arm_'+lado]={'rotacao':[ombro,s*3*abrir/21,-s*abrir]}
        p['forearm_'+lado]={'rotacao':[cotovelo,-s*curva(t,[(0,0),(.40,8),(.59,22),(.67,8),(.86,3),(1.2,0)]),0]}
        # Abre o manto no salto, liberando a silhueta das patas. A base segue o cotovelo.
        manto=curva(t,[(0,0),(.24,4),(.38,17),(.48,22),(.59,12),(.70,6),(.84,5),(1.2,0)])
        p['wing_'+lado]={'rotacao':[flex-manto,-s*.35*flex,s*.65*abrir]}
        for n in [1,2]:p[f'feather_{lado}_{n}']={'rotacao':[flex*(1+.25*n),0,0]}
    tail=curva(t,[(0,0),(.24,14),(.38,24),(.53,30),(.63,18),(.80,7),(.91,-4),(1.06,-2),(1.2,0)])
    p['tail_1']={'rotacao':[tail,0,0]}
    leque=curva(t,[(0,0),(.24,.4),(.39,1),(.59,.8),(.70,.3),(.83,.6),(1.02,.1),(1.2,0)])
    for n in range(1,8):p[f'feather_fan_{n}']={'rotacao':[-2*leque,(n-4)*3*leque,0]}
    if t<=0 or t>=DURACAO:
        p={n:{'rotacao':[0,0,0]} for n in m.ossos};p['body']['posicao']=[0,0,0]
    return p


def medir(m):
    minimo=(float('inf'),None,None);picos={n:0. for n in m.ossos};erros=[]
    for t in np.linspace(0,DURACAO,int(DURACAO*FPS)+1):
        try:p=pose(m,float(t))
        except ValueError as e:erros.append((round(float(t),4),str(e)));continue
        mats=bbmodelo.matrizes_ossos(m,p)
        for c in m.cubos:
            y=float(bbmodelo.caixa_mundo(m,c,mats)[0][1])
            if y<minimo[0]:minimo=(y,float(t),c.nome)
        for n,v in p.items():picos[n]=max(picos[n],float(np.linalg.norm(v.get('rotacao',[0,0,0]))))
    return {'minimo_y':minimo,'fora_alcance':erros,'amplitudes':picos}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--medir',action='store_true');parser.add_argument('--refazer',action='store_true')
    args=parser.parse_args();original=v2.base.sha(FONTE)
    m=bbmodelo.ler(FONTE);ops=preparar_rig(m);medidas=medir(m)
    if args.medir:
        print('Mínimo Y:',medidas['minimo_y']);print('Fora do alcance:',medidas['fora_alcance'][:8]);return
    if medidas['fora_alcance'] or medidas['minimo_y'][0]<SAIDA_MIN-.02:
        raise SystemExit('Corrigir alcance/chão antes de gerar a proposta.')
    assert v2.base.sha(FONTE)==original,'a fonte mudou durante o preparo; executar de novo'
    prov=PASTA/'proveniencia.json'
    if SAIDA.exists():
        anterior=json.loads(prov.read_text(encoding='utf-8')) if prov.exists() else {}
        if not args.refazer or anterior.get('saida_sha256')!=v2.base.sha(SAIDA) or anterior.get('fonte_sha256')!=original:
            raise SystemExit('Proposta existente/editada preservada; criar outra versão.')
    PASTA.mkdir(exist_ok=True)
    ops.append({'op':'add_animation','name':NOME,'length':DURACAO,'loop':'once','snapping':FPS})
    tempos=np.linspace(0,DURACAO,int(round(DURACAO*FPS))+1);poses=[pose(m,float(t)) for t in tempos]
    for osso in m.ossos:
        for canal,campo in [('rotation','rotacao'),('position','posicao')]:
            if canal=='position' and osso!='body':continue
            vs=np.array([p.get(osso,{}).get(campo,[0,0,0]) for p in poses],float)
            inds=[0,len(tempos)-1] if np.max(abs(vs-vs[0]))<1e-9 else range(len(tempos))
            for i in inds:ops.append({'op':'set_keyframe','animation':NOME,'bone':osso,'channel':canal,
                'time':round(float(tempos[i]),6),'value':vs[i].round(6).tolist(),'interpolation':'linear'})
    (PASTA/'ataque.ops.json').write_text(json.dumps(ops,separators=(',',':'))+'\n',encoding='utf-8')
    shutil.copy2(FONTE,SAIDA)
    assert v2.base.sha(SAIDA)==original,'a cópia não coincide com a fonte medida'
    motor.editar(SAIDA,ops)
    novo=bbmodelo.ler(SAIDA);antes=bbmodelo.ler(FONTE)
    assert novo.bruto['elements']==antes.bruto['elements'] and novo.bruto['textures']==antes.bruto['textures']
    novos={c.uuid:c for c in novo.cubos}
    for c in antes.cubos:np.testing.assert_allclose(bbmodelo.caixa_mundo(antes,c),bbmodelo.caixa_mundo(novo,novos[c.uuid]),atol=1e-9)
    for a in antes.animacoes:
        esperado=copy.deepcopy(a)
        for b in esperado.get('animators',{}).values():b.setdefault('keyframes',[])
        assert esperado==next(b for b in novo.animacoes if b['uuid']==a['uuid'])
    assert v2.base.sha(FONTE)==original
    prov.write_text(json.dumps({'fonte':FONTE.relative_to(RAIZ).as_posix(),'fonte_sha256':original,
        'saida_sha256':v2.base.sha(SAIDA),'fps':FPS,'animacao':NOME,'duracao':DURACAO,'operacoes':len(ops),
        'rig':'penas de cotovelo sob forearm_*; dois grupos neutros para acomodação das penas das pernas'},indent=2)+'\n',encoding='utf-8')
    (PASTA/'medidas-planejadas.json').write_text(json.dumps(medidas,indent=2)+'\n',encoding='utf-8')
    (PASTA/'animacoes.json').write_text(json.dumps({NOME:{'HitFrame':.59,'RecoveryStart':.67,'CancelOpen':.92,
        'observacao':'Proposta: contato no arco descendente das duas patas. Sem dano ou deslocamento de gameplay integrado.'}},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{SAIDA.relative_to(RAIZ)}: {DURACAO}s, {len(ops)} operações, {len(novo.ossos)} grupos')
    print('Fonte, geometria, textura e chaves originais de idle/walk preservadas.')


if __name__=='__main__':main()
