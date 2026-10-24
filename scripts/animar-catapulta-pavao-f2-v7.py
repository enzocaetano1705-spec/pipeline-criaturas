"""F2 v7: cauda com curvatura distribuída, transferência de peso e catapulta."""
import argparse
import copy
import importlib.util
import json
import shutil
from pathlib import Path

import numpy as np
from criaturas import bbmodelo, motor

RAIZ=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('impulso_v6',RAIZ/'scripts/animar-impulso-cauda-pavao-f2-v6.py')
v6=importlib.util.module_from_spec(s);s.loader.exec_module(v6)
v5=v6.v5
FONTE=v6.SAIDA
PASTA=FONTE.parent.parent/'ataque-v7'
SAIDA=PASTA/'criatura-pavao-e2-ataque-v7.bbmodel'
NOME=v6.NOME
DURACAO=2.70
FPS=120
CHAO=v6.CHAO
SOLTA_PES=.38
CARGA=.62
SAI=.82
POUSA=1.60
C=v6.C
sha=v6.sha
euler=v6.euler
hermite=v6.hermite
CAUDA=['tail_1','tail_mid_flex_2','tail_mid_flex_3','tail_2','tail_base_flex_2','tail_base_flex_3']
PARTES=['tail_mid','tail_mid_2','tail_mid_3','tail_base','tail_base_2','tail_base_3']


def faces_fatia(c,a,b):
    """Recorta UV pela mesma fração longitudinal da geometria; não repinta o atlas."""
    faces=copy.deepcopy(c.faces)
    for n,f in faces.items():
        assert not f.get('rotation',0)
        u,v,uu,vv=f['uv'];du=uu-u;dv=vv-v
        if n=='east':f['uv']=[u+du*(1-b),v,u+du*(1-a),vv]
        elif n=='west':f['uv']=[u+du*a,v,u+du*b,vv]
        elif n in ['up','down']:f['uv']=[u,v+dv*a,uu,v+dv*b]
    return faces


def preparar_rig(m):
    """Somente subdivide dois sólidos existentes; juntas neutras nos clipes aprovados."""
    ops=[];rest=bbmodelo.matrizes_ossos(m)
    for nome in ['tail_mid','tail_base']:
        c=m.cubo(nome);rc=bbmodelo.matriz_cubo(m,c,rest);pai=c.osso
        ops.append({'op':'remove_node','target':c.uuid});m.cubos.remove(c)
        for i in range(3):
            a,b=i/3,(i+1)/3;novo=copy.deepcopy(c)
            novo.nome=nome if i==0 else f'{nome}_{i+1}'
            novo.uuid='virtual_'+novo.nome
            novo.de[2]=c.de[2]+c.tamanho[2]*a;novo.ate[2]=c.de[2]+c.tamanho[2]*b
            if i:
                # Dorsal: face interna sobrepõe durante a flexão, sem abrir fendas externas.
                ponto=(c.de+c.ate)/2;ponto[1]=c.ate[1];ponto[2]=novo.de[2]
                n=f'{nome}_flex_{i+1}';o=bbmodelo.aplicar(rc,[ponto])[0]
                m.ossos[n]=bbmodelo.Osso(n,'virtual_'+n,pai,o,np.zeros(3))
                ops.append({'op':'add_group','name':n,'parent':pai,'origin':o.tolist()});pai=n
            novo.osso=pai;novo.faces=faces_fatia(c,a,b);m.cubos.append(novo)
            ops.append({'op':'add_cube','name':novo.nome,'parent':pai,'from':novo.de.tolist(),'to':novo.ate.tolist(),
                        'origin':novo.origem.tolist(),'rotation':novo.rotacao.tolist(),'box_uv':False,'faces':novo.faces})
        if nome=='tail_mid':
            m.ossos['tail_2'].pai=pai;ops.append({'op':'update_node','target':'tail_2','parent':pai})
        else:
            for n in list(m.ossos):
                if n.startswith('feather_fan_') and m.ossos[n].pai=='tail_2':
                    m.ossos[n].pai=pai;ops.append({'op':'update_node','target':n,'parent':pai})
    return ops


