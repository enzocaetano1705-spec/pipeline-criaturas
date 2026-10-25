"""Confere estrutura, textura sólida, piso opaco e vínculos das penas da F3."""
import hashlib
import json
from pathlib import Path

import numpy as np
from criaturas import bbmodelo, exportar, motor, roblox_infra, texturizar

PASTA=Path(__file__).resolve().parents[1]/'modelos/criatura-pavao/f3'
ARQUIVO=PASTA/'criatura-pavao-e3.bbmodel'


def superficie(m,c):
    if np.all(c.tamanho>1e-5):return bbmodelo.cantos(c)
    mask,axes=roblox_infra.mascara_plano(m,c)
    y,x=np.nonzero(mask)
    points=[]
    for dx,dy in [(0,0),(0,1),(1,0),(1,1)]:
        p=np.tile(c.de,(len(x),1))
        p[:,axes[0]]+=(x+dx)/mask.shape[1]*c.tamanho[axes[0]]
        p[:,axes[1]]+=(y+dy)/mask.shape[0]*c.tamanho[axes[1]]
        points.append(p)
    return np.concatenate(points)


def main():
    m=bbmodelo.ler(ARQUIVO);mats=bbmodelo.matrizes_ossos(m)
    engine=motor.validar(ARQUIVO,allow_planes=True,min_thickness=.5)
    (PASTA/'validacao-estrutura.json').write_text(json.dumps(engine,indent=2)+'\n',encoding='utf-8')
    alpha=np.asarray(m.textura)[:,:,3];empty=[];floor=[];blank=[];parents=[];contacts=[]
    for c in m.cubos:
        points=superficie(m,c)
        if not len(points):blank.append(c.nome);continue
        world=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mats),points)
        floor.append((float(world[:,1].min()),c.nome))
        if np.all(c.tamanho>1e-5):
            for face in c.faces:
                rows=texturizar.texels_da_face(c,face,np.eye(4))
                if rows is None:continue
                uv=np.asarray(rows[0],int)
                if len(uv) and np.any(alpha[uv[:,1],uv[:,0]]<255):empty.append(c.nome+'.'+face)
        if c.nome.startswith('arm_blade_'):
            side='left' if '_left_' in c.nome else 'right'
            if m.ossos[c.osso].pai!='forearm_'+side:parents.append(c.nome)
        if c.nome.startswith('ankle_plume_'):
            side='left' if '_left_' in c.nome else 'right'
            if m.ossos[c.osso].pai!='shin_'+side:parents.append(c.nome)
        if c.nome.startswith(('arm_blade_','ankle_plume_','tail_fan_')):
            axis=int(np.argmax(c.tamanho))
            progress=(points[:,axis]-c.de[axis])/c.tamanho[axis]
            if not c.nome.startswith('tail_fan_'):progress=1-progress
            distal=progress>.20
            for solid in m.cubos:
                if not np.all(solid.tamanho>1e-5):continue
                local=bbmodelo.aplicar(np.linalg.inv(bbmodelo.matriz_cubo(m,solid,mats)),world)
                depth=np.minimum(local-solid.de,solid.ate-local).min(axis=1)
                if np.any((depth>.2)&distal):
                    selected=(depth>.2)&distal
                    contacts.append({'plano':c.nome,'solido':solid.nome,
                                     'profundidade':round(float(depth[distal].max()),3),
                                     'fracao_comprimento_max':round(float(progress[selected].max()),3),
                                     'amostras':int(selected.sum()),'total':len(points)})
    uv_errors=exportar.uv_fora_do_atlas(m)
    minimum=min(floor)
    report={'fonte_sha256':hashlib.sha256(ARQUIVO.read_bytes()).hexdigest(),
            'motor':engine['summary'],'avisos_por_gate':{g['id']:len(g['violations']) for g in engine['gates']},
            'pecas':len(m.cubos),'ossos':len(m.ossos),'locators':len(m.locators),'animacoes':len(m.animacoes),
            'atlas':list(m.resolucao),'faces_solidas_com_transparencia':empty,'planos_sem_pixels':blank,
            'uv_fora_do_atlas':uv_errors,'vinculos_incorretos':parents,
            'contatos_opacos_distais':contacts,
            'piso_opaco_minimo':{'y':minimum[0],'peca':minimum[1]},
            'limite':'Interpenetração usa AABB; penas recortadas/rotacionadas e encaixes precisam de revisão visual. Não valida combate nem colisão no Studio.'}
    # Só a inserção proximal rasa da pena em sua própria canela é aceita.
    unexpected=[c for c in contacts if not (c['plano'].startswith('ankle_plume_')
        and c['solido']=='shank_'+('left' if '_left_' in c['plano'] else 'right')
        and c['profundidade']<=.5 and c['fracao_comprimento_max']<=.4)]
    report['contatos_opacos_inesperados']=unexpected
    report['aprovado_tecnicamente']=engine['summary']['errors']==0 and not (empty or blank or uv_errors or parents or unexpected) and minimum[0]>=-.05
    (PASTA/'revisao.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (PASTA/'sobreposicoes-opacas.json').write_text(json.dumps(contacts,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Estrutura:',engine['summary'])
    print('Avisos:',report['avisos_por_gate'])
    print('Piso opaco:',minimum,'; faces sólidas vazias:',len(empty),'; UVs fora:',len(uv_errors))
    print('Vínculos incorretos:',parents,'; planos vazios:',blank)
    print('Contatos opacos distais:',len(contacts))
    print('Revisão técnica:',report['aprovado_tecnicamente'])
    if not report['aprovado_tecnicamente']:raise SystemExit(1)


if __name__=='__main__':main()
