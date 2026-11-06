"""Lê o blend final em processo limpo e confirma que a calibração só moveu câmeras."""
import bpy,bmesh,json,math
from pathlib import Path

folder=Path(bpy.data.filepath).parent
source=json.loads((folder/'malha-projecao.json').read_text(encoding='utf-8'))
errors=[];triangles=0
for item in source:
    ob=bpy.data.objects.get(item['nome'])
    if not ob or ob.type!='MESH':errors.append('volume ausente: '+item['nome']);continue
    if len(ob.data.vertices)!=len(item['vertices']):errors.append('topologia mudou: '+ob.name);continue
    for vertex,expected in zip(ob.data.vertices,item['vertices']):
        actual=ob.matrix_world@vertex.co
        if max(abs(a-b) for a,b in zip(actual,expected))>1e-5:errors.append('câmera alterou geometria: '+ob.name);break
    bm=bmesh.new();bm.from_mesh(ob.data)
    if any(not e.is_manifold for e in bm.edges):errors.append('volume aberto: '+ob.name)
    bm.free();triangles+=sum(len(p.vertices)-2 for p in ob.data.polygons)
    if not all(math.isfinite(x) for v in ob.data.vertices for x in v.co):errors.append('coordenada inválida: '+ob.name)
ref=bpy.data.objects.get('GABARITO_PERFIL_excluido_do_render')
if not ref or ref.type!='EMPTY' or not ref.hide_render or not ref.data.packed_file:errors.append('gabarito ausente/renderizável/não empacotado')
report={'arquivo':bpy.data.filepath,'processo_limpo':True,'volumes':len(source),'triangulos':triangles,
        'geometria_preservada_na_calibracao':not any('geometria' in e or 'topologia' in e for e in errors),
        'gabarito_no_fundo':bool(ref),'gabarito_excluido_do_render':bool(ref and ref.hide_render),
        'cameras_de_conferencia':sum(o.type=='CAMERA' for o in bpy.data.objects),'erros':errors,
        'aprovacao_artistica':False,'pronto_para_roblox':False}
(folder/'validacao-reabertura.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('CONFERENCIA_GABARITO '+json.dumps(report,ensure_ascii=False))
if errors:raise RuntimeError(str(errors))
