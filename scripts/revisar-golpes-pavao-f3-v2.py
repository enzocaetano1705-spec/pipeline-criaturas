"""Conferência de Low/Cross com extensão, punho solidário e alinhamento do fio."""
import copy
import json
import math
import numpy as np
from PIL import Image,ImageDraw


def quality(v,m,reader,rate=90):
    rig=reader if isinstance(reader,v.Rig) else v.Rig(m);result={};errors=[]
    for name,actions in v.ACTIVE.items():
        result[name]={}
        for side,a,b in actions:
            samples=[];normals=[];wrists=[];elevations=[];tips=[];elbows=[]
            for t in np.linspace(a,b,round((b-a)*rate)+1):
                p=reader.pose(name,float(t));mat=rig.mats(p);w=rig.weapons[side];wm=mat[w['name']]
                d=wm[:3,:3]@w['frame'][:,1];n=wm[:3,:3]@w['frame'][:,2]
                sample=w['grip']+w['frame'][:,1]*(w['length']*.85)
                before=rig.mats(reader.pose(name,float(t-.0005)));after=rig.mats(reader.pose(name,float(t+.0005)))
                vel=(v.point(after[w['name']],sample)-v.point(before[w['name']],sample))/.001
                transverse=vel-d*(vel@d)
                error=math.degrees(math.asin(float(np.clip(abs(n@v.unit(transverse)),0,1))))
                samples.append([float(t),error,float(np.linalg.norm(vel))]);normals.append(n)
                wrists.append(v.R(p['hand_'+side]['rotacao']))
                joints=[v.point(mat[k+side],m.ossos[k+side].origem) for k in ['arm_','forearm_','hand_']]
                elbows.append(math.degrees(math.acos(float(np.clip(v.unit(joints[1]-joints[0])@v.unit(joints[2]-joints[1]),-1,1)))))
                elevations.append(math.degrees(math.asin(float(d[1]))));tips.append(v.point(wm,sample))
            dev=max(math.degrees(math.acos(float(np.clip((np.trace(wrists[0].T@r)-1)/2,-1,1)))) for r in wrists)
            data={'cotovelo_fase_ativa':[min(elbows),max(elbows)],'variacao_punho_graus':dev,
                  'desalinhamento_fio_max_graus':max(x[1] for x in samples),'amostras_fio':samples,
                  'elevacao_lamina':[min(elevations),max(elevations)],'trajetoria_ponta':np.array(tips).tolist()}
            result[name][side]=data
            if max(elbows)>26:errors.append(name+'/'+side+': braço não estende')
            if dev>.2:errors.append(name+'/'+side+': punho varia durante corte')
            if data['desalinhamento_fio_max_graus']>18:errors.append(name+'/'+side+': fio fora do corte')
            print(name,side,'cotovelo',np.round([min(elbows),max(elbows)],1).tolist(),'punho',round(dev,3),'fio',round(data['desalinhamento_fio_max_graus'],2),flush=True)
    return {'clipes':result,'erros':errors}


def sheet(v,m,reader,file):
    samples=[('attack_low',.29),('attack_low',.49),('attack_low',.66),
             ('attack_cross',.30),('attack_cross',.43),('attack_cross',.57),
             ('attack_cross',.70),('attack_cross',.86),('attack_cross',1.03)]
    sheet=Image.new('RGB',(768,768),(238,242,244));draw=ImageDraw.Draw(sheet)
    for i,(name,t) in enumerate(samples):
        mat=v.bbmodelo.matrizes_ossos(m,reader.pose(name,t))
        im,*_=v.render.renderizar(m,vista=(65 if name=='attack_low' else 35,8),mats=mat,escala=3.5,fundo=(238,242,244))
        rgb=np.array(im);ys,xs=np.where(np.any(rgb[:,:,:3]!=[238,242,244],axis=2))
        im=im.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1));im.thumbnail((250,226))
        x=i%3*256;y=i//3*256;sheet.paste(im,(x+(256-im.width)//2,y+26+(226-im.height)//2))
        draw.text((x+5,y+7),f'{name} {t:.2f}s',fill=(25,40,50))
    sheet.save(file)


def study(v):
    v.OUT.mkdir(parents=True,exist_ok=True);(v.OUT/'_cache').mkdir(exist_ok=True)
    old=v.module('revisao_v1','revisar-golpes-pavao-f3.py');m=v.bbmodelo.ler(v.SOURCE);rig=v.Rig(m)
    report=old.measure(v,m,rig,rate=36);report['qualidade']=quality(v,m,rig)
    report['espacial']=old.spatial(v,m,rig,rate=24)
    v.g.dump(v.OUT/'_cache/estudo.json',report);sheet(v,m,rig,v.OUT/'_cache/poses-estudo.png')


