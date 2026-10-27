"""Três golpes originais da F3, a partir da guarda e corridas aprovadas.

    Escreve somente pelo motor externo, em nova versão protegida por hash.
"""
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
    s=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
base=module('movimento_f3','animar-corrida-pavao-f3.py')
g,v2,bbmodelo,motor,render=base.g,base.v2,base.bbmodelo,base.motor,base.render
R,point,unit,smooth,blend=base.R,base.point,base.unit,base.smooth,base.blend
Saved=base.Saved
SOURCE=base.FILE
OUT=ROOT/'modelos/criatura-pavao/f3/ataques-v1'
FILE=OUT/'criatura-pavao-e3-ataques-v1.bbmodel'
base.v3.SOURCE=SOURCE
SIDES=base.SIDES
CLIPS={'attack_low':1.15,'attack_cross':1.50,'attack_spin':1.75}
FPS=120
EVENTS={'attack_low':{'HitFrame':.43,'DamageStart':.32,'DamageEnd':.54,'CancelOpen':.72,'RecoveryStart':.62},
        'attack_cross':{'HitFrame':.38,'HitFrame2':.76,'DamageStart':.29,'DamageEnd':.86,'CancelOpen':1.03,'RecoveryStart':.90},
        'attack_spin':{'HitFrame':.72,'DamageStart':.40,'DamageEnd':1.08,'CancelOpen':1.28,'RecoveryStart':1.10}}


def track(t,keys):
    """Hermite monotônico por eixo; sem pausas artificiais entre os controles."""
    ts=np.array([x for x,y in keys],float);ys=np.array([y for x,y in keys],float)
    if t<=ts[0]:return ys[0].copy()
    if t>=ts[-1]:return ys[-1].copy()
    slopes=np.diff(ys,axis=0)/np.diff(ts).reshape((-1,)+(1,)*(ys.ndim-1))
    tang=np.zeros_like(ys)
    for i in range(1,len(ts)-1):
        a,b=slopes[i-1],slopes[i]
        den=a+b
        tang[i]=np.where(a*b>0,2*a*b/np.where(abs(den)>1e-12,den,1),0.)
    i=int(np.searchsorted(ts,t,side='right')-1);d=ts[i+1]-ts[i];u=(t-ts[i])/d
    return (2*u**3-3*u*u+1)*ys[i]+(u**3-2*u*u+u)*d*tang[i]+(-2*u**3+3*u*u)*ys[i+1]+(u**3-u*u)*d*tang[i+1]


