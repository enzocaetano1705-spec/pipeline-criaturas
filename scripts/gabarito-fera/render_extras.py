"""Conferência das três capturas restantes, preservando a malha já construída."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,Quaternion

folder=Path(bpy.data.filepath).parent
sc=bpy.context.scene;cam=sc.camera
valid=json.loads((folder/'validacao.json').read_text(encoding='utf-8'))
views={'perfil_oposto':{'res':(704,471),'direction':(1*-1,0,0),'roll':0,'target':(0,.04,1.73)},
       'superior':{'res':(546,609),'direction':(0,0,1),'roll':math.pi,'target':(0,.12,1.75)},
       'inferior':{'res':(579,653),'direction':(0,0,-1),'roll':0,'target':(0,.12,1.75)}}
for view,data in views.items():
    sc.render.resolution_x,sc.render.resolution_y=data['res'];sc.render.resolution_percentage=100
    target=Vector(data['target']);cam.location=target+Vector(data['direction'])*20
    q=(target-cam.location).to_track_quat('-Z','Y')@Quaternion((0,0,1),data['roll'])
    cam.rotation_euler=q.to_euler();cam.data.ortho_scale=5
    frame=cam.data.view_frame(scene=sc);span=max(p.y for p in frame)-min(p.y for p in frame)
    cam.data.ortho_scale*=(data['res'][1]/92)/span
    sc.render.filepath=str(folder/(view+'.png'));bpy.ops.render.render(write_still=True)
    valid['cameras'][view]={'tipo':'ortográfica','localizacao':list(cam.location),'rotacao':list(cam.rotation_euler),'escala':cam.data.ortho_scale,'resolucao':list(data['res']),'rotulo_provisorio':view in ('superior','inferior')}
(folder/'validacao.json').write_text(json.dumps(valid,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(folder/'fera-gabarito-360-bruto.blend'),compress=True)
print('Três vistas adicionais renderizadas; geometria preservada.')
