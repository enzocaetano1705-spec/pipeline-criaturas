"""Refino específico desta criatura, sempre por operações do motor separado."""
import json
import math
from copy import deepcopy
from collections import Counter
from pathlib import Path

from PIL import Image
from criaturas import cubificar, ops, relatorio

ROOT = Path(__file__).resolve().parent
DEST = ROOT / 'e1'
plan_path = DEST / 'plano-cubos.json'
snapshot = DEST / 'plano-cubos-automatico.json'
if not snapshot.exists():
    snapshot.write_bytes(plan_path.read_bytes())
plan = json.loads(snapshot.read_text(encoding='utf-8'))
original = deepcopy(plan['cubos'])
image = Image.open(DEST / 'preparo/frente-recorte.png').convert('RGBA')
feather_region = image.crop((0, 0, image.width, round(image.height * 10 / 32)))
green_pixels = [(r//8*8, g//8*8, b//8*8)
                for r, g, b, a in feather_region.get_flattened_data()
                if a > 200 and g > 90 and g > r * 1.4 and g > b * 1.08]
green = Counter(green_pixels).most_common(1)[0][0]
green_hex = '#' + ''.join(f'{v:02x}' for v in green)
body = next(c for c in original if c['parte'] == 'body')
body_cubes = []
layers = []
edges = [0, 1, 3, 5, 7, 9, 11, 12, 13]
for low, high in zip(edges, edges[1:]):
    radius = math.sqrt(max(0.1, 1 - (((low + high) / 2 - 6.5) / 6.5) ** 2))
    half_x = max(2, round(8 * radius))
    half_z = max(2, round(7 * radius))
    shoulder = max(1, round(half_z / 2))
    front_half_x = max(1, round(half_x * 0.76))
    layers.append((low, high, half_z))
    strips = [(-half_z, -shoulder, front_half_x),
              (-shoulder, shoulder, half_x),
              (shoulder, half_z, front_half_x)]
    for z0, z1, width in strips:
        c = deepcopy(body)
        c['nome'] = 'body_cube' + (f'_{len(body_cubes)+1}' if body_cubes else '')
        c['from'], c['to'] = [-width, low, z0], [width, high, z1]
        body_cubes.append(c)

details = []
for c in original:
    if c['parte'] == 'body':
        continue
    if c['tipo'] == 'adesivo':
        count = 0
        for low, high, half_z in layers:
            y0, y1 = max(low, c['from'][1]), min(high, c['to'][1])
            if y1 <= y0:
                continue
            d = deepcopy(c)
            count += 1
            d['nome'] += f'_{count}' if count > 1 else ''
            d['from'][1], d['to'][1] = y0, y1
            d['from'][2] = d['to'][2] = -half_z - 0.01
            details.append(d)
    else:
        d = deepcopy(c)
        if c['parte'].startswith('feather_'):
            left = '_left_' in c['parte']
            pivot = -1 if left else 1
            x0, x1 = [(x - pivot) / math.cos(math.pi / 4) + pivot
                      for x in (c['from'][0], c['to'][0])]
            width = round(x1 - x0)
            centre = round(x0 + x1) / 2
            d['from'][0], d['to'][0] = centre - width / 2, centre + width / 2
            if c['parte'].endswith('_3'):
                d['cor'] = green_hex
        details.append(d)

for bone in plan['ossos']:
    if bone['nome'] in ('feather_left_1', 'feather_right_1'):
        left = '_left_' in bone['nome']
        bone['pivo'] = [-1 if left else 1, 12, 0]
        bone['rotacao'] = [0, 45 if left else -45, 0]

plan['cubos'] = body_cubes + details
offsets, (w, h) = ops.distribuir_uv(plan['cubos'], margem=1)
for c in plan['cubos']:
    c['uv_offset'] = offsets[c['nome']]
plan['resolucao'] = {'largura': w, 'altura': h}
plan['orcamento']['cubos'] = len(plan['cubos'])
relatorio.gravar_json(plan_path, plan, 'plano_cubos')
report = json.loads((DEST/'relatorio.json').read_text(encoding='utf-8'))
file, warning, digest = cubificar.construir(plan, DEST, 'criatura-pavao-e1', report.get('hashes', {}))
relatorio.registrar(DEST, 'criatura-pavao', 'e1', 'cubificar', True,
    arquivos=[str(file)], hashes={file.name:digest},
    resumo={'arquivo':file.name,'cubos':len(plan['cubos']), 'refino':'corpo em três eixos e penas em diagonal'})
print(f'Refino: {len(body_cubes)} volumes no corpo, {len(details)} detalhes; atlas {w}x{h}.')
print(file)
if warning:
    print(warning)
