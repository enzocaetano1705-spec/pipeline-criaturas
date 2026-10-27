"""F3: aceleração do Low, golpes separados e combo aéreo com duas lâminas.

Poses por cinemática; gravação em lotes exclusivamente pelo motor externo.
"""
import argparse
import copy
import json
import math
import shutil
from pathlib import Path
import numpy as np
import importlib.util

ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
    s=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
v4=module('golpes_f3_v4','animar-golpes-pavao-f3-v4.py')
g,bbmodelo,motor,render=v4.g,v4.bbmodelo,v4.motor,v4.render
R,point,unit,smooth,blend,track=v4.R,v4.point,v4.unit,v4.smooth,v4.blend,v4.track
Saved,base,SIDES,rod=v4.Saved,v4.base,v4.SIDES,v4.rod
SOURCE=v4.FILE;OUT=ROOT/'modelos/criatura-pavao/f3/ataques-v5';FILE=OUT/'criatura-pavao-e3-ataques-v5.bbmodel'
CLIPS={'attack_low':1.42,'attack_right':1.65,'attack_left':1.50,'attack_combo':2.20}
FPS=120;TAKEOFF=.40;LANDING=1.20;JUMP_HEIGHT=20.
EVENTS={
    'attack_low':{'DamageStart':.43,'HitFrame':.54,'DamageEnd':.67,'RecoveryStart':.80,'CancelOpen':1.08},
    'attack_right':{'DamageStart':.37,'HitFrame':.49,'DamageEnd':.64,'RecoveryStart':.83,'CancelOpen':1.12},
    'attack_left':{'DamageStart':.28,'HitFrame':.49,'DamageEnd':.55,'RecoveryStart':.78,'CancelOpen':1.10},
    'attack_combo':{'Takeoff':TAKEOFF,'DamageStart':.44,'HitFrame':.49,'DamageEnd':.57,'SpinEnd':1.00,
        'DamageStart2':1.03,'HitFrame2':1.19,'GroundImpact':LANDING,'DamageEnd2':1.24,'RecoveryStart':1.40,'CancelOpen':1.82}}
ACTIVE={'attack_low':[('right',.43,.66)],'attack_right':[('right',.37,.62)],
        'attack_left':[('left',.31,.53)],'attack_combo':[('right',.46,.54),('right',1.04,1.15),('left',1.04,1.15)]}
LOW_TIME=[(0,0),(.27,.28),(.35,.40),(.43,.46),(.57,.80),(.64,.95),(.77,1.07),(1.05,1.30),(1.42,1.65)]
RIGHT_TIME=[(0,0),(.27,.32),(.33,.40),(.40,.46),(.53,.77),(.62,.89),(.80,.91),(.98,1.02),(1.16,1.22),(1.65,2.40)]
LEFT_TIME=[(0,.91),(.20,1.10),(.32,1.18),(.49,1.32),(.60,1.48),(.76,1.62),(1.10,2.02),(1.50,2.40)]


def mix_pose(a,b,w):
    result=copy.deepcopy(a)
    for n in a:
        result[n]['rotacao']=g.forms.euler(g.slerp(R(a[n]['rotacao']),R(b[n]['rotacao']),w))
        result[n]['posicao']=blend(np.asarray(a[n].get('posicao',[0,0,0])),np.asarray(b[n].get('posicao',[0,0,0])),w)
    return result


