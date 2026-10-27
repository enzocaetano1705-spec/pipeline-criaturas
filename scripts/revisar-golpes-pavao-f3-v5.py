"""Revisão dos quatro golpes F3; voo permitido só na janela do combo."""
import copy
import json
import math
import numpy as np
from PIL import Image,ImageDraw


def mechanics(v,m,reader,rate=120,offset=0.):
    old=v.module('mecanica_golpes_v5','revisar-golpes-pavao-f3.py');r=old.measure(v,m,reader,rate=rate,offset=offset,verbose=False)
    expected=['attack_combo: sem apoio','attack_combo: root deslocado']+[n+': punho' for n in v.CLIPS]
    r['erros']=[x for x in r['erros'] if x not in expected]
    r['criterio_punho']='Eixo geométrico antebraço/espada e preensão; proxy legado mantídeo apenas diagnóstico.'
    rig=reader if isinstance(reader,v.Rig) else v.Rig(m);heights=[];spin=[];ground=[];root_off=0.
    for t in np.linspace(0,v.CLIPS['attack_combo'],round(v.CLIPS['attack_combo']*rate)+1):
        p=reader.pose('attack_combo',float(t));mat=rig.mats(p);root=mat['root'];root_off=max(root_off,float(abs(root[[0,2],3]).max()),float(abs(root[:3,:3]-np.eye(3)).max()))
        feet=[float((rig.footverts[s]@mat['foot_'+s][:3,:3].T+v.point(mat['foot_'+s],rig.feet[s]))[:,1].min()) for s in v.SIDES]
        if v.TAKEOFF+.08<t<v.LANDING-.08:heights.append([float(t),min(feet)])
        if t<v.TAKEOFF-.001 or t>v.LANDING+.001:ground.append(min(feet))
        if v.TAKEOFF<=t<=v.LANDING:
            z=mat['body'][:3,2];spin.append(math.atan2(z[0],z[2]))
    turned=float(np.degrees(np.unwrap(spin)[-1]-np.unwrap(spin)[0]))
    r['voo']={'pes_altura_max':max(x[1] for x in heights),'pes_altura_min_janela_interna':min(x[1] for x in heights),
        'apoio_fora_voo_max':max(ground),'root_fora_eixo_y':root_off,'giro_aereo_graus':turned}
    if root_off>1e-6:r['erros'].append('combo: root fora do eixo Y')
    if max(ground)>.08:r['erros'].append('combo: flutua fora do salto')
    if min(x[1] for x in heights)<1:r['erros'].append('combo: pés sem voo claro')
    if abs(turned-360)>4:r['erros'].append('combo: volta aérea incompleta')
    print('Mecânica:',r['erros'] or 'OK',flush=True);return r


