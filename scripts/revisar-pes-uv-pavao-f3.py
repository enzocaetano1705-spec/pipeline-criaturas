"""Adota a geometria manual da F3, repara UVs e monta pés compactos no estilo F2."""
import argparse
import copy
import importlib.util
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image
from criaturas import bbmodelo, exportar, motor, ops, render, texturizar

ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('identidade_f3',ROOT/'scripts/revisar-identidade-pavao-f3.py')
base=importlib.util.module_from_spec(sp);sp.loader.exec_module(base)
OUT=ROOT/'modelos/criatura-pavao/f3/revisao-v5'
SOURCE=OUT/'origem-manual.bbmodel'
FILE=OUT/'criatura-pavao-e3-v5.bbmodel'
F2=base.F2
HISTORY='237ceb7:modelos/criatura-pavao/f3/revisao-v4/criatura-pavao-e3-v4.bbmodel'
SCALE=1.15


def endpoints(m,c):
    points=np.tile((c.de+c.ate)/2,(2,1));points[0,1]=c.ate[1];points[1,1]=c.de[1]
    return bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,bbmodelo.matrizes_ossos(m)),points)


def historical():
    p=OUT/'_cache/antes-edicoes.bbmodel';p.parent.mkdir(exist_ok=True)
    p.write_bytes(subprocess.run(['git','show',HISTORY],capture_output=True,check=True,cwd=ROOT).stdout)
    return bbmodelo.ler(p)


