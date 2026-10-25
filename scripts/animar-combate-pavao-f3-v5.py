"""F3: respiração pesada e arco contínuo do saque à extensão do braço.

Reutiliza a base aprovada da v4. Só modifica combat_ready e o intervalo
0,40–1,15 s do braço do ombro em combat_enter; o restante é preservado.
"""
import argparse
import copy
import importlib.util
import math
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('combate_f3_v4',ROOT/'scripts/animar-combate-pavao-f3-v4.py')
v4=importlib.util.module_from_spec(sp);sp.loader.exec_module(v4)
v3=v4.v3;g=v4.g;v2=v4.v2
R,point,unit,smooth,blend=v4.R,v4.point,v4.unit,v4.smooth,v4.blend
SOURCE=v4.FILE
OUT=ROOT/'modelos/criatura-pavao/f3/animacoes-v5'
FILE=OUT/'criatura-pavao-e3-combate-v5.bbmodel'
CLIPS={'combat_ready':2.4,'combat_enter':2.1}
FLOW_START=.40;FLOW_GUIDE=.56;FLOW_END=1.15


def logrot(r):
    a=math.acos(float(np.clip((np.trace(r)-1)/2,-1,1)))
    if a<1e-9:return np.zeros(3)
    return np.array([r[2,1]-r[1,2],r[0,2]-r[2,0],r[1,0]-r[0,1]])*a/(2*math.sin(a))


def exprot(v):
    a=float(np.linalg.norm(v))
    return np.eye(3) if a<1e-10 else v2.rod(v/a,math.degrees(a))


def rotation_controls(a,b,va,vb,d):
    return [a,a@exprot(va*d/3),b@exprot(-vb*d/3),b]


def rotation_bezier(ctrl,u):
    points=[r.copy() for r in ctrl]
    while len(points)>1:points=[g.slerp(a,b,u) for a,b in zip(points,points[1:])]
    return points[0]


def hermite(a,b,va,vb,u,d):
    return (2*u**3-3*u*u+1)*a+(u**3-2*u*u+u)*d*va+(-2*u**3+3*u*u)*b+(u**3-u*u)*d*vb


class Rig(v4.Rig):
    def __init__(self,m):
        super().__init__(m)
        self.drag_cache={};self.root_evaluations=[]
        self.endpoints=[]
        for t in [FLOW_START,FLOW_END]:
            p=self.saved.pose('combat_enter',t);mat=self.mats(p);h=.0001
            before=self.mats(self.saved.pose('combat_enter',t-h));after=self.mats(self.saved.pose('combat_enter',t+h))
            n='tail_fan_04';w=self.weapons['left'];grip=point(mat[n],w['grip'])
            vel=(point(after[n],w['grip'])-point(before[n],w['grip']))/(2*h)
            omega=logrot(before[n][:3,:3].T@after[n][:3,:3])/(2*h)
            armomega=logrot(R(self.saved.pose('combat_enter',t-h)['arm_left']['rotacao']).T@R(self.saved.pose('combat_enter',t+h)['arm_left']['rotacao']))/(2*h)
            self.endpoints.append((grip,vel,mat[n][:3,:3],omega,R(p['arm_left']['rotacao']),armomega))
        a,b=self.endpoints
        guide=np.array([-15.,39.,-11.]);guidevel=np.array([0.,25.,0.])
        pref=g.slerp(a[4],b[4],.48)
        rot=g.slerp(a[2],b[2],.55)
        rot=self.aligned_roll(self.saved.pose('combat_enter',FLOW_GUIDE),'left',guide,rot,pref)
        middle_omega=logrot(rot.T@b[2])*1.2/(FLOW_END-FLOW_GUIDE)
        middle_arm=logrot(pref.T@b[4])*1.2/(FLOW_END-FLOW_GUIDE)
        self.path=[(a[0],guide,a[1],guidevel,FLOW_GUIDE-FLOW_START),
                   (guide,b[0],guidevel,b[1],FLOW_END-FLOW_GUIDE)]
        self.rotations=[rotation_controls(a[2],rot,a[3],middle_omega,self.path[0][4]),
                        rotation_controls(rot,b[2],middle_omega,b[3],self.path[1][4])]
        self.preferences=[rotation_controls(a[4],pref,a[5],middle_arm,self.path[0][4]),
                          rotation_controls(pref,b[4],middle_arm,b[5],self.path[1][4])]

    def drag_target(self,p):
        # Mesmo alvo geométrico da v3/v4, com raiz numérica salvaguardada.
        # Evita 22 bisseções completas de IK em cada quadro da respiração.
        torso=self.mats(p)['torso'];key=tuple(np.round(torso.ravel(),11))
        if key in self.drag_cache:return tuple(v.copy() for v in self.drag_cache[key])
        sh=point(torso,self.m.ossos['arm_right'].origem);grip=sh+[3.4,-13,2.2]
        horizontal=unit([.40,0,.9165]);pref=R([-42,0,0]);count=0
        def evaluate(dy):
            nonlocal count
            count+=1
            rot=self.direction_rotation('right',horizontal*math.sqrt(1-dy*dy)+[0,dy,0],[1,0,0])
            rot=self.aligned_roll(p,'right',grip,rot,pref)
            return float((self.weaponverts['right']@rot.T+grip)[:,1].min()),rot
        lo,hi=-.95,-.02;flo,_=evaluate(lo);fhi,_=evaluate(hi)
        assert flo<0<fhi
        for i in range(24):
            dy=(lo*fhi-hi*flo)/(fhi-flo)
            if not lo<dy<hi or (i%5==4):dy=(lo+hi)/2
            f,rot=evaluate(dy)
            if abs(f)<1e-7:break
            if f<0:lo,flo=dy,f
            else:hi,fhi=dy,f
        assert abs(f)<1e-5,('Ponta não convergiu ao piso',f)
        self.root_evaluations.append(count)
        self.drag_cache[key]=(grip.copy(),rot.copy())
        return grip,rot

    def ready(self,t=0):
        if abs(t%2.4)<1e-10:return copy.deepcopy(self.walk_still)
        p=copy.deepcopy(self.walk_still);a=2*math.pi*t/2.4;b=math.sin(a)
        lag=math.sin(a-.25)+math.sin(.25)
        p['body']['posicao']+=np.array([0,.50*b,.20*b])
        p['body']['rotacao'][0]+=.35*b
        p['waist']['rotacao'][0]+=.9*b
        p['torso']['rotacao'][0]-=2.8*b
        p['neck_1']['rotacao'][0]+=1.6*lag
        p['tail_1']['rotacao'][0]+=1.4*lag
        p['tail_2']['rotacao'][0]+=.55*lag
        for n in self.anchors:p[n]['rotacao'][0]+=(1.1 if n.startswith('wing_') else .85)*lag
        reference=self.mats(self.walk_still)['head'][:3,:3]
        self.set_world(p,'head',R([-.7*b,.25*b,.15*b])@reference)
        self.legs(p,self.ready_feet)
        self.carry(p,'left',*self.shoulder_target(p),R([-5,0,35]))
        self.carry(p,'right',*self.drag_target(p),R([-42,0,0]))
        self.anchored_wings(p)
        return p

    def enter(self,t,moving=False):
        p=self.saved.pose('combat_enter',float(np.clip(t,0,2.1)))
        if t<=FLOW_START or t>=FLOW_END:return p
        i=0 if t<FLOW_GUIDE else 1;start=FLOW_START if i==0 else FLOW_GUIDE
        u=(t-start)/self.path[i][4];a,b,va,vb,d=self.path[i]
        grip=hermite(a,b,va,vb,u,d)
        rot=rotation_bezier(self.rotations[i],u)
        pref=rotation_bezier(self.preferences[i],u)
        self.held(p,'left',grip,rot,pref)
        self.anchored_wings(p)
        return p


