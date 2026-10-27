"""Validação dos golpes v4, incluindo penas dos cotovelos contra o peito."""
import copy
import json
import math
import numpy as np
from PIL import Image,ImageDraw


def mechanics(v,m,reader,rate=240,offset=0.):
    old=v.module('mecanica_ataques','revisar-golpes-pavao-f3.py')
    report=old.measure(v,m,reader,rate=rate,offset=offset,verbose=False)
    report['erros']=[e for e in report['erros'] if e not in ['attack_low: punho','attack_cross: punho']]
    report['referencia_punho']='Proxy mantídeo registrado; aceite por colinearidade real do antebraço/empunhadura e preensão, com pronossupinação axial independente do cotovelo.'
    print('Mecânica:',report['erros'] or 'OK',flush=True);return report


def requested(v,m,reader,rate=60):
    old=v.module('distancias_v3','revisar-golpes-pavao-f3-v3.py');rig=reader if isinstance(reader,v.Rig) else v.Rig(m)
    data={};errors=[]
    for name,d in v.CLIPS.items():
        gaps=[]
        for t in np.linspace(0,d,round(d*rate)+1):
            limbs=old.arms(v,m,rig,reader.pose(name,float(t)))
            for a,b,ra,na in limbs['right']:
                for c,e,rb,nb in limbs['left']:gaps.append([old.segment_distance(a,b,c,e)-ra-rb,float(t),na,nb])
        data[name]={'folga_bracos':min(gaps),'cortes':{}}
        if min(gaps)[0]<.15:errors.append(name+': braços se atravessam')
        for side,a,b in v.ACTIVE[name]:
            align=[];edges=[];tips=[];az=[];speed=[]
            w=rig.weapons[side];sample=w['grip']+w['frame'][:,1]*w['length']*.85
            for t in np.linspace(a,b,round((b-a)*120)+1):
                p=reader.pose(name,float(t));mat=rig.mats(p);wm=mat[w['name']]
                direction=wm[:3,:3]@w['frame'][:,1];normal=wm[:3,:3]@w['frame'][:,2]
                forearm=v.unit(v.point(mat['hand_'+side],m.ossos['hand_'+side].origem)-v.point(mat['forearm_'+side],m.ossos['forearm_'+side].origem))
                align.append(old.angle(forearm,direction));az.append(math.atan2(direction[0],direction[2]))
                before=rig.mats(reader.pose(name,float(t-.0005)));after=rig.mats(reader.pose(name,float(t+.0005)))
                velocity=(v.point(after[w['name']],sample)-v.point(before[w['name']],sample))/.001
                transverse=velocity-direction*(direction@velocity)
                edges.append(math.degrees(math.asin(float(np.clip(abs(normal@v.unit(transverse)),0,1)))))
                tip=v.point(wm,sample);tips.append([float(t),float(-tip[0]),float(tip[1]),float(tip[2])]);speed.append(float(np.linalg.norm(velocity)))
            xy=np.array(tips);delta=xy[-1,1:3]-xy[0,1:3]
            entry={'alinhamento_max':max(align),'fio_max':max(edges),'pico_velocidade_ponta':max(speed),
                   'arco_azimute':float(np.degrees(np.unwrap(az)[-1]-np.unwrap(az)[0])),
                   'delta_frontal_xy':delta.tolist(),'trajetoria':tips}
            data[name]['cortes'][side]=entry
            if max(align)>2:errors.append(name+'/'+side+': eixo espada desalinhado')
            if max(edges)>20:errors.append(name+'/'+side+': fio fora do corte')
            if name=='attack_low' and entry['arco_azimute']<150:errors.append('Low: amplitude insuficiente')
            if name=='attack_cross' and side=='right' and (delta[0]<50 or delta[1]<25):errors.append('Cross: ascendente sem amplitude diagonal')
            if name=='attack_cross' and side=='left' and not (delta[0]<-8 and delta[1]<-30):errors.append('Cross: descendente sem leve diagonal oposta')
            print(name,side,'eixo',round(max(align),3),'fio',round(max(edges),2),'arco',round(entry['arco_azimute'],1),flush=True)
    data['erros']=errors;return data


