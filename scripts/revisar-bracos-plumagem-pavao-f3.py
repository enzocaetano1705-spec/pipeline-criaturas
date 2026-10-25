"""F3 v4: braços humanoides sem dedos, espadas-penas e plumagem real da F2."""
import argparse
import copy
import importlib.util
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image
from criaturas import bbmodelo, motor, ops, render, roblox_infra, texturizar

ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('identidade_f3',ROOT/'scripts/revisar-identidade-pavao-f3.py')
base=importlib.util.module_from_spec(sp);sp.loader.exec_module(base)
OUT=ROOT/'modelos/criatura-pavao/f3/revisao-v4'
SOURCE=OUT/'origem-aberta.bbmodel'
FILE=OUT/'criatura-pavao-e3-v4.bbmodel'
F2=base.F2


def unit(a):
    a=np.asarray(a,float);return a/np.linalg.norm(a)


def frame(axis,normal):
    axis=unit(axis);normal=np.asarray(normal,float)
    normal=unit(normal-axis*(axis@normal))
    return np.column_stack([normal,np.cross(axis,normal),axis])


def build(m,f2):
    batch=[{'op':'set_model_properties','name':FILE.stem}]
    arms=base.descendants(m,'arm_left')|base.descendants(m,'arm_right')
    head=base.descendants(m,'head')
    upper=base.descendants(m,'waist')-arms-head
    tails=base.descendants(m,'tail_1')
    lean=base.transform(np.array([0,26.5,0]),[-6,0,0])
    tail=base.transform(m.ossos['tail_1'].origem,[-6,0,0])
    head_shift=bbmodelo.aplicar(lean,[m.ossos['head'].origem])[0]-m.ossos['head'].origem
    translation=np.eye(4);translation[:3,3]=head_shift
    batch += [{'op':'remove_node','target':m.ossos[n].uuid} for n in ['arm_left','arm_right']]
    for c in m.cubos:
        if c.osso in arms:continue
        mat=translation if c.osso in head else lean if c.osso in upper else tail if c.osso in tails else None
        if mat is not None:batch.append(base.move_cube(c,mat))
    for n,o in m.ossos.items():
        if n in arms:continue
        mat=translation if n in head else lean if n in upper else tail if n in tails else None
        if mat is not None:
            batch.append({'op':'update_node','target':o.uuid,'origin':bbmodelo.aplicar(mat,[o.origem])[0].tolist()})
    # A aba aberta era a prévia anterior aos pivôs corrigidos da v3b.
    for side in ['left','right']:
        batch.append({'op':'update_node','target':'shin_'+side,'origin':m.cubo('shank_'+side).origem.tolist()})
    for loc in m.locators:
        if loc.osso in arms:continue
        mat=translation if loc.osso in head else lean if loc.osso in upper else tail if loc.osso in tails else None
        if mat is not None:
            elem=next(e for e in m.bruto['elements'] if e.get('type')=='locator' and e['name']==loc.nome)
            batch.extend([{'op':'remove_node','target':elem['uuid']},
                          {'op':'add_locator','name':loc.nome,'parent':loc.osso,
                           'position':bbmodelo.aplicar(mat,[loc.posicao])[0].tolist()}])
    cubes=[];kinds={};decors=[];grips={}
    def group(n,p,a):batch.append({'op':'add_group','name':n,'parent':p,'origin':list(a)})
    def box(n,p,c,size,r=None,kind='arm'):
        c=np.asarray(c,float);h=np.asarray(size,float)/2
        cubes.append({'nome':n,'osso':p,'from':(c-h).tolist(),'to':(c+h).tolist(),
                      'origin':c.tolist(),'rotation':base.forms.euler(r) if r is not None else [0,0,0]})
        kinds[n]=kind
    def segment(n,p,a,b,w,d,kind='arm'):
        a,b=np.asarray(a,float),np.asarray(b,float)
        box(n,p,(a+b)/2,[w,np.linalg.norm(b-a),d],base.forms.alinhar([0,1,0],b-a),kind)
    def feather(n,parent,template,root,axis,normal,length):
        source=f2.cubo(template);factor=length/source.tamanho[2];width=source.tamanho[1]*factor
        r=frame(axis,normal);root=np.array(root,float)
        faces=copy.deepcopy(source.faces)
        for face in faces.values():
            face['uv'][0]+=256;face['uv'][2]+=256
            if face.get('texture') is not None:face['texture']=0
        batch.append({'op':'add_cube','name':n,'parent':parent,
                      'from':(root+[0,-width/2,0]).tolist(),'to':(root+[0,width/2,length]).tolist(),
                      'origin':root.tolist(),'rotation':base.forms.euler(r),'box_uv':False,
                      'inflate':source.inflate,'faces':faces})
        decors.append({'nome':n,'fonte_f2':template,'pai':parent,'raiz':root.tolist(),
                       'ponta':(root+unit(axis)*length).tolist(),'fator':factor,'comprimento':length})
    mats=bbmodelo.matrizes_ossos(m);rib=m.cubo('ribcage')
    for side,s in [('left',-1),('right',1)]:
        shoulder=bbmodelo.aplicar(lean,[m.ossos['arm_'+side].origem])[0]
        elbow=shoulder+[s*2.5,-7.6,1.4]
        wrist=elbow+[s*1.8,-6.2,-3.0]
        forearm=unit(wrist-elbow);grip=wrist+forearm*1.25
        group('arm_'+side,'torso',shoulder)
        group('forearm_'+side,'arm_'+side,elbow)
        group('hand_'+side,'forearm_'+side,wrist)
        group('feather_sword_'+side,'hand_'+side,grip)
        group('wing_'+side,'forearm_'+side,elbow)
        segment('upper_arm_'+side,'arm_'+side,shoulder,elbow,3.4,3.5)
        segment('forearm_solid_'+side,'forearm_'+side,elbow,wrist,2.9,3.0)
        box('hand_block_'+side,'hand_'+side,grip,[2.8,2.8,2.6],base.forms.alinhar([0,-1,0],forearm),'hand')
        # Espadas simétricas em guarda, com haste, pequena guarda e ponta definida.
        axis=unit([s*.42,.67,-.61]);normal=unit([0,.67,.74])
        normal=unit(normal-axis*(axis@normal));across=unit(np.cross(axis,normal))
        blade_frame=np.column_stack([across,axis,normal])
        segment('sword_handle_'+side,'feather_sword_'+side,grip-axis*1.9,grip+axis*3.3,1.0,1.0,'handle')
        box('sword_guard_'+side,'feather_sword_'+side,grip+axis*2.7,[5.0,.8,1.2],blade_frame,'guard')
        box('sword_pommel_'+side,'feather_sword_'+side,grip-axis*2.15,[1.3,1.0,1.3],blade_frame,'guard')
        blade_root=grip+axis*3.1
        box('feather_blade_'+side,'feather_sword_'+side,blade_root+axis*15,[5,30,0],blade_frame,'blade')
        grips[side]={'pegada':grip.tolist(),'base':blade_root.tolist(),'ponta':(blade_root+axis*30).tolist()}
        for label,point in [('hand',grip),('weapon_base',blade_root),('weapon_tip',blade_root+axis*30)]:
            batch.append({'op':'add_locator','name':'loc_'+label+'_'+side,
                          'parent':('hand_' if label=='hand' else 'feather_sword_')+side,'position':point.tolist()})
        # O leque menor da F2 acompanha o cotovelo da F3.
        small=['wing_left_feather_7','wing_left_feather_3','wing_left_feather_2'] if s<0 else [
            'wing_right_feather_4','wing_right_feather_5','wing_right_feather_6']
        for j,(template,axis) in enumerate(zip(small,[[s*.12,.72,.68],[s*.19,.43,.88],[s*.25,.1,.96]]),1):
            feather(f'elbow_wing_{side}_{j}','wing_'+side,template,
                    elbow+[s*.6,.15,0.3],axis,[s*1,.1,.25],12)
        # Seis penas longas da F2 cobrem o dorso a partir das escápulas.
        local=rib.de+rib.tamanho*np.array([.5+s*.32,.76,.92])
        back_root=bbmodelo.aplicar(lean@bbmodelo.matriz_cubo(m,rib,mats),[local])[0]
        group('back_feathers_'+side,'torso',back_root)
        large=['wing_left_feather_8','wing_left_feather_9','wing_left_feather_1'] if s<0 else [
            'wing_right_feather_7','wing_right_feather_8','wing_right_feather_9']
        for j,(template,axis,length) in enumerate(zip(large,
              [[s*.52,-.37,.77],[s*.4,-.56,.72],[s*.24,-.75,.62]],[24,25,26]),1):
            feather(f'back_wing_feather_{side}_{j}','back_feathers_'+side,template,
                    back_root+[s*1.0 if j==3 else 0,-(j-1)*.55,(j-1)*.22],axis,[s*.45,.7,.55],length)
    offsets,_=ops.distribuir_uv(cubes,margem=2,larguras=(256,))
    for c in cubes:
        batch.append({'op':'add_cube','name':c['nome'],'parent':c['osso'],'from':c['from'],'to':c['to'],
                      'origin':c['origin'],'rotation':c['rotation'],'box_uv':True,
                      'uv_offset':[offsets[c['nome']][0]+256,offsets[c['nome']][1]+256]})
    return batch,kinds,decors,grips,head_shift


