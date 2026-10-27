"""F3 v4: cotovelos externos, espadas alinhadas, Cross mais lento e Low amplo."""
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
v3=module('golpes_f3_v3','animar-golpes-pavao-f3-v3.py');v2=v3.v2
g,bbmodelo,motor,render=v3.g,v3.bbmodelo,v3.motor,v3.render
R,point,unit,smooth,blend,track=v3.R,v3.point,v3.unit,v3.smooth,v3.blend,v3.track
Saved,base,SIDES=v3.Saved,v3.base,v3.SIDES
rod=v2.v1.v2.rod
SOURCE=v3.FILE;OUT=ROOT/'modelos/criatura-pavao/f3/ataques-v4';FILE=OUT/'criatura-pavao-e3-ataques-v4.bbmodel'
CLIPS={'attack_low':1.65,'attack_cross':2.40};FPS=120
ACTIVE={'attack_low':[('right',.44,.96)],'attack_cross':[('right',.43,.87),('left',1.15,1.38)]}
EVENTS={'attack_low':{'DamageStart':.42,'HitFrame':.73,'DamageEnd':.98,'RecoveryStart':1.08,'CancelOpen':1.25},
        'attack_cross':{'DamageStart':.41,'HitFrame':.67,'HitFrame2':1.30,'DamageEnd':1.43,'RecoveryStart':1.57,'CancelOpen':1.85}}
LEFT_TILT=15.


def direction_blend(a,b,w):
    if w<=0:return unit(a)
    if w>=1:return unit(b)
    axis=np.cross(a,b);n=np.linalg.norm(axis)
    if n<1e-8:return unit(blend(a,b,w))
    angle=math.degrees(math.acos(float(np.clip(unit(a)@unit(b),-1,1))))
    return rod(axis,angle*w)@unit(a)


