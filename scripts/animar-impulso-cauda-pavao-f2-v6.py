"""F2 v6: carga elástica da cauda, salto e golpe à altura do peito base."""
import argparse
import copy
import importlib.util
import json
import shutil
from pathlib import Path

import numpy as np
from criaturas import bbmodelo, motor

RAIZ=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('base_v5',RAIZ/'scripts/animar-combate-pavao-f2-v5.py')
v5=importlib.util.module_from_spec(s);s.loader.exec_module(v5)
FONTE=v5.SAIDA
PASTA=FONTE.parent.parent/'ataque-v6'
SAIDA=PASTA/'criatura-pavao-e2-ataque-v6.bbmodel'
NOME='attack_tail_kick'
DURACAO=2.10
FPS=120
CHAO=v5.CHAO
SAI=.70
POUSA=1.12
C=v5.C
sha=v5.sha
euler=v5.euler


def preparar_rig(m):
    ops=[]
    def grupo(n,p,o):
        m.ossos[n]=bbmodelo.Osso(n,'virtual_'+n,p,np.array(o,float),np.zeros(3))
        ops.append({'op':'add_group','name':n,'parent':p,'origin':list(o)})
    def pai(n,p):
        m.ossos[n].pai=p;ops.append({'op':'update_node','target':n,'parent':p})
    def mover(c,p):
        c.osso=p;ops.append({'op':'update_node','target':c.uuid,'parent':p})
    grupo('pelvis','body',m.ossos['body'].origem)
    c=m.cubo('TorsoHips');base=(c.de+c.ate)/2;base[1]=c.de[1]
    junta=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,bbmodelo.matrizes_ossos(m)),[base])[0]
    grupo('waist','pelvis',junta)
    mover(m.cubo('hips'),'pelvis');mover(c,'waist')
    pai('tail_1','pelvis')
    for n in ['leg_left','leg_right']:pai(n,'waist')
    pai('chest','waist')
    return ops


def angulos(t):
    p=C(t,[(0,0),(.20,5),(.38,19),(.54,27),(.72,27),(.84,-4),(1.0,-9),(1.12,-10),(1.24,-8),(1.50,-4),(2.10,0)])
    if t<=.54:
        a=C(t,[(0,0),(.20,8),(.38,50),(.54,75)])
        b=C(t,[(0,0),(.20,-6),(.38,-15),(.54,-15)])
    elif t<=SAI:
        a=hermite(75,50,0,-345.4622,t-.54,SAI-.54)
        b=hermite(-15,10,0,361.9793,t-.54,SAI-.54)
    elif t<=.82:
        a=hermite(50,18,-345.4622,0,t-SAI,.82-SAI)
        b=hermite(10,-2,361.9793,0,t-SAI,.82-SAI)
    else:
        a=C(t,[(.82,18),(1.00,4),(1.20,0),(2.10,0)])
        b=C(t,[(.82,-2),(1.00,-10),(1.20,0),(2.10,0)])
    return p,a,b


def tronco(m,t,aereo=True):
    p,a,b=angulos(t)
    if aereo:
        dobra=C(t,[(0,0),(SAI,0),(.77,1),(.95,1),(POUSA,0),(DURACAO,0)])
        a-=10*dobra;b-=20*dobra
    pose={n:{'rotacao':[0,0,0]} for n in m.ossos}
    pose['pelvis']={'rotacao':[p,0,0]}
    pose['waist']={'rotacao':[C(t,[(0,0),(.28,-4),(.44,-9),(.54,-13),(.68,-5),(.84,8),(1.02,4),(1.12,-6),(1.35,2),(2.10,0)]),0,0]}
    pose['chest']={'rotacao':[C(t,[(0,0),(.28,-2),(.50,-8),(.64,-4),(.78,-3),(.86,3),(.98,-5),(1.13,8),(1.35,-3),(2.10,0)]),0,0]}
    pose['tail_1']={'rotacao':[a-p,0,0]};pose['tail_2']={'rotacao':[b-a,0,0]}
    return pose


