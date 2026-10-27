"""F3 v6: Low intacto, Left acelerado, Right sem espera e combo fechado."""
import argparse
import copy
import importlib.util
import json
import math
import shutil
from functools import lru_cache
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
    s=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
v5=module('golpes_f3_v5','animar-golpes-pavao-f3-v5.py')
g,bbmodelo,motor,render=v5.g,v5.bbmodelo,v5.motor,v5.render
R,point,unit,smooth,blend,track=v5.R,v5.point,v5.unit,v5.smooth,v5.blend,v5.track
Saved,base,SIDES,rod=v5.Saved,v5.base,v5.SIDES,v5.rod
SOURCE=v5.FILE;OUT=ROOT/'modelos/criatura-pavao/f3/ataques-v6';FILE=OUT/'criatura-pavao-e3-ataques-v6.bbmodel'
CLIPS={**v5.CLIPS,'attack_left':1.32,'attack_right':1.51}
TAKEOFF,LANDING,JUMP_HEIGHT=v5.TAKEOFF,v5.LANDING,v5.JUMP_HEIGHT
LEFT_TIME=[(0,0),(.22,.22),(.30,.30),(.34,.32),(.39,.40),(.43,.50),(.49,.60),(.70,.83),(1.,1.18),(1.32,1.50)]
RIGHT_TIME=[(0,0),(.10,.10),(.54,.54),(.60,.60),(.66,.80),(.84,.98),(1.02,1.16),(1.37,1.51),(1.51,1.65)]
WRIST_START=.60;WRIST_END=.91
CLOSE_START=.90;CLOSE_FULL=1.02;CLOSE_HOLD=1.43;CLOSE_END=1.62
COMBO_CHANNELS={'arm_left':['rotation'],'arm_right':['rotation'],
    'wing_left':['rotation','position'],'wing_right':['rotation','position']}


def source_time(name,t):
    if name=='attack_left':return float(track(t,LEFT_TIME))
    if name=='attack_right':return t if t<=.54 else float(track(t,RIGHT_TIME))
    return t


@lru_cache(maxsize=None)
def inverse_time(name,t):
    if name not in ['attack_left','attack_right']:return t
    lo,hi=0.,CLIPS[name]
    for _ in range(45):
        mid=(lo+hi)/2
        if source_time(name,mid)<t:lo=mid
        else:hi=mid
    return round((lo+hi)/2,9)


EVENTS={n:{key:inverse_time(n,t) for key,t in events.items()} for n,events in v5.EVENTS.items()}
ACTIVE={n:[(s,inverse_time(n,a),inverse_time(n,b)) for s,a,b in rows] for n,rows in v5.ACTIVE.items()}
# O usuário identifica 0,60 s como fim do corte; depois começa a retomada.
# A aferição do fio termina um quadro antes do contato/repouso, como no Low.
EVENTS['attack_right']['DamageEnd']=.60
ACTIVE['attack_right']=[('right',.37,.59)]


