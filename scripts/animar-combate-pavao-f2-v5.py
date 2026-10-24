"""F2 v5: giro com impulso/torção e cauda articulada; pisão v4 protegido."""
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
spec=importlib.util.spec_from_file_location('combate_base_v4',RAIZ/'scripts/animar-combate-pavao-f2-v4.py')
v4=importlib.util.module_from_spec(spec);spec.loader.exec_module(v4)
FONTE=v4.SAIDA
PASTA=FONTE.parent.parent/'ataque-v5'
SAIDA=PASTA/'criatura-pavao-e2-ataque-v5.bbmodel'
FPS=120
CHAO=v4.CHAO
CLIPES={'attack_spin':1.65,'attack_tail_kick':1.85}
C=v4.C
sha=v4.base.v2.base.sha
euler=v4.base.v2.base.euler


def rot(x=0,y=0,z=0):return bbmodelo.matriz_rotacao([x,y,z])


def preparar_rig(m):
    ops=[]
    def grupo(n,p,o):
        m.ossos[n]=bbmodelo.Osso(n,'virtual_'+n,p,np.array(o,float),np.zeros(3))
        ops.append({'op':'add_group','name':n,'parent':p,'origin':list(o)})
    def pai(n,p):
        m.ossos[n].pai=p;ops.append({'op':'update_node','target':n,'parent':p})
    def mover(c,p):
        c.osso=p;ops.append({'op':'update_node','target':c.uuid,'parent':p})
    grupo('chest','body',[0,20.2,.5])
    for c in m.cubos:
        if c.nome in ['torso','shoulders']:mover(c,'chest')
    for n in ['neck_1','arm_left','arm_right']:pai(n,'chest')
    junta=v4.ponto_face(m,m.cubo('tail_base'))
    grupo('tail_2','tail_1',junta)
    mover(m.cubo('tail_base'),'tail_2')
    for n in list(m.ossos):
        if n.startswith('feather_fan_') and m.ossos[n].pai=='tail_1':pai(n,'tail_2')
    for lado in ['left','right']:
        for c in m.cubos:
            if not c.nome.startswith(f'wing_{lado}_feather_'):continue
            if c.tamanho[2]>24 and c.osso=='wing_'+lado:
                # Nomes não são simétricos: a pena direita 7 também é longa.
                n='elbow_blade_right_7'
                grupo(n,'forearm_right',v4.ponto_face(m,c));mover(c,n)
    # Eixo sobre a ponta de apoio esquerda; neutro nos outros clipes.
    toe=m.cubo('toe_left_1');o=[float((toe.de[0]+toe.ate[0])/2),0,float(toe.de[2])]
    m.ossos['combat_pivot'].origem=np.array(o)
    ops.append({'op':'update_node','target':'combat_pivot','origin':o})
    return ops


def neutra(m,br,bp):return v4.base_pose(m,br,bp,0,0)


def azimute(r):return math.degrees(math.atan2(r[0,2],r[2,2]))


def laminas_giro(m,p,w,t):
    """Toda a plumagem da asa orienta-se pelo membro que a sustenta."""
    for lado,s in [('left',1),('right',-1)]:
        mats=bbmodelo.matrizes_ossos(m,p)
        rp=mats['arm_'+lado][:3,:3]
        # Armas acompanham o peito e têm pequena defasagem no arco do ombro.
        yaw=azimute(mats['chest'][:3,:3])+C(t,[(0,0),(.36,-s*10),(.52,-s*5),(.74,s*5),(1.0,s*8),(1.65,0)])
        desejado=rot(y=yaw)@v4.orientacao_lamina(m,lado)
        p['forearm_'+lado]={'rotacao':euler(v4.misturar(np.eye(3),rp.T@desejado,w))}
    mats=bbmodelo.matrizes_ossos(m,p)
    for c in m.cubos:
        if not c.osso.startswith('tail_blade_'):continue
        o=m.ossos[c.osso];rp=mats[o.pai][:3,:3]
        n=bbmodelo.matriz_rotacao(c.rotacao)[:,0]
        flat=v4.base.v2.entre_vetores(n,np.array([0,1,0]))
        alvo=rot(y=azimute(rp))@flat
        p[o.nome]={'rotacao':euler(v4.misturar(np.eye(3),rp.T@alvo,w))}


