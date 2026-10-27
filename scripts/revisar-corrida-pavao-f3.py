"""Conferência das corridas F3: apoios, vínculos, fases e arquivo efetivo."""
import copy
import math
from pathlib import Path

import numpy as np
from PIL import Image,ImageDraw


def angle(a,b):
    return math.degrees(math.acos(float(np.clip((np.trace(a.T@b)-1)/2,-1,1))))


def measure(v,m,reader,names,rate=240,offset=0.,rig=None,verbose=True):
    rig=rig or v.Rig(m);report={};errors=[]
    footcubes={s:[c for c in m.cubos if c.nome.startswith('toe_'+s) or c.nome=='foot_base_'+s] for s in v.SIDES}
    for name in names:
        duration=v.CLIPS[name];floor=1e9;tip=1e9;grip=dock=anchor=footerr=root=jointpos=weld=0.
        elbows=[];knees=[];wrists=[];flight=0;stance=0;maxstep=0.;last=None;worst={};body=[]
        times=np.linspace(0,duration,round(duration*rate)+1)
        if offset:times=np.unique(np.r_[0,times[:-1]+offset,duration])
        for t in times:
            t=float(t);p=reader.pose(name,t);mat=rig.mats(p);combat=v.mode(name)
            phase,weight=v.timing(name,t);targets,rolls,contact=rig.gait(phase%1,weight,combat)
            allfeet=[]
            for side in v.SIDES:
                verts=v.v2.review.world_vertices(m,mat,footcubes[side]);y=float(verts[:,1].min())
                floor=min(floor,y);allfeet.append(y)
                center=v.point(mat['foot_'+side],rig.feet[side])
                if name in v.LOOPS or 1e-5<t<duration-1e-5:
                    e=float(np.linalg.norm(center-targets[side]));footerr=max(footerr,e)
                w=rig.weapons[side];wm=mat[w['name']];wg=v.point(wm,w['grip'])
                expected=v.point(mat['hand_'+side],rig.grips[side]) if combat else v.point(mat['tail_1'],w['grip'])
                e=float(np.linalg.norm(wg-expected))
                if combat:grip=max(grip,e)
                else:dock=max(dock,e)
                expected_rot=mat['hand_'+side][:3,:3]@rig.bind[side] if combat else mat['tail_1'][:3,:3]
                points=rig.weaponverts[side]
                weld=max(weld,float(np.linalg.norm(points@wm[:3,:3].T+wg-(points@expected_rot.T+expected),axis=1).max()))
                bottom=float((rig.weaponverts[side]@wm[:3,:3].T+wg)[:,1].min())
                if bottom<tip:tip=bottom;worst['piso_espada']=[side,t,bottom]
                a,b,c=[v.point(mat[n+side],m.ossos[n+side].origem) for n in ['arm_','forearm_','hand_']]
                elbows.append(math.degrees(math.acos(np.clip(v.unit(b-a)@v.unit(c-b),-1,1))))
                a,b,c=[v.point(mat[n+side],m.ossos[n+side].origem) for n in ['leg_','shin_','foot_']]
                knees.append(math.degrees(math.acos(np.clip(v.unit(b-a)@v.unit(c-b),-1,1))))
                u=v.unit(rig.hinges[side][1]);a=mat['forearm_'+side][:3,:3]@u;b=mat['hand_'+side][:3,:3]@u
                wrists.append(math.degrees(math.acos(np.clip(a@b,-1,1))))
            if min(allfeet)>.05:flight+=1
            else:stance+=1
            if name in v.LOOPS:
                for n,a in rig.anchors.items():
                    anchor=max(anchor,float(np.linalg.norm(v.point(mat[n],a)-v.point(mat[m.ossos[n].pai],a))))
            root=max(root,float(abs(mat['root']-np.eye(4)).max()))
            for n in ['body','pelvis','waist','torso','tail_1','tail_2','neck_1','neck_2','head']:
                if n!='body':jointpos=max(jointpos,float(np.linalg.norm(p[n].get('posicao',[0,0,0]))))
            body.append(np.r_[v.point(mat['body'],m.ossos['body'].origem),v.g.forms.euler(mat['torso'][:3,:3]),v.g.forms.euler(mat['head'][:3,:3])])
            if last:
                for n in m.ossos:
                    e=angle(last[n][:3,:3],mat[n][:3,:3]);maxstep=max(maxstep,e)
            last=mat
        spans=np.ptp(body,axis=0)
        data={'min_pes_y':floor,'min_laminas_y':tip,'erro_mao_arma':grip,'erro_cauda_arma':dock,
              'erro_raizes_penas':anchor,'erro_alvo_pes':footerr,'erro_root':root,'translacao_juntas':jointpos,'erro_vinculo_lamina_inteira':weld,
              'cotovelos_graus':[min(elbows),max(elbows)],'joelhos_graus':[min(knees),max(knees)],
              'punho_max_graus':max(wrists),'fracao_aerea':flight/len(times),
              'curso_body_xyz':spans[:3].tolist(),'oscilacao_peito_graus':spans[3:6].tolist(),
              'oscilacao_cabeca_graus':spans[6:].tolist(),'maior_passo_angular':maxstep,'piores_amostras':worst}
        checks=[(floor<-.04,'pé sob o piso'),(tip<-.04,'espada sob o piso'),
                (grip>.035,'preensão'),(dock>.04,'pena fora da cauda'),(anchor>.015,'raiz da pena'),(weld>.12,'lâmina tremendo'),
                (footerr>.06,'alcance/apoio da perna'),(root>1e-6,'root deslocado'),(jointpos>1e-6,'junta deslocada'),
                (min(elbows)<5 or max(elbows)>150,'cotovelo'),(min(knees)<3 or max(knees)>155,'joelho'),
                (max(wrists)>80,'punho'),(rate>=120 and maxstep>14,'salto angular')]
        if name in v.LOOPS:
            checks += [(not .025<data['fracao_aerea']<.27,'fase aérea'),(spans[1]<2.0,'corpo sem impulso'),
                       (spans[3]<5,'peito rígido'),(spans[6]<4,'cabeça rígida')]
        failures=[msg for failed,msg in checks if failed]
        report[name]=data;errors.extend(name+': '+msg for msg in failures)
        if verbose:print(name+': '+(', '.join(failures) if failures else 'OK'),flush=True)
    return {'clipes':report,'erros':errors,'alcance_excedido':rig.max_unreachable,'alcance_por_membro':rig.reach}


