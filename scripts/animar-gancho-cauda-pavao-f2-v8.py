"""F2 v8: cauda em J voltado para trás, leque externo e chute na descida."""
import argparse
import copy
import importlib.util
import json
import shutil
from pathlib import Path

import numpy as np
from criaturas import bbmodelo,motor

RAIZ=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('catapulta_v7',RAIZ/'scripts/animar-catapulta-pavao-f2-v7.py')
v7=importlib.util.module_from_spec(s);s.loader.exec_module(v7)
v5=v7.v5
FONTE=v7.SAIDA
PASTA=FONTE.parent.parent/'ataque-v8'
SAIDA=PASTA/'criatura-pavao-e2-ataque-v8.bbmodel'
NOME=v7.NOME
DURACAO=2.85
FPS=120
CHAO=v7.CHAO
CARGA=.62
SAI=.82
POUSA=1.70
C=v7.C
sha=v7.sha
euler=v7.euler
hermite=v7.hermite
PARTES=v7.PARTES
CAUDA=['tail_1','tail_mid_flex_2','tail_mid_flex_3','tail_hook','tail_base_flex_2','tail_base_flex_3']


def preparar_rig(m):
    ops=[];rest=bbmodelo.matrizes_ossos(m)
    for n in ['tail_mid_flex_2','tail_mid_flex_3','tail_base_flex_2','tail_base_flex_3']:
        c=m.cubo(n.replace('_flex',''));pt=(c.de+c.ate)/2
        pt[1]=c.ate[1] if n=='tail_mid_flex_2' else c.de[1];pt[2]=c.de[2]
        o=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,rest),[pt])[0]
        m.ossos[n].origem=o;ops.append({'op':'update_node','target':n,'origin':o.tolist()})
    c=m.cubo('tail_base');pt=(c.de+c.ate)/2;pt[1]=c.de[1];pt[2]=c.de[2]
    o=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,rest),[pt])[0]
    m.ossos['tail_hook']=bbmodelo.Osso('tail_hook','virtual_tail_hook','tail_2',o,np.zeros(3))
    ops.append({'op':'add_group','name':'tail_hook','parent':'tail_2','origin':o.tolist()})
    c.osso='tail_hook';ops.append({'op':'update_node','target':c.uuid,'parent':'tail_hook'})
    m.ossos['tail_base_flex_2'].pai='tail_hook';ops.append({'op':'update_node','target':'tail_base_flex_2','parent':'tail_hook'})
    return ops


def derivadas():
    return np.array([-392.567873,-353.492916,.368813,413.663585,748.735144,-300.])


def parametros(t):
    repouso=np.array([15,15,15,12.5,12.5,12.5])
    toca=np.array([60,75,55,15,-20,-35])
    carga=np.array([80,90,70,30,-8,-35])
    solta=np.array([82,85,75,55,10,-23])
    if t<=.34:ang=repouso+(toca-repouso)*C(t,[(0,0),(.08,0),(.34,1)])
    elif t<=CARGA:ang=toca+(carga-toca)*C(t,[(.34,0),(CARGA,1)])
    elif t<=SAI:ang=hermite(carga,solta,np.zeros(6),derivadas(),t-CARGA,SAI-CARGA)
    elif t<=.94:ang=hermite(solta,np.array([65,72,65,58,30,-8]),derivadas(),np.zeros(6),t-SAI,.12)
    else:
        fim=np.array([65,72,65,58,30,-8]);w=C(t,[(.94,0),(1.35,.8),(1.60,1),(DURACAO,1)])
        alvo=repouso.copy();alvo[-1]=C(t,[(.94,-20),(2.28,-20),(2.75,12.5),(DURACAO,12.5)])
        ang=(1-w)*fim+w*alvo
    pel=C(t,[(0,0),(.18,12),(.34,48),(.48,77),(CARGA,95),(SAI,82),(.99,37),(1.17,7),(1.50,-12),(POUSA,-15),(1.85,-9),(2.25,-3),(DURACAO,0)])
    return pel,ang


