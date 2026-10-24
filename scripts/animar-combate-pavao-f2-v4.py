"""F2 v4: pisão, giro cortante baixo e ataque duplo com apoio sólido da cauda.

uv run python scripts/animar-combate-pavao-f2-v4.py [--medir | --refazer]
"""
import argparse
import copy
import importlib.util
import json
import math
import shutil
from pathlib import Path

import numpy as np
from criaturas import bbmodelo, motor, roblox_infra

RAIZ=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('bote_base_v3',RAIZ/'scripts/animar-bote-pavao-f2-v3.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
FONTE=base.FONTE
PASTA=FONTE.parent/'ataque-v4'
SAIDA=PASTA/'criatura-pavao-e2-ataque-v4.bbmodel'
FPS=120
CHAO=.08741
CLIPES={'attack_stomp':1.25,'attack_spin':1.35,'attack_tail_kick':1.55}
C=base.curva


def unit(v):
    v=np.asarray(v,float);return v/np.linalg.norm(v)


def rod(eixo,angulo):
    x,y,z=unit(eixo);k=np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
    return np.eye(3)+math.sin(angulo)*k+(1-math.cos(angulo))*(k@k)


def misturar(a,b,w):
    if w<=0:return a
    if w>=1:return b
    d=a.T@b;ang=math.acos(float(np.clip((np.trace(d)-1)/2,-1,1)))
    if ang<1e-9:return a
    if math.pi-ang<1e-5:
        _,v=np.linalg.eigh((d+np.eye(3))/2);eixo=v[:,-1]
    else:eixo=unit([d[2,1]-d[1,2],d[0,2]-d[2,0],d[1,0]-d[0,1]])
    return a@rod(eixo,w*ang)


def ponto_face(m,c,frente=True):
    p=(c.de+c.ate)/2;p[2]=c.de[2] if frente else c.ate[2]
    return bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,bbmodelo.matrizes_ossos(m)),[p])[0]


def preparar_rig(m):
    """Rig corrigido sem mover geometria/UV em repouso nem adicionar partes."""
    ops=[]
    def grupo(nome,pai,origem):
        origem=np.array(origem,float)
        m.ossos[nome]=bbmodelo.Osso(nome,'virtual_'+nome,pai,origem,np.zeros(3))
        ops.append({'op':'add_group','name':nome,'origin':origem.tolist(),**({'parent':pai} if pai else {})})
    def mover(c,pai):
        c.osso=pai;ops.append({'op':'update_node','target':c.uuid,'parent':pai})
    grupo('combat_pivot',None,[0,0,.66835])
    m.ossos['body'].pai='combat_pivot';ops.append({'op':'update_node','target':'body','parent':'combat_pivot'})
    junta=ponto_face(m,m.cubo('tail_mid'))
    m.ossos['tail_1'].origem=junta
    ops.append({'op':'update_node','target':'tail_1','origin':junta.tolist()})
    for lado in ['left','right']:
        grupo('elbow_blades_'+lado,'forearm_'+lado,m.ossos['forearm_'+lado].origem)
        for c in m.cubos:
            if c.nome in [f'wing_{lado}_feather_{n}' for n in [1,8,9]]:mover(c,'elbow_blades_'+lado)
            elif c.nome.startswith('leg_'+lado+'_feather_'):
                nome=f'ankle_blade_{lado}_{c.nome.rsplit("_",1)[-1]}'
                grupo(nome,'shin_'+lado,ponto_face(m,c));mover(c,nome)
    # As lâminas da cauda giram sobre suas próprias bases, não por pivôs no meio do leque.
    for i,c in enumerate([c for c in m.cubos if c.nome.startswith('fan_')],1):
        nome=f'tail_blade_{i:02d}';grupo(nome,c.osso,ponto_face(m,c));mover(c,nome)
    return ops


def centro_pe(m,lado):
    c=m.cubo('toe_'+lado+'_1');return (c.de+c.ate)/2


def apoio(m,lado,ang):
    return base.v2.apoio(m,lado,ang)


def perna(m,lado,br,bp,alvo,ang):
    return base.ik(m,lado,br,bp,alvo,ang)


def base_pose(m,br,bp,neck,olhar):
    p={n:{'rotacao':[0,0,0]} for n in m.ossos}
    p['body']={'rotacao':br,'posicao':bp}
    p['neck_1']={'rotacao':[neck,0,0]};p['head']={'rotacao':[olhar-br[0]-neck,0,0]}
    return p