def build(m,old,f2):
    if m.animacoes:raise ValueError('Esta revisão espera um modelo sem clipes; preservar animações exige adaptar o deslocamento.')
    references={c.uuid:c for c in old.cubos}
    repairs={c.uuid:references[c.uuid] for c in m.cubos if c.uuid in references
             and not np.allclose(c.tamanho,references[c.uuid].tamanho,atol=1e-4)}
    if not np.array_equal(np.array(m.textura),np.array(old.textura)):
        raise ValueError('A pintura foi editada desde a v4: rever a origem das amostras antes de reparar os UVs.')
    mats=bbmodelo.matrizes_ossos(m)
    f2_tarsus=f2.cubo('tarsus_left');f2_bottom=endpoints(f2,f2_tarsus)[1]
    f2_floor=bbmodelo.caixa_mundo(f2,f2_tarsus)[0][1]
    feet=[];pads=[];joints={};contact_data={}
    for side,s in [('left',-1),('right',1)]:
        thigh=m.cubo('thigh_'+side);shank=m.cubo('shank_'+side);tarsus=m.cubo('tarsus_'+side)
        hip,knee=endpoints(m,thigh);shin_top,hock=endpoints(m,shank);foot_top,ankle=endpoints(m,tarsus)
        joints['leg_'+side]=hip
        joints['shin_'+side]=(knee+shin_top)/2
        joints['foot_'+side]=(hock+foot_top)/2
        tarsus_min=bbmodelo.caixa_mundo(m,tarsus,mats)[0][1]
        # Alinha a sola à parte baixa do tornozelo, usando as proporções da F2.
        offset=np.array([ankle[0]-s*5.5*SCALE,tarsus_min-f2_floor*SCALE,
                         ankle[2]-f2_bottom[2]*SCALE])
        floor=f2.cubo('toe_left_1').de[1]*SCALE+offset[1]
        pad_center=np.array([ankle[0],floor+SCALE/2,ankle[2]+.55])
        pads.append({'nome':'foot_base_'+side,'osso':'foot_'+side,
                     'from':(pad_center-[1.25,SCALE/2,1.35]).tolist(),
                     'to':(pad_center+[1.25,SCALE/2,1.35]).tolist(),
                     'origin':pad_center.tolist(),'rotation':[0,0,0]})
        for label in ['0','1','2','back']:
            c=f2.cubo('toe_left_'+label);de=c.de.copy();ate=c.ate.copy();origin=c.origem.copy();rot=c.rotacao.copy()
            if s>0:
                de[0],ate[0]=-ate[0],-de[0];origin[0]*=-1;rot[1:]*=-1
            de=de*SCALE+offset;ate=ate*SCALE+offset;origin=origin*SCALE+offset
            if label=='back':
                # A raiz posterior encosta na base compacta, sem ficar flutuando.
                shift=(pad_center[2]+1.35-.35)-de[2]
                de[2]+=shift;ate[2]+=shift;origin[2]+=shift
            faces=copy.deepcopy(c.faces)
            for face in faces.values():
                face['uv'][0]+=256;face['uv'][2]+=256
                if face.get('texture') is not None:face['texture']=0
            feet.append({'op':'add_cube','name':'toe_'+side+'_'+label,'parent':'foot_'+side,
                         'from':de.tolist(),'to':ate.tolist(),'origin':origin.tolist(),'rotation':rot.tolist(),
                         'inflate':c.inflate,'box_uv':False,'faces':faces})
        contact_data[side]={'tornozelo':ankle.tolist(),'solo_antes_ajuste':float(floor)}
    ground_shift=-min(f['from'][1] for f in feet)
    delta=np.array([0,ground_shift,0])
    pack=[{'nome':c.uuid,'from':c.de.tolist(),'to':c.ate.tolist()} for c in m.cubos if c.uuid in repairs]+pads
    offsets,_=ops.distribuir_uv(pack,margem=2,larguras=(256,))
    for name,(u,v) in offsets.items():
        if v+ops.tamanho_box_uv(next(c for c in pack if c['nome']==name)['from'],
                                next(c for c in pack if c['nome']==name)['to'])[1]>128:
            raise ValueError('As ilhas reparadas não cabem no retângulo livre do atlas.')
    # Confere o retângulo antes de usá-lo; evita atingir pintura existente.
    for c in m.cubos:
        if c.uuid in repairs:continue
        for face in c.faces.values():
            u1,v1,u2,v2=face['uv']
            if max(u1,u2)>256 and min(u1,u2)<512 and max(v1,v2)>384 and min(v1,v2)<512:
                raise ValueError('A área reservada já é usada por '+c.nome)
    batch=[{'op':'add_texture','name':'textura','width':512,'height':512,
            'source':texturizar._data_url(np.array(m.textura))}]
    pending=set(m.ossos)
    while pending:
        for name in sorted(pending):
            o=m.ossos[name]
            if o.pai in pending:continue
            pivo=joints.get(name,o.origem)+delta if name!='root' else o.origem
            op={'op':'add_group','name':name,'uuid':o.uuid,'origin':pivo.tolist(),'rotation':o.rotacao.tolist()}
            if o.pai:op['parent']=m.ossos[o.pai].uuid
            batch.append(op);pending.remove(name);break
        else:raise ValueError('Ciclo na hierarquia manual.')
    for c in m.cubos:
        op={'op':'add_cube','name':c.nome,'uuid':c.uuid,'from':(c.de+delta).tolist(),
            'to':(c.ate+delta).tolist(),'origin':(c.origem+delta).tolist(),
            'rotation':c.rotacao.tolist(),'inflate':c.inflate,'box_uv':c.uuid in repairs,
            'mirror_uv':c.mirror_uv}
        if c.osso:op['parent']=m.ossos[c.osso].uuid
        if c.uuid in repairs:
            u,v=offsets[c.uuid];op['uv_offset']=[u+256,v+384]
        else:op['faces']=copy.deepcopy(c.faces)
        batch.append(op)
    for p in pads:
        u,v=offsets[p['nome']]
        batch.append({'op':'add_cube','name':p['nome'],'parent':'foot_'+('left' if p['nome'].endswith('left') else 'right'),
                      'from':(np.array(p['from'])+delta).tolist(),'to':(np.array(p['to'])+delta).tolist(),
                      'origin':(np.array(p['origin'])+delta).tolist(),'box_uv':True,'uv_offset':[u+256,v+384]})
    for f in feet:
        f=copy.deepcopy(f)
        for key in ['from','to','origin']:f[key]=(np.array(f[key])+delta).tolist()
        batch.append(f)
    for loc in m.locators:
        position=loc.posicao+delta
        batch.append({'op':'add_locator','name':loc.nome,'parent':loc.osso,'position':position.tolist()})
    for side,s in [('left',-1),('right',1)]:
        if not any(l.nome=='loc_foot_'+side for l in m.locators):
            batch.append({'op':'add_locator','name':'loc_foot_'+side,'parent':'foot_'+side,
                          'position':[contact_data[side]['tornozelo'][0],0,contact_data[side]['tornozelo'][2]]})
    if not any(l.nome=='loc_ground' for l in m.locators):
        batch.append({'op':'add_locator','name':'loc_ground','parent':'root','position':[0,0,0]})
    return batch,repairs,delta,contact_data


