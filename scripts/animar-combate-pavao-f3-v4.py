"""Guarda da F3 derivada da marcha aprovada; floreio só da arma do ombro.

Os lados seguem a criatura: esquerda no ombro, direita no arrasto. Mantém
combat_walk integralmente; substitui somente combat_ready e combat_enter.
"""
import argparse
import copy
import importlib.util
import math
from pathlib import Path

import numpy as np
from PIL import Image,ImageDraw
from criaturas import bbmodelo,render

ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('combate_f3_v3',ROOT/'scripts/animar-combate-pavao-f3-v3.py')
v3=importlib.util.module_from_spec(sp);sp.loader.exec_module(v3)
g=v3.g;v2=v3.v2
R,point,unit,smooth,blend=v3.R,v3.point,v3.unit,v3.smooth,v3.blend
SOURCE=v3.FILE
OUT=ROOT/'modelos/criatura-pavao/f3/animacoes-v4'
FILE=OUT/'criatura-pavao-e3-combate-v4.bbmodel'
CLIPS={'combat_ready':2.4,'combat_enter':2.1}
DRAG_READY=.90
# Alinha a recuperação a uma chave de 120 Hz, depois da volta aprovada.
SHOULDER_START=1.70


class Rig(v3.Rig):
    def __init__(self,m):
        super().__init__(m)
        self.walk_still=self.saved.pose('combat_walk',0)
        mats=bbmodelo.matrizes_ossos(self.orig,self.walk_still)
        self.ready_feet={s:point(mats['foot_'+s],self.feet[s]) for s in ['left','right']}
        initial=self.saved.pose('combat_enter',.50)
        self.draw_end_mats=bbmodelo.matrizes_ossos(self.orig,initial)
        self.spin_end=self.saved.pose('combat_enter',SHOULDER_START)
        self.spin_end_mats=bbmodelo.matrizes_ossos(self.orig,self.spin_end)

    def ready(self,t=0):
        # O primeiro quadro é precisamente a postura da marcha aprovada.
        if abs(t%CLIPS['combat_ready'])<1e-10:return copy.deepcopy(self.walk_still)
        p=copy.deepcopy(self.walk_still);breath=math.sin(2*math.pi*t/CLIPS['combat_ready'])
        p['body']['posicao']+=np.array([0,.18*breath,0])
        p['waist']['rotacao'][0]+=.3*breath
        p['torso']['rotacao'][0]-=.9*breath
        p['neck_1']['rotacao'][0]+=.5*breath
        p['tail_1']['rotacao'][0]+=.6*breath
        p['tail_2']['rotacao'][0]+=.25*breath
        for n in self.anchors:p[n]['rotacao'][0]+=.35*breath
        reference=self.mats(self.walk_still)['head'][:3,:3]
        self.set_world(p,'head',R([-.2*breath,0,0])@reference)
        self.legs(p,self.ready_feet)
        self.carry(p,'left',*self.shoulder_target(p),R([-5,0,35]))
        self.carry(p,'right',*self.drag_target(p),R([-42,0,0]))
        self.anchored_wings(p)
        return p

    def enter(self,t,moving=False):
        if t>=2.1:return self.ready(0)
        p=self.saved.pose('combat_enter',t)
        if t<=.50:return p
        # Mantém o corpo/floreio aprovados. Só após a volta a postura assenta
        # na inclinação e altura da marcha, agora sem deslocamento dos pés.
        settle=smooth((t-SHOULDER_START)/(2.1-SHOULDER_START))
        if settle:p=self.mix_pose(p,self.walk_still,settle)

        feet={s:self.feet[s].copy() for s in ['left','right']}
        # Passos curtos até a base escalonada da marcha, sem deslizar as solas.
        for s,start,end in [('left',.50,.84),('right',1.71,2.1)]:
            w=smooth((t-start)/(end-start))
            feet[s]=blend(self.feet[s],self.ready_feet[s],w)
            feet[s][1]+=.9*math.sin(math.pi*w)**2
        self.legs(p,feet)

        # A espada do chão encerra seu gesto antes do início do floreio.
        side='right';grip,rot=self.drag_target(p);pref=R([-42,0,0])
        if t<DRAG_READY:
            u=smooth((t-.50)/(DRAG_READY-.50))
            old=self.draw_end_mats[self.weapons[side]['name']]
            grip=blend(point(old,self.weapons[side]['grip']),grip,u)
            rot=g.slerp(old[:3,:3],rot,u)
            initial=self.saved.pose('combat_enter',.50)
            pref=g.slerp(R(initial['arm_right']['rotacao']),pref,u)
            self.held(p,side,grip,rot,pref)
        else:self.carry(p,side,grip,rot,pref)

        if t>SHOULDER_START:
            side='left';final_grip,final_rot=self.shoulder_target(p)
            final_rot=self.aligned_roll(p,side,final_grip,final_rot,R([-5,0,35]))
            old=self.spin_end_mats[self.weapons[side]['name']]
            grip=blend(point(old,self.weapons[side]['grip']),final_grip,settle)
            rot=g.slerp(old[:3,:3],final_rot,settle)
            pref=g.slerp(R(self.spin_end['arm_left']['rotacao']),R([-5,0,35]),settle)
            self.held(p,side,grip,rot,pref)
        self.anchored_wings(p)
        return p


