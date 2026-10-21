"""Referências externas: análise agregada, nomes heurísticos e cache sem copiar modelos."""
import argparse
import json

import pytest

from criaturas import referencias


def gravar(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def antigo():
    return {"name":"sintetica", "meta":{"model_format":"animated_entity_model","box_uv":True},
            "resolution":{"width":32,"height":64},
            "elements":[{"uuid":"c1","name":"cube","from":[-2,0,-1],"to":[2,4,1]},
                        {"uuid":"c2","name":"cube","from":[0,4,0],"to":[4,6,0],"box_uv":False}],
            "outliner":[{"uuid":"root","name":"body","children":["c1",{"uuid":"head","name":"head","children":["c2"]}]}],
            "textures":[{"width":32,"height":64,"source":"do not include texture"}],
            "animations":[]}


def test_grupos_antigos_e_nomes_duplicados_nao_perdem_pecas(tmp_path):
    path=gravar(tmp_path/'modelo.bbmodel',antigo())
    before=path.read_bytes()
    r=referencias.inspecionar(path)
    assert r['contagem']=={'pecas':2,'solidos':1,'planos':1,'ossos':2}
    assert r['texturas']['uv']=={'box':1,'por_face':1}
    assert r['texturas']['resolucao_uv']==[32,64]
    assert r['volumes']['fracao_por_regiao']['corpo']==1
    assert path.read_bytes()==before
    dumped=json.dumps(r)
    for campo in ('"from"','"to"','"origin"','"source"','"uv_offset"','"data_points"'):
        assert campo not in dumped


def test_grupos_5_e_rotacao_herdada_alteram_proporcoes(tmp_path):
    d=antigo()
    d['groups']=[{'uuid':'root','name':'body','rotation':[0,0,90],'origin':[0,0,0]},
                 {'uuid':'head','name':'head','rotation':[0,0,0],'origin':[0,0,0]}]
    d['outliner']=[{'uuid':'root','children':['c1',{'uuid':'head','children':['c2']}]}]
    r=referencias.inspecionar(gravar(tmp_path/'novo.bbmodel',d))
    assert r['contagem']['ossos']==2
    assert r['rotacoes']['pecas_com_rotacao_propria_ou_herdada']==2
    assert r['proporcoes']['largura_altura']==pytest.approx(1.0)
    assert r['proporcoes']['profundidade_altura']==pytest.approx(1/3,abs=0.0001)


def test_geo_json_conta_planos_rotacoes_e_uv(tmp_path):
    d={'minecraft:geometry':[{'description':{'texture_width':64,'texture_height':32},'bones':[
        {'name':'body','cubes':[{'origin':[0,0,0],'size':[4,4,2],'uv':[0,0]}]},
        {'name':'leftWing','parent':'body','rotation':[0,45,0],
         'cubes':[{'origin':[4,1,0],'size':[4,3,0],'uv':{'north':{'uv':[0,0]}}}]}]}]}
    r=referencias.inspecionar(gravar(tmp_path/'teste.geo.json',d))
    assert r['contagem']=={'pecas':2,'solidos':1,'planos':1,'ossos':2}
    assert r['tags']==['asas','corpo']
    assert r['motivos_tags']['asas']==['leftWing']
    assert r['rotacoes']['fracao']==0.5
    assert r['texturas']['uv']=={'box':1,'por_face':1}


def test_clip_selecionado_e_compatibilidade_nao_prometem_retarget(tmp_path):
    d=antigo()
    d['animations']=[{'name':'idle','length':2,'loop':'loop','animators':{
        'root':{'name':'body','keyframes':[{'channel':'rotation','data_points':[{'x':'0','y':'math.sin(query.life_time)','z':'0'}]}]}}}]
    path=gravar(tmp_path/'modelo.bbmodel',d)
    species=gravar(tmp_path/'dados.json',{'evo_stage':1,'anims':['walk2','missing']})
    library=gravar(tmp_path/'animacoes.json',{'animations':{'animation.lib.walk2':{
        'animation_length':1,'bones':{'body':{'rotation':{'0':[0,0,0]}},'leg':{'rotation':[1,2,3]}}}}})
    r=referencias.inspecionar(path,dados=species,biblioteca=library)
    embedded=r['animacoes']['incorporadas'][0]
    assert embedded['usa_expressoes'] is True and embedded['chaves']==1
    chosen=r['animacoes']['selecionadas']
    assert chosen[0]['encontrada'] is True and chosen[0]['ossos_ausentes']==['leg']
    assert chosen[1]['encontrada'] is False


def test_tags_nao_confundem_forehead_com_head():
    tags,motivos=referencias._tags(['forehead','leftWing2','ear_left','random'])
    assert tags==['asas','orelhas']
    assert 'cabeca' not in motivos


def test_interpolacao_nao_e_confundida_com_expressao():
    r=referencias._resumo_clip('walk',{'bones':{'body':{
        'relative_to':{'rotation':'entity'},
        'rotation':{'0':{'post':[0,1,2],'lerp_mode':'catmullrom'}}}}}, {'body'}, bedrock=True)
    assert r['usa_expressoes'] is False
    assert r['canais']=={'rotation':1}


def biblioteca(tmp_path):
    model=gravar(tmp_path/'blockbench/babies2/sintetica.bbmodel',antigo())
    gravar(tmp_path/'indice-modelos.json',[{'nome':'sintetica','estagio':'Baby II','evo_stage':1,
        'bbmodel':['blockbench\\babies2\\sintetica.bbmodel'],'cubos_e_planos':2}])
    return model


def test_busca_filtra_e_cache_invalida_quando_modelo_muda(tmp_path):
    model=biblioteca(tmp_path)
    r=referencias.buscar(tmp_path,'cabeca',estagio='Baby II')
    assert len(r)==1 and r[0]['nome']=='sintetica'
    assert (tmp_path/referencias.CACHE).exists()
    cache_mtime=(tmp_path/referencias.CACHE).stat().st_mtime_ns
    assert not referencias.buscar(tmp_path,tags=['asas'])
    assert (tmp_path/referencias.CACHE).stat().st_mtime_ns==cache_mtime
    d=antigo();d['outliner'][0]['name']='leftWing'
    gravar(model,d)
    assert len(referencias.buscar(tmp_path,tags=['asas']))==1


def test_indice_nao_le_arquivo_fora_da_biblioteca(tmp_path):
    gravar(tmp_path/'indice-modelos.json',[{'nome':'x','bbmodel':['../segredo.bbmodel']}])
    with pytest.raises(ValueError,match='fora da biblioteca'):
        referencias.catalogar(tmp_path)


def test_indice_simples_prefere_projeto_editavel_ao_geo(tmp_path):
    gravar(tmp_path/'sintetica/sintetica.bbmodel',antigo())
    gravar(tmp_path/'resumo.json',[{'nome':'sintetica','arquivo':'sintetica/sintetica.geo.json'}])
    r=referencias.catalogar(tmp_path)
    assert r[0]['arquivo'].endswith('.bbmodel')


def test_cli_inspecao_grava_so_resumo_e_imprime_ate_20_linhas(tmp_path,capsys):
    p=argparse.ArgumentParser();referencias.opcoes(p)
    model=biblioteca(tmp_path)
    output=tmp_path/'relatorios/estrutura.json'
    args=p.parse_args(['inspecionar',str(model),'--saida',str(output)])
    assert referencias.cmd_referencias(args)==0
    assert len(capsys.readouterr().out.splitlines())<=20
    r=json.loads(output.read_text(encoding='utf-8'))
    assert r['contagem']['pecas']==2
    assert 'elements' not in r and 'outliner' not in r


def test_erro_de_hierarquia_nao_fica_oculto(tmp_path):
    d=antigo();d['outliner']=[{'uuid':'root','children':[{'uuid':'head','children':[{'uuid':'root','children':[]}]}]}]
    with pytest.raises(ValueError,match='ciclo'):
        referencias.inspecionar(gravar(tmp_path/'ciclo.bbmodel',d))
