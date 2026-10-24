"""Conferência da v7 salva: superfícies, curva, transferência, impulso e aprovados."""
import argparse
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
g=carregar('catapulta_v7','animar-catapulta-pavao-f2-v7.py')
r6=carregar('revisao_v6','revisar-impulso-cauda-pavao-f2-v6.py')
previa=r6.r5.r4.previa


def aprovados(m):
    antes=bbmodelo.ler(g.FONTE);res={}
    for clip in antes.animacoes:
        nome=clip['name'];dur=clip['length']
        if nome==g.NOME:continue
        copia=copy.deepcopy(clip)
        for v in copia.get('animators',{}).values():v.setdefault('keyframes',[])
        assert copia==next(a for a in m.animacoes if a['uuid']==clip['uuid'])
        if nome not in ['attack_stomp','attack_spin']:
            novos=set(m.ossos)-set(antes.ossos)
            assert not ({m.ossos[n].uuid for n in novos}&set(clip.get('animators',{})))
            for n,o in antes.ossos.items():
                novo=m.ossos[n];pai=novo.pai
                while pai in novos:pai=m.ossos[pai].pai
                assert pai==o.pai
                np.testing.assert_allclose(novo.origem,o.origem,atol=1e-10)
                np.testing.assert_allclose(novo.rotacao,o.rotacao,atol=1e-10)
            res[nome]={'chaves_originais_preservadas':True,'prova':'Articulações inseridas neutras, sem animadores no clipe; cadeia reduzida e transformações originais iguais. Vale também para curvas não lineares.'}
            continue
        aa=g.v5.leitor_linear(antes,nome);bb=g.v5.leitor_linear(m,nome);erro=0
        for t in np.linspace(0,dur,int(round(dur*240))+1):
            ma=bbmodelo.matrizes_ossos(antes,aa(t));mb=bbmodelo.matrizes_ossos(m,bb(t))
            for c in m.cubos:
                orig=antes.cubo('tail_mid' if c.nome.startswith('tail_mid') else 'tail_base') if c.nome in g.PARTES else next(x for x in antes.cubos if x.uuid==c.uuid)
                # Para cada fatia, aplica os mesmos pontos materiais nas matrizes antiga/nova.
                a=bbmodelo.aplicar(bbmodelo.matriz_cubo(antes,orig,ma),bbmodelo.cantos(c))
                b=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mb),bbmodelo.cantos(c))
                erro=max(erro,float(np.linalg.norm(a-b,axis=1).max()))
        assert erro<1e-8,(nome,erro)
        res[nome]={'desvio_superficies_max':erro,'amostragem_hz':240,'chaves_originais_preservadas':True}
    for n in ['tail_mid','tail_base']:
        orig=antes.cubo(n);segs=[m.cubo(n if i==0 else f'{n}_{i+1}') for i in range(3)]
        for i,c in enumerate(segs):
            assert c.faces==g.faces_fatia(orig,i/3,(i+1)/3)
            np.testing.assert_allclose(c.de[:2],orig.de[:2]);np.testing.assert_allclose(c.ate[:2],orig.ate[:2])
            np.testing.assert_allclose(c.origem,orig.origem);np.testing.assert_allclose(c.rotacao,orig.rotacao)
            assert abs(c.de[2]-(orig.de[2]+orig.tamanho[2]*i/3))<1e-8
            assert abs(c.ate[2]-(orig.de[2]+orig.tamanho[2]*(i+1)/3))<1e-8
    assert m.bruto['textures']==antes.bruto['textures']
    res['uv']={'particao_contigua':True,'uv_recortado_proporcionalmente':True,'atlas_identico':True,'observacao':'Faces internas fecham as fatias; ocultas em repouso e nos clipes aprovados.'}
    return res