def checks(report,m,rig,saved):
    errors=report['erros'];src=v2.review.Saved(bbmodelo.ler(SOURCE))
    ma=rig.mats(saved.pose('combat_ready',0));mb=rig.mats(src.pose('combat_walk',0))
    err=max(float(abs(ma[n]-mb[n]).max()) for n in ma)
    report['guarda_igual_marcha_quadro_zero']=err
    report['combat_walk_preservado_integralmente']='combat_walk' in report['clipes_preservados']
    if err>1e-5:errors.append('Guarda não coincide com a postura da marcha aprovada')
    contact=0.
    for name,start,end in [('combat_ready',0,2.4),('combat_enter',DRAG_READY,2.1)]:
        for t in np.linspace(start,end,round((end-start)*240)+1):
            mat=rig.mats(saved.pose(name,float(t)));w=rig.weapons['right'];wm=mat[w['name']]
            vertices=rig.weaponverts['right']@wm[:3,:3].T+point(wm,w['grip'])
            contact=max(contact,abs(float(vertices[:,1].min())))
    report['erro_contato_espada_em_descanso']=contact
    if contact>.025:errors.append('Espada de arrasto perde contato com o piso')
    ds=[];preserved=0.
    for t in np.linspace(v3.FLOURISH_START,v3.FLOURISH_END,181):
        mat=rig.mats(saved.pose('combat_enter',float(t)))
        w=rig.weapons['right'];ds.append(mat[w['name']][:3,:3]@w['frame'][:,1])
        old=rig.mats(src.pose('combat_enter',float(t)))
        for n in ['arm_left','forearm_left','hand_left','tail_fan_04']:
            preserved=max(preserved,float(abs(mat[n]-old[n]).max()))
    ds=np.array(ds);pitch=np.degrees(np.unwrap(np.arctan2(ds[:,2],ds[:,1])))
    report['variacao_angular_espada_sem_floreio']=float(np.ptp(pitch))
    report['erro_floreio_aprovado_braço_ombro']=preserved
    if np.ptp(pitch)>5:errors.append('Espada do chão está participando do floreio')
    if preserved>.002:errors.append('Floreio aprovado do braço do ombro mudou')


def overview(samples=None):
    m=bbmodelo.ler(FILE);saved=v2.review.Saved(m)
    samples=samples or [('combat_ready',0,0),('combat_ready',0,90),('combat_enter',.90,65),
             ('combat_enter',1.40,35),('combat_enter',1.90,65),('combat_enter',2.1,35)]
    sheet=Image.new('RGB',(768,768),(238,242,244));d=ImageDraw.Draw(sheet)
    for i,(name,t,az) in enumerate(samples):
        mat=bbmodelo.matrizes_ossos(m,saved.pose(name,t))
        im,*_=render.renderizar(m,vista=(az,5),mats=mat,escala=5,fundo=(238,242,244))
        rgb=np.array(im);ys,xs=np.where(np.any(rgb[:,:,:3]!=[238,242,244],axis=2))
        im=im.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1));im.thumbnail((248,350))
        x=i%3*256;y=i//3*384
        sheet.paste(im,(x+(256-im.width)//2,y+28+(350-im.height)//2))
        d.text((x+5,y+5),f'{name} {t:.2f}s / {az}',fill=(25,40,50))
    sheet.save(OUT/'poses.png')


# Reutiliza escrita e verificações da v3, sempre em uma saída nova.
v3.SOURCE=SOURCE;v3.OUT=OUT;v3.FILE=FILE;v3.CLIPS=CLIPS;v3.Rig=Rig


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--animar',action='store_true')
    ap.add_argument('--validar',action='store_true');ap.add_argument('--previas',action='store_true')
    ap.add_argument('--folha',action='store_true')
    args=ap.parse_args();(OUT/'_cache').mkdir(parents=True,exist_ok=True)
    if args.animar:v3.bake(list(CLIPS))
    if args.validar:v3.validate(list(CLIPS),flourish_sides=('left',),extra_checks=checks)
    if args.previas:v3.previews(list(CLIPS))
    if args.folha:overview()


if __name__=='__main__':main()
