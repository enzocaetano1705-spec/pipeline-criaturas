"""Corrige flicks da F3: relógio comum, vínculos rígidos e camadas ancoradas."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path)
    m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
v8=module('combate_v8','scripts/animar-combate-pavao-f3-v8.py')
review8=module('revisao_v8','scripts/revisar-combate-pavao-f3-v8.py')
auditmod=module('auditoria_v9','scripts/revisar-flicks-pavao-f3-v9.py')
g=v8.g;v2=v8.v2;v3=v8.v3;bbmodelo=v8.bbmodelo;motor=v8.motor
R,point,smooth,blend=v8.R,v8.point,v8.smooth,v8.blend
SOURCE=v8.FILE;OUT=ROOT/'modelos/criatura-pavao/f3/animacoes-v9';FILE=OUT/'criatura-pavao-e3-combate-v9.bbmodel'
ENTER,EXIT,TRANSITION=v8.ENTER,v8.EXIT,v8.TRANSITION
REST_START,REST_END,REST_EXIT,RESUME=v8.REST_START,v8.REST_END,v8.REST_EXIT,v8.RESUME
SIDES=v8.SIDES;phase=v8.phase;dock_time=v8.dock_time
CLIPS={'combat_enter':ENTER,**v8.CLIPS}
APPROVED=['idle','walk','combat_ready','combat_walk']


class Rig(v8.Rig):
    def __init__(self,m):
        super().__init__(m)
        self.original=v2.review.Saved(bbmodelo.ler(SOURCE))
        self.full_cache={}

    def fixed_binding(self,p,name,t):
        for side in SIDES:
            state=review8.state(v8,name,t,side)
            if state=='tail':self.sheathed(p,side)
            elif state=='ground':self.weapon(p,side,self.plant_grip,self.plant_rot)
            else:
                mat=self.mats(p)['hand_'+side]
                # Uma relação constante de empunhadura substitui compensações
                # quase iguais que variavam a cada chave junto da singularidade.
                self.weapon(p,side,point(mat,self.grips[side]),mat[:3,:3]@self.bind[side])

    def crest(self,p,name,t):
        d=CLIPS[name];strength=smooth(t/.08)*smooth((d-t)/.08)
        source=[(self.original.pose(name,float(np.clip(t+dt,0,d))),w)
                for dt,w in [(-.024,1),(-.012,2),(0,3),(.012,2),(.024,1)]]
        for n in ['feather_left_1','feather_right_1','feather_left_2','feather_right_2']:
            center=np.asarray(p[n]['rotacao']);samples=[]
            for sample,w in source:
                value=sample[n]['rotacao']
                samples.append((value+360*np.round((center-value)/360))*w)
            p[n]['rotacao']=blend(center,sum(samples)/9,strength)

    def corrected_walk(self,t):
        p=self.original.pose('combat_enter_walk',t)
        if t<=0 or t>=ENTER:return p
        old=self.original.pose('combat_enter',t);ref=self.mats(old);now=self.mats(p)
        settle=smooth((t-1.25)/.40)
        for side in SIDES:
            if t<v2.GRASP[side]:continue
            w=self.weapons[side]
            sh=self.m.ossos['arm_'+side].origem
            offset=point(now['torso'],sh)-point(ref['torso'],sh)
            grip=point(ref[w['name']],w['grip'])+offset
            rot=ref[w['name']][:3,:3].copy()
            pref=R(old['arm_'+side]['rotacao'])
            weight=1-smooth((t-v2.GRASP[side])/(.50-v2.GRASP[side]))
            dock0=point(ref['tail_1'],w['grip'])+offset
            grip+=(point(now['tail_1'],w['grip'])-dock0)*weight
            rot=g.slerp(np.eye(3),now['tail_1'][:3,:3]@ref['tail_1'][:3,:3].T,weight)@rot
            # Conserva o plano do floreio no mundo. Inclinar a lâmina com o
            # torso fazia o IK levantá-la do piso e quase travar o cotovelo.
            if settle:
                wm=now[w['name']]
                grip=blend(grip,point(wm,w['grip']),settle)
                rot=g.slerp(rot,wm[:3,:3],settle)
                pref=g.slerp(pref,R(p['arm_'+side]['rotacao']),settle)
            self.held(p,side,grip,rot,pref)
        return p

    def full(self,name,t):
        key=(name,round(t,8))
        if key in self.full_cache:return copy.deepcopy(self.full_cache[key])
        p=self.corrected_walk(t) if name=='combat_enter_walk' else self.original.pose(name,t)
        self.crest(p,name,t)
        if 1e-9<t<CLIPS[name]-1e-9:self.anchored_wings(p)
        self.fixed_binding(p,name,t)
        self.full_cache[key]=copy.deepcopy(p)
        return p

    def base_layer(self,name,t):
        return self.full('combat_enter_walk' if name.startswith('combat_enter') else 'combat_exit',t)

    def layer(self,name,t):
        full_name='combat_enter_walk' if name.startswith('combat_enter') else 'combat_exit'
        # Uma camada local é uma máscara do movimento completo. A postura do
        # corpo/pernas vem do companheiro completo; não se deslocam os pivôs
        # da cauda/cintura para imitar outra base de locomoção.
        p=self.full(full_name,t)
        return {n:p[n] for n in self.upper_bones}

    def pose(self,name,t):return self.layer(name,t) if name.endswith('upper') else self.full(name,t)


def new_rig(m):return Rig(m)
def compose_base(rig,name,t,saved=None):
    companion='combat_enter_walk' if name.startswith('combat_enter') else 'combat_exit'
    return saved.pose(companion,t) if saved is not None else rig.base_layer(name,t)


def geometry_repairs():
    repairs={}
    for c in bbmodelo.ler(SOURCE).cubos:
        if c.osso in ['tail_fan_04','tail_fan_06'] and 'point' in c.nome:
            a=c.de.copy();b=c.ate.copy();a[2]+=.01;b[2]-=.01
            repairs[c.uuid]={'de':a,'ate':b,'nome':c.nome,'osso':c.osso}
        elif c.nome.startswith('crest_') and abs(c.ate[2]-c.de[2])<1e-9:
            a=c.de.copy();b=c.ate.copy();a[2]-=.005;b[2]+=.005
            repairs[c.uuid]={'de':a,'ate':b,'nome':c.nome,'osso':c.osso}
    assert len(repairs)==6
    return repairs


def repair_surfaces():
    record=json.loads((OUT/'geracao.json').read_text(encoding='utf-8'))
    if record['saida_sha256']!=g.sha(FILE):raise ValueError('Saída alterada fora do gerador.')
    src=bbmodelo.ler(SOURCE);ops=[]
    for uid,data in geometry_repairs().items():
        c=next(c for c in src.cubos if c.uuid==uid)
        ops.append({'op':'update_node','target':uid,'from':data['de'].tolist(),'to':data['ate'].tolist(),
                    'faces':copy.deepcopy(c.faces)})
    g.dump(OUT/'ops-superficies.json',ops);motor.editar(FILE,ops)
    record['saida_sha256']=g.sha(FILE)
    record['reparo_superficies']='Pontas recuadas em 0,01 unidade; cristas com espessura 0,01. Contornos/UVs preservados.'
    g.dump(OUT/'geracao.json',record)
    print('Pontas/cristas: faces separadas, mesmos contornos/UVs.',flush=True)


def bake(names):
    known={}
    if FILE.exists():
        known=json.loads((OUT/'geracao.json').read_text(encoding='utf-8'))
        if known['saida_sha256']!=g.sha(FILE):raise ValueError('Saída alterada; preservar em outra versão.')
    m=bbmodelo.ler(FILE) if FILE.exists() and set(names)!=set(CLIPS) else v3.prepare()
    rig=new_rig(m);ops=[];counts=known.get('chaves',{}) if set(names)!=set(CLIPS) else {}
    for name in names:
        length=CLIPS[name];fps=300 if name.startswith('combat_enter') else 120
        times=np.linspace(0,length,round(length*fps)+1)
        # O evento exato é parte do relógio comum de TODOS os canais.
        extra=[x for x in [.30,.34,.48,.72,.95,REST_START,REST_END,REST_END+.30,REST_EXIT,
                           dock_time('left'),dock_time('right'),REST_EXIT+dock_time('left'),REST_EXIT+dock_time('right')]
               if 0<x<length and np.min(abs(times-x))>1e-7]
        times=np.unique(np.round(np.r_[times,extra],8))
        poses=[rig.pose(name,float(t)) for t in times]
        ops.extend([{'op':'remove_animation','animation':name},
                    {'op':'add_animation','name':name,'length':length,'loop':'once','snapping':fps}])
        count=0
        for n in (rig.upper_bones if name.endswith('upper') else m.ossos):
            for ch,field in [('rotation','rotacao'),('position','posicao')]:
                vals=np.array([p[n].get(field,[0,0,0]) for p in poses])
                if ch=='rotation':vals=g.continuous_euler(vals)
                indices=[0,len(times)-1] if np.max(np.ptp(vals,axis=0))<1e-8 else range(len(times))
                for i in indices:
                    ops.append({'op':'set_keyframe','animation':name,'bone':n,'channel':ch,
                        'time':float(times[i]),'value':np.round(vals[i],8).tolist(),'interpolation':'linear'});count+=1
        counts[name]=count;print('Calculado:',name,flush=True)
    g.dump(OUT/'_cache/ops.json',ops);motor.editar(FILE,ops,lote=500)
    g.dump(OUT/'geracao.json',{'fonte_sha256':g.sha(SOURCE),'saida_sha256':g.sha(FILE),
        'clipes_revistos':list(counts),'chaves':counts,'operacoes_ultima_gravacao':len(ops),'metodo':'Relógio comum e vínculos rígidos; camadas sem deslocar raízes.'})
    repair_surfaces()
    print('Gravado:',FILE.name,flush=True)


v3.SOURCE=SOURCE;v3.OUT=OUT;v3.FILE=FILE


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--animar',action='store_true');ap.add_argument('--auditar',action='store_true')
    ap.add_argument('--validar',action='store_true');ap.add_argument('--previas',action='store_true')
    ap.add_argument('--estudo',action='store_true')
    ap.add_argument('--superficies',action='store_true')
    ap.add_argument('--clipes',nargs='+',choices=list(CLIPS),default=list(CLIPS));args=ap.parse_args()
    (OUT/'_cache').mkdir(parents=True,exist_ok=True)
    if args.estudo:review8.check(sysmod=__import__(__name__),names=args.clipes,study=True)
    if args.animar:bake(args.clipes)
    if args.superficies:repair_surfaces()
    if args.auditar:auditmod.audit(__import__(__name__),FILE,args.clipes,OUT/'auditoria-flicks.json')
    if args.validar:
        review8.check(sysmod=__import__(__name__),names=args.clipes)
        review8.check(sysmod=__import__(__name__),names=args.clipes,
                      reader_factory=auditmod.NativeSaved,sample_offset=.00047)
    if args.previas:
        m=bbmodelo.ler(FILE);raw=v2.review.Saved(m);rig=new_rig(m)
        class Reader:
            def pose(self,name,t):
                p=raw.pose(name,t)
                return {**compose_base(rig,name,t,saved=raw),**p} if name.endswith('upper') else p
        v2.review.OUT=OUT;v2.review.g.CLIPS=CLIPS
        v2.review.preview(m,Reader(),args.clipes,fps=20,size=640)


if __name__=='__main__':main()
