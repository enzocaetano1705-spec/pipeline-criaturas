"""Desacelera só o braço do arrasto; conserva o braço esquerdo da v6.

A mão direita completa a descida aos 1,65 s, junto do apoio no ombro.
Retarget da trajetória anterior sobre o torso atual, com cotovelo em dobradiça.
"""
import argparse
import importlib.util
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
    sp=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
v3=module('combate_f3_v3','animar-combate-pavao-f3-v3.py')
v5=module('combate_f3_v5','animar-combate-pavao-f3-v5.py')
g=v3.g;v2=v3.v2;bbmodelo=v3.bbmodelo
SOURCE=ROOT/'modelos/criatura-pavao/f3/animacoes-v6/criatura-pavao-e3-combate-v6.bbmodel'
REFERENCE=ROOT/'modelos/criatura-pavao/f3/animacoes-v5/criatura-pavao-e3-combate-v5.bbmodel'
OUT=ROOT/'modelos/criatura-pavao/f3/animacoes-v7'
FILE=OUT/'criatura-pavao-e3-combate-v7.bbmodel'
START=.4;LENGTH=1.65;CLIPS={'combat_enter':LENGTH}
CHANGED={'arm_right','forearm_right','hand_right','tail_fan_06'}


def right_time(t):
    if t<=START:return t
    u=float(np.clip((t-START)/(LENGTH-START),0,1))
    # Velocidade inicial igual à fonte; desacelera até parar, sem pausa interna.
    return START+.5*(2.5*u-2*u*u+.5*u**3)


class Rig(v3.Rig):
    drag_target=v5.Rig.drag_target

    def __init__(self,m):
        super().__init__(m)
        self.reference=v2.review.Saved(bbmodelo.ler(REFERENCE))
        self.drag_cache={};self.root_evaluations=[]

    def enter(self,t,moving=False):
        p=self.saved.pose('combat_enter',t)
        if t<=START or t>=LENGTH:return p
        old=self.reference.pose('combat_enter',right_time(t))
        mats=self.mats(old);torso=self.mats(p)['torso']
        transfer=torso@np.linalg.inv(mats['torso'])
        w=self.weapons['right'];world=transfer@mats[w['name']]
        grip=g.point(world,w['grip']);rot=world[:3,:3]
        # A compensação do torso/apoio entra progressivamente. O gesto longo
        # termina na mesma empunhadura e no mesmo piso da marcha aprovada.
        weight=g.smooth((t-.50)/(LENGTH-.50))
        pref=g.R(old['arm_right']['rotacao'])
        if weight:
            target,target_rot=self.drag_target(p)
            grip=g.blend(grip,target,weight)
            rot=g.slerp(rot,target_rot,weight)
            pref=g.slerp(pref,g.R([-42,0,0]),weight)
        self.held(p,'right',grip,rot,pref)
        return p


def samples(m):
    anim=next(a for a in m.animacoes if a['name']=='combat_enter')
    original=np.unique([float(k['time']) for a in anim['animators'].values() for k in a.get('keyframes',[])])
    # Não cria duas chaves quase simultâneas quando a grade de 240 Hz cruza
    # uma chave não uniforme da v6. As chaves originais têm precedência.
    dense=np.linspace(START,LENGTH,301)
    dense=dense[np.min(abs(dense[:,None]-original[None,:]),axis=1)>.00012]
    return np.unique(np.round(np.r_[original,dense],8))


def bake():
    m=v3.prepare();rig=Rig(m);anim=next(a for a in m.animacoes if a['name']=='combat_enter')
    times=samples(m);times=times[times>=START]
    poses=[rig.enter(float(t)) for t in times]
    names={o.uuid:n for n,o in m.ossos.items()};ops=[]
    for uid,a in anim['animators'].items():
        n=names.get(uid)
        if n not in CHANGED:continue
        for k in a.get('keyframes',[]):
            if float(k['time'])>START:
                ops.append({'op':'remove_keyframe','animation':'combat_enter','bone':n,
                            'channel':k['channel'],'time':float(k['time'])})
        for ch,field in [('rotation','rotacao'),('position','posicao')]:
            vals=np.array([p[n][field] for p in poses])
            if ch=='rotation':
                vals=g.continuous_euler(vals)
                # Escolhe o ramo de Euler que continua a chave da v6 em 0,40 s.
                vals+=360*np.round((poses[0][n][field]-vals[0])/360)
            for t,value in zip(times,vals):
                ops.append({'op':'set_keyframe','animation':'combat_enter','bone':n,
                    'channel':ch,'time':float(t),'value':np.round(value,8).tolist(),'interpolation':'linear'})
    g.dump(OUT/'_cache/ops-animacoes.json',ops);v3.motor.editar(FILE,ops)
    g.dump(OUT/'geracao.json',{'fonte_sha256':g.sha(SOURCE),'referencia_sha256':g.sha(REFERENCE),
        'saida_sha256':g.sha(FILE),'clipes_revistos':list(CLIPS),'ossos_revistos':sorted(CHANGED),
        'operacoes':len(ops),'alcance_excedido':rig.max_unreachable,
        'metodo':'Trajetória direita independente; todas as chaves do lado esquerdo preservadas.'})
    print('Gravado:',FILE.name,flush=True)


