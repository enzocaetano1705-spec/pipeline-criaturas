"""Aplica apenas os parâmetros de câmera ao blend; salva outra versão e rerenderiza."""
import bpy,json,shutil,sys
from pathlib import Path
from mathutils import Vector

folder=Path(bpy.data.filepath).parent
extra='--extras' in sys.argv
fitfile=folder/('calibracao-extras.json' if extra else 'calibracao-enquadramento.json')
fit=json.loads(fitfile.read_text(encoding='utf-8'))
valid=json.loads((folder/'validacao.json').read_text(encoding='utf-8'))
cam=bpy.context.scene.camera
for view,data in fit.items():
    source=valid['cameras'][view]
    sc=bpy.context.scene;sc.render.resolution_x,sc.render.resolution_y=source['resolucao'];sc.render.resolution_percentage=100
    cam.location=source['localizacao'];cam.rotation_euler=source['rotacao'];cam.data.ortho_scale=source['escala'];bpy.context.view_layer.update()
    k=data['fator_escala_global'];dx,dy=data['translacao_pixel']
    right=cam.matrix_world.to_3x3()@Vector((1,0,0));up=cam.matrix_world.to_3x3()@Vector((0,1,0))
    cam.data.ortho_scale/=k;cam.location+=right*(-dx/(92*k))+up*(dy/(92*k))
    old=folder/(view+'.png');backup=folder/(view+'-antes-calibracao.png')
    if backup.exists():raise RuntimeError('Calibração já aplicada: usar outro diretório')
    shutil.copy2(old,backup)
    sc.render.filepath=str(old);bpy.ops.render.render(write_still=True)
    data['camera_aplicada']={'localizacao':list(cam.location),'rotacao':list(cam.rotation_euler),'escala':cam.data.ortho_scale}
# The profile remains the active modeling view, using the unchanged traced underlay.
source=valid['cameras']['perfil'];sc=bpy.context.scene
sc.render.resolution_x,sc.render.resolution_y=source['resolucao'];cam.location=source['localizacao'];cam.rotation_euler=source['rotacao'];cam.data.ortho_scale=source['escala']
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
path=folder/('fera-gabarito-360.blend' if extra else 'fera-gabarito-calibrado.blend')
if path.exists():raise RuntimeError('Arquivo calibrado já existe')
if extra:
    camera_collection=bpy.data.collections.new('Cameras_de_conferencia');sc.collection.children.link(camera_collection)
    presets=dict(valid['cameras'])
    for name in ('calibracao-enquadramento.json','calibracao-extras.json'):
        data=json.loads((folder/name).read_text(encoding='utf-8'))
        if name=='calibracao-extras.json':data=fit
        for key,value in data.items():presets[key]={**presets[key],**value.get('camera_aplicada',{})}
    for key,preset in presets.items():
        ob=bpy.data.objects.new('View_'+key,cam.data.copy());camera_collection.objects.link(ob)
        ob.location=preset['localizacao'];ob.rotation_euler=preset['rotacao'];ob.data.ortho_scale=preset['escala'];ob['resolucao']=preset['resolucao']
bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
fitfile.write_text(json.dumps(fit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Calibração aplicada às câmeras secundárias; geometria e perfil preservados.')
