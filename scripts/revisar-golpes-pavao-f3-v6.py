"""Conferência da revisão curta dos golpes, com Low e base do combo protegidos."""
import copy
import json
import math
import numpy as np
from PIL import Image,ImageDraw


def requests(v,m,reader):
    rig=reader if isinstance(reader,v.Rig) else v.Rig(m);old=v.Saved(v.bbmodelo.ler(v.SOURCE));report={};errors=[]
    if isinstance(reader,v.base.native.NativeSaved):old=v.base.native.NativeSaved(old)
    def speeds(r,name,a,b):
        weapon=rig.weapons['left'];q=weapon['grip']+weapon['frame'][:,1]*weapon['length']*.85;rows=[]
        for t in np.linspace(a,b,81):
            x=rig.mats(r.pose(name,float(t-.0005)));y=rig.mats(r.pose(name,float(t+.0005)))
            rows.append([float(t),float(np.linalg.norm(v.point(y[weapon['name']],q)-v.point(x[weapon['name']],q))/.001)])
        return np.array(rows)
    a,b=v.ACTIVE['attack_left'][0][1:];now=speeds(reader,'attack_left',a,b);before=speeds(old,'attack_left',.31,.53)
    ratio=float(now[:,1].max()/before[:,1].max());gain=float(now[:,1].max()/now[:16,1].mean())
    report['left']={'pico_v5':float(before[:,1].max()),'pico_v6':float(now[:,1].max()),'ganho_pico':ratio,'pico_sobre_inicio':gain}
    if ratio<1.35 or gain<1.5:errors.append('Left: aceleração insuficiente')
    wait=v.inverse_time('attack_right',.80)-v.inverse_time('attack_right',.60)
    report['right']={'intervalo_v5':[.60,.80],'intervalo_v6':[v.inverse_time('attack_right',.60),v.inverse_time('attack_right',.80)],'duracao_intervalo':wait}
    if wait>.08+1e-6:errors.append('Right: espera ainda longa')
    combo=[]
    for t in np.linspace(1.04,1.32,65):
        mat=rig.mats(reader.pose('attack_combo',float(t)));src=rig.mats(old.pose('attack_combo',float(t)));directions=[];tips=[];oldtips=[]
        for side in v.SIDES:
            w=rig.weapons[side];wm=mat[w['name']];d=wm[:3,:3]@w['frame'][:,1];directions.append(d)
            tip=w['grip']+w['frame'][:,1]*w['length'];tips.append(v.point(wm,tip));oldtips.append(v.point(src[w['name']],tip))
        angle=math.degrees(math.acos(float(np.clip(directions[0]@directions[1],-1,1))))
        combo.append([float(t),angle,float(abs(tips[0][0]-tips[1][0])),float(abs(oldtips[0][0]-oldtips[1][0]))])
    report['combo']={'amostras_t_angulo_abertura_v6_v5':combo,'angulo_max':max(x[1] for x in combo),
        'abertura_media_v6':float(np.mean([x[2] for x in combo])),'abertura_media_v5':float(np.mean([x[3] for x in combo]))}
    if report['combo']['angulo_max']>3:errors.append('Combo: lâminas ainda divergentes')
    if report['combo']['abertura_media_v6']>.70*report['combo']['abertura_media_v5']:errors.append('Combo: fechamento insuficiente')
    report['erros']=errors;print('Ajustes:',errors or 'OK','Left',round(ratio,2),'vezes; pausa',round(wait,3),'s; paralelo',round(report['combo']['angulo_max'],2),'graus',flush=True)
    return report


def study(v):
    v.OUT.mkdir(parents=True,exist_ok=True);(v.OUT/'_cache').mkdir(exist_ok=True)
    m=v.bbmodelo.ler(v.SOURCE);rig=v.Rig(m);prior=v.module('revisao_v5','revisar-golpes-pavao-f3-v5.py');wings=v.module('revisao_v4','revisar-golpes-pavao-f3-v4.py')
    r=prior.mechanics(v,m,rig,rate=60);r['movimento']=prior.motion(v,m,rig,rate=36);r['ajustes']=requests(v,m,rig)
    r['cotovelos']=wings.wing_chest(v,m,rig,rate=30);old=v.module('espacial_golpes','revisar-golpes-pavao-f3.py');r['espacial']=old.spatial(v,m,rig,rate=30)
    v.g.dump(v.OUT/'_cache/estudo.json',r)


