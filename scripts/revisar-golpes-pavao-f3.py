"""Confere golpes F3 no arquivo e no relógio nativo; cria prévias pelo MCP."""
import copy
import json
import math

import numpy as np
from PIL import Image,ImageDraw


def angle(a,b):return math.degrees(math.acos(float(np.clip((np.trace(a.T@b)-1)/2,-1,1))))


def measure(v,m,reader,rate=120,offset=0.,verbose=True):
    rig=reader if isinstance(reader,v.Rig) else v.Rig(m)
    result={};errors=[]
    for name,duration in v.CLIPS.items():
        floor=1e9;blade_floor=1e9;air=0.;grip=hinge=anchor=weld=root=0.;last=None;step=0.
        elbows=[];knees=[];wrists=[];worst={};yaws=[];lowtips=[];trace=[]
        times=np.linspace(0,duration,round(duration*rate)+1)
        if offset:times=np.unique(np.r_[0,times[:-1]+offset,duration])
        for t in times:
            t=float(t);p=reader.pose(name,t);mat=rig.mats(p);feet_y=[];points={}
            root=max(root,float(abs(mat['root']-np.eye(4)).max()))
            for side in v.SIDES:
                r=mat['foot_'+side][:3,:3];center=v.point(mat['foot_'+side],rig.feet[side])
                fy=float((rig.footverts[side]@r.T+center)[:,1].min());feet_y.append(fy);floor=min(floor,fy)
                w=rig.weapons[side];wm=mat[w['name']];wg=v.point(wm,w['grip']);hand=mat['hand_'+side]
                hg=v.point(hand,rig.grips[side]);grip=max(grip,float(np.linalg.norm(wg-hg)))
                vs=rig.weaponverts[side];world=vs@wm[:3,:3].T+wg;points[side]=world
                expected=vs@(hand[:3,:3]@rig.bind[side]).T+hg
                weld=max(weld,float(np.linalg.norm(world-expected,axis=1).max()))
                bottom=float(world[:,1].min())
                if bottom<blade_floor:blade_floor=bottom;worst['espada_piso']=[side,t,bottom]
                a,b,c=[v.point(mat[n+side],m.ossos[n+side].origem) for n in ['arm_','forearm_','hand_']]
                elbows.append(math.degrees(math.acos(np.clip(v.unit(b-a)@v.unit(c-b),-1,1))))
                a,b,c=[v.point(mat[n+side],m.ossos[n+side].origem) for n in ['leg_','shin_','foot_']]
                knees.append(math.degrees(math.acos(np.clip(v.unit(b-a)@v.unit(c-b),-1,1))))
                u=v.unit(rig.hinges[side][1]);a=mat['forearm_'+side][:3,:3]@u;b=mat['hand_'+side][:3,:3]@u
                wrists.append(math.degrees(math.acos(np.clip(a@b,-1,1))))
                axis=rig.hinges[side][2];hinge=max(hinge,float(np.linalg.norm(v.R(p['forearm_'+side]['rotacao'])@axis-axis)))
            air=max(air,min(feet_y))
            for n,a in rig.anchors.items():
                anchor=max(anchor,float(np.linalg.norm(v.point(mat[n],a)-v.point(mat[m.ossos[n].pai],a))))
            z=mat['body'][:3,2];yaws.append(math.atan2(z[0],z[2]))
            if last:
                for n in m.ossos:
                    e=angle(last[n][:3,:3],mat[n][:3,:3])
                    if e>step:step=e;worst['passo']=[n,t,e]
            last=mat
            if v.EVENTS[name]['DamageStart']<=t<=v.EVENTS[name]['DamageEnd']:
                w=rig.weapons['right'];vs=rig.weaponverts['right'];a=vs@w['frame'][:,1]
                selected=points['right'][a>np.quantile(a,.70)]
                lowtips.append([float(selected[:,1].min()),float(selected[:,1].max()),float(selected[:,2].min())])
            trace.append({'t':t,'right_min_y':float(points['right'][:,1].min()),'left_min_y':float(points['left'][:,1].min())})
        data={'min_pe_y':floor,'min_lamina_y':blade_floor,'ambos_pes_fora_y':air,'erro_preensao':grip,
            'erro_lamina_inteira':weld,'erro_ancoras':anchor,'erro_eixo_cotovelo':hinge,'erro_root':root,
            'cotovelos_graus':[min(elbows),max(elbows)],'joelhos_graus':[min(knees),max(knees)],
            'punho_max_graus':max(wrists),'maior_passo_angular':step,
            'giro_corpo_graus':float(np.degrees(np.unwrap(yaws)[-1]-np.unwrap(yaws)[0])),
            'faixa_pontas_ativas':np.array(lowtips).tolist(),'piores_amostras':worst}
        checks=[(floor<-.05,'pé sob o piso'),(blade_floor<-.05,'lâmina sob o piso'),(air>.08,'sem apoio'),
                (grip>.035,'preensão'),(weld>.08,'vínculo da lâmina'),(anchor>.02,'pena deslocada'),
                (hinge>.005,'eixo do cotovelo'),(root>1e-6,'root deslocado'),
                (min(elbows)<5 or max(elbows)>150,'cotovelo'),(min(knees)<3 or max(knees)>155,'joelho'),
                (max(wrists)>80,'punho'),(rate>=120 and step>18,'flick angular')]
        if name=='attack_spin':checks.append((abs(data['giro_corpo_graus']-360)>.05,'volta incompleta'))
        fails=[msg for failed,msg in checks if failed];errors.extend(name+': '+msg for msg in fails)
        result[name]=data
        if verbose:print(name+': '+(', '.join(fails) if fails else 'OK'),flush=True)
    return {'clipes':result,'erros':errors,'alcance_excedido':rig.max_unreachable,'alcance_por_membro':rig.reach}