def tronco(m,t):
    pel,ang=parametros(t);p={n:{'rotacao':[0,0,0]} for n in m.ossos}
    p['pelvis']={'rotacao':[pel,0,0]}
    p['waist']={'rotacao':[C(t,[(0,0),(.34,-16),(CARGA,-22),(SAI,-20),(.99,-2),(1.17,9),(1.50,5),(POUSA,-6),(1.88,4),(DURACAO,0)]),0,0]}
    p['chest']={'rotacao':[C(t,[(0,0),(.34,-6),(CARGA,-12),(SAI,-16),(.99,-9),(1.17,4),(1.50,-3),(POUSA,10),(1.95,-4),(DURACAO,0)]),0,0]}
    anterior=pel
    for i,n in enumerate(CAUDA):
        absoluto=ang[i]-(15 if i<3 else 12.5)
        p[n]={'rotacao':[float(absoluto-anterior),0,0]};anterior=absoluto
    return p


def apoio_cauda(m,t):
    mat=bbmodelo.matrizes_ossos(m,tronco(m,t))
    pts=np.concatenate([bbmodelo.aplicar(bbmodelo.matriz_cubo(m,m.cubo(n),mat),bbmodelo.cantos(m.cubo(n))) for n in PARTES])
    # Apoio na barriga do gancho, não na ponta que deve ficar levantada.
    c=m.cubo('tail_base_2');pt=(c.de+c.ate)/2;pt[1]=c.de[1];pt[2]=c.de[2]
    pt=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mat),[pt])[0]
    return np.array([0,CHAO-pts[:,1].min(),20.5-pt[2]])


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
    if t<1.87:return np.array([0,hermite(fim[1],-6.2,v[1]-grav*(POUSA-SAI),0,t-POUSA,.17),hermite(fim[2],parada,v[2],0,t-POUSA,.17)])
    return np.array([0,C(t,[(1.87,-6.2),(2.12,-3.3),(2.50,-2.5),(DURACAO,0)]),C(t,[(1.87,parada),(1.98,parada),(2.38,parada*.5),(2.75,0),(DURACAO,0)])])


def alvo_pe(m,t,lado,parent):
    c=v5.v4.centro_pe(m,lado);landing=cinematica(m)[2][2]
    if t<.38:
        ang=C(t,[(0,0),(.12,-4),(.28,-32),(.38,-45)])
        a=v5.v4.apoio(m,lado,ang);a[2]+=C(t,[(0,0),(.08,0),(.22,4.5),(.38,7.5)])
        ini,fim=(.05,.17) if lado=='right' else (.18,.29)
        if ini<t<fim:a[1]+=.7*np.sin(np.pi*(t-ini)/(fim-ini))**2
        return a,ang
    if t>=POUSA:
        ini,fim=(2.01,2.50) if lado=='right' else (2.24,2.75)
        a=c.copy();a[2]+=C(t,[(POUSA,landing),(ini,landing),(fim,0),(DURACAO,0)])
        if ini<t<fim:a[1]+=1.5*np.sin(np.pi*(t-ini)/(fim-ini))**2
        return a,0
    h=bbmodelo.aplicar(parent,[m.ossos['leg_'+lado].origem])[0]
    tuck=np.array([c[0],h[1]-5.2,h[2]-7.0]);hit=np.array([np.copysign(4.7,c[0]),h[1]+5.5,h[2]-16.3])
    entrada=C(t,[(.38,0),(.54,1),(POUSA,1)])
    # Espera o arco: chute começa somente após o ápice e com avanço já estabelecido.
    a,v,_,grav=cinematica(m);apice=SAI+v[1]/grav;inicio=apice+.035;impacto=inicio+.13
    golpe=C(t,[(.38,0),(inicio,0),(impacto,1),(impacto+.045,1),(impacto+.17,0),(POUSA,0)])
    saida=C(t,[(.38,0),(POUSA-.16,0),(POUSA,1)])
    alvo=(1-entrada)*(v5.v4.apoio(m,lado,-45)+[0,0,7.5])+entrada*((1-golpe)*tuck+golpe*hit)
    alvo=(1-saida)*alvo+saida*(c+[0,0,landing])
    ang=C(t,[(.38,-45),(.54,10),(inicio,12),(impacto,70),(impacto+.045,70),(impacto+.17,15),(POUSA,0)])
    return alvo,ang