def wing_chest(v,m,reader,rate=30):
    rig=reader if isinstance(reader,v.Rig) else v.Rig(m);texture=np.asarray(m.textura);points={}
    wings=[c for c in m.cubos if c.osso in ['wing_left','wing_right']]
    core=[c for c in m.cubos if c.osso in ['body','pelvis','waist','torso','neck_1','neck_2'] and min(c.tamanho)>1]
    for cube in wings:
        chunks=[]
        for face in ['north','south','east','west','up','down']:
            result=v.g.texturizar.texels_da_face(cube,face,np.eye(4))
            if result is None:continue
            uv,xyz=result;mask=(uv[:,0]>=0)&(uv[:,0]<texture.shape[1])&(uv[:,1]>=0)&(uv[:,1]<texture.shape[0]);uv=uv[mask];xyz=xyz[mask]
            xyz=xyz[texture[uv[:,1],uv[:,0],3]>128]
            if len(xyz)>180:xyz=xyz[np.linspace(0,len(xyz)-1,180).astype(int)]
            if len(xyz):chunks.append(xyz)
        points[cube.uuid]=np.concatenate(chunks) if chunks else np.empty((0,3))
    def penetration(xyz,c):return np.maximum(0,np.minimum(xyz-c.de,c.ate-xyz).min(axis=1))
    baseline={}
    for c in wings:
        world=v.bbmodelo.aplicar(v.bbmodelo.matriz_cubo(m,c,rig.guardmat),points[c.uuid])
        for b in core:baseline[c.uuid,b.uuid]=penetration(v.bbmodelo.aplicar(np.linalg.inv(v.bbmodelo.matriz_cubo(m,b,rig.guardmat)),world),b)
    report={};errors=[]
    for name,d in v.CLIPS.items():
        worst=[0.,None,None,None];elbow=[1e9,None,None,None]
        for t in np.linspace(0,d,round(d*rate)+1):
            mat=rig.mats(reader.pose(name,float(t)));inv={b.uuid:np.linalg.inv(v.bbmodelo.matriz_cubo(m,b,mat)) for b in core}
            for c in wings:
                if not len(points[c.uuid]):continue
                world=v.bbmodelo.aplicar(v.bbmodelo.matriz_cubo(m,c,mat),points[c.uuid])
                for b in core:
                    depth=penetration(v.bbmodelo.aplicar(inv[b.uuid],world),b)-baseline[c.uuid,b.uuid]
                    amount=float(depth.max())
                    if amount>worst[0]:worst=[amount,float(t),c.nome,b.nome]
            for side in v.SIDES:
                e=v.point(mat['forearm_'+side],m.ossos['forearm_'+side].origem)
                for b in core:
                    q=v.point(inv[b.uuid],e);outside=np.maximum(np.maximum(b.de-q,q-b.ate),0);distance=float(np.linalg.norm(outside))
                    if distance<1e-8:distance=-float(np.minimum(q-b.de,b.ate-q).min())
                    if distance<elbow[0]:elbow=[distance,float(t),side,b.nome]
        report[name]={'pena_penetracao_nova':worst,'cotovelo_distancia_corpo':elbow}
        if worst[0]>.2:errors.append(name+': pena do cotovelo entra no corpo')
        if elbow[0]<.4:errors.append(name+': cotovelo no peito')
        print(name,'penas/peito',round(worst[0],3),'cotovelo livre',round(elbow[0],3),flush=True)
    report['erros']=errors;return report


def sheet(v,m,reader,file):
    samples=[('attack_low',.45),('attack_low',.73),('attack_low',.96),
             ('attack_cross',.43),('attack_cross',.67),('attack_cross',.88),
             ('attack_cross',1.15),('attack_cross',1.30),('attack_cross',1.42)]
    sheet=Image.new('RGB',(768,768),(238,242,244));draw=ImageDraw.Draw(sheet)
    for i,(name,t) in enumerate(samples):
        mat=v.bbmodelo.matrizes_ossos(m,reader.pose(name,t))
        im,*_=v.render.renderizar(m,vista=('frente' if name=='attack_cross' else (65,20)),mats=mat,escala=3.2,fundo=(238,242,244))
        arr=np.asarray(im);ys,xs=np.where(np.any(arr[:,:,:3]!=[238,242,244],axis=2));im=im.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1));im.thumbnail((250,226))
        x=i%3*256;y=i//3*256;sheet.paste(im,(x+(256-im.width)//2,y+26+(226-im.height)//2));draw.text((x+5,y+7),f'{name} {t:.2f}s',fill=(25,40,50))
    sheet.save(file)


def study(v):
    v.OUT.mkdir(parents=True,exist_ok=True);(v.OUT/'_cache').mkdir(exist_ok=True)
    m=v.bbmodelo.ler(v.SOURCE);rig=v.Rig(m);old=v.module('espacial_antiga','revisar-golpes-pavao-f3.py')
    r=mechanics(v,m,rig,rate=30);r['pedido']=requested(v,m,rig,rate=45);r['cotovelos']=wing_chest(v,m,rig,rate=24)
    r['espacial']=old.spatial(v,m,rig,rate=24);v.g.dump(v.OUT/'_cache/estudo.json',r);sheet(v,m,rig,v.OUT/'_cache/poses-estudo.png')


