"""Confere o chute cedo e a preservação da trajetória caudal da v8 após mudar o ritmo."""
import copy
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image
from criaturas import bbmodelo

RAIZ=Path(__file__).resolve().parents[1]
def carregar(n,f):
    s=importlib.util.spec_from_file_location(n,RAIZ/'scripts'/f);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
g=carregar('ritmo_v9','animar-ritmo-cauda-pavao-f2-v9.py')
r8=carregar('revisao_v8','revisar-gancho-cauda-pavao-f2-v8.py')
previa=r8.previa


def conferir(m):
    fonte=bbmodelo.ler(g.FONTE);fn=g.v5.leitor_linear(m,g.NOME);original=g.v5.leitor_linear(fonte,g.NOME)
    src=lambda s:fn(g.tempo_novo(s))
    # Reutiliza os gates espaciais em tempo da fonte. Os metadados do golpe tardio
    # da v8 são substituídos abaixo pelas medidas do novo golpe antecipado.
    rel=r8.conferir(m,src,240)
    apice=g.tempo_novo(rel['apice_s'])
    for k in ['lancamento_velocidade','velocidade_vertical_inicio_chute','velocidade_vertical_impacto','inicio_chute_s','impacto_s']:
        rel.pop(k,None)
    for k in ['minimo_y_visivel','nova_penetracao_leque_cauda']:rel[k]=list(rel[k]);rel[k][1]=g.tempo_novo(rel[k][1]) if rel[k][1] is not None else None
    rel['fase_aerea_completa']=[g.tempo_novo(t) for t in rel['fase_aerea_completa']]
    rel['apice_s']=apice
    contato=r8.r7.r6.r5.r4.medir(m,src,g.v8.DURACAO,240)
    for k in ['minimo_y_visivel','minimo_penas_opacas_centros','nova_penetracao_pena_perna','minimo_caixas_inclui_transparencia']:
        contato[k]=list(contato[k]);contato[k][1]=g.tempo_novo(contato[k][1]) if contato[k][1] is not None else None
    rel.update(contato)
    assert rel['nova_penetracao_pena_perna'][0]<.05,rel['nova_penetracao_pena_perna']
    # Igualdade de rig, geometria e curvas comprova os demais clipes em qualquer instante.
    for campo in ['elements','textures','groups','outliner']:assert m.bruto[campo]==fonte.bruto[campo]
    preservados={}
    for a in fonte.animacoes:
        if a['name']==g.NOME:continue
        b=copy.deepcopy(a)
        for c in b.get('animators',{}).values():c.setdefault('keyframes',[])
        assert b==next(c for c in m.animacoes if c['uuid']==a['uuid'])
        preservados[a['name']]={'curvas_rig_geometria_identicos':True,'desvio_geometrico_max':0}
    # Confere todos os sólidos/planos da cauda no arquivo salvo, fase por fase.
    partes=[c for c in m.cubos if c.nome in g.v8.PARTES or c.osso.startswith('tail_blade_')];antes={c.uuid:c for c in fonte.cubos};erro=0
    for s in np.linspace(0,g.v8.DURACAO,685):
        a=bbmodelo.matrizes_ossos(fonte,original(s));b=bbmodelo.matrizes_ossos(m,src(s))
        for c in partes:
            x=bbmodelo.aplicar(bbmodelo.matriz_cubo(fonte,antes[c.uuid],a),bbmodelo.cantos(c));y=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,b),bbmodelo.cantos(c))
            erro=max(erro,float(np.linalg.norm(x-y,axis=1).max()))
    assert erro<.002,erro
    # Extensão completa na fase do impulso, antes do ápice, com alcance igual ao da v7.
    p=fn(g.IMPACTO);mat=bbmodelo.matrizes_ossos(m,p);impactos=[]
    for lado in ['left','right']:
        h=bbmodelo.aplicar(mat['waist'],[m.ossos['leg_'+lado].origem])[0];c=m.cubo('toe_'+lado+'_1')
        alvo=np.array([np.copysign(4.7,(c.de[0]+c.ate[0])/2),h[1]+5.5,h[2]-16.3])
        toe=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mat),[(c.de+c.ate)/2])[0]
        impactos.append(float(np.linalg.norm(toe-alvo)))
    assert max(impactos)<.025 and g.INICIO_CHUTE<g.SAI<g.IMPACTO<apice,(impactos,apice)
    rel.update(duracao=g.DURACAO,reducao_duracao_percentual=100*(1-g.DURACAO/g.v8.DURACAO),inicio_chute_s=g.INICIO_CHUTE,
               soltura_cauda_s=g.SAI,impacto_s=g.IMPACTO,chute_antes_apice=True,erro_extensao_impacto_max=max(impactos),
               desvio_cantos_cauda_apos_retemporizar=erro,cauda_v8_preservada_por_fase=True)
    _,tr=r8.r7.r6.r5.r4.anterior.leitor(m,next(a for a in m.animacoes if a['name']==g.NOME))
    maior=max(float(abs(np.diff(np.array([v for _,v in ch['rotation']]),axis=0)).max()) for ch in tr.values())
    pos=np.array([v for _,v in tr['body']['position']]);passo=float(np.linalg.norm(np.diff(pos,axis=0),axis=1).max())
    assert maior<30 and passo<1,(maior,passo)
    rel.update(variacao_euler_chave_max=maior,passo_bacia_chave_max=passo)
    (g.PASTA/'aprovados-preservados.json').write_text(json.dumps(preservados,indent=2)+'\n',encoding='utf-8')
    return fn,rel


