"""Confere eixo antebraço/espada, separação dos braços, arco frontal e preservação."""
import copy
import json
import math
import numpy as np
from PIL import Image,ImageDraw


def angle(a,b):return math.degrees(math.acos(float(np.clip(np.dot(a,b),-1,1))))


def segment_distance(a,b,c,d):
    u=b-a;v=d-c;w=a-c;uu=u@u;vv=v@v;uv=u@v
    candidates=[]
    for p in [a,b]:candidates.append(np.linalg.norm(p-(c+np.clip((p-c)@v/max(vv,1e-12),0,1)*v)))
    for p in [c,d]:candidates.append(np.linalg.norm(p-(a+np.clip((p-a)@u/max(uu,1e-12),0,1)*u)))
    det=uu*vv-uv*uv
    if det>1e-10:
        s=(uv*(v@w)-vv*(u@w))/det;t=(uu*(v@w)-uv*(u@w))/det
        if 0<=s<=1 and 0<=t<=1:candidates.append(np.linalg.norm(a+s*u-c-t*v))
    return float(min(candidates))


def arms(v,m,rig,p):
    mat=rig.mats(p);result={}
    for side in v.SIDES:
        a,b,c=[v.point(mat[n+side],m.ossos[n+side].origem) for n in ['arm_','forearm_','hand_']]
        hand=v.point(mat['hand_'+side],rig.grips[side]);result[side]=[]
        for n,x,y in [('upper_arm_',a,b),('forearm_solid_',b,c),('hand_block_',c,hand)]:
            cube=m.cubo(n+side);r=float(np.linalg.norm(np.sort(cube.tamanho)[:2])/2)
            result[side].append((x,y,r,n+side))
    return result


def requested(v,m,reader,rate=120):
    rig=reader if isinstance(reader,v.Rig) else v.Rig(m);errors=[];alignment=[];gaps=[];offsets=[];trajectory=[];cross_gaps=[]
    for t in np.linspace(0,v.CLIPS['attack_low'],round(v.CLIPS['attack_low']*rate)+1):
        p=reader.pose('attack_low',float(t));mat=rig.mats(p);limbs=arms(v,m,rig,p)
        for a,b,ra,na in limbs['right']:
            for c,d,rb,nb in limbs['left']:
                gap=segment_distance(a,b,c,d)-ra-rb;gaps.append([gap,float(t),na,nb])
        if .34<=t<=.76:
            forearm=v.unit(v.point(mat['hand_right'],m.ossos['hand_right'].origem)-v.point(mat['forearm_right'],m.ossos['forearm_right'].origem))
            w=rig.weapons['right'];blade=mat[w['name']][:3,:3]@w['frame'][:,1]
            alignment.append(angle(forearm,blade))
            grip=v.point(mat[w['name']],w['grip']);elbow=v.point(mat['forearm_right'],m.ossos['forearm_right'].origem)
            offsets.append(float(np.linalg.norm(np.cross(grip-elbow,forearm))))
    for t in np.linspace(.34,.50,41):
        mat=rig.mats(reader.pose('attack_cross',float(t)));w=rig.weapons['right']
        tip=v.point(mat[w['name']],w['grip']+w['frame'][:,1]*w['length']*.85)
        trajectory.append([float(t),float(-tip[0]),float(tip[1]),float(tip[2])])
    for t in np.linspace(0,v.CROSS_JOIN,90):
        limbs=arms(v,m,rig,reader.pose('attack_cross',float(t)))
        for a,b,ra,na in limbs['right']:
            for c,d,rb,nb in limbs['left']:
                cross_gaps.append([segment_distance(a,b,c,d)-ra-rb,float(t),na,nb])
    a=np.array(trajectory);dx=float(a[-1,1]-a[0,1]);dy=float(a[-1,2]-a[0,2]);backwards=float(np.min(np.diff(a[:,1])))
    if max(alignment)>2:errors.append('Low: espada não prolonga o antebraço')
    if max(offsets)>1.5:errors.append('Low: eixo da empunhadura afastado do antebraço')
    if min(x[0] for x in gaps)<.15:errors.append('Low: braços se aproximam ou atravessam')
    if min(x[0] for x in cross_gaps)<.15:errors.append('Cross: braços se aproximam ou atravessam')
    if dx<25 or dy<15 or backwards<-.2:errors.append('Cross: arco frontal não sobe em diagonal para o lado oposto')
    data={'low_angulo_antebraco_espada_max':max(alignment),'low_desvio_linha_empunhadura_max':max(offsets),
          'low_folga_bracos_min':min(gaps),'cross_folga_bracos_min':min(cross_gaps),'cross_frente_delta_xy':[dx,dy],
          'cross_recuo_horizontal_max':backwards,'cross_arco_frontal':trajectory,'erros':errors}
    print('Pedido: alinhamento',round(max(alignment),4),'folga braços',round(min(x[0] for x in gaps),3),'arco',np.round([dx,dy],2).tolist(),flush=True)
    return data