def checks(report,m,rig,saved):
    v4.checks(report,m,rig,saved)
    original=v2.review.Saved(v3.bbmodelo.ler(SOURCE));error=0.
    for t in np.linspace(FLOW_END,2.1,229):
        a=rig.mats(saved.pose('combat_enter',float(t)));b=rig.mats(original.pose('combat_enter',float(t)))
        error=max(error,max(float(abs(a[n]-b[n]).max()) for n in a))
    report['erro_trecho_aprovado_apos_extensao']=error
    if error>.001:report['erros'].append('Trecho aprovado após a extensão mudou')
    speeds=[];ys=[]
    for t in np.linspace(FLOW_START+.01,FLOW_END-.05,169):
        positions=[]
        for u in [t-.001,t+.001]:
            mat=rig.mats(saved.pose('combat_enter',float(u)))
            positions.append(point(mat['hand_left'],rig.grips['left']))
        v=(positions[1]-positions[0])/.002;speeds.append(float(np.linalg.norm(v)));ys.append(float(v[1]))
    report['arco_continuo']={'menor_velocidade_mao':min(speeds),'menor_velocidade_vertical':min(ys)}
    if min(speeds)<1 or min(ys)<-.15:report['erros'].append('Pausa ou recuo no novo arco')
    body=[];torso=[]
    for t in np.linspace(0,2.4,241):
        p=saved.pose('combat_ready',float(t));body.append(p['body']['posicao'][1]);torso.append(p['torso']['rotacao'][0])
    report['respiracao']={'amplitude_vertical_corpo':float(np.ptp(body)),'amplitude_inclinacao_peito':float(np.ptp(torso))}


v4.SOURCE=SOURCE;v3.SOURCE=SOURCE;v3.OUT=OUT;v3.FILE=FILE;v3.CLIPS=CLIPS;v3.Rig=Rig


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--animar',action='store_true');ap.add_argument('--validar',action='store_true')
    ap.add_argument('--previas',action='store_true');ap.add_argument('--folha',action='store_true');args=ap.parse_args()
    (OUT/'_cache').mkdir(parents=True,exist_ok=True)
    if args.animar:v3.bake(list(CLIPS))
    if args.validar:v3.validate(list(CLIPS),flourish_sides=('left',),extra_checks=checks,preserve_draw_until=FLOW_START)
    if args.previas:v3.previews(list(CLIPS))
    if args.folha:
        v4.FILE=FILE;v4.OUT=OUT
        v4.overview([('combat_ready',.6,65),('combat_ready',1.8,65),
                     ('combat_enter',.40,35),('combat_enter',.56,35),
                     ('combat_enter',.90,35),('combat_enter',1.15,35)])


if __name__=='__main__':main()