def alvo_giro(m,t,lado):
    if lado=='left':
        ang=C(t,[(0,0),(.25,-3),(.42,-12),(.65,-17),(.88,-10),(1.04,0),(1.65,0)])
        return v4.apoio(m,lado,ang),ang
    ang=C(t,[(0,0),(.24,-3),(.40,-24),(.48,-20),(.70,-8),(.94,0),(1.65,0)])
    a=v4.apoio(m,lado,ang)
    a[0]+=C(t,[(0,0),(.20,0),(.42,-2),(.62,-2.3),(.80,-2),(.98,-1.5),(1.20,0),(1.65,0)])
    a[2]+=C(t,[(0,0),(.20,0),(.40,3),(.58,1.5),(.76,-1.5),(.98,-1),(1.20,0),(1.65,0)])
    a[1]+=C(t,[(0,0),(.41,0),(.55,2.8),(.76,2.3),(.94,0),(1.08,0),(1.15,.8),(1.24,0),(1.65,0)])
    return a,ang


def pose_giro(m,t):
    w=C(t,[(0,0),(.18,.18),(.42,1),(.92,1),(1.30,0),(1.65,0)])
    br=[C(t,[(0,0),(.22,-10),(.40,-26),(.56,-22),(.72,-27),(.90,-18),(1.02,-25),(1.28,-7),(1.65,0)]),
        C(t,[(0,0),(.28,-10),(.38,-10),(.49,14),(.64,4),(.80,-10),(.90,-4),(1.05,7),(1.30,-3),(1.65,0)]),
        C(t,[(0,0),(.24,-5),(.42,-8),(.58,3),(.76,7),(.92,3),(1.08,-4),(1.65,0)])]
    bp=[C(t,[(0,0),(.27,-2),(.42,-3),(.70,-2.8),(.92,-2.0),(1.20,-.5),(1.65,0)]),
        C(t,[(0,0),(.22,-1.7),(.40,-4.7),(.54,-3.8),(.72,-4.8),(.90,-4),(1.02,-4.9),(1.28,-1.5),(1.65,0)]),
        C(t,[(0,0),(.26,.8),(.42,0),(.65,-.8),(.90,-1.3),(1.10,-.6),(1.65,0)])]
    bp[1]+=2*w
    p=neutra(m,br,bp)
    p['chest']={'rotacao':[C(t,[(0,0),(.28,-6),(.42,2),(.60,-5),(.83,2),(1.02,7),(1.30,-3),(1.65,0)]),
        C(t,[(0,0),(.20,-10),(.36,-25),(.45,-16),(.55,12),(.72,14),(.90,5),(1.05,-8),(1.35,3),(1.65,0)]),
        C(t,[(0,0),(.38,-5),(.58,5),(.84,2),(1.05,-4),(1.65,0)])]}
    v4.colocar_pernas(m,p,{l:alvo_giro(m,t,l) for l in ['left','right']})
    for lado,s in [('left',1),('right',-1)]:
        p['arm_'+lado]={'rotacao':[C(t,[(0,0),(.35,7),(.52,18),(.72,5),(.90,12),(1.13,-6),(1.65,0)]),
            s*C(t,[(0,0),(.36,12),(.60,-8),(.90,6),(1.65,0)]),-s*(12+5*s)*w]}
    p['neck_1']={'rotacao':[C(t,[(0,0),(.25,6),(.40,21),(.62,15),(.85,19),(1.10,5),(1.65,0)]),
        C(t,[(0,0),(.28,15),(.40,20),(.50,-8),(.65,-15),(.83,10),(1.02,-5),(1.65,0)]),0]}
    p['head']={'rotacao':[C(t,[(0,0),(.40,6),(.62,2),(.90,-5),(1.65,0)]),0,0]}
    p['tail_1']={'rotacao':[-br[0]*.6,C(t,[(0,0),(.28,15),(.40,22),(.55,-12),(.70,-20),(.88,-5),(1.10,10),(1.65,0)]),0]}
    p['tail_2']={'rotacao':[C(t,[(0,0),(.42,4),(.65,-3),(1.0,4),(1.65,0)]),C(t,[(0,0),(.40,10),(.58,15),(.79,-12),(1.10,-7),(1.65,0)]),0]}
    v4.alinhar_penas_pernas(m,p,C(t,[(0,0),(.28,1),(1.40,1),(1.65,0)]))
    laminas_giro(m,p,w,t)
    yaw=C(t,[(0,0),(.12,-4),(.28,-18),(.38,-24),(.46,5),(.56,82),(.68,220),(.80,335),(.90,360),(.96,368),(1.10,360),(1.65,360)])
    p['combat_pivot']={'rotacao':[0,yaw,0]}
    return p


