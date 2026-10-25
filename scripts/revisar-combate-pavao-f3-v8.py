"""Confere apoio, preensão, penas, máscaras e conexões do pacote F3 v8."""
import copy
import math

import numpy as np


def preview_reader(v,m):
    saved=v.v2.review.Saved(m);source=v.v2.review.Saved(v.bbmodelo.ler(v.SOURCE))
    class Reader:
        def pose(self,name,t):
            p=saved.pose(name,t)
            if name.endswith('upper'):
                d=v.ENTER if name.startswith('combat_enter') else v.EXIT
                base=source.pose('walk',(v.phase(t,d,name.startswith('combat_exit'))%1)*1.5)
                base.update(p);return base
            return p
    return Reader()


def state(v,name,t,side):
    if name.startswith('combat_enter'):return 'hand' if t>=v.v2.GRASP[side] else 'tail'
    if name.startswith('combat_exit'):return 'tail' if t>v.dock_time(side) else 'hand'
    if name=='combat_idle':
        if t>=v.REST_EXIT:return state(v,'combat_exit',t-v.REST_EXIT,side)
        if side=='left':return 'hand'
        return 'ground' if .95<t<v.REST_END+.30 else 'hand'
    if name=='combat_idle_resume' and side=='right':return 'ground' if t<.30 else 'hand'
    return 'hand'


def buried(v,name,t,side):
    if side!='right':return False
    return (name=='combat_idle' and .48<=t<v.REST_EXIT) or name=='combat_idle_resume'