class Rig(v5.Rig):
    def __init__(self,m):
        super().__init__(m);self.source_reader=Saved(bbmodelo.ler(SOURCE));self.cache={};self.right_frames={}

    def soft_right_wrist(self,p,t):
        if not WRIST_START<t<WRIST_END:return
        w=self.weapons['right'];mat=self.mats(p);d=mat[w['name']][:3,:3]@w['frame'][:,1];normals=[]
        for time in [WRIST_START,WRIST_END]:
            if time not in self.right_frames:
                frame=self.mats(self.source_reader.pose('attack_right',source_time('attack_right',time)))[w['name']][:3,:3]
                self.right_frames[time]=(frame@w['frame'][:,1],frame@w['frame'][:,2])
            old,normal=self.right_frames[time];axis=np.cross(old,d)
            if np.linalg.norm(axis)>1e-10:
                angle=math.degrees(math.atan2(float(np.linalg.norm(axis)),float(old@d)));normal=rod(unit(axis),angle)@normal
            normals.append(unit(normal-d*(normal@d)))
        angle=math.degrees(math.atan2(float(d@np.cross(*normals)),float(normals[0]@normals[1])))
        normal=rod(d,angle*smooth((t-WRIST_START)/(WRIST_END-WRIST_START)))@normals[0]
        sword=self.direction_rotation('right',d,normal);self.set_world(p,'hand_right',sword@self.bind['right'].T)

    def pose(self,name,t):
        key=(name,round(t,9))
        if key in self.cache:return copy.deepcopy(self.cache[key])
        p=self.source_reader.pose(name,source_time(name,t))
        if name=='attack_right':self.soft_right_wrist(p,t)
        if name=='attack_combo':
            close=smooth((t-CLOSE_START)/(CLOSE_FULL-CLOSE_START))*(1-smooth((t-CLOSE_HOLD)/(CLOSE_END-CLOSE_HOLD)))
            if close>0:
                before=self.mats(p);yaw=v5.Rig.combo_yaw(t);turn=R([0,yaw,0])
                for side in SIDES:
                    w=self.weapons[side];d=before[w['name']][:3,:3]@w['frame'][:,1]
                    local=turn.T@d;local[0]*=1-close;target=unit(turn@local)
                    axis=np.cross(d,target);angle=math.degrees(math.atan2(float(np.linalg.norm(axis)),float(d@target)))
                    if np.linalg.norm(axis)>1e-10:self.set_world(p,'arm_'+side,rod(unit(axis),angle)@before['arm_'+side][:3,:3])
                    self.clear_floor(p,side,target=.015)
                for side in SIDES:self.set_world(p,'wing_'+side,before['wing_'+side][:3,:3])
                self.anchored_wings(p)
        self.cache[key]=copy.deepcopy(p);return p


def retime_ops(rig,m,name):
    source=next(a for a in m.animacoes if a['name']==name)
    ops=[{'op':'remove_animation','animation':name},{'op':'add_animation','name':name,'length':CLIPS[name],'loop':'once','snapping':120}]
    for bone,fields in rig.source_reader.channels[name].items():
        for field,(times,values) in fields.items():
            channel={'rotacao':'rotation','posicao':'position','escala':'scale'}[field]
            if name=='attack_right' and bone=='hand_right' and field=='rotacao':
                values=g.continuous_euler([rig.pose(name,inverse_time(name,float(t)))[bone][field] for t in times])
            for t,value in zip(times,values):
                ops.append({'op':'set_keyframe','animation':name,'bone':bone,'channel':channel,
                    'time':inverse_time(name,float(t)),'value':np.asarray(value).tolist(),'interpolation':'linear'})
    return ops


def combo_ops(rig,m):
    animation=next(a for a in m.animacoes if a['name']=='attack_combo');times=v5.sample_times(rig,'attack_combo',CLIPS['attack_combo'])
    source_times=[k['time'] for a in animation['animators'].values() for k in a.get('keyframes',[])]
    times=np.unique(np.round(np.r_[times,source_times,CLOSE_START,CLOSE_END],9));times=times[(times>=CLOSE_START)&(times<=CLOSE_END)]
    poses=[rig.pose('attack_combo',float(t)) for t in times];ops=[]
    for bone,channels in COMBO_CHANNELS.items():
        animator=animation['animators'].get(m.ossos[bone].uuid,{})
        for k in animator.get('keyframes',[]):
            if k['channel'] in channels and CLOSE_START<=k['time']<=CLOSE_END:
                ops.append({'op':'remove_keyframe','animation':'attack_combo','bone':bone,'channel':k['channel'],'time':k['time']})
        for channel in channels:
            field='rotacao' if channel=='rotation' else 'posicao';values=np.array([p[bone].get(field,[0,0,0]) for p in poses])
            if channel=='rotation':
                values=g.continuous_euler(values)
                old=rig.source_reader.pose('attack_combo',float(times[0]))[bone][field]
                values+=360*np.round((np.asarray(old)-values[0])/360)
            for t,value in zip(times,values):ops.append({'op':'set_keyframe','animation':'attack_combo','bone':bone,'channel':channel,'time':float(t),'value':np.round(value,9).tolist(),'interpolation':'linear'})
    return ops


