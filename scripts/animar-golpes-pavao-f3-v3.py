"""F3 v3: espada prolonga o antebraço no Low; Cross direito em arco diagonal."""
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
v2=module('golpes_f3_v2','animar-golpes-pavao-f3-v2.py')
g,bbmodelo,motor,render=v2.g,v2.bbmodelo,v2.motor,v2.render
R,point,unit,smooth,blend,track=v2.R,v2.point,v2.unit,v2.smooth,v2.blend,v2.track
Saved,base,SIDES=v2.Saved,v2.base,v2.SIDES
SOURCE=v2.FILE;OUT=ROOT/'modelos/criatura-pavao/f3/ataques-v3'
FILE=OUT/'criatura-pavao-e3-ataques-v3.bbmodel'
CLIPS=dict(v2.CLIPS);EVENTS=copy.deepcopy(v2.EVENTS);FPS=120
CROSS_JOIN=.725;CROSS_CUT_END=.52
ACTIVE={'attack_low':[('right',.36,.66)],'attack_cross':[('right',.35,.50),('left',.74,.98)]}
CHANGED=['arm_right','forearm_right','hand_right']


class Rig(v2.Rig):
    def __init__(self,m):
        super().__init__(m);self.previous=Saved(bbmodelo.ler(SOURCE))
        f=unit(self.hinges['right'][1]);blade=self.bind['right']@self.weapons['right']['frame'][:,1]
        angle=math.degrees(math.acos(float(np.clip(f@blade,-1,1))))
        self.aligned_hand=v2.v1.v2.rod(unit(np.cross(blade,f)),angle)
        self.start_sigma=-55.
        p=self.previous.pose('attack_cross',.30)
        # Mantém o começo do arco baixo, com folga física para a lâmina longa.
        for sigma in np.linspace(-55,-20,71):
            q=copy.deepcopy(p);direction,normal=self.cross_geometry(float(sigma))
            self.lever(q,'right',direction,normal,10,1.,wrist=self.wrists['right'])
            if self.sword_floor(q,'right')>=.3:
                self.start_sigma=float(sigma);self.start_floor=self.sword_floor(q,'right');break
        else:raise ValueError('Arco diagonal sem início livre do piso.')
        direction,normal=self.cross_geometry(self.start_sigma)
        self.start_az=math.degrees(math.atan2(direction[0],direction[2]))
        reference=unit(np.array([0.,1.,0.])-direction*direction[1])
        self.start_roll=math.degrees(math.atan2(float(direction@np.cross(reference,normal)),float(reference@normal)))
        self.start_roll+=360*round((self.guard_roll['right']-self.start_roll)/360)

    @staticmethod
    def cross_geometry(sigma):
        # Frente: início quase rasante, depois sobe em diagonal até o lado oposto.
        a=math.radians(sigma);beta=math.radians(30+sigma*10/55);k=10/55
        sa,ca,sb,cb=math.sin(a),math.cos(a),math.sin(beta),math.cos(beta)
        direction=np.array([-cb*sa,sb*sa,-ca])
        tangent=np.array([sb*k*sa-cb*ca,cb*k*sa+sb*ca,sa])
        return direction,-unit(np.cross(direction,tangent))

    def bind_weapon(self,p):
        hand=self.mats(p)['hand_right']
        self.weapon(p,'right',point(hand,self.grips['right']),hand[:3,:3]@self.bind['right'])

    def low(self,p,t):
        d=CLIPS['attack_low'];w=smooth(t/.30)*(1-smooth((t-.82)/(d-.82)))
        az=float(track(t,[(0,self.angle0['right']),(.28,94),(.34,101),(.50,156),(.66,194),(.76,198),(1.04,112),(d,self.angle0['right'])]))
        target_flex=float(track(t,[(0,10),(.66,10),(.82,35),(1.08,70),(d,70)]))
        flex=float(blend(self.guard_flex['right'],target_flex,w))
        hand=g.slerp(R(self.guard['hand_right']['rotacao']),self.aligned_hand,w)
        roll=float(blend(self.guard_roll['right'],0,w));a=math.radians(az)
        horizontal=np.array([math.sin(a),0,math.cos(a)]);initial=copy.deepcopy(p)
        clearance=float(track(t,[(0,0),(.28,.9),(.35,1.2),(.68,1.2),(.84,2.2),(1.10,.8),(d,0)]))
        def evaluate(y):
            q=copy.deepcopy(initial);direction=horizontal*math.sqrt(1-y*y)+[0,y,0]
            reference=unit(np.array([0.,1.,0.])-direction*direction[1])
            normal=v2.v1.v2.rod(direction,roll)@reference
            self.lever(q,'right',direction,normal,flex,1.,wrist=hand)
            return self.sword_floor(q,'right'),q
        lo,hi=-.92,.75;f0,q=evaluate(lo);f1,q1=evaluate(hi)
        if not f0<=clearance<=f1:raise ValueError(('Low sem altura',t,f0,f1))
        for _ in range(24):
            mid=(lo+hi)/2;floor,q=evaluate(mid)
            if floor<clearance:lo=mid
            else:hi=mid
        p.update(q)

    def cross_strike(self,p,t):
        sigma=float(track(t,[(.30,self.start_sigma),(.34,self.start_sigma+2),(.43,0),(CROSS_CUT_END,55)]))
        direction,normal=self.cross_geometry(sigma)
        self.lever(p,'right',direction,normal,10,1.,wrist=self.wrists['right'])

    def cross(self,p,t):
        if t>=CROSS_JOIN:return
        if t>=CROSS_CUT_END:
            start=self.previous.pose('attack_cross',CROSS_CUT_END);self.cross_strike(start,CROSS_CUT_END)
            u=smooth((t-CROSS_CUT_END)/(CROSS_JOIN-CROSS_CUT_END))
            for n in CHANGED:p[n]['rotacao']=g.forms.euler(g.slerp(R(start[n]['rotacao']),R(p[n]['rotacao']),u))
            self.bind_weapon(p);return
        if t>=.30:self.cross_strike(p,t);return
        u=smooth(t/.30);az=float(blend(self.angle0['right'],self.start_az,u))
        roll=float(blend(self.guard_roll['right'],self.start_roll,u))
        flex=float(blend(self.guard_flex['right'],10,u))
        hand=g.slerp(R(self.guard['hand_right']['rotacao']),self.wrists['right'],u)
        a=math.radians(az);horizontal=np.array([math.sin(a),0,math.cos(a)])
        clearance=self.start_floor*u+1.25*math.sin(math.pi*t/.30)**2
        initial=copy.deepcopy(p)
        def evaluate(y):
            q=copy.deepcopy(initial);direction=horizontal*math.sqrt(1-y*y)+[0,y,0]
            reference=unit(np.array([0.,1.,0.])-direction*direction[1])
            normal=v2.v1.v2.rod(direction,roll)@reference
            self.lever(q,'right',direction,normal,flex,1.,wrist=hand)
            return self.sword_floor(q,'right'),q
        lo,hi=-.90,.90;f0,q=evaluate(lo);f1,q1=evaluate(hi)
        if not f0<=clearance<=f1:raise ValueError(('Cross sem preparação',t,f0,f1))
        for _ in range(24):
            mid=(lo+hi)/2;floor,q=evaluate(mid)
            if floor<clearance:lo=mid
            else:hi=mid
        p.update(q)

    def pose(self,name,t):
        key=(name,round(t,9))
        if key in self.cache:return copy.deepcopy(self.cache[key])
        p=self.previous.pose(name,float(t))
        if 0<t<CLIPS[name]:
            if name=='attack_low':self.low(p,t)
            else:self.cross(p,t)
        self.cache[key]=copy.deepcopy(p);return p


