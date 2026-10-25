"""Reconstrução da F3 por proporções das referências do usuário, em saída protegida."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from criaturas import bbmodelo, motor, ops, render, texturizar

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'modelos/criatura-pavao/f3/revisao-v2'
FILE=OUT/'criatura-pavao-e3-v2b.bbmodel'
spec=importlib.util.spec_from_file_location('pavao_pintura',ROOT/'scripts/modelar-pavao-f3.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
TEAL,GREEN,CREAM,DARK,GOLD=old.TEAL,old.GREEN,old.CREAM,old.DARK,old.GOLD

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else x.tolist())+'\n',encoding='utf-8')

def build():
    bones=[];cubes=[];meta={}
    def bone(n,p,a):bones.append({'nome':n,'pai':p,'pivo':list(a)})
    def box(n,p,a,b,kind='body',rotation=None,origin=None):
        c={'nome':n,'osso':p,'from':list(a),'to':list(b)}
        if rotation is not None:c.update(rotation=list(rotation),origin=list(origin))
        cubes.append(c);meta[n]={'kind':kind}
    def segment(n,p,a,b,w,d,kind='body'):
        a,b=np.array(a,float),np.array(b,float);length=np.linalg.norm(b-a)
        box(n,p,a+[-w/2,-length,-d/2],a+[w/2,0,d/2],kind,old.euler(old.alinhar([0,-1,0],b-a)),a)
    def feather(n,p,a,b,w,normal=(0,0,-1),kind='feather'):
        a,b=np.array(a,float),np.array(b,float);axis=(b-a)/np.linalg.norm(b-a)
        normal=np.array(normal,float);normal-=axis*(normal@axis);normal/=np.linalg.norm(normal)
        across=np.cross(-axis,normal);across/=np.linalg.norm(across)
        rotation=np.column_stack([across,-axis,normal]);length=float(np.linalg.norm(b-a))
        data={'width':w,'length':length,'normal':normal.tolist(),'root':a.tolist(),'tip':b.tolist(),'frame':rotation.tolist(),'solid_leaf':kind in ['blade','fan','hip','crest']}
        if data['solid_leaf']:
            depth=.9 if kind in ['blade','fan'] else .7
            main_w=w*.82;start=length*.13;end=length-main_w/2
            box(n+'_stem',p,a+[-w*.21,-start,-depth/2],a+[w*.21,0,depth/2],kind,old.euler(rotation),a)
            box(n+'_vane',p,a+[-main_w/2,-end,-depth/2],a+[main_w/2,-start,depth/2],kind,old.euler(rotation),a)
            center=a+rotation@np.array([0,-end,0]);size=main_w/np.sqrt(2)
            box(n+'_point',p,center+[-size/2,-size/2,-depth/2],center+[size/2,size/2,depth/2],kind,old.euler(rotation@bbmodelo.matriz_rotacao([0,0,45])),center)
            for suffix in ['_stem','_vane','_point']:meta[n+suffix].update(data,leaf_id=n)
        else:
            box(n,p,a+[-w/2,-length,0],a+[w/2,0,0],kind,old.euler(rotation),a)
            meta[n].update(data,leaf_id=n)

    bone('root',None,[0,0,0]);bone('body','root',[0,25,1]);bone('pelvis','body',[0,25,1])
    box('hips','pelvis',[-4.2,22.5,-2.7],[4.2,27.2,4.3])
    bone('waist','pelvis',[0,26.5,0]);box('abdomen','waist',[-2.9,26.5,-2.8],[2.9,30.7,2.8])
    bone('torso','waist',[0,30,0]);box('ribcage','torso',[-4.5,33,-3.2],[4.5,38.8,3.5])
    box('ribcage_lower','torso',[-3.7,30,-3],[3.7,33.5,3.1])
    box('chest_top','torso',[-5.0,36.1,-2.7],[5.0,40.0,3.2])
    bone('neck_1','torso',[0,39.4,-.2]);segment('neck_lower','neck_1',[0,39.4,-.2],[0,42.3,-1.7],5.2,4.8)
    bone('neck_2','neck_1',[0,42.0,-1.6]);segment('neck_upper','neck_2',[0,42.0,-1.6],[0,46.3,-2.6],4.8,4.8)
    bone('head','neck_2',[0,46.5,-2.7]);box('skull','head',[-4.6,49,-7],[4.6,54,1.2])
    box('face_lower','head',[-3.8,46.5,-7],[3.8,49,.5])
    box('brow','head',[-4.9,51.4,-7.2],[4.9,52.7,-5.8],kind='brow')
    box('beak','head',[-2.2,46.2,-9.5],[2.2,49.0,-6.8],kind='beak')
    box('beak_hook','head',[-1.4,45.2,-11.4],[1.4,48.1,-9.2],kind='beak')
    box('forehead_gem','head',[-1.6,49.5,-7.25],[1.6,54,-7.25],kind='gem')
    feather('ventral_lappet','pelvis',[0,27.1,-2.85],[0,18.6,-3.5],5.4,kind='ventral')

    for side,s in [('left',-1),('right',1)]:
        shoulder=np.array([s*5.0,38.1,.0]);elbow=np.array([s*8.5,31.7,.8]);wrist=np.array([s*10.9,24.3,-.4])
        bone('arm_'+side,'torso',shoulder);segment('upper_arm_'+side,'arm_'+side,shoulder,elbow,3.6,3.6)
        bone('forearm_'+side,'arm_'+side,elbow);segment('forearm_solid_'+side,'forearm_'+side,elbow,wrist,3.4,3.6)
        bone('hand_'+side,'forearm_'+side,wrist);box('palm_'+side,'hand_'+side,[s*10.9-1.9,21.1,-2.2],[s*10.9+1.9,24.7,1.2],'hand')
        for j in range(3):
            a=np.array([s*(10.9+(j-1)*1.15),21.9,-1.5]);b=a+[0,-1.7,-.5]
            segment(f'finger_{side}_{j+1}','hand_'+side,a,b,1.0,1.6,'hand')
        a=np.array([s*9.3,23.8,-.6]);segment('thumb_'+side,'hand_'+side,a,a+[-s*.7,-2.0,-1.0],1.1,1.4,'hand')
        # Grandes lâminas: a área proximal cruza a inserção do cotovelo.
        blades=[([s*11.5,40.3,1.8],[s*25.2,1.5,18.5],10.0),
                ([s*10.8,36.9,3.0],[s*27.5,6.5,22.5],9.0),
                ([s*10.0,34.4,4.1],[s*24.9,13.0,23.0],8.0)]
        for j,(a,b,w) in enumerate(blades,1):
            n=f'arm_blade_{side}_{j}';bone(n,'forearm_'+side,elbow)
            feather(n+'_plane',n,a,b,w,(s*.50,0,-.87),'blade')
        segment('feather_socket_'+side,'forearm_'+side,elbow+[s*.7,.8,1.0],elbow+[s*2.6,-1.5,2.0],2.2,2.0)
        for j,(a,b,w) in enumerate([
            ([s*2.8,39.3,.4],[s*7.2,44.5,2.1],3.5),
            ([s*3.7,38.1,1.1],[s*8.8,41.1,3.0],3.8),
        ],1):feather(f'collar_{side}_{j}','torso',a,b,w,(s*.15,0,-1),'collar')
        feather('hip_plume_'+side,'pelvis',[s*2.3,26.8,-2.2],[s*7.0,14.0,-.8],6.2,(s*.25,0,-1),'hip')
        feather('hip_outer_'+side,'pelvis',[s*4.2,26,.2],[s*12.0,14.5,7],5.5,(s*.5,0,-1),'hip')

        hip=np.array([s*3.3,24.3,1]);knee=np.array([s*7.0,16.1,-1.1]);hock=np.array([s*8.4,8.4,2.2]);base=np.array([s*8.8,2.5,-.6])
        bone('leg_'+side,'pelvis',hip);segment('thigh_'+side,'leg_'+side,hip,knee,5.2,5.3)
        bone('shin_'+side,'leg_'+side,knee);segment('shank_'+side,'shin_'+side,knee,hock,3.1,3.6)
        bone('foot_'+side,'shin_'+side,hock);segment('tarsus_'+side,'foot_'+side,hock,base,2.9,3.0)
        box('foot_pad_'+side,'foot_'+side,[s*8.8-2.8,.9,-3.8],[s*8.8+2.8,2.8,1.2])
        for j in range(3):
            a=base+[s*(j-1)*1.8,-.1,-1.5];b=base+[s*(j-1)*3.8,-.2,-5.8+abs(j-1)*1.3]
            segment(f'toe_{side}_{j+1}','foot_'+side,a,b,2.0,2.2)
            c=b+[s*.15*(j-1),.4,-2.4];d=c+[s*.1*(j-1),-1.9,-1.1]
            segment(f'claw_{side}_{j+1}_base','foot_'+side,b,c,2.6,3.0,'claw')
            segment(f'claw_{side}_{j+1}_tip','foot_'+side,c,d,1.8,2.1,'claw')
        a=base+[s*1.7,-.3,1.0];b=a+[s*.6,-.1,2.3]
        segment('toe_'+side+'_back','foot_'+side,a,b,1.5,1.6)
        segment('claw_'+side+'_back','foot_'+side,b,b+[s*.3,-.7,1.3],1.1,1.4,'claw')
        feather('ankle_plume_'+side,'shin_'+side,[s*7.3,14.4,1.6],[s*9.7,9.1,2.3],3.1,(s*.5,0,-1),'ankle')

        feather('cheek_'+side,'head',[s*4.0,52.1,-3.2],[s*5.5,45.4,.8],3.0,(s*.7,0,-.7),'cheek')
        feather('nape_'+side,'head',[s*3.2,52.3,.5],[s*4.5,46.1,4.7],4.5,(s*.8,0,-.4),'nape')
        n='crest_'+side;bone(n,'head',[s*2.0,53.4,-2.3])
        a=[s*2,53.4,-2.3];b=[s*5.0,56.5,1.2];c=[s*6.0,57.5,2.5]
        segment(n+'_quill_1',n,a,b,1.3,1.0,'quill');segment(n+'_quill_2',n,b,c,1.1,.9,'quill')
        feather(n+'_leaf',n,c,[s*14.0,61.8,10],6.5,(0,0,-1),'crest')

    a=np.array([0,25,4.0]);b=np.array([0,18.4,13]);c=np.array([0,11.4,23.5])
    for n,p,start,end,w,d in [('tail_1','pelvis',a,b,7.0,6.5),('tail_2','tail_1',b,c,5.3,5.0)]:
        bone(n,p,start);segment(n+'_solid',n,start,end,w,d)
    fans=[([0,25.8,6],[0,.5,10],8.5,(0,.55,.85),'tail_1'),
          ([0,24.7,7.5],[0,1.2,45],13.0,(.3,.85,.52),'tail_1')]
    for s in [-1,1]:
        fans.extend([([s*3.6,25.5,5.5],[s*12.0,.5,12],8.5,(s*.1,.55,.85),'tail_1'),
                     ([s*3.2,27,6],[s*22.5,1.2,39],9.0,(s*.65,.25,-.72),'tail_1')])
    for j,(a,b,w,norm,p) in enumerate(fans,1):
        n=f'tail_fan_{j:02d}';bone(n,p,a);feather(n+'_plane',n,a,b,w,norm,'fan')
    locs=[('loc_ground','root',[0,0,0]),('loc_center','body',[0,30,0]),('loc_top','head',[0,65,0]),
          ('loc_head_look','head',[0,50,-7]),('loc_mouth','head',[0,47,-11.4]),('loc_tail_tip','tail_1',[0,.5,45])]
    for side,s in [('left',-1),('right',1)]:locs.extend([('loc_hand_'+side,'hand_'+side,[s*10.9,21,-2]),('loc_foot_'+side,'foot_'+side,[s*8.8,1,-7])])
    return bones,cubes,meta,locs

def feather_color(info,c,p):
    w=info['width'];length=info['length'];q=(p-np.array(info['root']))@np.array(info['frame']);x=q[0];v=-q[1]/length
    kind=info['kind']
    knots=[0,.10,.28,.62,.86,1];widths=[.16,.39,.50,.44,.24,0]
    if kind=='fan':knots=[0,.15,.35,.75,.90,1];widths=[.12,.30,.50,.50,.35,0]
    half=w*float(np.interp(v,knots,widths))
    # Dois recortes largos de barbas, sem voxelizar cada pixel da borda.
    half-=.18*(1-((v*length/3)%1))
    if not info['solid_leaf'] and (abs(x)>max(.12,half) or not 0<=v<=1):return None
    if kind in ['fan','crest']:
        leaf=info['leaf_id'];pos=(.68 if leaf=='tail_fan_01_plane' else .62 if leaf in ['tail_fan_03_plane','tail_fan_05_plane'] else .70) if kind=='fan' else .61
        e=(x/(w*.20))**2+((v-pos)/(.11 if kind=='fan' else .12))**2
        if e<.34:return old.rgb('#03273c')
        if e<1:return TEAL[2]
        if e<1.6:return TEAL[3]
    if kind=='ventral':return CREAM[4 if abs(x)<half*.75 else 3]
    if kind in ['collar','nape','cheek']:return TEAL[1 if v>.55 else 3 if int(v*length)%3 else 4]
    cream=v>(.63+.14*(1-abs(x)/max(half,.1))) if kind in ['hip','ankle'] else v>.86
    if kind=='blade':
        inward=x*(-1 if '_left_' in c.nome else 1)
        cream=(v>.32 and inward>w*(.03+.06*v)) or v>.85
    if cream:return CREAM[3 if abs(x)>half-.5 else 4 if int(x+v*4)%4 else 5]
    if abs(x)>half-.3:return TEAL[1]
    k=int(v*length/2+abs(x)/2)
    if kind=='crest':return GREEN[4] if v>.60 else TEAL[4 if k%3 else 5]
    if kind=='fan':return GREEN[3+k%2] if v>.55 else TEAL[3+k%3]
    return GREEN[3 if k%3 else 4] if v>.4 and x>0 else TEAL[4 if k%4 else 5]

def solid_color(c,face,p):
    n=c.nome;x,y,z=p;rel=(p-c.de)/np.maximum(c.tamanho,1e-9)
    if n.startswith(('claw','finger','thumb','palm')):return DARK[3 if face=='up' else 2 if face in ['north','east'] else 1]
    if n.startswith('beak'):return CREAM[5 if face=='up' else 4 if face=='north' else 3]
    if n.startswith('crest_'):return TEAL[5 if face=='up' else 4]
    if n=='brow':return TEAL[2 if face=='north' else 4]
    a,b=old.g2._coords(face,x,y,z);ramp=TEAL;value=.5 if face=='up' else -1 if face=='down' else 0
    if n in ['hips','abdomen','ribcage','ribcage_lower','chest_top','neck_lower','neck_upper']:
        normal=bbmodelo.matriz_rotacao(c.rotacao)@np.array(render.NORMAIS[face])
        if normal[2]<-.5 and abs(x)<(.5*c.tamanho[0]-.3 if n.startswith('neck') else c.tamanho[0]*.34):ramp=CREAM
    if n in ['skull','face_lower']:
        if face=='north':
            if y<48.2:ramp=CREAM
            q=abs(x)
            if 1.6<q<4.1 and 47.9<y<51.3:
                if y>50.8 or q>3.7:return DARK[0]
                if 2.2<q<3.0 and y>48.3:return DARK[0]
                return GOLD[2 if y<49.5 else 1]
            if 1.4<q<4.3 and y<48.0:ramp=CREAM
        if face in ['east','west']:
            if z< -3.5 and 47.9<y<51.3:
                if y>50.8 or z> -4:return DARK[0]
                return DARK[0] if -6.0<z< -5 else GOLD[2]
            if y<48.0:ramp=CREAM
    block=(int(a//2)*17+int(b//2)*31+sum(map(ord,n)))%13
    if ramp is CREAM:return CREAM[3 if block<3 else 4 if block<11 else 5]
    return TEAL[4 if block<3 else 5 if block<11 else 6]

def paint(m,meta):
    res=m.resolucao[0];tex=np.zeros((res,res,4),np.uint8);mats=bbmodelo.matrizes_ossos(m)
    for c in m.cubos:
        info=meta[c.nome];matrix=bbmodelo.matriz_cubo(m,c,mats)
        for face in c.faces:
            rows=texturizar.texels_da_face(c,face,np.eye(4))
            if rows is None:continue
            for (u,v),p in zip(*rows):
                if info['kind']=='gem':
                    center=(c.de+c.ate)/2;dx=(p[0]-center[0])/1.6;dy=(p[1]-center[1])/2.25
                    color=None if abs(dx)+abs(dy)>1 else GOLD[3 if dx<0 else 1 if dy<0 else 2]
                elif 'width' in info:
                    world=bbmodelo.aplicar(matrix,[p])[0]
                    color=feather_color(info,c,world)
                else:color=solid_color(c,face,p)
                if color is not None and 0<=u<res and 0<=v<res:tex[int(v),int(u)]=[*color,255]
    return tex

class Perspective:
    def __init__(self,position,target,size=(384,360),fov=21):
        self.position=np.array(position,float);self.tamanho=size
        self.frente=np.array(target,float)-self.position;self.frente/=np.linalg.norm(self.frente)
        self.direita=np.cross(self.frente,[0,1,0]);self.direita/=np.linalg.norm(self.direita)
        self.cima=np.cross(self.direita,self.frente);self.focal=size[1]/(2*np.tan(np.radians(fov/2)))
    def pixel(self,points):
        delta=np.atleast_2d(points)-self.position;depth=delta@self.frente
        return np.column_stack([self.tamanho[0]/2+self.focal*(delta@self.direita)/depth,
                                self.tamanho[1]/2-self.focal*(delta@self.cima)/depth])

def render_compare(m):
    # Perspectiva: os pés são vistos mais de cima que a cabeça, como nas referências.
    sheet=Image.new('RGB',(768,768),'white');draw=ImageDraw.Draw(sheet)
    for row,(name,angle) in enumerate([('frente',(0,5)),('lado',(65,8))]):
        ref=Image.open(OUT/(name+'-768.png')).convert('RGB');ref.thumbnail((370,352))
        sheet.paste(ref,((384-ref.width)//2,row*384+24))
        if row:
            az=np.radians(65);target=[0,29.5,16];position=[-180*np.sin(az),70,16-180*np.cos(az)]
        else:target=[0,29.5,8];position=[0,70,-180]
        proj=Perspective(position,target)
        im,mask,ids,_=render.renderizar(m,projecao=proj,sombreado=.15)
        sheet.paste(im,(384,row*384+24));draw.text((8,row*384+5),name+' | referencia',fill='black');draw.text((392,row*384+5),'modelo | perspectiva',fill='black')
        im.save(OUT/(name+'-modelo.png'))
    sheet.save(OUT/'comparacao.png')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--refazer',action='store_true');args=ap.parse_args();OUT.mkdir(exist_ok=True)
    prov=OUT/'proveniencia.json'
    if FILE.exists():
        prior=json.loads(prov.read_text()) if prov.exists() else {}
        if not args.refazer or prior.get('saida_sha256')!=sha(FILE):raise SystemExit('Saída existente/editada preservada; crie nova versão.')
    bones,cubes,meta,locs=build();offsets,(res,_)=ops.distribuir_uv(cubes,margem=1,larguras=(256,512))
    batch=[{'op':'add_group','name':b['nome'],'origin':b['pivo'],**({'parent':b['pai']} if b['pai'] else {})} for b in bones]
    for c in cubes:
        o={'op':'add_cube','name':c['nome'],'parent':c['osso'],'from':c['from'],'to':c['to'],'box_uv':True,'uv_offset':offsets[c['nome']]}
        if 'rotation' in c:o.update(rotation=c['rotation'],origin=c['origin'])
        batch.append(o)
    for n,p,a in locs:batch.append({'op':'add_locator','name':n,'parent':p,'position':a})
    batch=json.loads(json.dumps(batch,default=lambda x:x.item() if isinstance(x,np.generic) else x.tolist()))
    dump(OUT/'geometria.ops.json',batch);motor.criar(FILE,FILE.stem,res,res);motor.editar(FILE,batch)
    dump(prov,{'saida_sha256':sha(FILE),'status':'geometria-gerada-pintura-pendente'})
    m=bbmodelo.ler(FILE);tex=paint(m,meta);Image.fromarray(tex).save(OUT/'textura.png');texturizar.aplicar_no_modelo(FILE,tex,m,[])
    dump(prov,{'saida_sha256':sha(FILE),'status':'em-revisao-artistica','pecas':len(cubes),'ossos':len(bones),'atlas':res,'fonte_design':'imagens-fonte.json','fonte_anterior_preservada':'../criatura-pavao-e3.bbmodel'})
    dump(OUT/'plano-cubos.json',{'ossos':bones,'cubos':cubes,'materiais':meta,'locators':locs,'atlas':res})
    render_compare(bbmodelo.ler(FILE));print('F3 v2:',len(cubes),'peças;',len(bones),'ossos; atlas',res,'; comparacao.png 768 px.')

if __name__=='__main__':main()