def apoio_cauda(m,t):
    pose=tronco(m,t,False);mats=bbmodelo.matrizes_ossos(m,pose)
    pts=np.concatenate([bbmodelo.aplicar(bbmodelo.matriz_cubo(m,m.cubo(n),mats),bbmodelo.cantos(m.cubo(n))) for n in ['tail_mid','tail_base']])
    minimo=float(pts[:,1].min())
    ponta=v5.v4.contato_cauda(m)
    z=bbmodelo.aplicar(mats['tail_2'],[ponta])[0,2]
    ancora=float(ponta[2]-1)
    return np.array([0,CHAO-minimo,ancora-z])


def hermite(a,b,va,vb,t,d):
    u=float(np.clip(t/d,0,1));return (2*u**3-3*u**2+1)*a+(u**3-2*u**2+u)*d*va+(-2*u**3+3*u**2)*b+(u**3-u**2)*d*vb


_cinematica={}
def cinematica(m):
    k=id(m)
    if k not in _cinematica:
        dt=.0001;a=apoio_cauda(m,SAI)
        vel=(25*a-48*apoio_cauda(m,SAI-dt)+36*apoio_cauda(m,SAI-2*dt)-16*apoio_cauda(m,SAI-3*dt)+3*apoio_cauda(m,SAI-4*dt))/(12*dt)
        tempo=POUSA-SAI;fim=np.array([0,-4.2,a[2]+vel[2]*tempo])
        grav=2*(a[1]+vel[1]*tempo-fim[1])/(tempo*tempo)
        _cinematica[k]=(a,vel,fim,grav)
    return _cinematica[k]


def corpo(m,t):
    a,v,fim,grav=cinematica(m)
    if t<=SAI:
        w=C(t,[(0,0),(.26,0),(.40,1),(SAI,1)])
        regular=np.array([0,C(t,[(0,0),(.20,-.7),(.40,-2),(SAI,-2)]),C(t,[(0,0),(.20,.8),(.40,2.8),(SAI,2.8)])])
        return (1-w)*regular+w*apoio_cauda(m,t)
    if t<=POUSA:
        u=t-SAI;return a+v*u+np.array([0,-.5*grav*u*u,0])
    parada=fim[2]+v[2]*.07
    if t<1.26:
        u=t-POUSA
        y=hermite(fim[1],-5.8,v[1]-grav*(POUSA-SAI),0,u,.14)
        z=hermite(fim[2],parada,v[2],0,u,.14)
        return np.array([0,y,z])
    return np.array([0,C(t,[(1.26,-5.8),(1.50,-1.5),(1.80,-.3),(2.10,0)]),
                     C(t,[(1.26,parada),(1.32,parada),(1.64,parada*.45),(1.96,0),(2.10,0)])])


def altura_peito(m):
    c=m.cubo('torso');return float(bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,bbmodelo.matrizes_ossos(m)),[(c.de+c.ate)/2])[0,1])


def alvo_pe(m,t,lado,bp,p,parent):
    c=v5.v4.centro_pe(m,lado);a=c.copy();landing=cinematica(m)[2][2]
    if t<.43:
        ini,fim=(.04,.18) if lado=='right' else (.20,.35)
        a[2]+=C(t,[(0,0),(ini,0),(fim,2.8),(.43,2.8)])
        if ini<t<fim:a[1]+=.85*np.sin(np.pi*(t-ini)/(fim-ini))**2
        return a,0
    if t>=POUSA:
        ini,fim=(1.38,1.64) if lado=='right' else (1.66,1.96)
        a[2]+=C(t,[(POUSA,landing),(ini,landing),(fim,0),(DURACAO,0)])
        if ini<t<fim:a[1]+=1.1*np.sin(np.pi*(t-ini)/(fim-ini))**2
        return a,0
    h=bbmodelo.aplicar(parent,[m.ossos['leg_'+lado].origem])[0]
    tuck=np.array([c[0],h[1]-6.5,h[2]-7.5])
    hit=np.array([np.copysign(4.2,c[0]),altura_peito(m),h[2]-16.8])
    entrada=C(t,[(.43,0),(.55,1),(POUSA,1)])
    golpe=C(t,[(.43,0),(.60,0),(.70,.3),(.82,1),(.88,1),(1.00,0),(POUSA,0)])
    saida=C(t,[(.43,0),(1.00,0),(POUSA,1)])
    inicio=c+[0,0,2.8];destino=c+[0,0,landing]
    a=(1-entrada)*inicio+entrada*((1-golpe)*tuck+golpe*hit)
    a=(1-saida)*a+saida*destino
    ang=C(t,[(.43,0),(.55,10),(.70,30),(.82,68),(.88,68),(1.00,12),(POUSA,0)])
    return a,ang


