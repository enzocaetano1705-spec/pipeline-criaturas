"""Reconstrução facetada por seções medidas no perfil, com largura das outras vistas.
Não importa qualquer malha externa. Os gabaritos são empties excluídos do render.
"""
import bpy,bmesh,json,math,sys,time
from pathlib import Path
from mathutils import Vector,Matrix

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'modelos/fera-fera-agil-das-sombras/gabarito-v1'
REV=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'r01'
OUT=BASE/REV
SCALE=92.0;ORIGIN_U=360;GROUND_V=395
PARTS=[];LANDMARKS=[]


def dump(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def world(u,v,x=0):return Vector((x,(u-ORIGIN_U)/SCALE,(GROUND_V-v)/SCALE))


def newmesh(name,verts,faces):
    me=bpy.data.meshes.new(name+'_mesh');me.from_pydata(verts,[],faces);me.update()
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    ob=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(MAT)
    ob['fonte']='seções e landmarks do gabarito; autoria por código'
    return ob


def loft(name,sections,axis='path',n=8):
    # sections = (u_pixel,v_pixel,x_world,halfwidth_x,halfwidth_profile)
    pts=[world(u,v,x) for u,v,x,rx,rz in sections];verts=[];faces=[]
    for j,(p,section) in enumerate(zip(pts,sections)):
        rx,rz=section[3:]
        if axis=='y':v=Vector((0,0,1))
        elif axis=='z':v=Vector((0,1,0))
        else:
            t=pts[min(j+1,len(pts)-1)]-pts[max(0,j-1)]
            t.x=0;t.normalize();v=Vector((0,-t.z,t.y))
        for i in range(n):
            a=i*2*math.pi/n
            verts.append(tuple(p+Vector((rx*math.cos(a),0,0))+v*rz*math.sin(a)))
    for j in range(len(pts)-1):
        for i in range(n):faces.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    faces.append(tuple(reversed(range(n))));faces.append(tuple((len(pts)-1)*n+i for i in range(n)))
    ob=newmesh(name,verts,faces)
    PARTS.append({'nome':name,'tipo':'loft','eixo_secao':axis,'secoes_pixel_e_largura':sections})
    return ob


def shard(name,polygon,x,width):
    # Polygon silhouette with two bevelled faces and a central perimeter ridge.
    pts=[world(u,v,x(u,v) if callable(x) else x) for u,v in polygon];center=sum(pts,Vector())/len(pts)
    verts=[tuple(p) for p in pts]
    for sign in (-1,1):
        verts.extend(tuple(center+(p-center)*.74+Vector((sign*(width(*uv) if callable(width) else width),0,0))) for p,uv in zip(pts,polygon))
    count=len(pts);faces=[]
    for i in range(count):
        j=(i+1)%count
        faces.extend(((i,j,count+j,count+i),(j,i,2*count+i,2*count+j)))
    faces.append(tuple(count+i for i in reversed(range(count))))
    faces.append(tuple(2*count+i for i in range(count)))
    ob=newmesh(name,verts,faces)
    PARTS.append({'nome':name,'tipo':'volume_silhueta','poligono_pixel':polygon,'centro_x':'restrito pela frente' if callable(x) else x,'meia_espessura':'variável pela parte' if callable(width) else width})
    return ob


def mask_ranges():
    # Blender loads the mask itself: no optional scientific dependency in the host.
    im=bpy.data.images.load(str(BASE/'entrada/perfil_esquerdo-mascara.png'),check_existing=False)
    w,h=im.size;pixels=list(im.pixels)
    def interval(x,low,high):
        ys=[y for y in range(low,high) if pixels[((h-1-y)*w+x)*4]>.5]
        return (min(ys),max(ys)) if ys else None
    return interval


def anatomy():
    interval=mask_ranges()
    contours=json.loads((BASE/'entrada/contornos-partes.json').read_text(encoding='utf-8'))
    # Main head+crest height follows the observed contour column by column.
    sections=[]
    for u in list(range(114,294,4))+[294]:
        r=interval(u,70,211)
        if not r:continue
        top,bottom=r
        width=.30+min(.50,max(0,(u-118)/100*.50))
        if u>254:width-=.004*(u-254)
        sections.append((u,(top+bottom)/2,0,width,max(.035,(bottom-top)/2/SCALE)))
    loft('head_and_mane_profile',sections,'y')
    shard('mane_back_profile',contours['mane_back_profile']['poligono'],0,.55)
    loft('neck',[(270,180,0,.48,.28),(292,195,0,.48,.34),(318,210,0,.50,.34)])
    loft('torso',[(316,190,0,.48,.27),(331,216,0,.59,.34),(343,243,0,.58,.34),(337,265,0,.56,.31),(316,285,0,.48,.25)],'z')
    shard('torso_profile_trace',contours['torso_profile']['poligono'],0,.52)
    shard('back_fur',[(342,170),(366,180),(389,189),(395,201),(378,202),(401,214),(385,222),(403,239),(384,237),(372,222),(358,217),(343,202)],0,.57)
    for s,side in ((-1,'left'),(1,'right')):
        loft('upper_arm_'+side,[(342,194,s*.76,.32,.35),(303,218,s*.98,.36,.34),(260,243,s*1.23,.34,.30)])
        shard('forearm_'+side,contours['forearm_profile']['poligono'],lambda u,v,s=s:s*(1.23+(260-u)/86*.45),.32)
        loft('palm_'+side,[(173,283,s*1.69,.30,.20),(151,298,s*1.70,.32,.25),(150,312,s*1.70,.26,.18)])
        claws=[[(135,297),(121,320),(116,342),(128,363)],[(149,299),(138,326),(134,349),(137,365)],[(168,300),(158,325),(150,347),(149,357)]]
        for i,path in enumerate(claws):
            dx=(-.21,0,.21)[i]
            loft('claw_'+side+str(i),[(u,v,s*(1.70+dx),r,r*1.2) for (u,v),r in zip(path,(.09,.075,.045,.006))])
        shard('leg_and_paw_'+side,contours['leg_profile']['poligono'],lambda u,v,s=s:s*(.55+.21*min(1,max(0,(v-280)/100))),lambda u,v:.28 if v<352 else .25+.26*min(1,(v-352)/22))
        # Side fur planes retain the profile but distribute their mass across X.
        shard('cheek_'+side,[(204,171),(250,169),(261,181),(235,203),(225,185),(213,194)],s*.65,.10)
        shard('shoulder_fur_'+side,[(299,183),(340,185),(363,205),(344,205),(358,221),(329,215),(322,229),(303,210)],s*.72,.12)
        shard('hip_fur_'+side,[(305,271),(330,274),(340,296),(325,292),(330,314),(308,305),(292,301)],s*.56,.11)
    tail=[(348,294,0,.35,.24),(370,297,0,.4,.32),(390,296,0,.44,.48)]
    for u in list(range(399,628,6))+[627]:
        r=interval(u,235,390)
        if not r:continue
        top,bottom=r
        t=(u-399)/(627-399);width=.32+.42*math.sin(math.pi*t)**.8
        if u>610:width*=max(.10,(635-u)/25)
        tail.append((u,(top+bottom)/2,0,width,max(.035,(bottom-top)/2/SCALE)))
    loft('tail_profile',tail,'y')
    # Broad folds/torn hems come from the guide; all pieces have actual volume.
    shard('mantle_neck',[(245,171),(267,162),(313,171),(342,185),(337,211),(308,207),(284,228),(268,208),(252,206)],0,.69)
    shard('mantle_trailing',[(317,135),(344,122),(363,99),(390,80),(411,83),(395,94),(426,114),(454,118),(478,140),(481,166),(470,154),(463,140),(441,138),(444,127),(423,126),(411,137),(393,132),(386,145),(370,137),(363,125),(345,139)],-.28,.045)
    shard('belt',[(311,258),(354,253),(370,266),(346,281),(313,284),(301,274)],0,.66)
    shard('tabard_front',[(300,275),(322,277),(326,294),(314,317),(303,302),(295,320),(284,304)],0,.46)
    shard('tabard_back',[(340,277),(360,277),(378,300),(365,314),(355,302),(348,321)],0,.43)
    shard('pouch',[(364,244),(390,244),(396,270),(369,280),(359,258)],-.71,.12)
    for name,uv in [('nose',(116,178)),('crown',(272,80)),('shoulder',(342,194)),('hip',(316,280)),('ankle',(307,359)),('tail_tip',(627,379))]:
        LANDMARKS.append({'nome':name,'perfil_pixel':uv,'world':list(world(*uv))})


def setup():
    sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.render.film_transparent=True
    sc.render.image_settings.file_format='PNG';sc.render.threads_mode='FIXED';sc.render.threads=2
    sc.view_settings.view_transform='Standard';sc.view_settings.exposure=-.4;sc.world.color=(.4,.4,.4)
    for i,(p,power) in enumerate((((-5,-5,8),1200),((5,1,6),1100),((0,5,5),1000))):
        l=bpy.data.lights.new('Softbox_'+str(i),'AREA');l.energy=power;l.shape='DISK';l.size=5
        ob=bpy.data.objects.new(l.name,l);sc.collection.objects.link(ob);ob.location=p;ob.rotation_euler=(Vector((0,0,1.7))-ob.location).to_track_quat('-Z','Y').to_euler()
    data=bpy.data.cameras.new('Camera_gabarito');data.type='ORTHO'
    cam=bpy.data.objects.new(data.name,data);sc.collection.objects.link(cam);sc.camera=cam
    return cam


def setcam(cam,kind):
    sc=bpy.context.scene
    if kind=='perfil':
        sc.render.resolution_x=728;sc.render.resolution_y=466
        target=world(364,233);direction=Vector((1,0,0));height=466/SCALE
    elif kind=='frente':
        sc.render.resolution_x=644;sc.render.resolution_y=497
        target=Vector((0,0,1.63));e=math.radians(8);direction=Vector((0,-math.cos(e),math.sin(e)));height=497/SCALE
    elif kind=='costas':
        sc.render.resolution_x=577;sc.render.resolution_y=524
        target=Vector((0,.2,1.6));e=math.radians(17);direction=Vector((0,math.cos(e),math.sin(e)));height=524/SCALE
    else:
        sc.render.resolution_x=640;sc.render.resolution_y=640
        target=Vector((0,.12,1.7));direction=Vector((.8,-.8,.35)).normalized();height=6.6
    sc.render.resolution_percentage=100
    cam.location=target+direction*20;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=5
    frame=cam.data.view_frame(scene=sc);h=max(p.y for p in frame)-min(p.y for p in frame)
    cam.data.ortho_scale*=height/h
    return {'tipo':'ortográfica','localizacao':list(cam.location),'rotacao':list(cam.rotation_euler),'escala':cam.data.ortho_scale,'resolucao':[sc.render.resolution_x,sc.render.resolution_y],'elevacao_assumida':0 if kind=='perfil' else 8 if kind=='frente' else 17 if kind=='costas' else None}


def reference_empty():
    im=bpy.data.images.load(str(BASE/'entrada/perfil_esquerdo.png'),check_existing=False);im.pack()
    ob=bpy.data.objects.new('GABARITO_PERFIL_excluido_do_render',None);bpy.context.scene.collection.objects.link(ob)
    ob.empty_display_type='IMAGE';ob.data=im;ob.empty_display_size=728/SCALE
    ob.color=(1,1,1,.35);ob.empty_image_depth='BACK';ob.hide_render=True
    ob.location=world(364,233,-3)
    ob.rotation_euler=Matrix(((0,0,1),(1,0,0),(0,1,0))).to_euler()
    if hasattr(ob,'show_empty_image_perspective'):ob.show_empty_image_perspective=False
    ob['uso']='perfil em vista lateral +X, fundo apenas para modelagem; não participa das métricas'


def main():
    global MAT
    start=time.perf_counter();OUT.mkdir(exist_ok=False)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    MAT=bpy.data.materials.new('Argila_neutra');MAT.use_nodes=True
    p=next(n for n in MAT.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(.26,.27,.28,1);p.inputs['Roughness'].default_value=.9
    anatomy();cam=setup();reference_empty();camera=setcam(cam,'perfil')
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    bad=[];polys=0;meshdata=[]
    for ob in meshes:
        bm=bmesh.new();bm.from_mesh(ob.data)
        if any(not e.is_manifold for e in bm.edges):bad.append(ob.name)
        bm.free();polys+=sum(len(p.vertices)-2 for p in ob.data.polygons)
        meshdata.append({'nome':ob.name,'vertices':[list(ob.matrix_world@v.co) for v in ob.data.vertices],'faces':[list(p.vertices) for p in ob.data.polygons]})
    if bad:raise RuntimeError('Volumes abertos: '+str(bad))
    dump('plano-gabarito.json',{'metodo':'seções do perfil; larguras restringidas pela frente; volumes facetados','escala_px_unidade':SCALE,'origem_pixel':[ORIGIN_U,GROUND_V],'partes':PARTS,'landmarks':LANDMARKS,'hipotese_camera':camera,'geometria_aprovada':False})
    dump('malha-projecao.json',meshdata)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'fera-gabarito.blend'),compress=True)
    cameras={}
    for view in ('perfil','frente','costas','3-4'):
        cameras[view]=setcam(cam,view);bpy.context.scene.render.filepath=str(OUT/(view+'.png'));bpy.ops.render.render(write_still=True)
    dump('validacao.json',{'triangulos':polys,'volumes':len(meshes),'volumes_abertos':bad,'cameras':cameras,'referencia_renderizada':False,'textura':'nenhuma; cinza para julgar forma','rig':'pendente','segundos':time.perf_counter()-start})
    print('GABARITO_OK '+json.dumps({'triangulos':polys,'volumes':len(meshes),'abertos':bad,'segundos':round(time.perf_counter()-start,2)}))


if __name__=='__main__':main()
