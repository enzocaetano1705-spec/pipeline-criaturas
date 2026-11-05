"""Autoria orgânica da F3, executada somente pelo Blender CLI, nunca pelo MCP.

Superfície corporal fundida por voxels, unhas/olhos/vestuário autorais. O mestre
fica preservado; a cópia de apresentação é reduzida, sem alegar retopologia de rig.
"""
import bpy,bmesh,math,json,sys,time,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'modelos/fera-fera-agil-das-sombras/organico-v1'
REV=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'r01'
OUT=BASE/REV
T0=time.perf_counter()
SOFT=[]
STATS={}
COLORS={'fur':'915640','cream':'ead0a0','dark':'352320','wine':'792434','wine_light':'9e3546',
        'wrap':'49332c','gold':'d9a344','ivory':'ead4a6','iris':'d99a29','pupil':'171510'}


def dump(name,data):
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def srgb(h):return tuple(int(h[i:i+2],16)/255 for i in (0,2,4))


def linear(c):return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4


def material(name,color,rough=.75,noise=0):
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    p=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*[linear(x) for x in srgb(color)],1)
    p.inputs['Roughness'].default_value=rough
    if 'Specular IOR Level' in p.inputs:p.inputs['Specular IOR Level'].default_value=.25
    if noise:
        tex=mat.node_tree.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=110
        tex.inputs['Detail'].default_value=2
        bump=mat.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18
        bump.inputs['Distance'].default_value=noise
        mat.node_tree.links.new(tex.outputs['Fac'],bump.inputs['Height'])
        mat.node_tree.links.new(bump.outputs['Normal'],p.inputs['Normal'])
    return mat


def mesh(name,verts,faces,mat=None,soft=False):
    data=bpy.data.meshes.new(name+'_mesh');data.from_pydata(verts,[],faces);data.update()
    ob=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(ob)
    if mat:ob.data.materials.append(mat)
    for poly in data.polygons:poly.use_smooth=True
    if soft:SOFT.append(ob)
    return ob


def sphere(name,c,r,soft=True,mat=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24 if soft else 16,ring_count=16 if soft else 10,radius=1,location=c)
    ob=bpy.context.object;ob.name=name
    for v in ob.data.vertices:v.co=Vector((v.co.x*r[0],v.co.y*r[1],v.co.z*r[2]))
    for p in ob.data.polygons:p.use_smooth=True
    if mat:ob.data.materials.append(mat)
    if soft:SOFT.append(ob)
    return ob


def sample_path(points,radii,steps=4):
    pts=[Vector(p) for p in points];res=[];rs=[]
    for j in range(len(pts)-1):
        p0,p1,p2,p3=pts[max(0,j-1)],pts[j],pts[j+1],pts[min(len(pts)-1,j+2)]
        for k in range(steps):
            t=k/steps
            p=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t)
            res.append(p)
            rs.append(tuple((1-t)*a+t*b for a,b in zip(radii[j],radii[j+1])))
    return res+[pts[-1]],rs+[radii[-1]]


def tube(name,points,radii,sides=12,steps=4,soft=False,mat=None):
    pts,rs=sample_path(points,radii,steps)
    verts=[];faces=[]
    for j,(p,(rx,ry)) in enumerate(zip(pts,rs)):
        tangent=(pts[min(len(pts)-1,j+1)]-pts[max(0,j-1)]).normalized()
        u=Vector((1,0,0))
        if abs(tangent.dot(u))>.94:u=Vector((0,1,0))
        u=(u-tangent*u.dot(tangent)).normalized();v=tangent.cross(u).normalized()
        for i in range(sides):
            a=i*2*math.pi/sides
            verts.append(tuple(p+u*rx*math.cos(a)+v*ry*math.sin(a)))
    for j in range(len(pts)-1):
        for i in range(sides):
            a=j*sides+i;b=j*sides+(i+1)%sides
            faces.append((a,b,b+sides,a+sides))
    verts.extend((tuple(pts[0]),tuple(pts[-1])))
    for i in range(sides):
        faces.append((len(verts)-2,(i+1)%sides,i))
        a=(len(pts)-1)*sides
        faces.append((len(verts)-1,a+i,a+(i+1)%sides))
    ob=mesh(name,verts,faces,mat,soft)
    # Consistent normals on lofts, including reversed limb paths.
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    return ob


