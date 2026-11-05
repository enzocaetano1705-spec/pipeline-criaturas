"""Conferência em processo limpo do blend salvo; nunca altera/salva o arquivo."""
import bpy,bmesh,json,math
from pathlib import Path

folder=Path(bpy.data.filepath).parent
body=bpy.data.objects.get('body_game_preview')
errors=[]
if not body:raise RuntimeError('Corpo de apresentação ausente')
bm=bmesh.new();bm.from_mesh(body.data)
seen=set();sizes=[]
for v in bm.verts:
    if v in seen:continue
    stack=[v];seen.add(v);size=0
    while stack:
        u=stack.pop();size+=1
        for e in u.link_edges:
            n=e.other_vert(u)
            if n not in seen:seen.add(n);stack.append(n)
    sizes.append(size)
boundary=sum(e.is_boundary for e in bm.edges)
nonmanifold=sum(not e.is_manifold for e in bm.edges)
volume=bm.calc_volume(signed=True)
bm.free()
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render]
max_tri=max(sum(len(p.vertices)-2 for p in ob.data.polygons) for ob in meshes)
if len(sizes)!=1 or boundary or nonmanifold or volume<=0:errors.append('continuidade/volume/normais do corpo')
if not bpy.data.objects.get('body_sculpt_master'):errors.append('mestre não preservado')
if not body.data.color_attributes.get('Estudo_cor'):errors.append('cores de estudo ausentes')
if not all(math.isfinite(c) for ob in meshes for v in ob.data.vertices for c in v.co):errors.append('coordenada não finita')
if max_tri>20000:errors.append('malha individual acima de 20 mil triângulos')
report={'arquivo':bpy.data.filepath,'reaberto_em_processo_limpo':True,'corpo_componentes':sizes,'corpo_bordas_abertas':boundary,
        'corpo_arestas_nao_manifold':nonmanifold,'volume_corpo_positivo':volume>0,'maior_malha_triangulos':max_tri,
        'mestre_preservado':True,'erros':errors,'validacao':'arquivo/Blender; não equivale a importação Roblox ou aprovação artística'}
(folder/'validacao-reabertura.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('REABERTURA_ORGANICO '+json.dumps(report,ensure_ascii=False))
if errors:raise RuntimeError(str(errors))
