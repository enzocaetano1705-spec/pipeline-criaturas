"""Valida poses salvas, dobradiças, soltura da espada, arrasto e sobreposição."""
import argparse
import copy
import importlib.util
import json
import math
from pathlib import Path
import numpy as np
from criaturas import bbmodelo,motor

ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('combate_f3_v2',ROOT/'scripts/animar-combate-pavao-f3-v2.py')
v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
OUT=v.OUT


def vertices(m,mats,parts):
    return np.concatenate([bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mats),bbmodelo.cantos(c)) for c in parts])


def state(name,t,side):
    if name in ['idle','walk']:return 'tail'
    if name.startswith('combat_enter'):return 'hand' if t>=v.GRASP[side] else 'tail'
    if name.startswith('combat_exit'):return 'hand' if t<=v.DOCK[side] else 'tail'
    if name=='combat_idle':
        dock=4.8+2.2*v.DOCK[side]/1.5
        if t>dock:return 'tail'
        if side=='right' and .78<t<4.4:return 'ground'
        return 'hand'
    if name=='combat_idle_resume' and side=='right' and t<.25:return 'ground'
    return 'hand'


def verify(m,saved):
    rig=v.Rig(m);orig=rig.orig;old=rig.saved
    errors=[];report={'saida_sha256':v.g.sha(v.FILE),'fonte_sha256':v.g.sha(v.SOURCE),'clipes':{},'erros':errors}
    assert len(m.cubos)==len(orig.cubos)==93
    a={c.uuid:c for c in orig.cubos}
    for c in m.cubos:
        p=a[c.uuid]
        assert all(np.array_equal(getattr(c,f),getattr(p,f)) for f in ['de','ate','origem','rotacao']),c.nome
        assert c.faces==p.faces and c.osso==p.osso,c.nome
    assert np.array_equal(np.array(m.textura),np.array(orig.textura))
    report['geometria_e_textura_preservadas']=True
    feet={s:[c for c in m.cubos if c.nome.startswith('toe_'+s) or c.nome=='foot_base_'+s] for s in ['left','right']}
    weapons={s:[c for c in m.cubos if c.osso==rig.weapons[s]['name']] for s in ['left','right']}
    allclips={'idle':3.2,'walk':1.5,**v.CLIPS}
    for name,length in allclips.items():
        if name.endswith('upper'):continue
        floor=1e9;grip_error=0;tail_error=0;drag=[1e9,-1e9];release=1e9;depth=[];hinge_error=0;flex=[1e9,-1e9];weapon_floor=1e9
        rate=480 if name=='combat_enter_walk' else 240
        for t in np.linspace(0,length,round(length*rate)+1):
            p=saved.pose(name,float(t));mats=bbmodelo.matrizes_ossos(m,p)
            floor=min(floor,min(vertices(m,mats,feet[s])[:,1].min() for s in feet))
            assert abs(mats['root']-np.eye(4)).max()<1e-7
            for side in ['left','right']:
                w=rig.weapons[side];actual=v.point(mats[w['name']],w['grip']);where=state(name,float(t),side)
                hand=v.point(mats['hand_'+side],rig.grips[side]);gap=float(np.linalg.norm(hand-actual))
                if name not in ['combat_idle','combat_idle_resume']:
                    weapon_floor=min(weapon_floor,float(vertices(m,mats,weapons[side])[:,1].min()))
                if where=='hand':grip_error=max(grip_error,gap)
                if where=='tail':tail_error=max(tail_error,float(np.linalg.norm(v.point(mats['tail_1'],w['grip'])-actual)))
                if name=='combat_idle' and 1.1<=t<=4.1 and side=='right':
                    release=min(release,gap);depth.append(float(-vertices(m,mats,weapons[side])[:,1].min()/w['length']))
                if name=='combat_walk' and side=='right':
                    value=float(vertices(m,mats,weapons[side])[:,1].min());drag=[min(drag[0],value),max(drag[1],value)]
                handoff=(name=='combat_enter_walk' and t<.10) or (name=='combat_exit' and t>=1.38)
                if name not in ['idle','walk'] and not handoff:
                    axis=rig.hinges[side][2];rot=v.R(p['forearm_'+side]['rotacao'])
                    hinge_error=max(hinge_error,float(np.linalg.norm(rot@axis-axis)))
                    sine=np.dot(axis,[rot[2,1]-rot[1,2],rot[0,2]-rot[2,0],rot[1,0]-rot[0,1]])/2
                    angle=rig.hinges[side][3]+math.degrees(math.atan2(sine,(np.trace(rot)-1)/2))
                    flex=[min(flex[0],angle),max(flex[1],angle)]
        r={'min_sola_y':float(floor),'erro_mao_arma':grip_error,'erro_cauda':tail_error,'erro_eixo_cotovelo':hinge_error,
           'flexao_cotovelo':flex if name not in ['idle','walk'] else None}
        if name not in ['combat_idle','combat_idle_resume']:r['min_lamina_y']=weapon_floor
        if name=='combat_walk':r['ponta_arrastando']=drag
        if name=='combat_idle':r.update(distancia_mao_espada_solta=release,fracao_enterrada=[min(depth),max(depth)])
        if floor<-.035:errors.append(f'{name}: piso {floor:.4f}')
        if name not in ['combat_idle','combat_idle_resume'] and weapon_floor<-.04:errors.append(f'{name}: lâmina no piso {weapon_floor:.4f}')
        if grip_error>.12:errors.append(f'{name}: mão/arma {grip_error:.4f}')
        # Menos de 0,04 unidade: 4% de um texel, inclusive entre chaves de 120 Hz.
        if tail_error>.04:errors.append(f'{name}: encaixe cauda {tail_error:.4f}')
        if hinge_error>.001 or (name not in ['idle','walk'] and (flex[0]<5 or flex[1]>150)):errors.append(f'{name}: dobradiça')
        if name=='combat_walk' and max(abs(x) for x in drag)>.035:errors.append('combat_walk: arrasto fora do chão')
        if name=='combat_idle' and (release<2 or not .35<min(depth)<=max(depth)<.65):errors.append('combat_idle: soltura/profundidade')
        report['clipes'][name]=r
    # A geometria aprovada permanece no mesmo lugar mesmo com o vínculo novo.
    preservation={}
    for name,d in [('idle',3.2),('walk',1.5)]:
        err=0
        for t in np.linspace(0,d,round(d*240)+1):
            aa=bbmodelo.matrizes_ossos(orig,old.pose(name,float(t)));bb=bbmodelo.matrizes_ossos(m,saved.pose(name,float(t)))
            for n in m.ossos:err=max(err,float(abs(aa[n]-bb[n]).max()))
        preservation[name]=err
        if err>.025:errors.append(f'{name}: alteração das poses aprovadas {err}')
    report['preservacao_aprovados_matriz']=preservation
    phase_enter=1.3/1.5+(1/1.8-1/1.5)*1.3/2
    phase_exit=1.5/1.8+(1/1.5-1/1.8)*1.5/2
    pairs=[('idle',0,'combat_enter',0),('walk',0,'combat_enter_walk',0),('combat_enter',1.3,'combat_ready',0),
           ('combat_enter_walk',1.3,'combat_walk',phase_enter*1.8),('combat_walk',0,'combat_exit',0),
           ('combat_exit',1.5,'walk',phase_exit*1.5),('combat_ready',0,'combat_idle',0),('combat_idle',7,'idle',0),
           ('combat_ready',0,'combat_walk_start',0),('combat_walk_start',.6,'combat_walk',0),
           ('combat_walk',0,'combat_walk_stop',0),('combat_walk_stop',.6,'combat_ready',0),
           ('combat_idle',1.1,'combat_idle_resume',0),('combat_idle_resume',1,'combat_ready',0)]
    report['conexoes']=[]
    for a,ta,b,tb in pairs:
        aa=bbmodelo.matrizes_ossos(m,saved.pose(a,ta));bb=bbmodelo.matrizes_ossos(m,saved.pose(b,tb))
        err=max(float(abs(aa[n]-bb[n]).max()) for n in aa)
        report['conexoes'].append({'de':a,'para':b,'erro_matriz':err})
        if err>.015:errors.append(f'Conexão {a}/{b}: {err:.4f}')
    # Camadas sem canais de pernas, raiz ou bacia. Aplicação em fases distintas.
    report['camadas']={}
    for name in ['combat_enter_upper','combat_exit_upper']:
        assert set(saved.channels[name])==set(rig.upper)
        held_error=0;dock_error=0;lower_error=0
        for phase in np.linspace(0,1,13)[:-1]:
            lower=rig.peaceful(float(phase)*1.5,True)
            for t in np.linspace(0,v.CLIPS[name],81):
                p=copy.deepcopy(lower);p.update(saved.pose(name,float(t)));mats=bbmodelo.matrizes_ossos(m,p)
                for side in ['left','right']:
                    w=rig.weapons[side];actual=v.point(mats[w['name']],w['grip'])
                    if state(name,t,side)=='hand':held_error=max(held_error,float(np.linalg.norm(v.point(mats['hand_'+side],rig.grips[side])-actual)))
                    else:dock_error=max(dock_error,float(np.linalg.norm(v.point(mats['tail_1'],w['grip'])-actual)))
                for n in ['root','body','pelvis','leg_left','leg_right','shin_left','shin_right','foot_left','foot_right']:
                    assert p[n]==lower[n] if isinstance(p[n],list) else all(np.array_equal(p[n][f],lower[n][f]) for f in p[n])
        report['camadas'][name]={'erro_mao_arma':held_error,'erro_cauda':dock_error,'fases_verificadas':12,'canais_pernas':False}
        if held_error>.12 or dock_error>.04:errors.append(f'{name}: vínculo durante sobreposição')
    report['integridade_ok']=not errors
    v.g.dump(OUT/'validacao.json',report)
    print(json.dumps({'ok':not errors,'erros':errors,'aprovados':preservation},ensure_ascii=False))
    return report


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--validar',action='store_true');ap.add_argument('--previas',nargs='*');args=ap.parse_args()
    m=bbmodelo.ler(v.FILE);saved=v.review.Saved(m)
    if args.validar:
        result=verify(m,saved)
        if not result['integridade_ok']:raise SystemExit(1)
    if args.previas is not None:
        v.review.OUT=OUT;v.review.g.CLIPS={'idle':3.2,'walk':1.5,**v.CLIPS}
        v.review.preview(m,saved,args.previas or [n for n in v.CLIPS if not n.endswith('upper')],fps=20)


if __name__=='__main__':main()