def lock(name,root,tip,width,depth=None):
    root,tip=Vector(root),Vector(tip)
    p=root.lerp(tip,.48)+Vector((0,-.025,.04))
    return tube(name,[root,p,tip],[(width*.72,(depth or width)*.62),(width,depth or width),(.004,.004)],10,3,True)


def ribbon(name,outline,mapper,thickness,mat):
    front=[Vector(mapper(u,w)) for u,w in outline]
    n=len(front);verts=[tuple(v+Vector((0,-thickness/2,0))) for v in front]+[tuple(v+Vector((0,thickness/2,0))) for v in front]
    tris=tessellate_polygon([front])
    def idx(v):return v if isinstance(v,int) else min(range(n),key=lambda i:(front[i]-v).length_squared)
    faces=[]
    for tri in tris:
        inds=tuple(idx(v) for v in tri);faces.append(inds);faces.append(tuple(i+n for i in reversed(inds)))
    for i in range(n):faces.append((i,(i+1)%n,(i+1)%n+n,i+n))
    ob=mesh(name,verts,faces,mat)
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    return ob


def line(name,points,r,mat):return tube(name,points,[(r,r)]*len(points),8,1,False,mat)


def components(me):
    links=[[] for _ in me.vertices]
    for e in me.edges:
        a,b=e.vertices;links[a].append(b);links[b].append(a)
    seen=set();sizes=[]
    for i in range(len(links)):
        if i in seen:continue
        stack=[i];seen.add(i);size=0
        while stack:
            u=stack.pop();size+=1
            for v in links[u]:
                if v not in seen:seen.add(v);stack.append(v)
        sizes.append(size)
    return sorted(sizes,reverse=True)


def clean_voxel_specks(ob):
    """Remove somente ilhas do tamanho de 1–2 voxels; não descarta partes anatômicas."""
    bm=bmesh.new();bm.from_mesh(ob.data);seen=set();remove=[];removed=[]
    for v in bm.verts:
        if v in seen:continue
        group=[];stack=[v];seen.add(v)
        while stack:
            u=stack.pop();group.append(u)
            for e in u.link_edges:
                n=e.other_vert(u)
                if n not in seen:seen.add(n);stack.append(n)
        if len(group)>16:continue
        dims=[max(v.co[i] for v in group)-min(v.co[i] for v in group) for i in range(3)]
        if max(dims)<.08:
            removed.append({'vertices':len(group),'dimensoes':dims});remove.extend(group)
    if remove:bmesh.ops.delete(bm,geom=remove,context='VERTS')
    bm.to_mesh(ob.data);bm.free();STATS['artefatos_voxel_removidos']=removed


