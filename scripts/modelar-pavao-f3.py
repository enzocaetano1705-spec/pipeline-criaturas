"""F3 original a partir das quatro vistas: volumes grandes, penas recortadas e rig editável.

Escrita exclusivamente por operações do motor. A saída editada pelo usuário é protegida.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image
from criaturas import bbmodelo, motor, ops, render, texturizar

RAIZ=Path(__file__).resolve().parents[1]
PASTA=RAIZ/'modelos/criatura-pavao/f3'
ARQUIVO=PASTA/'criatura-pavao-e3.bbmodel'
sp=importlib.util.spec_from_file_location('pintura_pavao',RAIZ/'modelos/criatura-pavao/f2/gerar-f2.py')
g2=importlib.util.module_from_spec(sp);sp.loader.exec_module(g2)

def rgb(h):return np.array(tuple(bytes.fromhex(h.lstrip('#'))),dtype=np.uint8)
TEAL=[rgb(h) for h in ['#06364c','#045575','#016386','#01708b','#0095a1','#02afb1','#03c1bd','#5edbc7']]
GREEN=[rgb(h) for h in ['#075a64','#067e7b','#099b8c','#21b798','#3fc698','#73d6ad','#aae7c5']]
CREAM=[rgb(h) for h in ['#97875f','#b7a16e','#d7c99d','#ead498','#fee7a8','#feecb1','#fff4ce']]
DARK=[rgb(h) for h in ['#061a25','#102c3a','#1c3e50','#315568','#557585']]
GOLD=[rgb(h) for h in ['#9b5c08','#e8a313','#ffd747','#fff3aa']]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def euler(r):
    y=math.asin(float(np.clip(-r[2,0],-1,1)))
    if abs(math.cos(y))>1e-8:x,z=math.atan2(r[2,1],r[2,2]),math.atan2(r[1,0],r[0,0])
    else:x,z=math.atan2(-r[1,2],r[1,1]),0
    return np.degrees([x,y,z]).tolist()

def alinhar(a,b):
    a=np.array(a,float);b=np.array(b,float);a/=np.linalg.norm(a);b/=np.linalg.norm(b)
    v=np.cross(a,b);c=float(np.clip(a@b,-1,1));s=np.linalg.norm(v)
    if s<1e-9:return np.eye(3) if c>0 else np.diag([1,-1,-1])
    k=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
    return np.eye(3)+k+k@k*((1-c)/(s*s))


def construir():
    bones=[];cubes=[];meta={}
    def bone(n,p,a):bones.append({'nome':n,'pai':p,'pivo':list(a)})
    def cube(n,p,a,b,rotation=None,origin=None,kind='body'):
        c={'nome':n,'osso':p,'from':list(a),'to':list(b)}
        if rotation is not None:c.update(rotation=list(rotation),origin=list(origin))
        cubes.append(c);meta[n]={'kind':kind}
    def segment(n,p,a,b,w,d,kind='body'):
        a=np.array(a,float);b=np.array(b,float);length=float(np.linalg.norm(b-a))
        cube(n,p,a+[-w/2,-length,-d/2],a+[w/2,0,d/2],euler(alinhar([0,-1,0],b-a)),a,kind)
    def leaf(n,p,a,w,l,rot=(0,0,0),kind='feather',plane='xy'):
        a=np.array(a,float)
        if plane=='xy':lo=a+[-w/2,-l,0];hi=a+[w/2,0,0]
        else:lo=a+[-w/2,0,0];hi=a+[w/2,0,l]
        cube(n,p,lo,hi,rot,a,kind);meta[n].update(plane=plane,w=w,l=l)

    bone('root',None,[0,0,0]);bone('body','root',[0,28,1])
    bone('pelvis','body',[0,28,1]);cube('hips','pelvis',[-5,25,-2.5],[5,30,4])
    bone('waist','pelvis',[0,29,0]);cube('abdomen','waist',[-4,29,-2.7],[4,36,3.1])
    bone('chest','waist',[0,35,0]);cube('torso','chest',[-6.5,35,-3.5],[6.5,43,3.7])
    bone('neck_1','chest',[0,42,-.5]);cube('neck_lower','neck_1',[-2.6,42,-2.7],[2.6,47,2])
    bone('neck_2','neck_1',[0,46,-1]);cube('neck_upper','neck_2',[-2.5,46,-3.4],[2.5,50,1.5])
    bone('head','neck_2',[0,49,-2.5]);cube('skull','head',[-3.5,48.5,-5.5],[3.5,55,1])
    cube('beak','head',[-2.2,47.3,-9],[2.2,50,-5.2],kind='beak')
    cube('beak_hook','head',[-1.1,46.5,-10],[1.1,48,-8.2],kind='beak')

    for side,s in [('left',-1),('right',1)]:
        shoulder=np.array([s*6.7,41.8,0]);elbow=np.array([s*11.5,33.5,.5]);wrist=np.array([s*14,26,-.5])
        bone('arm_'+side,'chest',shoulder);segment('upper_arm_'+side,'arm_'+side,shoulder,elbow,3.5,3.5)
        bone('forearm_'+side,'arm_'+side,elbow);segment('lower_arm_'+side,'forearm_'+side,elbow,wrist,3.2,3.3)
        bone('hand_'+side,'forearm_'+side,wrist);cube('palm_'+side,'hand_'+side,[s*14-1.7,22.8,-2],[s*14+1.7,26.2,1.0],kind='hand')
        for j in range(3):
            a=np.array([s*(14+(j-1)*1.05),23.1,-1.0]);b=a+[0,-2.0,-.7];tip=b+[0,.25,-1.0]
            n=f'finger_{side}_{j+1}';bone(n,'hand_'+side,a)
            segment(n+'_a',n,a,b,.9,1.1,'hand');segment(n+'_b',n,b,tip,.8,1.0,'hand')
        a=np.array([s*12.5,25.2,-.3]);b=a+[-s*.9,-1.8,-.7];n='thumb_'+side
        bone(n,'hand_'+side,a);segment(n+'_a',n,a,b,1.0,1.2,'hand');segment(n+'_b',n,b,b+[s*.7,-.6,-.8],.8,1.0,'hand')
        # Trois lâminas em cada antebraço; raiz no sólido, ponta além dos dedos.
        for j,(w,l,z,angle) in enumerate([(9,28,1.5,24),(8,24,1.5,14),(6,18,1.5,10)],1):
            a=elbow+[s*1.0,.1,z];n=f'arm_blade_{side}_{j}';bone(n,'forearm_'+side,a)
            leaf(n+'_plane',n,a,w,l,(0,s*28,s*angle),'blade')
        for j,(w,l,x,ang) in enumerate([(7,9,6.3,65),(5,8,7.0,92)],1):
            leaf(f'shoulder_plume_{side}_{j}','chest',[s*x,42.8,1.2+j*.25],w,l,(0,-s*25,s*ang),'tuft')
        leaf('hip_plume_'+side,'pelvis',[s*4.6,28.7,-.2],6,14,(0,-s*20,s*15),'tuft')
        # Z digitígrado: joelho anterior, jarrete posterior e tarso alto.
        hip=np.array([s*4,27,.5]);knee=np.array([s*7.5,17,-1.4]);ankle=np.array([s*8.7,7,3.2]);base=np.array([s*8.7,1.5,0])
        bone('leg_'+side,'pelvis',hip);segment('thigh_'+side,'leg_'+side,hip,knee,5.0,5.0)
        bone('shin_'+side,'leg_'+side,knee);segment('shank_'+side,'shin_'+side,knee,ankle,3.0,3.2)
        bone('foot_'+side,'shin_'+side,ankle);segment('tarsus_'+side,'foot_'+side,ankle,base,2.4,2.6)
        cube('foot_pad_'+side,'foot_'+side,[s*8.7-2.0,.6,-1.7],[s*8.7+2,2.2,1.5])
        for j in range(3):
            a=base+[s*(j-1)*1.1,-.1,-.7];b=base+[s*(j-1)*2.25,-.5,-6.1+(abs(j-1)*.4)]
            segment(f'toe_{side}_{j+1}','foot_'+side,a,b,1.6,1.6)
            c=b+[s*.18*(j-1),.3,-1.6];d=c+[s*.18*(j-1),-.8,-1.8]
            segment(f'claw_{side}_{j+1}_base','foot_'+side,b,c,1.7,1.5,'claw')
            segment(f'claw_{side}_{j+1}_tip','foot_'+side,c,d,.9,1.0,'claw')
        a=base+[s*1.4,-.1,.8];b=a+[s*.8,-.2,3.0]
        segment('toe_'+side+'_back','foot_'+side,a,b,1.3,1.4)
        segment('claw_'+side+'_back','foot_'+side,b,b+[s*.3,-.5,1.2],.8,1.0,'claw')
        for j in range(2):
            a=np.array([s*9.3,12-j*.8,2.2+j*.8]);n=f'ankle_plume_{side}_{j+1}'
            bone(n,'shin_'+side,a);leaf(n+'_plane',n,a,3.5,5.5-j*.3,(0,s*45,s*(34+12*j)),'tuft')
        # Cabeça/crina: cartões laterais; não são asas adicionais.
        leaf('cheek_plume_'+side,'head',[s*2.6,53,.4],4,8,(0,-s*25,s*25),'tuft')
        n='neck_frill_'+side
        cube(n,'neck_2',[s*2.3,42,.2],[s*2.3,52,6.5],kind='frill');meta[n].update(plane='yz',w=6.3,l=10)
        # Plumas arqueadas: duas, sobrepostas quando observadas no perfil.
        a=np.array([s*1.5,54.2,-.2]);n='crest_'+side;bone(n,'head',a)
        cube(n+'_plane',n,a+[0,-4,0],a+[23,10,0],(0,-40 if s>0 else -140,0),a,'crest')
        meta[n+'_plane'].update(plane='xy',w=23,l=14)

    a=np.array([0,27.5,3.3]);b=np.array([0,23.5,12.5]);c=np.array([0,20,21]);d=np.array([0,17,27])
    for n,parent,start,end,w,dep in [('tail_1','pelvis',a,b,7,6),('tail_2','tail_1',b,c,5.5,5.0),('tail_3','tail_2',c,d,4,4)]:
        bone(n,parent,start);segment(n+'_solid',n,start,end,w,dep)
    # Leque em seis penas originais, escalonadas; raiz inserida na parte sólida.
    fans=[(0,25,16,38,0,0),(0,22,16,24,0,0),(-1,24,15,35,-22,-12),(1,24,15,35,22,12),(-1,22,13,34,-42,-18),(1,22,13,34,42,18)]
    for i,(s,l,w,pitch,yaw,roll) in enumerate(fans,1):
        root=[0,23.9,18.2] if i==2 else [s*.6,18.2,25.0]
        # Torce a folha ao redor do próprio eixo longo: visível de frente E de perfil.
        r0=bbmodelo.matriz_rotacao([pitch,yaw,roll]);axis=r0[:,2];x,y,z=axis
        skew=np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
        twist=math.radians((55 if i==1 else -25 if i==2 else 45*(1 if s>0 else -1)))
        rotation=(np.eye(3)+math.sin(twist)*skew+(1-math.cos(twist))*skew@skew)@r0
        n=f'tail_fan_{i:02d}';bone(n,'tail_2' if i==2 else 'tail_3',root);leaf(n+'_plane',n,root,w,l,euler(rotation),'fan','xz')
    locs=[('loc_ground','root',[0,0,0]),('loc_center','body',[0,31,0]),('loc_head_look','head',[0,52,-6]),
          ('loc_mouth','head',[0,48,-10]),('loc_tail_tip','tail_3',[0,3,45])]
    for side,s in [('left',-1),('right',1)]:
        locs.extend([('loc_hand_'+side,'hand_'+side,[s*14,23,-1]),('loc_foot_'+side,'foot_'+side,[s*8.7,1,-5])])
    return bones,cubes,meta,locs


def leaf_color(info,c,p):
    size=c.ate-c.de;kind=info['kind'];plane=info['plane'];w,l=info['w'],info['l']
    if plane=='yz':
        u=(p[2]-c.de[2])/size[2];v=(c.ate[1]-p[1])/size[1]
        edge=.60+.30*math.sin(math.pi*v)+.10*(1-(v*5)%1)
        if not (0<=v<=1 and 0<=u<edge):return None
        return TEAL[2 if u>.6 else 4 if int(v*8)%2 else 3]
    u=(p[0]-c.de[0])/max(size[0],1e-9)
    if kind=='crest':
        q=np.array([u*23,p[1]-c.de[1]])
        ts=np.linspace(0,1,96);p0=np.array([0,4]);p1=np.array([3,15]);p2=np.array([13,15]);p3=np.array([22,0])
        path=(1-ts[:,None])**3*p0+3*(1-ts[:,None])**2*ts[:,None]*p1+3*(1-ts[:,None])*ts[:,None]**2*p2+ts[:,None]**3*p3
        idx=int(np.argmin(np.linalg.norm(path-q,axis=1)));t=float(ts[idx]);dist=float(np.linalg.norm(path[idx]-q))
        width=.65+3.0*math.exp(-((t-.76)/.19)**2)
        width*=max(.0,min(1,(1-t)/.10)) if t>.90 else 1
        if dist>width:return None
        e=((t-.73)/.085)**2+(dist/1.35)**2
        if e<.40:return rgb('#03263e')
        if e<1:return rgb('#00638c')
        if t>.84:return CREAM[4 if dist<width*.7 else 3]
        return GREEN[4] if t>.6 else TEAL[5 if dist<width*.6 else 2]
    v=((c.ate[1]-p[1])/max(size[1],1e-9)) if plane=='xy' else (p[2]-c.de[2])/max(size[2],1e-9)
    if not (0<=v<=1):return None
    x=(u-.5)*w
    half=(w/2)*(.16+.84*math.sin(math.pi*v)**.65)*(1-.20*v)
    half=min(half,w*max(0,1-v)*2.2)
    half-=.30*(1-(v*l/2)%1)
    if abs(x)>max(.25,half):return None
    if kind=='fan':
        e=(x/(w*.24))**2+((v-.64)/.115)**2
        if e<.32:return rgb('#03263e')
        if e<1:return rgb('#00638c')
        if e<1.5:return TEAL[2]
    cream=v>(.56+.22*(1-abs(x)/max(half,.01))) if kind in ['blade','tuft'] else v>.82-.10*abs(x)/max(half,.01)
    if c.nome.startswith(('shoulder_plume_','cheek_plume_')):cream=False
    if cream:return CREAM[3 if abs(x)>half-.5 else 4 if int(x+v*6)%3 else 5]
    k=int(v*l/2)+int(abs(x)/2)
    if abs(x)>half-.45:return TEAL[1]
    if kind=='blade':return GREEN[4] if abs(x)<half*.3 and v>.4 else TEAL[4+(k%3==0)]
    return GREEN[3+k%2] if v>.48 else TEAL[3+k%3]


def solid_color(c,face,p):
    n=c.nome;x,y,z=p;de,ate=c.de,c.ate;rel=(p-de)/np.maximum(ate-de,1e-8)
    if n.startswith(('claw','finger','thumb','palm')):
        return DARK[3 if face=='up' else 2 if face in ['north','east'] else 1]
    if n.startswith('beak'):
        if face in ['east','west'] and rel[1]<.20:return DARK[0]
        return CREAM[5 if face=='up' else 4 if face=='north' else 3]
    a,b=g2._coords(face,x,y,z);seed=sum(map(ord,n))
    value={'up':.6,'down':-1.2}.get(face,0)+(.35 if rel[1]>.6 else -.3)
    ramp=TEAL
    if n in ['hips','abdomen','torso','neck_lower','neck_upper']:
        cream=face=='north' and abs(x)<(2.3 if n.startswith('neck') else 2.2+.9*rel[1])
        if cream:ramp=CREAM
        elif face=='south' and abs(x)<1.2:ramp=TEAL[:4]+[TEAL[3]]*4
    if n=='skull':
        if face in ['north','east','west']:
            q=abs(x)-1.4 if face=='north' else z+5.5
            if 0<=q<3 and 50.1<=y<53.0:
                row=int(52.99-y);col=int(q)
                tile=['KKK','GPK','_GG'][min(2,row)][min(2,col)]
                if tile=='K':return DARK[0]
                if tile=='P':return rgb('#ffe888') if face=='north' else DARK[0]
                if tile=='G':return GOLD[2 if col==0 else 1]
        if face=='north' and abs(x)<1.2 and 52<=y<=55:
            if abs(x)/1.2+abs(y-53.6)/1.5<1.1:return GOLD[3 if x>0 else 1]
        if face=='north' and y<50.2:ramp=CREAM
    if n.startswith('tail_'):ramp=TEAL
    if n.startswith(('toe_','tarsus_')):return g2.plumagem(TEAL,a,b,value*.5,seed,suave=True)
    return g2.plumagem(ramp,a,b,value,seed,suave=ramp is CREAM)


def pintar(modelo,meta):
    res=modelo.resolucao[0];tex=np.zeros((res,res,4),dtype=np.uint8)
    for c in modelo.cubos:
        info=meta[c.nome]
        for face in ['north','south','east','west','up','down']:
            rows=texturizar.texels_da_face(c,face,np.eye(4))
            if rows is None:continue
            for (u,v),p in zip(*rows):
                color=leaf_color(info,c,p) if info['kind'] in ['blade','fan','crest','tuft','frill'] else solid_color(c,face,p)
                if color is not None and 0<=u<res and 0<=v<res:tex[int(v),int(u),:3]=color;tex[int(v),int(u),3]=255
    return tex


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--refazer',action='store_true');args=ap.parse_args()
    PASTA.mkdir(exist_ok=True);prov=PASTA/'proveniencia.json'
    if ARQUIVO.exists():
        old=json.loads(prov.read_text()) if prov.exists() else {}
        if not args.refazer or old.get('saida_sha256')!=sha(ARQUIVO):raise SystemExit('Modelo existente/editado preservado; criar versão nova.')
    bones,cubes,meta,locs=construir();offsets,(res,_)=ops.distribuir_uv(cubes,margem=1,larguras=(128,256))
    # Criação/sobrescrita somente após proteção por hash, nunca texto .bbmodel artesanal.
    batch=[]
    for b in bones:batch.append({'op':'add_group','name':b['nome'],'origin':b['pivo'],**({'parent':b['pai']} if b['pai'] else {})})
    for c in cubes:
        o={'op':'add_cube','name':c['nome'],'parent':c['osso'],'from':c['from'],'to':c['to'],'box_uv':True,'uv_offset':offsets[c['nome']]}
        if 'rotation' in c:o.update(rotation=c['rotation'],origin=c['origin'])
        batch.append(o)
    for n,p,a in locs:batch.append({'op':'add_locator','name':n,'parent':p,'position':a})
    batch=json.loads(json.dumps(batch,default=lambda x:x.item() if isinstance(x,np.generic) else x.tolist()))
    (PASTA/'geometria.ops.json').write_text(json.dumps(batch,indent=1)+'\n',encoding='utf-8')
    motor.criar(ARQUIVO,'criatura-pavao-e3',res,res)
    motor.editar(ARQUIVO,batch);m=bbmodelo.ler(ARQUIVO);tex=pintar(m,meta)
    Image.fromarray(tex).save(PASTA/'textura.png');texturizar.aplicar_no_modelo(ARQUIVO,tex,m,[])
    m=bbmodelo.ler(ARQUIVO)
    (PASTA/'plano-cubos.json').write_text(json.dumps({'ossos':bones,'cubos':cubes,'materiais':meta,'locators':locs,'atlas':res},indent=1,default=lambda x:x.item() if isinstance(x,np.generic) else x.tolist())+'\n',encoding='utf-8')
    prov.write_text(json.dumps({'saida_sha256':sha(ARQUIVO),'imagens_fonte':'imagens-fonte.json','pecas':len(cubes),'ossos':len(bones),'atlas':res,'status':'primeira-proposta-aguarda-aprovacao','modelagem':'poucas_formas; planos recortados para plumagem; volumes sólidos nas articulações'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    render.folha(m,lado_px=384,titulo='Pavao F3 | prototipo editavel | 3 de 3').save(PASTA/'folha.png')
    print(ARQUIVO.name,len(cubes),'peças;',len(bones),'ossos; atlas',res,'px; folha 768px.')


if __name__=='__main__':main()