def cauda_apoio(m,t):
    phi=C(t,[(0,0),(.18,5),(.36,17),(.50,25),(.64,28),(.72,32),(.86,26),(1.04,17),(1.26,6),(1.85,0)])
    tau=C(t,[(0,0),(.20,6),(.36,21),(.50,25),(.72,20),(1.02,29),(1.26,12),(1.60,0),(1.85,0)])
    psi=C(t,[(0,0),(.20,-12),(.36,-49),(.50,-72.5),(.72,-74.5),(1.02,-68.5),(1.26,-30),(1.60,0),(1.85,0)])
    w=C(t,[(0,0),(.27,0),(.40,1),(1.10,1),(1.34,0),(1.85,0)])
    regular=np.array([0,C(t,[(0,0),(.24,-1),(.40,-3),(1.1,-3),(1.4,-.8),(1.85,0)]),
                      C(t,[(0,0),(.20,1.5),(.40,5),(1.04,6),(1.40,2),(1.85,0)])])
    p={'body':{'rotacao':[phi,0,0]},'tail_1':{'rotacao':[tau,0,0]},'tail_2':{'rotacao':[psi,0,0]}}
    mats=bbmodelo.matrizes_ossos(m,p)
    # Apoio na superfície sólida mais baixa da curva, nunca nas penas.
    partes=[m.cubo(n) for n in ['tail_mid','tail_base']]
    pts=np.concatenate([bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mats),bbmodelo.cantos(c)) for c in partes])
    contato=pts[np.argmin(pts[:,1])].copy();contato[0]=0
    # Altura usa o envelope sólido; o avanço usa a mesma junta material.
    # Trocar o ponto de Z pelo vértice mais baixo fazia a bacia saltar 6 unidades.
    contato[2]=bbmodelo.aplicar(mats['tail_1'],[m.ossos['tail_2'].origem])[0,2]
    braco=np.array([0,CHAO-contato[1],23-contato[2]])
    return phi,tau,psi,(1-w)*regular+w*braco,w


def alvo_cauda(m,t,lado,bp,phi):
    c=v4.centro_pe(m,lado);a=c.copy()
    if t<.42:
        ini,fim=(.04,.19) if lado=='right' else (.20,.35)
        a[2]+=C(t,[(0,0),(ini,0),(fim,3.5),(.42,3.5)])
        if ini<t<fim:a[1]+=.9*math.sin(math.pi*(t-ini)/(fim-ini))**2
        return a,0
    if t>1.08:
        ini,fim=(1.18,1.43) if lado=='right' else (1.40,1.67)
        a[2]+=C(t,[(1.08,3.5),(ini,3.5),(fim,0),(1.85,0)])
        if ini<t<fim:a[1]+=.9*math.sin(math.pi*(t-ini)/(fim-ini))**2
        return a,0
    b=m.ossos['body'].origem
    h=b+bp+rot(phi)@(m.ossos['leg_'+lado].origem-b)
    tuck=np.array([c[0],h[1]-6.5,h[2]-7.5])
    hit=np.array([math.copysign(4.2,c[0]),h[1]+1.8,h[2]-16.5])
    entrada=C(t,[(.42,0),(.56,1),(1.08,1)])
    golpe=C(t,[(.42,0),(.57,0),(.70,1),(.75,1),(.92,0),(1.08,0)])
    saida=C(t,[(.42,0),(.92,0),(1.08,1)])
    ancora=c+np.array([0,0,3.5])
    a=(1-entrada)*ancora+entrada*((1-golpe)*tuck+golpe*hit)
    a=(1-saida)*a+saida*ancora
    ang=C(t,[(.42,0),(.56,10),(.70,62),(.75,62),(.92,12),(1.08,0)])
    return a,ang