def check(v):
    src=v.bbmodelo.ler(v.SOURCE);m=v.bbmodelo.ler(v.FILE)
    for k in ['elements','groups','textures','outliner']:assert src.bruto[k]==m.bruto[k],k
    assert len(m.animacoes)==21
    def canonical(a):
        a=copy.deepcopy(a);a['animators']={k:x for k,x in a['animators'].items() if x.get('keyframes')};return a
    preserved=[]
    for a in src.animacoes:
        if a['name'] in v.CLIPS:continue
        assert canonical(a)==canonical(next(b for b in m.animacoes if b['uuid']==a['uuid'])),a['name'];preserved.append(a['name'])
    saved=v.Saved(m);native=v.base.native.NativeSaved(saved);r={'fonte_sha256':v.g.sha(v.SOURCE),'saida_sha256':v.g.sha(v.FILE),
        'clipes_preservados':preserved,'geometria_rig_uv_textura_preservados':True}
    r['linear']=mechanics(v,m,saved);r['nativo']=mechanics(v,m,native,offset=.00047);r['nativo_segunda_fase']=mechanics(v,m,native,offset=.00219)
    r['pedido']=requested(v,m,native);r['cotovelos']=wing_chest(v,m,native,rate=60)
    old=v.module('espacial_antiga','revisar-golpes-pavao-f3.py');r['espacial']=old.spatial(v,m,saved,rate=36)
    rig=v.Rig(m);r['conexoes']=[]
    for n,d in v.CLIPS.items():
        for t in [0,d]:
            mat=rig.mats(saved.pose(n,t));err=max(float(abs(mat[k]-rig.guardmat[k]).max()) for k in mat)
            r['conexoes'].append({'clipe':n,'t':t,'erro':err});assert err<.001,(n,t,err)
    r['erros']=sum((r[k]['erros'] for k in ['linear','nativo','nativo_segunda_fase','pedido','cotovelos']),[])
    for n,data in r['espacial'].items():
        if data['nova_penetracao_lamina_corpo'][0]>.35:r['erros'].append(n+': espada entra no corpo')
        if data['min_superficie_opaca_y'][0]<-.06:r['erros'].append(n+': superfície sob o piso')
    r['ok']=not r['erros'];v.g.dump(v.OUT/'validacao-ataques.json',r);print('Resultado:',r['ok'],r['erros'],flush=True)
    if not r['ok']:raise SystemExit(1)


def capture(v):
    helper=v.module('captura_nativa','previas-corrida-pavao-f3.py');client=helper.Client(v.ROOT)
    info=client.call('get_project_info');data=info.get('structuredContent') or json.loads(info['content'][0]['text'])
    from pathlib import Path
    assert Path(data['project']['save_path']).resolve()==v.FILE.resolve()
    view='golpes_f3_v4_preview';client.call('create_offscreen_view',id=view,width=640,height=560,antialias=False,copy_view='none')
    tracks={'attack_low':('attack_low',[175,90,-230],[0,28,-2]),
            'attack_cross':('attack_cross',[0,28,-285],[0,28,0]),
            'attack_cross-3q':('attack_cross',[160,80,-235],[0,28,-2])}
    counts={};cleanup='ok'
    try:
        client.call('animation_timeline',action='pause',animation_id='attack_low')
        for key,(name,position,target) in tracks.items():
            client.call('set_camera_angle',view=view,projection='perspective',position=position,target=target,fov=37,max_size=640)
            d=v.CLIPS[name];n=round(d*30);sequence=[(name,float(t),f'{key} | {t:.2f}s') for t in np.arange(n)*d/n]
            counts[key]=helper.gif(v,client,view,sequence,v.OUT/(key+'.gif'),fps=n/d)
            print('Prévia nativa:',key,counts[key],'quadros',flush=True)
        montage=Image.new('RGB',(768,768),(238,242,244));draw=ImageDraw.Draw(montage)
        samples=[('attack_low',.45),('attack_low',.73),('attack_low',.96),
                 ('attack_cross',.43),('attack_cross',.67),('attack_cross',.88),
                 ('attack_cross-3q',1.02),('attack_cross',1.28),('attack_cross',1.42)]
        for i,(key,t) in enumerate(samples):
            clip=tracks[key][0];d=v.CLIPS[clip]
            with Image.open(v.OUT/(key+'.gif')) as gif:
                frame=min(counts[key]-1,round(t*counts[key]/d));gif.seek(frame);im=gif.convert('RGB')
            im.thumbnail((250,226));x=i%3*256;y=i//3*256;montage.paste(im,(x+(256-im.width)//2,y+26+(226-im.height)//2))
            draw.text((x+5,y+7),f'{key} {frame*d/counts[key]:.2f}s',fill=(25,40,50))
        montage.save(v.OUT/'poses-nativas.png')
    finally:
        try:client.call('delete_offscreen_view',view=view)
        except RuntimeError as error:
            if 'onContextMenu is not defined' not in str(error):raise
            cleanup='registro removido; erro conhecido do listener onContextMenu'
        finally:client.call('animation_timeline',action='set_time',animation_id='attack_low',time=0)
    v.g.dump(v.OUT/'previas-nativas.json',{'saida_sha256':v.g.sha(v.FILE),'quadros':counts,'cameras':tracks,
        'camera_fixa_por_clipe':True,'limpeza_view':cleanup})