def pose(m,t):
    t=float(t);p,_,_=angulos(t);bp=corpo(m,t);out=tronco(m,t)
    out['body']={'rotacao':[0,0,0],'posicao':bp.tolist()}
    parent=bbmodelo.matrizes_ossos(m,out)['waist'];r=parent[:3,:3];o=m.ossos['body'].origem
    br=euler(r);pos_equivalente=parent[:3,3]-o+r@o
    for lado in ['left','right']:
        alvo,ang=alvo_pe(m,t,lado,bp,p,parent)
        r1,r2,r3=v5.v4.perna(m,lado,br,pos_equivalente,alvo,ang)
        for n,r in [('leg_',r1),('shin_',r2),('foot_',r3)]:out[n+lado]={'rotacao':r}
    out['neck_1']={'rotacao':[C(t,[(0,0),(.26,-7),(.50,-9),(.65,2),(.80,-5),(.90,-12),(1.12,3),(1.28,-6),(1.55,2),(2.10,0)]),0,0]}
    out['head']={'rotacao':[C(t,[(0,0),(.30,-3),(.54,-6),(.70,-1),(.86,-5),(1.0,2),(1.18,-9),(1.50,0),(2.10,0)]),0,0]}
    for lado,sinal in [('left',1),('right',-1)]:
        ar=C(t,[(0,0),(.25,13),(.48,23),(.56,29),(.69,13),(.82,-12),(.90,-6),(1.02,14),(1.18,23),(1.45,-5),(2.10,0)])
        fr=C(t,[(0,0),(.25,-8),(.50,-19),(.62,-25),(.82,-2),(.98,-11),(1.16,-22),(1.40,3),(2.10,0)])
        out['arm_'+lado]={'rotacao':[ar,0,-sinal*C(t,[(0,0),(.40,8),(.70,10),(.85,6),(1.20,12),(1.60,0),(2.10,0)])]}
        out['forearm_'+lado]={'rotacao':[fr,0,0]}
    leque=C(t,[(0,0),(.25,-8),(.40,-48),(.54,-54),(.68,-63),(.82,-43),(1.00,-30),(1.30,-30),(1.65,-8),(1.95,0),(2.10,0)])
    for n in m.ossos:
        if n.startswith('tail_blade_'):out[n]={'rotacao':[leque,0,0]}
    v5.v4.alinhar_penas_pernas(m,out,C(t,[(0,0),(.26,1),(1.65,1),(1.95,0),(2.10,0)]))
    return out


def medir(m):
    superficies={c.uuid:v5.v4.superficie_opaca(m,c) for c in m.cubos};minimo=(100,None,None);erros=[]
    for t in np.linspace(0,DURACAO,int(round(DURACAO*FPS))+1):
        try:po=pose(m,t)
        except ValueError as e:erros.append((float(t),str(e)));continue
        mats=bbmodelo.matrizes_ossos(m,po)
        for c in m.cubos:
            y=float(bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mats),superficies[c.uuid])[:,1].min())
            if y<minimo[0]:minimo=(y,float(t),c.nome)
    a,v,f,grav=cinematica(m)
    return {'minimo_y_visivel':minimo,'alcance_erros':erros,'lancamento_pos':a.tolist(),'lancamento_vel':v.tolist(),
            'pouso_pos':f.tolist(),'gravidade_visual':grav,'altura_peito_base':altura_peito(m)}