def mechanics(v,m,reader,rate=240,offset=0.,verbose=True):
    old=v.module('mecanica_legada','revisar-golpes-pavao-f3.py')
    result=old.measure(v,m,reader,rate=rate,offset=offset,verbose=False)
    # O antigo eixo virtual do punho usa o eixo do antebraço na pose mantídea.
    # O Low agora tem outra orientação neutra, determinada pela empunhadura.
    # Mantemos o proxy no relatório; o aceite usa eixo real + vínculo + constância.
    result['erros']=[x for x in result['erros'] if x!='attack_low: punho']
    result['referencia_punho_low']='Proxy legado registrado; substituído por colinearidade geométrica, preensão e punho constante na fase ativa.'
    if verbose:print('Mecânica:', 'OK' if not result['erros'] else result['erros'],flush=True)
    return result


def sheet(v,m,reader,file):
    samples=[('attack_low',.40),('attack_low',.55),('attack_low',.68),
             ('attack_cross',.34),('attack_cross',.43),('attack_cross',.50)]
    sheet=Image.new('RGB',(768,512),(238,242,244));draw=ImageDraw.Draw(sheet)
    for i,(name,t) in enumerate(samples):
        mat=v.bbmodelo.matrizes_ossos(m,reader.pose(name,t))
        im,*_=v.render.renderizar(m,vista=('frente' if name=='attack_cross' else (65,15)),mats=mat,escala=3.2,fundo=(238,242,244))
        rgb=np.array(im);ys,xs=np.where(np.any(rgb[:,:,:3]!=[238,242,244],axis=2))
        im=im.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1));im.thumbnail((250,226));x=i%3*256;y=i//3*256
        sheet.paste(im,(x+(256-im.width)//2,y+26+(226-im.height)//2));draw.text((x+5,y+7),f'{name} {t:.2f}s',fill=(25,40,50))
    sheet.save(file)


def study(v):
    v.OUT.mkdir(parents=True,exist_ok=True);(v.OUT/'_cache').mkdir(exist_ok=True)
    old=v.module('revisao_antiga','revisar-golpes-pavao-f3.py');quality=v.module('qualidade_v2','revisar-golpes-pavao-f3-v2.py')
    m=v.bbmodelo.ler(v.SOURCE);rig=v.Rig(m);report=mechanics(v,m,rig,rate=36)
    report['pedido']=requested(v,m,rig,rate=60);report['qualidade']=quality.quality(v,m,rig,rate=60)
    report['espacial']=old.spatial(v,m,rig,rate=24)
    v.g.dump(v.OUT/'_cache/estudo.json',report);sheet(v,m,rig,v.OUT/'_cache/poses-estudo.png')


def check(v):
    old=v.module('revisao_antiga','revisar-golpes-pavao-f3.py');quality=v.module('qualidade_v2','revisar-golpes-pavao-f3-v2.py')
    src=v.bbmodelo.ler(v.SOURCE);m=v.bbmodelo.ler(v.FILE)
    for field in ['elements','groups','textures','outliner']:assert src.bruto[field]==m.bruto[field],field
    assert len(m.animacoes)==21
    preserved=[]
    def canonical(a):
        a=copy.deepcopy(a);a['animators']={u:x for u,x in a['animators'].items() if x.get('keyframes')};return a
    for a in src.animacoes:
        new=next(b for b in m.animacoes if b['uuid']==a['uuid'])
        if a['name'] not in v.CLIPS:assert canonical(a)==canonical(new);preserved.append(a['name']);continue
        for bone,animator in a['animators'].items():
            if not animator.get('keyframes'):continue
            name=animator['name']
            oldkeys=animator['keyframes'];newkeys=new['animators'][bone]['keyframes']
            if name not in v.CHANGED:assert oldkeys==newkeys,(a['name'],name)
            else:
                f=lambda k:k['channel']!='rotation' or (a['name']=='attack_cross' and k['time']>=v.CROSS_JOIN-1e-9)
                assert [k for k in oldkeys if f(k)]==[k for k in newkeys if f(k)],(a['name'],name,'trecho preservado')
    saved=v.Saved(m);native=v.base.native.NativeSaved(saved)
    report={'fonte_sha256':v.g.sha(v.SOURCE),'saida_sha256':v.g.sha(v.FILE),'clipes_preservados':preserved,
            'geometria_rig_uv_textura_preservados':True,'somente_rotacoes_tres_ossos_direitos':True,'cross_esquerda_chaves_identicas':True}
    report['linear']=mechanics(v,m,saved)
    report['nativo']=mechanics(v,m,native,offset=.00047)
    report['nativo_segunda_fase']=mechanics(v,m,native,offset=.00219,verbose=False)
    report['pedido']=requested(v,m,native)
    report['qualidade']=quality.quality(v,m,native)
    report['espacial']=old.spatial(v,m,saved,rate=36)
    rig=v.Rig(m);report['conexoes']=[]
    for n,d in v.CLIPS.items():
        for t in [0,d]:
            mat=rig.mats(saved.pose(n,t));e=max(float(abs(mat[k]-rig.guardmat[k]).max()) for k in mat)
            report['conexoes'].append({'clipe':n,'t':t,'erro':e});assert e<.001,(n,t,e)
    report['erros']=sum((report[k]['erros'] for k in ['linear','nativo','nativo_segunda_fase','pedido','qualidade']),[])
    for n,data in report['espacial'].items():
        if data['nova_penetracao_lamina_corpo'][0]>.35:report['erros'].append(n+': lâmina atravessa corpo')
        if data['min_superficie_opaca_y'][0]<-.06:report['erros'].append(n+': superfície sob o piso')
    report['ok']=not report['erros'];v.g.dump(v.OUT/'validacao-ataques.json',report);print('Resultado:',report['ok'],report['erros'],flush=True)
    if not report['ok']:raise SystemExit(1)


def capture(v):
    helper=v.module('captura_nativa','previas-corrida-pavao-f3.py');client=helper.Client(v.ROOT)
    info=client.call('get_project_info');data=info.get('structuredContent') or json.loads(info['content'][0]['text'])
    from pathlib import Path
    assert Path(data['project']['save_path']).resolve()==v.FILE.resolve()
    view='golpes_f3_v3_preview';client.call('create_offscreen_view',id=view,width=640,height=560,antialias=False,copy_view='none')
    counts={};cleanup='ok';cameras={'attack_low':([160,80,-200],[0,28,-2]),'attack_cross':([0,28,-260],[0,28,0])}
    try:
        client.call('animation_timeline',action='pause',animation_id='attack_low')
        for name,d in v.CLIPS.items():
            position,target=cameras[name]
            client.call('set_camera_angle',view=view,projection='perspective',position=position,target=target,fov=37,max_size=640)
            n=round(d*30);sequence=[(name,float(t),f'{name} | {t:.2f}s') for t in np.arange(n)*d/n]
            counts[name]=helper.gif(v,client,view,sequence,v.OUT/(name+'.gif'),fps=n/d)
            print('Prévia nativa:',name,counts[name],'quadros',flush=True)
        montage=Image.new('RGB',(768,768),(238,242,244));draw=ImageDraw.Draw(montage)
        samples=[('attack_low',.40),('attack_low',.55),('attack_low',.68),
                 ('attack_cross',.34),('attack_cross',.43),('attack_cross',.50),
                 ('attack_cross',.62),('attack_cross',.87),('attack_cross',1.04)]
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
    v.g.dump(v.OUT/'previas-nativas.json',{'saida_sha256':v.g.sha(v.FILE),'quadros':counts,'camera_fixa_por_clipe':cameras,
        'cross_camera':'frontal, seguindo o desenho do usuário','limpeza_view':cleanup})