def sheet(v,m,reader,file):
    samples=[('attack_low',.22),('attack_low',.43),('attack_low',.65),
             ('attack_cross',.38),('attack_cross',.76),('attack_cross',.98),
             ('attack_spin',.30),('attack_spin',.70),('attack_spin',1.03)]
    sheet=Image.new('RGB',(768,768),(238,242,244));draw=ImageDraw.Draw(sheet)
    for i,(name,t) in enumerate(samples):
        mat=v.bbmodelo.matrizes_ossos(m,reader.pose(name,t))
        im,*_=v.render.renderizar(m,vista=(35,8),mats=mat,escala=4,fundo=(238,242,244))
        rgb=np.array(im);ys,xs=np.where(np.any(rgb[:,:,:3]!=[238,242,244],axis=2))
        im=im.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1));im.thumbnail((250,226))
        x=i%3*256;y=i//3*256;sheet.paste(im,(x+(256-im.width)//2,y+26+(226-im.height)//2))
        draw.text((x+5,y+7),f'{name} {t:.2f}s',fill=(25,40,50))
    sheet.save(file)


def spatial(v,m,reader,rate=36):
    """Sondagem de superfície opaca contra volumes corporais; não é uma hitbox de jogo."""
    texture=np.asarray(m.textura);local={}
    for c in m.cubos:
        chunks=[]
        for face in ['north','south','east','west','up','down']:
            result=v.g.texturizar.texels_da_face(c,face,np.eye(4))
            if result is None:continue
            uv,points=result;valid=(uv[:,0]>=0)&(uv[:,0]<texture.shape[1])&(uv[:,1]>=0)&(uv[:,1]<texture.shape[0])
            uv=uv[valid];points=points[valid];points=points[texture[uv[:,1],uv[:,0],3]>128]
            if len(points)>180:points=points[np.linspace(0,len(points)-1,180).astype(int)]
            if len(points):chunks.append(points)
        local[c.uuid]=np.concatenate(chunks) if chunks else v.bbmodelo.cantos(c)
    rig=reader if isinstance(reader,v.Rig) else v.Rig(m);rest=rig.guardmat
    core=[c for c in m.cubos if min(c.tamanho)>1.5 and
          (c.osso in ['body','pelvis','waist','torso','neck_1','neck_2','head'] or c.osso.startswith(('leg_','shin_')))]
    weapons=[c for c in m.cubos if c.osso in ['tail_fan_04','tail_fan_06']]
    def depth(points,c):return np.maximum(0,np.minimum(points-c.de,c.ate-points).min(axis=1))
    baseline={}
    for c in weapons:
        world=v.bbmodelo.aplicar(v.bbmodelo.matriz_cubo(m,c,rest),local[c.uuid])
        for b in core:
            q=v.bbmodelo.aplicar(np.linalg.inv(v.bbmodelo.matriz_cubo(m,b,rest)),world)
            baseline[c.uuid,b.uuid]=depth(q,b)
    report={}
    for name,d in v.CLIPS.items():
        worst=(0.,None,None,None);floor=(1e9,None,None)
        for t in np.linspace(0,d,round(d*rate)+1):
            mat=rig.mats(reader.pose(name,float(t)));inverses={b.uuid:np.linalg.inv(v.bbmodelo.matriz_cubo(m,b,mat)) for b in core}
            for c in m.cubos:
                cm=v.bbmodelo.matriz_cubo(m,c,mat)
                low=float(v.bbmodelo.aplicar(cm,v.bbmodelo.cantos(c))[:,1].min())
                if low<floor[0]:
                    actual=float(v.bbmodelo.aplicar(cm,local[c.uuid])[:,1].min())
                    if actual<floor[0]:floor=(actual,float(t),c.nome)
            for c in weapons:
                world=v.bbmodelo.aplicar(v.bbmodelo.matriz_cubo(m,c,mat),local[c.uuid])
                for b in core:
                    dep=depth(v.bbmodelo.aplicar(inverses[b.uuid],world),b)-baseline[c.uuid,b.uuid]
                    amount=float(dep.max())
                    if amount>worst[0]:worst=(amount,float(t),c.nome,b.nome)
        report[name]={'nova_penetracao_lamina_corpo':worst,'min_superficie_opaca_y':floor}
        print(name,'superfície mínima',round(floor[0],4),'penetração nova',round(worst[0],4),flush=True)
    return report


