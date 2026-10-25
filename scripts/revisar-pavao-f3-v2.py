"""Integridade e comparação visual da reconstrução F3, sem editar o modelo."""
import copy
import importlib.util
from pathlib import Path
import subprocess
import tempfile

import numpy as np
from PIL import Image
from criaturas import bbmodelo, exportar, motor, render, roblox_infra, texturizar

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('f3_v2',ROOT/'scripts/modelar-pavao-f3-v2.py')
f3=importlib.util.module_from_spec(spec);spec.loader.exec_module(f3)
spec=importlib.util.spec_from_file_location('superficie_f3',ROOT/'scripts/revisar-pavao-f3.py')
surface=importlib.util.module_from_spec(spec);spec.loader.exec_module(surface)


def reference_mask(view):
    im=Image.open(f3.OUT/(view+'-768.png')).convert('RGB');im.thumbnail((370,352))
    canvas=Image.new('RGB',(384,360),'white');canvas.paste(im,((384-im.width)//2,0))
    a=np.array(canvas).astype(int)
    return (a.min(2)<220)&((a.max(2)-a.min(2)>25)|(a.max(2)<150))


def iou(a,b):return round(float((a&b).sum()/(a|b).sum()),4)


def main():
    m=bbmodelo.ler(f3.FILE);mat=bbmodelo.matrizes_ossos(m);alpha=np.array(m.textura)[:,:,3]
    engine=motor.validar(f3.FILE,allow_planes=True,min_thickness=.5)
    f3.dump(f3.OUT/'validacao-estrutura.json',engine)
    empty=[];floor=[];parents=[]
    for c in m.cubos:
        pts=surface.superficie(m,c)
        if not len(pts):empty.append(c.nome);continue
        world=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mat),pts)
        floor.append((float(world[:,1].min()),c.nome))
        if np.all(c.tamanho>1e-5):
            for face in c.faces:
                rows=texturizar.texels_da_face(c,face,np.eye(4))
                if rows is None:continue
                uv=np.array(rows[0],int)
                if len(uv) and (alpha[uv[:,1],uv[:,0]]<255).any():empty.append(c.nome+'.'+face)
        if c.nome.startswith('arm_blade_'):
            side='left' if '_left_' in c.nome else 'right'
            if m.ossos[c.osso].pai!='forearm_'+side:parents.append(c.nome)
    uv_errors=exportar.uv_fora_do_atlas(m)
    cam=f3.Perspective([0,70,-180],[0,29.5,8]);target=reference_mask('frente')
    _,mask,_,_=render.renderizar(m,projecao=cam)
    with tempfile.TemporaryDirectory(prefix='f3-referencia-v1-') as tmp:
        path=Path(tmp)/'v1.bbmodel'
        data=subprocess.run(['git','show','fe94ca4:modelos/criatura-pavao/f3/criatura-pavao-e3.bbmodel'],capture_output=True,check=True,cwd=ROOT).stdout
        path.write_bytes(data);v1=bbmodelo.ler(path);_,oldmask,_,_=render.renderizar(v1,projecao=cam)
    report={'sha256':f3.sha(f3.FILE),'motor':engine['summary'],
            'avisos_por_gate':{g['id']:len(g['violations']) for g in engine['gates']},
            'faces_solidas_transparentes_ou_pecas_vazias':empty,'uv_fora_do_atlas':uv_errors,
            'vinculos_incorretos':parents,'minimo_y_opaco':min(floor),
            'comparacao_silhueta_frontal':{'v1_commit':'fe94ca4','v1_iou':iou(oldmask,target),'v2_iou':iou(mask,target),
                'limite':'Máscara inteira, mesma câmera aproximada; não mede qualidade artística, semântica, textura ou anatomia.'},
            'medidas':{'pecas':len(m.cubos),'solidos':sum(np.all(c.tamanho>1e-5) for c in m.cubos),'ossos':len(m.ossos),'locators':len(m.locators),'animacoes':len(m.animacoes),'atlas':list(m.resolucao)}}
    # Perfil físico calculado localmente; não exporta nem altera o Roblox Studio.
    try:
        profile=roblox_infra.perfil_composto(f3.FILE,{'planos_alfa':True,'espessura_planos':.25,'max_partes':192})
        report['perfil_composto_local']={'pecas':len(profile['pecas']),'limite':192}
    except (ValueError,KeyError) as e:report['perfil_composto_local']={'aviso':str(e)}
    report['integridade_ok']=not (engine['summary']['errors'] or empty or uv_errors or parents) and min(floor)[0]>=-.05
    report['revisao_artistica']='pendente; proposta anterior rejeitada pelo usuário com 3/10'
    f3.dump(f3.OUT/'revisao.json',report)
    # A máscara só permanece nos detalhes finos; as lâminas e o leque são sólidos.
    clay=copy.copy(m);tex=np.array(m.textura);tex[:,:,:3]=[176,185,188];clay.textura=Image.fromarray(tex)
    cam3=f3.Perspective([-145,78,-155],[0,29,13],size=(768,768),fov=23)
    im,_,_,_=render.renderizar(clay,projecao=cam3,sombreado=.42);im.save(f3.OUT/'massas.png')
    cameras={'projecao':'perspective','fov':21,'frente':{'position':[0,70,-180],'target':[0,29.5,8]},
             'lado_aproximado':{'position':[-180*np.sin(np.radians(65)),70,16-180*np.cos(np.radians(65))],'target':[0,29.5,16]},
             'limite':'As referências redesenhadas não são projeções calibradas de uma mesma malha; frente e lado foram aproximados.'}
    f3.dump(f3.OUT/'cameras.json',cameras)
    print('Estrutura:',engine['summary'],'; UV fora:',len(uv_errors),'; faces vazias:',len(empty))
    print('Piso opaco:',min(floor),'; vínculos incorretos:',parents)
    print('Silhueta frontal IoU v1/v2:',report['comparacao_silhueta_frontal']['v1_iou'],report['comparacao_silhueta_frontal']['v2_iou'])
    print('Perfil composto local:',report['perfil_composto_local'])
    print('Integridade:',report['integridade_ok'],'; avaliação artística pendente.')
    if not report['integridade_ok']:raise SystemExit(1)


if __name__=='__main__':main()