class Rig(v4.Rig):
    def __init__(self,m):
        super().__init__(m);self.source_reader=Saved(bbmodelo.ler(SOURCE));self.cache={}

    def floor_passive(self,p,side):
        self.reset_guard(p,side);self.clear_floor(p,side,target=.001)

    def right(self,t):
        old=float(track(t,RIGHT_TIME));self.context='attack_cross';self.current_time=old
        p=self.body('attack_cross',old);before=self.mats(p)
        brake=smooth((t-.50)/.19)*(1-smooth((t-.83)/.55))
        p['body']['rotacao']=g.forms.euler(R([0,12*brake,0])@R(p['body']['rotacao']))
        p['body']['posicao']=np.asarray(p['body']['posicao'])+[.8*brake,-1.8*brake,-.7*brake]
        p['waist']['rotacao']=np.asarray(p['waist']['rotacao'])+[3*brake,4*brake,0]
        p['torso']['rotacao']=np.asarray(p['torso']['rotacao'])+[4*brake,7*brake,0]
        p['tail_1']['rotacao']=np.asarray(p['tail_1']['rotacao'])+[-4*brake,-9*brake,0]
        feet={s:point(before['foot_'+s],self.feet[s]) for s in SIDES}
        rots={s:before['foot_'+s][:3,:3] for s in SIDES}
        self.legs_world(p,feet,rots,self.heading(p))
        self.cross_right(p,old);self.floor_passive(p,'left');self.flare_elbow_fan(p,old)
        return p

    def left(self,t):
        old=float(track(t,LEFT_TIME));self.context='attack_cross';self.current_time=old
        p=self.body('attack_cross',old);mat=self.mats(p);w=smooth(t/.22)
        feet={s:blend(self.contacts[s],point(mat['foot_'+s],self.feet[s]),w) for s in SIDES}
        rots={s:g.slerp(self.guardmat['foot_'+s][:3,:3],mat['foot_'+s][:3,:3],w) for s in SIDES}
        p=mix_pose(self.guard,p,w)
        for s in SIDES:
            low=float((self.footverts[s]@rots[s].T+feet[s])[:,1].min())
            if low<0:feet[s][1]-=low
        self.legs_world(p,feet,rots,self.heading(p))
        self.cross_left(p,old);self.floor_passive(p,'right')
        return p

    @staticmethod
    def combo_yaw(t):
        return float(track(t,[(0,0),(.26,-18),(.36,-8),(.40,0),(.50,38),(.64,146),(.78,272),(.92,356),(1.,360),(2.20,360)]))

    def combo_body(self,t):
        p=copy.deepcopy(self.guard);yaw=self.combo_yaw(t)
        pitch=float(track(t,[(0,0),(.27,-14),(.40,4),(.57,9),(.78,-2),(.96,5),(1.12,-9),(1.25,-21),(1.39,-11),(1.66,3),(2.2,0)]))
        twist=float(track(t,[(0,0),(.27,-13),(.49,16),(.63,23),(.81,-10),(.98,-9),(1.18,4),(1.32,7),(1.65,-2),(2.2,0)]))
        roll=float(track(t,[(0,0),(.27,-4),(.50,-11),(.69,-15),(.90,8),(1.07,5),(1.25,-3),(1.52,2),(2.2,0)]))
        shift=track(t,[(0,[0,0,0]),(.27,[-1.2,-6.2,1.5]),(.40,[.7,1.0,-1]),(.64,[.6,1.5,-1.5]),
            (.90,[-.4,1.2,-.7]),(1.20,[0,-2.8,-3.5]),(1.27,[0,-7.1,-4.5]),(1.43,[0,-3.8,-3]),(1.67,[0,.7,-.8]),(2.2,[0,0,0])])
        u=float(np.clip((t-TAKEOFF)/(LANDING-TAKEOFF),0,1));h=4*JUMP_HEIGHT*u*(1-u)
        p['root']['posicao']=np.array([0,h,0])
        p['body']['rotacao']=np.asarray(self.guard['body']['rotacao'])+[pitch,yaw,roll]
        p['body']['posicao']=np.asarray(self.guard['body']['posicao'])+shift
        for n,k in [('pelvis',.12),('waist',.30),('torso',.50)]:
            p[n]['rotacao']=np.asarray(self.guard[n]['rotacao'])+[pitch*k,twist*(1 if n=='torso' else .28),roll*.14]
        p['neck_1']['rotacao']=np.asarray(self.guard['neck_1']['rotacao'])+[-.34*pitch,-.30*twist,-.18*roll]
        p['neck_2']['rotacao']=np.asarray(self.guard['neck_2']['rotacao'])+[-.13*pitch,-.12*twist,-.08*roll]
        self.set_world(p,'head',R([0,yaw-.25*twist,0])@R([-1+.15*pitch,0,.18*roll]))
        # A cauda e as penas atrasam a pelve; retornam após o impacto, sem escalar peças.
        lag=float(track(t,[(0,0),(.30,5),(.48,-8),(.65,-23),(.84,-18),(1.02,10),(1.24,12),(1.46,-7),(1.75,2),(2.2,0)]))
        p['tail_1']['rotacao']=np.asarray(self.guard['tail_1']['rotacao'])+[-.45*pitch,lag,-.35*roll]
        p['tail_2']['rotacao']=np.asarray(self.guard['tail_2']['rotacao'])+[-.20*pitch,.55*lag,-.12*roll]
        envelope=math.sin(math.pi*t/CLIPS['attack_combo'])**2
        for side,s in [('left',-1),('right',1)]:
            for i in [1,2]:
                n=f'feather_{side}_{i}'
                response=track(max(0,t-.035*i),[(0,0),(.28,4),(.52,-7),(.80,-3),(1.02,5),(1.25,8),(1.44,-5),(1.72,2),(2.2,0)])
                p[n]['rotacao']=np.asarray(self.guard[n]['rotacao'])+[response,-s*.12*twist,s*.1*roll]
            for n in self.anchors:
                if n.startswith('back') and side in n:
                    p[n]['rotacao']=np.asarray(self.guard[n]['rotacao'])+[-.18*pitch+2.5*math.sin(4*math.pi*t/2.2)*envelope,-s*.12*twist,0]
        self.combo_legs(p,t,yaw,h,u)
        return p,yaw

    def combo_legs(self,p,t,yaw,h,u):
        targets={};rotations={};air=TAKEOFF<t<LANDING
        if air:
            tuck=math.sin(math.pi*u)**1.3
            foot_yaw=yaw-self.combo_yaw(TAKEOFF)*(1-smooth(u/.60))*.65
            for side,s in [('left',-1),('right',1)]:
                rot=R([0,foot_yaw,0])@R([-17*tuck,0,s*5*tuck])
                target=R([0,foot_yaw,0])@(self.contacts[side]+[s*.2*tuck,(9 if side=='left' else 6)*tuck,(-3 if side=='left' else 2)*tuck])
                target[1]+=h;floor=float((self.footverts[side]@rot.T+target)[:,1].min())
                # Evita que a sola inclinada reduza a altura do contato esperado.
                if floor<h:target[1]+=h-floor
                targets[side]=target;rotations[side]=rot
        else:
            load=smooth(t/.27)*(1-smooth((t-.32)/.08)) if t<TAKEOFF else 0
            impact=smooth((t-1.20)/.08)*(1-smooth((t-1.45)/.50))
            for side,s in [('left',-1),('right',1)]:
                turn=yaw*.35 if t<TAKEOFF else 360.
                rot=R([0,turn,0])@R([-9*load-4*impact,0,0])
                target=self.contacts[side]+self.toe[side]-rot@self.toe[side]
                floor=float((self.footverts[side]@rot.T+target)[:,1].min())
                if floor<0:target[1]-=floor
                targets[side]=target;rotations[side]=rot
        self.legs_world(p,targets,rotations,yaw)

    @staticmethod
    def diagonal45(sigma):
        a=math.radians(sigma);c=math.sqrt(.5)
        d=np.array([-c*math.sin(a),c*math.sin(a),-math.cos(a)])
        tangent=np.array([-c*math.cos(a),c*math.cos(a),math.sin(a)])
        return d,-unit(np.cross(d,tangent))

    def combo_arms(self,p,t,yaw):
        self.context='attack_cross';self.current_time=float(track(t,[(0,0),(.34,.40),(.53,.85),(.96,1.1),(1.42,1.7),(2.2,2.4)]))
        prep=None
        if .34<=t<.375:
            prep=copy.deepcopy(p);self.cross_right(prep,.4-1e-8)
        # Direita inicia o corte; a trajetória no ar continua na volta do corpo.
        if t<.34:
            self.cross_right(p,float(track(t,[(0,0),(.27,.32),(.34,.40)])))
        else:
            self.reset_guard(p,'right');endd,endn=self.diagonal45(50)
            if t<=.70:
                sigma=float(track(t,[(.34,-70),(.40,-58),(.48,21),(.53,50),(.61,80),(.70,95)]));d,n=self.diagonal45(sigma)
                turn=R([0,(yaw-self.combo_yaw(.53))*smooth((t-.53)/.17),0]) if t>.53 else np.eye(3)
                d=turn@d;n=turn@n;flex=float(track(t,[(.34,12),(.53,12),(.70,35)]));w=1.
            elif t<1.00:
                endd,endn=self.diagonal45(95)
                carry=R([0,yaw-self.combo_yaw(.53),0])@self.direction_rotation('right',endd,endn)
                goal=self.direction_rotation('right',R([0,yaw,0])@unit([.20,math.sin(math.radians(100)),-math.cos(math.radians(100))]),R([0,yaw,0])@np.array([1.,0,0]))
                rot=g.slerp(carry,goal,smooth((t-.70)/.30));d=rot@self.weapons['right']['frame'][:,1];n=rot@self.weapons['right']['frame'][:,2]
                flex=float(track(t,[(.70,35),(.80,38),(1.0,22)]));w=1.
            else:
                self.overhead(p,'right',t,yaw);d=n=None
            if d is not None:self.anatomical_arm(p,'right',d,n,flex,w)
        if prep is not None:
            w=smooth((t-.34)/.035)
            for n in ['arm_right','forearm_right','hand_right']:
                p[n]['rotacao']=g.forms.euler(g.slerp(R(prep[n]['rotacao']),R(p[n]['rotacao']),w))
        # A esquerda se abre lateralmente antes de armar acima da cabeça.
        self.reset_guard(p,'left')
        if t<1.00:
            guard=self.mats(p)[self.weapons['left']['name']][:3,:3]
            if t<.60:
                d=R([0,yaw,0])@unit([-.72,.42,.54]);n=R([0,yaw,0])@np.array([1.,0,0]);w=smooth((t-.27)/.33)
            else:
                a=unit([-.72,.42,.54]);b=unit([-.20,math.sin(math.radians(100)),-math.cos(math.radians(100))]);d=R([0,yaw,0])@v4.direction_blend(a,b,smooth((t-.60)/.40));n=R([0,yaw,0])@np.array([1.,0,0]);w=1.
            rot=g.slerp(guard,self.direction_rotation('left',d,n),w)
            d=rot@self.weapons['left']['frame'][:,1];n=rot@self.weapons['left']['frame'][:,2]
            self.anatomical_arm(p,'left',d,n,float(blend(self.guard_flex['left'],22,w)),w)
        else:self.overhead(p,'left',t,yaw)
        for side in SIDES:self.clear_floor(p,side,target=.001)
        opening=smooth(t/.25)*(1-smooth((t-1.65)/.45));mat=self.mats(p)
        for side,s in [('left',-1),('right',1)]:
            n='wing_'+side;outward=unit(mat['torso'][:3,:3]@np.array([s,-.05,.45]));normal=mat['torso'][:3,:3]@np.array([0.,0.,-1.])
            target=g.frame(outward,normal)@g.frame(self.fan_axis[side],[1,0,0]).T
            self.set_world(p,n,g.slerp(mat[n][:3,:3],target,opening))

    def overhead(self,p,side,t,yaw):
        s=-1 if side=='left' else 1;self.reset_guard(p,side)
        e=float(track(t,[(1.0,100),(1.05,89),(1.13,20),(1.20,-29),(1.30,-29),(1.43,-10),(1.62,75),(1.85,130),(2.2,168)]))
        a=math.radians(e);direction=unit([s*.20,math.sin(a),-math.cos(a)]);turn=R([0,yaw,0]);d=turn@direction;n=turn@np.array([1.,0,0])
        w=1-smooth((t-1.62)/.58);flex=float(blend(self.guard_flex[side],float(track(t,[(1,22),(1.14,12),(1.33,12),(1.58,48)])),w))
        held=self.mats(p)[self.weapons[side]['name']][:3,:3]
        blade_weight=1-smooth((t-1.85)/.35)
        target=self.direction_rotation(side,d,n);sword=g.slerp(held,target,blade_weight)
        self.anatomical_arm(p,side,sword@self.weapons[side]['frame'][:,1],sword@self.weapons[side]['frame'][:,2],flex,w)
        # No impacto, as duas pontas terminam juntas no piso, sem enterrá-las.
        impact=smooth((t-1.15)/.05)*(1-smooth((t-1.32)/.12))
        if impact>0:
            before=copy.deepcopy(p);horizontal=turn@unit([s*.20,0,-1]);ref=unit(np.array([0.,1.,0.])-d*d[1]);roll=math.degrees(math.atan2(float(d@np.cross(ref,n)),float(ref@n)))
            self.floor_direction(p,side,horizontal,roll,flex,w,.015)
            p.update(mix_pose(before,p,impact))

    def raw_pose(self,name,t):
        if t<=0 or t>=CLIPS[name]-1e-9:return copy.deepcopy(self.guard)
        key=(name,round(t,9))
        if key in self.cache:return copy.deepcopy(self.cache[key])
        if name=='attack_low':p=self.source_reader.pose('attack_low',float(track(t,LOW_TIME)))
        elif name=='attack_right':p=self.right(t)
        elif name=='attack_left':p=self.left(t)
        else:
            p,yaw=self.combo_body(t);self.combo_arms(p,t,yaw)
        self.anchored_wings(p);self.cache[key]=copy.deepcopy(p);return p

    def pose(self,name,t):
        p=self.raw_pose(name,t)
        if name not in ['attack_right','attack_combo']:return p
        # Rolamento pequeno da empunhadura: o fio segue a velocidade real,
        # que inclui subida/queda e a alavanca do ombro, não apenas o arco local.
        first=(smooth((t-.33)/.04)*(1-smooth((t-.62)/.18)) if name=='attack_right'
            else smooth((t-.435)/.025)*(1-smooth((t-.54)/.09)))
        second=smooth((t-.99)/.05)*(1-smooth((t-1.15)/.04)) if name=='attack_combo' else 0.
        impact=smooth((t-1.15)/.05)*(1-smooth((t-1.32)/.12)) if name=='attack_combo' else 0.
        if max(first,second,impact)<=0:return p
        mat=self.mats(p);before=self.mats(self.raw_pose(name,t-.0005));after=self.mats(self.raw_pose(name,t+.0005))
        for side in SIDES:
            w=second if side=='left' else max(first,second)
            if w<=0:continue
            weapon=self.weapons[side];wm=mat[weapon['name']];d=wm[:3,:3]@weapon['frame'][:,1];normal=wm[:3,:3]@weapon['frame'][:,2]
            sample=weapon['grip']+weapon['frame'][:,1]*weapon['length']*.85
            velocity=(point(after[weapon['name']],sample)-point(before[weapon['name']],sample))/.001
            desired=unit(np.cross(d,velocity))
            if desired@normal<0:desired=-desired
            angle=math.degrees(math.atan2(float(d@np.cross(normal,desired)),float(normal@desired)))
            angle=float(np.clip(angle,-55,55))*w
            sword=rod(d,angle)@wm[:3,:3];hand_world=sword@self.bind[side].T
            self.set_world(p,'hand_'+side,hand_world)
        if impact>0:
            self.context='attack_cross';self.current_time=float(track(t,[(0,0),(.34,.40),(.53,.85),(.96,1.1),(1.42,1.7),(2.2,2.4)]))
            for side in SIDES:
                before=copy.deepcopy(p);mat=self.mats(p);w=self.weapons[side];d=mat[w['name']][:3,:3]@w['frame'][:,1];n=mat[w['name']][:3,:3]@w['frame'][:,2]
                ref=unit(np.array([0.,1.,0.])-d*d[1]);roll=math.degrees(math.atan2(float(d@np.cross(ref,n)),float(ref@n)))
                self.floor_direction(p,side,unit([d[0],0,d[2]]),roll,12,1.,.015)
                p.update(mix_pose(before,p,impact))
        return p