def colocar_pernas(m,p,alvos):
    for lado,(alvo,ang) in alvos.items():
        a,b,c=perna(m,lado,p['body']['rotacao'],p['body']['posicao'],alvo,ang)
        for nome,v in [('leg_',a),('shin_',b),('foot_',c)]:p[nome+lado]={'rotacao':v}


def alinhar_penas_pernas(m,p,w):
    # Penas rígidas: pequena correção pela raiz real para liberar o tornozelo.
    for lado,s in [('left',1),('right',-1)]:
        for i in [1,2,3]:p[f'ankle_blade_{lado}_{i}']={'rotacao':[0,s*12*w,0]}


def alvo_pisao(m,t,lado):
    centro=centro_pe(m,lado)
    if lado=='right':
        ang=C(t,[(0,0),(.2,0),(.42,-8),(.575,-22),(.70,-14),(.85,0),(1.25,0)])
        a=apoio(m,lado,ang)
        a[2]+=C(t,[(0,0),(.04,0),(.18,3.5),(.70,3.5),(.91,0),(1.25,0)])
        a[1]+=C(t,[(0,0),(.04,0),(.10,.8),(.18,0),(.70,0),(.80,1.1),(.91,0),(1.25,0)])
        return a,ang
    a=centro.copy()
    a[0]+=C(t,[(0,0),(.18,0),(.40,3),(.90,3),(1.16,0),(1.25,0)])
    a[1]+=C(t,[(0,0),(.18,0),(.32,3),(.425,4.5),(.50,3),(.575,0),(.90,0),(1.02,1.5),(1.16,0),(1.25,0)])
    a[2]-=C(t,[(0,0),(.18,0),(.425,2),(.575,8.5),(.90,8.5),(1.16,0),(1.25,0)])
    ang=C(t,[(0,0),(.18,0),(.425,-8),(.52,-3),(.575,0),(.90,0),(1.02,-8),(1.16,0),(1.25,0)])
    return a,ang


def pose_pisao(m,t):
    phi=C(t,[(0,0),(.20,-3),(.425,-7),(.575,-15),(.64,-19),(.78,-9),(1.25,0)])
    bx=C(t,[(0,0),(.10,-1),(.20,2.5),(.425,2.8),(.575,1.8),(.72,-.8),(.90,0),(1.25,0)])
    by=C(t,[(0,0),(.18,-.5),(.425,0),(.575,-1),(.64,-1.4),(.78,-.5),(1.25,0)])
    bz=C(t,[(0,0),(.20,-.2),(.425,-.6),(.575,-2.6),(.64,-3.2),(.78,-2.5),(.90,-1.8),(1.25,0)])
    neck=C(t,[(0,0),(.18,-9),(.425,4),(.575,14),(.70,8),(1.25,0)])
    olhar=C(t,[(0,0),(.18,-15),(.425,-24),(.575,-40),(.70,-25),(1.25,0)])
    p=base_pose(m,[phi,0,0],[bx,by,bz],neck,olhar)
    colocar_pernas(m,p,{l:alvo_pisao(m,t,l) for l in ['left','right']})
    for lado,s in [('left',1),('right',-1)]:
        p['arm_'+lado]={'rotacao':[C(t,[(0,0),(.425,7),(.575,13),(.72,5),(1.25,0)]),0,-s*C(t,[(0,0),(.425,5),(.575,8),(1.25,0)])]}
        p['forearm_'+lado]={'rotacao':[C(t,[(0,0),(.425,-7),(.575,-12),(.72,4),(1.25,0)]),0,0]}
    p['tail_1']={'rotacao':[-phi*.55,0,0]}
    alinhar_penas_pernas(m,p,C(t,[(0,0),(.20,1),(.99,1),(1.25,0)]))
    return p


def orientacao_lamina(m,lado):
    cubos=[c for c in m.cubos if c.osso=='elbow_blades_'+lado]
    rs=[bbmodelo.matriz_rotacao(c.rotacao) for c in cubos]
    n=unit(np.mean([r[:,0] for r in rs],axis=0))
    l=np.mean([r[:,2] for r in rs],axis=0);l=unit(l-n*(l@n))
    s=1 if lado=='left' else -1
    alvo_n=np.array([0,-s,0]);alvo_l=np.array([-s,0,0])
    return np.column_stack([alvo_n,alvo_l,np.cross(alvo_n,alvo_l)])@np.column_stack([n,l,np.cross(n,l)]).T


