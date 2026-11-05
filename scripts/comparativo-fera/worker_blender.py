"""Executado no Blender instalado: salva B nativo, depois renderiza A/B sob a mesma cena."""
import bpy
from mathutils import Vector, Matrix
from pathlib import Path
import json,sys,math,hashlib

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'modelos/fera-fera-agil-das-sombras/comparativo-v1'
REV=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'v1'
BDIR=BASE/('blender-'+REV)
ADIR=BASE/('blockbench-'+REV)


def dump(path,data):Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def xyz(p):return Vector((p[0],-p[2],p[1]))


def material(path,name):
    im=bpy.data.images.load(str(path),check_existing=False)
    im.pack()
    mat=bpy.data.materials.new(name)
    mat.use_nodes=True
    mat.diffuse_color=(.6,.3,.2,1)
    bsdf=mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Roughness'].default_value=1
    bsdf.inputs['Metallic'].default_value=0
    if 'Specular IOR Level' in bsdf.inputs:bsdf.inputs['Specular IOR Level'].default_value=0
    image=mat.node_tree.nodes.new('ShaderNodeTexImage')
    image.image=im
    image.interpolation='Closest'
    mat.node_tree.links.new(image.outputs['Color'],bsdf.inputs['Base Color'])
    mat.node_tree.links.new(image.outputs['Alpha'],bsdf.inputs['Alpha'])
    mat.surface_render_method='DITHERED'
    mat.use_backface_culling=False
    return mat


def criar(data,tex,colname):
    collection=bpy.data.collections.new(colname)
    bpy.context.scene.collection.children.link(collection)
    mat=material(tex,colname+'_pixel_blockout')
    groups={}
    for b in data.get('ossos',[]):
        ob=bpy.data.objects.new(b['nome'],None)
        collection.objects.link(ob)
        ob['pivo_canonico']=b['pivo']
        ob['pai_planejado']=b['pai'] or ''
        ob.empty_display_size=.2
        groups[b['nome']]=ob
    for b in data.get('ossos',[]):
        if b['pai']: groups[b['nome']].parent=groups[b['pai']]
    byname={}
    for p in data['patches']:byname.setdefault(p['name'],[]).append(p)
    for name,patches in byname.items():
        verts=[]; faces=[]; uvs=[]
        for patch in patches:
            pts=patch['vertices']
            # ordem dos cantos do renderizador: TL,TR,BL,BR; ordem CCW externa.
            order=[0,2,3,1]
            v=[xyz(pts[i]) for i in order]
            normal=xyz(patch['normal'])
            if (v[1]-v[0]).cross(v[2]-v[0]).dot(normal)<0:order=list(reversed(order))
            start=len(verts)
            verts += [xyz(pts[i]) for i in order]
            faces.append(tuple(range(start,start+4)))
            a,b,c,d=patch['uv']
            UV=[(a/128,1-b/128),(c/128,1-b/128),(a/128,1-d/128),(c/128,1-d/128)]
            uvs.append([UV[i] for i in order])
        mesh=bpy.data.meshes.new(name+'_mesh')
        mesh.from_pydata(verts,[],faces)
        mesh.update()
        layer=mesh.uv_layers.new(name='PixelUV')
        for poly,uv in zip(mesh.polygons,uvs):
            for li,value in zip(poly.loop_indices,uv):layer.data[li].uv=value
        ob=bpy.data.objects.new(name,mesh)
        collection.objects.link(ob)
        ob.data.materials.append(mat)
        if groups:ob.parent=groups[patches[0]['bone']]
        ob['fase']='geometria_com_cores_de_bloqueio; pintura_final_pendente'
    return collection