def connections(v,m,reader):
    rig=v.Rig(m);rows=[]
    for name,d in v.CLIPS.items():
        combat=v.mode(name)
        if name in v.LOOPS:pairs=[(name,0,name,d)]
        else:
            phase,weight=v.timing(name,d)
            pairs=[(name,0,v.run_name(combat) if name.endswith('stop') else v.walk_name(combat),0),
                   (name,d,v.walk_name(combat) if name.endswith('stop') else v.run_name(combat),
                    phase%1*(v.WALK[combat] if name.endswith('stop') else v.PERIOD[combat]))]
        for a,ta,b,tb in pairs:
            ma=rig.mats(reader.pose(a,ta));mb=rig.mats(reader.pose(b,tb))
            e=max(float(abs(ma[n]-mb[n]).max()) for n in ma)
            rows.append({'de':a,'t':ta,'para':b,'t_destino':tb,'erro_matriz':e});assert e<.001,(a,b,e)
    return rows


def borders(v,m,reader):
    """Compara um quadro antes/depois do encaixe com a continuação da base."""
    rig=v.Rig(m);report={};h=1/60
    for name,d in v.CLIPS.items():
        if name in v.LOOPS:continue
        c=v.mode(name);ph,_=v.timing(name,d);stop=name.endswith('stop')
        pairs=[('inicio',h,v.run_name(c) if stop else v.walk_name(c),h),
               ('fim',d-h,v.walk_name(c) if stop else v.run_name(c),
                (ph%1)*(v.WALK[c] if stop else v.PERIOD[c])-h)]
        row={}
        for label,t,base,tb in pairs:
            a=rig.mats(reader.pose(name,t));b=rig.mats(reader.pose(base,tb))
            distance=max(float(np.linalg.norm(v.point(a[n],m.ossos[n].origem)-v.point(b[n],m.ossos[n].origem))) for n in m.ossos)
            rotation=max(angle(a[n][:3,:3],b[n][:3,:3]) for n in m.ossos)
            row[label]={'desvio_pivo_unidades':distance,'desvio_graus':rotation}
            assert distance<.02 and rotation<.1,(name,label,distance,rotation)
        report[name]=row
    v.g.dump(v.OUT/'continuidade-bordas.json',report)
    return report


