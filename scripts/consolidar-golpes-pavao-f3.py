"""Consolida os três golpes aprovados, sem alterar nenhuma de suas chaves."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from criaturas import bbmodelo,motor

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'modelos/criatura-pavao/f3/ataques-v6/criatura-pavao-e3-ataques-v6.bbmodel'
OUT=ROOT/'modelos/criatura-pavao/f3/ataques-v7'
FILE=OUT/'criatura-pavao-e3-ataques-v7.bbmodel'
ATTACKS=['attack_low','attack_left','attack_combo']


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def metadata():
    d=json.loads((SOURCE.parent/'animacoes.json').read_text(encoding='utf-8'))
    d.update(status='golpes-aprovados-low-left-combo',modelo=FILE.name,fonte=SOURCE.relative_to(ROOT).as_posix(),
        fonte_sha256=sha(SOURCE),saida_sha256=sha(FILE),validacao='validacao-catalogo.json')
    d['golpes']={name:d['golpes'][name] for name in ATTACKS}
    d['aprovados']=list(dict.fromkeys([n for n in d.get('aprovados',[]) if n!='attack_right']+ATTACKS))
    d['sequencia_sugerida']=ATTACKS.copy()
    d['aprovacao_golpes']={'data':'2026-10-27','clipes':ATTACKS,'decisao':'Manter Low, Left e Combo; retirar Right. Combo aprovado pelo usuário.'}
    d['alvos_golpes']={'attack_low':'Alvos de qualquer altura, conforme avaliação do usuário.',
        'attack_left':'Alvos de qualquer altura, conforme avaliação do usuário.','attack_combo':'Combo aéreo com golpe duplo na queda.'}
    d['golpes_removidos']={'attack_right':'Retirado por decisão do usuário; histórico preservado na v6.'}
    d['controle_golpes']='Conjunto atual: Low, Left e Combo. Todas as poses, durações, eventos e vínculos destes golpes são iguais aos da v6.'
    d.pop('aprovacoes_parciais',None)
    d['referencias_usuario']=['../ataques-v6/referencias/combo-fechado.png']
    d['validacao_movimento_origem']={'arquivo':'../ataques-v6/validacao-ataques.json','sha256_modelo':sha(SOURCE),
        'preservacao':'Os 22 clipes mantidos são idênticos aos da fonte validada; só um clipe foi removido.'}
    d['legado_cross']='Cross antigo permanece na v4; o catálogo atual contém apenas Low, Left e Combo.'
    save(OUT/'animacoes.json',d)


def validate():
    src=bbmodelo.ler(SOURCE);out=bbmodelo.ler(FILE)
    kept=[a for a in src.animacoes if a['name']!='attack_right']
    assert len(src.animacoes)==23 and len(kept)==len(out.animacoes)==22
    expected={**src.bruto,'name':FILE.stem,'animations':kept}
    assert out.bruto==expected,'Alteração além do nome do projeto e da remoção do clipe.'
    assert all(n in [a['name'] for a in out.animacoes] for n in ATTACKS)
    d=json.loads((OUT/'animacoes.json').read_text(encoding='utf-8'))
    assert set(d['golpes'])==set(ATTACKS) and 'attack_right' not in d['sequencia_sugerida']
    assert not any('attack_right' in d[k] for k in ['aprovados'])
    previous=json.loads((SOURCE.parent/'animacoes.json').read_text(encoding='utf-8'))
    for name in ATTACKS:assert d['golpes'][name]==previous['golpes'][name],name
    report={'ok':True,'fonte_sha256':sha(SOURCE),'saida_sha256':sha(FILE),'clipes':22,
        'removidos':['attack_right'],'preservados_integralmente':[a['name'] for a in kept],
        'geometria_rig_uv_atlas_locators_preservados':True,'eventos_dos_golpes_preservados':True,
        'unicas_alteracoes_modelo':['name','animations: remoção de attack_right'],
        'validacao_de_movimento_origem':'../ataques-v6/validacao-ataques.json'}
    save(OUT/'validacao-catalogo.json',report)
    print('Validado: 22 clipes idênticos à v6; attack_right ausente; geometria e metadados preservados.')


def generate():
    OUT.mkdir(parents=True,exist_ok=True)
    source_record=json.loads((SOURCE.parent/'geracao.json').read_text(encoding='utf-8'))
    if sha(SOURCE)!=source_record['saida_sha256']:raise ValueError('Fonte v6 editada: adotar a revisão em outra versão.')
    if FILE.exists():
        record=json.loads((OUT/'geracao.json').read_text(encoding='utf-8'))
        if sha(FILE)!=record['saida_sha256']:raise ValueError('Saída editada à mão: criar outra versão.')
    shutil.copy2(SOURCE,FILE)
    operations=[{'op':'remove_animation','animation':'attack_right'},{'op':'set_model_properties','name':FILE.stem}]
    save(OUT/'ops.json',operations);motor.editar(FILE,operations)
    save(OUT/'geracao.json',{'fonte':SOURCE.relative_to(ROOT).as_posix(),'fonte_sha256':sha(SOURCE),'saida_sha256':sha(FILE),'removidos':['attack_right'],'golpes':ATTACKS})
    metadata();validate()


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--validar',action='store_true');a=ap.parse_args()
    if a.validar:validate()
    else:generate()
