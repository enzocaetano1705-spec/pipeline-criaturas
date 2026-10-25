"""Revisão restrita à guarda, marcha de combate e saque da F3.

Preserva a geometria manual e todos os clipes adiados. As penas articulam
em sua base real, por compensação local, sem alterar o rig dos outros clipes.
"""
import argparse
import copy
import importlib.util
import json
import math
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from criaturas import bbmodelo, motor, render

ROOT = Path(__file__).resolve().parents[1]
sp = importlib.util.spec_from_file_location('combate_f3_v2', ROOT/'scripts/animar-combate-pavao-f3-v2.py')
v2 = importlib.util.module_from_spec(sp); sp.loader.exec_module(v2)
g = v2.g
OUT = ROOT/'modelos/criatura-pavao/f3/animacoes-v3'
SOURCE = OUT/'origem-revisada.bbmodel'
FILE = OUT/'criatura-pavao-e3-combate-v3.bbmodel'
R, point, unit, smooth, blend, curve = v2.R, v2.point, v2.unit, v2.smooth, v2.blend, v2.curve
CLIPS = {'combat_ready':2.4, 'combat_walk':1.8, 'combat_enter':2.1}
SETTLED=.72
FLOURISH_START=1.15
FLOURISH_END=1.68
OUTWARD_CANT=30