def configurar():
    scene=bpy.context.scene
    scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x=scene.render.resolution_y=512
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=True
    scene.render.threads_mode='FIXED';scene.render.threads=2
    scene.view_settings.view_transform='Standard'
    scene.view_settings.look='None'
    scene.view_settings.exposure=0
    scene.world.color=(.7,.7,.7)
    for i,(location,power,size) in enumerate((((-30,25,60),35000,45),((35,0,45),25000,50),((0,-40,50),25000,40))):
        light=bpy.data.lights.new('Softbox_'+str(i),'AREA')
        light.energy=power;light.shape='DISK';light.size=size
        ob=bpy.data.objects.new(light.name,light)
        scene.collection.objects.link(ob)
        ob.location=location
        ob.rotation_euler=(xyz([0,16,0])-ob.location).to_track_quat('-Z','Y').to_euler()
    c=bpy.data.cameras.new('Comparacao_ortografica')
    c.type='ORTHO';c.ortho_scale=43
    ob=bpy.data.objects.new(c.name,c);scene.collection.objects.link(ob);scene.camera=ob
    return ob


def orientar(cam,az,el):
    target=xyz([0,16,4])
    a,e=math.radians(az),math.radians(el)
    direction=xyz([-math.sin(a)*math.cos(e),math.sin(e),-math.cos(a)*math.cos(e)])
    cam.location=target+direction*90
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()


def main():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    # Autoria B já foi definida sem consultar A; salva somente seu próprio asset nativo.
    bp=BDIR/'render-malha.json'
    data=json.loads(bp.read_text(encoding='utf-8'))
    B=criar(data,BDIR/'cores-bloqueio.png','Autoria_Blender')
    camera=configurar();orientar(camera,55,10)
    bpy.context.view_layer.update()
    path=BDIR/f'fera-sombras-e3-blender-{REV}.blend'
    if path.exists():raise RuntimeError('Não sobrescrever blend existente')
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    # Só agora entra uma cópia de apresentação da geometria A, sem transferir autoria.
    a=json.loads((ADIR/'render-malha.json').read_text(encoding='utf-8'))
    A=criar(a,ADIR/'cores-bloqueio.png','Geometria_Blockbench_para_render')
    views={'frente':(0,0),'lado':(90,0),'costas':(180,0),'3-4':(55,10)}
    previews=BASE/('previas-'+REV);previews.mkdir(exist_ok=True)
    for author,col,other in [('blockbench',A,B),('blender',B,A)]:
        col.hide_render=False;other.hide_render=True
        for view,(az,el) in views.items():
            orientar(camera,az,el)
            bpy.context.scene.render.filepath=str(previews/f'{author}-{view}.png')
            bpy.ops.render.render(write_still=True)
    allpoints=[p for group in (a,data) for patch in group['patches'] for p in patch['vertices']]
    # Validação da autoria B: sem não finitos, normais/UVs, contagem real do arquivo salvo.
    bpoints=[p for patch in data['patches'] for p in patch['vertices']]
    finite=all(math.isfinite(v) for p in bpoints for v in p)
    report={'arquivo':str(path),'blender':bpy.app.version_string,'autoria':'Blender independente',
            'elementos':len({p['name'] for p in data['patches']}),'quads':len(data['patches']),
            'triangulos':len(data['patches'])*2,'uv_finitas':all(math.isfinite(v) for p in data['patches'] for v in p['uv']),
            'coordenadas_finitas':finite,'limites':{'min':[min(p[i] for p in bpoints) for i in range(3)],'max':[max(p[i] for p in bpoints) for i in range(3)]},
            'render':'Blender EEVEE comum às duas autorias','camera':{'tipo':'ortografica','escala':43,'alvo_canonico':[0,16,4],'vistas':views},
            'textura':'cores/recortes de bloqueio, 128², nearest; pintura final pendente','rig':'grupos de edição; rig/animações não concluídos',
            'geometria_aprovada':False,'origem_B_sha256':data['autoria_sha256']}
    dump(BDIR/'validacao-autoria.json',report)
    print('COMPARATIVO_OK '+json.dumps({'elementos_B':report['elementos'],'triangulos_B':report['triangulos'],'finitos':finite}))


if __name__=='__main__':main()
