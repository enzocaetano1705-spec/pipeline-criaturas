"""Tentativa A: caixas/planos Bedrock via ops; nenhuma leitura da tentativa Blender."""
import base64
import hashlib
import sys
from pathlib import Path
import numpy as np
from criaturas import contratos, motor
from comum import BASE, ler, gravar, rot_segmento, atlas_face


def construir():
    out=BASE/(sys.argv[1] if len(sys.argv)>1 else 'blockbench-v1')
    out.mkdir(exist_ok=False)
    bones=[]
    cubes=[]
    def bone(name,parent,p): bones.append({'nome':name,'pai':parent,'pivo':p})
    def cube(name,parent,center,size,role,rotation=None,origin=None,cut=None,eye=False):
        a=np.array(center,float)-np.array(size,float)/2
        b=a+size
        cubes.append({'name':name,'bone':parent,'from':a.tolist(),'to':b.tolist(),'role':role,
                      'rotation':rotation or [0,0,0],'origin':origin or center,'cut':cut,'eye':eye})
    def limb(name,parent,a,b,width,depth,role):
        r,L=rot_segmento(a,b)
        bone(name,parent,a)
        length=max(1,round(L))
        cube(name+'_volume',name,[a[0],a[1]+length/2,a[2]],[width,length,depth],role,r,a)
    bone('root',None,[0,0,0])
    bone('body','root',[0,14,0])
    cube('hips','body',[0,14.5,.5],[6,5,5],'shadow')
    bone('torso','body',[0,16,0])
    cube('chest','torso',[0,20,0],[8,8,6],'fur',[-10,0,0],[0,17,0])
    bone('neck_1','torso',[0,24,-1])
    cube('neck_mass','neck_1',[0,25,-1],[6,4,5],'shadow')
    bone('head','neck_1',[0,26,-1])
    cube('head_mass','head',[0,28,-2.5],[7,6,7],'fur',eye=True)
    cube('snout','head',[0,26.5,-6.5],[5,3,3],'cream')
    cube('nose','head',[0,26.5,-8.1],[3,2,1],'shadow')
    cube('chin','head',[0,24.9,-5.5],[5,1,4],'shadow')
    # Dois planos de juba por lado e um topo: sem camadas de microcubos.
    for s,label in ((-1,'left'),(1,'right')):
        cube('mane_'+label,'head',[s*4.2,27,-1],[0,9,8],'fur',[0,0,s*18],[s*3,28,-1],cut='mane')
        cube('cheek_'+label,'head',[s*3.6,25,-3.6],[0,5,5],'shadow',[0,s*15,s*15],[s*3.5,27,-3],cut='fur')
        cube('mane_front_'+label,'head',[s*3.9,27,-4.9],[4,8,0],'fur',[0,0,s*20],[s*3.5,28,-4.9],cut='mane')
    cube('mane_top','head',[0,31,-1],[7,0,7],'fur',[15,0,0],[0,30,-1],cut='mane')
    for s,label in ((-1,'left'),(1,'right')):
        shoulder=[s*4.4,23.5,.1]
        elbow=[s*6.8,18.5,-.5]
        wrist=[s*8.3,13.2,-3]
        limb('arm_'+label,'torso',shoulder,elbow,4,5,'fur')
        limb('forearm_'+label,'arm_'+label,elbow,wrist,4,4,'wrap')
        bone('hand_'+label,'forearm_'+label,wrist)
        cube('hand_'+label+'_volume','hand_'+label,[s*8.4,12,-3.3],[4,3,4],'fur',[-10,0,s*8],wrist)
        cube('elbow_fur_'+label,'arm_'+label,[s*6.8,19.5,1.1],[4,5,0],'fur',[0,s*25,s*18],elbow,cut='fur')
        # Cada garra é uma curva angular de três caixas; somente três dedos visíveis.
        for i,dx in enumerate((-1.4,0,1.4)):
            x=s*(8.4+dx)
            start=[x,11.6,-4.7]
            mid=[x,8.4,-5.5]
            tip=[x,5.6,-4.8]
            r,L=rot_segmento(start,mid)
            cube(f'claw_{label}_{i}_base','hand_'+label,[x,start[1]+1.5,start[2]],[1,3,1],'cream',r,start)
            r,L=rot_segmento(mid,tip)
            cube(f'claw_{label}_{i}_tip','hand_'+label,[x,mid[1]+1.5,mid[2]],[1,3,1],'cream',r,mid)
        hip=[s*2.6,14.2,0]
        knee=[s*4.1,8.6,-1.1]
        ankle=[s*4.1,2.8,.4]
        limb('leg_'+label,'body',hip,knee,4,5,'fur')
        limb('shin_'+label,'leg_'+label,knee,ankle,3,3,'wrap')
        bone('foot_'+label,'shin_'+label,ankle)
        cube('foot_'+label+'_volume','foot_'+label,[s*4.1,1.5,-1],[5,3,5],'cream')
        for i,dx in enumerate((-1.6,0,1.6)):
            cube(f'toe_{label}_{i}','foot_'+label,[s*(4.1+dx),1,-4],[1,2,2],'shadow',[16,0,0],[s*(4.1+dx),2,-3])
    # Cauda ampla de três massas: cresce e depois afina; não é a cauda curta de um mamífero real.
    prev='body'
    for i,(a,b,w,d) in enumerate((([0,14,2],[0,13,7],5,5),([0,13,7],[0,11,13],7,7),([0,11,13],[0,7,18],6,7)),1):
        name=f'tail_{i}'
        limb(name,prev,a,b,w,d,'fur')
        prev=name
    cube('tail_tip_fur','tail_3',[0,6.5,18],[7,7,0],'fur',[-35,0,0],[0,8.5,17],cut='fur')
    # Colar e tecidos amplos; broches pequenos contam como detalhe plano.
    bone('scarf','torso',[0,25,-.3])
    cube('scarf_collar','scarf',[0,24.5,-1],[9,3,7],'wine',[-12,0,0],[0,24,-1])
    for i,(x,z,ry) in enumerate(((-1.4,7,-12),(1.5,7,18))):
        cube(f'scarf_ribbon_{i}','scarf',[x,27.4,z],[0,5,11],'wine',[-12,ry,-4],[x,26,2],cut='ribbon')
    cube('scarf_brooch','scarf',[-2.7,25.3,-5.15],[2,3,0],'gold',cut='diamond')
    cube('belt','body',[0,15,-.1],[7,2,6],'wrap')
    cube('belt_buckle','body',[0,15,-3.2],[2,2,0],'gold',cut='diamond')
    cube('tabard_front','body',[0,10.6,-3.35],[5,8,0],'wine',[-7,0,0],[0,14,-3.35],cut='tabard')
    cube('tabard_side','body',[-2.4,11.2,.2],[0,7,5],'wine',[0,-12,0],[-2.5,14,0],cut='tabard')
    cube('belt_pouch','body',[-4,15,1.6],[2,3,3],'shadow')
    paleta=ler('paleta.json')['cores']
    atlas,faces=atlas_face(cubes,paleta,128)
    atlas.save(out/'cores-bloqueio.png')
    ops=[]
    for b in bones:
        op={'op':'add_group','name':b['nome'],'origin':b['pivo']}
        if b['pai']: op['parent']=b['pai']
        ops.append(op)
    tex='data:image/png;base64,'+base64.b64encode((out/'cores-bloqueio.png').read_bytes()).decode()
    ops.append({'op':'add_texture','name':'cores_bloqueio','source':tex,'width':128,'height':128})
    for c in cubes:
        fs={k:{**v,'texture':'cores_bloqueio'} for k,v in faces[c['name']].items()}
        # Bedrock força Box UV. As faces serão reendereçadas pelo motor e pintadas em seguida.
        op={'op':'add_cube','name':c['name'],'parent':c['bone'],'from':c['from'],'to':c['to'],
            'origin':c['origin'],'rotation':c['rotation'],'box_uv':True,'texture':'cores_bloqueio'}
        ops.append(op)
    # Atlas Box UV nativo: uma ilha por cubo. Evita adulterar o formato ou gravar bbmodel à mão.
    from criaturas.ops import distribuir_uv
    mapped=[{'nome':c['name'],'from':c['from'],'to':c['to']} for c in cubes]
    uv,res=distribuir_uv(mapped,margem=1,larguras=(128,))
    ops[ len(bones) ]['width']=res[0]
    ops[ len(bones) ]['height']=res[1]
    for op in ops:
        if op['op']=='add_cube': op['uv_offset']=uv[op['name']]
    gravar(out/'geometria-autoria.json',{'ossos':bones,'cubos':cubes,'paleta':paleta,'tipo':'real','estagio':'e3'})
    # Arquivo de operações preserva o lote, sem duplicar a imagem base64 no relatório curto.
    gravar(out/'ops.json',ops)
    rev=out.name.removeprefix('blockbench-')
    target=out/f'fera-sombras-e3-blockbench-{rev}.bbmodel'
    motor.criar(target,'Fera das Sombras — Blockbench '+rev,128,128)
    motor.editar(target,ops)
    # A textura de bloqueio usa as UVs efetivas do motor; não modifica a geometria.
    from criaturas import bbmodelo
    from comum import tile
    model=bbmodelo.ler(target)
    texim=Image.new('RGBA',(128,128),(0,0,0,0))
    byname={c['name']:c for c in cubes}
    for c in model.cubos:
        for face,f in c.faces.items():
            if 'uv' not in f: continue
            u,v,U,V=[round(x) for x in f['uv']]
            if U==u or V==v: continue
            w,h=abs(U-u),abs(V-v)
            patch=tile(byname[c.nome],face,(w,h),paleta)
            if U<u: patch=patch.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            if V<v: patch=patch.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            texim.paste(patch,(min(u,U),min(v,V)))
    texim.save(out/'cores-bloqueio.png')
    src='data:image/png;base64,'+base64.b64encode((out/'cores-bloqueio.png').read_bytes()).decode()
    final_ops=[{'op':'update_texture','target':'cores_bloqueio','source':src,'width':128,'height':128}]
    gravar(out/'ops-cores.json',final_ops)
    motor.editar(target,final_ops)
    valid=motor.validar(target)
    gravar(out/'validacao-motor.json',valid)
    errors,warnings,msg=motor.resumo_validacao(valid)
    print(f'Blockbench: {len(cubes)} elementos, {len(bones)} ossos; {errors} erros, {warnings} avisos.')
    print(target)
    if errors: print('\n'.join(msg[:8]))


if __name__=='__main__':
    from PIL import Image
    construir()
