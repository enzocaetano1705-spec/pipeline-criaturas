"""Completa os oito clipes adiados a partir da base F3 aprovada na v7.

Preserva os cinco clipes aprovados e a geometria. Sem lógica de jogo.
Escrita em lote pelo motor externo; estudo/validação usam as poses salvas.
"""
import argparse
import copy
import importlib.util
import json
import math
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('combate_f3_v7',ROOT/'scripts/animar-combate-pavao-f3-v7.py')
v7=importlib.util.module_from_spec(sp);sp.loader.exec_module(v7)
v3=v7.v3;v2=v7.v2;g=v7.g;bbmodelo=v7.bbmodelo;motor=v3.motor
R,point,smooth,blend=g.R,g.point,g.smooth,g.blend
SOURCE=v7.FILE
OUT=ROOT/'modelos/criatura-pavao/f3/animacoes-v8'
FILE=OUT/'criatura-pavao-e3-combate-v8.bbmodel'
ENTER=1.65;EXIT=1.8;TRANSITION=.6;REST_START=1.25;REST_END=4.25;RESUME=1.1
REST_EXIT=REST_END+RESUME
CLIPS={'combat_enter_walk':ENTER,'combat_enter_upper':ENTER,
       'combat_walk_start':TRANSITION,'combat_walk_stop':TRANSITION,
       'combat_idle':REST_EXIT+EXIT,'combat_idle_resume':RESUME,
       'combat_exit':EXIT,'combat_exit_upper':EXIT}
APPROVED=['idle','walk','combat_ready','combat_walk','combat_enter']
SIDES=['left','right']
ARM={p+s for p in ['arm_','forearm_','hand_'] for s in SIDES}|{'tail_fan_04','tail_fan_06'}


def phase(t,length,exiting=False):
    a,b=(1/1.8,1/1.5) if exiting else (1/1.5,1/1.8)
    return a*t+(b-a)*t*t/(2*length)


def exit_time(t,side):
    if side=='right':return ENTER*(1-smooth(t/EXIT))
    if t<.35:return ENTER-.4*smooth(t/.35)
    if t<.50:return None  # ponte entre a recuperação e o começo do floreio
    if t<1.20:return .70-.40*smooth((t-.50)/.70)
    return .30*(1-smooth((t-1.20)/(EXIT-1.20)))


def dock_time(side):
    if side=='left':return 1.20
    lo,hi=0.,EXIT
    for _ in range(40):
        mid=(lo+hi)/2
        if exit_time(mid,side)>v2.GRASP[side]:lo=mid
        else:hi=mid
    return (lo+hi)/2


def cached(fn):
    def wrapped(self,*args,**kwargs):
        key=(fn.__name__,tuple(round(a,8) if isinstance(a,float) else a for a in args),tuple(sorted(kwargs.items())))
        if key not in self.motion_cache:self.motion_cache[key]=fn(self,*args,**kwargs)
        return copy.deepcopy(self.motion_cache[key])
    return wrapped