def check(v):
    src=v.bbmodelo.ler(v.SOURCE);m=v.bbmodelo.ler(v.FILE);r={'fonte_sha256':v.g.sha(v.SOURCE),'saida_sha256':v.g.sha(v.FILE)}
    for field in ['elements','groups','textures','outliner']:assert src.bruto[field]==m.bruto[field],field
    def canonical(a):
        a=copy.deepcopy(a);a['animators']={k:x for k,x in a['animators'].items() if x.get('keyframes')};return a
    preserved=[]
    for a in src.animacoes:
        if a['name'] in ['attack_left','attack_right','attack_combo']:continue
        assert canonical(a)==canonical(next(b for b in m.animacoes if b['uuid']==a['uuid'])),a['name'];preserved.append(a['name'])
    assert len(m.animacoes)==23 and len(preserved)==20
    old_combo=next(a for a in src.animacoes if a['name']=='attack_combo');new_combo=next(a for a in m.animacoes if a['name']=='attack_combo')
    for bone in m.ossos:
        uuid=m.ossos[bone].uuid;a=old_combo['animators'].get(uuid,{});b=new_combo['animators'].get(uuid,{})
        changed=v.COMBO_CHANNELS.get(bone,[])
        for channel in ['rotation','position','scale']:
            before=[k for k in a.get('keyframes',[]) if k['channel']==channel];after=[k for k in b.get('keyframes',[]) if k['channel']==channel]
            if channel not in changed:assert before==after,(bone,channel)
            else:
                outside=lambda rows:[k for k in rows if k['time']<v.CLOSE_START or k['time']>v.CLOSE_END]
                assert outside(before)==outside(after),(bone,channel,'fora da janela')
    r.update(clipes_preservados=preserved,geometria_rig_uv_textura_preservados=True,combo_canais_restritos=True)
    saved=v.Saved(m);native=v.base.native.NativeSaved(saved);prior=v.module('revisao_v5','revisar-golpes-pavao-f3-v5.py')
    r['linear']=prior.mechanics(v,m,saved,rate=240);r['nativo']=prior.mechanics(v,m,native,rate=240,offset=.00047);r['nativo_segunda_fase']=prior.mechanics(v,m,native,rate=240,offset=.00219)
    r['movimento']=prior.motion(v,m,native);r['ajustes']=requests(v,m,native)
    wings=v.module('revisao_v4','revisar-golpes-pavao-f3-v4.py');r['cotovelos']=wings.wing_chest(v,m,native,rate=60)
    old=v.module('espacial_golpes','revisar-golpes-pavao-f3.py');r['espacial']=old.spatial(v,m,saved,rate=48)
    r['erros']=sum((r[k]['erros'] for k in ['linear','nativo','nativo_segunda_fase','movimento','ajustes','cotovelos']),[])
    for n,x in r['espacial'].items():
        if x['nova_penetracao_lamina_corpo'][0]>.35:r['erros'].append(n+': espada entra no corpo')
        if x['min_superficie_opaca_y'][0]<-.06:r['erros'].append(n+': superfície sob o piso')
    r['ok']=not r['erros'];v.g.dump(v.OUT/'validacao-ataques.json',r);print('Resultado:',r['ok'],r['erros'],flush=True)
    if not r['ok']:raise SystemExit(1)


def capture(v):
    helper=v.module('captura_nativa','previas-corrida-pavao-f3.py');client=helper.Client(v.ROOT);info=client.call('get_project_info');data=info.get('structuredContent') or json.loads(info['content'][0]['text'])
    from pathlib import Path
    assert Path(data['project']['save_path']).resolve()==v.FILE.resolve()
    view='golpes_f3_v6_preview';client.call('create_offscreen_view',id=view,width=640,height=560,antialias=False,copy_view='none');counts={};cleanup='ok'
    tracks={n:(n,[155,95,-230],[0,35 if n=='attack_combo' else 28,-2]) for n in ['attack_left','attack_right','attack_combo']}
    tracks['attack_combo-front']=('attack_combo',[0,48,-290],[0,38,0]);tracks['attack_combo-top']=('attack_combo',[0,240,-70],[0,25,-10])
    try:
        client.call('animation_timeline',action='pause',animation_id='attack_combo')
        for key,(name,pos,target) in tracks.items():
            client.call('set_camera_angle',view=view,projection='perspective',position=pos,target=target,fov=37,max_size=640)
            d=v.CLIPS[name];n=round(d*30);sequence=[(name,float(t),f'{key} | {t:.2f}s') for t in np.arange(n)*d/n]
            counts[key]=helper.gif(v,client,view,sequence,v.OUT/(key+'.gif'),fps=n/d);print('Prévia nativa:',key,counts[key],'quadros',flush=True)
        canvas=Image.new('RGB',(768,768),(238,242,244));draw=ImageDraw.Draw(canvas)
        samples=[('attack_left',.34),('attack_left',.43),('attack_left',.51),('attack_right',.59),('attack_right',.70),('attack_right',.86),('attack_combo-top',1.06),('attack_combo-top',1.20),('attack_combo-top',1.32)]
        for i,(key,t) in enumerate(samples):
            name=tracks[key][0];d=v.CLIPS[name];frame=min(counts[key]-1,round(t*counts[key]/d))
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