def paint(m,source,repairs):
    tex=np.array(source.textura).copy()
    for c in m.cubos:
        old=repairs.get(c.uuid)
        if old is None and not c.nome.startswith('foot_base_'):continue
        for face in c.faces:
            rows=texturizar.texels_da_face(c,face,np.eye(4))
            if rows is None:continue
            uv,points=rows;uv=np.array(uv,int)
            if old is None:
                rel=(points-c.de)/np.maximum(c.tamanho,1e-9)
                palette=np.array([(43,133,144),(63,154,154),(75,187,186)],np.uint8)
                colors=palette[(np.floor(rel[:,0]*3)+np.floor(rel[:,2]*3)).astype(int)%3]
            else:
                # Normaliza o ponto na face editada e amostra a face íntegra anterior.
                queries=old.de+(points-c.de)/np.maximum(c.tamanho,1e-9)*old.tamanho
                old_uv,old_points=texturizar.texels_da_face(old,face,np.eye(4));old_uv=np.asarray(old_uv,int)
                palette=np.array(source.textura)[old_uv[:,1],old_uv[:,0]]
                valid=palette[:,3]>127
                if not valid.any():raise ValueError('A face de referência está vazia: '+old.nome+'.'+face)
                nearest=np.argmin(((queries[:,None]-old_points[valid][None])**2).sum(2),axis=1)
                colors=palette[valid][nearest,:3]
            tex[uv[:,1],uv[:,0],:3]=colors;tex[uv[:,1],uv[:,0],3]=255
    return tex


def validate(m,source,delta,repairs,contact_data):
    engine=motor.validar(FILE,allow_planes=True,min_thickness=.5)
    base.dump(OUT/'validacao-estrutura.json',engine)
    current={c.uuid:c for c in m.cubos};preserved=[]
    for old in source.cubos:
        c=current[old.uuid]
        error=max(abs(c.de-delta-old.de).max(),abs(c.ate-delta-old.ate).max(),
                  abs(c.origem-delta-old.origem).max(),abs(c.rotacao-old.rotacao).max())
        preserved.append({'nome':old.nome,'uuid':old.uuid,'erro_geometria':float(error)})
    alpha=np.array(m.textura)[:,:,3];blank=[];legacy=[]
    for c in m.cubos:
        if not np.all(c.tamanho>1e-5):continue
        for face in c.faces:
            rows=texturizar.texels_da_face(c,face,np.eye(4))
            if rows is None:continue
            q=np.asarray(rows[0],int)
            if len(q) and np.any(alpha[q[:,1],q[:,0]]<255):
                label=c.nome+'.'+face
                (legacy if label in ['beak.south','beak.down'] else blank).append(label)
    uv=exportar.uv_fora_do_atlas(m)
    mats=bbmodelo.matrizes_ossos(m);feet={}
    for side in ['left','right']:
        parts=[c for c in m.cubos if c.nome.startswith('toe_'+side) or c.nome=='foot_base_'+side]
        world=np.concatenate([bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mats),bbmodelo.cantos(c)) for c in parts])
        feet[side]={'pecas':len(parts),'dimensoes':(world.max(0)-world.min(0)).tolist(),'minimo_y':float(world[:,1].min())}
    # As regiões anteriores do atlas continuam idênticas, exceto as ilhas novas.
    a=np.array(source.textura).copy();b=np.array(m.textura).copy()
    a[384:512,256:512]=0;b[384:512,256:512]=0
    same=bool(np.array_equal(a,b))
    report={'fonte_manual_sha256':base.sha(SOURCE),'historico_textura':HISTORY,'saida_sha256':base.sha(FILE),
            'motor':engine['summary'],'avisos_por_gate':{g['id']:len(g['violations']) for g in engine['gates']},
            'geometria_manual':preserved,'translacao_vertical':float(delta[1]),
            'blocos_uv_reparados':[{'nome':c.nome,'uuid':c.uuid} for c in source.cubos if c.uuid in repairs],
            'atlas_anterior_preservado':same,'uv_fora_do_atlas':uv,'faces_solidas_transparentes':blank,
            'transparencias_herdadas_f2':legacy,'pes':feet,'escala_dedos_f2':SCALE,
            'pecas':len(m.cubos),'ossos':len(m.ossos),'animacoes':len(m.animacoes),
            'limite':'Verificação em repouso; não valida poses animadas ou colisões no Roblox. As sobreposições AABB incluem camadas e encaixes herdados da edição manual.'}
    report['integridade_ok']=bool(not(engine['summary']['errors'] or blank or uv) and same
                                  and max(p['erro_geometria'] for p in preserved)<1e-6
                                  and all(abs(p['minimo_y'])<1e-5 and p['pecas']==5 for p in feet.values()))
    base.dump(OUT/'revisao.json',report)
    return report