def bake(names=None):
    names=names or ['attack_left','attack_right','attack_combo'];partial=set(names)!=set(['attack_left','attack_right','attack_combo'])
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'_cache').mkdir(exist_ok=True)
    if FILE.exists():
        record=json.loads((OUT/'geracao.json').read_text(encoding='utf-8'))
        if g.sha(FILE)!=record['saida_sha256']:raise ValueError('Modelo editado à mão: criar outra versão.')
    elif partial:raise ValueError('Gere a cópia completa antes de atualizar apenas um clipe.')
    m=bbmodelo.ler(SOURCE);rig=Rig(m);ops=[]
    for name in names:
        clip_ops=combo_ops(rig,m) if name=='attack_combo' else retime_ops(rig,m,name)
        ops.extend(clip_ops);print(name,len(clip_ops),'operações',flush=True)
    if partial and 'attack_combo' in names:
        # Para uma atualização parcial, remover as chaves realmente presentes na saída.
        current=bbmodelo.ler(FILE);old=next(a for a in current.animacoes if a['name']=='attack_combo')
        ops=[x for x in ops if not (x['op']=='remove_keyframe' and x.get('animation')=='attack_combo')]
        deletes=[]
        for bone,channels in COMBO_CHANNELS.items():
            for k in old['animators'].get(current.ossos[bone].uuid,{}).get('keyframes',[]):
                if k['channel'] in channels and CLOSE_START<=k['time']<=CLOSE_END:deletes.append({'op':'remove_keyframe','animation':'attack_combo','bone':bone,'channel':k['channel'],'time':k['time']})
        ops=deletes+ops
    if not partial:shutil.copy2(SOURCE,FILE)
    ops.append({'op':'set_model_properties','name':FILE.stem});g.dump(OUT/'_cache/ops.json',ops);motor.editar(FILE,ops,lote=500)
    g.dump(OUT/'geracao.json',{'fonte':SOURCE.relative_to(ROOT).as_posix(),'fonte_sha256':g.sha(SOURCE),'saida_sha256':g.sha(FILE),'clipes':CLIPS,'preservado':'attack_low e demais 19 clipes','combo_canais':COMBO_CHANNELS,'combo_janela':[CLOSE_START,CLOSE_END]})
    refs=OUT/'referencias';refs.mkdir(exist_ok=True)
    picture=Path('C:/Users/enzoc/AppData/Local/Temp/codex-clipboard-30e51931-63c6-464c-b02f-36cdac5631ac.png')
    if picture.exists() and not (refs/'combo-fechado.png').exists():shutil.copy2(picture,refs/'combo-fechado.png')
    metadata();print('Gravado:',FILE.name,flush=True)


def metadata():
    d=json.loads((SOURCE.parent/'animacoes.json').read_text(encoding='utf-8'))
    d.update(modelo=FILE.name,fonte=SOURCE.relative_to(ROOT).as_posix(),fonte_sha256=g.sha(SOURCE),saida_sha256=g.sha(FILE),status='golpes-v6-em-avaliacao',validacao='validacao-ataques.json')
    d['golpes']={n:{'duracao':x,'origem':'combat_ready@0','destino':'combat_ready@0','loop':False,'marcadores':EVENTS[n]} for n,x in CLIPS.items()}
    d['aprovacoes_parciais']={'attack_low':'Aprovado na v5 e preservado integralmente.',
        'attack_combo':'Movimento v5 aprovado; revisão só do fechamento das lâminas no descendente.'}
    d['aprovados']=list(dict.fromkeys(d.get('aprovados',[])+['attack_low']))
    d['controle_golpes']='Low intacto. Left com carga lenta e corte acelerado. Right com intervalo de frenagem encurtado e retomada axial suave do punho, mantendo o corte inicial. Combo aproxima as duas trajetórias e retira a abertura lateral no golpe duplo; salto, giro, corpo e pernas preservados.'
    d['referencias_usuario']=['referencias/combo-fechado.png'];g.dump(OUT/'animacoes.json',d)


def main():
    ap=argparse.ArgumentParser()
    for flag in ['estudo','gerar','validar','nativo']:ap.add_argument('--'+flag,action='store_true')
    ap.add_argument('--clipes',nargs='+',choices=['attack_left','attack_right','attack_combo']);a=ap.parse_args();review=module('revisao_golpes_v6','revisar-golpes-pavao-f3-v6.py')
    if a.estudo:review.study(__import__(__name__))
    if a.gerar:bake(a.clipes)
    if a.validar:review.check(__import__(__name__))
    if a.nativo:review.capture(__import__(__name__))


if __name__=='__main__':main()
