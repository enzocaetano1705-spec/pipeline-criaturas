"""Cria proposta de ataque do F2 em cópia protegida; não altera a fonte manual nem idle/walk.

uv run python scripts/animar-ataque-pavao-f2.py [--refazer]
"""
import argparse
import copy
import hashlib
import json
import math
import shutil
from pathlib import Path

import numpy as np

from criaturas import bbmodelo, motor

RAIZ = Path(__file__).resolve().parents[1]
FONTE = RAIZ / "modelos/criatura-pavao/f2/criatura-pavao-e2.bbmodel"
PASTA = FONTE.parent / "ataque-v1"
SAIDA = PASTA / "criatura-pavao-e2-ataque-v1.bbmodel"
NOME, DURACAO, FPS = "attack_physical", 1.5, 60


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def curva(t, pontos):
    """Easing cosseno entre poses desenhadas; extremos sem overshoot."""
    if t <= pontos[0][0]:
        return float(pontos[0][1])
    for (a,x),(b,y) in zip(pontos,pontos[1:]):
        if t <= b:
            u=(t-a)/(b-a)
            return x+(y-x)*(.5-.5*math.cos(math.pi*u))
    return float(pontos[-1][1])


def euler(r):
    y=math.asin(float(np.clip(-r[2,0],-1,1)))
    x=math.atan2(r[2,1],r[2,2])
    z=math.atan2(r[1,0],r[0,0])
    return np.degrees([x,y,z])


def dobrar(v):
    return (v+math.pi)%(2*math.pi)-math.pi


def pe_alvo(t, lado, centro):
    p=centro.copy();inclinacao=0.
    if lado == "left":
        if .06 < t < .32:
            u=(t-.06)/.26
            p[2]-=1.25*(.5-.5*math.cos(math.pi*u))
            p[1]+=.75*math.sin(math.pi*u)
            inclinacao=-6*math.sin(math.pi*u)
        elif .32 <= t <= .94:
            p[2]-=1.25
        elif .94 < t < 1.32:
            u=(t-.94)/.38
            p[2]-=1.25*(.5+.5*math.cos(math.pi*u))
            p[1]+=.65*math.sin(math.pi*u)
            inclinacao=-5*math.sin(math.pi*u)
    return p,inclinacao


def perna_ik(m, lado, body_r, body_p, alvo, inclinacao):
    """IK analítica sagital de quadril/joelho/tornozelo, com dedo plantado no apoio."""
    hip=m.ossos[f"leg_{lado}"].origem
    knee=m.ossos[f"shin_{lado}"].origem
    ankle=m.ossos[f"foot_{lado}"].origem
    toe=m.cubo(f"toe_{lado}_1")
    dedo=(toe.de+toe.ate)/2
    vetor_dedo=dedo-ankle
    alvo_ankle=alvo-bbmodelo.matriz_rotacao([inclinacao,0,0])@vetor_dedo
    body=bbmodelo.matrizes_ossos(m,{"body":{"rotacao":body_r,"posicao":body_p}})["body"]
    alvo_local=bbmodelo.aplicar(np.linalg.inv(body),[alvo_ankle])[0]-hip
    a,b=(knee-hip)[1:],(ankle-knee)[1:]
    q=alvo_local[1:]
    l1,l2=np.linalg.norm(a),np.linalg.norm(b)
    cos_b=(q@q-l1*l1-l2*l2)/(2*l1*l2)
    if not -1.000001 <= cos_b <= 1.000001:
        raise ValueError(f"Pé {lado} fora do alcance do rig: cos={cos_b:.4f}")
    aa,ab=math.atan2(a[1],a[0]),math.atan2(b[1],b[0])
    repouso=dobrar(ab-aa)
    beta=math.copysign(math.acos(float(np.clip(cos_b,-1,1))),repouso)
    theta=math.atan2(q[1],q[0])-math.atan2(l2*math.sin(beta),l1+l2*math.cos(beta))
    quadril=math.degrees(dobrar(theta-aa))
    joelho=math.degrees(dobrar(beta-repouso))
    tornozelo=inclinacao-body_r[0]-quadril-joelho
    return quadril,joelho,tornozelo