def folhas_cauda(m,p,peso,modo):
    mats=bbmodelo.matrizes_ossos(m,p)
    for c in m.cubos:
        if not c.osso or not c.osso.startswith('tail_blade_'):continue
        o=m.ossos[c.osso];rp=mats[o.pai][:3,:3]
        if modo=='flat':
            n=bbmodelo.matriz_rotacao(c.rotacao)[:,0]
            destino=base.v2.entre_vetores(n,np.array([0,1,0]))
        else:
            rc=bbmodelo.matriz_rotacao(c.rotacao);n,l=rc[:,0],rc[:,2]
            # Lâminas erguidas com a aresta de fixação horizontal: não entram no piso.
            nn=unit([n[0],0,n[2]]);ll=np.array([0,1,0])
            cima=np.column_stack([nn,ll,np.cross(nn,ll)])@np.column_stack([n,l,np.cross(n,l)]).T
            destino=misturar(np.eye(3),cima,peso)
        r=misturar(np.eye(3),rp.T@destino,peso) if modo=='flat' else rp.T@destino
        p[o.nome]={'rotacao':base.v2.base.euler(r)}


def pose_giro(m,t):
    w=C(t,[(0,0),(.18,.25),(.40,1),(.80,1),(1.15,0),(1.35,0)])
    phi=-26*w;by=-6*w
    p=base_pose(m,[phi,0,0],[0,by,0],18*w,-3*w)
    alvos={}
    for lado,s in [('left',1),('right',-1)]:
        ang=-5*w;a=apoio(m,lado,ang)
        a[0]+=s*C(t,[(0,0),(.3,-.5),(.8,-.5),(1.15,0),(1.35,0)])
        alvos[lado]=(a,ang)
        ar=[6*w,0,-s*8*w];p['arm_'+lado]={'rotacao':ar}
        parent=bbmodelo.matriz_rotacao([phi,0,0])@bbmodelo.matriz_rotacao(ar)
        p['forearm_'+lado]={'rotacao':base.v2.base.euler(misturar(np.eye(3),parent.T@orientacao_lamina(m,lado),w))}
    colocar_pernas(m,p,alvos)
    alinhar_penas_pernas(m,p,w)
    p['tail_1']={'rotacao':[-phi,0,0]}
    folhas_cauda(m,p,w,'flat')
    yaw=C(t,[(0,0),(.30,-14),(.40,-14),(.46,0),(.56,125),(.66,280),(.76,360),(.84,364),(1.0,360),(1.35,360)])
    p['combat_pivot']={'rotacao':[0,yaw,0]}
    return p


def contato_cauda(m):
    c=m.cubo('tail_base');a=np.array([(c.de[0]+c.ate[0])/2,c.de[1],c.ate[2]])
    return bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,bbmodelo.matrizes_ossos(m)),[a])[0]


def corpo_cauda(m,t):
    phi=C(t,[(0,0),(.18,8),(.36,18),(.50,24),(.70,24),(.94,10),(1.16,4),(1.55,0)])
    tau=C(t,[(0,0),(.18,12),(.36,35),(.70,35),(.94,45),(.98,45),(1.16,12),(1.55,0)])
    w=C(t,[(0,0),(.28,0),(.34,1),(.98,1),(1.18,0),(1.55,0)])
    regular=np.array([0,C(t,[(0,0),(.18,-1.8),(.30,-2),(.95,-2),(1.16,-1.2),(1.55,0)]),C(t,[(0,0),(.2,2),(.36,6),(.95,6),(1.16,3),(1.55,0)])])
    p={'body':{'rotacao':[phi,0,0]},'tail_1':{'rotacao':[tau,0,0]}}
    v=bbmodelo.aplicar(bbmodelo.matrizes_ossos(m,p)['tail_1'],[contato_cauda(m)])[0]
    braco=np.array([0,CHAO-v[1],25-v[2]])
    return phi,tau,(1-w)*regular+w*braco,w


