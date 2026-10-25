"""Ajusta uma cópia da edição manual: cabeça F2, postura aviana e penas empunhadas.

Geometria e textura entram exclusivamente pelo motor externo, em lotes registrados.
O snapshot de origem inclui as alterações ainda não salvas no Blockbench.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from criaturas import bbmodelo, exportar, motor, ops, render, roblox_infra, texturizar

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'modelos/criatura-pavao/f3/revisao-v3'
SOURCE = OUT / 'origem-manual.bbmodel'
F2 = ROOT / 'modelos/criatura-pavao/f2/corrida-v2/criatura-pavao-e2-corrida-v2.bbmodel'
FILE = OUT / 'criatura-pavao-e3-v3b.bbmodel'
sp = importlib.util.spec_from_file_location('pavao_formas', ROOT / 'scripts/modelar-pavao-f3.py')
forms = importlib.util.module_from_spec(sp)
sp.loader.exec_module(forms)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dump(p, data):
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2,
                           default=lambda x: x.tolist() if isinstance(x, np.ndarray) else x.item()) + '\n', encoding='utf-8')


def descendants(m, root):
    names = {root}
    while True:
        more = names | {o.nome for o in m.ossos.values() if o.pai in names}
        if names == more:
            return names
        names = more


def transform(pivot, degrees):
    r = bbmodelo.matriz_rotacao(degrees)
    m = np.eye(4)
    m[:3, :3] = r
    m[:3, 3] = np.array(pivot) - r @ pivot
    return m


def move_cube(c, matrix):
    # Mantém dimensões/UV e incorpora a transformação na rotação de cada peça.
    origin = bbmodelo.aplicar(matrix, [c.origem])[0]
    delta = origin - c.origem
    return {'op': 'update_node', 'target': c.uuid, 'origin': origin.tolist(),
            'from': (c.de + delta).tolist(), 'to': (c.ate + delta).tolist(),
            'rotation': forms.euler(matrix[:3, :3] @ bbmodelo.matriz_rotacao(c.rotacao)),
            'faces': copy.deepcopy(c.faces)}


def palette_texture(m):
    # Cores da F2: preserva a pintura e os recortes da edição manual da F3.
    new = [
        [(22,63,76),(31,77,94),(31,98,113),(42,105,118),(43,133,144),(63,154,154),(75,187,186),(104,205,200)],
        [(31,98,113),(43,133,144),(63,154,154),(79,174,127),(92,189,127),(143,208,154),(147,224,214)],
        [(151,135,95),(183,161,110),(207,194,152),(230,220,182),(243,236,208),(243,236,208),(251,246,230)],
        [(22,63,76),(25,54,82),(31,77,94),(42,105,118),(43,133,144)],
        [(168,122,36),(232,195,90),(239,192,78),(251,246,230)],
    ]
    original = [forms.TEAL, forms.GREEN, forms.CREAM, forms.DARK, forms.GOLD]
    tex = np.array(m.textura)
    rgb = tex[:,:,:3].copy()
    for ramp, target in zip(original, new):
        for before, after in zip(ramp, target):
            tex[np.all(rgb == before, axis=2), :3] = after
    return tex


def build(m, f2):
    batch = [{'op':'set_model_properties', 'name':FILE.stem,
              'resolution':{'width':512, 'height':512}}]
    head_old = descendants(m, 'head')
    arm_old = descendants(m, 'arm_left') | descendants(m, 'arm_right')
    # Remoção acontece apenas na cópia, inclusive grupos vazios e locators antigos.
    batch += [{'op':'remove_node','target':m.ossos[n].uuid} for n in ['head','arm_left','arm_right']]
    batch += [{'op':'remove_node','target':c.uuid} for c in m.cubos if c.osso in ['neck_1','neck_2']]
    lean = transform(np.array([0,26.5,0]), [-16,0,0])
    tail = transform(np.array([0,25,4]), [-8,0,0])
    upper = descendants(m, 'waist') - head_old - arm_old
    tail_nodes = descendants(m, 'tail_1')
    for c in m.cubos:
        if c.osso in head_old | arm_old or c.osso in ['neck_1','neck_2']:
            continue
        mat = lean if c.osso in upper else tail if c.osso in tail_nodes else None
        if mat is not None:
            batch.append(move_cube(c, mat))
    for n, o in m.ossos.items():
        if n in head_old | arm_old:
            continue
        mat = lean if n in upper else tail if n in tail_nodes else None
        if mat is not None:
            batch.append({'op':'update_node','target':o.uuid,
                          'origin':bbmodelo.aplicar(mat,[o.origem])[0].tolist()})
    for side in ['left','right']:
        # O usuário acentuou o joelho movendo a geometria; ajusta a junta à edição.
        batch.append({'op':'update_node','target':'shin_'+side,
                      'origin':m.cubo('shank_'+side).origem.tolist()})

    cubes = []
    kinds = {}

    def group(name, parent, origin):
        batch.append({'op':'add_group','name':name,'parent':parent,'origin':list(origin)})

    def box(name, parent, center, dimensions, rotation=None, kind='body'):
        center = np.array(center, float)
        half = np.array(dimensions, float)/2
        cubes.append({'nome':name, 'osso':parent, 'from':(center-half).tolist(),
                      'to':(center+half).tolist(), 'origin':center.tolist(),
                      'rotation':forms.euler(rotation) if rotation is not None else [0,0,0]})
        kinds[name] = kind

    def segment(name, parent, a, b, width, depth, kind='body'):
        a,b = np.array(a,float),np.array(b,float)
        length = np.linalg.norm(b-a)
        box(name,parent,(a+b)/2,[width,length,depth],forms.alinhar([0,1,0], b-a),kind)

    # Cabeça original inteira, sem escala ou mudança de orientação interna.
    offset = np.array([0,43.0,-5.8]) - f2.ossos['head'].origem
    head = descendants(f2, 'head')
    pending = set(head)
    while pending:
        for n in sorted(pending):
            o = f2.ossos[n]
            if n != 'head' and o.pai in pending:
                continue
            group(n, 'neck_2' if n=='head' else o.pai, o.origem+offset)
            if np.any(o.rotacao):
                batch.append({'op':'update_node','target':n,'rotation':o.rotacao.tolist()})
            pending.remove(n)
            break
    head_cubes = [c for c in f2.cubos if c.osso in head]
    elements = {e['uuid']:e for e in f2.bruto['elements']}
    for c in head_cubes:
        faces = copy.deepcopy(c.faces)
        for f in faces.values():
            f['uv'][0] += 256
            f['uv'][2] += 256
            if f.get('texture') is not None:
                f['texture'] = 0
        uv = np.array(elements[c.uuid].get('uv_offset',[0,0]))+[256,0]
        batch.append({'op':'add_cube','name':c.nome,'parent':c.osso,
                      'from':(c.de+offset).tolist(),'to':(c.ate+offset).tolist(),
                      'origin':(c.origem+offset).tolist(),'rotation':c.rotacao.tolist(),
                      'inflate':c.inflate,'box_uv':elements[c.uuid].get('box_uv',False),'uv_offset':uv.tolist(),
                      'mirror_uv':c.mirror_uv,'faces':faces})

    # Pescoço compacto liga o peito inclinado à parte posterior do crânio.
    neck_a = bbmodelo.aplicar(lean, [[0,39.1,-.6]])[0]
    neck_b = np.array([0,41.7,-4.5])
    neck_c = np.array([0,43.0,-5.7])
    batch += [{'op':'update_node','target':'neck_1','origin':neck_a.tolist()},
              {'op':'update_node','target':'neck_2','origin':neck_b.tolist()}]
    segment('neck_lower_avian','neck_1',neck_a,neck_b,4.3,4.0,'neck')
    segment('neck_upper_avian','neck_2',neck_b,neck_c,3.8,3.8,'neck')
    grip_data = {}
    for side,s in [('left',-1),('right',1)]:
        shoulder = bbmodelo.aplicar(lean, [[s*5,38.1,0]])[0]
        elbow = np.array([s*7.6,30.4,-.3])
        wrist = np.array([s*9.0,33.1,-6.0])
        grip = np.array([s*10.0,33.0,-7.4])
        axis = np.array([s*.28,-.64,-.72]);axis/=np.linalg.norm(axis)
        normal = np.array([0,.75,-.65]);normal-=axis*(normal@axis);normal/=np.linalg.norm(normal)
        across = np.cross(axis,normal);across/=np.linalg.norm(across)
        frame = np.column_stack([across,axis,normal])
        group('arm_'+side,'torso',shoulder)
        group('forearm_'+side,'arm_'+side,elbow)
        group('hand_'+side,'forearm_'+side,wrist)
        group('feather_sword_'+side,'hand_'+side,grip)
        segment('upper_arm_'+side,'arm_'+side,shoulder,elbow,3.3,3.3)
        segment('forearm_solid_'+side,'forearm_'+side,elbow,wrist,2.5,2.7)
        # Pequeno carpo e dois dedos opostos, cada um com duas falanges curtas.
        segment('carpal_'+side,'hand_'+side,wrist,grip-normal*.85,1.9,1.8)
        for label, sign in [('inner',-1),('outer',1)]:
            sign *= s
            a=grip+across*sign*.75-normal*.65
            b=grip+across*sign*1.15+normal*.2
            c=grip+across*sign*.3+normal*.65
            segment(f'pincer_{side}_{label}_base','hand_'+side,a,b,.85,.85,'pincer')
            segment(f'pincer_{side}_{label}_tip','hand_'+side,b,c,.7,.7,'pincer_tip')
        segment('quill_grip_'+side,'feather_sword_'+side,grip-axis*2.0,grip+axis*3.5,.85,.85,'quill')
        base = grip+axis*1.5
        box('feather_blade_'+side,'feather_sword_'+side,base+axis*15,[9,30,0],frame,'blade')
        grip_data[side] = {'grip':grip,'base':base,'tip':base+axis*30,'axis':axis,'frame':frame}
        for suffix,point in [('hand',grip),('weapon_base',base),('weapon_tip',base+axis*30)]:
            parent = 'hand_'+side if suffix=='hand' else 'feather_sword_'+side
            batch.append({'op':'add_locator','name':'loc_'+suffix+'_'+side,'parent':parent,'position':point.tolist()})
    for name,p in [('loc_head_look',[0,32,-16]),('loc_mouth',[0,30,-17.3]),('loc_top',[0,44,-12])]:
        batch.append({'op':'add_locator','name':name,'parent':'head','position':(np.array(p)+offset).tolist()})
    # Atualiza os locators existentes que acompanham as peças reorientadas.
    by_name = {e['name']:e for e in m.bruto['elements'] if e.get('type')=='locator'}
    for loc in m.locators:
        mat = lean if loc.osso in upper else tail if loc.osso in tail_nodes else None
        if mat is not None:
            batch.append({'op':'remove_node','target':by_name[loc.nome]['uuid']})
            batch.append({'op':'add_locator','name':loc.nome,'parent':loc.osso,
                          'position':bbmodelo.aplicar(mat,[loc.posicao])[0].tolist()})

    # A edição manual aumentou estes volumes além das regiões antes pintadas.
    # Novas ilhas isolam o reparo e preservam as cores das outras peças.
    repairs=[]
    for name in ['ribcage','shank_left','shank_right']:
        c=m.cubo(name)
        repairs.append({'nome':name,'from':c.de.tolist(),'to':c.ate.tolist()})
        kinds[name]='repair'
    offsets, _ = ops.distribuir_uv(cubes+repairs,margem=2,larguras=(256,))
    for c in repairs:
        batch.append({'op':'update_node','target':m.cubo(c['nome']).uuid,
                      'uv_offset':[offsets[c['nome']][0],offsets[c['nome']][1]+256]})
    for c in cubes:
        batch.append({'op':'add_cube','name':c['nome'],'parent':c['osso'],
                      'from':c['from'],'to':c['to'],'origin':c['origin'],'rotation':c['rotation'],
                      'box_uv':True,'uv_offset':[offsets[c['nome']][0],offsets[c['nome']][1]+256]})
    return batch, kinds, head_cubes, offset, grip_data


def paint(m, original, f2, kinds):
    tex = np.zeros((512,512,4),np.uint8)
    tex[:256,:256] = palette_texture(original)
    tex[:256,256:512] = np.array(f2.textura)
    for c in m.cubos:
        kind=kinds.get(c.nome)
        if kind is None:
            continue
        for face in c.faces:
            rows=texturizar.texels_da_face(c,face,np.eye(4))
            if rows is None:
                continue
            if kind=='repair':
                old=original.cubo(c.nome)
                oldrows=texturizar.texels_da_face(old,face,np.eye(4))
                uv,points=rows;uv=np.asarray(uv,int)
                ou,op=oldrows;ou=np.asarray(ou,int)
                colors=tex[ou[:,1],ou[:,0]]
                valid=colors[:,3]>127
                if valid.any():
                    source_points=op[valid]-old.de
                    queries=points-c.de
                    nearest=np.argmin(((queries[:,None]-source_points[None])**2).sum(2),axis=1)
                    tex[uv[:,1],uv[:,0]]=colors[valid][nearest]
                else:
                    tex[uv[:,1],uv[:,0]]=[63,154,154,255]
                continue
            for (u,v),p in zip(*rows):
                rel=(p-c.de)/np.maximum(c.tamanho,1e-9)
                if kind=='blade':
                    t=rel[1];x=(rel[0]-.5)*9
                    half=np.interp(t,[0,.12,.30,.62,.83,1],[.35,1.8,4.5,3.7,2.0,0])
                    half-=.30*(1-((t*30/3)%1))
                    if abs(x)>max(.1,half):
                        continue
                    k=int(t*30//3+abs(x)//2)%4
                    color=(230,220,182) if t>.84 else (104,205,200) if abs(x)<.55 else (
                        [(79,174,127),(92,189,127),(63,154,154),(143,208,154)][k] if x>0 else
                        [(42,105,118),(43,133,144),(63,154,154),(75,187,186)][k])
                    # Um friso escuro recorta a lâmina como as penas finas da F2.
                    if abs(x)>half-.35 and t<.83:color=(31,98,113)
                elif kind in ['pincer','pincer_tip']:
                    color=(31,77,94) if kind=='pincer' else (25,54,82)
                elif kind=='quill':
                    color=(230,220,182) if face=='up' else (207,194,152)
                elif kind=='neck':
                    color=(63,154,154) if face in ['north','up'] else (42,105,118)
                else:
                    choices=[(43,133,144),(63,154,154),(75,187,186)]
                    color=choices[(int(rel[1]*5)+int(rel[0]*3))%3]
                tex[int(v),int(u)]=[*color,255]
    return tex


def render_sheet(m):
    sheet=Image.new('RGB',(768,768),(242,245,246))
    d=ImageDraw.Draw(sheet)
    font_path=Path('C:/Windows/Fonts/segoeui.ttf')
    font=ImageFont.truetype(str(font_path),16) if font_path.exists() else ImageFont.load_default()
    for i,(label,view) in enumerate([('Frente','frente'),('Perfil','lado'),('Costas','costas'),('3/4','3/4')]):
        im,*_=render.renderizar(m,vista=view,escala=5,margem=10,sombreado=.22,fundo=(242,245,246))
        im.thumbnail((370,350),Image.Resampling.LANCZOS)
        x=(i%2)*384+(384-im.width)//2;y=(i//2)*384+29+(350-im.height)//2
        sheet.paste(im,(x,y))
        d.text(((i%2)*384+12,(i//2)*384+6),label,fill=(35,50,58),font=font)
    sheet.save(OUT/'folha.png')
    im,*_=render.renderizar(m,vista='3/4',escala=11,margem=12,sombreado=.22,fundo=(242,245,246))
    im.thumbnail((744,744),Image.Resampling.LANCZOS)
    preview=Image.new('RGB',(768,768),(242,245,246))
    preview.paste(im,((768-im.width)//2,(768-im.height)//2))
    preview.save(OUT/'apresentacao.png')


def validate(m, f2, original, offset):
    engine=motor.validar(FILE,allow_planes=True,min_thickness=.5)
    dump(OUT/'validacao-estrutura.json',engine)
    head=descendants(f2,'head');head_check=[]
    # Geometria, pivôs, rotações, recortes e cores devem ser idênticos após translação.
    for old in f2.cubos:
        if old.osso not in head:
            continue
        new=m.cubo(old.nome)
        err=max(np.abs(new.de-offset-old.de).max(),np.abs(new.ate-offset-old.ate).max(),
                np.abs(new.origem-offset-old.origem).max(),np.abs(new.rotacao-old.rotacao).max())
        same=True
        for face,of in old.faces.items():
            nf=new.faces[face]
            uv=np.array(nf['uv'])-[256,0,256,0]
            same &= bool(np.allclose(uv,of['uv']))
        head_check.append({'peca':old.nome,'erro_maximo':float(err),'uv_identica':same})
    shared_texture=bool(np.array_equal(np.array(m.textura)[:256,256:512],np.array(f2.textura)))
    uv=exportar.uv_fora_do_atlas(m)
    blank=[];inherited=[]
    alpha=np.array(m.textura)[:,:,3]
    for c in m.cubos:
        if not np.all(c.tamanho>1e-5):continue
        for face in c.faces:
            rows=texturizar.texels_da_face(c,face,np.eye(4))
            if rows is None:continue
            coords=np.array(rows[0],int)
            if len(coords) and np.any(alpha[coords[:,1],coords[:,0]]<255):
                label=c.nome+'.'+face
                if c.osso in head:
                    old=f2.cubo(c.nome);source_rows=texturizar.texels_da_face(old,face,np.eye(4))
                    q=np.asarray(source_rows[0],int);original_alpha=np.array(f2.textura)[:,:,3]
                    if np.any(original_alpha[q[:,1],q[:,0]]<255):
                        inherited.append(label);continue
                blank.append(label)
    # Um teste de transformação, sem criar animações: a arma conserva seu encaixe.
    attachment=[]
    for side in ['left','right']:
        h='hand_'+side;w='feather_sword_'+side
        assert m.ossos[w].pai==h
        root=m.ossos[w].origem
        for angle in [-65,0,65]:
            mats=bbmodelo.matrizes_ossos(m,{h:{'rotacao':[angle,25,-20]}})
            a=bbmodelo.aplicar(mats[h],[root])[0]
            b=bbmodelo.aplicar(mats[w],[root])[0]
            attachment.append(float(np.linalg.norm(a-b)))
    preserved=[]
    for c in original.cubos:
        if c.nome.startswith(('thigh','shank','tarsus','foot_pad','toe','claw','hip_')) or c.nome in ['ribcage','ribcage_lower','chest_top'] or c.nome.startswith('tail_'):
            new=m.cubo(c.nome)
            preserved.append({'peca':c.nome,'dimensoes_preservadas':bool(np.allclose(c.tamanho,new.tamanho))})
    floor=[];mats=bbmodelo.matrizes_ossos(m)
    for c in m.cubos:
        if np.all(c.tamanho>1e-5):
            points=bbmodelo.cantos(c)
        else:
            mask,axes=roblox_infra.mascara_plano(m,c)
            y,x=np.nonzero(mask);corners=[]
            for dx,dy in [(0,0),(0,1),(1,0),(1,1)]:
                q=np.tile(c.de,(len(x),1))
                q[:,axes[0]]+=(x+dx)/mask.shape[1]*c.tamanho[axes[0]]
                q[:,axes[1]]+=(y+dy)/mask.shape[0]*c.tamanho[axes[1]]
                corners.append(q)
            points=np.concatenate(corners)
        if len(points):
            world=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mats),points)
            floor.append((float(world[:,1].min()),c.nome))
    report={'fonte_manual_sha256':sha(SOURCE),'fonte_f2_sha256':sha(F2),'saida_sha256':sha(FILE),
            'motor':engine['summary'],'avisos_por_gate':{g['id']:len(g['violations']) for g in engine['gates']},
            'cabeca_f2':head_check,'textura_f2_identica':shared_texture,
            'dimensoes_preservadas':preserved,'uv_fora_do_atlas':uv,'faces_solidas_transparentes':blank,
            'transparencias_herdadas_cabeca_f2':inherited,
            'piso_opaco_minimo':min(floor),
            'desvio_encaixe_arma':max(attachment),'animacoes':len(m.animacoes),'pecas':len(m.cubos),
            'ossos':len(m.ossos),'atlas':list(m.resolucao),
            'limites':'Revisão de forma e rig em repouso; colisões e desempenho no Roblox ainda não testados. Sobreposições AABB incluem encaixes e camadas.'}
    report['integridade_ok']=bool(not(engine['summary']['errors'] or uv or blank)
                                 and shared_texture and max(attachment)<1e-7
                                 and all(c['erro_maximo']<1e-4 and c['uv_identica'] for c in head_check)
                                 and all(p['dimensoes_preservadas'] for p in preserved)
                                 and min(floor)[0]>=-.05)
    dump(OUT/'revisao.json',report)
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--regenerar',action='store_true')
    args=parser.parse_args()
    if FILE.exists():
        stamp=OUT/'geracao.json'
        if not args.regenerar or not stamp.exists() or json.loads(stamp.read_text())['sha256']!=sha(FILE):
            raise SystemExit('Saída existente protegida; use uma nova versão se houve edição manual.')
    m=bbmodelo.ler(SOURCE);f2=bbmodelo.ler(F2)
    batch,kinds,_,offset,grips=build(m,f2)
    dump(OUT/'ajustes.ops.json',batch)
    shutil.copy2(SOURCE,FILE)
    motor.editar(FILE,batch)
    dump(OUT/'geracao.json',{'sha256':sha(FILE),'etapa':'geometria'})
    model=bbmodelo.ler(FILE)
    tex=paint(model,m,f2,kinds)
    Image.fromarray(tex).save(OUT/'textura.png')
    # O projeto exportado pelo desktop registra material=""; limpa essa referência
    # vazia ao atualizar a textura simples, sem criar materiais PBR.
    motor.editar(FILE,[{'op':'update_texture','target':0,'source':texturizar._data_url(tex),
                        'width':512,'height':512,'material':None},
                       {'op':'assign_texture','targets':[c.uuid for c in model.cubos],'texture':0}])
    dump(OUT/'geracao.json',{'sha256':sha(FILE),'etapa':'textura'})
    model=bbmodelo.ler(FILE)
    report=validate(model,f2,m,offset)
    render_sheet(model)
    dump(OUT/'geracao.json',{'sha256':sha(FILE),'fonte_manual_sha256':sha(SOURCE),'fonte_f2_sha256':sha(F2),
                            'translacao_cabeca':offset,'pegadas':grips,'inclinacao_tronco_graus':16,'elevacao_cauda_graus':8})
    print('F3 v3:',len(model.cubos),'peças;',len(model.ossos),'ossos; atlas 512; animações:',len(model.animacoes))
    print('Cabeça F2 exata:',all(c['erro_maximo']<1e-4 and c['uv_identica'] for c in report['cabeca_f2']),'; textura igual:',report['textura_f2_identica'])
    print('Estrutura:',report['motor'],'; UV fora:',len(report['uv_fora_do_atlas']),'; faces vazias:',len(report['faces_solidas_transparentes']))
    print('Encaixe arma:',report['desvio_encaixe_arma'],'; integridade:',report['integridade_ok'])
    print('Prévia: modelos/criatura-pavao/f3/revisao-v3/folha.png')
    if not report['integridade_ok']:raise SystemExit(1)


if __name__=='__main__':main()