def pose_cauda(m,t):
    phi,tau,psi,bp,w=cauda_apoio(m,t)
    p=neutra(m,[phi,0,0],bp)
    p['chest']={'rotacao':[C(t,[(0,0),(.24,-5),(.44,-11),(.60,-7),(.72,5),(.84,-3),(1.04,-6),(1.40,3),(1.85,0)]),0,0]}
    p['neck_1']={'rotacao':[C(t,[(0,0),(.28,-9),(.52,-12),(.70,-20),(.88,-8),(1.25,3),(1.85,0)]),0,0]}
    p['head']={'rotacao':[C(t,[(0,0),(.40,-5),(.64,-4),(.75,-12),(.92,-2),(1.30,-3),(1.85,0)]),0,0]}
    v4.colocar_pernas(m,p,{l:alvo_cauda(m,t,l,bp,phi) for l in ['left','right']})
    p['tail_1']={'rotacao':[tau,0,0]};p['tail_2']={'rotacao':[psi,0,0]}
    # Um mesmo movimento para o leque inteiro conserva sua abertura e ângulos entre penas.
    leque=C(t,[(0,0),(.20,-8),(.39,-38),(.56,-46),(.75,-43),(1.08,-42),(1.40,-13),(1.70,0),(1.85,0)])
    for n in m.ossos:
        if n.startswith('tail_blade_'):p[n]={'rotacao':[leque,0,0]}
    v4.alinhar_penas_pernas(m,p,C(t,[(0,0),(.24,.8),(.40,1),(1.20,1),(1.60,0),(1.85,0)]))
    for lado,s in [('left',1),('right',-1)]:
        q=t
        ar=C(q,[(0,0),(.28,13),(.48,25),(.64,9),(.72,-7),(.86,12),(1.10,7),(1.45,-3),(1.85,0)])
        fore=C(q,[(0,0),(.28,-5),(.48,-18),(.64,-28),(.78,-5),(.94,-15),(1.40,3),(1.85,0)])
        p['arm_'+lado]={'rotacao':[ar,0,-s*7*w]};p['forearm_'+lado]={'rotacao':[fore,0,0]}
    return p


def pose(m,n,t):
    return {'attack_spin':pose_giro,'attack_tail_kick':pose_cauda}[n](m,float(t))


def medir(m):
    res={};superficies={c.uuid:v4.superficie_opaca(m,c) for c in m.cubos}
    for n,d in CLIPES.items():
        minimo=(100,None,None);erros=[]
        for t in np.linspace(0,d,int(round(d*FPS))+1):
            try:p=pose(m,n,float(t))
            except ValueError as e:erros.append((float(t),str(e)));continue
            mats=bbmodelo.matrizes_ossos(m,p)
            for c in m.cubos:
                y=float(bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mats),superficies[c.uuid])[:,1].min())
                if y<minimo[0]:minimo=(y,float(t),c.nome)
        res[n]={'minimo_y_visivel':minimo,'alcance_erros':erros}
    return res


def leitor_linear(m,nome):
    a=next(a for a in m.animacoes if a['name']==nome)
    nomes={o.uuid:n for n,o in m.ossos.items()};tr={}
    for uid,v in a['animators'].items():
        for k in v.get('keyframes',[]):
            assert k['interpolation']=='linear'
            tr.setdefault((nomes[uid],k['channel']),[]).append((k['time'],[float(k['data_points'][0][x]) for x in ['x','y','z']]))
    tr={k:sorted(v) for k,v in tr.items()}
    def fn(t):
        p={}
        for (n,c),vv in tr.items():
            tt,vs=zip(*vv);v=[np.interp(t,tt,[a[i] for a in vs]) for i in range(3)]
            p.setdefault(n,{})[{'rotation':'rotacao','position':'posicao'}[c]]=v
        return p
    return fn


def preservar_pisao(m,original,ops):
    """Compensa apenas a pena reparentada, conservando a pose aprovada no mundo."""
    fn=leitor_linear(original,'attack_stomp');osso='elbow_blade_right_7';o=m.ossos[osso].origem
    tt=np.linspace(0,1.25,151);rr=[];pp=[]
    for t in tt:
        p=fn(t);antes=bbmodelo.matrizes_ossos(original,p);depois=bbmodelo.matrizes_ossos(m,p)
        local=np.linalg.inv(depois['forearm_right'])@antes['wing_right'];r=local[:3,:3]
        rr.append(euler(r));pp.append(local[:3,3]-o+r@o)
    rr=v4.continuidade(rr)
    for canal,vv in [('rotation',rr),('position',pp)]:
        for t,v in zip(tt,vv):ops.append({'op':'set_keyframe','animation':'attack_stomp','bone':osso,'channel':canal,'time':round(float(t),6),'value':np.array(v).round(6).tolist(),'interpolation':'linear'})