def pose(m,t):
    t=float(t);p=tronco(m,t);p['body']={'rotacao':[0,0,0],'posicao':corpo(m,t).tolist()}
    parent=bbmodelo.matrizes_ossos(m,p)['waist'];r=parent[:3,:3];o=m.ossos['body'].origem
    for lado in ['left','right']:
        a,ang=alvo_pe(m,t,lado,parent)
        rs=v5.v4.perna(m,lado,euler(r),parent[:3,3]-o+r@o,a,ang)
        for n,v in zip(['leg_','shin_','foot_'],rs):p[n+lado]={'rotacao':v}
    _,vel,_,grav=cinematica(m);apice=SAI+vel[1]/grav;hit=apice+.165
    p['neck_1']={'rotacao':[C(t,[(0,0),(.30,-10),(CARGA,-22),(SAI,-16),(apice,-10),(hit,7),(POUSA,8),(1.96,-5),(DURACAO,0)]),0,0]}
    p['head']={'rotacao':[C(t,[(0,0),(.34,-7),(CARGA,-18),(SAI,-8),(apice,0),(hit,-6),(POUSA,-10),(2.15,1),(DURACAO,0)]),0,0]}
    for lado,s in [('left',1),('right',-1)]:
        p['arm_'+lado]={'rotacao':[C(t,[(0,0),(.30,16),(.59,32),(SAI,32),(apice,29),(hit,-15),(hit+.15,13),(POUSA,23),(2.05,-7),(DURACAO,0)]),0,
                                  -s*C(t,[(0,0),(.38,7),(SAI,12),(apice,13),(hit,15),(POUSA,12),(2.35,0),(DURACAO,0)])]}
        p['forearm_'+lado]={'rotacao':[C(t,[(0,0),(.32,-12),(CARGA,-28),(SAI,-26),(apice,-24),(hit,-3),(hit+.14,-17),(POUSA,-22),(2.05,4),(DURACAO,0)]),0,0]}
    for n in m.ossos:
        if n.startswith('tail_blade_'):p[n]={'rotacao':[0,0,0]}
    # A lâmina central inferior levanta pela inserção durante a soltura; não dobra o leque inteiro.
    for c in m.cubos:
        if c.osso.startswith('tail_blade_') and c.nome=='fan_5':
            p[c.osso]={'rotacao':[C(t,[(0,0),(.62,0),(.75,-15),(.88,-15),(1.08,0),(DURACAO,0)]),0,0]}
    v5.v4.alinhar_penas_pernas(m,p,1.5*C(t,[(0,0),(.26,1),(2.38,1),(2.75,0),(DURACAO,0)]))
    if t<=0 or t>=DURACAO:
        p={n:{'rotacao':[0,0,0]} for n in m.ossos};p['body']['posicao']=[0,0,0]
    return p


