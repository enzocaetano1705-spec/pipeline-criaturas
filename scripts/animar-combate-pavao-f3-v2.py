"""F3 v2: saque curto, cotovelo em dobradiça e descanso que termina em guarda.

As armas pertencem às mãos; as chaves compensam a cauda e o chão quando soltas.
Idle/walk aprovados são preservados em mundo, convertendo apenas esses vínculos.
"""
import argparse
import copy
import importlib.util
import json
import math
import shutil
from pathlib import Path

import numpy as np
from PIL import Image,ImageDraw
from criaturas import bbmodelo,motor,render

ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
    sp=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod);return mod
g=module('base_f3_v1','animar-pavao-f3.py')
review=module('leitor_f3_v1','revisar-animacoes-pavao-f3.py')
OUT=ROOT/'modelos/criatura-pavao/f3/animacoes-v2'
SOURCE=OUT/'origem-revisada.bbmodel'
FILE=OUT/'criatura-pavao-e3-combate-v2c.bbmodel'
CLIPS={'combat_ready':2.4,'combat_enter':1.3,'combat_enter_walk':1.3,
       'combat_enter_upper':1.3,'combat_walk':1.8,'combat_walk_start':.6,
       'combat_walk_stop':.6,'combat_idle':7.0,'combat_idle_resume':1.0,
       'combat_exit':1.5,'combat_exit_upper':1.5}
LOOPS={'combat_ready','combat_walk'}
GRASP={'left':.30,'right':.34}
DOCK={'left':.94,'right':1.02}
R=g.R;point=g.point;smooth=g.smooth;curve=g.curve;blend=g.blend;unit=g.unit


def rod(axis,angle):
    x,y,z=unit(axis);a=math.radians(angle);k=np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
    return np.eye(3)+math.sin(a)*k+(1-math.cos(a))*k@k


def node_local(o,world,parent):
    a=np.linalg.inv(parent)@world;r=a[:3,:3]
    return {'rotacao':g.forms.euler(r),'posicao':a[:3,3]-o.origem+r@o.origem}


def prepare():
    if FILE.exists():
        p=OUT/'validacao.json'
        if not p.exists():p=OUT/'geracao.json'
        r=json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
        if r.get('saida_sha256')!=g.sha(FILE):raise ValueError('Saída editada; criar outra versão.')
    shutil.copy2(SOURCE,FILE);m=bbmodelo.ler(FILE)
    ops=[{'op':'remove_animation','animation':a['name']} for a in m.animacoes if a['name'] in g.CLIPS and a['name'] not in ['idle','walk']]
    for side,name in [('left','tail_fan_04'),('right','tail_fan_06')]:
        ops.append({'op':'update_node','target':name,'parent':'hand_'+side})
    ops.append({'op':'set_model_properties','name':FILE.stem})
    g.dump(OUT/'ops-preparo.json',ops);motor.editar(FILE,ops)
    return bbmodelo.ler(FILE)