def study(v):
    v.OUT.mkdir(parents=True,exist_ok=True);(v.OUT/'_cache').mkdir(exist_ok=True)
    m=v.bbmodelo.ler(v.SOURCE);rig=v.Rig(m)
    result=measure(v,m,rig,list(v.CLIPS),rate=60,rig=rig)
    v.g.dump(v.OUT/'_cache/estudo.json',result)
    print('Alcance:',round(rig.max_unreachable,6),'por membro',rig.reach,flush=True)
    sheet(v,m,rig,v.OUT/'_cache/poses-estudo.png')


def check(v):
    src=v.bbmodelo.ler(v.SOURCE);m=v.bbmodelo.ler(v.FILE)
    for field in ['elements','groups','textures','outliner']:assert src.bruto[field]==m.bruto[field],field
    assert len(m.animacoes)==len(src.animacoes)+len(v.CLIPS)
    def canonical(a):
        a=copy.deepcopy(a)
        a['animators']={u:x for u,x in a['animators'].items() if x.get('keyframes')}
        return a
    for a in src.animacoes:assert canonical(a)==canonical(next(b for b in m.animacoes if b['uuid']==a['uuid'])),a['name']
    for a in m.animacoes:
        for anim in a['animators'].values():
            for k in anim.get('keyframes',[]):
                assert k['channel'] in ['rotation','position']
                assert all('e' not in str(k['data_points'][0][x]).lower() for x in 'xyz')
    saved=v.Saved(m);report={'fonte_sha256':v.g.sha(v.SOURCE),'saida_sha256':v.g.sha(v.FILE),
        'clipes_preservados':[a['name'] for a in src.animacoes],'geometria_rig_textura_preservados':True}
    report['linear']=measure(v,m,saved,list(v.CLIPS));report['conexoes']=connections(v,m,saved)
    report['nativo']=measure(v,m,v.native.NativeSaved(saved),list(v.CLIPS),offset=.00047)
    report['nativo_segunda_fase']=measure(v,m,v.native.NativeSaved(saved),list(v.CLIPS),offset=.00219,verbose=False)
    report['conexoes_nativas']=connections(v,m,v.native.NativeSaved(saved));report['bordas_1_60_s']=borders(v,m,saved)
    report['erros']=report['linear']['erros']+report['nativo']['erros']+report['nativo_segunda_fase']['erros']
    report['ok']=not report['erros']
    v.g.dump(v.OUT/'validacao-corrida.json',report)
    print('Resultado:',report['ok'],report['erros'],flush=True)
    if report['erros']:raise SystemExit(1)


def sheet(v,m,reader,file):
    samples=[('run',0,90),('run',.18,90),('run',.38,35),
             ('combat_run',0,90),('combat_run',.20,90),('combat_run',.44,35)]
    sheet=Image.new('RGB',(768,660),(238,242,244));d=ImageDraw.Draw(sheet)
    for i,(name,t,az) in enumerate(samples):
        mats=v.bbmodelo.matrizes_ossos(m,reader.pose(name,t))
        im,*_=v.render.renderizar(m,vista=(az,5),mats=mats,escala=5,fundo=(238,242,244))
        rgb=np.array(im);ys,xs=np.where(np.any(rgb[:,:,:3]!=[238,242,244],axis=2))
        im=im.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1));im.thumbnail((250,296))
        x=i%3*256;y=i//3*330;sheet.paste(im,(x+(256-im.width)//2,y+25+(296-im.height)//2))
        d.text((x+5,y+7),f'{name} {t:.2f} s',fill=(25,40,50))
    sheet.save(file)


def previews(v):
    m=v.bbmodelo.ler(v.FILE);saved=v.Saved(m)
    v.v2.review.OUT=v.OUT;v.v2.review.g.CLIPS=v.CLIPS
    v.v2.review.preview(m,saved,list(v.CLIPS),fps=24,size=640)
    sheet(v,m,saved,v.OUT/'poses-corrida.png')
