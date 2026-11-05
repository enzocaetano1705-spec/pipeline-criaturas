"""Tentativa B: autoria própria, lê só briefing/paleta comuns; não lê Blockbench."""
import sys
import numpy as np
from comum import BASE, ler, gravar, rot_segmento, atlas_face


def planejar():
    out=BASE/(sys.argv[1] if len(sys.argv)>1 else 'blender-v1')
    out.mkdir(exist_ok=False)
    bones=[]
    cubes=[]
    def group(name,parent,p): bones.append({'nome':name,'pai':parent,'pivo':p})
    def box(name,bone,p,size,role,r=None,o=None,cut=None,eye=False):
        a=np.array(p,float)-np.array(size,float)/2
        cubes.append({'name':name,'bone':bone,'from':a.tolist(),'to':(a+size).tolist(),'role':role,
                      'rotation':r or [0,0,0],'origin':o or p,'cut':cut,'eye':eye})
    def beam(name,parent,a,b,w,d,role):
        group(name,parent,a)
        rot,L=rot_segmento(a,b)
        L=max(1,round(L))
        box(name+'_box',name,[a[0],a[1]+L/2,a[2]],[w,L,d],role,rot,a)
    group('root',None,[0,0,0])
    group('body','root',[0,14,0])
    box('pelvis','body',[0,14.6,.4],[6,5,5],'shadow')
    group('torso','body',[0,17,0])
    box('ribcage','torso',[0,20.7,-.4],[8,8,6],'fur',[-13,0,0],[0,17,0])
    group('neck_1','torso',[0,24,-1])
    box('neck','neck_1',[0,24.7,-1.5],[6,4,5],'shadow')
    group('head','neck_1',[0,26,-2])
    box('skull','head',[0,28,-3],[7,6,7],'fur',[-7,0,0],[0,26,-2],eye=True)
    box('muzzle','head',[0,26.5,-7.0],[5,3,3],'cream',[-5,0,0],[0,26,-2])
    box('nose','head',[0,26.7,-8.6],[3,2,1],'shadow')
    box('lower_lip','head',[0,25,-6.4],[5,1,4],'shadow')
    # Juba repartida em poucas lâminas largas, sem modelar cada fio.
    for s,side in ((-1,'left'),(1,'right')):
        box('mane_side_'+side,'head',[s*3.8,28,-1],[0,8,8],'fur',[-12,s*12,s*15],[s*3,27,-1],cut='mane')
        box('mane_lower_'+side,'head',[s*3.7,25,-3.1],[0,5,5],'shadow',[0,s*12,s*19],[s*3,27,-2],cut='fur')
        box('mane_front_'+side,'head',[s*4.1,27,-5.1],[4,8,0],'fur',[0,0,s*18],[s*3.5,28,-5.1],cut='mane')
    box('mane_crown','head',[0,31.2,-1],[7,0,7],'fur',[16,0,0],[0,30,-2],cut='mane')
    for s,side in ((-1,'left'),(1,'right')):
        shoulder=[s*4.6,23.8,-.2]
        elbow=[s*7.2,18.7,-.2]
        wrist=[s*8.4,13.3,-3.4]
        beam('arm_'+side,'torso',shoulder,elbow,4,5,'fur')
        beam('forearm_'+side,'arm_'+side,elbow,wrist,4,4,'wrap')
        group('hand_'+side,'forearm_'+side,wrist)
        box('palm_'+side,'hand_'+side,[s*8.5,12.2,-3.8],[4,3,4],'fur',[-12,0,s*9],wrist)
        box('shoulder_fur_'+side,'arm_'+side,[s*5.6,22,2.2],[5,5,0],'fur',[0,s*20,s*20],shoulder,cut='fur')
        for i,dx in enumerate((-1.5,0,1.5)):
            start=[s*(8.5+dx),11.6,-5]
            mid=[s*(8.5+dx),8.4,-6]
            end=[s*(8.5+dx),5.5,-5.4]
            for part,(a,b) in enumerate(((start,mid),(mid,end))):
                r,L=rot_segmento(a,b)
                box(f'talon_{side}_{i}_{part}','hand_'+side,[a[0],a[1]+1.5,a[2]],[1,3,1],'cream',r,a)
        hip=[s*2.5,14.3,.2]
        knee=[s*4.2,8.5,-1.6]
        ankle=[s*4.3,2.8,.2]
        beam('leg_'+side,'body',hip,knee,4,5,'fur')
        beam('shin_'+side,'leg_'+side,knee,ankle,3,3,'wrap')
        group('foot_'+side,'shin_'+side,ankle)
        box('paw_'+side,'foot_'+side,[s*4.3,1.5,-1.3],[5,3,5],'cream')
        for i,dx in enumerate((-1.6,0,1.6)):
            box(f'foot_claw_{side}_{i}','foot_'+side,[s*(4.3+dx),.9,-4.25],[1,2,2],'shadow',[12,0,0],[s*(4.3+dx),2,-3.2])
    # A cauda recebe massas maiores no meio, independentes do plano da tentativa A.
    prev='body'
    for i,(a,b,w,d) in enumerate((([0,14,2.2],[0,13.6,7.2],5,5),([0,13.6,7.2],[0,11.3,13.2],7,7),([0,11.3,13.2],[0,7.2,18.3],6,7)),1):
        name=f'tail_{i}'
        beam(name,prev,a,b,w,d,'fur')
        # Marca creme no dorso: plano próprio, não uma nova massa branca.
        prev=name
    box('tail_fringe','tail_3',[0,7,18.2],[7,7,0],'fur',[-30,0,0],[0,9,17],cut='fur')
    group('scarf','torso',[0,25,-1])
    box('neck_wrap','scarf',[0,24.6,-1],[9,3,7],'wine',[-15,0,0],[0,24,-1])
    box('ribbon_left','scarf',[-1.2,27,7],[0,5,11],'wine',[-10,-16,-5],[-1.2,25,2],cut='ribbon')
    box('ribbon_right','scarf',[1.4,27.5,7.3],[0,5,11],'wine',[-17,20,-3],[1.4,25,2],cut='ribbon')
    box('brooch','scarf',[-2.5,25.3,-5.2],[2,3,0],'gold',cut='diamond')
    box('waist_wrap','body',[0,15,-.1],[7,2,6],'wrap')
    box('buckle','body',[0,15,-3.3],[2,2,0],'gold',cut='diamond')
    box('front_cloth','body',[0,10.7,-3.4],[5,8,0],'wine',[-8,0,0],[0,14,-3.4],cut='tabard')
    box('side_cloth','body',[-2.7,11.3,.3],[0,7,5],'wine',[0,-15,0],[-2.7,14,0],cut='tabard')
    box('pouch','body',[-4.1,15,1.7],[2,3,3],'shadow')
    palette=ler('paleta.json')['cores']
    atlas,faces=atlas_face(cubes,palette,128)
    atlas.save(out/'cores-bloqueio.png')
    data={'ossos':bones,'cubos':cubes,'faces':faces,'paleta':palette,'tipo':'real','estagio':'e3',
          'autoria':'Blender; definida a partir da entrada comum; não lê tentativa Blockbench'}
    gravar(out/'geometria-autoria.json',data)
    print(f'Plano Blender independente: {len(cubes)} elementos, {len(bones)} grupos.')


if __name__=='__main__': planejar()