def sample_times(rig,name,d):
    """Acrescenta chaves só onde âncoras/piso precisam de maior resolução."""
    times=np.unique(np.round(np.r_[np.linspace(0,d,round(d*FPS)+1),list(EVENTS[name].values())],9))
    if name not in ['attack_right','attack_combo']:return times
    for _ in range(3):
        poses=[rig.pose(name,float(t)) for t in times]
        rotations={n:g.continuous_euler([p[n]['rotacao'] for p in poses]) for n in rig.m.ossos}
        extra=[]
        for i,(a,b) in enumerate(zip(times[:-1],times[1:])):
            mid=(a+b)/2;p={n:{'rotacao':(rotations[n][i]+rotations[n][i+1])/2,
                'posicao':blend(np.asarray(poses[i][n].get('posicao',[0,0,0])),np.asarray(poses[i+1][n].get('posicao',[0,0,0])),.5)} for n in rig.m.ossos}
            errors=[]
            for n,anchor in rig.anchors.items():
                o=rig.m.ossos[n].origem
                errors.append(float(np.linalg.norm(o+p[n]['posicao']+R(p[n]['rotacao'])@(anchor-o)-anchor)))
            if max(errors)>.006:extra.append(mid);continue
            mat=rig.mats(p)
            floors=[]
            for side in SIDES:
                w=rig.weapons[side];wm=mat[w['name']]
                floors.append(float((rig.weaponverts[side]@wm[:3,:3].T+point(wm,w['grip']))[:,1].min()))
                fm=mat['foot_'+side];floors.append(float((rig.footverts[side]@fm[:3,:3].T+point(fm,rig.feet[side]))[:,1].min()))
            if min(floors)<-.018:extra.append(mid)
        if not extra:break
        times=np.unique(np.round(np.r_[times,extra],9))
    return times