def pose(m,t):
    antecipacao=[(0,0),(.12,1),(.30,2.5),(.38,2.5),(.52,-9),(.64,-12),(.72,-10),(.94,-2),(1.30,0),(1.5,0)]
    pitch=curva(t,antecipacao)
    body_r=[pitch,0,0]
    body_p=[0,curva(t,[(0,0),(.30,-.7),(.38,-.7),(.52,.65),(.64,.45),(.84,0),(1.20,0),(1.5,0)]),
            curva(t,[(0,0),(.30,.3),(.38,.3),(.52,-2.8),(.64,-3.2),(.74,-2.8),(.98,-.3),(1.32,0),(1.5,0)])]
    # Transferência de peso antes de flexionar a perna: mantém as penas longas fora do chão.
    for inicio,fim in [(.06,.32),(.94,1.32)]:
        if inicio < t < fim:
            body_p[1]+=.75*math.sin(math.pi*(t-inicio)/(fim-inicio))
    neck=curva(t,[(0,0),(.28,10),(.38,10),(.52,-10),(.64,-7),(.84,4),(1.25,0),(1.5,0)])
    p={"body":{"rotacao":body_r,"posicao":body_p},"neck_1":{"rotacao":[neck,0,0]},
       "head":{"rotacao":[-pitch-neck+curva(t,[(0,0),(.46,0),(.56,-3),(.74,0),(1.5,0)]),0,0]}}
    abrir=curva(t,[(0,0),(.28,1),(.40,1),(.52,.65),(.65,1),(.92,.4),(1.32,0),(1.5,0)])
    for lado,s in [("left",1),("right",-1)]:
        braco=curva(t,[(0,0),(.28,20),(.38,20),(.52,65),(.64,48),(.72,40),(.94,10),(1.32,0),(1.5,0)])
        antebraco=curva(t,[(0,0),(.28,52),(.38,52),(.52,-65),(.64,2),(.72,16),(.94,18),(1.32,0),(1.5,0)])
        arm_r=np.array([braco,8*s*abrir,-4*s*abrir])
        p[f"arm_{lado}"]={"rotacao":arm_r}
        p[f"forearm_{lado}"]={"rotacao":[antebraco,-s*curva(t,[(0,0),(.38,2),(.52,10),(.65,18),(.80,8),(1.32,0),(1.5,0)]),0]}
        # Penas compridas pertencem ao ombro; compensar o braço para não varrerem o chão.
        desejada=bbmodelo.matriz_rotacao([3*abrir,-s*5*abrir,s*2*abrir])
        p[f"wing_{lado}"]={"rotacao":euler(bbmodelo.matriz_rotacao(arm_r).T@desejada)}
        toe=m.cubo(f"toe_{lado}_1")
        alvo,angulo=pe_alvo(t,lado,(toe.de+toe.ate)/2)
        q,j,a=perna_ik(m,lado,body_r,body_p,alvo,angulo)
        for osso,valor in [(f"leg_{lado}",q),(f"shin_{lado}",j),(f"foot_{lado}",a)]:
            p[osso]={"rotacao":[valor,0,0]}
        atraso=max(0,t-.06)
        ondular=curva(atraso,[(0,0),(.30,3),(.45,-2),(.58,7),(.78,-3),(1.05,2),(1.38,0),(1.5,0)])
        for n in [1,2]:
            p[f"feather_{lado}_{n}"]={"rotacao":[ondular*(1 if n==1 else 1.35),s*.5*ondular,0]}
    p["tail_1"]={"rotacao":[-pitch,0,0]}
    for n in range(1,8):
        p[f"feather_fan_{n}"]={"rotacao":[-1.5*abrir,((n-4)/3)*3.5*abrir,0]}
    if t <= 1e-8 or t >= DURACAO-1e-8:
        p={n:{"rotacao":[0.,0.,0.]} for n in m.ossos}
        p["body"]["posicao"]=[0.,0.,0.]
    return p


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refazer',action='store_true')
    args=parser.parse_args()
    original=sha(FONTE);m=bbmodelo.ler(FONTE)
    if any('claw' in c.nome for c in m.cubos):
        raise SystemExit('A fonte ainda contém garras; confira o arquivo salvo pelo usuário.')
    if any(a['name']==NOME for a in m.animacoes):
        raise SystemExit('A fonte já tem attack_physical; criar nova versão da proposta.')
    proveniencia=PASTA/'proveniencia.json'
    if SAIDA.exists():
        anterior=json.loads(proveniencia.read_text(encoding='utf-8')) if proveniencia.exists() else {}
        if not args.refazer or anterior.get('saida_sha256') != sha(SAIDA) or anterior.get('fonte_sha256') != original:
            raise SystemExit('Saída já existe ou foi editada; preservada. Use outra versão.')
    PASTA.mkdir(exist_ok=True)
    ops=[{'op':'add_animation','name':NOME,'length':DURACAO,'loop':'once','snapping':FPS}]
    tempos=np.linspace(0,DURACAO,int(DURACAO*FPS)+1)
    poses=[pose(m,float(t)) for t in tempos]
    for osso in m.ossos:
        for canal,campo in [('rotation','rotacao'),('position','posicao')]:
            valores=[np.asarray(p.get(osso,{}).get(campo,[0,0,0]),float) for p in poses]
            if canal=='position' and osso!='body':
                continue
            indices=range(len(tempos)) if any(np.linalg.norm(v)>1e-7 for v in valores) else [0,len(tempos)-1]
            for i in indices:
                ops.append({'op':'set_keyframe','animation':NOME,'bone':osso,'channel':canal,
                            'time':round(float(tempos[i]),6),'value':valores[i].round(6).tolist(),'interpolation':'linear'})
    (PASTA/'ataque.ops.json').write_text(json.dumps(ops,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    shutil.copy2(FONTE,SAIDA)
    motor.editar(SAIDA,ops)
    alterado=bbmodelo.ler(SAIDA)
    assert alterado.bruto['elements']==m.bruto['elements'] and alterado.bruto['groups']==m.bruto['groups']
    assert alterado.bruto['textures']==m.bruto['textures']
    for a in m.animacoes:
        esperado=copy.deepcopy(a)
        # O codec normaliza animadores vazios; nenhuma chave ou curva existente pode mudar.
        for animador in esperado.get('animators',{}).values():
            animador.setdefault('keyframes',[])
        assert esperado==next(b for b in alterado.animacoes if b['uuid']==a['uuid'])
    assert sha(FONTE)==original
    proveniencia.write_text(json.dumps({'fonte':FONTE.relative_to(RAIZ).as_posix(),'fonte_sha256':original,
        'saida_sha256':sha(SAIDA),'animacao':NOME,'duracao':DURACAO,'fps':FPS,'operacoes':len(ops)},indent=2)+'\n',encoding='utf-8')
    (PASTA/'animacoes.json').write_text(json.dumps({NOME:{'HitFrame':.52,'CancelOpen':.94,'RecoveryStart':.74,
        'observacao':'Marcadores propostos para avaliação; ainda sem integração de dano no jogo.'}},indent=2)+'\n',encoding='utf-8')
    print(f'{SAIDA.relative_to(RAIZ)}: {NOME}, {DURACAO}s, {len(ops)-1} chaves, {len(m.cubos)} peças')
    print('Geometria, textura, rig, idle/walk e fonte manual preservados.')


if __name__=='__main__':
    main()