class Rig(base.Rig):
    def __init__(self,m):
        super().__init__(m)
        self.guard=self.saved.pose('combat_ready',0);self.guardmat=self.mats(self.guard)
        self.offset={};self.reference={};self.angle0={};self.dy0={};self.target_cache={}
        for side in SIDES:
            w=self.weapons[side];wm=self.guardmat[w['name']]
            sh=point(self.guardmat['torso'],m.ossos['arm_'+side].origem)
            self.offset[side]=point(wm,w['grip'])-sh;self.reference[side]=wm.copy()
            direction=wm[:3,:3]@w['frame'][:,1]
            self.angle0[side]=math.degrees(math.atan2(direction[0],direction[2]));self.dy0[side]=float(direction[1])
        self.contacts={s:point(self.guardmat['foot_'+s],self.feet[s]) for s in SIDES}
        self.toe={}
        for s in SIDES:
            candidates=self.footverts[s][self.footverts[s][:,1]<self.footverts[s][:,1].min()+.02]
            self.toe[s]=candidates[np.argmin(candidates[:,2])]

    def natural_arm(self,p,side,grip,handrot,pref,record=True):
        before=self.max_unreachable
        value=super().natural_arm(p,side,grip,handrot,pref,record=record)
        if not record:self.max_unreachable=before  # sondagens do rolamento não são poses finais
        return value

    def heading(self,p):
        z=self.mats(p)['torso'][:3,2];return math.degrees(math.atan2(z[0],z[2]))

    def body_pose(self,name,t):
        d=CLIPS[name];p=copy.deepcopy(self.guard)
        if name=='attack_low':
            yaw=float(track(t,[(0,0),(.20,-15),(.31,-6),(.51,30),(.64,34),(.92,4),(d,0)]))
            shift=track(t,[(0,[0,0,0]),(.23,[-.8,-4.8,.5]),(.46,[1.3,-4.3,-2.2]),(.64,[1.5,-3.3,-1.7]),(.92,[.2,-.6,-.4]),(d,[0,0,0])])
            pitch=float(track(t,[(0,0),(.22,-8),(.44,-10),(.62,-4),(.88,2),(d,0)]))
            twist=float(track(t,[(0,0),(.25,-10),(.47,12),(.64,6),(.90,-2),(d,0)]))
            roll=float(track(t,[(0,0),(.23,-3),(.48,4),(.72,1),(d,0)]))
        elif name=='attack_cross':
            yaw=float(track(t,[(0,0),(.18,-15),(.39,20),(.54,25),(.76,-20),(.88,-28),(1.16,3),(d,0)]))
            shift=track(t,[(0,[0,0,0]),(.20,[-.8,-2.8,.4]),(.39,[1.1,-1.5,-1.3]),(.55,[.8,-2.0,-1.8]),(.77,[-1.5,-3.2,-2.3]),(.94,[-1.1,-2.4,-1.6]),(1.2,[.2,-.4,-.3]),(d,[0,0,0])])
            pitch=float(track(t,[(0,0),(.19,-5),(.40,0),(.58,2),(.78,-9),(.94,-5),(1.18,2),(d,0)]))
            twist=float(track(t,[(0,0),(.21,-9),(.36,10),(.55,5),(.73,-11),(.89,-5),(1.13,2),(d,0)]))
            roll=float(track(t,[(0,0),(.19,-2),(.39,3),(.60,1),(.79,-4),(.97,-1),(d,0)]))
        else:
            yaw=float(track(t,[(0,0),(.27,-18),(.34,-15),(.63,120),(.88,280),(1.08,360),(d,360)]))
            shift=track(t,[(0,[0,0,0]),(.27,[-3.0,-4.0,0]),(.48,[-3.5,-4.1,0]),(.85,[-3.5,-3.4,0]),(1.09,[-2.7,-4.3,0]),(1.35,[-.4,-1.0,0]),(d,[0,0,0])])
            pitch=float(track(t,[(0,0),(.29,-9),(.61,-6),(.87,-3),(1.10,-8),(1.34,2),(d,0)]))
            twist=float(track(t,[(0,0),(.29,-9),(.49,-12),(.76,8),(1.03,10),(1.22,-5),(d,0)]))
            roll=float(track(t,[(0,0),(.29,-3),(.56,2),(.83,3),(1.08,-3),(1.36,1),(d,0)]))
        p['body']['posicao']=np.asarray(self.guard['body']['posicao'])+shift
        if name=='attack_spin':
            # Y mantém uma volta contínua. Decompor Ry*Rz perto de 90° gerava
            # grande curvatura de Euler entre amostras apesar da pose suave.
            p['body']['rotacao']=np.array([self.guard['body']['rotacao'][0]+pitch,yaw,roll])
        else:p['body']['rotacao']=g.forms.euler(R([0,yaw,0])@R([self.guard['body']['rotacao'][0]+pitch,0,roll]))
        p['pelvis']['rotacao']=np.asarray(self.guard['pelvis']['rotacao'])+[pitch*.12,twist*.28,-roll*.30]
        p['waist']['rotacao']=np.asarray(self.guard['waist']['rotacao'])+[pitch*.22,twist*.25,roll*.16]
        p['torso']['rotacao']=np.asarray(self.guard['torso']['rotacao'])+[pitch*.18,twist,roll*.25]
        envelope=math.sin(math.pi*t/d)**2
        # Cabeça acompanha a ação e mantém inércia; o bico não executa golpes.
        p['neck_1']['rotacao']=np.asarray(self.guard['neck_1']['rotacao'])+[-.3*pitch,-.3*twist,0]
        p['neck_2']['rotacao']=np.asarray(self.guard['neck_2']['rotacao'])+[-.1*pitch,-.12*twist,0]
        self.set_world(p,'head',R([0,yaw-.30*twist,0])@R([-1+.14*pitch,0,.1*roll]))
        p['tail_1']['rotacao']=np.asarray(self.guard['tail_1']['rotacao'])+[-.40*pitch,-.85*twist,-.6*roll]
        p['tail_2']['rotacao']=np.asarray(self.guard['tail_2']['rotacao'])+[1.8*envelope,-.45*twist,-.2*roll]
        for side,s in [('left',-1),('right',1)]:
            for i in [1,2]:
                n=f'feather_{side}_{i}'
                p[n]['rotacao']=np.asarray(self.guard[n]['rotacao'])+[-.22*pitch+(1+i*.4)*math.sin(2*math.pi*t/d)*envelope,
                                                                           -s*.12*twist,s*.15*roll]
            n='wing_'+side
            p[n]['rotacao']=np.asarray(self.guard[n]['rotacao'])+[3*envelope,s*(10 if name=='attack_spin' else 3)*envelope,s*4*envelope]
            for n in self.anchors:
                if n.startswith('back') and side in n:
                    p[n]['rotacao']=np.asarray(self.guard[n]['rotacao'])+[2.8*math.sin(2*math.pi*t/d)*envelope,-s*.15*twist,0]
        return p,yaw

    def legs_world(self,p,targets,rotations,yaw):
        for side,s in [('left',-1),('right',1)]:
            r=rotations[side];hock=self.m.ossos['foot_'+side].origem
            target=targets[side]+r@(hock-self.feet[side])
            hip=point(self.mats(p)['pelvis'],self.m.ossos['leg_'+side].origem)
            self.two_bone(p,['leg_'+side,'shin_'+side,'foot_'+side],target,hip+R([0,yaw,0])@np.array([s*1.5,0,-20]))
            self.set_world(p,'foot_'+side,r)

    def foot_targets(self,name,t,yaw):
        d=CLIPS[name];feet={s:self.contacts[s].copy() for s in SIDES};rots={s:np.eye(3) for s in SIDES}
        if name=='attack_spin':
            load=smooth(t/.29);restore=smooth((t-1.12)/(d-1.12));w=load*(1-restore)
            left_ref=blend(self.contacts['left'],[-3.5,0,.8],w)
            toe=self.toe['left'];r=R([0,yaw,0])@R([-13*w,0,0])
            feet['left']=left_ref+toe-r@toe;rots['left']=r
            if 0<t<.29:feet['left'][1]+=1.4*math.sin(math.pi*t/.29)**2
            if 1.12<t<d:feet['left'][1]+=1.3*math.sin(math.pi*(t-1.12)/(d-1.12))**2
            f=float(np.clip((t-.29)/.82,0,1));lift=2.6*math.sin(math.pi*f)**2
            axis=np.array([-3.5,0,.8]);offset=self.contacts['right']-axis
            foot_yaw=yaw+18*(1-smooth((t-.29)/.25)) if t>=.29 else 0.
            moving=axis+R([0,foot_yaw,0])@offset;moving[1]=lift
            travel=smooth((t-.29)/.08)
            feet['right']=blend(self.contacts['right'],moving,travel)*(1-restore)+self.contacts['right']*restore
            rots['right']=R([0,foot_yaw,0])
        else:
            if name=='attack_low':
                step=float(track(t,[(0,0),(.12,0),(.29,1),(.69,1),(.99,0),(d,0)]));height=0.
                if .12<t<.29:height=1.6*math.sin(math.pi*(t-.12)/.17)**2
                if .69<t<.99:height=1.3*math.sin(math.pi*(t-.69)/.30)**2
                feet['right']+=[.4*step,height,-3.2*step]
                rolls={'left':-10*math.sin(math.pi*t/d)**2,'right':0}
            else:
                a=float(track(t,[(0,0),(.11,0),(.28,1),(.94,1),(1.17,0),(d,0)]))
                b=float(track(t,[(0,0),(.46,0),(.66,1),(1.20,1),(1.45,0),(d,0)]))
                hr=1.6*math.sin(math.pi*(t-.11)/.17)**2 if .11<t<.28 else 0.
                hl=1.8*math.sin(math.pi*(t-.46)/.20)**2 if .46<t<.66 else 0.
                if .94<t<1.17:hr=1.1*math.sin(math.pi*(t-.94)/.23)**2
                if 1.20<t<1.45:hl=1.0*math.sin(math.pi*(t-1.20)/.25)**2
                feet['right']+=[.5*a,hr,-2.3*a];feet['left']+=[-.4*b,hl,-3.4*b]
                rolls={'left':-7*a*(1-b),'right':-6*b*(1-smooth((t-.92)/.58))}
            for side in SIDES:
                r=R([0,yaw*.35,0])@R([rolls[side],0,0]);toe=self.toe[side]
                feet[side]+=toe-r@toe;rots[side]=r
        # Mantém os dedos mais baixos sobre o piso sem alongar os ossos.
        for side in SIDES:
            bottom=float((self.footverts[side]@rots[side].T+feet[side])[:,1].min())
            if bottom<0:feet[side][1]-=bottom
        return feet,rots

    def blade(self,p,side,offset,azimuth,dy,pref,clearance=0.,hug_floor=False):
        heading=self.heading(p);turn=R([0,heading,0])
        shoulder=point(self.mats(p)['torso'],self.m.ossos['arm_'+side].origem)
        grip=shoulder+turn@np.asarray(offset,float)
        a=math.radians(azimuth);horizontal=turn@np.array([math.sin(a),0,math.cos(a)])
        def evaluate(y):
            direction=horizontal*math.sqrt(max(0,1-y*y))+[0,y,0]
            rot=self.direction_rotation(side,direction,[0,1,0])
            rot=self.aligned_roll(p,side,grip,rot,pref)
            return float((self.weaponverts[side]@rot.T+grip)[:,1].min()),rot
        low=-.94 if hug_floor else float(dy);bottom,rot=evaluate(low)
        if hug_floor or bottom<clearance:
            hi=.50;f0=bottom-clearance;f1,r1=evaluate(hi);f1-=clearance
            if f0>=0:rot=evaluate(low)[1]
            else:
                assert f1>0,('Sem altura de lâmina',side,grip,clearance)
                for j in range(20):
                    y=(low*f1-hi*f0)/(f1-f0)
                    if not low<y<hi or j%5==4:y=(low+hi)/2
                    value,rot=evaluate(y);f=value-clearance
                    if abs(f)<1e-5:break
                    if f<0:low,f0=y,f
                    else:hi,f1=y,f
        self.held(p,side,grip,rot,pref)
        hand=self.mats(p)['hand_'+side]
        self.weapon(p,side,point(hand,self.grips[side]),hand[:3,:3]@self.bind[side])

    def attack_arms(self,p,name,t):
        d=CLIPS[name]
        if name=='attack_low':
            a=float(track(t,[(0,self.angle0['right']),(.18,38),(.28,68),(.49,218),(.65,232),(.88,80),(d,self.angle0['right'])]))
            off=track(t,[(0,self.offset['right']),(.22,[5,-10,-2]),(.43,[-2,-8,-7]),(.60,[-3,-7,-7]),(.83,[6,-7,-4]),(d,self.offset['right'])])
            clearance=float(track(t,[(0,0),(.16,.6),(.30,1.25),(.54,1.1),(.72,5.0),(.92,3),(d,0)]))
            w=math.sin(math.pi*t/d)**2;pref=g.slerp(R(self.guard['arm_right']['rotacao']),R([-25,0,25]),w)
            self.blade(p,'right',off,a,-.3,pref,clearance,hug_floor=True)
            # A arma esquerda continua apoiada: herda o torso e contrabalança o corte.
        elif name=='attack_cross':
            w=math.sin(math.pi*t/d)**2
            off=track(t,[(0,self.offset['right']),(.18,[5,-9,-3]),(.37,[3,-3,-7]),(.49,[-2,0,-8]),(.64,[7,-3,-5]),(.96,[7,-4,-4]),(1.18,[5,-9,0]),(d,self.offset['right'])])
            a=float(track(t,[(0,self.angle0['right']),(.19,55),(.37,155),(.48,184),(.64,118),(.94,110),(1.18,65),(d,self.angle0['right'])]))
            dy=float(track(t,[(0,self.dy0['right']),(.17,-.23),(.37,.22),(.47,.47),(.67,.40),(.96,.31),(1.18,-.12),(d,self.dy0['right'])]))
            pref=g.slerp(R(self.guard['arm_right']['rotacao']),R([-25,0,40]),w)
            self.blade(p,'right',off,a,dy,pref,.8*math.sin(math.pi*t/d)**2)
            off=track(t,[(0,self.offset['left']),(.24,self.offset['left']),(.45,[-6,7,-2]),(.57,[-6,6,-5]),(.75,[-2,0,-8]),(.88,[0,-3,-9]),(1.10,[-7,5,-4]),(d,self.offset['left'])])
            a=float(track(t,[(0,self.angle0['left']),(.24,self.angle0['left']),(.46,-85),(.58,-105),(.77,-166),(.88,-202),(1.10,-74),(d,self.angle0['left'])]))
            dy=float(track(t,[(0,self.dy0['left']),(.24,self.dy0['left']),(.46,.28),(.58,.38),(.77,-.16),(.88,-.34),(1.10,.25),(d,self.dy0['left'])]))
            pref=g.slerp(R(self.guard['arm_left']['rotacao']),R([-25,0,-70]),w)
            self.blade(p,'left',off,a,dy,pref,.5*math.sin(math.pi*t/d)**2)
        else:
            opening=smooth(t/.32);closing=smooth((t-1.11)/(d-1.11));w=opening*(1-closing)
            for side,s in [('left',-1),('right',1)]:
                off=blend(self.offset[side],[s*7.5,-2 if side=='left' else -8,-2.5],w)
                a=float(blend(self.angle0[side],s*74,w))
                pref=g.slerp(R(self.guard['arm_'+side]['rotacao']),R([-30,0,s*60]),w)
                if side=='right':self.blade(p,side,off,a,-.3,pref,1.2*w,hug_floor=True)
                else:self.blade(p,side,off,a,float(blend(self.dy0[side],.02,w)),pref)

    def pose(self,name,t):
        key=(name,round(t,9))
        if key in self.cache:return copy.deepcopy(self.cache[key])
        if t<=0 or t>=CLIPS[name]-1e-9:return copy.deepcopy(self.guard)
        p,yaw=self.body_pose(name,t);feet,rots=self.foot_targets(name,t,yaw)
        self.legs_world(p,feet,rots,yaw)
        self.attack_arms(p,name,t);self.anchored_wings(p)
        self.cache[key]=copy.deepcopy(p);return p