def bake(names=None):
    names=names or list(CLIPS);partial=set(names)!=set(CLIPS)
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'_cache').mkdir(exist_ok=True)
    record={}
    if FILE.exists():
        record=json.loads((OUT/'geracao.json').read_text(encoding='utf-8'))
        if record['saida_sha256']!=g.sha(FILE):raise ValueError('Modelo editado à mão: criar nova versão.')
    if partial and not FILE.exists():raise ValueError('Gere os quatro clipes antes da atualização parcial.')
    m=bbmodelo.ler(FILE if partial else SOURCE);rig=Rig(m);ops=[];counts=record.get('chaves',{}).copy()
    if not partial:
        ops.extend({'op':'remove_animation','animation':n} for n in ['attack_low','attack_cross'])
    for name in names:
        if partial:ops.append({'op':'remove_animation','animation':name})
        d=CLIPS[name];times=sample_times(rig,name,d)
        poses=[rig.pose(name,float(t)) for t in times];ops.append({'op':'add_animation','name':name,'length':d,'loop':'once','snapping':120});count=0
        for bone in m.ossos:
            for ch,field in [('rotation','rotacao'),('position','posicao')]:
                values=np.array([p[bone].get(field,[0,0,0]) for p in poses],float)
                if ch=='rotation':values=g.continuous_euler(values)
                ids=[0,len(times)-1] if np.max(np.ptp(values,axis=0))<1e-7 else range(len(times))
                for i in ids:
                    ops.append({'op':'set_keyframe','animation':name,'bone':bone,'channel':ch,'time':float(times[i]),'value':np.round(values[i],9).tolist(),'interpolation':'linear'});count+=1
        counts[name]=count;print('Calculado:',name,count,'chaves',flush=True)
    if not partial:shutil.copy2(SOURCE,FILE)
    ops.append({'op':'set_model_properties','name':FILE.stem});g.dump(OUT/'_cache/ops.json',ops);motor.editar(FILE,ops,lote=500)
    g.dump(OUT/'geracao.json',{'fonte':SOURCE.relative_to(ROOT).as_posix(),'fonte_sha256':g.sha(SOURCE),'saida_sha256':g.sha(FILE),'clipes':CLIPS,'chaves':counts})
    metadata();print('Gravado:',FILE.name,flush=True)