class Rig(v2.Rig):
    def __init__(self,m):
        super().__init__(m);self.previous=Saved(bbmodelo.ler(SOURCE));self.cache={}
        self.context='';self.current_time=0.
        self.pole_bias={'attack_low':{'right':15.,'left':0.},'attack_cross':{
            'right':[(0,0),(.24,30),(.32,75),(.47,75),(.70,40),(.88,30),(1.45,30),(1.90,0),(2.4,0)],'left':-65.}}
        self.fan_axis={}
        for side in SIDES:
            n='wing_'+side;anchor=self.anchors[n];tips=[]
            for c in m.cubos:
                if c.osso!=n:continue
                q=np.tile((c.de+c.ate)/2,(2,1));q[:,2]=[c.de[2],c.ate[2]]
                q=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,self.rest),q)
                tips.append(max(q,key=lambda p:np.linalg.norm(p-anchor)))
            self.fan_axis[side]=unit(np.mean(tips,axis=0)-anchor)

    @staticmethod
    def old_time(name,t):
        if name=='attack_low':return t*1.35/CLIPS[name]
        return float(track(t,[(0,0),(.36,.30),(.40,.34),(.88,.52),(1.125,.725),(1.35,.95),(2.40,1.95)]))

    def body(self,name,t):
        old=self.old_time(name,t);p=self.previous.pose(name,old)
        if name=='attack_cross':
            before=self.mats(p);avoid=math.sin(math.pi*float(np.clip((t-.72)/.54,0,1)))**2 if .72<t<1.26 else 0.
            p['neck_1']['rotacao']=np.asarray(p['neck_1']['rotacao'])+[10*avoid,0,0]
            p['neck_2']['rotacao']=np.asarray(p['neck_2']['rotacao'])+[3*avoid,0,0]
            self.set_world(p,'head',before['head'][:3,:3]);return p
        before=self.mats(p);weight=smooth((t-.20)/.36)*(1-smooth((t-1.07)/.58));extra=27*weight
        p['body']['rotacao']=g.forms.euler(R([0,extra,0])@R(p['body']['rotacao']))
        for n,k in [('pelvis',.05),('waist',.10),('torso',.20)]:p[n]['rotacao']=np.asarray(p[n]['rotacao'])+[0,k*extra,0]
        p['tail_1']['rotacao']=np.asarray(p['tail_1']['rotacao'])+[0,-.5*extra,0]
        p['tail_2']['rotacao']=np.asarray(p['tail_2']['rotacao'])+[0,-.2*extra,0]
        targets={};rotations={}
        for s in SIDES:
            oldr=before['foot_'+s][:3,:3];newr=R([0,extra*.60,0])@oldr
            center=point(before['foot_'+s],self.feet[s]);targets[s]=center+oldr@self.toe[s]-newr@self.toe[s]
            floor=float((self.footverts[s]@newr.T+targets[s])[:,1].min())
            if floor<0:targets[s][1]-=floor
            rotations[s]=newr
        z=R(p['body']['rotacao'])[:,2];yaw=math.degrees(math.atan2(z[0],z[2]))
        self.legs_world(p,targets,rotations,yaw)
        self.set_world(p,'head',R([0,extra*.35,0])@before['head'][:3,:3])
        # O tronco e os apoios dão amplitude sem retirar a espada passiva do ombro.
        return p

    def reset_guard(self,p,side):
        for n in ['arm_','forearm_','hand_']:p[n+side]['rotacao']=copy.deepcopy(self.guard[n+side]['rotacao'])

    def anatomical_arm(self,p,side,direction,normal,flex,alignment=1.,reference=None):
        """Plano do cotovelo externo independente da orientação do fio da espada."""
        direction=unit(direction);s=-1 if side=='left' else 1
        mat=self.mats(p) if reference is None else reference
        a,b,c=[point(mat[n+side],self.m.ossos[n+side].origem) for n in ['arm_','forearm_','hand_']]
        oldd=unit(c-b);oldu=unit(b-a);oldbend=unit(oldu-oldd*(oldu@oldd))
        forearm=direction_blend(oldd,direction,alignment)
        pole_local=np.array([s*.85,-.08,.60])
        pole=mat['torso'][:3,:3]@pole_local
        pole=unit(pole-forearm*(pole@forearm))
        oldbend=unit(oldbend-forearm*(oldbend@forearm))
        pole_weight=alignment
        if self.context=='attack_cross':
            bend=blend(oldbend,pole,pole_weight)
            length=float(np.linalg.norm(bend))
            if length<.3:
                bend+=np.cross(forearm,oldbend)*.3*math.sin(math.pi*pole_weight)*smooth((.3-length)/.3)
            bend=unit(bend)
        else:bend=direction_blend(oldbend,pole,pole_weight)
        bend=unit(bend-forearm*(bend@forearm))
        bias=self.pole_bias.get(self.context,{}).get(side,0)
        if isinstance(bias,list):bias=float(track(self.current_time,bias))
        bend=rod(forearm,bias*alignment)@bend
        upper=forearm*math.cos(math.radians(flex))+bend*math.sin(math.radians(flex))
        plane=unit(np.cross(upper,forearm));v1,_,axis,theta=self.hinges[side]
        shoulder=g.frame(upper,plane)@g.frame(v1,axis).T
        F=rod(axis,flex-theta);forearm_rotation=shoulder@F
        p['arm_'+side]['rotacao']=g.forms.euler(mat['torso'][:3,:3].T@shoulder)
        p['forearm_'+side]['rotacao']=g.forms.euler(F)
        sword=self.direction_rotation(side,direction,normal)
        hand_rotation=sword@self.bind[side].T
        p['hand_'+side]['rotacao']=g.forms.euler(forearm_rotation.T@hand_rotation)
        weapon=self.weapons[side]
        p[weapon['name']]={'rotacao':g.forms.euler(self.bind[side]),'posicao':self.grips[side]-weapon['grip']}
        wrist=a+shoulder@v1+forearm_rotation@self.hinges[side][1]
        grip=wrist+hand_rotation@(self.grips[side]-self.m.ossos['hand_'+side].origem)
        return float((self.weaponverts[side]@sword.T+grip)[:,1].min())

    def floor_direction(self,p,side,horizontal,roll,flex,alignment,clearance):
        original=copy.deepcopy(p);horizontal=unit(horizontal);reference=self.mats(original)
        def evaluate(y):
            q=copy.deepcopy(original);direction=horizontal*math.sqrt(1-y*y)+[0,y,0]
            normal0=unit(np.array([0.,1.,0.])-direction*direction[1]);normal=rod(direction,roll)@normal0
            floor=self.anatomical_arm(q,side,direction,normal,flex,alignment,reference=reference)
            return floor,q
        lo,hi=-.93,.85;f0,q=evaluate(lo);f1,q1=evaluate(hi)
        if not f0<=clearance<=f1:raise ValueError(('Sem altura de lâmina',side,f0,f1,clearance))
        for _ in range(23):
            mid=(lo+hi)/2;floor,q=evaluate(mid)
            if floor<clearance:lo=mid
            else:hi=mid
        p.update(q)

    def low(self,p,t):
        d=CLIPS['attack_low'];w=smooth(t/.39)*(1-smooth((t-1.10)/(d-1.10)))
        self.reset_guard(p,'right')
        az=float(track(t,[(0,self.angle0['right']),(.32,75),(.43,92),(.67,174),(.96,260),(1.07,265),(1.30,170),(d,self.angle0['right'])]))
        flex=float(blend(self.guard_flex['right'],12,w));roll=float(blend(self.guard_roll['right'],0,w))
        clearance=float(track(t,[(0,0),(.30,1.2),(.43,1.3),(.97,1.3),(1.13,2.2),(1.40,1),(d,0)]))
        a=math.radians(az);self.floor_direction(p,'right',[math.sin(a),0,math.cos(a)],roll,flex,w,clearance)

    @staticmethod
    def cross_geometry(sigma):
        a=math.radians(sigma);beta=math.radians(30+sigma*10/70);k=10/70
        sa,ca,sb,cb=math.sin(a),math.cos(a),math.sin(beta),math.cos(beta)
        direction=np.array([-cb*sa,sb*sa,-ca]);tangent=np.array([sb*k*sa-cb*ca,cb*k*sa+sb*ca,sa])
        return direction,-unit(np.cross(direction,tangent))

    def cross_right(self,p,t):
        self.reset_guard(p,'right');d=CLIPS['attack_cross']
        w=smooth(t/.40)*(1-smooth((t-1.10)/.50))
        target_flex=float(track(t,[(0,12),(.90,12),(1.06,62),(1.45,48),(2.05,55),(d,55)]))
        flex=float(blend(self.guard_flex['right'],target_flex,w))
        if t<.40:
            u=smooth(t/.40);start,normal=self.cross_geometry(-70)
            startaz=math.degrees(math.atan2(start[0],start[2]));ref=unit(np.array([0.,1.,0.])-start*start[1])
            startroll=math.degrees(math.atan2(float(start@np.cross(ref,normal)),float(ref@normal)))
            startroll+=360*round((self.guard_roll['right']-startroll)/360)
            a=math.radians(float(blend(self.angle0['right'],startaz,u)))
            # A borda sai livre do piso antes da fatiada mais lenta.
            self.floor_direction(p,'right',[math.sin(a),0,math.cos(a)],float(blend(self.guard_roll['right'],startroll,u)),flex,w,3*u+1.2*math.sin(math.pi*u)**2)
        elif t<=.91:
            sigma=float(track(t,[(.40,-70),(.45,-66),(.68,0),(.91,60)]));direction,normal=self.cross_geometry(sigma)
            self.anatomical_arm(p,'right',direction,normal,12,1.)
            self.clear_floor(p,'right',target=.3)
        else:
            # Reabre à direita para deixar a diagonal esquerda passar limpa.
            end_dir,end_normal=self.cross_geometry(60)
            end_az=math.degrees(math.atan2(end_dir[0],end_dir[2]));end_elev=math.degrees(math.asin(end_dir[1]))
            if end_az<0:end_az+=360
            ref=unit(np.array([0.,1.,0.])-end_dir*end_dir[1])
            end_roll=math.degrees(math.atan2(float(end_dir@np.cross(ref,end_normal)),float(ref@end_normal)))
            end_roll+=360*round((self.guard_roll['right']-end_roll)/360)
            az=float(track(t,[(.91,end_az),(1.08,175),(1.28,100),(1.62,95),(2.05,65),(d,self.angle0['right'])]))
            elev=float(track(t,[(.91,end_elev),(.995,12),(1.18,32),(1.62,20),(2.05,-8),(d,math.degrees(math.asin(self.dy0['right'])))]))
            a,e=np.radians([az,elev]);direction=[math.sin(a)*math.cos(e),math.sin(e),math.cos(a)*math.cos(e)]
            normal0=unit(np.array([0.,1.,0.])-np.asarray(direction)*direction[1]);roll=float(blend(self.guard_roll['right'],end_roll,w))
            held=self.mats(p)[self.weapons['right']['name']][:3,:3]
            sword=g.slerp(held,self.direction_rotation('right',direction,rod(direction,roll)@normal0),w)
            direction=sword@self.weapons['right']['frame'][:,1];normal=sword@self.weapons['right']['frame'][:,2]
            self.anatomical_arm(p,'right',direction,normal,flex,w)
            self.clear_floor(p,'right',target=.001)

    def cross_left(self,p,t):
        self.reset_guard(p,'left');d=CLIPS['attack_cross']
        if t<=.91:return
        mat=self.mats(p);held=mat[self.weapons['left']['name']][:3,:3]
        w=smooth((t-.91)/.24)*(1-smooth((t-1.62)/(d-1.62)))
        flex=float(blend(self.guard_flex['left'],12,w))
        elev=float(track(t,[(0,168),(.91,168),(1.10,110),(1.20,78),(1.34,12),(1.48,-25),(1.62,-25),(1.98,65),(d,168)]))
        e=math.radians(elev);tilt=LEFT_TILT*smooth((t-.91)/.24)*(1-smooth((t-1.62)/(d-1.62)))
        turn=R([0,0,tilt]);direction=turn@np.array([0,math.sin(e),-math.cos(e)]);normal=turn@np.array([1.,0,0])
        blade_weight=w if t<=1.62 else 1-smooth((t-2.02)/.38)
        sword=g.slerp(held,self.direction_rotation('left',direction,normal),blade_weight)
        direction=sword@self.weapons['left']['frame'][:,1];normal=sword@self.weapons['left']['frame'][:,2]
        self.anatomical_arm(p,'left',direction,normal,flex,w)
        self.clear_floor(p,'left',target=.001)

    def flare_elbow_fan(self,p,t):
        w=smooth((t-.16)/.18)*(1-smooth((t-1.38)/.22))
        if w<=0:return
        mat=self.mats(p);n='wing_right'
        outward=unit(mat['torso'][:3,:3]@np.array([1.,-.05,.45]))
        normal=mat['torso'][:3,:3]@np.array([0.,0.,-1.])
        target=g.frame(outward,normal)@g.frame(self.fan_axis['right'],[1,0,0]).T
        rotation=g.slerp(mat[n][:3,:3],target,w)
        self.set_world(p,n,rotation)

    def pose(self,name,t):
        key=(name,round(t,9))
        if key in self.cache:return copy.deepcopy(self.cache[key])
        if t<=0 or t>=CLIPS[name]-1e-9:return copy.deepcopy(self.guard)
        self.context=name;self.current_time=t
        p=self.body(name,t)
        if name=='attack_low':self.low(p,t)
        else:self.cross_right(p,t);self.cross_left(p,t);self.flare_elbow_fan(p,t)
        self.anchored_wings(p);self.cache[key]=copy.deepcopy(p);return p