class Rig(v2.Rig):
    def __init__(self, m):
        super().__init__(m)
        self.orig = bbmodelo.ler(SOURCE)
        self.saved = v2.review.Saved(self.orig)
        self.anchors = {}
        for n in ['back_feathers_left', 'back_feathers_right2', 'wing_left', 'wing_right']:
            roots = []
            for c in m.cubos:
                if c.osso != n: continue
                a = (c.de+c.ate)/2; a[2] = c.de[2]
                roots.append(point(bbmodelo.matriz_cubo(m,c,self.rest),a))
            self.anchors[n] = np.mean(roots,axis=0)
        self.wrist_bends = []

    def anchored_wings(self, p):
        for n, anchor in self.anchors.items():
            o = self.m.ossos[n]
            rot = R(p[n]['rotacao'])
            # T(anchor) R T(-anchor), expresso no pivô herdado do modelo.
            p[n]['posicao'] = anchor-o.origem+rot@(o.origem-anchor)

    def base(self, t, c=1, walking=0, phase=0):
        p = super().base(t,c,walking,phase)
        # Todos os movimentos secundários agora conservam a base das penas.
        if hasattr(self,'anchors'): self.anchored_wings(p)
        return p

    def aligned_roll(self,p,side,grip,rot,pref):
        """Escolhe o rolamento da lâmina que exige menos dobra lateral do punho.

        Mantém direção, comprimento e preensão. A rotação axial é livre na
        empunhadura; o cotovelo continua uma dobradiça e permanece para trás.
        """
        for _ in range(3):
            self.natural_arm(p,side,grip,rot@self.bind[side].T,pref,record=False)
            mats = self.mats(p)
            d = rot@self.weapons[side]['frame'][:,1]
            f = mats['forearm_'+side][:3,:3]@unit(self.hinges[side][1])
            h = rot@self.bind[side].T@unit(self.hinges[side][1])
            hp = unit(h-d*(h@d)); fp = unit(f-d*(f@d))
            a = math.degrees(math.atan2(d@np.cross(hp,fp),hp@fp))
            rot = v2.rod(d,a)@rot
        return rot

    def carry(self,p,side,grip,rot,pref):
        rot = self.aligned_roll(p,side,grip,rot,pref)
        self.held(p,side,grip,rot,pref)
        mats = self.mats(p)
        u = unit(self.hinges[side][1])
        f = mats['forearm_'+side][:3,:3]@u
        h = mats['hand_'+side][:3,:3]@u
        self.wrist_bends.append((side,math.degrees(math.acos(np.clip(f@h,-1,1)))))

    def guide_front(self,side,w=1):
        return R([-20*w,0,0])

    def ready_target(self,p,side):
        s=-1 if side=='left' else 1
        sh=point(self.mats(p)['torso'],self.m.ossos['arm_'+side].origem)
        return sh+[s*5.8,-7,-5],self.direction_rotation(side,[s*.16,.986,-.055],[0,0,-1])

    def ready(self,t=0):
        p=self.base(t)
        for side in ['left','right']:
            self.carry(p,side,*self.ready_target(p,side),self.guide_front(side))
        return p

    def drag_target(self,p):
        sh = point(self.mats(p)['torso'],self.m.ossos['arm_right'].origem)
        # Braço pende do ombro, com o cotovelo atrás e a mão junto ao quadril.
        grip = sh+[3.4,-13,2.2]
        horizontal = unit([.40,0,.9165])
        pref = R([-42,0,0])
        low,high = -.95,-.02
        for _ in range(22):
            dy = (low+high)/2
            rot = self.direction_rotation('right',horizontal*math.sqrt(1-dy*dy)+[0,dy,0],[1,0,0])
            rot = self.aligned_roll(p,'right',grip,rot,pref)
            bottom = (self.weaponverts['right']@rot.T+grip)[:,1].min()
            if bottom < 0: low=dy
            else: high=dy
        return grip,rot

    def armed_walk(self,t=0):
        p = self.base(t,1,1,t/1.8)
        self.carry(p,'left',*self.shoulder_target(p),R([-5,0,35]))
        self.carry(p,'right',*self.drag_target(p),R([-42,0,0]))
        return p

    def enter(self,t,moving=False):
        if t>=CLIPS['combat_enter']:return self.ready(0)
        if t<=.50:
            # O usuário aprovou o saque. Conserva ombros, cotovelos e trajetórias.
            p=self.saved.pose('combat_enter',t)
            self.anchored_wings(p)
            return p
        w=smooth((t-.50)/(SETTLED-.50))
        initial=self.saved.pose('combat_enter',.50)
        p=self.mix_pose(initial,self.base(0),w)
        # Impulso e reação pequenos do peito: sem salto nem esticar o esqueleto.
        load=float(curve(t,[(.50,0),(.90,0),(1.15,-.40),(1.40,.45),(1.72,-.25),(2.1,0)]))
        p['body']['posicao']+=np.array([0,load,0])
        p['torso']['rotacao'][0]+=float(curve(t,[(.9,0),(1.15,-1.4),(1.42,1.8),(1.75,-.7),(2.1,0)]))
        p['neck_1']['rotacao'][0]-=float(curve(t,[(.9,0),(1.15,-.8),(1.42,1.0),(1.75,-.4),(2.1,0)]))
        self.legs(p)
        raise_w=smooth((t-.90)/(FLOURISH_START-.90))
        lower_w=smooth((t-FLOURISH_END)/(2.1-FLOURISH_END))
        lift=raise_w*(1-lower_w)
        theta=360*smooth((t-FLOURISH_START)/(FLOURISH_END-FLOURISH_START))
        oldmat=bbmodelo.matrizes_ossos(self.orig,initial)
        for side,s in [('left',-1),('right',1)]:
            grip,guard=self.ready_target(p,side)
            pref=self.guide_front(side)
            guard=self.aligned_roll(p,side,grip,guard,pref)
            if t<SETTLED:
                oldw=oldmat[self.weapons[side]['name']]
                oldgrip=point(oldw,self.weapons[side]['grip'])
                grip=blend(oldgrip,grip,w)
                rot=g.slerp(oldw[:3,:3],guard,w)
                pref=g.slerp(self.reach_pref(side,1),pref,w)
                self.held(p,side,grip,rot,pref)
            else:
                shoulder=point(self.mats(p)['torso'],self.m.ossos['arm_'+side].origem)
                high=shoulder+[s*6.0,12.0,-2.7]
                grip=blend(grip,high,lift)
                cant=math.radians(OUTWARD_CANT)
                start=self.direction_rotation(side,[s*math.sin(cant),math.cos(cant),0],[0,0,-1])
                # Uma volta real de 360° sobre o eixo lateral, com leve cone para
                # fora: a projeção YZ é circular, sem o oito horizontal da v2.
                spinning=v2.rod([1,0,0],theta)@start
                rot=g.slerp(guard,spinning,lift)
                pref=g.slerp(pref,R([10,0,s*110]),lift)
                self.carry(p,side,grip,rot,pref)
        # Mesmo com a reação do corpo, a raiz de cada wing fica na articulação.
        self.anchored_wings(p)
        return p