def parametros(t):
    """Ângulos das tangentes absolutas, incluindo a inclinação original dos cubos."""
    repouso=np.array([15,15,15,12.5,12.5,12.5])
    toca=np.array([32,43,54,65,76,87])
    carga=np.array([50,74,98,122,146,166])
    solta=np.array([48,68,88,108,128,148])
    if t<=.34:
        ang=repouso+(toca-repouso)*C(t,[(0,0),(.10,0),(.34,1)])
    elif t<=CARGA:
        ang=toca+(carga-toca)*C(t,[(.34,0),(CARGA,1)])
    elif t<=SAI:
        ang=hermite(carga,solta,np.zeros(6),derivadas(),t-CARGA,SAI-CARGA)
    else:
        # Continua a descarga no ar, seguida pelo recolhimento progressivo.
        fim=solta+derivadas()*.055
        if t<=.94:ang=hermite(solta,fim,derivadas(),np.zeros(6),t-SAI,.12)
        else:
            w=C(t,[(.94,0),(1.28,.75),(1.52,1),(DURACAO,1)])
            ang=(1-w)*fim+w*repouso
    pel=C(t,[(0,0),(.18,12),(.34,32),(.48,55),(CARGA,65),(SAI,66),(.96,34),(1.14,6),(1.44,-12),(POUSA,-15),(1.75,-9),(2.1,-3),(DURACAO,0)])
    return pel,ang


def derivadas():
    # Velocidades angulares distribuídas, sem inverter o sentido da curvatura.
    return np.array([-35,-90,-346.79857,-126.91361,-576.47687,-811.67851])


def tronco(m,t):
    pel,ang=parametros(t);p={n:{'rotacao':[0,0,0]} for n in m.ossos}
    p['pelvis']={'rotacao':[pel,0,0]}
    p['waist']={'rotacao':[C(t,[(0,0),(.34,-6),(CARGA,-5),(SAI,-12),(.96,-2),(1.12,9),(1.40,5),(POUSA,-6),(1.78,4),(DURACAO,0)]),0,0]}
    p['chest']={'rotacao':[C(t,[(0,0),(.34,-6),(CARGA,-12),(SAI,-16),(.96,-9),(1.12,4),(1.42,-3),(POUSA,10),(1.85,-4),(DURACAO,0)]),0,0]}
    anterior=pel
    for i,n in enumerate(CAUDA):
        absbone=ang[i]-(15 if i<3 else 12.5)
        p[n]={'rotacao':[float(absbone-anterior),0,0]};anterior=absbone
    return p


def apoio_cauda(m,t):
    mats=bbmodelo.matrizes_ossos(m,tronco(m,t))
    pts=np.concatenate([bbmodelo.aplicar(bbmodelo.matriz_cubo(m,m.cubo(n),mats),bbmodelo.cantos(m.cubo(n))) for n in PARTES])
    # Mesmo ponto material no plano sagital: nunca troca o contato para outro vértice em Z.
    c=m.cubo('tail_base_3');pt=(c.de+c.ate)/2;pt[1]=c.de[1];pt[2]=c.ate[2]
    pt=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mats),[pt])[0]
    return np.array([0,CHAO-pts[:,1].min(),24.75-pt[2]])


_cache={}
def cinematica(m):
    if id(m) not in _cache:
        dt=.0001;a=apoio_cauda(m,SAI)
        v=(25*a-48*apoio_cauda(m,SAI-dt)+36*apoio_cauda(m,SAI-2*dt)-16*apoio_cauda(m,SAI-3*dt)+3*apoio_cauda(m,SAI-4*dt))/(12*dt)
        d=POUSA-SAI;fim=np.array([0,-4.,a[2]+v[2]*d]);grav=2*(a[1]+v[1]*d-fim[1])/d**2
        _cache[id(m)]=(a,v,fim,grav)
    return _cache[id(m)]


def corpo(m,t):
    a,v,fim,grav=cinematica(m)
    if t<=SAI:
        w=C(t,[(0,0),(.13,0),(.34,1),(SAI,1)])
        regular=np.array([0,C(t,[(0,0),(.20,-1),(.34,-2)]),C(t,[(0,0),(.20,2),(.34,4)])])
        return (1-w)*regular+w*apoio_cauda(m,t)
    if t<=POUSA:
        u=t-SAI;return a+v*u+[0,-.5*grav*u*u,0]
    parada=fim[2]+v[2]*.085
    if t<1.77:
        return np.array([0,hermite(fim[1],-6.2,v[1]-grav*(POUSA-SAI),0,t-POUSA,.17),
                         hermite(fim[2],parada,v[2],0,t-POUSA,.17)])
    return np.array([0,C(t,[(1.77,-6.2),(2.02,-3.3),(2.38,-2.5),(DURACAO,0)]),
                     C(t,[(1.77,parada),(1.88,parada),(2.24,parada*.5),(2.6,0),(DURACAO,0)])])