def bake(names=None):
    names=names or list(CLIPS);partial=set(names)!=set(CLIPS)
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'_cache').mkdir(exist_ok=True)
    if partial and not FILE.exists():raise ValueError('Gere os dois golpes primeiro.')
    if FILE.exists():
        record=json.loads((OUT/'geracao.json').read_text(encoding='utf-8'))
        if record['saida_sha256']!=g.sha(FILE):raise ValueError('Saída editada; criar nova versão.')
    m=bbmodelo.ler(FILE if partial else SOURCE);rig=Rig(m);ops=[];counts=record['chaves'].copy() if partial else {}
    for name in names:
        d=CLIPS[name];times=np.unique(np.round(np.r_[np.linspace(0,d,round(d*FPS)+1),list(EVENTS[name].values())],9))
        poses=[rig.pose(name,float(t)) for t in times];ops.extend([{'op':'remove_animation','animation':name},
            {'op':'add_animation','name':name,'length':d,'loop':'once','snapping':120}]);count=0
        for bone in m.ossos:
            for channel,field in [('rotation','rotacao'),('position','posicao')]:
                values=np.array([p[bone].get(field,[0,0,0]) for p in poses],float)
                if channel=='rotation':values=g.continuous_euler(values)
                ids=[0,len(times)-1] if np.max(np.ptp(values,axis=0))<1e-7 else range(len(times))
                for i in ids:
                    ops.append({'op':'set_keyframe','animation':name,'bone':bone,'channel':channel,'time':float(times[i]),
                        'value':np.round(values[i],9).tolist(),'interpolation':'linear'});count+=1
        counts[name]=count;print('Calculado:',name,count,'chaves',flush=True)
    if not partial:shutil.copy2(SOURCE,FILE)
    ops.append({'op':'set_model_properties','name':FILE.stem});g.dump(OUT/'_cache/ops.json',ops);motor.editar(FILE,ops,lote=500)
    g.dump(OUT/'geracao.json',{'fonte':SOURCE.relative_to(ROOT).as_posix(),'fonte_sha256':g.sha(SOURCE),'saida_sha256':g.sha(FILE),
        'clipes':CLIPS,'chaves':counts,'cross_inclinacao_esquerda':LEFT_TILT,'low_arco_azimute':[92,260]})
    metadata();print('Gravado:',FILE.name,flush=True)