def bake(names=None):
    names=names or list(CLIPS);partial=set(names)!=set(CLIPS)
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'_cache').mkdir(exist_ok=True)
    if partial and not FILE.exists():raise ValueError('Gere a cópia completa primeiro.')
    if FILE.exists():
        record=json.loads((OUT/'geracao.json').read_text(encoding='utf-8'))
        if record['saida_sha256']!=g.sha(FILE):raise ValueError('Saída editada à mão; criar outra versão.')
    m=bbmodelo.ler(FILE if partial else SOURCE);rig=Rig(m);ops=[];counts=record['chaves'].copy() if partial else {}
    for name in names:
        duration=CLIPS[name];end=CROSS_JOIN if name=='attack_cross' else duration
        animation=next(a for a in m.animacoes if a['name']==name)
        times=np.unique(np.round(np.r_[np.arange(round(end*FPS)+1)/FPS,list(EVENTS[name].values()),end],9))
        times=times[(times>=0)&(times<=end+1e-9)]
        poses=[rig.pose(name,float(t)) for t in times];count=0
        for bone in CHANGED:
            animator=animation['animators'][m.ossos[bone].uuid]
            for k in animator['keyframes']:
                if k['channel']=='rotation' and (name=='attack_low' or k['time']<end-1e-9):
                    ops.append({'op':'remove_keyframe','animation':name,'bone':bone,'channel':'rotation','time':k['time']})
            raw=np.array([p[bone]['rotacao'] for p in poses],float)
            values=g.continuous_euler(raw[::-1])[::-1] if name=='attack_cross' else g.continuous_euler(raw)
            for t,value in zip(times,values):
                # O frame de chegada original permanece intacto no Cross.
                if name=='attack_cross' and t>=end-1e-9:continue
                ops.append({'op':'set_keyframe','animation':name,'bone':bone,'channel':'rotation','time':float(t),
                            'value':np.round(value,9).tolist(),'interpolation':'linear'});count+=1
        counts[name]=count;print('Calculado:',name,count,'chaves direitas',flush=True)
    if not partial:shutil.copy2(SOURCE,FILE)
    ops.append({'op':'set_model_properties','name':FILE.stem});g.dump(OUT/'_cache/ops.json',ops);motor.editar(FILE,ops,lote=500)
    g.dump(OUT/'geracao.json',{'fonte':SOURCE.relative_to(ROOT).as_posix(),'fonte_sha256':g.sha(SOURCE),'saida_sha256':g.sha(FILE),
        'clipes':CLIPS,'chaves':counts,'ossos_revistos':CHANGED,'cross_preservado_a_partir_de':CROSS_JOIN,
        'inicio_arco_sigma':rig.start_sigma})
    metadata();print('Gravado:',FILE.name,flush=True)