def alvo_pe(m,t,lado,parent):
    c=v5.v4.centro_pe(m,lado);landing=cinematica(m)[2][2]
    if t<SOLTA_PES:
        ang=C(t,[(0,0),(.12,-4),(.28,-32),(SOLTA_PES,-45)])
        a=v5.v4.apoio(m,lado,ang)
        a[2]+=C(t,[(0,0),(.08,0),(.22,4.5),(SOLTA_PES,7.5)])
        # Passos curtos antes da rolagem sobre os dedos.
        ini,fim=(.05,.17) if lado=='right' else (.18,.29)
        if ini<t<fim:a[1]+=.7*np.sin(np.pi*(t-ini)/(fim-ini))**2
        return a,ang
    if t>=POUSA:
        ini,fim=(1.91,2.35) if lado=='right' else (2.12,2.60)
        a=c.copy();a[2]+=C(t,[(POUSA,landing),(ini,landing),(fim,0),(DURACAO,0)])
        if ini<t<fim:a[1]+=1.5*np.sin(np.pi*(t-ini)/(fim-ini))**2
        return a,0
    h=bbmodelo.aplicar(parent,[m.ossos['leg_'+lado].origem])[0]
    # Alvo acompanha o quadril e a linha de ação do peito; não fixa a pata em Y global.
    tuck=np.array([c[0],h[1]-5.2,h[2]-7.0])
    hit=np.array([np.copysign(4.7,c[0]),h[1]+5.5,h[2]-16.3])
    entry=C(t,[(SOLTA_PES,0),(.54,1),(POUSA,1)])
    kick=C(t,[(SOLTA_PES,0),(.79,0),(.87,.60),(.94,1),(1.02,1),(1.17,0),(POUSA,0)])
    exit=C(t,[(SOLTA_PES,0),(1.30,0),(POUSA,1)])
    inicio=v5.v4.apoio(m,lado,-45)+[0,0,7.5]
    a=(1-entry)*inicio+entry*((1-kick)*tuck+kick*hit)
    a=(1-exit)*a+exit*(c+[0,0,landing])
    ang=C(t,[(SOLTA_PES,-45),(.54,10),(.79,12),(.94,70),(1.02,70),(1.17,15),(POUSA,0)])
    return a,ang


def pose(m,t):
    t=float(t);out=tronco(m,t);out['body']={'rotacao':[0,0,0],'posicao':corpo(m,t).tolist()}
    parent=bbmodelo.matrizes_ossos(m,out)['waist'];r=parent[:3,:3];o=m.ossos['body'].origem
    for lado in ['left','right']:
        a,ang=alvo_pe(m,t,lado,parent)
        rs=v5.v4.perna(m,lado,euler(r),parent[:3,3]-o+r@o,a,ang)
        for n,v in zip(['leg_','shin_','foot_'],rs):out[n+lado]={'rotacao':v}
    out['neck_1']={'rotacao':[C(t,[(0,0),(.30,-10),(CARGA,-22),(SAI,-16),(.98,-10),(1.12,7),(1.40,-4),(POUSA,8),(1.86,-5),(DURACAO,0)]),0,0]}
    out['head']={'rotacao':[C(t,[(0,0),(.34,-7),(CARGA,-18),(SAI,-8),(.98,3),(1.16,-6),(POUSA,-10),(2.02,1),(DURACAO,0)]),0,0]}
    for lado,s in [('left',1),('right',-1)]:
        out['arm_'+lado]={'rotacao':[C(t,[(0,0),(.30,16),(.59,32),(.76,32),(.91,4),(1.04,-15),(1.21,13),(POUSA,23),(1.90,-7),(DURACAO,0)]),0,
                                    -s*C(t,[(0,0),(.38,7),(.72,12),(.99,15),(1.24,8),(1.62,12),(2.2,0),(DURACAO,0)])]}
        out['forearm_'+lado]={'rotacao':[C(t,[(0,0),(.32,-12),(CARGA,-28),(SAI,-26),(.98,-3),(1.18,-17),(POUSA,-22),(1.90,4),(DURACAO,0)]),0,0]}
    distal=parametros(t)[1][-1]-12.5
    w=C(t,[(0,0),(.04,0),(.14,1),(1.90,1),(2.40,0),(DURACAO,0)])
    fan=-(distal+105)*w
    for n in m.ossos:
        if n.startswith('tail_blade_'):out[n]={'rotacao':[fan,0,0]}
    # 18 graus liberam os dedos durante a transferência sem cruzar a bacia.
    v5.v4.alinhar_penas_pernas(m,out,1.5*C(t,[(0,0),(.26,1),(2.24,1),(2.60,0),(DURACAO,0)]))
    return out