def motion(v,m,reader,rate=60):
    helper=v.module('distancias_golpes_v5','revisar-golpes-pavao-f3-v3.py');rig=reader if isinstance(reader,v.Rig) else v.Rig(m);report={};errors=[]
    for name,duration in v.CLIPS.items():
        gaps=[]
        for t in np.linspace(0,duration,round(duration*rate)+1):
            limbs=helper.arms(v,m,rig,reader.pose(name,float(t)))
            for a,b,ra,na in limbs['right']:
                for c,e,rb,nb in limbs['left']:gaps.append([helper.segment_distance(a,b,c,e)-ra-rb,float(t),na,nb])
        report[name]={'folga_bracos':min(gaps),'cortes':[]}
        if min(gaps)[0]<.15:errors.append(name+': braços se atravessam')
        for side,start,end in v.ACTIVE[name]:
            rows=[];weapon=rig.weapons[side];sample=weapon['grip']+weapon['frame'][:,1]*weapon['length']*.85
            for t in np.linspace(start,end,round((end-start)*120)+1):
                p=reader.pose(name,float(t));mat=rig.mats(p);wm=mat[weapon['name']]
                direction=wm[:3,:3]@weapon['frame'][:,1];normal=wm[:3,:3]@weapon['frame'][:,2]
                forearm=v.unit(v.point(mat['hand_'+side],m.ossos['hand_'+side].origem)-v.point(mat['forearm_'+side],m.ossos['forearm_'+side].origem))
                a=rig.mats(reader.pose(name,float(t-.0005)));b=rig.mats(reader.pose(name,float(t+.0005)))
                velocity=(v.point(b[weapon['name']],sample)-v.point(a[weapon['name']],sample))/.001
                transverse=velocity-direction*(direction@velocity)
                edge=math.degrees(math.asin(float(np.clip(abs(normal@v.unit(transverse)),0,1))))
                rows.append([float(t),helper.angle(forearm,direction),edge,float(np.linalg.norm(velocity))])
            values=np.array(rows);entry={'lado':side,'inicio':start,'fim':end,'eixo_max':float(values[:,1].max()),'fio_max':float(values[:,2].max()),'velocidade_ponta':rows}
            report[name]['cortes'].append(entry)
            if entry['eixo_max']>2:errors.append(name+'/'+side+': eixo espada')
            if entry['fio_max']>20:errors.append(name+'/'+side+': fio fora do corte')
        print(name,'braços',round(min(gaps)[0],2),'eixo/fio',[(round(c['eixo_max'],2),round(c['fio_max'],1)) for c in report[name]['cortes']],flush=True)
    # A ponta deve ganhar velocidade depois de carregar; não basta encurtar todo o clipe.
    for name in ['attack_low','attack_right']:
        a=np.array(report[name]['cortes'][0]['velocidade_ponta']);peak=float(a[:,3].max());early=float(np.mean(a[:max(2,len(a)//5),3]))
        report[name]['aceleracao']={'pico':peak,'media_inicio':early,'razao':peak/early}
        if peak/early<1.5:errors.append(name+': aceleração insuficiente')
    # Os dois golpes finais efetivamente tocam o solo durante a aterrissagem.
    mat=rig.mats(reader.pose('attack_combo',v.LANDING));ends={}
    for side in v.SIDES:
        w=rig.weapons[side];wm=mat[w['name']];ends[side]=float((rig.weaponverts[side]@wm[:3,:3].T+v.point(wm,w['grip']))[:,1].min())
    report['impacto_laminas_y']=ends
    if any(abs(y)>.1 for y in ends.values()):errors.append('combo: lâminas não chegam juntas ao chão')
    report['erros']=errors;return report


def sheet(v,m,reader,path):
    times=[.27,.45,.55,.67,.80,.97,1.10,1.23,1.45]
    canvas=Image.new('RGB',(768,768),(238,242,244));draw=ImageDraw.Draw(canvas)
    for i,t in enumerate(times):
        mat=v.bbmodelo.matrizes_ossos(m,reader.pose('attack_combo',t));im,*_=v.render.renderizar(m,vista=(35,12),mats=mat,escala=3,fundo=(238,242,244))
        a=np.asarray(im);ys,xs=np.where(np.any(a[:,:,:3]!=[238,242,244],axis=2));im=im.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1));im.thumbnail((250,225));x=i%3*256;y=i//3*256
        canvas.paste(im,(x+(256-im.width)//2,y+26+(225-im.height)//2));draw.text((x+5,y+6),f'combo {t:.2f}s',fill=(20,35,45))
    canvas.save(path)


def study(v):
    v.OUT.mkdir(parents=True,exist_ok=True);(v.OUT/'_cache').mkdir(exist_ok=True)
    m=v.bbmodelo.ler(v.SOURCE);rig=v.Rig(m);prior=v.module('revisao_v4','revisar-golpes-pavao-f3-v4.py');old=v.module('espacial_v5','revisar-golpes-pavao-f3.py')
    r=mechanics(v,m,rig,rate=48);r['movimento']=motion(v,m,rig,rate=36);r['cotovelos']=prior.wing_chest(v,m,rig,rate=30);r['espacial']=old.spatial(v,m,rig,rate=30)
    v.g.dump(v.OUT/'_cache/estudo.json',r);sheet(v,m,rig,v.OUT/'_cache/poses-estudo.png')


def check(v):
    src=v.bbmodelo.ler(v.SOURCE);m=v.bbmodelo.ler(v.FILE)
    for field in ['elements','groups','textures','outliner']:assert src.bruto[field]==m.bruto[field],field
    def canonical(a):
        a=copy.deepcopy(a);a['animators']={k:x for k,x in a['animators'].items() if x.get('keyframes')};return a
    preserved=[]
    for a in src.animacoes:
        if a['name'] in ['attack_low','attack_cross']:continue
        assert canonical(a)==canonical(next(b for b in m.animacoes if b['uuid']==a['uuid'])),a['name'];preserved.append(a['name'])
    assert len(m.animacoes)==23
    saved=v.Saved(m);native=v.base.native.NativeSaved(saved);r={'fonte_sha256':v.g.sha(v.SOURCE),'saida_sha256':v.g.sha(v.FILE),'geometria_rig_uv_textura_preservados':True,'clipes_preservados':preserved}
    r['linear']=mechanics(v,m,saved,rate=240);r['nativo']=mechanics(v,m,native,rate=240,offset=.00047);r['nativo_segunda_fase']=mechanics(v,m,native,rate=240,offset=.00219)
    r['movimento']=motion(v,m,native);prior=v.module('revisao_v4','revisar-golpes-pavao-f3-v4.py');r['cotovelos']=prior.wing_chest(v,m,native,rate=60)
    old=v.module('espacial_v5','revisar-golpes-pavao-f3.py');r['espacial']=old.spatial(v,m,saved,rate=48);r['conexoes']=[];rig=v.Rig(m)
    for n,d in v.CLIPS.items():
        for t in [0,d]:
            mat=rig.mats(saved.pose(n,t));e=max(float(abs(mat[k]-rig.guardmat[k]).max()) for k in mat);assert e<.001,(n,t,e);r['conexoes'].append([n,t,e])
    r['erros']=sum((r[k]['erros'] for k in ['linear','nativo','nativo_segunda_fase','movimento','cotovelos']),[])
    for n,x in r['espacial'].items():
        if x['nova_penetracao_lamina_corpo'][0]>.35:r['erros'].append(n+': espada entra no corpo')
        if x['min_superficie_opaca_y'][0]<-.06:r['erros'].append(n+': superfície sob o piso')
    r['ok']=not r['erros'];v.g.dump(v.OUT/'validacao-ataques.json',r);print('Resultado:',r['ok'],r['erros'],flush=True)
    if not r['ok']:raise SystemExit(1)


def capture(v):
    helper=v.module('captura_nativa_v5','previas-corrida-pavao-f3.py');client=helper.Client(v.ROOT);info=client.call('get_project_info');data=info.get('structuredContent') or json.loads(info['content'][0]['text'])
    from pathlib import Path
    assert Path(data['project']['save_path']).resolve()==v.FILE.resolve()
    view='golpes_f3_v5_preview';client.call('create_offscreen_view',id=view,width=640,height=560,antialias=False,copy_view='none');counts={}
    tracks={n:(n,[155,95,-230],[0,35 if n=='attack_combo' else 28,-2]) for n in v.CLIPS}
    tracks['attack_combo-front']=('attack_combo',[0,48,-290],[0,38,0]);cleanup='ok'
    try:
        client.call('animation_timeline',action='pause',animation_id='attack_combo')
        for key,(name,pos,target) in tracks.items():
            client.call('set_camera_angle',view=view,projection='perspective',position=pos,target=target,fov=37,max_size=640)
            d=v.CLIPS[name];n=round(d*30);sequence=[(name,float(t),f'{key} | {t:.2f}s') for t in np.arange(n)*d/n]
            counts[key]=helper.gif(v,client,view,sequence,v.OUT/(key+'.gif'),fps=n/d);print('Prévia nativa:',key,counts[key],'quadros',flush=True)
        canvas=Image.new('RGB',(768,768),(238,242,244));draw=ImageDraw.Draw(canvas)
        samples=[('attack_low',.54),('attack_right',.50),('attack_left',.50)]+[('attack_combo',t) for t in [.45,.60,.78,.97,1.10,1.23]]
        for i,(key,t) in enumerate(samples):
            d=v.CLIPS[key];frame=min(counts[key]-1,round(t*counts[key]/d))
            with Image.open(v.OUT/(key+'.gif')) as gif:gif.seek(frame);im=gif.convert('RGB')
            im.thumbnail((250,226));x=i%3*256;y=i//3*256;canvas.paste(im,(x+(256-im.width)//2,y+26+(226-im.height)//2));draw.text((x+5,y+6),f'{key} {frame*d/counts[key]:.2f}s',fill=(20,35,45))
        canvas.save(v.OUT/'poses-nativas.png')
    finally:
        try:client.call('delete_offscreen_view',view=view)
        except RuntimeError as e:
            if 'onContextMenu is not defined' not in str(e):raise
            cleanup='registro removido; erro conhecido do listener onContextMenu'
        finally:client.call('animation_timeline',action='set_time',animation_id='attack_combo',time=0)
    v.g.dump(v.OUT/'previas-nativas.json',{'saida_sha256':v.g.sha(v.FILE),'quadros':counts,'cameras':tracks,'camera_fixa_por_clipe':True,'limpeza_view':cleanup})