def body():
    tube('torso_base',[(0,.04,1.4),(0,.02,1.65),(0,-.04,1.92),(0,-.1,2.2),(0,-.12,2.5),(0,-.09,2.72),(0,-.1,2.86)],
         [(.29,.25),(.36,.26),(.33,.23),(.36,.29),(.50,.31),(.48,.29),(.3,.24)],24,4,True)
    sphere('neck_base',(0,-.24,2.89),(.29,.30,.38))
    sphere('cranium',(0,-.43,3.23),(.40,.43,.43))
    sphere('jaw',(0,-.59,3.02),(.30,.34,.20))
    sphere('muzzle',(0,-.82,3.09),(.29,.28,.18))
    sphere('nose_bridge',(0,-.86,3.22),(.16,.16,.20))
    for s,side in ((-1,'left'),(1,'right')):
        tube('arm_'+side,[(s*.43,-.06,2.73),(s*.65,-.04,2.48),(s*.79,-.09,2.12),(s*.90,-.23,1.73),(s*.96,-.31,1.48)],
             [(.30,.29),(.29,.25),(.25,.23),(.22,.21),(.19,.18)],18,4,True)
        sphere('deltoid_'+side,(s*.49,-.06,2.66),(.32,.30,.37))
        sphere('palm_'+side,(s*.99,-.36,1.30),(.24,.21,.26))
        for i,dx in enumerate((-.14,0,.14)):
            x=s*(.99+dx)
            tube('digit_'+side+str(i),[(x,-.37,1.30),(x,-.47,1.16),(x+s*.02,-.53,1.12)],[(.105,.105),(.09,.1),(.075,.08)],12,3,True)
        tube('leg_'+side,[(s*.25,.02,1.53),(s*.39,-.09,1.27),(s*.48,-.20,1.03),(s*.47,-.02,.69),(s*.45,.015,.34)],
             [(.26,.25),(.28,.25),(.21,.21),(.17,.17),(.13,.14)],18,4,True)
        sphere('paw_'+side,(s*.45,-.18,.18),(.26,.34,.17))
        for i,dx in enumerate((-.15,0,.15)):sphere('toe_'+side+str(i),(s*(.45+dx),-.37,.16),(.105,.18,.11))
        tube('brow_'+side,[(s*.06,-.84,3.31),(s*.20,-.80,3.365),(s*.31,-.67,3.40)],[(.04,.04),(.045,.045),(.035,.035)],12,3,True)
        locks=[((s*.27,-.1,3.37),(s*.53,.35,3.67),.19),((s*.39,-.08,3.23),(s*.70,.23,3.42),.21),
               ((s*.37,-.20,3.03),(s*.63,.07,2.91),.18),((s*.18,-.14,3.54),(s*.33,.25,3.88),.19),
               ((s*.44,-.02,2.76),(s*.82,.12,2.51),.18),((s*.60,.03,2.47),(s*.91,.17,2.20),.16),
               ((s*.73,.04,2.18),(s*1.02,.10,1.92),.14),((s*.33,.00,1.40),(s*.63,.12,1.14),.15),
               ((s*.43,-.02,1.17),(s*.66,.10,.94),.13),
               ((s*.28,-.55,3.20),(s*.48,-.24,2.98),.17),
               ((s*.32,-.35,3.30),(s*.63,.05,3.13),.17),
               ((s*.25,-.58,3.03),(s*.42,-.29,2.87),.12)]
        for i,(a,b,w) in enumerate(locks):lock('fur_'+side+str(i),a,b,w,w*.70)
    lock('crest',(0,-.06,3.54),(0,.25,3.98),.20,.15)
    # Tufts of the breast and shoulder blades, integrated into the same body surface.
    for s in (-1,1):
        lock('breast_'+str(s),(s*.12,-.32,2.58),(s*.12,-.41,2.24),.15,.10)
        lock('back_'+str(s),(s*.19,.18,2.54),(s*.31,.34,2.20),.18,.12)
    tp=[(0,.18,1.52),(.02,.61,1.40),(.04,1.08,1.16),(.04,1.58,.86),(.03,1.99,.48),(.02,2.17,.30)]
    tr=[(.22,.23),(.36,.35),(.49,.47),(.51,.49),(.31,.36),(.012,.012)]
    tube('tail_core',tp,tr,24,5,True)
    for j in range(1,5):
        c=Vector(tp[j]);r=tr[j][0]
        for s in (-1,1):
            lock(f'tail_side_{j}_{s}',c+Vector((s*r*.66,0,.02)),c+Vector((s*(r+.15),.30,-.28)),.17,.12)
        lock('tail_dorsal_'+str(j),c+Vector((0,0,tr[j][1]*.65)),c+Vector((0,.32,tr[j][1]*.58)),.16,.11)
    bpy.ops.object.select_all(action='DESELECT')
    for ob in SOFT:ob.select_set(True)
    bpy.context.view_layer.objects.active=SOFT[0]
    bpy.ops.object.join();ob=bpy.context.object;ob.name='body_sculpt_master'
    ob.data.remesh_voxel_size=.024
    if hasattr(ob.data,'use_remesh_preserve_volume'):ob.data.use_remesh_preserve_volume=True
    bpy.ops.object.voxel_remesh()
    smooth=ob.modifiers.new('Relaxamento_superficie','SMOOTH');smooth.factor=.62;smooth.iterations=3
    bpy.ops.object.modifier_apply(modifier=smooth.name)
    clean_voxel_specks(ob)
    STATS['mestre_componentes']=components(ob.data)
    if len(STATS['mestre_componentes'])!=1:raise RuntimeError('Corpo deve ser uma única superfície conectada: '+str(STATS['mestre_componentes']))
    for p in ob.data.polygons:p.use_smooth=True
    master_collection=bpy.data.collections.new('Mestre_preservado_nao_exportar');bpy.context.scene.collection.children.link(master_collection)
    for c in list(ob.users_collection):c.objects.unlink(ob)
    master_collection.objects.link(ob)
    preview=ob.copy();preview.data=ob.data.copy();bpy.context.scene.collection.objects.link(preview)
    preview.name='body_game_preview'
    ob.hide_render=True;ob.hide_set(True)
    bpy.context.view_layer.objects.active=preview;preview.select_set(True);ob.select_set(False)
    tris=sum(len(p.vertices)-2 for p in preview.data.polygons)
    dec=preview.modifiers.new('Reducao_apresentacao_nao_retopologia','DECIMATE');dec.ratio=min(1,8500/max(1,tris))
    bpy.ops.object.modifier_apply(modifier=dec.name)
    paint_body(preview)
    STATS['mestre_vertices']=len(ob.data.vertices);STATS['mestre_triangulos']=tris
    STATS['corpo_preview_componentes']=components(preview.data)
    return preview


