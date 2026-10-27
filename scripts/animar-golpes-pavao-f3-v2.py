"""Low/Cross: alavanca do ombro, extensão e fio no plano do corte; spin isolado."""
import argparse
import copy
import importlib.util
import json
import math
import shutil
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
v1=module('golpes_f3_v1','animar-golpes-pavao-f3.py')
g,bbmodelo,motor,render=v1.g,v1.bbmodelo,v1.motor,v1.render
R,point,unit,smooth,blend,track=v1.R,v1.point,v1.unit,v1.smooth,v1.blend,v1.track
Saved=v1.Saved;base=v1.base;SIDES=v1.SIDES
SOURCE=v1.FILE
OUT=ROOT/'modelos/criatura-pavao/f3/ataques-v2'
FILE=OUT/'criatura-pavao-e3-ataques-v2.bbmodel'
CLIPS={'attack_low':1.35,'attack_cross':1.95}
FPS=120
EVENTS={'attack_low':{'DamageStart':.36,'HitFrame':.50,'DamageEnd':.68,'RecoveryStart':.78,'CancelOpen':.94},
        'attack_cross':{'DamageStart':.35,'HitFrame':.43,'HitFrame2':.89,'DamageEnd':1.03,'RecoveryStart':1.11,'CancelOpen':1.36}}
ACTIVE={'attack_low':[('right',.36,.64)],'attack_cross':[('right',.36,.52),('left',.74,.98)]}