def check(v):
    old=v.module('revisao_v1','revisar-golpes-pavao-f3.py');src=v.bbmodelo.ler(v.SOURCE);m=v.bbmodelo.ler(v.FILE)
    for field in ['elements','groups','textures','outliner']:assert src.bruto[field]==m.bruto[field],field
    assert len(m.animacoes)==21 and not any(a['name']=='attack_spin' for a in m.animacoes)
    preserved=[]
    def canonical(a):
        a=copy.deepcopy(a);a['animators']={u:x for u,x in a['animators'].items() if x.get('keyframes')};return a
    for a in src.animacoes:
        if a['name'].startswith('attack_'):continue
        assert canonical(a)==canonical(next(b for b in m.animacoes if b['uuid']==a['uuid'])),a['name'];preserved.append(a['name'])
    saved=v.Saved(m);report={'fonte_sha256':v.g.sha(v.SOURCE),'saida_sha256':v.g.sha(v.FILE),
        'clipes_preservados':preserved,'geometria_rig_uv_textura_preservados':True,'spin_isolado':True}
    report['linear']=old.measure(v,m,saved,rate=240)
    native=v.base.native.NativeSaved(saved)
    report['nativo']=old.measure(v,m,native,rate=240,offset=.00047)
    report['nativo_segunda_fase']=old.measure(v,m,native,rate=240,offset=.00219,verbose=False)
    report['qualidade']=quality(v,m,native)
    report['espacial']=old.spatial(v,m,saved,rate=36)
    report['conexoes']=[];rig=v.Rig(m)
    for n,d in v.CLIPS.items():
        for t in [0,d]:
            mat=rig.mats(saved.pose(n,t));e=max(float(abs(mat[k]-rig.guardmat[k]).max()) for k in mat)
            report['conexoes'].append({'clipe':n,'t':t,'erro':e});assert e<.001,(n,t,e)
    report['erros']=sum((report[k]['erros'] for k in ['linear','nativo','nativo_segunda_fase','qualidade']),[])
    for name,data in report['espacial'].items():
        if data['nova_penetracao_lamina_corpo'][0]>.35:report['erros'].append(name+': lâmina atravessa o corpo')
        if data['min_superficie_opaca_y'][0]<-.06:report['erros'].append(name+': parte opaca sob o piso')
    report['ok']=not report['erros'];v.g.dump(v.OUT/'validacao-ataques.json',report)
    print('Resultado:',report['ok'],report['erros'],flush=True)
    if report['erros']:raise SystemExit(1)


def offline(v):
    old=v.module('revisao_v1','revisar-golpes-pavao-f3.py');old.sheet=sheet;old.offline(v)


def capture(v):
    helper=v.module('captura_golpes','previas-corrida-pavao-f3.py');client=helper.Client(v.ROOT)
    info=client.call('get_project_info');data=info.get('structuredContent') or json.loads(info['content'][0]['text'])
    from pathlib import Path
    assert Path(data['project']['save_path']).resolve()==v.FILE.resolve()
    view='golpes_f3_v2_preview';client.call('create_offscreen_view',id=view,width=640,height=560,antialias=False,copy_view='none')
    counts={};cleanup='ok'
    try:
        client.call('animation_timeline',action='pause',animation_id='attack_low')
        for name,d in v.CLIPS.items():
            client.call('set_camera_angle',view=view,projection='perspective',position=[160,80,-200],target=[0,28,-2],fov=37,max_size=640)
            n=round(d*30);sequence=[(name,float(t),f'{name} | {t:.2f}s') for t in np.arange(n)*d/n]
            counts[name]=helper.gif(v,client,view,sequence,v.OUT/(name+'.gif'),fps=n/d)
            print('Prévia nativa:',name,counts[name],'quadros',flush=True)
        montage=Image.new('RGB',(768,768),(238,242,244));draw=ImageDraw.Draw(montage)
        samples=[('attack_low',.30),('attack_low',.50),('attack_low',.67),
                 ('attack_cross',.30),('attack_cross',.43),('attack_cross',.57),
                 ('attack_cross',.70),('attack_cross',.87),('attack_cross',1.03)]
        for i,(name,t) in enumerate(samples):
            with Image.open(v.OUT/(name+'.gif')) as gif:
                frame=min(counts[name]-1,round(t*counts[name]/v.CLIPS[name]));gif.seek(frame);im=gif.convert('RGB')
            im.thumbnail((250,226));x=i%3*256;y=i//3*256
            montage.paste(im,(x+(256-im.width)//2,y+26+(226-im.height)//2))
            draw.text((x+5,y+7),f'{name} {frame*v.CLIPS[name]/counts[name]:.2f}s',fill=(25,40,50))
        montage.save(v.OUT/'poses-nativas.png')
    finally:
        try:client.call('delete_offscreen_view',view=view)
        except RuntimeError as error:
            if 'onContextMenu is not defined' not in str(error):raise
            cleanup='registro removido; erro conhecido do listener onContextMenu'
        finally:client.call('animation_timeline',action='set_time',animation_id='attack_low',time=0)
    v.g.dump(v.OUT/'previas-nativas.json',{'modelo':str(v.FILE),'saida_sha256':v.g.sha(v.FILE),'quadros':counts,'camera_fixa':True,'limpeza_view':cleanup})