class Rig(g.Rig):
    def __init__(self,m):
        super().__init__(m)
        self.orig=bbmodelo.ler(SOURCE);self.saved=review.Saved(self.orig)
        self.hinges={};self.bind={};self.anatomy=[];self.weaponverts={}
        self.upper=[n for n in m.ossos if n not in ['root','body','pelvis'] and not n.startswith(('leg_','shin_','foot_')) and m.ossos[n].pai]
        for side in ['left','right']:
            a,b,c=[m.ossos[n+side].origem for n in ['arm_','forearm_','hand_']]
            v1,v2=b-a,c-b;n=unit(np.cross(v1,v2));theta=math.degrees(math.acos(np.clip(unit(v1)@unit(v2),-1,1)))
            self.hinges[side]=(v1,v2,n,theta)
            w=self.weapons[side]
            self.weaponverts[side]=np.concatenate([bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,self.rest),bbmodelo.cantos(c)) for c in m.cubos if c.osso==w['name']])-w['grip']
        # Relação de preensão definida na pose natural de alcançar a cauda.
        for side in ['left','right']:
            p=self.base(0,.35);pref=self.reach_pref(side,1)
            self.fk(p,side,pref,-36)
            mats=self.mats(p);tail=mats['tail_1'][:3,:3]
            self.bind[side]=mats['hand_'+side][:3,:3].T@tail

    def peaceful(self,t,walk=False):
        p=self.saved.pose('walk' if walk else 'idle',t%(1.5 if walk else 3.2))
        mats=bbmodelo.matrizes_ossos(self.orig,p)
        for side,n in [('left','tail_fan_04'),('right','tail_fan_06')]:
            p[n]=node_local(self.m.ossos[n],mats[n],mats['hand_'+side])
        return p

    def base(self,t,c=1,walking=0,phase=0):
        p=super().body(t,c,walking,phase)
        if not walking:
            # Respiração periódica da guarda; o descanso tem ritmo próprio.
            p=super().body(t*(3/2.4),c,0,0)
        if walking:
            a,ra=self.walk_feet(phase,False);b,rb=self.walk_feet(phase,True)
            feet={s:blend(a[s],b[s],c) for s in a};rolls={s:float(blend(ra[s],rb[s],c)) for s in a}
        else:feet,rolls=self.feet,{}
        self.legs(p,feet,rolls)
        return p

    def reach_pref(self,side,w):
        s=-1 if side=='left' else 1
        return R([-74*w,0,0])@R([0,0,-s*12*w])

    def fk(self,p,side,pref,delta,hand=None):
        p['arm_'+side]['rotacao']=g.forms.euler(pref)
        p['forearm_'+side]['rotacao']=g.forms.euler(rod(self.hinges[side][2],delta))
        p['hand_'+side]['rotacao']=g.forms.euler(hand if hand is not None else np.eye(3))

    def natural_arm(self,p,side,grip,handrot,pref,record=True):
        """O ombro orienta o plano; o cotovelo possui apenas flexão/extensão."""
        a,b,c=[self.m.ossos[n+side].origem for n in ['arm_','forearm_','hand_']]
        v1,v2,axis,theta0=self.hinges[side]
        parent=self.mats(p)['torso'];sh=point(parent,a);preferred=parent[:3,:3]@pref
        target=np.asarray(grip)-handrot@(self.grips[side]-c)
        d=target-sh;distance=np.linalg.norm(d);l1,l2=np.linalg.norm(v1),np.linalg.norm(v2)
        self.max_unreachable=max(self.max_unreachable,float(distance-l1-l2))
        distance=float(np.clip(distance,abs(l1-l2)+.03,l1+l2-.02));direction=unit(d)
        natural=preferred@v1;ortho=natural-direction*(natural@direction)
        if np.linalg.norm(ortho)<.05:ortho=preferred@np.cross(axis,v1)
        ortho=unit(ortho);along=(l1*l1-l2*l2+distance*distance)/(2*distance)
        elbow=sh+direction*along+ortho*math.sqrt(max(0,l1*l1-along*along))
        second=target-elbow;plane=unit(np.cross(elbow-sh,second))
        shoulder=g.frame(elbow-sh,plane)@g.frame(v1,axis).T
        angle=math.degrees(math.acos(np.clip(unit(elbow-sh)@unit(second),-1,1)))
        delta=angle-theta0
        self.set_world(p,'arm_'+side,shoulder)
        p['forearm_'+side]['rotacao']=g.forms.euler(rod(axis,delta))
        self.set_world(p,'hand_'+side,handrot)
        if record:self.anatomy.append((side,angle,float(np.linalg.norm(ortho)),float(distance)))
        return elbow

    def free_arm(self,p,side,pref,delta=0):self.fk(p,side,pref,delta)

    def held(self,p,side,grip,rotation,pref,allow_buried=False):
        grip=np.asarray(grip,float).copy()
        if not allow_buried:
            bottom=(self.weaponverts[side]@rotation.T+grip)[:,1].min()
            grip[1]+=max(0.,-float(bottom))
        self.natural_arm(p,side,grip,rotation@self.bind[side].T,pref)
        self.weapon(p,side,grip,rotation)

    def direction_rotation(self,side,direction,normal=(0,1,0)):
        return self.sword_rotation(side,unit(direction),normal)

    def guide_front(self,side,w=1):
        s=-1 if side=='left' else 1
        return R([8*w,0,-s*30*w])

    def ready_target(self,p,side):
        s=-1 if side=='left' else 1
        sh=point(self.mats(p)['torso'],self.m.ossos['arm_'+side].origem)
        grip=sh+[s*7,-5,-7]
        return grip,self.direction_rotation(side,[s*.50,.30,-.81])

    def shoulder_target(self,p):
        sh=point(self.mats(p)['torso'],self.m.ossos['arm_left'].origem)
        return sh+[-2,3,-6],self.direction_rotation('left',[-.025,.12,.99],[-1,.2,0])

    def drag_target(self,p):
        sh=point(self.mats(p)['torso'],self.m.ossos['arm_right'].origem)
        grip=sh+[7,-9,-3]
        # Ajusta a inclinação à altura REAL da ponta, não só ao centro da lâmina.
        horizontal=unit([.62,0,.78]);low,high=-.95,-.02
        w=self.weapons['right'];candidates=[c for c in self.m.cubos if c.osso==w['name']]
        verts=np.concatenate([bbmodelo.aplicar(bbmodelo.matriz_cubo(self.m,c,self.rest),bbmodelo.cantos(c)) for c in candidates])-w['grip']
        for _ in range(18):
            dy=(low+high)/2;d=horizontal*math.sqrt(1-dy*dy)+[0,dy,0]
            rot=self.direction_rotation('right',d,[1,0,0]);bottom=(verts@rot.T+grip)[:,1].min()
            if bottom<0:low=dy
            else:high=dy
        return grip,rot

    def ready(self,t=0):
        p=self.base(t)
        for side in ['left','right']:
            self.held(p,side,*self.ready_target(p,side),self.guide_front(side))
        return p

    def armed_walk(self,t=0):
        p=self.base(t,1,1,t/1.8)
        self.held(p,'left',*self.shoulder_target(p),R([-5,0,35]))
        self.held(p,'right',*self.drag_target(p),self.guide_front('right'))
        return p

    def enter(self,t,moving=False):
        d=1.3;c=float(curve(t,[(0,0),(.18,.12),(.52,1),(d,1)]))
        phase=t/1.5+(1/1.8-1/1.5)*t*t/(2*d)
        p=self.base(t if moving else 0,c,1 if moving else 0,phase if moving else 0)
        if t==0:
            p=self.peaceful(0,moving)
            # Os alvos das penas serão recalculados no rig novo.
        if .50<t<1.10:
            w=smooth((t-.50)/.07)*(1-smooth((t-1.03)/.07))
            theta=2*math.pi*smooth((t-.56)/.50);yaw=w*math.sin(theta)
            p['torso']['rotacao'][1]+=5*yaw;p['waist']['rotacao'][1]-=2*yaw
            p['torso']['rotacao'][0]+=1.6*w*math.sin(2*theta)
            p['head']['rotacao'][1]-=3*yaw;p['tail_1']['rotacao'][1]-=3*yaw
            for n in p:
                if n.startswith('back_feathers_'):p[n]['rotacao'][0]+=1.2*w*math.sin(theta-.2)
        for side,s in [('left',-1),('right',1)]:
            grab=GRASP[side];turn=smooth(t/.17);ext=smooth((t-.12)/(grab-.12))
            pref=self.reach_pref(side,turn)
            if t<grab:
                self.fk(p,side,pref,-36*ext)
                mats=self.mats(p);fkgrip=point(mats['hand_'+side],self.grips[side]);tail=mats['tail_1']
                dock=point(tail,self.weapons[side]['grip']);w=smooth((t-.16)/(grab-.16))
                handrot=g.slerp(mats['hand_'+side][:3,:3],tail[:3,:3]@self.bind[side].T,w)
                target=blend(fkgrip,dock,w)
                self.natural_arm(p,side,target,handrot,pref)
                self.sheathed(p,side)
            else:
                tail=self.mats(p)['tail_1'];dock=point(tail,self.weapons[side]['grip']);rdock=tail[:3,:3]
                sh=point(self.mats(p)['torso'],self.m.ossos['arm_'+side].origem)
                outside=sh+[s*10,-2,-4];flower=sh+[s*10,5,-5]
                final=self.ready_target(p,side)
                if moving:
                    last=self.shoulder_target(p) if side=='left' else self.drag_target(p)
                    w=smooth((t-1.10)/.20)
                    final=(blend(final[0],last[0],w),g.slerp(final[1],last[1],w))
                grip=curve(t,[(grab,dock),(.50,outside),(.62,flower),(1.03,flower),(d,final[0])])
                # Duplo oito inclinado, adaptado ao comprimento das grandes penas.
                theta=2*math.pi*smooth((t-.56)/.50)
                yy=.63*math.sin(theta);zz=.70*math.sin(2*theta)
                xx=s*math.sqrt(max(.01,1-yy*yy-zz*zz))
                flowerrot=self.direction_rotation(side,[xx,yy,zz],[0,1,0])
                if t<.56:rot=g.slerp(rdock,self.direction_rotation(side,[s,0,0]),smooth((t-grab)/(.56-grab)))
                elif t<1.06:rot=flowerrot
                else:rot=g.slerp(self.direction_rotation(side,[s,0,0]),final[1],smooth((t-1.06)/.24))
                pr=g.slerp(self.reach_pref(side,1),self.guide_front(side),smooth((t-.46)/.24))
                if moving and side=='left':pr=g.slerp(pr,R([-5,0,35]),smooth((t-1.10)/.20))
                self.held(p,side,grip,rot,pr)
        if moving and t<.10:
            initial=self.peaceful(phase*1.5,True);u=smooth(t/.10)
            for side in ['left','right']:
                for prefix in ['arm_','forearm_','hand_']:
                    n=prefix+side;p[n]['rotacao']=g.forms.euler(g.slerp(R(initial[n]['rotacao']),R(p[n]['rotacao']),u))
                self.sheathed(p,side)
        if t>=d:return self.armed_walk(phase*1.8) if moving else self.ready(0)
        return p

    def exit_pose(self,t,moving=True,start=None):
        end=1.5;c=1-smooth(t/end)
        phase=t/1.8+(1/1.5-1/1.8)*t*t/(2*end)
        p=self.base(t if moving else 0,c,1 if moving else 0,phase if moving else 0)
        for side,s in [('left',-1),('right',1)]:
            docktime=DOCK[side];tail=self.mats(p)['tail_1'];dock=point(tail,self.weapons[side]['grip']);rdock=tail[:3,:3]
            initial=(self.shoulder_target(p) if side=='left' else self.drag_target(p)) if moving else self.ready_target(p,side)
            if start is not None:initial=start[side]
            initial_pref=R([-5,0,35]) if side=='left' and (moving or start is not None) else self.guide_front(side)
            pref=g.slerp(initial_pref,self.reach_pref(side,1),smooth((t-.08)/(.75)))
            sh=point(self.mats(p)['torso'],self.m.ossos['arm_'+side].origem)
            if t<docktime:
                out=sh+[s*10,-2,-2]
                grip=curve(t,[(0,initial[0]),(.22,initial[0]+[0,3,0]),(.63,out),(docktime,dock)])
                rot=g.slerp(initial[1],rdock,smooth((t-.12)/(docktime-.12)))
                self.held(p,side,grip,rot,pref)
            else:
                # Já solta na cauda: ombro retorna e o braço volta a se dobrar.
                u=smooth((t-docktime)/(end-docktime))
                self.held(p,side,dock,rdock,self.reach_pref(side,1))
                docked={n:copy.deepcopy(p[n]) for n in ['arm_'+side,'forearm_'+side,'hand_'+side]}
                self.fk(p,side,self.reach_pref(side,1-u),-36*(1-u))
                for n,a in docked.items():p[n]['rotacao']=g.forms.euler(g.slerp(R(a['rotacao']),R(p[n]['rotacao']),smooth(u/.3)))
                self.sheathed(p,side)
        if moving and t>=end-.12:
            natural=self.peaceful(phase*1.5,True)
            p=self.mix_pose(p,natural,smooth((t-(end-.12))/.12))
            for side in ['left','right']:self.sheathed(p,side)
        if t>=end:
            p=self.peaceful(phase*1.5 if moving else 0,moving)
            for side in ['left','right']:self.sheathed(p,side)
        return p

    def planted(self):
        grip=np.array([13.0,26.0,-11.0])
        return grip,self.direction_rotation('right',[.035,-.998,.035],[0,0,1])

    def rest_hold(self,t=0):
        p=self.base(0)
        # Respiração pesada, mas a espada cravada permanece imóvel no mundo.
        br=math.sin(2*math.pi*t/3)
        p['body']['posicao']+=np.array([0,.35*br,0]);p['torso']['rotacao'][0]+=-2.2*br
        p['neck_1']['rotacao'][0]+=1.6*br;p['head']['rotacao'][0]+=.6*br
        for n in p:
            if n.startswith(('back_feathers_','wing_','feather_')):p[n]['rotacao'][0]+=.8*br
        self.legs(p)
        self.held(p,'left',*self.shoulder_target(p),R([-5,0,35]))
        self.fk(p,'right',R([8,0,-18]),-8)
        self.weapon(p,'right',*self.planted())
        return p

    def rest_pose(self,t):
        if t>=7:return self.peaceful(0)
        if t<1.1:
            p=self.base(0);dip=float(curve(t,[(0,0),(.38,.1),(.66,-1.5),(.80,-.4),(1.1,0)]))
            p['body']['posicao']+=np.array([0,dip,0]);self.legs(p)
            for side in ['left','right']:
                start=self.ready_target(p,side)
                if side=='left':
                    end=self.shoulder_target(p);w=smooth(t/.70)
                    self.held(p,side,blend(start[0],end[0],w),g.slerp(start[1],end[1],w),g.slerp(self.guide_front(side),R([-5,0,35]),w))
                else:
                    bottom,rb=self.planted();high=np.array([14,39,-11])
                    grip=curve(t,[(0,start[0]),(.35,high),(.65,bottom),(1.1,bottom)])
                    raised=self.direction_rotation(side,[.1,.95,.2],[0,0,1])
                    rot=g.slerp(start[1],raised,smooth(t/.35)) if t<.35 else g.slerp(raised,rb,smooth((t-.35)/.30))
                    self.held(p,side,grip,rot,self.guide_front(side),allow_buried=True)
                    if t>.78:
                        current={n:copy.deepcopy(p[n]) for n in ['arm_right','forearm_right','hand_right']}
                        self.fk(p,side,R([8,0,-18]),-8);u=smooth((t-.78)/.32)
                        for n,a in current.items():p[n]['rotacao']=g.forms.euler(g.slerp(R(a['rotacao']),R(p[n]['rotacao']),u))
                        self.weapon(p,side,bottom,rb)
            return p
        if t<=4.1:return self.rest_hold(t-1.1)
        if t<4.80:
            p=self.rest_hold(0);u=smooth((t-4.1)/.30)
            neutral={n:copy.deepcopy(p[n]) for n in ['arm_right','forearm_right','hand_right']}
            grip,rot=self.planted()
            self.held(p,'right',grip,rot,self.guide_front('right'),allow_buried=True)
            if t<4.4:
                for n,a in neutral.items():p[n]['rotacao']=g.forms.euler(g.slerp(R(a['rotacao']),R(p[n]['rotacao']),u))
                self.weapon(p,'right',grip,rot)
            else:
                u=smooth((t-4.4)/.40);lift=grip+np.array([2,12,0])*u
                lifted=self.direction_rotation('right',[.80,-.46,.38],[0,0,1])
                rr=g.slerp(rot,lifted,u);self.held(p,'right',lift,rr,self.guide_front('right'),allow_buried=True)
            return p
        # Da recuperação à guarda: o corpo se abaixa junto com os ombros.
        local=(t-4.8)/2.2*1.5
        pose0=self.rest_pose(4.8-1e-5);mat0=self.mats(pose0)
        start={s:(point(mat0[self.weapons[s]['name']],self.weapons[s]['grip']),mat0[self.weapons[s]['name']][:3,:3]) for s in ['left','right']}
        p=self.exit_pose(local,False,start)
        if t==7:return self.peaceful(0)
        return p

    def resume(self,t):
        p=self.base(0);u=smooth(t)
        hold=self.rest_hold(0)
        for side in ['left','right']:
            if side=='left':initial=self.shoulder_target(p)
            else:
                initial=self.planted()
                if t<.25:
                    target=self.ready_target(p,side)
                    self.held(p,side,*initial,self.guide_front(side),allow_buried=True)
                    for n in ['arm_right','forearm_right','hand_right']:
                        p[n]['rotacao']=g.forms.euler(g.slerp(R(hold[n]['rotacao']),R(p[n]['rotacao']),smooth(t/.25)))
                    self.weapon(p,side,*initial);continue
            final=self.ready_target(p,side);v=smooth((t-(.25 if side=='right' else 0))/(.75 if side=='right' else 1))
            grip=blend(initial[0],final[0],v)
            if side=='right':grip[1]+=8*math.sin(math.pi*v)**2
            pref=g.slerp(R([-5,0,35]),self.guide_front(side),v) if side=='left' else self.guide_front(side)
            self.held(p,side,grip,g.slerp(initial[1],final[1],v),pref,allow_buried=side=='right')
        if t>=1:return self.ready(0)
        return p

    def transition(self,t,stop=False):
        u=smooth(t/.6);u=1-u if stop else u
        p=self.mix_pose(self.ready(0),self.armed_walk(0),u)
        walkfeet,_=self.walk_feet(0,True);feet={}
        for i,s in enumerate(['right','left'] if stop else ['left','right']):
            w=smooth((t-(.03 if i==0 else .32))/.25)
            a,b=(walkfeet[s],self.feet[s]) if stop else (self.feet[s],walkfeet[s])
            feet[s]=blend(a,b,w)+[0,1.1*math.sin(math.pi*w)**2,0]
        self.legs(p,feet)
        for side in ['left','right']:
            a=self.ready_target(p,side);b=self.shoulder_target(p) if side=='left' else self.drag_target(p)
            grip=blend(a[0],b[0],u);rot=g.slerp(a[1],b[1],u)
            pref=g.slerp(self.guide_front(side),R([-5,0,35]),u) if side=='left' else self.guide_front(side)
            self.held(p,side,grip,rot,pref)
        return p

    def upper_pose(self,p):
        """Transfere a postura para a cintura, preservando o ciclo das pernas."""
        mats=self.mats(p);ref=self.mats(self.peaceful(0))['pelvis']
        q=copy.deepcopy(p)
        for n in ['waist','tail_1']:
            q[n]=node_local(self.m.ossos[n],mats[n],ref)
        return {n:q[n] for n in self.upper}

    def pose(self,name,t):
        if name=='combat_ready':return self.ready(t)
        if name=='combat_walk':return self.armed_walk(t)
        if name.startswith('combat_enter'):return self.enter(t,name.endswith('walk'))
        if name.startswith('combat_exit'):return self.exit_pose(t,name!='combat_exit_upper')
        if name=='combat_idle':return self.rest_pose(t)
        if name=='combat_idle_resume':return self.resume(t)
        return self.transition(t,name.endswith('stop'))


