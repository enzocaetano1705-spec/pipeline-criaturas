"""F3: edição manual preservada, marcha aviana e saque das penas 04/06.

Geometria, rig, pintura e chaves são gravados apenas pelo motor externo.
Os controladores das armas assam o vínculo cauda/mão; nenhuma peça é duplicada.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from criaturas import bbmodelo, motor, render, texturizar

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'modelos/criatura-pavao/f3/animacoes-v1'
SOURCE = OUT / 'origem-manual.bbmodel'
FILE = OUT / 'criatura-pavao-e3-animacoes-v1b.bbmodel'
FPS = 60
CLIPS = {'idle':3.2, 'walk':1.5, 'combat_enter':3.4,
         'combat_idle':3.0, 'combat_walk':1.8, 'combat_exit':2.8,
         'combat_walk_start':.8, 'combat_walk_stop':.8}
LOOPS = {'idle','walk','combat_idle','combat_walk'}
sp=importlib.util.spec_from_file_location('formas_f3', ROOT/'scripts/modelar-pavao-f3.py')
forms=importlib.util.module_from_spec(sp);sp.loader.exec_module(forms)


def dump(p,data):
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2,
        default=lambda a:a.tolist() if isinstance(a,np.ndarray) else a.item())+'\n',encoding='utf-8')


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unit(v):
    v=np.asarray(v,float);return v/max(np.linalg.norm(v),1e-12)
def R(v):return bbmodelo.matriz_rotacao(v)
def point(mat,v):return bbmodelo.aplicar(mat,[v])[0]
def smooth(x):
    x=float(np.clip(x,0,1));return x*x*x*(x*(6*x-15)+10)
def blend(a,b,w):return np.asarray(a)*(1-w)+np.asarray(b)*w


def curve(t,keys):
    if t<=keys[0][0]:return np.asarray(keys[0][1],float)
    if t>=keys[-1][0]:return np.asarray(keys[-1][1],float)
    for (a,x),(b,y) in zip(keys,keys[1:]):
        if a<=t<=b:return blend(x,y,smooth((t-a)/(b-a)))


def slerp(a,b,w):
    if w<=0:return a.copy()
    if w>=1:return b.copy()
    d=a.T@b;angle=math.acos(float(np.clip((np.trace(d)-1)/2,-1,1)))
    if angle<1e-7:return a.copy()
    if math.pi-angle<1e-5:
        _,v=np.linalg.eigh((d+np.eye(3))/2);axis=v[:,-1]
    else:axis=unit([d[2,1]-d[1,2],d[0,2]-d[2,0],d[1,0]-d[0,1]])
    x,y,z=axis;k=np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
    return a@(np.eye(3)+math.sin(w*angle)*k+(1-math.cos(w*angle))*(k@k))


def continuous_euler(values):
    """Escolhe também a representação Euler equivalente ao cruzar ±90° em Y."""
    out=[np.asarray(values[0],float)]
    for v in values[1:]:
        v=np.asarray(v,float);alt=np.array([v[0]+180,180-v[1],v[2]+180])
        choices=[a+360*np.round((out[-1]-a)/360) for a in [v,alt]]
        out.append(min(choices,key=lambda a:np.linalg.norm(a-out[-1])))
    return np.asarray(out)


def frame(direction,normal):
    y=unit(direction);z=unit(np.asarray(normal)-y*np.dot(y,normal));x=unit(np.cross(y,z))
    return np.column_stack([x,y,z])


def endpoints(m,c):
    p=np.tile((c.de+c.ate)/2,(2,1));p[:,1]=[c.ate[1],c.de[1]]
    return bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,bbmodelo.matrizes_ossos(m)),p)


def prepare():
    src=bbmodelo.ler(SOURCE)
    if src.animacoes:raise ValueError('A origem já contém clipes: revisar em outra versão.')
    if FILE.exists():
        old=OUT/'validacao.json'
        if not old.exists() or json.loads(old.read_text(encoding='utf-8')).get('saida_sha256')!=sha(FILE):
            raise ValueError('A saída mudou fora do gerador; crie uma nova versão.')
    shutil.copy2(SOURCE,FILE)
    ops=[]
    def pivot(n,p):ops.append({'op':'update_node','target':n,'origin':np.asarray(p).tolist()})
    lower=src.cubo('neck_lower_avian');top,bottom=endpoints(src,lower)
    pivot('neck_1',bottom);pivot('neck_2',top);pivot('head',top)
    for side in ['left','right']:
        elbow,shoulder=endpoints(src,src.cubo('upper_arm_'+side))
        wrist,elbow2=endpoints(src,src.cubo('forearm_solid_'+side))
        pivot('arm_'+side,shoulder);pivot('forearm_'+side,(elbow+elbow2)/2)
        pivot('hand_'+side,wrist);pivot('wing_'+side,(elbow+elbow2)/2)
        hip,knee=endpoints(src,src.cubo('thigh_'+side))
        knee2,hock=endpoints(src,src.cubo('shank_'+side))
        hock2,_=endpoints(src,src.cubo('tarsus_'+side))
        pivot('leg_'+side,hip);pivot('shin_'+side,(knee+knee2)/2);pivot('foot_'+side,(hock+hock2)/2)
    for n in ['tail_fan_04','tail_fan_06']:
        stem=src.cubo(n+'_plane_stem');a,b=endpoints(src,stem);grip=(a+b)/2
        ops.append({'op':'update_node','target':n,'origin':grip.tolist(),'parent':'body'})
    # Nova ilha por face, sem tocar as regiões anteriores nem UVs de outras peças.
    # O pescoço foi repintado: remapear o antigo bloco sólido não restauraria o padrão.
    neck=src.cubo('neck_lower_avian');faces=copy.deepcopy(neck.faces)
    used=np.zeros((512,512),bool)
    for c in src.cubos:
        for f in c.faces.values():
            u,v,a,b=f['uv'];x0,x1=sorted([int(math.floor(u)),int(math.ceil(a))]);y0,y1=sorted([int(math.floor(v)),int(math.ceil(b))])
            used[max(0,y0-1):min(512,y1+1),max(0,x0-1):min(512,x1+1)]=True
    tex=np.array(src.textura).copy();x=256;y=300
    palette=np.array([[31,98,113],[42,105,118],[43,133,144],[63,154,154],[75,187,186]],np.uint8)
    cream=np.array([[183,161,110],[207,194,152],[230,220,182],[243,236,208]],np.uint8)
    for i,(name,f) in enumerate(faces.items()):
        size={'north':(5,8),'south':(5,8),'east':(3,8),'west':(3,8),'up':(5,3),'down':(5,3)}[name]
        w,h=size
        while used[y:y+h+2,x:x+w+2].any():
            x+=1
            if x+w+2>512:x=256;y+=12
            if y+h+2>512:raise ValueError('Sem espaço reservado para o pescoço.')
        f['uv']=[x+1,y+1,x+1+w,y+1+h];f['texture']=0
        for row in range(h):
            for col in range(w):
                # Manchas de 1–2 pixels na mesma rampa do corpo; faixa ventral creme.
                idx=(col//2+2*(row//2)+i)%5
                color=palette[idx]
                if name=='north' and abs(col-(w-1)/2)<=1+(row%3==0):color=cream[(row//2+col)%4]
                elif name in ['east','west'] and col==w-1 and row%3!=0:color=cream[(row//2)%4]
                tex[y+1+row,x+1+col]=[*color,255]
        used[y:y+h+2,x:x+w+2]=True;x+=w+3
    # Remover/repor apenas o cubo elimina Box UV automático mantendo UUID e forma.
    ops.extend([{'op':'remove_node','target':neck.uuid},
        {'op':'add_cube','name':neck.nome,'uuid':neck.uuid,'parent':neck.osso,
         'from':neck.de.tolist(),'to':neck.ate.tolist(),'origin':neck.origem.tolist(),
         'rotation':neck.rotacao.tolist(),'inflate':neck.inflate,'box_uv':False,'faces':faces},
        {'op':'update_texture','target':0,'source':texturizar._data_url(tex),'width':512,'height':512,'material':None},
        {'op':'set_model_properties','name':FILE.stem}])
    dump(OUT/'ops-preparo.json',ops);motor.editar(FILE,ops)
    Image.fromarray(tex).save(OUT/'textura.png')
    return bbmodelo.ler(FILE)


class Rig:
    def __init__(self,m):
        self.m=m;self.source=bbmodelo.ler(SOURCE);self.rest=bbmodelo.matrizes_ossos(m)
        self.feet={};self.grips={};self.weapons={};self.max_unreachable=0;self.reach={}
        for side,s,n in [('left',-1,'tail_fan_04'),('right',1,'tail_fan_06')]:
            toes=[c for c in m.cubos if c.nome.startswith('toe_'+side) or c.nome=='foot_base_'+side]
            bounds=np.concatenate([bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,self.rest),bbmodelo.cantos(c)) for c in toes])
            self.feet[side]=np.array([bounds[:,0].mean(),0,bounds[:,2].mean()])
            hand=m.cubo('hand_block_'+side)
            self.grips[side]=point(bbmodelo.matriz_cubo(m,hand,self.rest),(hand.de+hand.ate)/2)
            stem=m.cubo(n+'_plane_stem');a,b=endpoints(m,stem);vane=m.cubo(n+'_plane_vane')
            _,tip=endpoints(m,vane);grip=m.ossos[n].origem.copy()
            r=bbmodelo.matriz_rotacao(stem.rotacao)
            self.weapons[side]={'name':n,'grip':grip,'frame':frame(tip-grip,r[:,2]),
                                'length':float(np.linalg.norm(tip-grip)), 's':s}

    def blank(self):return {n:{'rotacao':[0.,0.,0.]} for n in self.m.ossos}
    def mats(self,p):return bbmodelo.matrizes_ossos(self.m,p)
    def set_world(self,p,name,rot):
        o=self.m.ossos[name];parent=self.mats(p)[o.pai][:3,:3] if o.pai else np.eye(3)
        p[name]['rotacao']=forms.euler(parent.T@rot)

    def two_bone(self,p,names,target,pole):
        a,b,c=[self.m.ossos[n].origem for n in names]
        parent=self.mats(p)[self.m.ossos[names[0]].pai]
        hip=point(parent,a);v1=b-a;v2=c-b;l1=np.linalg.norm(v1);l2=np.linalg.norm(v2)
        d=np.asarray(target)-hip;dist=np.linalg.norm(d)
        self.max_unreachable=max(self.max_unreachable,float(dist-(l1+l2)))
        self.reach[names[0]]=max(self.reach.get(names[0],0),float(dist-(l1+l2)))
        dst=float(np.clip(dist,abs(l1-l2)+.01,l1+l2-.005));direction=unit(d)
        pole=np.asarray(pole)-hip;ortho=unit(pole-direction*np.dot(pole,direction))
        along=(l1*l1-l2*l2+dst*dst)/(2*dst);height=math.sqrt(max(0,l1*l1-along*along))
        elbow=hip+direction*along+ortho*height
        # Transporta o plano original da cadeia, evitando torção arbitrária.
        restplane=unit(np.cross(v1,v2));newplane=unit(np.cross(elbow-hip,np.asarray(target)-elbow))
        if np.linalg.norm(restplane)<.5 or np.linalg.norm(newplane)<.5:
            r1=forms.alinhar(v1,elbow-hip)
        else:r1=frame(elbow-hip,newplane)@frame(v1,restplane).T
        self.set_world(p,names[0],r1)
        # Com os dois pivôs alinhados, o último segmento chega exatamente ao alvo.
        r2=frame(np.asarray(target)-elbow,newplane)@frame(v2,restplane).T
        self.set_world(p,names[1],r2)
        return elbow

    def legs(self,p,feet=None,rolls=None):
        for side,s in [('left',-1),('right',1)]:
            target=np.array((feet or self.feet)[side],float);roll=(rolls or {}).get(side,0)
            # Pé inteiro rola em torno do contato; nenhum redimensionamento de ossos.
            footrot=R([roll,0,s*1.5*abs(roll)/20]);hock=self.m.ossos['foot_'+side].origem
            desired_hock=target+footrot@(hock-self.feet[side])
            hip=point(self.mats(p)['pelvis'],self.m.ossos['leg_'+side].origem)
            self.two_bone(p,['leg_'+side,'shin_'+side,'foot_'+side],desired_hock,hip+[s*1.5,0,-20])
            self.set_world(p,'foot_'+side,footrot)

    def arm(self,p,side,grip,handrot,pole):
        wrist=self.m.ossos['hand_'+side].origem
        target=np.asarray(grip)-handrot@(self.grips[side]-wrist)
        self.two_bone(p,['arm_'+side,'forearm_'+side,'hand_'+side],target,pole)
        self.set_world(p,'hand_'+side,handrot)

    def weapon(self,p,side,grip,orient):
        w=self.weapons[side];name=w['name'];parent=self.mats(p)[self.m.ossos[name].pai]
        # Compensa o corpo nas chaves; só body permanece diretamente sob root.
        p[name]={'rotacao':forms.euler(parent[:3,:3].T@orient),
                 'posicao':point(np.linalg.inv(parent),grip)-w['grip']}

    def sheathed(self,p,side):
        w=self.weapons[side];tail=self.mats(p)['tail_1']
        # A mesma geometria acompanha a cauda quando não está empunhada.
        self.weapon(p,side,point(tail,w['grip']),tail[:3,:3])

    def sword_rotation(self,side,direction,normal):
        return frame(direction,normal)@self.weapons[side]['frame'].T

    def body(self,t,combat=0,walking=0,phase=0):
        p=self.blank();a=2*math.pi*phase;breath=math.sin(a if walking else 2*math.pi*t/(3 if combat else 3.2))
        w=walking;c=combat
        # Duas transferências de peso por ciclo, contraposição bacia/peito.
        p['body']={'rotacao':[-5+18*c-2.4*w*math.cos(2*a),2.1*w*math.sin(a),1.7*w*math.sin(a)],
                   'posicao':[.8*w*math.sin(a),-2.2*w+.55*w*math.cos(2*a)+(.14+.28*c)*breath,0]}
        p['pelvis']['rotacao']=[1.3*w*math.cos(2*a),3*w*math.sin(a),-1.8*w*math.sin(a)]
        p['waist']['rotacao']=[.55*breath,-1.9*w*math.sin(a),-.9*w*math.sin(a)]
        p['torso']['rotacao']=[-(.85+1.1*c)*breath, -2.9*w*math.sin(a),-1.1*w*math.sin(a)]
        p['neck_1']['rotacao']=[2.5-8*c+.8*breath+1.1*w*math.cos(2*a-.3),0,0]
        p['neck_2']['rotacao']=[-2*c-.5*breath,0,0]
        # Cabeça parcialmente estabilizada, nunca rigidamente travada no mundo.
        parent=self.mats(p)['neck_2'][:3,:3]
        p['head']['rotacao']=forms.euler(parent.T@R([-1+.45*breath,.7*breath,.35*breath]))
        p['tail_1']['rotacao']=[-7-10*c+1.2*breath+2.2*w*math.cos(2*a-.8),-3.7*w*math.sin(a-.55),-.7*w*math.sin(a-.7)]
        p['tail_2']['rotacao']=[1.2*breath+2*w*math.cos(2*a-1.15),-2*w*math.sin(a-1),0]
        for side,s in [('left',-1),('right',1)]:
            for i in [1,2]:p[f'feather_{side}_{i}']['rotacao']=[.8*breath+1.6*w*math.cos(2*a-.9-i*.3),s*.6*breath,0]
            p['wing_'+side]['rotacao']=[1.1*breath+2*w*math.sin(a-.65)*(s if c else 1),s*.6*breath,0]
            for n in self.m.ossos:
                if n.startswith('back_feathers_'+side) and self.m.ossos[n].pai:
                    # Recolhe a plumagem dorsal para liberar o apoio da espada.
                    p[n]['rotacao']=[45*c+.8*breath+2*w*math.cos(2*a-.6),s*.5*breath,0]
            if not c:
                p['arm_'+side]['rotacao']=[1.5*breath+3*w*s*math.sin(a-.25),s*.5*breath,-s*.6*breath]
                p['forearm_'+side]['rotacao']=[-1.3*breath-2*w*s*math.sin(a-.5),0,0]
        return p

    def peaceful(self,t,walk=False):
        phase=t/CLIPS['walk'] if walk else 0
        p=self.body(t,0,1 if walk else 0,phase)
        feet,rolls=self.walk_feet(phase,False) if walk else (self.feet,{})
        self.legs(p,feet,rolls)
        for side in self.weapons:self.sheathed(p,side)
        return p

    def walk_feet(self,phase,combat):
        feet={};rolls={};stride=8.5 if combat else 10;stance=.66 if combat else .63
        for side,off in [('left',0),('right',.5)]:
            u=(phase+off)%1;v=self.feet[side].copy()
            if u<stance:
                v[2]+=stride*(u/stance-.5)
                roll=0 # apoio completo; a flexão ocorre no tarso acima dele
            else:
                q=(u-stance)/(1-stance)
                # Hermite mantém a velocidade de apoio na saída e na aterrissagem.
                vel=stride*(1-stance)/stance
                z=(2*q**3-3*q*q+1)*stride/2+(q**3-2*q*q+q)*vel+(-2*q**3+3*q*q)*(-stride/2)+(q**3-q*q)*vel
                v[2]+=z;v[1]+=2.2*math.sin(math.pi*q)**2
                roll=-10*math.sin(math.pi*q)**2
            feet[side]=v;rolls[side]=roll
        return feet,rolls

    def combat_targets(self,p,t,walking=0,phase=0):
        mats=self.mats(p);torso=mats['torso'];a=2*math.pi*phase
        targets={}
        # Esquerda: cabo à frente e lâmina pousada atrás sobre o ombro.
        shoulder=point(torso,self.m.ossos['arm_left'].origem)
        grip=shoulder+[-2,3,-6]
        direction=unit([-.025,.12,.99]);rot=self.sword_rotation('left',direction,[-1,.2,0])
        targets['left']=(grip,rot)
        # Direita: ponta enterrada. A direção oblíqua cabe nos braços curtos.
        # No caminhar a espada sobe, permanecendo fora das pernas e da plumagem.
        w=self.weapons['right'];length=w['length']
        grip=np.array([12.4,29.8,-10.8])
        down=unit([.68,-.58,-.44]);rot=self.sword_rotation('right',down,[0,0,1])
        if walking:
            sh=point(torso,self.m.ossos['arm_right'].origem)
            grip=blend(grip,sh+[6,-7,-5],walking)
            grip[1]+=3*math.sin(math.pi*walking)**2
            clear=self.sword_rotation('right',[.95,-.25,0],[0,0,1])
            carried=self.sword_rotation('right',[.35,-.35,.87],[1,0,0])
            if walking<.4:rot=slerp(rot,clear,smooth(walking/.4))
            else:rot=slerp(clear,carried,smooth((walking-.4)/.6))
            rot=R([1.3*walking*math.sin(a-.6),0,0])@rot
        targets['right']=(grip,rot)
        return targets

    def place_combat_arms(self,p,targets):
        for side,s in [('left',-1),('right',1)]:
            grip,rot=targets[side]
            # A face de preensão acompanha a lâmina; o punho não se desprende.
            hr=rot@R([0,0,s*15])
            sh=point(self.mats(p)['torso'],self.m.ossos['arm_'+side].origem)
            self.arm(p,side,grip,hr,sh+[s*7,-14,6])
            self.weapon(p,side,grip,rot)

    def combat(self,t,walk=False,weight=1):
        phase=t/CLIPS['combat_walk'] if walk else 0
        p=self.body(t,1,weight if walk else 0,phase)
        feet,rolls=self.walk_feet(phase,True) if walk else (self.feet,{})
        self.legs(p,feet,rolls)
        self.place_combat_arms(p,self.combat_targets(p,t,weight if walk else 0,phase))
        return p

    def mix_pose(self,a,b,w):
        p=self.blank()
        for n in p:
            p[n]['rotacao']=forms.euler(slerp(R(a[n]['rotacao']),R(b[n]['rotacao']),w))
            if 'posicao' in a[n] or 'posicao' in b[n]:p[n]['posicao']=blend(a[n].get('posicao',[0,0,0]),b[n].get('posicao',[0,0,0]),w)
        return p

    def enter(self,t):
        # Respiração começa e termina na fase zero dos idles.
        w=float(curve(t,[(0,0),(.35,.08),(1.1,.25),(1.9,1),(3.4,1)]))
        p=self.mix_pose(self.peaceful(0),self.combat(0),w)
        yaw=float(curve(t,[(0,0),(.65,-5),(1.1,0),(2,3),(2.7,0),(3.4,0)]))
        p['waist']['rotacao'][1]+=yaw
        p['body']['posicao']+=curve(t,[(0,[0,0,0]),(.5,[0,-1,1]),(1,[0,-.5,.5]),(1.9,[0,0,0]),(2.15,[-.6,.35,0]),(2.45,[.6,-1.4,-.5]),(2.65,[-.25,-.3,0]),(3.4,[0,0,0])])
        self.legs(p)
        for side,s in [('left',-1),('right',1)]:
            weapon=self.weapons[side];tail=self.mats(p)['tail_1'];back=point(tail,weapon['grip']);rback=tail[:3,:3]
            grasp=.92 if side=='left' else 1.08
            reach=float(smooth(t/grasp))
            for part in ['arm_','forearm_','hand_']:p[part+side]['rotacao']=[0,0,0]
            mats=self.mats(p)
            neutral=point(mats['hand_'+side],self.grips[side])
            shoulder=point(mats['torso'],self.m.ossos['arm_'+side].origem)
            rest_elbow=point(mats['torso'],self.m.ossos['forearm_'+side].origem)
            pole=blend(rest_elbow,shoulder+[s*7,-14,6],reach)
            if t<grasp:
                # Cotovelos abrem lateralmente antes de alcançar atrás do tronco.
                grip=blend(neutral,back,reach)+np.array([s*4*math.sin(math.pi*reach),.8*math.sin(math.pi*reach),0])
                rot=slerp(mats['hand_'+side][:3,:3],rback@R([0,0,s*15]),reach)
                self.arm(p,side,grip,rot,pole)
                self.sheathed(p,side)
            else:
                ready=self.combat_targets(p,t)[side]
                # Saque: primeiro afasta da raiz; depois varre por fora do corpo.
                out=back+np.array([s*8,4,-4])
                if side=='left':
                    over=shoulder+[-10,4,-6]
                    grip=curve(t,[(grasp,back),(1.43,out),(1.70,over),(2.02,ready[0]),(3.4,ready[0])])
                    amt=smooth((t-grasp)/(1.92-grasp));rot=slerp(rback,ready[1],amt)
                else:
                    high=np.array([14,40,-8]);bottom=ready[0]
                    grip=curve(t,[(grasp,back),(1.5,out),(2.06,high),(2.27,high),(2.46,bottom),(2.60,bottom+[0,.22,0]),(3.4,bottom)])
                    raised=self.sword_rotation(side,[.55,.76,.35],[0,0,1])
                    if t<2.07:rot=slerp(rback,raised,smooth((t-grasp)/(2.07-grasp)))
                    else:rot=slerp(raised,ready[1],smooth((t-2.27)/.19))
                shoulder=point(self.mats(p)['torso'],self.m.ossos['arm_'+side].origem)
                self.arm(p,side,grip,rot@R([0,0,s*15]),pole)
                self.weapon(p,side,grip,rot)
        if t<=0:return self.peaceful(0)
        if t>=CLIPS['combat_enter']:return self.combat(0)
        return p

    def exit(self,t):
        # Saída própria: extrair a lâmina primeiro, guardar em arcos laterais,
        # só então dobrar os braços e baixar a postura. Não toca o impacto ao inverso.
        end=CLIPS['combat_exit'];w=smooth((t-.45)/(end-.45))
        p=self.mix_pose(self.combat(0),self.peaceful(0),w);self.legs(p)
        for side,s in [('left',-1),('right',1)]:
            weapon=self.weapons[side];tail=self.mats(p)['tail_1'];dock=point(tail,weapon['grip']);rdock=tail[:3,:3]
            initial=self.combat_targets(self.combat(0),0)[side]
            release=1.95 if side=='left' else 2.12
            if t<release:
                out=dock+[s*8,4,-4]
                grip=curve(t,[(0,initial[0]),(.42,initial[0]+[0,4,0]),(1.25,out),(release,dock)])
                rot=slerp(initial[1],rdock,smooth((t-.42)/(release-.42)))
                shoulder=point(self.mats(p)['torso'],self.m.ossos['arm_'+side].origem)
                self.arm(p,side,grip,rot@R([0,0,s*15]),shoulder+[s*7,-14,6])
                self.weapon(p,side,grip,rot)
            else:
                u=smooth((t-release)/(end-release));natural=self.peaceful(0)
                shoulder=point(self.mats(p)['torso'],self.m.ossos['arm_'+side].origem)
                # Depois de soltar, a mão fica livre: retornar as juntas por FK
                # evita uma singularidade de IK ao cruzar diretamente sob o ombro.
                self.arm(p,side,dock,rdock@R([0,0,s*15]),shoulder+[s*7,-14,6])
                for part in ['arm_','forearm_','hand_']:
                    n=part+side
                    p[n]['rotacao']=forms.euler(slerp(R(p[n]['rotacao']),R(natural[n]['rotacao']),u))
                self.sheathed(p,side)
        if t<=0:return self.combat(0)
        if t>=end:return self.peaceful(0)
        return p

    def transition_walk(self,t,stop=False):
        # Levanta a espada enterrada antes de caminhar; inversa pousa sem novo golpe.
        w=smooth(t/.8);w=1-w if stop else w
        a=self.combat(0);b=self.combat(0,True)
        p=self.mix_pose(a,b,w)
        feet0,_=self.walk_feet(0,True)
        feet={}
        order=['right','left'] if stop else ['left','right']
        for i,side in enumerate(order):
            u=smooth((t-(.06 if i==0 else .43))/.30)
            start,end=(feet0[side],self.feet[side]) if stop else (self.feet[side],feet0[side])
            feet[side]=blend(start,end,u)+[0,1.4*math.sin(math.pi*u)**2,0]
        self.legs(p,feet)
        self.place_combat_arms(p,self.combat_targets(p,0,w,0))
        return p

    def pose(self,n,t):
        if n=='idle':return self.peaceful(t)
        if n=='walk':return self.peaceful(t,True)
        if n=='combat_idle':return self.combat(t)
        if n=='combat_walk':return self.combat(t,True)
        if n=='combat_enter':return self.enter(t)
        if n=='combat_exit':return self.exit(t)
        return self.transition_walk(t,n=='combat_walk_stop')


def bake(m,rig,names=None):
    ops=[]
    for name,length in CLIPS.items():
        if names and name not in names:continue
        if any(a['name']==name for a in m.animacoes):ops.append({'op':'remove_animation','animation':name})
        fps=120 if name=='combat_enter' else FPS
        ops.append({'op':'add_animation','name':name,'length':length,'loop':'loop' if name in LOOPS else 'once','snapping':fps})
        times=np.linspace(0,length,round(length*fps)+1);poses=[rig.pose(name,float(t)) for t in times]
        # Os loops respiram com o período do próprio clipe; a pose final é idêntica.
        if name in LOOPS:poses[-1]=copy.deepcopy(poses[0])
        for bone in m.ossos:
            for channel,field in [('rotation','rotacao'),('position','posicao')]:
                values=np.array([p[bone].get(field,[0,0,0]) for p in poses],float)
                if channel=='rotation':values=continuous_euler(values)
                if np.max(np.ptp(values,axis=0))<1e-7:indices=[0,len(times)-1]
                else:indices=range(len(times))
                for i in indices:
                    ops.append({'op':'set_keyframe','animation':name,'bone':bone,'channel':channel,
                                'time':round(float(times[i]),8),'value':np.round(values[i],7).tolist(),'interpolation':'linear'})
    dump(OUT/'_cache/ops-animacoes.json',ops);motor.editar(FILE,ops)
    return len(ops)


def update_locators(m):
    """As marcações das espadas removidas passam a seguir as penas reais."""
    rig=Rig(m);ops=[];exists={l.nome for l in m.locators}
    for side in ['left','right']:
        w=rig.weapons[side];parts=[c for c in m.cubos if c.osso==w['name']]
        verts=np.concatenate([bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,rig.rest),bbmodelo.cantos(c)) for c in parts])
        projection=(verts-w['grip'])@w['frame'][:,1]
        tip=verts[projection>projection.max()-1e-4].mean(0)
        for name,parent,position in [('loc_hand_'+side,'hand_'+side,rig.grips[side]),
                ('loc_weapon_base_'+side,w['name'],w['grip']),('loc_weapon_tip_'+side,w['name'],tip),
                ('loc_tail_socket_'+side,'tail_1',w['grip'])]:
            if name in exists:ops.append({'op':'remove_node','target':name})
            ops.append({'op':'add_locator','name':name,'parent':parent,'position':position.tolist()})
    dump(OUT/'ops-locators.json',ops);motor.editar(FILE,ops)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--preparar',action='store_true');ap.add_argument('--poses',action='store_true');ap.add_argument('--animar',action='store_true');ap.add_argument('--clipes',nargs='+',choices=list(CLIPS))
    args=ap.parse_args();(OUT/'_cache').mkdir(exist_ok=True)
    if args.animar and not args.preparar:
        previous=json.loads((OUT/'validacao.json').read_text(encoding='utf-8'))
        if previous['saida_sha256']!=sha(FILE):raise ValueError('Saída editada fora do gerador; preservar e criar outra versão.')
    m=prepare() if args.preparar else bbmodelo.ler(FILE);rig=Rig(m)
    if args.poses:
        sheet=Image.new('RGB',(768,768),(238,242,244));d=ImageDraw.Draw(sheet)
        for i,(n,t) in enumerate([('idle',0),('combat_enter',1.08),('combat_enter',2.15),('combat_idle',0)]):
            mat=rig.mats(rig.pose(n,t));img,*_=render.renderizar(m,vista='3/4',mats=mat,escala=3.4,fundo=(238,242,244))
            img.thumbnail((376,354));x=(i%2)*384+(384-img.width)//2;y=(i//2)*384+24
            sheet.paste(img,(x,y));d.text(((i%2)*384+8,(i//2)*384+6),f'{n} {t:.2f}s',fill=(40,50,60))
        sheet.save(OUT/'poses.png')
    if args.animar:
        count=bake(m,rig,args.clipes)
        update_locators(bbmodelo.ler(FILE))
        dump(OUT/'validacao.json',{'saida_sha256':sha(FILE),'fonte_sha256':sha(SOURCE),'clipes':CLIPS,'operacoes':count,'alcance_excedido_max':rig.max_unreachable,'status':'aguardando-validacao'})
    print(json.dumps({'arquivo':str(FILE.relative_to(ROOT)),'cubos':len(m.cubos),'ossos':len(m.ossos),'clipes':len(CLIPS) if args.animar else 0,'alcance_excedido':round(rig.max_unreachable,3)},ensure_ascii=False))


if __name__=='__main__':main()