class Rig(v7.Rig):
    def __init__(self,m):
        super().__init__(m)
        self.motion_cache={}
        self.upper_mask=self.upper;del self.upper
        self.idle0=self.saved.pose('idle',0);self.ready0=self.saved.pose('combat_ready',0)
        self.ready_feet=self.contact_feet(self.ready0)[0]
        self.plant_grip=np.array([13.,26.,-11.])
        self.plant_pref=R([-35,0,-5])
        p=copy.deepcopy(self.ready0)
        rot=self.direction_rotation('right',[.035,-.998,-.035],[0,0,1])
        self.plant_rot=self.aligned_roll(p,'right',self.plant_grip,rot,self.plant_pref)
        self.free_arm_pose={}
        self.fk(p,'right',R([-38,0,-5]),-18)
        for n in ['arm_right','forearm_right','hand_right']:self.free_arm_pose[n]=copy.deepcopy(p[n])

    def contact_feet(self,p):
        mats=self.mats(p)
        return ({s:point(mats['foot_'+s],self.feet[s]) for s in SIDES},
                {s:float(g.forms.euler(mats['foot_'+s][:3,:3])[0]) for s in SIDES})

    def walking(self,t,length,exiting=False):
        ph=phase(t,length,exiting)
        a=self.saved.pose('walk',(ph%1)*1.5)
        b=self.saved.pose('combat_walk',(ph%1)*1.8)
        return a,b,ph

    def locomotion(self,p,t,length,c,exiting=False):
        a,b,_=self.walking(t,length,exiting)
        for n in self.m.ossos:
            if n in ARM or n.startswith(('leg_','shin_','foot_')):continue
            delta_a=R(self.idle0[n]['rotacao']).T@R(a[n]['rotacao'])
            delta_b=R(self.ready0[n]['rotacao']).T@R(b[n]['rotacao'])
            p[n]['rotacao']=g.forms.euler(R(p[n]['rotacao'])@g.slerp(delta_a,delta_b,c))
            p[n]['posicao']=np.asarray(p[n].get('posicao',[0,0,0]))+blend(
                a[n].get('posicao',np.zeros(3))-self.idle0[n].get('posicao',np.zeros(3)),
                b[n].get('posicao',np.zeros(3))-self.ready0[n].get('posicao',np.zeros(3)),c)
        fa,ra=self.contact_feet(a);fb,rb=self.contact_feet(b)
        self.legs(p,{s:blend(fa[s],fb[s],c) for s in SIDES},
                  {s:float(blend(ra[s],rb[s],c)) for s in SIDES})
        return a,b

    def transfer_arm(self,p,old,tau,side,final=None,settle=0.,initial=None,initial_weight=0.):
        """Reusa o gesto aprovado sobre o torso atual e encontra a cauda real."""
        mats=self.mats(old);now=self.mats(p)
        transfer=now['torso']@np.linalg.inv(mats['torso'])
        w=self.weapons[side];grab=v2.GRASP[side]
        pref=R(old['arm_'+side]['rotacao'])
        holding=tau>=grab
        if holding:
            wm=transfer@mats[w['name']];grip=point(wm,w['grip']);rot=wm[:3,:3]
            dock_weight=1-smooth((tau-grab)/(.50-grab))
            base=transfer@mats['tail_1'];tail=now['tail_1']
            grip+=(point(tail,w['grip'])-point(base,w['grip']))*dock_weight
            correction=tail[:3,:3]@base[:3,:3].T
            rot=g.slerp(np.eye(3),correction,dock_weight)@rot
            if final is not None and settle:
                fm=self.mats(final)[w['name']]
                grip=blend(grip,point(fm,w['grip']),settle)
                rot=g.slerp(rot,fm[:3,:3],settle)
                pref=g.slerp(pref,R(final['arm_'+side]['rotacao']),settle)
            self.held(p,side,grip,rot,pref)
        else:
            hm=transfer@mats['hand_'+side];grip=point(hm,self.grips[side]);rot=hm[:3,:3]
            weight=smooth((tau-.16)/(grab-.16));tail=now['tail_1']
            base=transfer@mats['tail_1']
            grip+=(point(tail,w['grip'])-point(base,w['grip']))*weight
            rot=g.slerp(np.eye(3),tail[:3,:3]@base[:3,:3].T,weight)@rot
            if initial is not None and initial_weight:
                im=self.mats(initial)['hand_'+side]
                grip=blend(grip,point(im,self.grips[side]),initial_weight)
                rot=g.slerp(rot,im[:3,:3],initial_weight)
                pref=g.slerp(pref,R(initial['arm_'+side]['rotacao']),initial_weight)
            self.natural_arm(p,side,grip,rot,pref)
            self.sheathed(p,side)

    @cached
    def enter_walk(self,t):
        if t<=0:return self.saved.pose('walk',0)
        if t>=ENTER:return self.saved.pose('combat_walk',(phase(ENTER,ENTER)%1)*1.8)
        old=self.saved.pose('combat_enter',t);p=copy.deepcopy(old)
        a,b=self.locomotion(p,t,ENTER,smooth(t/ENTER))
        for side in SIDES:
            self.transfer_arm(p,old,t,side,final=b,settle=smooth((t-1.25)/.40),
                initial=a,initial_weight=1-smooth(t/.15))
        self.anchored_wings(p)
        return p

    def transition(self,t,stop=False):
        if t<=0:return self.saved.pose('combat_walk',0) if stop else copy.deepcopy(self.ready0)
        if t>=TRANSITION:
            return copy.deepcopy(self.ready0) if stop else self.saved.pose('combat_walk',TRANSITION/2)
        ph=(t-t*t/(2*TRANSITION) if stop else t*t/(2*TRANSITION))/1.8
        walking=self.saved.pose('combat_walk',ph*1.8)
        weight=smooth(t/TRANSITION);weight=1-weight if stop else weight
        p=self.mix_pose(self.ready0,walking,weight)
        feet,rolls=self.contact_feet(walking)
        self.legs(p,{s:blend(self.ready_feet[s],feet[s],weight) for s in SIDES},
                  {s:rolls[s]*weight for s in SIDES})
        self.carry(p,'left',*self.shoulder_target(p),R([-5,0,35]))
        self.carry(p,'right',*self.drag_target(p),R([-42,0,0]))
        self.anchored_wings(p)
        return p

    @cached
    def exit_pose(self,t,moving=True):
        if t<=0:return self.saved.pose('combat_walk',0) if moving else copy.deepcopy(self.ready0)
        if t>=EXIT-1e-9:return self.saved.pose('walk',(phase(EXIT,EXIT,True)%1)*1.5) if moving else copy.deepcopy(self.idle0)
        c=1-smooth(t/EXIT);p=self.mix_pose(self.idle0,self.ready0,c)
        a,b=(self.locomotion(p,t,EXIT,c,True) if moving else (self.idle0,self.ready0))
        if not moving:
            feet={}
            for side,start,end in [('left',.20,.72),('right',.90,1.45)]:
                w=smooth((t-start)/(end-start))
                feet[side]=blend(self.ready_feet[side],self.feet[side],w)+[0,.8*math.sin(math.pi*w)**2,0]
            self.legs(p,feet)
        for side in SIDES:
            tau=exit_time(t,side)
            if tau is None:
                old=self.mix_pose(self.saved.pose('combat_enter',1.25),self.saved.pose('combat_enter',.70),smooth((t-.35)/.15))
                tau=.7
            else:old=self.saved.pose('combat_enter',tau)
            self.transfer_arm(p,old,tau,side,initial=a,initial_weight=smooth((t-(EXIT-.18))/.18))
        self.anchored_wings(p)
        return p

    def resting(self,t=0):
        p=self.saved.pose('combat_ready',(t/3%1)*2.4)
        for n,value in self.free_arm_pose.items():p[n]=copy.deepcopy(value)
        self.weapon(p,'right',self.plant_grip,self.plant_rot)
        self.anchored_wings(p)
        return p

    def load_body(self,p,t,kind):
        if kind=='plant':
            dip=float(g.curve(t,[(0,0),(.40,.5),(.67,-1.4),(.83,-.65),(REST_START,0)]))
            lean=float(g.curve(t,[(0,0),(.40,2),(.67,-4),(.90,-1),(REST_START,0)]))
        else:
            dip=float(g.curve(t,[(0,0),(.30,-.3),(.62,-.8),(.87,.3),(RESUME,0)]))
            lean=float(g.curve(t,[(0,0),(.30,-2),(.60,-3),(.88,1),(RESUME,0)]))
        p['body']['posicao']+=np.array([0,dip,0]);p['torso']['rotacao'][0]+=lean
        p['neck_1']['rotacao'][0]-=.5*lean;p['tail_1']['rotacao'][0]-=.6*lean
        for n in self.anchors:p[n]['rotacao'][0]+=.3*lean
        self.legs(p,self.ready_feet)
        self.carry(p,'left',*self.shoulder_target(p),R([-5,0,35]))

    def plant(self,t):
        if t<=0:return copy.deepcopy(self.ready0)
        if t>=REST_START:return self.resting(0)
        p=copy.deepcopy(self.ready0);self.load_body(p,t,'plant')
        target,rot0=self.drag_target(p)
        pref=g.slerp(R([-42,0,0]),self.plant_pref,smooth(t/.48))
        grip=g.curve(t,[(0,target),(.48,np.array([14.,34.,-10.])),(.72,self.plant_grip),(REST_START,self.plant_grip)])
        if t<.48:
            # Varrida lateral com altura constante da ponta; uma slerp direta
            # entre duas diagonais baixas passaria pelo piso no meio do arco.
            d0=rot0@self.weapons['right']['frame'][:,1];u=smooth(t/.48)
            az0=math.atan2(d0[0],d0[2]);az=blend(az0,3*math.pi/4,u)
            dy=float(blend(d0[1],-.48,u))
            d=np.array([math.sin(az)*math.sqrt(1-dy*dy),dy,math.cos(az)*math.sqrt(1-dy*dy)])
            rot=self.direction_rotation('right',d,[0,0,1])
            rot=self.aligned_roll(p,'right',grip,rot,pref)
        else:
            diagonal=self.direction_rotation('right',[.62,-.48,-.62],[0,0,1])
            diagonal=self.aligned_roll(p,'right',grip,diagonal,self.plant_pref)
            rot=g.slerp(diagonal,self.plant_rot,smooth((t-.48)/.24))
        self.held(p,'right',grip,rot,pref,allow_buried=t>=.48)
        if t>.95:
            weight=smooth((t-.95)/(REST_START-.95))
            for n,final in self.free_arm_pose.items():
                p[n]['rotacao']=g.forms.euler(g.slerp(R(p[n]['rotacao']),R(final['rotacao']),weight))
            self.weapon(p,'right',self.plant_grip,self.plant_rot)
        self.anchored_wings(p)
        return p

    @cached
    def resume(self,t):
        if t<=0:return self.resting(0)
        if t>=RESUME:return copy.deepcopy(self.ready0)
        p=copy.deepcopy(self.ready0);self.load_body(p,t,'resume')
        target,rot=self.drag_target(p)
        if t<.30:
            self.held(p,'right',self.plant_grip,self.plant_rot,self.plant_pref,allow_buried=True)
            w=smooth(t/.30)
            for n,start in self.free_arm_pose.items():
                p[n]['rotacao']=g.forms.euler(g.slerp(R(start['rotacao']),R(p[n]['rotacao']),w))
            self.weapon(p,'right',self.plant_grip,self.plant_rot)
        else:
            u=smooth((t-.30)/.80)
            wave=math.sin(math.pi*u)**2
            grip=blend(self.plant_grip,target,u)+[2*wave,6*wave,0]
            rr=g.slerp(self.plant_rot,rot,u)
            pref=g.slerp(self.plant_pref,R([-42,0,0]),u)
            aligned=self.aligned_roll(p,'right',grip,rr,pref)
            roll_weight=smooth((t-.30)/.12)*(1-smooth((t-(RESUME-.12))/.12))
            rr=g.slerp(rr,aligned,roll_weight)
            self.held(p,'right',grip,rr,pref,allow_buried=True)
        self.anchored_wings(p)
        return p

    def rest_pose(self,t):
        if t<REST_START:return self.plant(t)
        if t<=REST_END:return self.resting(t-REST_START)
        if t<REST_EXIT:return self.resume(t-REST_END)
        return self.exit_pose(t-REST_EXIT,False)

    def upper(self,p,base):
        mats=self.mats(p);parent=self.mats(base)['pelvis'];q=copy.deepcopy(p)
        for n in ['waist','tail_1']:q[n]=v2.node_local(self.m.ossos[n],mats[n],parent)
        return {n:q[n] for n in self.upper_bones}

    @property
    def upper_bones(self):return self.upper_mask

    def pose(self,name,t):
        if name.startswith('combat_enter'):p=self.enter_walk(t)
        elif name.startswith('combat_exit'):p=self.exit_pose(t)
        elif name=='combat_idle':return self.rest_pose(t)
        elif name=='combat_idle_resume':return self.resume(t)
        else:return self.transition(t,name.endswith('stop'))
        if name.endswith('upper'):
            d=ENTER if name.startswith('combat_enter') else EXIT
            base=self.saved.pose('walk',(phase(t,d,name.startswith('combat_exit'))%1)*1.5)
            return self.upper(p,base)
        return p