def paint_body(ob):
    mat=material('Pelagem_cores_de_estudo',COLORS['fur'],.88,.006)
    nodes=mat.node_tree.nodes;shader=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
    attr=nodes.new('ShaderNodeVertexColor');attr.layer_name='Estudo_cor'
    mat.node_tree.links.new(attr.outputs['Color'],shader.inputs['Base Color'])
    ob.data.materials.clear();ob.data.materials.append(mat)
    colors=ob.data.color_attributes.new(name='Estudo_cor',type='FLOAT_COLOR',domain='POINT')
    for v,item in zip(ob.data.vertices,colors.data):
        x,y,z=v.co;X=abs(x);role='fur'
        if y<-.20 and 1.87<z<2.70 and X<(.28-(2.7-z)*.14):role='cream'
        if y>.13 and 1.95<z<2.55 and X<.24:role='cream'
        if .53<X<.91 and 1.92<z<2.55 and y<-.13 and X<.78+.06*math.sin(z*26):role='cream'
        if .30<X<.67 and .74<z<1.36 and y<-.12 and X<.46+.07*math.sin(z*23):role='cream'
        if y>.45:
            u=min(1,max(0,(y-.45)/1.7));cz=1.5-1.13*u;rad=.35+.13*math.sin(u*math.pi)
            if z>cz+rad*.36 and X<.27+.06*math.sin(y*17):role='cream'
        if z>2.94 and y<-.59:
            if X<.36 and (z>3.34 or z<3.18):role='cream'
            if y<-.89:role='cream'
            eye=min(((x-s*.20)/.17)**2+((z-3.31)/.11)**2 for s in (-1,1))
            if eye<1.3 and y<-.63:role='dark'
        base=srgb(COLORS[role]);variation=1+.035*math.sin(x*17+z*13)*math.sin(y*21-z*11)
        item.color=(*[linear(min(1,c*variation)) for c in base],1)
    ob['material']='cores de estudo por vértice; UV e mapas finais pendentes'


def accessories(mats):
    for s,side in ((-1,'left'),(1,'right')):
        eye=sphere('eye_'+side,(s*.19,-.800,3.315),(.112,.037,.046),False,mats['iris'])
        eye.rotation_euler.y=s*.23
        sphere('pupil_'+side,(s*.19,-.837,3.315),(.021,.007,.035),False,mats['pupil'])
        sphere('eye_glint_'+side,(s*.18,-.845,3.33),(.009,.004,.009),False,mats['ivory'])
        line('eyelid_'+side,[(s*.075,-.833,3.322),(s*.19,-.843,3.353),(s*.31,-.73,3.37)],.023,mats['dark'])
        for i,dx in enumerate((-.14,0,.14)):
            x=s*(.99+dx);L=(.73,.87,.76)[i]
            tube('hand_claw_'+side+str(i),[(x,-.52,1.14),(x+s*.015,-.69,.98),(x+s*.035,-.72,1.14-L*.70),(x+s*.05,-.54,1.14-L)],
                 [(.079,.067),(.085,.055),(.05,.031),(.002,.002)],12,4,False,mats['ivory'])
            tx=s*(.45+(-.15,0,.15)[i])
            tube('foot_claw_'+side+str(i),[(tx,-.44,.17),(tx,-.56,.15),(tx,-.67,.045)],[(.082,.07),(.078,.05),(.002,.002)],12,4,False,mats['dark'])
        cuff(side,[(s*.80,-.10,2.04),(s*.87,-.20,1.82),(s*.93,-.28,1.57)],.282,.235,mats['wrap'])
        cuff('ankle_'+side,[(s*.47,.0,.78),(s*.46,.008,.55),(s*.45,.015,.35)],.205,.18,mats['wrap'])
    tube('nose',[(0,-1.04,3.28),(0,-1.075,3.18),(0,-1.10,3.065)],[(.075,.055),(.13,.09),(.022,.034)],16,4,False,mats['dark'])
    for s in (-1,1):sphere('nostril_'+str(s),(s*.069,-1.151,3.17),(.022,.008,.027),False,mats['pupil'])
    line('mouth',[(-.255,-.922,3.00),(-.13,-1.053,2.968),(0,-1.088,2.962),(.13,-1.053,2.968),(.255,-.922,3.00)],.012,mats['dark'])
    collar(mats)
    belt(mats)