def inspect_walk():
    m = bbmodelo.ler(SOURCE); rig=Rig(m)
    samples = [('combat_ready',0,0),('combat_ready',0,90),('combat_walk',0,35)]
    sheet=Image.new('RGB',(768,440),(238,242,244));d=ImageDraw.Draw(sheet)
    for i,(name,t,az) in enumerate(samples):
        p=rig.pose(name,t)
        im,*_=render.renderizar(m,vista=(az,5),mats=rig.mats(p),escala=5,fundo=(238,242,244))
        # Recorta o fundo do render para a comparação não perder tamanho útil.
        rgb=np.array(im);mask=np.any(rgb[:,:,:3]!=[238,242,244],axis=2)
        ys,xs=np.where(mask)
        im=im.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1));im.thumbnail((248,395))
        sheet.paste(im,(i*256+(256-im.width)//2,32+(395-im.height)//2))
        d.text((i*256+5,8),f'{name} / {az} graus',fill=(25,40,50))
    sheet.save(OUT/'_cache/marcha-estudo.png')
    print('Estudo da marcha; alcance excedido:',round(rig.max_unreachable,5))


def overview():
    m=bbmodelo.ler(FILE);saved=v2.review.Saved(m)
    samples=[('combat_ready',0,0),('combat_ready',0,90),('combat_walk',.2,65),
             ('combat_enter',.32,35),('combat_enter',1.28,35),('combat_enter',1.49,35)]
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


def prepare():
    if FILE.exists():
        record=OUT/'geracao.json'
        known=json.loads(record.read_text(encoding='utf-8')) if record.exists() else {}
        if known.get('saida_sha256')!=g.sha(FILE):
            raise ValueError('Saída editada fora do gerador: preservar e criar outra versão.')
    shutil.copy2(SOURCE,FILE)
    ops=[{'op':'set_model_properties','name':FILE.stem}]
    g.dump(OUT/'ops-preparo.json',ops);motor.editar(FILE,ops)
    return bbmodelo.ler(FILE)


def bake(names):
    m=prepare();rig=Rig(m);ops=[]
    for name in names:
        length=CLIPS[name];fps=120
        ops.extend([{'op':'remove_animation','animation':name},
            {'op':'add_animation','name':name,'length':length,
             'loop':'once' if name=='combat_enter' else 'loop','snapping':120}])
        times=np.linspace(0,length,round(length*fps)+1)
        poses=[rig.pose(name,float(t)) for t in times]
        if name!='combat_enter':poses[-1]=copy.deepcopy(poses[0])
        for n in m.ossos:
            for ch,field in [('rotation','rotacao'),('position','posicao')]:
                vals=np.array([p[n].get(field,[0,0,0]) for p in poses])
                if ch=='rotation':vals=g.continuous_euler(vals)
                indices=[0,len(times)-1] if np.max(np.ptp(vals,axis=0))<1e-8 else range(len(times))
                for i in indices:
                    ops.append({'op':'set_keyframe','animation':name,'bone':n,
                        'channel':ch,'time':round(float(times[i]),8),
                        'value':np.round(vals[i],7).tolist(),'interpolation':'linear'})
        print('Calculado:',name,flush=True)
    g.dump(OUT/'_cache/ops-animacoes.json',ops);motor.editar(FILE,ops)
    g.dump(OUT/'geracao.json',{'fonte_sha256':g.sha(SOURCE),'saida_sha256':g.sha(FILE),
        'clipes_revistos':names,'operacoes':len(ops),'alcance_excedido':rig.max_unreachable,
        'ancoras_reais':rig.anchors,
        'maior_dobra_punho_nos_clipes_revistos':max((a for _,a in rig.wrist_bends),default=0)})
    print('Gravado:',FILE.name,flush=True)


def validate(names, *, flourish_sides=('left','right'), extra_checks=None):
    m=bbmodelo.ler(FILE);src=bbmodelo.ler(SOURCE);saved=v2.review.Saved(m);rig=Rig(m)
    def canonical(a):
        a=copy.deepcopy(a)
        # O codec remove/adiciona keyframes:[] nos animadores vazios.
        a['animators']={u:v for u,v in a['animators'].items() if v.get('keyframes')}
        return a
    originals={a['name']:a for a in src.animacoes};errors=[]
    report={'fonte_sha256':g.sha(SOURCE),'saida_sha256':g.sha(FILE),'clipes':{},'erros':errors}
    for a in m.animacoes:
        if a['name'] not in names:
            assert canonical(a)==canonical(originals[a['name']]),f'Clipe adiado alterado: {a["name"]}'
    report['clipes_preservados']=[n for n in originals if n not in names]
    assert np.array_equal(np.array(m.textura),np.array(src.textura))
    for c,a in zip(m.cubos,src.cubos):
        assert c.uuid==a.uuid and c.faces==a.faces and c.osso==a.osso
        assert all(np.array_equal(getattr(c,k),getattr(a,k)) for k in ['de','ate','origem','rotacao'])
    assert all(np.array_equal(o.origem,src.ossos[n].origem) and o.pai==src.ossos[n].pai for n,o in m.ossos.items())
    feet={s:[c for c in m.cubos if c.nome.startswith('toe_'+s) or c.nome=='foot_base_'+s] for s in ['left','right']}
    for name in names:
        length=saved.durations[name];anchor_error=grip_error=0.;floor=tip=1e9;air=-1e9;drag_error=0.;wrist_bend=0.;bend_angles=[]
        hinge_error=0.;previous=None;angular_step=0.
        for t in np.linspace(0,length,round(length*240)+1):
            p=saved.pose(name,float(t));mat=bbmodelo.matrizes_ossos(m,p)
            for n,a in rig.anchors.items():
                parent=m.ossos[n].pai
                # No primeiro quadro do saque, mantém a pose aprovada de idle.
                if name=='combat_enter' and t<.15:continue
                anchor_error=max(anchor_error,float(np.linalg.norm(point(mat[n],a)-point(mat[parent],a))))
            floors=[float(v2.review.world_vertices(m,mat,feet[s])[:,1].min()) for s in feet]
            floor=min(floor,min(floors));air=max(air,min(floors))
            for side in ['left','right']:
                w=rig.weapons[side];wm=mat[w['name']];wv=rig.weaponverts[side]@wm[:3,:3].T+point(wm,w['grip'])
                tip=min(tip,float(wv[:,1].min()))
                if name!='combat_enter' or t>=v2.GRASP[side]:
                    err=np.linalg.norm(point(mat['hand_'+side],rig.grips[side])-point(wm,w['grip']))
                    grip_error=max(grip_error,float(err))
                if name=='combat_walk' and side=='right':drag_error=max(drag_error,abs(float(wv[:,1].min())))
                u=unit(rig.hinges[side][1]);f=mat['forearm_'+side][:3,:3]@u;h=mat['hand_'+side][:3,:3]@u
                wrist_bend=max(wrist_bend,math.degrees(math.acos(np.clip(f@h,-1,1))))
                _,_,axis,theta0=rig.hinges[side]
                hinge_error=max(hinge_error,float(np.linalg.norm(R(p['forearm_'+side]['rotacao'])@axis-axis)))
                v1,v2h,_,_=rig.hinges[side]
                elbow=math.degrees(math.acos(np.clip(unit(mat['arm_'+side][:3,:3]@v1)@unit(mat['forearm_'+side][:3,:3]@v2h),-1,1)))
                bend_angles.append(elbow)
            if previous is not None:
                for n in ['hand_left','hand_right','tail_fan_04','tail_fan_06']:
                    delta=previous[n][:3,:3].T@mat[n][:3,:3]
                    angular_step=max(angular_step,math.degrees(math.acos(np.clip((np.trace(delta)-1)/2,-1,1))))
            previous=mat
        seam=0
        if name!='combat_enter':
            a=bbmodelo.matrizes_ossos(m,saved.pose(name,0));b=bbmodelo.matrizes_ossos(m,saved.pose(name,length))
            seam=max(float(abs(a[n]-b[n]).max()) for n in a)
        report['clipes'][name]={'erro_ancora_penas':anchor_error,'erro_mao_arma':grip_error,
            'min_sola_y':floor,'ambos_pes_fora_chao':air,'min_lamina_y':tip,'erro_arrasto':drag_error,
            'costura_matriz':seam,'maior_dobra_punho':wrist_bend,'flexao_cotovelo':[min(bend_angles),max(bend_angles)]}
        report['clipes'][name].update({'erro_eixo_cotovelo':hinge_error,'maior_passo_angular_240hz':angular_step})
        if anchor_error>.01:errors.append(name+': base de pena solta')
        if grip_error>.03:errors.append(name+': empunhadura solta')
        if floor<-.04 or air>.06:errors.append(name+': apoio dos pés')
        if tip<-.04:errors.append(name+': lâmina abaixo do piso')
        if drag_error>.025:errors.append(name+': arrasto fora do piso')
        if seam>1e-5:errors.append(name+': costura do loop')
        if min(bend_angles)<5 or max(bend_angles)>150:errors.append(name+': limite de cotovelo')
        if hinge_error>.004:errors.append(name+': torção fora do eixo do cotovelo')
        if angular_step>15:errors.append(name+': salto de orientação entre amostras')
        if wrist_bend>80:errors.append(name+': dobra excessiva do punho')
    if 'combat_enter' in names:
        report['floreio']={}
        for side in flourish_sides:
            ds=[]
            for t in np.linspace(FLOURISH_START,FLOURISH_END,241):
                mat=bbmodelo.matrizes_ossos(m,saved.pose('combat_enter',float(t)))
                ds.append(mat[rig.weapons[side]['name']][:3,:3]@rig.weapons[side]['frame'][:,1])
            ds=np.array(ds);angles=np.unwrap(np.arctan2(ds[:,2],ds[:,1]))
            turns=math.degrees(angles[-1]-angles[0]);cant=np.degrees(np.arcsin(np.abs(ds[:,0])))
            report['floreio'][side]={'volta_projetada_yz_graus':turns,'inclinacao_para_fora_graus':[float(min(cant)),float(max(cant))]}
            if abs(turns-360)>.05:errors.append('Floreio incompleto: '+side)
        report['conexoes']=[]
        source_saved=v2.review.Saved(src)
        for name,ta,other,tb in [('combat_enter',0,'idle',0),('combat_enter',2.1,'combat_ready',0)]:
            a=bbmodelo.matrizes_ossos(m,saved.pose(name,ta));b=bbmodelo.matrizes_ossos(m,saved.pose(other,tb))
            err=max(float(abs(a[n]-b[n]).max()) for n in a)
            report['conexoes'].append({'de':name,'para':other,'erro_matriz':err})
            if err>1e-4:errors.append('Conexão: '+name+'/'+other)
        preserved=0.
        for t in np.linspace(0,.5,61):
            a=bbmodelo.matrizes_ossos(m,saved.pose('combat_enter',float(t)))
            b=bbmodelo.matrizes_ossos(src,source_saved.pose('combat_enter',float(t)))
            for n in ['arm_left','forearm_left','hand_left','arm_right','forearm_right','hand_right','tail_fan_04','tail_fan_06']:
                preserved=max(preserved,float(abs(a[n]-b[n]).max()))
        report['erro_saque_aprovado_matriz']=preserved
        if preserved>.001:errors.append('Trajetória de saque aprovada alterada')
    if extra_checks:extra_checks(report,m,rig,saved)
    report['integridade_ok']=not errors
    g.dump(OUT/'validacao.json',report)
    print(json.dumps({'integridade_ok':not errors,'erros':errors,'clipes':names},ensure_ascii=False))
    if errors:raise SystemExit(1)


def previews(names):
    m=bbmodelo.ler(FILE);saved=v2.review.Saved(m)
    v2.review.OUT=OUT;v2.review.g.CLIPS=CLIPS
    v2.review.preview(m,saved,names,fps=20,size=640)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--animar',action='store_true');ap.add_argument('--validar',action='store_true')
    ap.add_argument('--folha',action='store_true')
    ap.add_argument('--previas',action='store_true');ap.add_argument('--clipes',nargs='+',default=list(CLIPS),choices=list(CLIPS));args=ap.parse_args()
    (OUT/'_cache').mkdir(exist_ok=True)
    if args.animar:bake(args.clipes)
    if args.validar:validate(args.clipes)
    if args.previas:previews(args.clipes)
    if args.folha:overview()
    if not (args.animar or args.validar or args.previas or args.folha):inspect_walk()