class Rig(v1.Rig):
    def __init__(self,m):
        super().__init__(m)
        self.wrists={}
        for side in SIDES:
            f=unit(self.hinges[side][1]);d=self.bind[side]@self.weapons[side]['frame'][:,1]
            # Um punho fixo durante o golpe; o ombro conduz a lâmina.
            tilt=v1.v2.rod(unit(np.cross(d,f)),35)
            self.wrists[side]=tilt@v1.v2.rod(f,25 if side=='left' else 0)
        self.guard_flex={};self.guard_roll={}
        for side in SIDES:
            a,b,c=[point(self.guardmat[n+side],m.ossos[n+side].origem) for n in ['arm_','forearm_','hand_']]
            self.guard_flex[side]=math.degrees(math.acos(float(np.clip(unit(b-a)@unit(c-b),-1,1))))
            w=self.weapons[side];rot=self.guardmat[w['name']][:3,:3];d=rot@w['frame'][:,1];n=rot@w['frame'][:,2]
            ref=self.direction_rotation(side,d,[0,1,0])@w['frame'][:,2]
            self.guard_roll[side]=math.degrees(math.atan2(float(d@np.cross(ref,n)),float(ref@n)))

    def body_pose(self,name,t):
        if name=='attack_low':return super().body_pose(name,t*1.15/CLIPS[name])
        d=CLIPS[name];p=copy.deepcopy(self.guard)
        yaw=float(track(t,[(0,0),(.24,-12),(.46,18),(.61,20),(.90,12),(1.08,10),(1.46,1),(d,0)]))
        pitch=float(track(t,[(0,0),(.23,-5),(.44,1),(.64,2),(.91,-17),(1.08,-15),(1.48,2),(d,0)]))
        twist=float(track(t,[(0,0),(.25,-8),(.43,7),(.59,4),(.89,0),(1.12,-2),(1.50,1),(d,0)]))
        roll=float(track(t,[(0,0),(.23,-2),(.44,3),(.65,0),(.92,-2),(1.18,-1),(d,0)]))
        shift=track(t,[(0,[0,0,0]),(.24,[-.8,-3,.4]),(.46,[1.0,-1.1,-1.4]),(.64,[.5,-1.5,-2.0]),
                       (.93,[-.8,-5.2,-4.5]),(1.09,[-.7,-5.2,-4.8]),(1.48,[.1,-.7,-.5]),(d,[0,0,0])])
        p['body']['posicao']=np.asarray(self.guard['body']['posicao'])+shift
        p['body']['rotacao']=g.forms.euler(R([0,yaw,0])@R([self.guard['body']['rotacao'][0]+pitch,0,roll]))
        for bone,scale in [('pelvis',.12),('waist',.22),('torso',.18)]:
            p[bone]['rotacao']=np.asarray(self.guard[bone]['rotacao'])+[pitch*scale,twist*(1 if bone=='torso' else .25),roll*.2]
        env=math.sin(math.pi*t/d)**2
        p['neck_1']['rotacao']=np.asarray(self.guard['neck_1']['rotacao'])+[-.28*pitch,-.3*twist,0]
        p['neck_2']['rotacao']=np.asarray(self.guard['neck_2']['rotacao'])+[-.1*pitch,-.12*twist,0]
        self.set_world(p,'head',R([0,yaw-.3*twist,0])@R([-1+.1*pitch,0,.1*roll]))
        p['tail_1']['rotacao']=np.asarray(self.guard['tail_1']['rotacao'])+[-.40*pitch,-.85*twist,-.5*roll]
        p['tail_2']['rotacao']=np.asarray(self.guard['tail_2']['rotacao'])+[2*env,-.45*twist,0]
        for side,s in [('left',-1),('right',1)]:
            for i in [1,2]:
                n=f'feather_{side}_{i}';p[n]['rotacao']=np.asarray(self.guard[n]['rotacao'])+[-.22*pitch+1.5*math.sin(2*math.pi*t/d)*env,-s*.12*twist,s*.15*roll]
            n='wing_'+side;p[n]['rotacao']=np.asarray(self.guard[n]['rotacao'])+[3*env,s*3*env,s*4*env]
            for n in self.anchors:
                if n.startswith('back') and side in n:p[n]['rotacao']=np.asarray(self.guard[n]['rotacao'])+[2.8*math.sin(2*math.pi*t/d)*env,-s*.15*twist,0]
        return p,yaw

    def foot_targets(self,name,t,yaw):
        d=CLIPS[name]
        if name=='attack_low':return super().foot_targets(name,t*1.15/d,yaw)
        feet={s:self.contacts[s].copy() for s in SIDES};rots={s:np.eye(3) for s in SIDES}
        for side,a,b,hold,end,dz in [('right',.13,.31,1.14,1.45,-2.7),('left',.52,.72,1.50,1.82,-5.0)]:
            step=float(track(t,[(0,0),(a,0),(b,1),(hold,1),(end,0),(d,0)]));h=0.
            if a<t<b:h=1.6*math.sin(math.pi*(t-a)/(b-a))**2
            if hold<t<end:h=1.2*math.sin(math.pi*(t-hold)/(end-hold))**2
            feet[side]+=[(-.4 if side=='left' else .4)*step,h,dz*step]
            roll=-7*step*(1-smooth((t-.80)/.55)) if side=='right' else -5*step*(1-smooth((t-.78)/.35))
            r=R([0,yaw*.35,0])@R([roll,0,0]);feet[side]+=self.toe[side]-r@self.toe[side];rots[side]=r
        for side in SIDES:
            floor=float((self.footverts[side]@rots[side].T+feet[side])[:,1].min())
            if floor<0:feet[side][1]-=floor
        return feet,rots

    def lever(self,p,side,direction,normal,flex,weight=1.,wrist=None):
        """Cinemática direta: espada/antebraço/punho solidários, cotovelo prescrito."""
        F=v1.v2.rod(self.hinges[side][2],float(flex)-self.hinges[side][3])
        H=self.wrists[side] if wrist is None else wrist
        sword=self.direction_rotation(side,direction,normal)
        A=sword@(F@H@self.bind[side]).T
        parent=self.mats(p)['torso'][:3,:3]
        for n,target in [('arm_'+side,parent.T@A),('forearm_'+side,F),('hand_'+side,H)]:
            p[n]['rotacao']=g.forms.euler(g.slerp(R(self.guard[n]['rotacao']),target,weight))
        hand=self.mats(p)['hand_'+side]
        self.weapon(p,side,point(hand,self.grips[side]),hand[:3,:3]@self.bind[side])

    def sword_floor(self,p,side):
        w=self.weapons[side];mat=self.mats(p)[w['name']]
        return float((self.weaponverts[side]@mat[:3,:3].T+point(mat,w['grip']))[:,1].min())

    def clear_floor(self,p,side,target=.03):
        if self.sword_floor(p,side)>=target:return
        mats=self.mats(p);w=self.weapons[side];wm=mats[w['name']]
        pts=self.weaponverts[side]@wm[:3,:3].T+point(wm,w['grip'])
        shoulder=point(mats['torso'],self.m.ossos['arm_'+side].origem)
        rel=pts[np.argmin(pts[:,1])]-shoulder;axis=unit([-rel[2],0,rel[0]])
        initial=mats['arm_'+side][:3,:3]
        def evaluate(a):
            self.set_world(p,'arm_'+side,v1.v2.rod(axis,a)@initial)
            return self.sword_floor(p,side)
        lo,hi=0.,4.
        while hi<120 and evaluate(hi)<target:hi*=1.7
        if evaluate(hi)<target:raise ValueError(('sem piso',side))
        for _ in range(24):
            mid=(lo+hi)/2
            if evaluate(mid)<target:lo=mid
            else:hi=mid
        evaluate(hi)

    def low_arm(self,p,t):
        d=CLIPS['attack_low'];side='right'
        w=smooth(t/.28)*(1-smooth((t-.80)/(d-.80)))
        a=float(track(t,[(0,self.angle0[side]),(.26,62),(.34,76),(.61,208),(.77,217),(1.04,95),(d,self.angle0[side])]))
        flex=float(track(t,[(0,80),(.26,22),(.35,10),(.65,10),(.80,25),(1.08,75),(d,80)]))
        az=math.radians(a+self.heading(p));horizontal=np.array([math.sin(az),0,math.cos(az)])
        clearance=float(track(t,[(0,0),(.25,.6),(.35,1.1),(.67,1.1),(.84,3),(1.10,2),(d,0)]))
        original=copy.deepcopy(p)
        def evaluate(y):
            q=copy.deepcopy(original);direction=horizontal*math.sqrt(1-y*y)+[0,y,0]
            self.lever(q,side,direction,[0,1,0],flex,w)
            return self.sword_floor(q,side),q
        # Piso resolvido pelo ombro, sem virar o fio ou dobrar o punho.
        lo,hi=-.85,.6;f0,q=evaluate(lo);f1,q1=evaluate(hi)
        if f0>=clearance:p.update(q);return
        if f1<0:p.update(q1);self.clear_floor(p,side);return
        clearance=min(clearance,max(0,f1-.001))
        for _ in range(24):
            y=(lo+hi)/2;f,q=evaluate(y)
            if f<clearance:lo=y
            else:hi=y
        p.update(q)

    def cross_arms(self,p,t):
        d=CLIPS['attack_cross']
        # A primeira ação sobe da linha baixa, com o cotovelo já estendido.
        w=smooth(t/.30)*(1-smooth((t-1.13)/(d-1.13)))
        az=float(track(t,[(0,self.angle0['right']),(.30,194.5),(.57,194.5),(.77,100),(1.12,90),(1.50,55),(d,self.angle0['right'])]))
        rest_elev=math.degrees(math.asin(self.dy0['right']))
        elev=float(track(t,[(0,rest_elev),(.30,-30),(.32,-28),(.43,12),(.56,58),(.75,38),(1.12,25),(1.50,-5),(d,rest_elev)]))
        target_flex=float(track(t,[(0,10),(.54,10),(.76,30),(1.12,40),(d,40)]))
        flex=float(blend(self.guard_flex['right'],target_flex,w))
        hand=g.slerp(R(self.guard['hand_right']['rotacao']),self.wrists['right'],w)
        roll=float(blend(self.guard_roll['right'],-90,w));a=math.radians(az)
        horizontal=np.array([math.sin(a),0,math.cos(a)]);initial=copy.deepcopy(p)
        def evaluate(y):
            q=copy.deepcopy(initial);direction=horizontal*math.sqrt(1-y*y)+[0,y,0]
            normal0=unit([0,1,0]-direction*float(direction[1]))
            normal=v1.v2.rod(direction,roll)@normal0
            self.lever(q,'right',direction,normal,flex,1.,wrist=hand)
            return self.sword_floor(q,'right'),q
        floor,q=evaluate(math.sin(math.radians(elev)))
        clearance=.001+1.25*math.sin(math.pi*t/.30)**2 if t<.30 else .001
        if t<.30 or floor<clearance:
            lo,hi=-.90,.90;f0,q0=evaluate(lo);f1,q1=evaluate(hi)
            if not f0<=clearance<=f1:raise ValueError(('preparação sem solução',t,f0,f1))
            for _ in range(24):
                mid=(lo+hi)/2;floor,q=evaluate(mid)
                if floor<clearance:lo=mid
                else:hi=mid
        p.update(q)
        # A esquerda sai diretamente do ombro, sobre a cabeça, e desce até o piso.
        w=smooth((t-.52)/.18)*(1-smooth((t-1.13)/(d-1.13)))
        elev=float(track(t,[(0,168),(.52,168),(.64,145),(.74,95),(.86,40),(.96,4),(1.05,-20),(1.13,-20),(1.50,60),(d,168)]))
        flex=float(track(t,[(0,110),(.52,110),(.67,25),(.73,10),(1.03,10),(1.13,20),(1.56,80),(d,110)]))
        angle=math.radians(elev);direction=np.array([0,math.sin(angle),-math.cos(angle)])
        self.lever(p,'left',direction,[1,0,0],flex,w)

    def pose(self,name,t):
        key=(name,round(t,9))
        if key in self.cache:return copy.deepcopy(self.cache[key])
        if t<=0 or t>=CLIPS[name]-1e-9:return copy.deepcopy(self.guard)
        p,yaw=self.body_pose(name,t);feet,rots=self.foot_targets(name,t,yaw);self.legs_world(p,feet,rots,yaw)
        if name=='attack_low':self.low_arm(p,t)
        else:self.cross_arms(p,t)
        for side in SIDES:self.clear_floor(p,side,target=.001)
        self.anchored_wings(p);self.cache[key]=copy.deepcopy(p);return p