def alvo_cauda(m,t,lado,bp,phi):
    c=centro_pe(m,lado);a=c.copy()
    if t<.34:
        ini,fim=(.03,.16) if lado=='right' else (.16,.30)
        a[2]+=C(t,[(0,0),(ini,0),(fim,4),(.34,4)])
        if ini<t<fim:a[1]+=.9*math.sin(math.pi*(t-ini)/(fim-ini))**2
        return a,0
    if t>.94:
        ini,fim=(1.04,1.24) if lado=='right' else (1.22,1.46)
        a[2]+=C(t,[(.94,4),(ini,4),(fim,0),(1.55,0)])
        if ini<t<fim:a[1]+=.9*math.sin(math.pi*(t-ini)/(fim-ini))**2
        return a,0
    b=m.ossos['body'].origem
    h=b+bp+bbmodelo.matriz_rotacao([phi,0,0])@(m.ossos['leg_'+lado].origem-b)
    tuck=np.array([c[0],h[1]-10.5,h[2]-8])
    hit=np.array([math.copysign(3.8,c[0]),h[1]-.7,h[2]-17.5])
    entrada=C(t,[(.34,0),(.46,1),(.94,1)])
    golpe=C(t,[(.34,0),(.46,0),(.60,1),(.66,1),(.79,0),(.94,0)])
    saida=C(t,[(.34,0),(.80,0),(.94,1)])
    ancora=c+np.array([0,0,4])
    a=(1-entrada)*ancora+entrada*((1-golpe)*tuck+golpe*hit)
    a=(1-saida)*a+saida*ancora
    ang=C(t,[(.34,0),(.46,8),(.60,60),(.66,60),(.79,8),(.94,0)])
    return a,ang


def pose_cauda(m,t):
    phi,tau,bp,w=corpo_cauda(m,t)
    p=base_pose(m,[phi,0,0],bp,-phi*.3,0)
    colocar_pernas(m,p,{l:alvo_cauda(m,t,l,bp,phi) for l in ['left','right']})
    p['tail_1']={'rotacao':[tau,0,0]}
    subir=C(t,[(0,0),(.18,.4),(.36,1),(.98,1),(1.20,.55),(1.45,0),(1.55,0)])
    folhas_cauda(m,p,subir,'up')
    alinhar_penas_pernas(m,p,subir)
    for lado,s in [('left',1),('right',-1)]:
        p['arm_'+lado]={'rotacao':[-phi*.35,0,-s*5*subir]}
        p['forearm_'+lado]={'rotacao':[-phi*.65,0,0]}
    return p


def pose(m,nome,t):
    return {'attack_stomp':pose_pisao,'attack_spin':pose_giro,'attack_tail_kick':pose_cauda}[nome](m,float(t))


def superficie_opaca(m,c,cantos=True):
    if np.all(c.tamanho>1e-5):return bbmodelo.cantos(c)
    mascara,eixos=roblox_infra.mascara_plano(m,c)
    y,x=np.nonzero(mascara)
    pontos=[]
    for dx,dy in ([(0,0),(0,1),(1,0),(1,1)] if cantos else [(.5,.5)]):
        p=np.tile(c.de,(len(x),1))
        p[:,eixos[0]]+=(x+dx)/mascara.shape[1]*c.tamanho[eixos[0]]
        p[:,eixos[1]]+=(y+dy)/mascara.shape[0]*c.tamanho[eixos[1]]
        pontos.append(p)
    return np.concatenate(pontos)


def medir(m):
    out={}
    superficies={c.uuid:superficie_opaca(m,c) for c in m.cubos}
    for nome,d in CLIPES.items():
        minimo=(100.,None,None);erros=[];rotmax=0
        for t in np.linspace(0,d,int(round(d*FPS))+1):
            try:p=pose(m,nome,float(t))
            except ValueError as e:erros.append((round(float(t),4),str(e)));continue
            mats=bbmodelo.matrizes_ossos(m,p)
            for c in m.cubos:
                y=float(bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mats),superficies[c.uuid])[:,1].min())
                if y<minimo[0]:minimo=(y,float(t),c.nome)
            rotmax=max(rotmax,max(np.linalg.norm(v.get('rotacao',[0,0,0])) for n,v in p.items() if n!='combat_pivot'))
        out[nome]={'minimo_y':minimo,'alcance_erros':erros,'rotacao_max':float(rotmax)}
    return out


def continuidade(vs):
    saida=[np.array(vs[0],float)]
    for v in vs[1:]:
        v=np.array(v,float);alt=np.array([v[0]+180,180-v[1],v[2]+180])
        cand=[x+360*np.round((saida[-1]-x)/360) for x in [v,alt]]
        saida.append(min(cand,key=lambda x:np.linalg.norm(x-saida[-1])))
    return np.array(saida)