def conferir(m,fn):
    surf={c.uuid:g.v5.v4.superficie_opaca(m,c) for c in m.cubos}
    mini=(100,None,None);air=[];solo=[];patas=[];juntas=[];curva=[];com=[];tang=[];traj=[]
    fans=[c for c in m.cubos if c.osso.startswith('tail_blade_')]
    rest=bbmodelo.matrizes_ossos(m);nn=np.array([bbmodelo.matriz_cubo(m,c,rest)[:3,0] for c in fans]);gram=nn@nn.T;ab=[]
    for t in np.linspace(0,g.DURACAO,int(round(g.DURACAO*240))+1):
        t=float(t);p=fn(t);mat=bbmodelo.matrizes_ossos(m,p);ys=[];angles=[]
        for c in m.cubos:
            y=float(bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mat),surf[c.uuid])[:,1].min());ys.append(y)
            if y<mini[0]:mini=(y,t,c.nome)
        for n in g.PARTES:
            c=m.cubo(n);r=bbmodelo.matriz_cubo(m,c,mat);angles.append(np.degrees(np.arctan2(-r[1,2],r[2,2])))
        if .48<=t<=g.CARGA:
            curva.append(float(abs(np.diff(angles)).max()))
            tang.append(abs(angles[0]-(p['pelvis']['rotacao'][0]-15)))
        ty=min(float(bbmodelo.caixa_mundo(m,m.cubo(n),mat)[0][1]) for n in g.PARTES)
        if .34<=t<=g.SAI:solo.append(abs(ty-g.CHAO))
        if g.SAI<t<g.POUSA and min(ys)>g.CHAO+.05:air.append(t)
        if .54<=t<=g.SAI:
            fy=min(float(bbmodelo.caixa_mundo(m,c,mat)[0][1]) for c in m.cubos if c.osso in ['foot_left','foot_right'])
            patas.append(fy)
        for bone,a,b in [('waist','hips','TorsoHips'),('chest','TorsoHips','torso'),('tail_1','hips','tail_mid')]:
            o=m.ossos[bone];pt=bbmodelo.aplicar(mat[bone],[o.origem])[0]
            juntas.extend([r6.fora(m,m.cubo(a),mat,pt),r6.fora(m,m.cubo(b),mat,pt)])
        ns=np.array([bbmodelo.matriz_cubo(m,c,mat)[:3,0] for c in fans]);ab.append(float(abs(ns@ns.T-gram).max()))
        if abs(t-g.CARGA)<.001:
            massa=[];centros=[]
            for c in m.cubos:
                v=float(np.prod(c.tamanho))
                if v>0 and c.nome not in g.PARTES:
                    massa.append(v);centros.append(bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mat),[(c.de+c.ate)/2])[0])
            centro=np.average(centros,axis=0,weights=massa)
            apoio=np.concatenate([bbmodelo.aplicar(bbmodelo.matriz_cubo(m,m.cubo(n),mat),bbmodelo.cantos(m.cubo(n))) for n in g.PARTES])
            chao=apoio[apoio[:,1]<g.CHAO+.25]
            com={'centro_volumes_solidos_sem_cauda':centro.tolist(),'apoio_z':chao[:,2].tolist(),'distancia_z_apoio':float(abs(centro[2]-chao[:,2].mean())),
                 'limite':'Proxy visual de volume com densidade uniforme; não é massa física ou prova de equilíbrio.'}
        traj.append(p['body']['posicao'])
    for t in [0,g.DURACAO]:
        mat=bbmodelo.matrizes_ossos(m,fn(t))
        for n in mat:np.testing.assert_allclose(mat[n],rest[n],atol=2e-5)
    a,v,f,grav=g.cinematica(m);tt=np.linspace(g.CARGA+.01,g.SAI-.01,100)
    aa=np.array([(g.corpo(m,t+.001)-2*g.corpo(m,t)+g.corpo(m,t-.001))/.001**2 for t in tt])
    pico=float(tt[np.argmax(np.linalg.norm(aa[:,1:],axis=1))])
    assert mini[0]>g.CHAO-.025,mini
    assert max(juntas)<1e-5 and max(solo)<.025
    assert max(curva)<30 and max(ab)<1e-6
    assert min(patas)>.5 and max(air)-min(air)>.65
    assert v[1]>35 and v[2]<-15
    return {'minimo_y_visivel':mini,'erro_juntas_max':max(juntas),'erro_apoio_cauda_max':max(solo),'dobra_por_junta_carga_max_graus':max(curva),
            'patas_livres_carga_min_y':min(patas),'fase_aerea_completa':[min(air),max(air)],'velocidade_lancamento':v.tolist(),
            'subida_bacia_apos_soltar':float(v[1]**2/(2*grav)),'avanco_no_ar':float(a[2]-f[2]),'pico_aceleracao_carga_s':pico,
            'transferencia_volume':com,'leque_abertura_erro_max':max(ab),'inicio_fim_neutros':True}