def checks(report,m,rig,saved):
    src=bbmodelo.ler(SOURCE);original=v2.review.Saved(src)
    a=next(a for a in src.animacoes if a['name']=='combat_enter')
    b=next(a for a in m.animacoes if a['name']=='combat_enter')
    names={o.uuid:n for n,o in m.ossos.items()}
    unchanged=[]
    for uid,animator in a['animators'].items():
        if names.get(uid) not in CHANGED and animator.get('keyframes'):
            assert animator==b['animators'][uid],names.get(uid)
            unchanged.append(names.get(uid))
    report['animadores_preservados_integralmente']=unchanged
    err=0.;speeds=[];angles=[];old_speeds=[];old_angles=[];previous=None;path=[];bottom=[]
    for t in np.linspace(0,LENGTH,397):
        mats=rig.mats(saved.pose('combat_enter',float(t)))
        old=rig.mats(original.pose('combat_enter',float(t)))
        for n in ['arm_left','forearm_left','hand_left','tail_fan_04']:
            err=max(err,float(abs(mats[n]-old[n]).max()))
        w=rig.weapons['right'];mat=mats[w['name']]
        grip=g.point(mat,w['grip']);tip=grip+mat[:3,:3]@w['frame'][:,1]*w['length']
        path.append((float(t),grip,tip))
        bottom.append(float((rig.weaponverts['right']@mat[:3,:3].T+grip)[:,1].min()))
        if previous is not None and t>.4:
            speeds.append(float(np.linalg.norm(grip-previous[0])*240))
            delta=previous[1].T@mat[:3,:3]
            angles.append(float(np.degrees(np.arccos(np.clip((np.trace(delta)-1)/2,-1,1)))*240))
            old_speeds.append(float(np.linalg.norm(g.point(old[w['name']],w['grip'])-previous[2])*240))
            delta=previous[3].T@old[w['name']][:3,:3]
            old_angles.append(float(np.degrees(np.arccos(np.clip((np.trace(delta)-1)/2,-1,1)))*240))
        previous=(grip,mat[:3,:3],g.point(old[w['name']],w['grip']),old[w['name']][:3,:3])
    report['erro_braco_esquerdo_v6_matriz']=err
    report['ritmo_direito']={'inicio_ajuste':START,'chegada_arrasto':LENGTH,
        'chegada_ombro_esquerdo':LENGTH,'pico_velocidade_mao_apos_saque':max(speeds),
        'pico_velocidade_mao_v6':max(old_speeds),'pico_angular_espada_v6':max(old_angles),
        'pico_angular_espada_apos_saque':max(angles),'min_ponta_y':min(bottom),
        'ponta_final_y':bottom[-1]}
    if err>1e-8:report['erros'].append('Braço esquerdo aprovado mudou')
    if abs(bottom[-1])>.025:report['erros'].append('Arrasto final perdeu o chão')
    g.dump(OUT/'_cache/trajetoria-direita.json',path)


v3.SOURCE=SOURCE;v3.OUT=OUT;v3.FILE=FILE;v3.CLIPS=CLIPS;v3.Rig=Rig
v3.FLOURISH_START=.70;v3.FLOURISH_END=1.23


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--animar',action='store_true')
    ap.add_argument('--validar',action='store_true');ap.add_argument('--previas',action='store_true')
    args=ap.parse_args();(OUT/'_cache').mkdir(parents=True,exist_ok=True)
    if args.animar:bake()
    if args.validar:v3.validate(list(CLIPS),flourish_sides=('left',),extra_checks=checks,preserve_draw_until=START)
    if args.previas:v3.previews(list(CLIPS))


if __name__=='__main__':main()