def study(v):
    v.OUT.mkdir(parents=True,exist_ok=True);(v.OUT/'_cache').mkdir(exist_ok=True)
    m=v.bbmodelo.ler(v.SOURCE);rig=v.Rig(m);result=measure(v,m,rig,rate=36)
    result['espacial']=spatial(v,m,rig)
    v.g.dump(v.OUT/'_cache/estudo.json',result)
    print('Alcance:',rig.max_unreachable,rig.reach,flush=True)
    sheet(v,m,rig,v.OUT/'_cache/poses-estudo.png')


def check(v):
    src=v.bbmodelo.ler(v.SOURCE);m=v.bbmodelo.ler(v.FILE)
    for field in ['elements','groups','textures','outliner']:assert src.bruto[field]==m.bruto[field],field
    assert len(m.animacoes)==len(src.animacoes)+3
    def canonical(a):
        a=copy.deepcopy(a);a['animators']={u:x for u,x in a['animators'].items() if x.get('keyframes')};return a
    for a in src.animacoes:assert canonical(a)==canonical(next(b for b in m.animacoes if b['uuid']==a['uuid'])),a['name']
    saved=v.Saved(m);report={'fonte_sha256':v.g.sha(v.SOURCE),'saida_sha256':v.g.sha(v.FILE),
        'clipes_preservados':[a['name'] for a in src.animacoes],'geometria_rig_uv_textura_preservados':True}
    report['linear']=measure(v,m,saved,rate=240)
    report['nativo']=measure(v,m,v.base.native.NativeSaved(saved),rate=240,offset=.00047)
    report['nativo_segunda_fase']=measure(v,m,v.base.native.NativeSaved(saved),rate=240,offset=.00219,verbose=False)
    report['espacial']=spatial(v,m,saved,rate=36)
    report['conexoes']=[];guard=v.Rig(m).guard
    gm=v.bbmodelo.matrizes_ossos(m,guard)
    for n,d in v.CLIPS.items():
        for t in [0,d]:
            mat=v.bbmodelo.matrizes_ossos(m,saved.pose(n,t));e=max(float(abs(mat[k]-gm[k]).max()) for k in gm)
            report['conexoes'].append({'clipe':n,'t':t,'erro':e});assert e<.001,(n,t,e)
    report['erros']=sum((report[k]['erros'] for k in ['linear','nativo','nativo_segunda_fase']),[])
    for name,data in report['espacial'].items():
        if data['nova_penetracao_lamina_corpo'][0]>.35:report['erros'].append(name+': lâmina atravessa o corpo')
        if data['min_superficie_opaca_y'][0]<-.06:report['erros'].append(name+': parte opaca sob o piso')
    report['ok']=not report['erros'];v.g.dump(v.OUT/'validacao-ataques.json',report)
    print('Resultado:',report['ok'],report['erros'],flush=True)
    if report['erros']:raise SystemExit(1)