def main():
    pa=argparse.ArgumentParser(description=__doc__);pa.add_argument('--medir',action='store_true');pa.add_argument('--refazer',action='store_true');a=pa.parse_args()
    original=sha(FONTE);m=bbmodelo.ler(FONTE);ops=preparar_rig(m);med=medir(m)
    if a.medir:
        for n,r in med.items():print(n,r['minimo_y_visivel'],'alcance',r['alcance_erros'][:4])
        return
    if any(r['alcance_erros'] or r['minimo_y_visivel'][0]<CHAO-.025 for r in med.values()):raise SystemExit('Revisar alcance/chão antes de gerar.')
    prov=PASTA/'proveniencia.json'
    if SAIDA.exists():
        velho=json.loads(prov.read_text()) if prov.exists() else {}
        if not a.refazer or velho.get('saida_sha256')!=sha(SAIDA) or velho.get('fonte_sha256')!=original:raise SystemExit('Saída existente/editada preservada; criar nova versão.')
    PASTA.mkdir(exist_ok=True)
    preservar_pisao(m,bbmodelo.ler(FONTE),ops)
    for nome,d in CLIPES.items():
        ops.extend([{'op':'remove_animation','animation':nome},{'op':'add_animation','name':nome,'length':d,'loop':'once','snapping':FPS}])
        tt=np.linspace(0,d,int(round(d*FPS))+1);ps=[pose(m,nome,float(t)) for t in tt]
        for n in m.ossos:
            for canal,campo in [('rotation','rotacao'),('position','posicao')]:
                if canal=='position' and n!='body':continue
                vv=np.array([p.get(n,{}).get(campo,[0,0,0]) for p in ps],float)
                if canal=='rotation' and n!='combat_pivot':vv=v4.continuidade(vv)
                inds=[0,len(tt)-1] if np.max(abs(vv-vv[0]))<1e-9 else range(len(tt))
                for i in inds:ops.append({'op':'set_keyframe','animation':nome,'bone':n,'channel':canal,'time':round(float(tt[i]),6),'value':vv[i].round(6).tolist(),'interpolation':'linear'})
    (PASTA/'combate.ops.json').write_text(json.dumps(ops,separators=(',',':'))+'\n',encoding='utf-8')
    shutil.copy2(FONTE,SAIDA);motor.editar(SAIDA,ops)
    novo=bbmodelo.ler(SAIDA);antes=bbmodelo.ler(FONTE)
    assert novo.bruto['elements']==antes.bruto['elements'] and novo.bruto['textures']==antes.bruto['textures']
    porid={c.uuid:c for c in novo.cubos}
    for c in antes.cubos:np.testing.assert_allclose(bbmodelo.caixa_mundo(antes,c),bbmodelo.caixa_mundo(novo,porid[c.uuid]),atol=1e-8)
    for a in antes.animacoes:
        if a['name'] in CLIPES:continue
        aa=copy.deepcopy(a)
        for v in aa.get('animators',{}).values():v.setdefault('keyframes',[])
        nv=copy.deepcopy(next(v for v in novo.animacoes if v['uuid']==a['uuid']))
        if a['name']=='attack_stomp':nv['animators'].pop(novo.ossos['elbow_blade_right_7'].uuid,None)
        assert aa==nv
    assert sha(FONTE)==original
    prov.write_text(json.dumps({'fonte':FONTE.relative_to(RAIZ).as_posix(),'fonte_sha256':original,'saida_sha256':sha(SAIDA),'clipes':CLIPES,'grupos':len(novo.ossos),'fps':FPS,'operacoes':len(ops),'pisao_preservado':True},indent=2)+'\n',encoding='utf-8')
    (PASTA/'medidas-planejadas.json').write_text(json.dumps(med,indent=2)+'\n',encoding='utf-8')
    marcadores=json.loads((FONTE.parent/'animacoes.json').read_text());marcadores.update(attack_spin={'HitFrame':.64,'RecoveryStart':.96,'CancelOpen':1.33},attack_tail_kick={'HitFrame':.70,'RecoveryStart':.92,'CancelOpen':1.43})
    (PASTA/'animacoes.json').write_text(json.dumps(marcadores,indent=2)+'\n',encoding='utf-8')
    print('Criada v5:',len(ops),'operações; pisão, idle e walk preservados nas chaves.')


if __name__=='__main__':main()