def imagens(m,fn):
    tt=np.arange(0,g.DURACAO,.02);proj=previa.projetor(m,fn,tt,'lado',256,280)
    im=Image.new('RGB',(768,614),(246,248,251))
    for i,(t,fase) in enumerate([(g.CARGA,'carga J'),(g.SAI,'descarga'),(g.IMPACTO,'impacto cedo'),(.99,'recolhe'),(g.POUSA,'pouso'),(g.DURACAO,'neutro')]):
        im.paste(previa.quadro(m,fn,t,proj,fase),(i%3*256,i//3*307))
    im.save(g.PASTA/'poses-ritmo.png')
    projs=[previa.projetor(m,fn,tt,v,384,300) for v in ['3/4','lado']];frames=[]
    for t in list(tt)+[g.DURACAO]*15:
        fase='carga' if t<g.INICIO_CHUTE else 'impulso e chute' if t<g.FIM_GOLPE else 'pouso' if t<g.POUSA else 'recupera'
        im=Image.new('RGB',(768,327),(246,248,251))
        for i,p in enumerate(projs):im.paste(previa.quadro(m,fn,t,p,fase),(i*384,0))
        frames.append(im)
    dur=[20]*len(tt);dur[-1]=round((g.DURACAO-float(tt[-1]))*1000);dur.extend([20]*15)
    frames[0].save(g.PASTA/'previa-ritmo.gif',save_all=True,append_images=frames[1:],duration=dur,loop=0)


def main():
    m=bbmodelo.ler(g.SAIDA);fn,rel=conferir(m)
    (g.PASTA/'medidas-ritmo.json').write_text(json.dumps(rel,indent=2)+'\n',encoding='utf-8')
    print('Duração',g.DURACAO,'redução',round(rel['reducao_duracao_percentual'],2),'%; impacto',g.IMPACTO,'ápice',rel['apice_s'])
    print('Cauda: desvio',rel['desvio_cantos_cauda_apos_retemporizar'],'piso',rel['minimo_y_visivel'],'penas/pernas',rel['nova_penetracao_pena_perna'])
    print('Extensão golpe: erro',rel['erro_extensao_impacto_max'],'continuidade Euler',rel['variacao_euler_chave_max'])
    imagens(m,fn)


if __name__=='__main__':main()
