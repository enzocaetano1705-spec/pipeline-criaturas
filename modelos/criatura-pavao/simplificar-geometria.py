"""Versão solicitada pelo usuário: oito peças e rosto pintado."""
import json
import shutil
import subprocess
from copy import deepcopy
from pathlib import Path

from criaturas import bbmodelo, ops, relatorio
from criaturas.cubificar import contexto
from criaturas.validar import modelo_atual

root = Path(__file__).resolve().parent
dest = root / 'e1'
ctx = contexto('criatura-pavao', 'e1')
file = modelo_atual(dest, ctx['relatorio'])
backup = dest / 'historico-versoes'
backup.mkdir(exist_ok=True)
if not (backup / 'antes-simplificacao-38.bbmodel').exists():
    shutil.copy2(file, backup / 'antes-simplificacao-38.bbmodel')
    shutil.copy2(dest / 'plano-cubos.json', backup / 'plano-38-cubos.json')

plan = json.loads((dest / 'plano-cubos-automatico.json').read_text(encoding='utf-8'))
original = deepcopy(plan['cubos'])
base = deepcopy(next(c for c in original if c['parte'] == 'body'))
main = deepcopy(base)
main['nome'] = 'body_cube'
main['from'], main['to'] = [-8, 2, -6], [8, 13, 7]
chin = deepcopy(base)
chin['nome'] = 'body_cube_2'
chin['from'], chin['to'] = [-7, 0, -7], [7, 2, 7]
feathers = [c for c in original if c['parte'].startswith('feather_')]
for c in feathers:
    if c['parte'].endswith(('_1', '_2')):
        c['from'][2], c['to'][2] = -0.5, 0.5
plan['cubos'] = [main, chin] + feathers
offsets, (w, h) = ops.distribuir_uv(plan['cubos'], margem=1)
for c in plan['cubos']:
    c['uv_offset'] = offsets[c['nome']]
plan['resolucao'] = {'largura': w, 'altura': h}
plan['orcamento']['cubos'] = len(plan['cubos'])

model = bbmodelo.ler(file)
batch = [{'op':'remove_node','target':c.nome} for c in model.cubos]
batch.append({'op':'set_model_properties','resolution':{'width':w,'height':h}})
for bone in plan['ossos']:
    batch.append({'op':'update_node','target':bone['nome'],
                  'origin':bone['pivo'],'rotation':bone.get('rotacao',[0,0,0])})
batch += [op for op in ops.gerar_ops(plan) if op['op'] == 'add_cube']
batch_path = dest / 'simplificacao-8-pecas.ops.json'
relatorio.gravar_json(batch_path, {'operations':batch})
subprocess.run(['uv','run','criaturas','aplicar','docs/criaturas/criatura-pavao',str(batch_path),
                '--motivo','Simplificação pedida pelo usuário: oito peças, grandes formas e rosto pintado'],
               cwd=root.parent.parent,check=True)
relatorio.gravar_json(dest/'plano-cubos.json',plan,'plano_cubos')
print(f'Plano sincronizado: {len(plan["cubos"])} peças, atlas {w}×{h}.')