def medir(m):
    surf={c.uuid:v5.v4.superficie_opaca(m,c) for c in m.cubos};mini=(100,None,None);erros=[]
    for t in np.linspace(0,DURACAO,int(round(DURACAO*FPS))+1):
        try:p=pose(m,t)
        except ValueError as e:erros.append((float(t),str(e)));continue
        mat=bbmodelo.matrizes_ossos(m,p)
        for c in m.cubos:
            y=float(bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mat),surf[c.uuid])[:,1].min())
            if y<mini[0]:mini=(y,float(t),c.nome)
    a,v,f,g=cinematica(m)
    return {'minimo_y_visivel':mini,'alcance_erros':erros,'lancamento_pos':a.tolist(),'lancamento_vel':v.tolist(),'pouso_pos':f.tolist(),'gravidade_visual':g}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--medir',action='store_true');ap.add_argument('--refazer',action='store_true');args=ap.parse_args()
    original=sha(FONTE);m=bbmodelo.ler(FONTE);ops=preparar_rig(m);med=medir(m)
    if args.medir:
        for k,v in med.items():print(k,v if k!='alcance_erros' else v[:8])
        return
    if med['alcance_erros'] or med['minimo_y_visivel'][0]<CHAO-.025:raise SystemExit('Corrigir alcance/chão antes de gerar.')
    prov=PASTA/'proveniencia.json'
    if SAIDA.exists():
        velho=json.loads(prov.read_text()) if prov.exists() else {}
        if not args.refazer or velho.get('saida_sha256')!=sha(SAIDA) or velho.get('fonte_sha256')!=original:raise SystemExit('Saída editada/existente preservada; criar outra versão.')
    PASTA.mkdir(exist_ok=True);ops.extend([{'op':'remove_animation','animation':NOME},{'op':'add_animation','name':NOME,'length':DURACAO,'loop':'once','snapping':FPS}])
    tt=np.linspace(0,DURACAO,int(round(DURACAO*FPS))+1);pp=[pose(m,t) for t in tt]
    rotacoes={n:v5.v4.continuidade(np.array([p.get(n,{}).get('rotacao',[0,0,0]) for p in pp])) for n in m.ossos}
    for n,vv in rotacoes.items():
        inds=[0,len(tt)-1] if np.max(abs(vv-vv[0]))<1e-9 else range(len(tt))
        for i in inds:ops.append({'op':'set_keyframe','animation':NOME,'bone':n,'channel':'rotation','time':round(float(tt[i]),6),'value':vv[i].round(6).tolist(),'interpolation':'linear'})
    # O ponto sólido mais baixo troca de canto na descarga. Refina somente a translação
    # do apoio, usando as rotações que o arquivo realmente interpola (sem duplicar o rig).
    tpos=sorted(set(tt.tolist()+[.34,SAI]+[float(t) for t in np.arange(.34,SAI,1/240)]))
    for t in tpos:
        bp=corpo(m,t).copy()
        if .34<=t<=SAI:
            po={n:{'rotacao':[float(np.interp(t,tt,vv[:,j])) for j in range(3)]} for n,vv in rotacoes.items()}
            po['body']['posicao']=bp.tolist();mat=bbmodelo.matrizes_ossos(m,po)
            low=min(float(bbmodelo.caixa_mundo(m,m.cubo(n),mat)[0][1]) for n in PARTES)
            bp[1]+=CHAO-low
        ops.append({'op':'set_keyframe','animation':NOME,'bone':'body','channel':'position','time':round(float(t),6),'value':bp.round(6).tolist(),'interpolation':'linear'})
    (PASTA/'gancho.ops.json').write_text(json.dumps(ops,separators=(',',':'))+'\n',encoding='utf-8')
    shutil.copy2(FONTE,SAIDA);motor.editar(SAIDA,ops)
    novo=bbmodelo.ler(SAIDA);assert novo.bruto['textures']==m.bruto['textures']
    assert novo.bruto['elements']==m.bruto['elements']
    for a in m.animacoes:
        if a['name']==NOME:continue
        aa=copy.deepcopy(a)
        for v in aa.get('animators',{}).values():v.setdefault('keyframes',[])
        assert aa==next(v for v in novo.animacoes if v['uuid']==a['uuid'])
    assert sha(FONTE)==original
    prov.write_text(json.dumps({'fonte':FONTE.relative_to(RAIZ).as_posix(),'fonte_sha256':original,'saida_sha256':sha(SAIDA),'cubos':len(novo.cubos),'grupos':len(novo.ossos),'fps':FPS,'operacoes':len(ops),'pisao_spin_chaves_preservadas':True},indent=2)+'\n',encoding='utf-8')
    (PASTA/'medidas-planejadas.json').write_text(json.dumps(med,indent=2)+'\n',encoding='utf-8')
    a,v,_,grav=cinematica(m);hit=SAI+v[1]/grav+.165
    marc=json.loads((FONTE.parent/'animacoes.json').read_text());marc[NOME]={'HitFrame':round(hit,6),'RecoveryStart':round(hit+.17,6),'CancelOpen':2.01}
    (PASTA/'animacoes.json').write_text(json.dumps(marc,indent=2)+'\n',encoding='utf-8')
    print('Criada v8:',len(novo.cubos),'cubos,',len(novo.ossos),'grupos;',len(ops),'operações; aprovados preservados.')


if __name__=='__main__':main()