def main():
    pa=argparse.ArgumentParser(description=__doc__);pa.add_argument('--medir',action='store_true');pa.add_argument('--refazer',action='store_true');args=pa.parse_args()
    original=sha(FONTE);m=bbmodelo.ler(FONTE);ops=preparar_rig(m);med=medir(m)
    if args.medir:
        for k,v in med.items():print(k,v if k!='alcance_erros' else v[:6])
        return
    if med['alcance_erros'] or med['minimo_y_visivel'][0]<CHAO-.025:raise SystemExit('Revisar alcance/chão antes de gerar.')
    prov=PASTA/'proveniencia.json'
    if SAIDA.exists():
        velho=json.loads(prov.read_text()) if prov.exists() else {}
        if not args.refazer or velho.get('saida_sha256')!=sha(SAIDA) or velho.get('fonte_sha256')!=original:raise SystemExit('Saída editada/existente preservada; criar versão nova.')
    PASTA.mkdir(exist_ok=True)
    ops.extend([{'op':'remove_animation','animation':NOME},{'op':'add_animation','name':NOME,'length':DURACAO,'loop':'once','snapping':FPS}])
    tt=np.linspace(0,DURACAO,int(round(DURACAO*FPS))+1);pp=[pose(m,t) for t in tt]
    for n in m.ossos:
        for canal,campo in [('rotation','rotacao'),('position','posicao')]:
            if canal=='position' and n!='body':continue
            vv=np.array([p.get(n,{}).get(campo,[0,0,0]) for p in pp],float)
            if canal=='rotation':vv=v5.v4.continuidade(vv)
            inds=[0,len(tt)-1] if np.max(abs(vv-vv[0]))<1e-9 else range(len(tt))
            for i in inds:ops.append({'op':'set_keyframe','animation':NOME,'bone':n,'channel':canal,'time':round(float(tt[i]),6),'value':vv[i].round(6).tolist(),'interpolation':'linear'})
    (PASTA/'impulso.ops.json').write_text(json.dumps(ops,separators=(',',':'))+'\n',encoding='utf-8')
    shutil.copy2(FONTE,SAIDA);motor.editar(SAIDA,ops)
    novo=bbmodelo.ler(SAIDA);antes=bbmodelo.ler(FONTE)
    assert novo.bruto['elements']==antes.bruto['elements'] and novo.bruto['textures']==antes.bruto['textures']
    porid={c.uuid:c for c in novo.cubos}
    for c in antes.cubos:np.testing.assert_allclose(bbmodelo.caixa_mundo(antes,c),bbmodelo.caixa_mundo(novo,porid[c.uuid]),atol=1e-8)
    for a in antes.animacoes:
        if a['name']==NOME:continue
        aa=copy.deepcopy(a)
        for v in aa.get('animators',{}).values():v.setdefault('keyframes',[])
        assert aa==next(v for v in novo.animacoes if v['uuid']==a['uuid'])
    assert sha(FONTE)==original
    prov.write_text(json.dumps({'fonte':FONTE.relative_to(RAIZ).as_posix(),'fonte_sha256':original,'saida_sha256':sha(SAIDA),'grupos':len(novo.ossos),'fps':FPS,'operacoes':len(ops),'pisao_spin_preservados':True},indent=2)+'\n',encoding='utf-8')
    (PASTA/'medidas-planejadas.json').write_text(json.dumps(med,indent=2)+'\n',encoding='utf-8')
    marc=json.loads((FONTE.parent/'animacoes.json').read_text());marc[NOME]={'HitFrame':.82,'RecoveryStart':1.00,'CancelOpen':1.50}
    (PASTA/'animacoes.json').write_text(json.dumps(marc,indent=2)+'\n',encoding='utf-8')
    print('Criada v6: impulso elástico; pisão/spin preservados;',len(ops),'operações.')


if __name__=='__main__':main()