def feather_raster(f2):
    # Amostra a própria pena longa da F2, preservando o motivo de pavão e suas cores.
    c=f2.cubo('wing_left_feather_1');face='east';corners=np.array([
        [([c.de,c.ate][i])[0],([c.de,c.ate][j])[1],([c.de,c.ate][k])[2]]
        for i,j,k in render.CANTOS_FACE[face]])
    u1,v1,u2,v2=c.faces[face]['uv'];e1=corners[1]-corners[0];e2=corners[2]-corners[0]
    raster=np.zeros((32,6,4),np.uint8);atlas=np.array(f2.textura)
    for y in range(32):
        for x in range(6):
            p=c.de+[0,x+.5,y+.5];q=p-corners[0]
            u=u1+(u2-u1)*(q@e1)/(e1@e1);v=v1+(v2-v1)*(q@e2)/(e2@e2)
            raster[y,x]=atlas[int(v),int(u)]
    good=np.argwhere(raster[:,:,3]>127)
    for y,x in np.argwhere(raster[:,:,3]<=127):
        point=good[np.argmin(((good-[y,x])**2).sum(1))]
        raster[y,x]=raster[tuple(point)]
    return raster


def paint(m,original,f2,kinds):
    tex=np.array(original.textura).copy();raster=feather_raster(f2)
    # O quadrante inferior direito era livre; as ilhas novas não tocam a cabeça.
    tex[256:512,256:512]=0
    for c in m.cubos:
        kind=kinds.get(c.nome)
        if kind is None:continue
        for face in c.faces:
            rows=texturizar.texels_da_face(c,face,np.eye(4))
            if rows is None:continue
            for (u,v),p in zip(*rows):
                rel=(p-c.de)/np.maximum(c.tamanho,1e-9)
                if kind=='blade':
                    t=float(rel[1]);x=(rel[0]-.5)*5
                    spine=-1.75+.40*t;edge=1.75+.60*t
                    if t>.78:
                        spine=np.interp(t,[.78,1],[-1.438,.75]);edge=np.interp(t,[.78,1],[2.218,.75])
                    if not spine<=x<=edge:continue
                    color=raster[min(31,int(t*32)),min(5,int(rel[0]*6)),:3]
                elif kind=='hand':color=(25,54,82) if face in ['down','south'] else (31,77,94)
                elif kind=='handle':color=(42,105,118) if int(rel[1]*6)%2 else (31,77,94)
                elif kind=='guard':color=(79,174,127) if face=='up' else (42,105,118)
                else:color=[(43,133,144),(63,154,154),(75,187,186)][(int(rel[1]*5)+int(rel[0]*3))%3]
                tex[int(v),int(u)]=[*color,255]
    return tex