def main():
    pa=argparse.ArgumentParser(description=__doc__);pa.add_argument('--medir',action='store_true');pa.add_argument('--refazer',action='store_true')
    args=pa.parse_args();sha=base.v2.base.sha;original=sha(FONTE)
    m=bbmodelo.ler(FONTE);ops=preparar_rig(m);med=medir(m)
    if args.medir:
        for n,r in med.items():print(n,'mínimo',r['minimo_y'],'alcance',r['alcance_erros'][:5])
        return
    if any(r['alcance_erros'] or r['minimo_y'][0]<CHAO-.025 for r in med.values()):
        raise SystemExit('Corrigir o alcance/chão antes de gerar os clipes.')
    prov=PASTA/'proveniencia.json'
    if SAIDA.exists():
        velho=json.loads(prov.read_text(encoding='utf-8')) if prov.exists() else {}
        if not args.refazer or velho.get('saida_sha256')!=sha(SAIDA) or velho.get('fonte_sha256')!=original:
            raise SystemExit('Proposta existente/editada preservada; criar nova versão.')
    assert sha(FONTE)==original
    PASTA.mkdir(exist_ok=True)
    for nome,d in CLIPES.items():
        ops.append({'op':'add_animation','name':nome,'length':d,'loop':'once','snapping':FPS})
        tt=np.linspace(0,d,int(round(d*FPS))+1);ps=[pose(m,nome,float(t)) for t in tt]
        for n in m.ossos:
            for canal,campo in [('rotation','rotacao'),('position','posicao')]:
                if canal=='position' and n!='body':continue
                vs=np.array([p.get(n,{}).get(campo,[0,0,0]) for p in ps],float)
                if canal=='rotation' and n!='combat_pivot':vs=continuidade(vs)
                inds=[0,len(tt)-1] if np.max(abs(vs-vs[0]))<1e-9 else range(len(tt))
                for i in inds:ops.append({'op':'set_keyframe','animation':nome,'bone':n,'channel':canal,
                    'time':round(float(tt[i]),6),'value':vs[i].round(6).tolist(),'interpolation':'linear'})
    (PASTA/'combate.ops.json').write_text(json.dumps(ops,separators=(',',':'))+'\n',encoding='utf-8')
    shutil.copy2(FONTE,SAIDA);assert sha(SAIDA)==original;motor.editar(SAIDA,ops)
    novo=bbmodelo.ler(SAIDA);antes=bbmodelo.ler(FONTE)
    assert novo.bruto['elements']==antes.bruto['elements'] and novo.bruto['textures']==antes.bruto['textures']
    atuais={c.uuid:c for c in novo.cubos}
    for c in antes.cubos:np.testing.assert_allclose(bbmodelo.caixa_mundo(antes,c),bbmodelo.caixa_mundo(novo,atuais[c.uuid]),atol=1e-8)
    for a in antes.animacoes:
        b=copy.deepcopy(a)
        for v in b.get('animators',{}).values():v.setdefault('keyframes',[])
        assert b==next(v for v in novo.animacoes if v['uuid']==a['uuid'])
    assert sha(FONTE)==original
    prov.write_text(json.dumps({'fonte':FONTE.relative_to(RAIZ).as_posix(),'fonte_sha256':original,
        'saida_sha256':sha(SAIDA),'clipes':CLIPES,'fps':FPS,'operacoes':len(ops),'grupos':len(novo.ossos)},indent=2)+'\n',encoding='utf-8')
    (PASTA/'medidas-planejadas.json').write_text(json.dumps(med,indent=2)+'\n',encoding='utf-8')
    (PASTA/'animacoes.json').write_text(json.dumps({'attack_stomp':{'HitFrame':.575,'RecoveryStart':.74,'CancelOpen':.99},
        'attack_spin':{'HitFrame':.58,'RecoveryStart':.80,'CancelOpen':1.15},
        'attack_tail_kick':{'HitFrame':.60,'RecoveryStart':.79,'CancelOpen':1.24}},indent=2)+'\n',encoding='utf-8')
    print('Criados',len(CLIPES),'clipes em',SAIDA.relative_to(RAIZ),';',len(ops),'operações.')


if __name__=='__main__':main()
