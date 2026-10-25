"""Repara números Molang e compacta o descanso sem redesenhar movimentos.

    Saída nova; toda alteração do bbmodel passa pelo motor externo.
"""
import argparse
import copy
import importlib.util
import json
import shutil
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('f3_v9',ROOT/'scripts/animar-combate-pavao-f3-v9.py')
v9=importlib.util.module_from_spec(sp);sp.loader.exec_module(v9)
g,v2,v3,bbmodelo,motor=v9.g,v9.v2,v9.v3,v9.bbmodelo,v9.motor
R,point=v9.R,v9.point
ENTER,EXIT,TRANSITION=v9.ENTER,v9.EXIT,v9.TRANSITION
REST_START,REST_END,REST_EXIT,RESUME=v9.REST_START,v9.REST_END,v9.REST_EXIT,v9.RESUME
phase,dock_time,SIDES=v9.phase,v9.dock_time,v9.SIDES
CLIPS,APPROVED=v9.CLIPS,v9.APPROVED
SOURCE=v9.FILE
OUT=ROOT/'modelos/criatura-pavao/f3/animacoes-v10'
FILE=OUT/'criatura-pavao-e3-combate-v10.bbmodel'
v9.SOURCE=SOURCE;v3.SOURCE=SOURCE
new_rig=v9.new_rig;compose_base=v9.compose_base


def canonical_animation(a):
    """Igualdade do conteúdo animado; UUID de chave e grafia decimal não mudam a pose."""
    a=copy.deepcopy(a)
    a['animators']={u:x for u,x in a['animators'].items() if x.get('keyframes')}
    for anim in a['animators'].values():
        for k in anim['keyframes']:
            k.pop('uuid',None)
            for p in k['data_points']:
                for axis in 'xyz':p[axis]=float(p[axis])
        anim['keyframes'].sort(key=lambda k:(k['channel'],k['time']))
    return a


def common_rdp(times,values,forced):
    """Reduz um vetor de canais respeitando o limite normalizado de erro."""
    keep=set(forced);stack=list(zip(sorted(keep)[:-1],sorted(keep)[1:]))
    while stack:
        a,b=stack.pop()
        if b<=a+1:continue
        w=(times[a+1:b]-times[a])/(times[b]-times[a])
        linear=values[a]+w[:,None]*(values[b]-values[a])
        errors=np.max(abs(values[a+1:b]-linear),axis=1)
        j=int(np.argmax(errors))
        if errors[j]>1:
            i=a+1+j;keep.add(i);stack.extend([(a,i),(i,b)])
    return sorted(keep)


def strip_constant_spans(indices,values):
    """Elimina miolos parados, conservando as bordas de cada pausa."""
    return [i for k,i in enumerate(indices) if k==0 or k==len(indices)-1 or
            max(np.max(abs(values[i]-values[indices[k-1]])),
                np.max(abs(values[indices[k+1]]-values[i])))>1e-7]


def idle_ops(m):
    saved=v2.review.Saved(m);name='combat_idle';length=saved.durations[name]
    times=np.unique(np.concatenate([ts for ch in saved.channels[name].values() for ts,_ in ch.values()]))
    channels=[]
    for bone,ch in saved.channels[name].items():
        for field,(ts,vs) in ch.items():
            vals=np.column_stack([np.interp(times,ts,vs[:,i]) for i in range(3)])
            constant=np.max(np.ptp(vals,axis=0))<1e-7
            channels.append((bone,field,vals,constant))
    events=[0,.48,.72,.95,REST_START,REST_END,REST_END+.30,REST_EXIT,
            REST_EXIT+dock_time('left'),REST_EXIT+dock_time('right'),length]
    forced={int(np.argmin(abs(times-t))) for t in events}
    ops=[{'op':'remove_animation','animation':name},
         {'op':'add_animation','name':name,'length':length,'loop':'once','snapping':120}]
    for bone,field,values,constant in channels:
        # A interpolação de cada canal é aproximada com limite pequeno.
        # Verificamos também a tolerância temporal nativa, não só float/linear.
        individual=common_rdp(times,values/(.01 if field=='rotacao' else .001),forced)
        for i in ([0,len(times)-1] if constant else strip_constant_spans(individual,values)):
            ops.append({'op':'set_keyframe','animation':name,'bone':bone,
                        'channel':'rotation' if field=='rotacao' else 'position',
                        'time':float(times[i]),'value':values[i].tolist(),'interpolation':'linear'})
    return ops,{'tempos_antes':len(times),'tempos_distintos_depois':len({op['time'] for op in ops if op['op']=='set_keyframe'}),
                'chaves_antes':sum(len(a.get('keyframes',[])) for a in next(a for a in m.animacoes if a['name']==name)['animators'].values()),
                'chaves_depois':len(ops)-2,'tolerancia_graus_por_eixo':.01,'tolerancia_unidades_por_eixo':.001,
                'eventos_preservados':events}