def patch_bones(name,bones):
    """Revisa canais isolados sem regravar os outros ossos do clipe."""
    record=json.loads((OUT/'geracao.json').read_text(encoding='utf-8'))
    if record['saida_sha256']!=g.sha(FILE):raise ValueError('Modelo editado à mão: criar nova versão.')
    m=bbmodelo.ler(FILE);rig=Rig(m);anim=next(a for a in m.animacoes if a['name']==name)
    times=sample_times(rig,name,CLIPS[name]);poses=[rig.pose(name,float(t)) for t in times];ops=[]
    for n in bones:
        animator=anim['animators'].get(m.ossos[n].uuid,{})
        for k in animator.get('keyframes',[]):
            if k['channel'] in ['rotation','position']:ops.append({'op':'remove_keyframe','animation':name,'bone':n,'channel':k['channel'],'time':k['time']})
        for ch,field in [('rotation','rotacao'),('position','posicao')]:
            values=np.array([p[n].get(field,[0,0,0]) for p in poses],float)
            if ch=='rotation':values=g.continuous_euler(values)
            ids=[0,len(times)-1] if np.max(np.ptp(values,axis=0))<1e-7 else range(len(times))
            for i in ids:ops.append({'op':'set_keyframe','animation':name,'bone':n,'channel':ch,'time':float(times[i]),'value':np.round(values[i],9).tolist(),'interpolation':'linear'})
    g.dump(OUT/'_cache/ops-reparo.json',ops);motor.editar(FILE,ops,lote=500)
    saved=bbmodelo.ler(FILE);a=next(a for a in saved.animacoes if a['name']==name)
    record['chaves'][name]=sum(len(x.get('keyframes',[])) for x in a['animators'].values());record['saida_sha256']=g.sha(FILE)
    g.dump(OUT/'geracao.json',record);metadata();print('Canais revistos:',name,', '.join(bones),flush=True)