def reduce_keys(times,values,tol):
    keep={0,len(times)-1};stack=[(0,len(times)-1)]
    while stack:
        a,b=stack.pop()
        if b-a<2:continue
        u=(times[a+1:b]-times[a])/(times[b]-times[a])
        residual=np.max(abs(values[a+1:b]-(values[a]+u[:,None]*(values[b]-values[a]))),axis=1)
        i=int(np.argmax(residual))+a+1
        if residual[i-a-1]>tol:keep.add(i);stack.extend([(a,i),(i,b)])
    return sorted(keep)


def bake(names):
    previous={}
    if FILE.exists() and set(names)!=set(CLIPS):
        previous=json.loads((OUT/'geracao.json').read_text(encoding='utf-8'))
        if previous['saida_sha256']!=g.sha(FILE):raise ValueError('Saída editada; criar outra versão.')
        m=bbmodelo.ler(FILE)
    else:m=v3.prepare()
    rig=Rig(m);ops=[];counts=previous.get('chaves',{})
    for name in names:
        length=CLIPS[name];fps=240 if name.startswith('combat_enter') else 120
        extra=[x for x in [.3,.34,.35,.48,.5,.7,.72,.95,REST_START,REST_END,REST_EXIT] if x<=length]
        grid=np.linspace(0,length,round(length*fps)+1)
        if name.startswith('combat_enter'):
            original=next(a for a in rig.orig.animacoes if a['name']=='combat_enter')
            extra+=list({float(k['time']) for a in original['animators'].values() for k in a.get('keyframes',[])})
            grid=np.r_[grid,np.arange(.90,1.05001,1/480)]
        priority=np.unique(np.round(extra,8));grid=np.unique(np.round(grid,8))
        grid=grid[np.min(abs(grid[:,None]-priority[None,:]),axis=1)>.00012]
        times=np.unique(np.r_[priority,grid])
        poses=[rig.pose(name,float(t)) for t in times]
        ops.extend([{'op':'remove_animation','animation':name},
                    {'op':'add_animation','name':name,'length':length,'loop':'once','snapping':120}])
        count=0
        for n in (rig.upper_bones if name.endswith('upper') else m.ossos):
            for ch,field in [('rotation','rotacao'),('position','posicao')]:
                vals=np.array([p[n].get(field,[0,0,0]) for p in poses])
                if ch=='rotation':vals=g.continuous_euler(vals)
                indices=reduce_keys(times,vals,.0007 if ch=='rotation' else .00015)
                for i in indices:
                    ops.append({'op':'set_keyframe','animation':name,'bone':n,'channel':ch,
                        'time':float(times[i]),'value':np.round(vals[i],8).tolist(),'interpolation':'linear'});count+=1
        counts[name]=count;print('Calculado:',name,flush=True)
    g.dump(OUT/'_cache/ops-animacoes.json',ops);motor.editar(FILE,ops)
    g.dump(OUT/'geracao.json',{'fonte_sha256':g.sha(SOURCE),'saida_sha256':g.sha(FILE),
        'clipes_revistos':list(counts),'chaves':counts,'operacoes_ultima_gravacao':len(ops),'alcance_excedido':rig.max_unreachable})
    print('Gravado:',FILE.name,flush=True)