def cuff(name,points,r1,r2,mat):
    # Outer and inner sleeves, capped by annuli; no disconnected stacked cylinders.
    pts,rs=sample_path(points,[(r1,r1*.92),((r1+r2)/2,(r1+r2)*.46),(r2,r2*.92)],4)
    n=16;vs=[];fs=[]
    for layer in (0,1):
        for j,(p,r) in enumerate(zip(pts,rs)):
            tangent=(pts[min(j+1,len(pts)-1)]-pts[max(0,j-1)]).normalized()
            u=Vector((1,0,0));u=(u-tangent*u.dot(tangent)).normalized();v=tangent.cross(u)
            for i in range(n):
                a=2*math.pi*i/n
                rr=.012*math.sin(j/4*math.pi*2)
                rx,ry=r[0]+rr-layer*.025,r[1]+rr-layer*.025
                vs.append(tuple(p+u*rx*math.cos(a)+v*ry*math.sin(a)))
    count=n*len(pts)
    for layer in range(2):
        for j in range(len(pts)-1):
            for i in range(n):
                a=layer*count+j*n+i;b=layer*count+j*n+(i+1)%n
                fs.append((a,b,b+n,a+n) if layer==0 else (a+n,b+n,b,a))
    for j in (0,len(pts)-1):
        for i in range(n):
            a=j*n+i;b=j*n+(i+1)%n;fs.append((a,a+count,b+count,b))
    mesh('wrap_'+name,vs,fs,mat)


def collar(m):
    n=64;vs=[];fs=[]
    for layer in range(2):
        for level in (0,1):
            for i in range(n):
                a=2*math.pi*i/n;front=(1-math.cos(a))/2
                r=(.48 if level else .63)-layer*.025
                x=math.sin(a)*r;y=-.10+math.cos(a)*r*.78
                z=(3.07+.05*math.cos(a)) if level else (2.76-.20*(1-abs(math.sin(a))))
                z+=.025*math.sin(a*3)
                vs.append((x,y,z))
    for layer in range(2):
        for i in range(n):
            a=layer*2*n+i;b=layer*2*n+(i+1)%n;fs.append((a,b,b+n,a+n))
    for level in (0,1):
        for i in range(n):
            a=level*n+i;b=level*n+(i+1)%n;fs.append((a,a+2*n,b+2*n,b))
    mesh('mantle_collar',vs,fs,m['wine'])
    mantle=[(-.64,.22),(0,.10),(.64,.22),(.52,.01),(.23,-.17),(0,-.32),(-.23,-.17),(-.52,.01)]
    ribbon('mantle_front_drape',mantle,lambda u,w:(u,-.39-.12*(1-abs(u)/.64),2.82+w),.028,m['wine'])
    ribbon('mantle_back_drape',mantle,lambda u,w:(u,.24+.17*(1-abs(u)/.64),2.82+w),.028,m['wine'])
    for k in (0,1):
        pts=[]
        for i in range(33):
            a=math.pi*.5+i/32*math.pi
            r=.60-k*.045
            pts.append((math.sin(a)*r,-.10+math.cos(a)*r*.78,2.85-k*.085-.10*(1-abs(math.sin(a)))))
        line('mantle_fold_'+str(k),pts,.018,m['wine_light'])
    outline=[(0,-.13),(0,.12),(.17,.30),(.38,.43),(.56,.37),(.48,.23),(.61,.16),(.74,.21),(.95,.08),(1.16,-.25),
             (.95,-.08),(.91,-.24),(.77,-.14),(.73,-.32),(.59,-.18),(.51,-.30),(.42,-.10),(.22,-.19)]
    def mapper(u,w):return (-.28-u*1.22,.15+u*.85,3.02+.12*math.sin(u*5)+w)
    ribbon('mantle_trailing_cloth',outline,mapper,.025,m['wine'])
    line('mantle_trailing_fold',[tuple(Vector(mapper(u,.04))+Vector((0,-.018,0))) for u in (0,.15,.3,.45,.6,.75,.9,1.03)],.012,m['wine_light'])
    diamond('mantle_brooch',(-.43,-.45,2.96),.23,.34,m['gold'])