def generate(study=False):
    m=bbmodelo.ler(SOURCE);ops,compression=idle_ops(m);repairs={}
    for a in m.animacoes:
        if a['name']=='combat_idle':continue
        count=0
        for uid,anim in a['animators'].items():
            for k in anim.get('keyframes',[]):
                p=k['data_points'][0]
                if any('e' in str(p.get(ax,'')).lower() for ax in 'xyz'):
                    assert len(k['data_points'])==1 and k['interpolation']=='linear'
                    ops.append({'op':'set_keyframe','animation':a['name'],'bone':uid,
                        'channel':k['channel'],'time':k['time'],'value':[p[x] for x in 'xyz'],
                        'interpolation':k['interpolation']});count+=1
        repairs[a['name']]=count
    (OUT/'_cache').mkdir(parents=True,exist_ok=True)
    report={'fonte_sha256':g.sha(SOURCE),'compactacao_idle':compression,'chaves_com_expoente_reparadas':repairs}
    g.dump(OUT/'compactacao.json',report)
    print('Descanso:',compression['chaves_antes'],'->',compression['chaves_depois'],'chaves.',flush=True)
    print('Expoentes nos outros clipes:',sum(repairs.values()),'chaves; sem alterar valores.',flush=True)
    if study:
        # Simulação em memória: nenhum bbmodel é escrito neste estudo.
        candidate=copy.copy(m);candidate.animacoes=copy.deepcopy(m.animacoes)
        idle=next(a for a in candidate.animacoes if a['name']=='combat_idle')
        idle['animators']={}
        for op in ops:
            if op['op']!='set_keyframe' or op['animation']!='combat_idle':continue
            uid=m.ossos[op['bone']].uuid
            anim=idle['animators'].setdefault(uid,{'name':op['bone'],'type':'bone','keyframes':[]})
            anim['keyframes'].append({'channel':op['channel'],'time':op['time'],
                'data_points':[dict(zip('xyz',map(motor._valor_chave,op['value'])))],'interpolation':'linear'})
        reader=v9.auditmod.NativeSaved(v2.review.Saved(candidate))
        previous_file=globals()['FILE'];globals()['FILE']=SOURCE
        try:v9.review8.check(__import__(__name__),['combat_idle'],reader_factory=lambda _:reader,sample_offset=.00047)
        finally:globals()['FILE']=previous_file
        return
    if FILE.exists():
        record=json.loads((OUT/'geracao.json').read_text(encoding='utf-8'))
        if record['saida_sha256']!=g.sha(FILE):raise ValueError('Saída editada fora do gerador; preserve em outra versão.')
    shutil.copy2(SOURCE,FILE)
    ops.append({'op':'set_model_properties','name':'criatura-pavao-e3-combate-v10'})
    g.dump(OUT/'_cache/ops.json',ops)
    motor.editar(FILE,ops,lote=500)
    report['saida_sha256']=g.sha(FILE);report['operacoes']=len(ops)
    g.dump(OUT/'geracao.json',report)
    print('Gravado:',FILE.name,flush=True)


def validate():
    source=bbmodelo.ler(SOURCE);out=bbmodelo.ler(FILE)
    for a in source.animacoes:
        if a['name']=='combat_idle':continue
        b=next(x for x in out.animacoes if x['name']==a['name'])
        assert canonical_animation(a)==canonical_animation(b),a['name']
    for a in out.animacoes:
        for anim in a['animators'].values():
            for k in anim.get('keyframes',[]):
                for p in k['data_points']:
                    assert all('e' not in str(p[x]).lower() for x in 'xyz'),(a['name'],k['time'])
    v9.review8.check(__import__(__name__),list(CLIPS))
    v9.review8.check(__import__(__name__),list(CLIPS),reader_factory=v9.auditmod.NativeSaved,sample_offset=.00047)


def technical_audit():
    """Mede o desvio visual da compactação e a preservação dos demais clipes."""
    src=bbmodelo.ler(SOURCE);out=bbmodelo.ler(FILE)
    a=v2.review.Saved(src);b=v2.review.Saved(out);rig=new_rig(out)
    pieces=[]
    for c in src.cubos:
        base=bbmodelo.matriz_cubo(src,c,bbmodelo.matrizes_ossos(src))
        pieces.append((c.osso,bbmodelo.aplicar(base,bbmodelo.cantos(c))))
    maximum=0.;worst={};rotation=position=0.
    for t in np.linspace(0,CLIPS['combat_idle'],round(CLIPS['combat_idle']*240)+1):
        p=a.pose('combat_idle',float(t));q=b.pose('combat_idle',float(t))
        am=rig.mats(p);bm=rig.mats(q)
        for n in p:
            for field in p[n]:
                error=float(abs(p[n][field]-q[n][field]).max())
                if field=='rotacao':rotation=max(rotation,error)
                else:position=max(position,error)
        for name,vertices in pieces:
            va=bbmodelo.aplicar(am[name],vertices);vb=bbmodelo.aplicar(bm[name],vertices)
            error=float(np.linalg.norm(va-vb,axis=1).max())
            if error>maximum:maximum=error;worst={'bone':name,'t':float(t)}
    assert rotation<=.010001 and position<=.001001
    result={'compactacao_idle':{'erro_angular_por_eixo':rotation,'erro_posicao_por_eixo':position,
            'maior_desvio_visual_unidades':maximum,'pior_amostra':worst,'amostras_por_segundo':240},
            'outros_12_clipes':'mesmos valores, tempos, interpolacoes e metadados; somente grafia decimal/UUID de chave',
            'notacao_cientifica_restante':0,'geometria_textura_rig':'iguais a v9',
            'causa_confirmada_no_parser_instalado':{'1e-8':-8,'-8.2e-7':-7,'-6.5e-7':-7,
                                                   '0.00000001':1e-8,'-0.00000082':-8.2e-7}}
    g.dump(OUT/'comparacao-tecnica.json',result)
    print('Desvio visual máximo do descanso:',round(maximum,6),'unidades.',flush=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--estudo',action='store_true');ap.add_argument('--gerar',action='store_true')
    ap.add_argument('--validar',action='store_true');ap.add_argument('--auditar',action='store_true');args=ap.parse_args()
    if args.estudo or args.gerar:generate(study=args.estudo)
    if args.validar:validate()
    if args.auditar:technical_audit()


if __name__=='__main__':main()