def offline(v):
    """Reserva sem aplicativo: lê as chaves salvas com a semântica numérica nativa."""
    m=v.bbmodelo.ler(v.FILE);reader=v.base.native.NativeSaved(v.Saved(m));counts={}
    cameras={'attack_low':(75,8),'attack_cross':(35,8),'attack_spin':(35,12)}
    background=(238,242,244)
    for name,d in v.CLIPS.items():
        n=round(d*30);times=np.r_[np.arange(n)*d/n,d]
        matrices=[v.bbmodelo.matrizes_ossos(m,reader.pose(name,float(t))) for t in times]
        f,r,u=v.render.camera(*cameras[name]);extents=[]
        for mat in matrices:
            points=np.concatenate([v.bbmodelo.aplicar(v.bbmodelo.matriz_cubo(m,c,mat),v.bbmodelo.cantos(c)) for c in m.cubos])
            extents.append(np.c_[points@r,points@u])
        extents=np.concatenate(extents);lo=extents.min(axis=0);hi=extents.max(axis=0)
        scale=min(520/(hi[0]-lo[0]),420/(hi[1]-lo[1]));center=(lo+hi)/2
        proj=v.render.Projecao(r,u,f,scale,center[0]-280/scale,center[1]+240/scale,0,(560,480))
        frames=[]
        for t,mat in zip(times,matrices):
            im,mask,*_=v.render.renderizar(m,mats=mat,projecao=proj,fundo=background)
            ground=Image.new('RGB',im.size,background);draw=ImageDraw.Draw(ground)
            for q in range(-80,81,8):
                for points in [np.array([[q,0,-80],[q,0,80]]),np.array([[-80,0,q],[80,0,q]])]:
                    xy=proj.pixel(points);draw.line([tuple(xy[0]),tuple(xy[1])],fill=(218,226,230))
            ground.paste(im,(0,0),Image.fromarray((mask*255).astype('uint8')))
            ImageDraw.Draw(ground).text((8,8),f'{name} | {t:.2f}s | previa local',fill=(25,40,50));frames.append(ground)
        durations=[round(1000*d/n)]*len(frames);durations[-1]=300
        frames[0].save(v.OUT/(name+'-local.gif'),save_all=True,append_images=frames[1:],duration=durations,loop=0,disposal=2)
        counts[name]=len(frames);print('Prévia local:',name,len(frames),'quadros',flush=True)
    sheet(v,m,reader,v.OUT/'poses-locais.png')
    v.g.dump(v.OUT/'previas-locais.json',{'saida_sha256':v.g.sha(v.FILE),'quadros':counts,
        'origem':'renderizador local; chaves do arquivo salvo e leitura numérica nativa, sem captura do aplicativo',
        'camera_fixa_por_clipe':cameras,'fps_aproximado':30})


def capture(v):
    helper=v.module('captura_golpes','previas-corrida-pavao-f3.py');client=helper.Client(v.ROOT)
    info=client.call('get_project_info');data=info.get('structuredContent') or json.loads(info['content'][0]['text'])
    from pathlib import Path
    assert Path(data['project']['save_path']).resolve()==v.FILE.resolve()
    view='golpes_f3_preview';client.call('create_offscreen_view',id=view,width=640,height=560,antialias=False,copy_view='none')
    counts={};cleanup='ok'
    try:
        client.call('animation_timeline',action='pause',animation_id='attack_low')
        client.call('set_camera_angle',view=view,projection='perspective',position=[155,90,-220],target=[0,23,0],fov=35,max_size=640)
        for name,d in v.CLIPS.items():
            n=round(d*30);sequence=[(name,float(t),f'{name} | {t:.2f}s') for t in np.arange(n)*d/n]
            counts[name]=helper.gif(v,client,view,sequence,v.OUT/(name+'.gif'),fps=n/d)
            print('Prévia nativa:',name,counts[name],'quadros',flush=True)
        sheet=Image.new('RGB',(768,768),(238,242,244));draw=ImageDraw.Draw(sheet)
        samples=[('attack_low',.22),('attack_low',.43),('attack_low',.65),('attack_cross',.38),('attack_cross',.76),('attack_cross',.98),
                 ('attack_spin',.30),('attack_spin',.70),('attack_spin',1.03)]
        for i,(name,t) in enumerate(samples):
            client.call('animation_timeline',action='set_time',animation_id=name,time=t)
            im=helper.decoded(client.call('capture_screenshot',view=view,max_size=640));im=im.crop(im.getbbox());im.thumbnail((250,226))
            bg=Image.new('RGBA',im.size,(238,242,244,255));bg.alpha_composite(im)
            x=i%3*256;y=i//3*256;sheet.paste(bg.convert('RGB'),(x+(256-im.width)//2,y+26+(226-im.height)//2))
            draw.text((x+5,y+7),f'{name} {t:.2f}s',fill=(25,40,50))
        sheet.save(v.OUT/'poses-nativas.png')
    finally:
        try:client.call('delete_offscreen_view',view=view)
        except RuntimeError as error:
            if 'onContextMenu is not defined' not in str(error):raise
            cleanup='registro removido; erro conhecido do listener onContextMenu'
        finally:client.call('animation_timeline',action='set_time',animation_id='attack_low',time=0)
    v.g.dump(v.OUT/'previas-nativas.json',{'modelo':str(v.FILE),'saida_sha256':v.g.sha(v.FILE),'quadros':counts,'camera_fixa':True,'limpeza_view':cleanup})
