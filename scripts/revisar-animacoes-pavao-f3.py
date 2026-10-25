"""Confere as chaves efetivamente salvas e produz prévias com câmera fixa."""
import argparse
import copy
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from criaturas import bbmodelo, exportar, motor, render, texturizar

ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('animador_f3',ROOT/'scripts/animar-pavao-f3.py')
g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g)
OUT=g.OUT


class Saved:
    def __init__(self,m):
        self.m=m;self.channels={};self.durations={};self.names={o.uuid:n for n,o in m.ossos.items()}
        for a in m.animacoes:
            name=a['name'];self.channels[name]={};self.durations[name]=a['length']
            for uid,anim in a['animators'].items():
                if uid not in self.names:continue
                bone=self.names[uid];self.channels[name][bone]={}
                for ch,field in [('rotation','rotacao'),('position','posicao')]:
                    keys=sorted((k for k in anim.get('keyframes',[]) if k['channel']==ch),key=lambda k:k['time'])
                    if keys:
                        ts=np.array([k['time'] for k in keys],float)
                        vals=np.array([[float(k['data_points'][0][v]) for v in 'xyz'] for k in keys])
                        assert np.all(np.isfinite(ts)) and np.all(np.isfinite(vals)),(name,bone,ch)
                        self.channels[name][bone][field]=(ts,vals)

    def pose(self,name,t):
        p={}
        for bone,channels in self.channels[name].items():
            p[bone]={}
            for field,(ts,v) in channels.items():
                p[bone][field]=np.array([np.interp(t,ts,v[:,i]) for i in range(3)])
        return p


def world_vertices(m,mats,parts=None):
    return np.concatenate([bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mats),bbmodelo.cantos(c)) for c in (parts or m.cubos)])


def held(name,t,side):
    if name=='combat_enter':return t>=(.92 if side=='left' else 1.08)
    if name=='combat_exit':return t<=(1.95 if side=='left' else 2.12)
    return name.startswith('combat_')


def check(m,saved):
    rig=g.Rig(m);src=bbmodelo.ler(g.SOURCE);original={c.uuid:c for c in src.cubos}
    errors=[];report={'fonte_sha256':g.sha(g.SOURCE),'saida_sha256':g.sha(g.FILE),'clipes':{},'erros':errors}
    assert len(m.cubos)==len(src.cubos)==93
    geometry=0
    for c in m.cubos:
        a=original[c.uuid]
        geometry=max(geometry,float(max(abs(c.de-a.de).max(),abs(c.ate-a.ate).max(),abs(c.origem-a.origem).max(),abs(c.rotacao-a.rotacao).max())))
        if c.nome!='neck_lower_avian':assert c.faces==a.faces,c.nome
    report['erro_geometria_manual']=geometry
    assert geometry<1e-6
    texture=np.array(m.textura);oldtex=np.array(src.textura);diff=np.any(texture!=oldtex,axis=2)
    report['pixels_repintados']=int(diff.sum());report['uv_fora']=exportar.uv_fora_do_atlas(m)
    affected=[]
    for c in m.cubos:
        if c.nome=='neck_lower_avian':continue
        for face in c.faces:
            rows=texturizar.texels_da_face(c,face,np.eye(4))
            if rows is None:continue
            uv=np.asarray(rows[0],int)
            if len(uv) and diff[uv[:,1],uv[:,0]].any():affected.append(c.nome+'.'+face)
    report['pintura_atingiu_outras_partes']=affected
    report['cores_pescoco']={}
    neck=m.cubo('neck_lower_avian')
    for f in neck.faces:
        uv=np.asarray(texturizar.texels_da_face(neck,f,np.eye(4))[0],int)
        pixels=texture[uv[:,1],uv[:,0]]
        report['cores_pescoco'][f]=len(np.unique(pixels[:,:3],axis=0))
        assert np.all(pixels[:,3]==255)
    feet={side:[c for c in m.cubos if c.nome.startswith('toe_'+side) or c.nome=='foot_base_'+side] for side in ['left','right']}
    for name,length in g.CLIPS.items():
        assert name in saved.channels
        for a in next(a for a in m.animacoes if a['name']==name)['animators'].values():
            assert all(k['channel']!='scale' for k in a.get('keyframes',[]))
        floor=1e9;air=0;grip_error=0;dock_error=0;root_error=0;body_motion=[]
        tipmin=1e9;max_speed=0;last=None;max_hand_error_t=None
        rate=240 if name=='combat_enter' else 120
        for t in np.linspace(0,length,round(length*rate)+1):
            p=saved.pose(name,float(t));mats=bbmodelo.matrizes_ossos(m,p)
            floors=[float(world_vertices(m,mats,feet[side])[:,1].min()) for side in feet]
            floor=min(floor,min(floors));air=max(air,min(floors))
            root_error=max(root_error,float(abs(mats['root']-np.eye(4)).max()))
            body_motion.append(g.point(mats['torso'],m.ossos['head'].origem))
            for side in ['left','right']:
                w=rig.weapons[side];grip=g.point(mats[w['name']],w['grip'])
                if held(name,t,side):
                    hand=g.point(mats['hand_'+side],rig.grips[side]);err=float(np.linalg.norm(hand-grip))
                    if err>grip_error:grip_error=err;max_hand_error_t=float(t)
                else:
                    expected=g.point(mats['tail_1'],w['grip'])
                    dock_error=max(dock_error,float(np.linalg.norm(expected-grip)))
            c=m.cubo('tail_fan_06_plane_point');tipmin=min(tipmin,float(world_vertices(m,mats,[c])[:,1].min()))
            # Velocidade das peças entre subamostras: identifica estouros/teleportes.
            v=np.concatenate([g.point(mats[n],m.ossos[n].origem) for n in m.ossos])
            if last is not None:max_speed=max(max_speed,float(abs(v-last).max()*rate))
            last=v
        seam=0;velocity_seam=0
        if name in g.LOOPS:
            p0,p1=saved.pose(name,0),saved.pose(name,length)
            a,b=bbmodelo.matrizes_ossos(m,p0),bbmodelo.matrizes_ossos(m,p1)
            seam=max(float(abs(a[n]-b[n]).max()) for n in a)
            dt=1/120
            before=bbmodelo.matrizes_ossos(m,saved.pose(name,length-dt));after=bbmodelo.matrizes_ossos(m,saved.pose(name,dt))
            velocity_seam=max(float(abs((after[n]-a[n])-(b[n]-before[n])).max()/dt) for n in a)
        result={'min_sola_y':floor,'max_ambos_pes_fora_solo':air,'erro_mao_arma':grip_error,
                'tempo_erro_mao':max_hand_error_t,'erro_arma_embainhada':dock_error,
                'raiz_erro':root_error,'costura_pose':seam,'costura_velocidade_matriz':velocity_seam,
                'amplitude_corpo':np.ptp(body_motion,axis=0),'min_ponta_espada_direita':tipmin,'velocidade_pivo_max':max_speed}
        report['clipes'][name]=result
        if floor<-.04:errors.append(f'{name}: sola abaixo do piso {floor:.4f}')
        if air>.05:errors.append(f'{name}: ambos os pés sem apoio {air:.4f}')
        if grip_error>.10:errors.append(f'{name}: arma distante da mão {grip_error:.4f}')
        if dock_error>.025:errors.append(f'{name}: arma descolada da cauda {dock_error:.4f}')
        if seam>1e-5 or root_error>1e-5:errors.append(f'{name}: costura/raiz')
    pairs=[('idle',0,'combat_enter',0),('combat_enter',3.4,'combat_idle',0),
           ('combat_idle',0,'combat_exit',0),('combat_exit',2.8,'idle',0),
           ('combat_idle',0,'combat_walk_start',0),('combat_walk_start',.8,'combat_walk',0),
           ('combat_walk',0,'combat_walk_stop',0),('combat_walk_stop',.8,'combat_idle',0)]
    report['transicoes']=[]
    for a,ta,b,tb in pairs:
        ma=bbmodelo.matrizes_ossos(m,saved.pose(a,ta));mb=bbmodelo.matrizes_ossos(m,saved.pose(b,tb))
        err=max(float(abs(ma[n]-mb[n]).max()) for n in ma)
        report['transicoes'].append({'de':a,'para':b,'erro_matriz':err})
        if err>1e-5:errors.append(f'Conexão {a}/{b}: {err}')
    if affected or report['uv_fora']:errors.append('UV/pintura fora do alvo')
    report['integridade_ok']=not errors
    report['limites']=['Validação local das poses e chaves; ainda requer avaliação artística.',
        'Ponta da espada direita atravessa o plano de chão intencionalmente no descanso.',
        'Clipes de começar/parar walk usam a fase zero; integração futura deve respeitar fase/mistura.',
        'Não valida gameplay, dano, colisões no motor ou um esqueleto biológico real.']
    g.dump(OUT/'validacao.json',report)
    print(json.dumps({'integridade_ok':report['integridade_ok'],'erros':errors,'geometria':geometry,'pixels':report['pixels_repintados']},ensure_ascii=False))
    return report