def metadata():
    data=json.loads((SOURCE.parent/'animacoes.json').read_text(encoding='utf-8'))
    data.update(modelo=FILE.name,fonte=SOURCE.relative_to(ROOT).as_posix(),fonte_sha256=g.sha(SOURCE),saida_sha256=g.sha(FILE),
                status='low-cross-v3-em-avaliacao',validacao='validacao-ataques.json')
    data['controle_golpes']='Low com eixo da espada colinear ao antebraço; Cross direito em arco diagonal ascendente conforme desenho frontal; esquerda preservada.'
    data['preservacao_cross']={'esquerda':'todos os animadores intactos','corpo_e_pernas':'intactos','clipe_completo_apos':CROSS_JOIN}
    data['aprovacoes_parciais']={'attack_cross_esquerdo':'Descida v2 aprovada pelo usuário; chaves preservadas integralmente.'}
    data['referencias_usuario']=['referencias/low-linha-1.png','referencias/low-linha-2.png','referencias/cross-arco-frontal.png']
    g.dump(OUT/'animacoes.json',data)


def main():
    ap=argparse.ArgumentParser()
    for name in ['estudo','gerar','validar','nativo']:ap.add_argument('--'+name,action='store_true')
    ap.add_argument('--clipes',nargs='+',choices=list(CLIPS));args=ap.parse_args()
    review=module('revisao_golpes_f3_v3','revisar-golpes-pavao-f3-v3.py')
    if args.estudo:review.study(__import__(__name__))
    if args.gerar:bake(args.clipes)
    if args.validar:review.check(__import__(__name__))
    if args.nativo:review.capture(__import__(__name__))


if __name__=='__main__':main()
