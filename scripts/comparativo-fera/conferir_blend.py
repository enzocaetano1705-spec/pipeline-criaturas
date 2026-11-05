"""Conferência de arquivo nativo reaberto, sem alterar/salvar a cena."""
import bpy,json,math
from pathlib import Path

folder=Path(bpy.data.filepath).parent
source=json.loads((folder/'render-malha.json').read_text(encoding='utf-8'))
expected={}
for p in source['patches']:expected.setdefault(p['name'],[]).extend((v[0],-v[2],v[1]) for v in p['vertices'])
errors=[]
for name,points in expected.items():
    ob=bpy.data.objects.get(name)
    if ob is None or ob.type!='MESH':errors.append('malha ausente: '+name);continue
    actual=[ob.matrix_world@v.co for v in ob.data.vertices]
    a=sorted(tuple(round(float(v),4) for v in p) for p in actual)
    b=sorted(tuple(round(float(v),4) for v in p) for p in points)
    if a!=b:errors.append('geometria diverge do plano: '+name)
    if not ob.data.uv_layers:errors.append('UV ausente: '+name)
    elif not all(-1e-7<=value<=1+1e-7 for uv in ob.data.uv_layers.active.data for value in uv.uv):errors.append('UV fora do atlas: '+name)
meshes=[o for o in bpy.data.objects if o.type=='MESH']
if len(meshes)!=len(expected):errors.append('contagem de malhas inesperada')
packed=[i for i in bpy.data.images if i.packed_file]
if len(packed)!=1:errors.append('atlas empacotado ausente ou inesperado')
data={'arquivo':bpy.data.filepath,'blender':bpy.app.version_string,'reaberto_em_processo_limpo':True,
      'malhas':len(meshes),'grupos_edicao':sum(o.type=='EMPTY' for o in bpy.data.objects),
      'atlas_empacotados':len(packed),'uvs_dentro_do_atlas':not any('UV' in e for e in errors),
      'erros':errors,'geometria_igual_ao_plano':not any('geometria' in e for e in errors),
      'armature_concluida':False,'aprovacao_artistica':False}
(folder/'validacao-reabertura.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('REABERTURA_OK '+json.dumps(data,ensure_ascii=False))
if errors:raise RuntimeError('; '.join(errors))