def bake(names=None):
    names=names or list(CLIPS);partial=set(names)!=set(CLIPS)
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'_cache').mkdir(exist_ok=True)
    if partial and not FILE.exists():raise ValueError('Gere os três golpes antes de atualizar um clipe isolado.')
    if FILE.exists():
        record=json.loads((OUT/'geracao.json').read_text(encoding='utf-8'))
        if record['saida_sha256']!=g.sha(FILE):raise ValueError('Saída editada; criar outra versão.')
    m=bbmodelo.ler(FILE if partial and FILE.exists() else SOURCE);rig=Rig(m);ops=[]
    counts=record['chaves'].copy() if partial else {}
    for name in names:
        duration=CLIPS[name]
        times=np.unique(np.round(np.r_[np.linspace(0,duration,round(duration*FPS)+1),list(EVENTS[name].values())],9))
        poses=[rig.pose(name,float(t)) for t in times]
        if partial:ops.append({'op':'remove_animation','animation':name})
        ops.append({'op':'add_animation','name':name,'length':duration,'loop':'once','snapping':120});count=0
        for n in m.ossos:
            for channel,field in [('rotation','rotacao'),('position','posicao')]:
                values=np.array([p[n].get(field,[0,0,0]) for p in poses],float)
                if channel=='rotation':values=g.continuous_euler(values)
                indices=[0,len(times)-1] if np.max(np.ptp(values,axis=0))<1e-7 else range(len(times))
                for i in indices:
                    ops.append({'op':'set_keyframe','animation':name,'bone':n,'channel':channel,'time':float(times[i]),
                                'value':np.round(values[i],9).tolist(),'interpolation':'linear'});count+=1
        counts[name]=count;print('Calculado:',name,count,'chaves',flush=True)
    assert rig.max_unreachable<.01,('Alvo além da anatomia',rig.max_unreachable,rig.reach)
    if not partial:shutil.copy2(SOURCE,FILE)
    ops.append({'op':'set_model_properties','name':FILE.stem})
    g.dump(OUT/'_cache/ops.json',ops);motor.editar(FILE,ops,lote=500)
    g.dump(OUT/'geracao.json',{'fonte':SOURCE.relative_to(ROOT).as_posix(),'fonte_sha256':g.sha(SOURCE),
        'saida_sha256':g.sha(FILE),'clipes':CLIPS,'chaves':counts,'operacoes_ultima_gravacao':len(ops),
        'clipes_ultima_gravacao':names,'alcance_excedido':rig.max_unreachable})
    metadata();print('Gravado:',FILE.name,flush=True)