def bake(names=None):
    names=names or list(CLIPS);partial=set(names)!=set(CLIPS)
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'_cache').mkdir(exist_ok=True)
    if partial and not FILE.exists():raise ValueError('Gere os dois golpes antes da revisão isolada.')
    if FILE.exists():
        record=json.loads((OUT/'geracao.json').read_text(encoding='utf-8'))
        if record['saida_sha256']!=g.sha(FILE):raise ValueError('Saída editada à mão; criar outra versão.')
    m=bbmodelo.ler(FILE if partial else SOURCE);rig=Rig(m);ops=[];counts=record['chaves'].copy() if partial else {}
    for n in names if partial else ['attack_low','attack_cross','attack_spin']:ops.append({'op':'remove_animation','animation':n})
    for name in names:
        d=CLIPS[name]
        times=np.unique(np.round(np.r_[np.linspace(0,d,round(d*FPS)+1),list(EVENTS[name].values())],9));poses=[rig.pose(name,float(t)) for t in times]
        ops.append({'op':'add_animation','name':name,'length':d,'loop':'once','snapping':120});count=0
        for bone in m.ossos:
            for channel,field in [('rotation','rotacao'),('position','posicao')]:
                values=np.array([p[bone].get(field,[0,0,0]) for p in poses],float)
                if channel=='rotation':values=g.continuous_euler(values)
                indices=[0,len(times)-1] if np.max(np.ptp(values,axis=0))<1e-7 else range(len(times))
                for i in indices:
                    ops.append({'op':'set_keyframe','animation':name,'bone':bone,'channel':channel,'time':float(times[i]),
                                'value':np.round(values[i],9).tolist(),'interpolation':'linear'});count+=1
        counts[name]=count;print('Calculado:',name,count,'chaves',flush=True)
    assert rig.max_unreachable<.01,rig.max_unreachable
    if not partial:shutil.copy2(SOURCE,FILE)
    ops.append({'op':'set_model_properties','name':FILE.stem})
    g.dump(OUT/'_cache/ops.json',ops);motor.editar(FILE,ops,lote=500)
    g.dump(OUT/'geracao.json',{'fonte':SOURCE.relative_to(ROOT).as_posix(),'fonte_sha256':g.sha(SOURCE),
        'saida_sha256':g.sha(FILE),'clipes':CLIPS,'chaves':counts,'spin':'isolado na v1; ausente nesta cópia'})
    metadata();print('Gravado:',FILE.name,flush=True)