def imagens(m,fn,planejado=False):
    tt=np.arange(0,g.DURACAO,.02);projs=[previa.projetor(m,fn,tt,v,384,300) for v in ['3/4','lado']]
    im=Image.new('RGB',(768,741),(246,248,251));proj=previa.projetor(m,fn,tt,'lado',256,220)
    for i,(t,fase) in enumerate([(.30,'dedos'),(.46,'transfere'),(.62,'carga'),(.78,'descarga'),(.88,'catapulta'),(1.,'chute'),(1.2,'ar'),(1.6,'pouso'),(1.77,'absorve')]):
        im.paste(previa.quadro(m,fn,t,proj,fase),(i%3*256,i//3*247))
    im.save(g.PASTA/('poses-planejadas.png' if planejado else 'poses-catapulta.png'))
    if planejado:return
    frames=[]
    for t in list(tt)+[g.DURACAO]*15:
        im=Image.new('RGB',(768,327),(246,248,251))
        fase='dedos' if t<.38 else 'transfere peso' if t<.62 else 'descarga' if t<g.SAI else 'catapulta e chute' if t<1.17 else 'pouso' if t<1.77 else 'recupera'
        for i,proj in enumerate(projs):im.paste(previa.quadro(m,fn,t,proj,fase),(i*384,0))
        frames.append(im)
    frames[0].save(g.PASTA/'previa-catapulta.gif',save_all=True,append_images=frames[1:],duration=20,loop=0)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--poses',action='store_true');a=ap.parse_args()
    if a.poses:
        m=bbmodelo.ler(g.FONTE);g.preparar_rig(m);fn=lambda t:g.pose(m,t)
    else:m=bbmodelo.ler(g.SAIDA);fn=g.v5.leitor_linear(m,g.NOME)
    rel=conferir(m,fn);rel.update(r6.r5.r4.medir(m,fn,g.DURACAO,60 if a.poses else 240))
    assert rel['nova_penetracao_pena_perna'][0]<.05,rel['nova_penetracao_pena_perna']
    if not a.poses:
        (g.PASTA/'aprovados-preservados.json').write_text(json.dumps(aprovados(m),indent=2)+'\n',encoding='utf-8')
        _,tr=r6.r5.r4.anterior.leitor(m,next(v for v in m.animacoes if v['name']==g.NOME))
        maior=max(float(abs(np.diff(np.array([v for _,v in ch['rotation']]),axis=0)).max()) for ch in tr.values())
        pos=np.array([v for _,v in tr['body']['position']]);passo=float(np.linalg.norm(np.diff(pos,axis=0),axis=1).max())
        assert maior<30 and passo<1,(maior,passo)
        assert all('scale' not in ch for ch in tr.values())
        rel.update(variacao_euler_chave_max=maior,passo_bacia_chave_max=passo,sem_escala=True)
    (g.PASTA/('medidas-planejadas-superficies.json' if a.poses else 'medidas-catapulta.json')).write_text(json.dumps(rel,indent=2)+'\n',encoding='utf-8')
    print('Chão',rel['minimo_y_visivel'],'pena/perna',rel['nova_penetracao_pena_perna'])
    print('Dobra por junta',rel['dobra_por_junta_carga_max_graus'],'voo',rel['fase_aerea_completa'],'subida',rel['subida_bacia_apos_soltar'])
    print('Transferência',rel['transferencia_volume'],'pico aceleração',rel['pico_aceleracao_carga_s'])
    imagens(m,fn,a.poses)


if __name__=='__main__':main()