def new_rig(m):
    return Rig(m)


def metadata():
    report=json.loads((OUT/'validacao.json').read_text(encoding='utf-8'))
    assert report['integridade_ok'] and set(report['clipes'])==set(CLIPS)
    assert report['saida_sha256']==g.sha(FILE)
    rig=new_rig(bbmodelo.ler(FILE))
    g.dump(OUT/'animacoes.json',{
        'status':'novos-clipes-aguardam-avaliacao-artistica','modelo':FILE.name,
        'fonte':SOURCE.relative_to(ROOT).as_posix(),'fonte_sha256':g.sha(SOURCE),
        'saida_sha256':g.sha(FILE),'root_motion':False,'aprovados':APPROVED,
        'clipes_revistos':{n:{'duracao':d,'loop':False} for n,d in CLIPS.items()},
        'lados':{'ombro_e_floreio':'left da criatura','arrasto_e_espada_cravada':'right da criatura'},
        'saque':{'GripLeft':.30,'GripRight':.34,'FlourishStart':.70,'FlourishEnd':1.23,
                 'fim_andando_fase_combat_walk':phase(ENTER,ENTER)%1,
                 'fim_andando_tempo_combat_walk':(phase(ENTER,ENTER)%1)*1.8},
        'passos':{'start_inicia_em':'combat_ready@0','start_termina_em':'combat_walk@0.30',
                  'stop_inicia_em':'combat_walk@0','stop_termina_em':'combat_ready@0',
                  'interrupcoes':'Misturar os estados e preservar a fase na integração futura.'},
        'descanso':{'clipe':'combat_idle','loop':False,'cravar_ate':.72,
                    'ReleaseStart':.95,'ReleaseEnd':REST_START,'pausa':[REST_START,REST_END],
                    'Regrasp':REST_END+.30,'recuperada_em':REST_EXIT,
                    'DockLeft':REST_EXIT+dock_time('left'),'DockRight':REST_EXIT+dock_time('right'),
                    'fim':CLIPS['combat_idle'],'termina_em':'idle@0',
                    'retomada':'combat_idle_resume','retomada_origem':'pausa, com mistura de respiração',
                    'retomada_termina_em':'combat_ready@0','retomada_Regrasp':.30,
                    'profundidade_unidades':report['clipes']['combat_idle']['profundidade_intencional'],
                    'espada_solta_imovel':True},
        'saida':{'andando':'combat_exit','camada':'combat_exit_upper',
                 'DockLeft':dock_time('left'),'DockRight':dock_time('right'),
                 'fim_andando_fase_walk':phase(EXIT,EXIT,True)%1,
                 'fim_andando_tempo_walk':(phase(EXIT,EXIT,True)%1)*1.5,
                 'floreio_reverso':False},
        'camadas':{'modo':'substituir canais da máscara; não aditivo','ossos':rig.upper_bones,
                   'base':'walk aprovado na fase descrita abaixo',
                   'fase_enter':'t/1.5 + (1/1.8-1/1.5)*t*t/(2*1.65)',
                   'fase_exit':'t/1.8 + (1/1.5-1/1.8)*t*t/(2*1.8)',
                   'sem_canais':['root','body','pelvis','leg_*','shin_*','foot_*']},
        'validacao':'validacao.json','golpes':'próxima etapa; não criados nesta revisão'})
    print('Metadados: oito clipes, fases, máscaras e marcadores.',flush=True)