def preview(m,saved,names,fps=18,size=640):
    for name in names:
        length=g.CLIPS[name];times=np.arange(0,length-1e-5,1/fps)
        poses=[bbmodelo.matrizes_ossos(m,saved.pose(name,float(t))) for t in times]
        limits=[bbmodelo.limites(m,mat) for mat in poses];lo=np.min([a for a,b in limits],0);hi=np.max([b for a,b in limits],0)
        # Cria um piso apenas no render; nunca grava geometria auxiliar no modelo.
        model=copy.copy(m);model.cubos=m.cubos+[bbmodelo.Cubo('_piso','preview_floor',None,
            np.array([-200,-3,-200]),np.array([200,0,200]),np.zeros(3),np.zeros(3),0,{})]
        f,r,u=render.camera(35,12)
        corners=np.array([[x,y,z] for x in [lo[0],hi[0]] for y in [lo[1],hi[1]] for z in [lo[2],hi[2]]])
        scale=min((size-35)/np.ptp(corners@r),(size-55)/np.ptp(corners@u))
        frames=[];projection=None
        for t,mat in zip(times,poses):
            im,_,_,projection=render.renderizar(model,vista=(35,12),mats=mat,escala=scale,
                limites=(lo,hi),projecao=projection,fundo=(238,242,244),cores={'_piso':'#dce3e6'},sombreado=.2)
            draw=ImageDraw.Draw(im);draw.text((8,6),f'{name}  {t:.2f}s',fill=(35,45,55))
            frames.append(im)
        frames[0].save(OUT/(name+'.gif'),save_all=True,append_images=frames[1:],duration=round(1000/fps),loop=0)
        print(f'Prévia: {name} ({len(frames)} quadros)')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--validar',action='store_true');ap.add_argument('--previas',nargs='*');args=ap.parse_args()
    m=bbmodelo.ler(g.FILE);saved=Saved(m)
    if args.validar:
        result=check(m,saved)
        if not result['integridade_ok']:raise SystemExit(1)
    if args.previas is not None:preview(m,saved,args.previas or list(g.CLIPS))


if __name__=='__main__':main()
