"""Corridas pacífica/armada da F3 e transições com fase contínua.

Base v10 preservada. Escrita somente pelo motor externo, em saída nova.
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
    sp=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod);return mod

v7=module('corrida_base_f3','animar-combate-pavao-f3-v7.py')
v3,v5,g,v2=v7.v3,v7.v5,v7.g,v7.v2
bbmodelo,motor,render=v3.bbmodelo,v3.motor,v3.render
R,point,unit,smooth,blend=g.R,g.point,g.unit,g.smooth,g.blend
Saved=v2.review.Saved
native=module('amostrador_corrida_f3','revisar-flicks-pavao-f3-v9.py')
reduce=module('reducao_corrida_f3','corrigir-flicks-pavao-f3-v10.py')
SOURCE=ROOT/'modelos/criatura-pavao/f3/animacoes-v10/criatura-pavao-e3-combate-v10.bbmodel'
OUT=ROOT/'modelos/criatura-pavao/f3/corrida-v1'
FILE=OUT/'criatura-pavao-e3-corrida-v1.bbmodel'
v3.SOURCE=SOURCE
SIDES=['left','right']
PERIOD={False:.84,True:.96}
WALK={False:1.5,True:1.8}
STANCE={False:.42,True:.44}
STRIDE={False:13.2,True:12.2}
WALK_STANCE={False:.63,True:.66}
WALK_STRIDE={False:10.,True:8.5}
CLIPS={'run':.84,'run_start':.60,'run_stop':.66,
       'combat_run':.96,'combat_run_start':.66,'combat_run_stop':.72}
LOOPS={'run','combat_run'}
FPS=240
ARM_CHAIN={'body','pelvis','waist','torso','arm_right','forearm_right','hand_right'}


def mode(name):return name.startswith('combat_')
def walk_name(combat):return 'combat_walk' if combat else 'walk'
def run_name(combat):return 'combat_run' if combat else 'run'


def timing(name,t):
    """Integral da frequência: não zera a fase ao acelerar/desacelerar."""
    combat=mode(name)
    if name in LOOPS:return t/PERIOD[combat],1.
    d=CLIPS[name];u=float(np.clip(t/d,0,1));w=smooth(u)
    integral=u**6-3*u**5+2.5*u**4
    f0,f1=(1/PERIOD[combat],1/WALK[combat]) if name.endswith('stop') else (1/WALK[combat],1/PERIOD[combat])
    return d*(f0*u+(f1-f0)*integral),1-w if name.endswith('stop') else w


class Rig(v3.Rig):
    drag_target=v5.Rig.drag_target

    def __init__(self,m):
        super().__init__(m)
        self.drag_cache={};self.root_evaluations=[];self.cache={}
        self.footverts={}
        for side in SIDES:
            cubes=[c for c in m.cubos if c.nome.startswith('toe_'+side) or c.nome=='foot_base_'+side]
            self.footverts[side]=np.concatenate([bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,self.rest),bbmodelo.cantos(c)) for c in cubes])-self.feet[side]

    def foot(self,side,center,roll,height=0.,pivot_weight=1.):
        s=-1 if side=='left' else 1
        rotation=R([roll,0,s*1.5*abs(roll)/20])
        center=np.asarray(center,float).copy()
        rotated=self.footverts[side]@rotation.T
        # O vértice de apoio não escorrega enquanto o calcanhar se levanta.
        pivot=self.footverts[side][int(np.argmin(rotated[:,1]))]
        compensation=pivot-rotation@pivot
        center[[0,2]]+=compensation[[0,2]]*pivot_weight
        center[1]=height-float(rotated[:,1].min())
        return center,rotation

    def gait(self,phase,weight,combat):
        stance=float(blend(WALK_STANCE[combat],STANCE[combat],weight))
        stride=float(blend(WALK_STRIDE[combat],STRIDE[combat],weight))
        lift=float(blend(2.2,3.9 if combat else 4.4,weight))
        feet={};rolls={};contacts={}
        for side,off in [('left',0),('right',.5)]:
            ph=(phase+off)%1;c=self.feet[side].copy()
            if ph<stance:
                q=ph/stance;c[2]+=stride*(q-.5);height=0.
                roll=-18*weight*smooth((q-.60)/.40)
                contacts[side]=True
            else:
                u=(ph-stance)/(1-stance);vel=stride*(1-stance)/stance
                c[2]+=(2*u**3-3*u*u+1)*stride/2+(u**3-2*u*u+u)*vel
                c[2]+=(-2*u**3+3*u*u)*(-stride/2)+(u**3-u*u)*vel
                height=lift*math.sin(math.pi*u)**2
                roll=-18*weight*(1-smooth(u/.18))+(-10+15*weight)*math.sin(math.pi*u)**2
                contacts[side]=False
            feet[side],_=self.foot(side,c,roll,height,pivot_weight=weight);rolls[side]=roll
        return feet,rolls,contacts

    def body_run(self,phase,combat):
        phase%=1.;a=2*math.pi*phase
        p=self.saved.pose(walk_name(combat),phase*WALK[combat])
        # Dois apoios por ciclo. Compressão antes do impulso, seguida de voo.
        heave=math.cos(2*a+.30*math.pi);load=math.cos(2*a+.05*math.pi)
        p['body']={'rotacao':np.array([(0 if combat else -17)-3.2*load,2.8*math.sin(a),2.9*math.sin(a)]),
                   'posicao':np.array([.48*math.sin(a),(-4.6 if combat else -4.9)+(1.15 if combat else 1.35)*heave,
                                       .40*math.sin(2*a-.5)])}
        p['pelvis']['rotacao']=np.array([-.9*math.cos(2*a-.40),3.9*math.sin(a-.20),-.8*math.sin(a-.15)])
        p['waist']['rotacao']=np.array([-2.5+1.4*math.cos(2*a-.25),-2.0*math.sin(a-.20),.45*math.sin(a-.50)])
        p['torso']['rotacao']=np.array([(-4 if combat else -5)-2.3*math.cos(2*a-.60),-3.0*math.sin(a-.38),.7*math.sin(a-.80)])
        p['neck_1']['rotacao']=np.array([(2 if combat else 16)+1.9*math.cos(2*a-.8),.7*math.sin(a-.2),.35*math.sin(a-.35)])
        p['neck_2']['rotacao']=np.array([2.4+1.0*math.cos(2*a-1.),.3*math.sin(a-.4),0])
        # Estabiliza parcialmente o olhar; preserva o impacto visível no pescoço/cabeça.
        self.set_world(p,'head',R([-2+2.8*math.cos(2*a-.92),-1.6*math.sin(a-.35),-.8*math.sin(a-.4)]))
        self.set_world(p,'tail_1',R([(-5 if combat else -12)+3.4*math.cos(2*a-1.0),
                                    -5.2*math.sin(a-.5),-2.0*math.sin(a-.45)]))
        p['tail_2']['rotacao']=np.array([2.0*math.cos(2*a-1.15),-2.1*math.sin(a-.9),.7*math.sin(a-.8)])
        for side,s in [('left',-1),('right',1)]:
            for i in [1,2]:
                p[f'feather_{side}_{i}']['rotacao']=np.array([-3+2.2*math.cos(2*a-1.0-i*.2),
                                                             s*1.0*math.sin(a-.6),s*.45*math.sin(2*a-.7)])
            p['wing_'+side]['rotacao']=np.array([2.4*math.sin(a-.65)*s,s*.9*math.sin(a-.4),0])
            for n in self.anchors:
                if n.startswith('back_') and side in n:
                    p[n]['rotacao']=np.array([(45 if combat else -4)+2.4*math.cos(2*a-.8),
                                              -s*1.3*math.sin(a-.5),0])
            if not combat:
                self.fk(p,side,R([13+6*s*math.sin(a-.2),-s*2,s*5]),-22-4*s*math.sin(a-.6),R([3,0,0]))
        self.anchored_wings(p)
        return p

    def arms(self,p,phase,combat,weight,old):
        if not combat:
            for side in SIDES:self.sheathed(p,side)
            return
        # Mantém a assinatura aprovada: esquerdo no ombro, direito em arrasto.
        # Torso/coluna amortecem o peso, em vez de transformar a arma num pêndulo.
        a=2*math.pi*phase;oldmat=self.mats(old)
        for side in SIDES:
            target,rot=self.shoulder_target(p) if side=='left' else self.drag_target(p)
            oldshoulder=point(oldmat['torso'],self.m.ossos['arm_'+side].origem)
            oldtarget=oldshoulder+([-2,3,-6] if side=='left' else [3.4,-13,2.2])
            weapon=self.weapons[side];actual=oldmat[weapon['name']]
            target+= (point(actual,weapon['grip'])-oldtarget)*(1-weight)
            if side=='left':rot=R([1.1*weight*math.cos(2*a-.6),.7*weight*math.sin(a-.4),0])@rot
            rot=g.slerp(actual[:3,:3],rot,weight)
            pref=g.slerp(R(old['arm_'+side]['rotacao']),R([-5,0,35] if side=='left' else [-42,0,0]),weight)
            self.carry(p,side,target,rot,pref)
            # Vínculo de empunhadura constante; evita drift de compensação.
            mat=self.mats(p)['hand_'+side]
            self.weapon(p,side,point(mat,self.grips[side]),mat[:3,:3]@self.bind[side])

    def pose(self,name,t):
        key=(name,round(t,9))
        if key in self.cache:return copy.deepcopy(self.cache[key])
        combat=mode(name);phase,weight=timing(name,t);ph=phase%1
        old=self.saved.pose(walk_name(combat),ph*WALK[combat])
        if name not in LOOPS and (t<=0 or t>=CLIPS[name]-1e-9):
            p=old if weight<.5 else self.pose(run_name(combat),ph*PERIOD[combat])
        else:
            running=self.body_run(ph,combat)
            p=self.mix_pose(old,running,weight) if weight<1 else running
            feet,rolls,_=self.gait(ph,weight,combat)
            self.legs(p,feet,rolls)
            # As bases aprovadas podem ter pequenas compensações próprias.
            # A âncora migra continuamente para o vínculo rígido do novo ciclo.
            for n,anchor in self.anchors.items():
                o=self.m.ossos[n];orig=old[n]
                oldroot=o.origem+np.asarray(orig.get('posicao',[0,0,0]))+R(orig['rotacao'])@(anchor-o.origem)
                desired=blend(oldroot,anchor,weight)
                p[n]['posicao']=desired-o.origem-R(p[n]['rotacao'])@(anchor-o.origem)
            self.arms(p,ph,combat,weight,old)
        self.cache[key]=copy.deepcopy(p)
        return p


def bake():
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'_cache').mkdir(exist_ok=True)
    if FILE.exists():
        record=json.loads((OUT/'geracao.json').read_text(encoding='utf-8'))
        if record['saida_sha256']!=g.sha(FILE):raise ValueError('Saída editada; criar outra versão.')
    m=bbmodelo.ler(SOURCE);rig=Rig(m);ops=[];counts={}
    for name,duration in CLIPS.items():
        times=np.linspace(0,duration,round(duration*FPS)+1)
        forced={0,len(times)-1}
        if name in LOOPS:
            arrival,_=timing(name+'_start',CLIPS[name+'_start'])
            arrival=(arrival%1)*duration
            times=np.unique(np.r_[times,arrival]);forced={0,len(times)-1,int(np.argmin(abs(times-arrival)))}
        poses=[rig.pose(name,float(t)) for t in times]
        ops.append({'op':'add_animation','name':name,'length':duration,'loop':'loop' if name in LOOPS else 'once','snapping':120})
        count=0
        for bone in m.ossos:
            for ch,field,tol in [('rotation','rotacao',.004),('position','posicao',.00025)]:
                vals=np.array([p[bone].get(field,[0,0,0]) for p in poses],float)
                if ch=='rotation':vals=g.continuous_euler(vals)
                ids=reduce.common_rdp(times,vals/tol,forced)
                # O arrasto exige que tronco e braço direito compartilhem o
                # relógio nativo. Só essa cadeia conserva a grade completa.
                if mode(name) and bone in ARM_CHAIN:ids=range(len(times))
                if np.max(np.ptp(vals,axis=0))<1e-8:ids=[0,len(times)-1]
                for i in ids:
                    ops.append({'op':'set_keyframe','animation':name,'bone':bone,'channel':ch,
                        'time':round(float(times[i]),9),'value':np.round(vals[i],9).tolist(),'interpolation':'linear'});count+=1
        counts[name]=count;print('Calculado:',name,count,'chaves',flush=True)
    assert rig.max_unreachable<.005,('Alvo fora do alcance',rig.max_unreachable,rig.reach)
    shutil.copy2(SOURCE,FILE)
    ops.append({'op':'set_model_properties','name':FILE.stem})
    g.dump(OUT/'_cache/ops.json',ops);motor.editar(FILE,ops,lote=500)
    g.dump(OUT/'geracao.json',{'fonte':SOURCE.relative_to(ROOT).as_posix(),'fonte_sha256':g.sha(SOURCE),
        'saida_sha256':g.sha(FILE),'operacoes':len(ops),'chaves':counts,'clipes':CLIPS,'alcance_excedido':rig.max_unreachable})
    print('Gravado:',FILE.name,flush=True)


def fix_links():
    """Inclui no loop a pose exata onde termina a partida já gravada."""
    record=json.loads((OUT/'geracao.json').read_text(encoding='utf-8'))
    if record['saida_sha256']!=g.sha(FILE):raise ValueError('Saída editada; preservar em outra versão.')
    m=bbmodelo.ler(FILE);saved=Saved(m);rig=Rig(m);ops=[]
    for name in sorted(LOOPS):
        phase,_=timing(name+'_start',CLIPS[name+'_start']);t=(phase%1)*CLIPS[name]
        pose=rig.pose(name,t);before=saved.pose(name,t);added=0
        for n in m.ossos:
            for ch,field in [('rotation','rotacao'),('position','posicao')]:
                value=np.asarray(pose[n].get(field,[0,0,0]),float)
                if ch=='rotation':value=g.continuous_euler([before[n].get(field,[0,0,0]),value])[1]
                ts=saved.channels[name][n][field][0]
                added+=int(np.min(abs(ts-t))>1e-6)
                ops.append({'op':'set_keyframe','animation':name,'bone':n,'channel':ch,'time':round(t,9),
                            'value':np.round(value,9).tolist(),'interpolation':'linear'})
        record['chaves'][name]+=added
    g.dump(OUT/'_cache/ops-encaixes.json',ops);motor.editar(FILE,ops,lote=500)
    record['saida_sha256']=g.sha(FILE);record['encaixes_exatos']=True;record['operacoes']+=len(ops)
    g.dump(OUT/'geracao.json',record);metadata()
    print('Poses exatas de encaixe incluídas nos dois loops.',flush=True)


def sync_arms():
    record=json.loads((OUT/'geracao.json').read_text(encoding='utf-8'))
    if record['saida_sha256']!=g.sha(FILE):raise ValueError('Saída editada; preservar em outra versão.')
    m=bbmodelo.ler(FILE);saved=Saved(m);ops=[]
    for name,d in CLIPS.items():
        if not mode(name):continue
        times=np.unique(np.round(np.r_[np.linspace(0,d,round(d*FPS)+1),
            np.concatenate([ts for n,ch in saved.channels[name].items() if n in ARM_CHAIN for ts,_ in ch.values()])],9))
        for n in ARM_CHAIN:
            for field,(ts,values) in saved.channels[name][n].items():
                if np.max(np.ptp(values,axis=0))<1e-8:continue
                for t in times:
                    value=[float(np.interp(t,ts,values[:,i])) for i in range(3)]
                    ops.append({'op':'set_keyframe','animation':name,'bone':n,
                        'channel':'rotation' if field=='rotacao' else 'position','time':float(t),
                        'value':value,'interpolation':'linear'})
    g.dump(OUT/'_cache/ops-cadeia-arrasto.json',ops);motor.editar(FILE,ops,lote=500)
    updated=bbmodelo.ler(FILE)
    record['chaves']={a['name']:sum(len(x.get('keyframes',[])) for x in a['animators'].values()) for a in updated.animacoes if a['name'] in CLIPS}
    record['saida_sha256']=g.sha(FILE);record['cadeia_arrasto_sincrona']=sorted(ARM_CHAIN);record['operacoes']+=len(ops)
    g.dump(OUT/'geracao.json',record);metadata()
    print('Cadeia do arrasto sincronizada nos três clipes armados.',flush=True)


def metadata():
    meta=json.loads((SOURCE.parent/'animacoes.json').read_text(encoding='utf-8'))
    meta.update(modelo=FILE.name,fonte=SOURCE.relative_to(ROOT).as_posix(),fonte_sha256=g.sha(SOURCE),
                saida_sha256=g.sha(FILE),status='corridas-f3-em-avaliacao')
    meta['validacao']='validacao-corrida.json'
    for key in ['validacao_nativa','comparacao_tecnica','comparacao_render','medicao_fps']:
        if key in meta.get('flicks',{}):meta['flicks'][key]='../animacoes-v10/'+meta['flicks'][key]
    meta['flicks']['relatorios_historicos']='Arquivos da base v10 preservada; não são medições desta corrida.'
    meta['corridas']={name:{'duracao':d,'loop':name in LOOPS} for name,d in CLIPS.items()}
    for c in [False,True]:
        p=PERIOD[c]
        meta['corridas'][run_name(c)]['eventos']={'FootLeft':0.,'FootRight':.5*p,
            'LiftLeft':STANCE[c]*p,'LiftRight':(.5+STANCE[c])*p}
    for name,d in CLIPS.items():
        if name in LOOPS:continue
        combat=mode(name);ph,w=timing(name,d)
        meta['corridas'][name].update(origem=run_name(combat) if name.endswith('stop') else walk_name(combat),
            tempo_origem=0.,destino=walk_name(combat) if name.endswith('stop') else run_name(combat),
            fase_destino=ph%1,tempo_destino=(ph%1)*(WALK[combat] if name.endswith('stop') else PERIOD[combat]))
    meta['corridas']['integracao']='Somente animações. Reutilizar fase/velocidade e fazer crossfade ao interromper transições; os clipes não implementam esse controle no jogo.'
    meta['corridas']['posturas']={'run':'tronco baixo, peito/pelve contrapostos, cauda em contrapeso e braços recolhidos',
        'combat_run':'inclinação intermediária, passada pesada, esquerda no ombro e direita no arrasto'}
    meta['corridas']['velocidade_referencia_unidades_s']={run_name(c):STRIDE[c]/STANCE[c]/PERIOD[c] for c in [False,True]}
    meta['corridas']['sem_root_motion']=True
    g.dump(OUT/'animacoes.json',meta)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--gerar',action='store_true');ap.add_argument('--estudo',action='store_true')
    ap.add_argument('--validar',action='store_true');ap.add_argument('--previas',action='store_true');ap.add_argument('--nativo',action='store_true');ap.add_argument('--encaixes',action='store_true');ap.add_argument('--sincronizar',action='store_true');args=ap.parse_args()
    review=module('revisao_corrida_f3','revisar-corrida-pavao-f3.py')
    if args.estudo:review.study(__import__(__name__))
    if args.gerar:bake();metadata()
    if args.encaixes:fix_links()
    if args.sincronizar:sync_arms()
    if args.validar:review.check(__import__(__name__))
    if args.previas:review.previews(__import__(__name__))
    if args.nativo:
        capture=module('captura_corrida_f3','previas-corrida-pavao-f3.py')
        capture.capture(__import__(__name__))


if __name__=='__main__':main()