def validate(m,f2,original,shift,decors):
    base.FILE=FILE;base.OUT=OUT;base.SOURCE=SOURCE
    offset=m.ossos['head'].origem-f2.ossos['head'].origem
    r=base.validate(m,f2,original,offset)
    errors=[]
    for info in decors:
        c=m.cubo(info['nome']);source=f2.cubo(info['fonte_f2'])
        if c.osso!=info['pai']:errors.append(c.nome+': pai')
        if not np.allclose(c.tamanho,source.tamanho*info['fator']):errors.append(c.nome+': tamanho')
        for name,face in source.faces.items():
            if not np.allclose(np.array(c.faces[name]['uv'])-[256,0,256,0],face['uv']):errors.append(c.nome+': UV')
    forbidden=[c.nome for c in m.cubos if c.nome.startswith(('pincer_','finger_','thumb_','carpal_'))]
    # Ombro -> cotovelo -> mão desce ao longo do braço, sem a dobra raptorial.
    arm_pose={s:[m.ossos['arm_'+s].origem[1],m.ossos['forearm_'+s].origem[1],m.ossos['hand_'+s].origem[1]] for s in ['left','right']}
    contacts=[];mats=bbmodelo.matrizes_ossos(m)
    for c in m.cubos:
        if not c.nome.startswith(('back_wing_feather_','elbow_wing_')):continue
        mask,axes=roblox_infra.mascara_plano(m,c);y,x=np.nonzero(mask)
        points=np.tile(c.de,(len(x),1))
        points[:,axes[0]]+=(x+.5)/mask.shape[1]*c.tamanho[axes[0]]
        points[:,axes[1]]+=(y+.5)/mask.shape[0]*c.tamanho[axes[1]]
        distal=(points[:,2]-c.de[2])/c.tamanho[2]>.2
        world=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mats),points)
        for solid in m.cubos:
            if not np.all(solid.tamanho>1e-5):continue
            local=bbmodelo.aplicar(np.linalg.inv(bbmodelo.matriz_cubo(m,solid,mats)),world)
            depth=np.minimum(local-solid.de,solid.ate-local).min(1);selected=distal&(depth>.15)
            if selected.any():
                contacts.append({'pena':c.nome,'solido':solid.nome,'profundidade_max':float(depth[selected].max()),
                                 'amostras':int(selected.sum())})
    base.dump(OUT/'contatos-plumagem.json',{'metodo':'Centros opacos após 20% do comprimento; penetração >0,15 em sólidos. Não testa poses animadas.','contatos':contacts})
    r.update({'plumagem_f2':decors,'erros_plumagem':errors,'dedos_ou_pincas':forbidden,
              'alturas_ombro_cotovelo_punho':arm_pose,
              'contatos_distais_plumagem':contacts,
              'mudanca_postura_graus':{'tronco_adicional':6,'cauda_adicional':6},
              'espadas':{'template_textura':'wing_left_feather_1','largura':5,'comprimento':30,'espessura_plano':0}})
    r['integridade_ok'] &= not(errors or forbidden or contacts) and all(a[0]>a[1]>a[2] for a in arm_pose.values())
    base.dump(OUT/'revisao.json',r)
    return r