def previews(m):
    base.OUT=OUT;base.render_sheet(m)
    detail=copy.copy(m)
    detail.cubos=[c for c in m.cubos if c.nome.startswith(('tarsus_','toe_','foot_base_'))]
    im,*_=render.renderizar(detail,vista=(35,18),escala=22,margem=12,sombreado=.18,fundo=(242,245,246))
    im.thumbnail((768,768));im.save(OUT/'pes-detalhe.png')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--regenerar',action='store_true');args=parser.parse_args()
    stamp=OUT/'geracao.json'
    if FILE.exists() and (not args.regenerar or not stamp.exists() or json.loads(stamp.read_text())['sha256']!=base.sha(FILE)):
        raise SystemExit('Saída protegida; edições manuais exigem outra versão.')
    source=bbmodelo.ler(SOURCE);old=historical();f2=bbmodelo.ler(F2)
    batch,repairs,delta,contacts=build(source,old,f2)
    base.dump(OUT/'ajustes.ops.json',batch)
    # Criação por operações mantém geometria/UUID/UV; a origem manual nunca é sobrescrita.
    motor.chamar('bbmodel_create',{'file':motor.relativo(FILE),'format':'bedrock','name':FILE.stem,
                                  'resolution':{'width':512,'height':512},'overwrite':True})
    motor.editar(FILE,batch)
    base.dump(stamp,{'sha256':base.sha(FILE),'etapa':'geometria'})
    model=bbmodelo.ler(FILE);tex=paint(model,source,repairs);Image.fromarray(tex).save(OUT/'textura.png')
    motor.editar(FILE,[{'op':'update_texture','target':0,'source':texturizar._data_url(tex),'width':512,'height':512}])
    base.dump(stamp,{'sha256':base.sha(FILE),'fonte_sha256':base.sha(SOURCE),'translacao':delta,'encaixes':contacts})
    model=bbmodelo.ler(FILE);r=validate(model,source,delta,repairs,contacts)
    previews(model)
    print('F3 v5:',len(model.cubos),'peças;',len(repairs),'blocos com UV reparado; 5 peças por pé.')
    print('Geometria manual: erro máximo',max(p['erro_geometria'] for p in r['geometria_manual']))
    print('Estrutura:',r['motor'],'; faces novas transparentes:',len(r['faces_solidas_transparentes']))
    print('Pés:',r['pes'])
    print('Atlas anterior preservado:',r['atlas_anterior_preservado'],'; integridade:',r['integridade_ok'])
    if not r['integridade_ok']:raise SystemExit(1)


if __name__=='__main__':main()