def preserve_walks(m,rig):
    """Só converte os canais das penas para seu novo pai, mantendo as poses."""
    ops=[]
    for name,length in [('idle',3.2),('walk',1.5)]:
        anim=next(a for a in m.animacoes if a['name']==name)
        for n in ['tail_fan_04','tail_fan_06']:
            for key in anim['animators'][m.ossos[n].uuid]['keyframes']:
                ops.append({'op':'remove_keyframe','animation':name,'bone':n,'channel':key['channel'],'time':key['time']})
        for t in np.linspace(0,length,round(length*120)+1):
            old=rig.saved.pose(name,float(t));mat=bbmodelo.matrizes_ossos(rig.orig,old)
            for side in ['left','right']:
                w=rig.weapons[side];n=w['name'];o=m.ossos[n]
                local=node_local(o,mat[n],mat['hand_'+side])
                for ch,f in [('rotation','rotacao'),('position','posicao')]:
                    ops.append({'op':'set_keyframe','animation':name,'bone':n,'channel':ch,'time':round(float(t),8),'value':np.round(local[f],7).tolist(),'interpolation':'linear'})
    return ops


def bake(m,rig,names=None):
    ops=preserve_walks(m,rig) if not names else []
    for name,length in CLIPS.items():
        if names and name not in names:continue
        if any(a['name']==name for a in m.animacoes):ops.append({'op':'remove_animation','animation':name})
        fps=240 if name=='combat_enter_walk' else 120
        ops.append({'op':'add_animation','name':name,'length':length,'loop':'loop' if name in LOOPS else 'once','snapping':120})
        times=np.linspace(0,length,round(length*fps)+1);poses=[]
        for t in times:
            p=rig.pose(name,float(t))
            poses.append(rig.upper_pose(p) if name.endswith('upper') else p)
        if name in LOOPS:poses[-1]=copy.deepcopy(poses[0])
        bones=rig.upper if name.endswith('upper') else list(m.ossos)
        for bone in bones:
            for ch,f in [('rotation','rotacao'),('position','posicao')]:
                vals=np.array([p[bone].get(f,[0,0,0]) for p in poses])
                if ch=='rotation':vals=g.continuous_euler(vals)
                indices=[0,len(times)-1] if np.max(np.ptp(vals,axis=0))<1e-8 else range(len(times))
                for i in indices:ops.append({'op':'set_keyframe','animation':name,'bone':bone,'channel':ch,'time':round(float(times[i]),8),'value':np.round(vals[i],7).tolist(),'interpolation':'linear'})
    g.dump(OUT/'_cache/ops-animacoes.json',ops);motor.editar(FILE,ops)
    g.dump(OUT/'geracao.json',{'saida_sha256':g.sha(FILE),'fonte_sha256':g.sha(SOURCE),'operacoes':len(ops),'alcance_excedido':rig.max_unreachable,'flexao_cotovelo':[min(x[1] for x in rig.anatomy),max(x[1] for x in rig.anatomy)]})


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--preparar',action='store_true');ap.add_argument('--animar',action='store_true');ap.add_argument('--poses',action='store_true');ap.add_argument('--clipes',nargs='+',choices=list(CLIPS));args=ap.parse_args()
    (OUT/'_cache').mkdir(exist_ok=True)
    if args.animar and not args.preparar:
        records=[OUT/'validacao.json',OUT/'geracao.json']
        hashes=[json.loads(p.read_text(encoding='utf-8')).get('saida_sha256') for p in records if p.exists()]
        if hashes and g.sha(FILE) not in hashes:raise ValueError('Saída editada fora do gerador; preservar em outra versão.')
    m=prepare() if args.preparar else bbmodelo.ler(FILE);rig=Rig(m)
    if args.poses:
        sheet=Image.new('RGB',(768,768),(238,242,244));d=ImageDraw.Draw(sheet)
        samples=[('combat_enter',.16),('combat_enter',.32),('combat_enter',.79),('combat_idle',2)]
        for i,(name,t) in enumerate(samples):
            p=rig.pose(name,t);im,*_=render.renderizar(m,vista=(65,10),mats=rig.mats(p),escala=3.3,fundo=(238,242,244));im.thumbnail((380,350));x=i%2*384;y=i//2*384
            sheet.paste(im,(x+(384-im.width)//2,y+25));d.text((x+6,y+5),f'{name} {t:.2f}s',fill=(25,40,50))
        sheet.save(OUT/'poses.png')
        print('Poses; alcance excedido:',round(rig.max_unreachable,4))
    if args.animar:bake(m,rig,args.clipes);print('Clipes gravados:',len(CLIPS)+2)


if __name__=='__main__':main()