def diamond(name,c,w,h,mat):
    x,y,z=c
    vs=[(x,z) for x,z in ((x,z+h/2),(x+w/2,z),(x,z-h/2),(x-w/2,z))]
    verts=[(a,y,b) for a,b in vs]+[(x,y-.065,z),(x,y+.018,z)]
    fs=[]
    for i in range(4):fs.extend(((i,(i+1)%4,4),((i+1)%4,i,5)))
    ob=mesh(name,verts,fs,mat)
    for p in ob.data.polygons:p.use_smooth=False


def belt(m):
    pts=[];vs=[];fs=[];n=48
    for layer in range(2):
        for z in (1.57,1.77):
            for i in range(n):
                a=i*2*math.pi/n;vs.append(((.39-layer*.03)*math.sin(a),(.29-layer*.03)*math.cos(a),z+.015*math.sin(a*3)))
    for i in range(n):
        j=(i+1)%n
        fs.extend(((i,j,j+n,i+n),(i+2*n,i+3*n,j+3*n,j+2*n),(i,i+2*n,j+2*n,j),(i+n,j+n,j+3*n,i+3*n)))
    mesh('belt_wrap',vs,fs,m['wrap'])
    diamond('belt_buckle',(0,-.323,1.69),.20,.27,m['gold'])
    outline=[(-.28,0),(.28,0),(.25,-.42),(.18,-.72),(.08,-.51),(0,-.87),(-.08,-.66),(-.19,-.77),(-.28,-.45)]
    ribbon('tabard_front',outline,lambda u,v:(u,-.30-.06*math.sin(v*7),1.57+v),.028,m['wine'])
    ribbon('tabard_back',outline,lambda u,v:(u,.30+.10*math.sin(v*3),1.57+v),.028,m['wine'])
    # Sewn leather pouch on the creature's left, consistent in front/back references.
    bpy.ops.mesh.primitive_cube_add(size=1,location=(-.46,-.04,1.61));ob=bpy.context.object;ob.name='belt_pouch'
    ob.scale=(.30,.27,.35);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bevel=ob.modifiers.new('Leather_rounding','BEVEL');bevel.width=.045;bevel.segments=3
    bpy.ops.object.modifier_apply(modifier=bevel.name);ob.data.materials.append(m['wrap'])
    outline=[(-.15,.15),(.15,.15),(.13,-.04),(0,-.10),(-.13,-.04)]
    ribbon('pouch_flap',outline,lambda u,v:(-.46+u,-.185,1.68+v),.025,m['wine'])
    sphere('pouch_button',(-.46,-.212,1.66),(.035,.018,.035),False,m['gold'])


def configure():
    sc=bpy.context.scene
    sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=sc.render.resolution_y=640;sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG';sc.render.film_transparent=True
    sc.render.threads_mode='FIXED';sc.render.threads=2
    sc.view_settings.view_transform='AgX'
    sc.view_settings.exposure=-.55
    sc.world.color=(.4,.4,.4)
    for i,(pos,power,size) in enumerate((((-4,-6,8),1300,5),((5,-1,5),950,5),((1,5,7),1700,4))):
        l=bpy.data.lights.new('Studio_'+str(i),'AREA');l.energy=power;l.shape='DISK';l.size=size
        ob=bpy.data.objects.new(l.name,l);sc.collection.objects.link(ob);ob.location=pos
        ob.rotation_euler=(Vector((0,0,2))-ob.location).to_track_quat('-Z','Y').to_euler()
    data=bpy.data.cameras.new('Review_camera');data.type='ORTHO';data.ortho_scale=5.5
    ob=bpy.data.objects.new(data.name,data);sc.collection.objects.link(ob);sc.camera=ob
    return ob