v3.SOURCE=SOURCE;v3.OUT=OUT;v3.FILE=FILE


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--animar',action='store_true')
    ap.add_argument('--estudo',action='store_true');ap.add_argument('--validar',action='store_true')
    ap.add_argument('--previas',action='store_true');ap.add_argument('--folha',action='store_true')
    ap.add_argument('--metadados',action='store_true')
    ap.add_argument('--clipes',nargs='+',choices=list(CLIPS),default=list(CLIPS))
    args=ap.parse_args();(OUT/'_cache').mkdir(parents=True,exist_ok=True)
    if args.estudo or args.validar or args.previas:
        sp=importlib.util.spec_from_file_location('revisao_v8',ROOT/'scripts/revisar-combate-pavao-f3-v8.py')
        review=importlib.util.module_from_spec(sp);sp.loader.exec_module(review)
        if args.estudo:review.check(sysmod=__import__(__name__),names=args.clipes,study=True)
    if args.animar:bake(args.clipes)
    if args.validar:review.check(sysmod=__import__(__name__),names=args.clipes)
    if args.metadados:metadata()
    if args.previas:
        m=bbmodelo.ler(FILE);saved=review.preview_reader(__import__(__name__),m)
        v2.review.OUT=OUT;v2.review.g.CLIPS=CLIPS
        v2.review.preview(m,saved,args.clipes,fps=20,size=640)
    if args.folha:
        sheet=v7.v5.v4;sheet.FILE=FILE;sheet.OUT=OUT
        sheet.overview([('combat_enter_walk',.95,35),('combat_walk_start',.40,35),
            ('combat_idle',.60,35),('combat_idle',2.75,35),('combat_idle_resume',.70,35),('combat_exit',.80,35)])


if __name__=='__main__':main()