def medir(m):
    surf={c.uuid:v5.v4.superficie_opaca(m,c) for c in m.cubos};mini=(100,None,None);errors=[]
    for t in np.linspace(0,DURACAO,int(round(DURACAO*FPS))+1):
        try:p=pose(m,t)
        except ValueError as e:errors.append((float(t),str(e)));continue
        mats=bbmodelo.matrizes_ossos(m,p)
        for c in m.cubos:
            y=float(bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mats),surf[c.uuid])[:,1].min())
            if y<mini[0]:mini=(y,float(t),c.nome)
    a,v,f,g=cinematica(m)
    return {'minimo_y_visivel':mini,'alcance_erros':errors,'lancamento_pos':a.tolist(),'lancamento_vel':v.tolist(),'pouso_pos':f.tolist(),'gravidade_visual':g}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--medir',action='store_true');ap.add_argument('--refazer',action='store_true');args=ap.parse_args()
    original=sha(FONTE);m=bbmodelo.ler(FONTE);ops=preparar_rig(m);med=medir(m)
    if args.medir:
        for k,v in med.items():print(k,v if k!='alcance_erros' else v[:8])
        return
    if med['alcance_erros'] or med['minimo_y_visivel'][0]<CHAO-.025:raise SystemExit('Corrigir alcance/chão antes de gerar.')
    prov=PASTA/'proveniencia.json'
    if SAIDA.exists():
        velho=json.loads(prov.read_text()) if prov.exists() else {}
        if not args.refazer or velho.get('saida_sha256')!=sha(SAIDA) or velho.get('fonte_sha256')!=original:raise SystemExit('Saída editada/existente preservada; criar outra versão.')
    PASTA.mkdir(exist_ok=True)
    ops.extend([{'op':'remove_animation','animation':NOME},{'op':'add_animation','name':NOME,'length':DURACAO,'loop':'once','snapping':FPS}])
    tt=np.linspace(0,DURACAO,int(round(DURACAO*FPS))+1);pp=[pose(m,t) for t in tt]
    for n in m.ossos:
        for canal,campo in [('rotation','rotacao'),('position','posicao')]:
            if canal=='position' and n!='body':continue
            vv=np.array([p.get(n,{}).get(campo,[0,0,0]) for p in pp])
            if canal=='rotation':vv=v5.v4.continuidade(vv)
            inds=[0,len(tt)-1] if np.max(abs(vv-vv[0]))<1e-9 else range(len(tt))
            for i in inds:ops.append({'op':'set_keyframe','animation':NOME,'bone':n,'channel':canal,'time':round(float(tt[i]),6),'value':vv[i].round(6).tolist(),'interpolation':'linear'})
    (PASTA/'catapulta.ops.json').write_text(json.dumps(ops,separators=(',',':'))+'\n',encoding='utf-8')
    shutil.copy2(FONTE,SAIDA);motor.editar(SAIDA,ops)
    novo=bbmodelo.ler(SAIDA);assert novo.bruto['textures']==m.bruto['textures']
    for a in m.animacoes:
        if a['name']==NOME:continue
        aa=copy.deepcopy(a)
        for v in aa.get('animators',{}).values():v.setdefault('keyframes',[])
        assert aa==next(v for v in novo.animacoes if v['uuid']==a['uuid'])
    assert sha(FONTE)==original
    prov.write_text(json.dumps({'fonte':FONTE.relative_to(RAIZ).as_posix(),'fonte_sha256':original,'saida_sha256':sha(SAIDA),'cubos':len(novo.cubos),'grupos':len(novo.ossos),'fps':FPS,'operacoes':len(ops),'pisao_spin_chaves_preservadas':True},indent=2)+'\n',encoding='utf-8')
    (PASTA/'medidas-planejadas.json').write_text(json.dumps(med,indent=2)+'\n',encoding='utf-8')
    marc=json.loads((FONTE.parent/'animacoes.json').read_text());marc[NOME]={'HitFrame':.94,'RecoveryStart':1.17,'CancelOpen':1.91}
    (PASTA/'animacoes.json').write_text(json.dumps(marc,indent=2)+'\n',encoding='utf-8')
    print('Criada v7:',len(novo.cubos),'cubos,',len(novo.ossos),'grupos;',len(ops),'operações; aprovados preservados.')


if __name__=='__main__':main()