def metadata():
    data=json.loads((SOURCE.parent/'animacoes.json').read_text(encoding='utf-8'))
    data.update(modelo=FILE.name,fonte=SOURCE.relative_to(ROOT).as_posix(),fonte_sha256=g.sha(SOURCE),saida_sha256=g.sha(FILE),
        status='low-cross-v4-em-avaliacao',validacao='validacao-ataques.json')
    data['golpes']={n:{'duracao':d,'origem':'combat_ready@0','destino':'combat_ready@0','loop':False,'marcadores':EVENTS[n]} for n,d in CLIPS.items()}
    data.pop('preservacao_cross',None);data['aprovacoes_parciais']={'attack_cross_esquerdo':'Aprovação vertical v2/v3 substituída pelo pedido de diagonal leve na v4.'}
    data['controle_golpes']='Espadas prolongam antebraços; plano do cotovelo independente do fio. Low amplo com rotação do tronco e apoios. Cross direito mais lento, recuperação flexiona o braço e abre as penas presas ao cotovelo; esquerda inclina 15 graus à direita.'
    data['referencias_usuario']=['referencias/cross-eixo-1.png','referencias/cross-eixo-2.png','referencias/low-amplitude.png']
    g.dump(OUT/'animacoes.json',data)


def main():
    ap=argparse.ArgumentParser()
    for name in ['estudo','gerar','validar','nativo']:ap.add_argument('--'+name,action='store_true')
    ap.add_argument('--clipes',nargs='+',choices=list(CLIPS));args=ap.parse_args();review=module('revisao_golpes_v4','revisar-golpes-pavao-f3-v4.py')
    if args.estudo:review.study(__import__(__name__))
    if args.gerar:bake(args.clipes)
    if args.validar:review.check(__import__(__name__))
    if args.nativo:review.capture(__import__(__name__))


if __name__=='__main__':main()