def metadata():
    d=json.loads((SOURCE.parent/'animacoes.json').read_text(encoding='utf-8'))
    d.update(modelo=FILE.name,fonte=SOURCE.relative_to(ROOT).as_posix(),fonte_sha256=g.sha(SOURCE),saida_sha256=g.sha(FILE),status='golpes-v5-em-avaliacao',validacao='validacao-ataques.json')
    d['golpes']={n:{'duracao':x,'origem':'combat_ready@0','destino':'combat_ready@0','loop':False,'marcadores':EVENTS[n]} for n,x in CLIPS.items()}
    d['sequencia_sugerida']=['attack_right','attack_left','attack_combo']
    d['root_motion']=True
    d['trajetoria_root']={'attack_combo':{'eixo':'Y','inicio':TAKEOFF,'fim':LANDING,'altura':JUMP_HEIGHT,'deslocamento_liquido':0}}
    d['controle_golpes']='Low aprovado com aceleração revista. Direita ascendente e esquerda descendente independentes. Combo com impulso das pernas, corte a 45 graus, volta completa no ar e impacto duplo na queda; penas presas às raízes.'
    d['legado_cross']='attack_cross preservado somente na v4; substituído nesta versão pelos três clipes pedidos.'
    d['referencias_usuario']=['../ataques-v4/'+p for p in ['referencias/cross-eixo-1.png','referencias/cross-eixo-2.png','referencias/low-amplitude.png']]
    d['aprovacoes_parciais']={'attack_low':'Trajetória e peso v4 aprovados; aceleração v5 em avaliação.',
        'attack_left':'Trajetória descendente v4 preservada; clipe independente em avaliação.'}
    g.dump(OUT/'animacoes.json',d)


def main():
    ap=argparse.ArgumentParser()
    for flag in ['estudo','gerar','validar','nativo']:ap.add_argument('--'+flag,action='store_true')
    ap.add_argument('--clipes',nargs='+',choices=list(CLIPS));ap.add_argument('--ossos',nargs='+');a=ap.parse_args();review=module('revisao_golpes_v5','revisar-golpes-pavao-f3-v5.py')
    if a.estudo:review.study(__import__(__name__))
    if a.gerar:
        if a.ossos:
            if not a.clipes or len(a.clipes)!=1:ap.error('--ossos requer exatamente um clipe.')
            patch_bones(a.clipes[0],a.ossos)
        else:bake(a.clipes)
    if a.validar:review.check(__import__(__name__))
    if a.nativo:review.capture(__import__(__name__))


if __name__=='__main__':main()