def metadata():
    data=json.loads((SOURCE.parent/'animacoes.json').read_text(encoding='utf-8'))
    data.update(modelo=FILE.name,fonte=SOURCE.relative_to(ROOT).as_posix(),fonte_sha256=g.sha(SOURCE),
                saida_sha256=g.sha(FILE),status='low-cross-v2-em-avaliacao',validacao='validacao-ataques.json')
    data['golpes']={n:{'duracao':d,'loop':False,'origem':'combat_ready@0','destino':'combat_ready@0','marcadores':EVENTS[n]} for n,d in CLIPS.items()}
    data['golpes_adiados']={'attack_spin':'Rejeitado; isolado intacto na versão anterior.'}
    data['referencias_ataques']=['https://calgaryrakushinkan.com/hasuji/','Guarda/marcha/corridas aprovadas da F3']
    data['controle_golpes']='Ombro conduz; cotovelo estende a 10 graus; punho fixo na fase ativa; fio no plano de corte.'
    g.dump(OUT/'animacoes.json',data)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--estudo',action='store_true');ap.add_argument('--gerar',action='store_true')
    ap.add_argument('--validar',action='store_true');ap.add_argument('--previas',action='store_true');ap.add_argument('--nativo',action='store_true')
    ap.add_argument('--clipes',nargs='+',choices=list(CLIPS))
    args=ap.parse_args();review=module('conferencia_golpes_f3_v2','revisar-golpes-pavao-f3-v2.py')
    if args.estudo:review.study(__import__(__name__))
    if args.gerar:bake(args.clipes)
    if args.validar:review.check(__import__(__name__))
    if args.previas:review.offline(__import__(__name__))
    if args.nativo:review.capture(__import__(__name__))


if __name__=='__main__':main()