def previews(m):
    base.OUT=OUT;base.render_sheet(m)
    # Ângulo próximo da frente permite avaliar as duas espadas simultaneamente.
    im,*_=render.renderizar(m,vista=(15,8),escala=11,margem=12,sombreado=.22,fundo=(242,245,246))
    im.thumbnail((744,744),Image.Resampling.LANCZOS)
    canvas=Image.new('RGB',(768,768),(242,245,246))
    canvas.paste(im,((768-im.width)//2,(768-im.height)//2));canvas.save(OUT/'apresentacao.png')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--regenerar',action='store_true');args=parser.parse_args()
    stamp=OUT/'geracao.json'
    if FILE.exists() and (not args.regenerar or not stamp.exists() or json.loads(stamp.read_text())['sha256']!=base.sha(FILE)):
        raise SystemExit('Saída protegida. Edição manual exige outra versão.')
    m=bbmodelo.ler(SOURCE);f2=bbmodelo.ler(F2)
    batch,kinds,decors,grips,shift=build(m,f2)
    base.dump(OUT/'ajustes.ops.json',batch);shutil.copy2(SOURCE,FILE);motor.editar(FILE,batch)
    base.dump(stamp,{'sha256':base.sha(FILE),'etapa':'geometria'})
    model=bbmodelo.ler(FILE);tex=paint(model,m,f2,kinds);Image.fromarray(tex).save(OUT/'textura.png')
    motor.editar(FILE,[{'op':'update_texture','target':0,'source':texturizar._data_url(tex),'width':512,'height':512,'material':None},
                       {'op':'assign_texture','targets':[c.uuid for c in model.cubos],'texture':0}])
    base.dump(stamp,{'sha256':base.sha(FILE),'fonte_sha256':base.sha(SOURCE),'fonte_f2_sha256':base.sha(F2),'pegadas':grips})
    model=bbmodelo.ler(FILE);r=validate(model,f2,m,shift,decors);previews(model)
    print('F3 v4:',len(model.cubos),'peças,',len(model.ossos),'ossos, zero animações.')
    print('Motor:',r['motor'],'; plumagem F2:',len(decors),'; erros:',len(r['erros_plumagem']))
    print('Cabeça F2 exata:',all(c['erro_maximo']<1e-4 and c['uv_identica'] for c in r['cabeca_f2']))
    print('UV fora:',len(r['uv_fora_do_atlas']),'; faces novas transparentes:',len(r['faces_solidas_transparentes']))
    print('Encaixe armas:',r['desvio_encaixe_arma'],'; piso:',r['piso_opaco_minimo'],'; integridade:',r['integridade_ok'])
    if not r['integridade_ok']:raise SystemExit(1)


if __name__=='__main__':main()