def metadata():
    data=json.loads((SOURCE.parent/'animacoes.json').read_text(encoding='utf-8'))
    data.update(modelo=FILE.name,fonte=SOURCE.relative_to(ROOT).as_posix(),fonte_sha256=g.sha(SOURCE),
                saida_sha256=g.sha(FILE),status='ataques-f3-em-avaliacao',validacao='validacao-ataques.json')
    data['aprovados']=list(dict.fromkeys(data.get('aprovados',[])+list(base.CLIPS)))
    data['corridas']['aprovacao']='Seis clipes aprovados pelo usuário em 27/10/2026, antes dos golpes.'
    data['golpes']={n:{'duracao':d,'loop':False,'origem':'combat_ready@0','destino':'combat_ready@0','marcadores':EVENTS[n]} for n,d in CLIPS.items()}
    data['golpes']['direcao']='Espadas/penas; sem ataque com o bico. Talho baixo, cruzado em dois tempos, giro de ceifa.'
    data['golpes']['integracao']='Somente clipes e marcadores propostos. Dano/hitboxes/VFX/lógica de combate ficam para a integração futura.'
    data['referencias_ataques']=['Guarda/marcha/corridas aprovadas da própria F3',
        'https://www.oakeshott.org/wp-content/uploads/2016/10/Figueiredo_Montante_Translation_Myers_and_Hick_v2.pdf']
    g.dump(OUT/'animacoes.json',data)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--estudo',action='store_true');ap.add_argument('--gerar',action='store_true')
    ap.add_argument('--validar',action='store_true');ap.add_argument('--nativo',action='store_true')
    ap.add_argument('--previas',action='store_true')
    ap.add_argument('--clipes',nargs='+',choices=list(CLIPS));args=ap.parse_args()
    review=module('conferencia_golpes_f3','revisar-golpes-pavao-f3.py')
    if args.estudo:review.study(__import__(__name__))
    if args.gerar:bake(args.clipes)
    if args.validar:review.check(__import__(__name__))
    if args.previas:review.offline(__import__(__name__))
    if args.nativo:review.capture(__import__(__name__))


if __name__=='__main__':main()