def camera(cam,angle):
    target=Vector((-.10,.35,1.97));a=math.radians(angle)
    cam.location=target+Vector((math.sin(a)*10,-math.cos(a)*10,1.7))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()


def validate(body_ob):
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render]
    body_mesh=body_ob.data;bm=bmesh.new();bm.from_mesh(body_mesh)
    boundary=sum(e.is_boundary for e in bm.edges);nonmanifold=sum(not e.is_manifold for e in bm.edges)
    bm.free()
    tris=sum(len(p.vertices)-2 for ob in meshes for p in ob.data.polygons)
    finite=all(math.isfinite(c) for ob in meshes for v in ob.data.vertices for c in v.co)
    report={'corpo_componentes':components(body_mesh),'corpo_arestas_abertas':boundary,'corpo_arestas_nao_manifold':nonmanifold,
            'triangulos_visiveis':tris,'malhas_visiveis':len(meshes),'coordenadas_finitas':finite,
            'garras_mao':sum(o.name.startswith('hand_claw_') for o in meshes),'garras_pe':sum(o.name.startswith('foot_claw_') for o in meshes),
            'blender':bpy.app.version_string,'rig':'não criado; retopologia e pesos pendentes','UV':'pintura UV e bake pendentes; cores por vértice/procedurais de estudo',
            'arquivo_pronto_roblox':False,'aprovacao_artistica':False,'mcp':'autoria não usa MCP; conferência dependerá da conexão',**STATS}
    report['erros']=[]
    if not finite or boundary or nonmanifold or len(report['corpo_componentes'])!=1:report['erros'].append('continuidade/integridade corporal')
    if report['garras_mao']!=6 or report['garras_pe']!=6:report['erros'].append('contagem das garras')
    dump('validacao-geometria.json',report)
    return report


def main():
    OUT.mkdir(exist_ok=False)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    m={key:material(key,color,.9 if key in ('fur','wrap') else .68,.004 if key in ('wrap','wine') else 0) for key,color in COLORS.items()}
    body_ob=body();accessories(m)
    for ob in bpy.context.scene.objects:
        if ob.type!='MESH' or ob.hide_render:continue
        bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    cam=configure();camera(cam,45)
    bpy.context.view_layer.update()
    report=validate(body_ob)
    if report['erros']:raise RuntimeError(str(report['erros']))
    for ob in bpy.context.selected_objects:ob.select_set(False)
    body_ob.hide_set(False);body_ob.select_set(True);bpy.context.view_layer.objects.active=body_ob
    path=OUT/'fera-sombras-organica.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
    for view,angle in [('frente',0),('lado',-90),('costas',180),('3-4',45)]:
        camera(cam,angle);bpy.context.scene.render.filepath=str(OUT/(view+'.png'));bpy.ops.render.render(write_still=True)
    # Conferência de volumes sem cor e detalhe facial, sem salvar modificações no asset.
    camera(cam,45)
    gray=material('Clay_review','99938c',.82)
    bpy.context.view_layer.material_override=gray
    bpy.context.scene.render.filepath=str(OUT/'cinza.png');bpy.ops.render.render(write_still=True)
    bpy.context.view_layer.material_override=None
    target=Vector((0,-.4,3.27));cam.location=target+Vector((2.5,-5,1));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.55
    bpy.context.scene.render.filepath=str(OUT/'rosto.png');bpy.ops.render.render(write_still=True)
    dump('execucao.json',{'duracao_segundos':time.perf_counter()-T0,'blender':bpy.app.version_string,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'arquivo':str(path),'arquivo_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'referencias_sha256':hashlib.sha256((BASE/'entrada/briefing.json').read_bytes()).hexdigest(),
         'metodo':'Python CLI; MCP não executou autoria','revisao':REV})
    print('ORGANICO_OK '+json.dumps({'triangulos':report['triangulos_visiveis'],'corpo_componentes':report['corpo_componentes'],'erros':report['erros'],'segundos':round(time.perf_counter()-T0,2)}))


if __name__=='__main__':main()