def check(sysmod,names,study=False):
    v=sysmod;g=v.g;R=v.R;point=v.point
    src=v.bbmodelo.ler(v.SOURCE);m=src if study else v.bbmodelo.ler(v.FILE)
    rig=v.new_rig(m);saved=None if study else v.v2.review.Saved(m)
    report={'fonte_sha256':g.sha(v.SOURCE),'clipes':{},'erros':[]};errors=report['erros']
    if not study:
        report['saida_sha256']=g.sha(v.FILE)
        assert {a['name'] for a in m.animacoes}==set(v.APPROVED)|set(v.CLIPS)
        assert len(m.cubos)==len(src.cubos) and set(m.ossos)==set(src.ossos)
        def canonical(a):
            a=copy.deepcopy(a);a['animators']={u:x for u,x in a['animators'].items() if x.get('keyframes')};return a
        for name in v.APPROVED:
            a=next(a for a in src.animacoes if a['name']==name);b=next(a for a in m.animacoes if a['name']==name)
            assert canonical(a)==canonical(b),name
        report['clipes_aprovados_preservados']=v.APPROVED
        assert np.array_equal(np.array(m.textura),np.array(src.textura))
        for c,d in zip(m.cubos,src.cubos):
            assert c.uuid==d.uuid and c.faces==d.faces and c.osso==d.osso
            assert all(np.array_equal(getattr(c,k),getattr(d,k)) for k in ['de','ate','origem','rotacao'])
        assert all(o.pai==src.ossos[n].pai and np.array_equal(o.origem,src.ossos[n].origem) for n,o in m.ossos.items())

    def pose(name,t):
        if name not in v.CLIPS:return rig.saved.pose(name,t)
        p=rig.pose(name,t) if study else saved.pose(name,t)
        if name.endswith('upper'):
            d=v.ENTER if name.startswith('combat_enter') else v.EXIT
            base=rig.saved.pose('walk',(v.phase(t,d,name.startswith('combat_exit'))%1)*1.5)
            base.update(p);return base
        return p

    feet={s:[c for c in m.cubos if c.nome.startswith('toe_'+s) or c.nome=='foot_base_'+s] for s in v.SIDES}
    for name in names:
        length=v.CLIPS[name];floor=1e9;air=-1e9;tip=1e9;grip=0.;dock=0.;anchor=0.;hinge=0.;wrist=0.
        elbows=[];ground=0.;root_error=0.;angle_step=0.;last=None;worst={};min_buried=0.;rate=24 if study else 240
        for t in np.linspace(0,length,round(length*rate)+1):
            t=float(t);p=pose(name,t);mat=rig.mats(p)
            root_error=max(root_error,float(abs(mat['root']-np.eye(4)).max()))
            f=[float(v.v2.review.world_vertices(m,mat,feet[s])[:,1].min()) for s in v.SIDES]
            floor=min(floor,min(f));air=max(air,min(f))
            for n,a in rig.anchors.items():
                # Os endpoints pacíficos aprovados são preservados, inclusive
                # o pequeno movimento original de penas do idle/walk.
                if name.startswith('combat_enter') and t<.15:continue
                if name.startswith('combat_exit') and t>v.EXIT-.15:continue
                if name=='combat_idle' and t>length-.15:continue
                e=float(np.linalg.norm(point(mat[n],a)-point(mat[m.ossos[n].pai],a)))
                anchor=max(anchor,e)
            for side in v.SIDES:
                w=rig.weapons[side];wm=mat[w['name']];wg=point(wm,w['grip'])
                vertices=rig.weaponverts[side]@wm[:3,:3].T+wg;bottom=float(vertices[:,1].min())
                if buried(v,name,t,side):min_buried=min(min_buried,bottom)
                elif bottom<tip:tip=bottom;worst['piso_lamina']=[side,t,bottom]
                st=state(v,name,t,side)
                if st=='hand':
                    e=float(np.linalg.norm(point(mat['hand_'+side],rig.grips[side])-wg))
                    if e>grip:grip=e;worst['mao']=[side,t,e]
                elif st=='tail':
                    e=float(np.linalg.norm(point(mat['tail_1'],w['grip'])-wg))
                    if e>dock:dock=e;worst['cauda']=[side,t,e]
                else:
                    ground=max(ground,float(np.linalg.norm(wg-rig.plant_grip)))
                    ground=max(ground,float(abs(wm[:3,:3]-rig.plant_rot).max()))
                axis=rig.hinges[side][2]
                # Endpoints idênticos aos ciclos pacíficos já aprovados podem
                # conter sua discreta rotação original em X. O gesto novo usa
                # exclusivamente a dobradiça anatômica em todas as amostras internas.
                if 1e-8<t<length-1e-8:
                    e=float(np.linalg.norm(R(p['forearm_'+side]['rotacao'])@axis-axis))
                    if e>hinge:hinge=e;worst['eixo']=[side,t,e]
                u=g.unit(rig.hinges[side][1]);a=mat['forearm_'+side][:3,:3]@u;b=mat['hand_'+side][:3,:3]@u
                e=math.degrees(math.acos(np.clip(a@b,-1,1)))
                if e>wrist:wrist=e;worst['punho']=[side,t,e]
                a,b,_,_=rig.hinges[side]
                angle=math.degrees(math.acos(np.clip(g.unit(mat['arm_'+side][:3,:3]@a)@g.unit(mat['forearm_'+side][:3,:3]@b),-1,1)))
                elbows.append(angle)
            if last is not None:
                for n in ['hand_left','hand_right','tail_fan_04','tail_fan_06']:
                    delta=last[n][:3,:3].T@mat[n][:3,:3]
                    e=math.degrees(math.acos(np.clip((np.trace(delta)-1)/2,-1,1)))
                    if e>angle_step:angle_step=e;worst['salto']=[n,t,e]
            last=mat
        data={'min_sola_y':floor,'ambos_pes_fora':air,'min_lamina_sem_enterrar_y':tip,
              'profundidade_intencional':-min_buried,'erro_mao_arma':grip,'erro_cauda_arma':dock,
              'erro_arma_solta':ground,'erro_ancoras':anchor,'erro_eixo_cotovelo':hinge,
              'erro_raiz':root_error,
              'flexao_cotovelo':[min(elbows),max(elbows)],'punho_max':wrist,
              'maior_passo_angular':angle_step,'piores_amostras':worst}
        report['clipes'][name]=data
        checks=[(floor<-.04,'pé sob o chão'),(air>.07,'ambos pés sem apoio'),(tip<-.04,'lâmina sob o chão'),
                (grip>.03,'preensão'),(dock>.03,'encaixe na cauda'),(ground>.03,'arma solta moveu'),
                (anchor>.015,'raiz da pena'),(hinge>.004,'eixo do cotovelo'),
                (root_error>1e-5,'raiz deslocada'),
                (min(elbows)<5 or max(elbows)>150,'limite do cotovelo'),(wrist>80,'dobra do punho'),
                (not study and angle_step>15,'salto de orientação')]
        errors.extend(name+': '+msg for failed,msg in checks if failed)
        print(name+': '+('OK' if not any(a for a,_ in checks) else ', '.join(msg for failed,msg in checks if failed)),flush=True)
    pairs=[('combat_walk_start',0,'combat_ready',0),('combat_walk_start',v.TRANSITION,'combat_walk',v.TRANSITION/2),
           ('combat_walk_stop',0,'combat_walk',0),('combat_walk_stop',v.TRANSITION,'combat_ready',0),
           ('combat_enter_walk',0,'walk',0),('combat_enter_walk',v.ENTER,'combat_walk',(v.phase(v.ENTER,v.ENTER)%1)*1.8),
           ('combat_exit',0,'combat_walk',0),('combat_exit',v.EXIT,'walk',(v.phase(v.EXIT,v.EXIT,True)%1)*1.5),
           ('combat_idle',0,'combat_ready',0),('combat_idle',v.CLIPS['combat_idle'],'idle',0),
           ('combat_idle',v.REST_END,'combat_idle_resume',0),('combat_idle_resume',v.RESUME,'combat_ready',0)]
    report['conexoes']=[]
    for a,ta,b,tb in pairs:
        if a not in names:continue
        ma=rig.mats(pose(a,ta));mb=rig.mats(pose(b,tb))
        e=max(float(abs(ma[n]-mb[n]).max()) for n in ma)
        report['conexoes'].append({'de':a,'para':b,'erro':e})
        if e>.001:errors.append(a+'/'+b+': conexão')
    if not study:
        report['mascaras']={}
        for name in ['combat_enter_upper','combat_exit_upper']:
            if name not in names:continue
            bones=set(saved.channels[name]);assert bones==set(rig.upper_bones)
            report['mascaras'][name]=sorted(bones)
    report['alcance_excedido']=rig.max_unreachable
    report['integridade_ok']=not errors
    g.dump(v.OUT/('_cache/estudo.json' if study else 'validacao.json'),report)
    print('Resultado:',json_summary(report),flush=True)
    if errors:raise SystemExit(1)


def json_summary(report):
    import json
    return json.dumps({'ok':report['integridade_ok'],'erros':report['erros'],'alcance':report['alcance_excedido']},ensure_ascii=False)
