"""V6: comprova preservação, juntas, altura do golpe e fase aérea; gera prévia a 1x."""
import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image
from criaturas import bbmodelo

RAIZ=Path(__file__).resolve().parents[1]


def carregar(n,arquivo):
    s=importlib.util.spec_from_file_location(n,RAIZ/'scripts'/arquivo)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


g=carregar('criador_v6','animar-impulso-cauda-pavao-f2-v6.py')
r5=carregar('revisor_v5','revisar-combate-pavao-f2-v5.py')


def folha(m,fn,pasta,nome):
    im=Image.new('RGB',(768,654),(246,248,251));tt=np.linspace(0,g.DURACAO,65)
    proj=r5.r4.previa.projetor(m,fn,tt,'lado',256,300)
    for i,(t,fase) in enumerate([(.40,'apoia'),(.54,'comprime'),(.70,'impulsiona'),(.85,'golpe no ar'),(1.12,'pousa'),(1.26,'absorve')]):
        im.paste(r5.r4.previa.quadro(m,fn,t,proj,fase),(i%3*256,i//3*327))
    im.save(pasta/nome)


def gif(m,fn,pasta):
    tt=np.arange(0,g.DURACAO,.02);projs=[r5.r4.previa.projetor(m,fn,tt,v,384,300) for v in ['3/4','lado']]
    frames=[]
    for t in list(tt)+[g.DURACAO]*15:
        im=Image.new('RGB',(768,327),(246,248,251))
        fase='apoio' if t<.43 else 'carga' if t<.54 else 'impulso' if t<g.SAI else 'golpe aereo' if t<1.0 else 'pouso' if t<1.26 else 'recupera'
        for i,p in enumerate(projs):im.paste(r5.r4.previa.quadro(m,fn,t,p,fase),(i*384,0))
        frames.append(im)
    frames[0].save(pasta/'previa-impulso.gif',save_all=True,append_images=frames[1:],duration=20,loop=0)


def fora(m,c,mats,p):
    q=bbmodelo.aplicar(np.linalg.inv(bbmodelo.matriz_cubo(m,c,mats)),[p])[0]
    return float(np.linalg.norm(np.maximum(np.maximum(c.de-q,q-c.ate),0)))


def conferir(m,fn):
    minimo=(100,None,None);juntas=[];solo=[];voo=[];altura=[];leque=[];passos=[];trajeto=[]
    superficie={c.uuid:g.v5.v4.superficie_opaca(m,c) for c in m.cubos}
    rest=bbmodelo.matrizes_ossos(m);fans=[c for c in m.cubos if c.osso.startswith('tail_blade_')]
    nn=np.array([bbmodelo.matriz_cubo(m,c,rest)[:3,0] for c in fans]);abertura=nn@nn.T
    for t in np.linspace(0,g.DURACAO,505):
        t=float(t);p=fn(t);mat=bbmodelo.matrizes_ossos(m,p);yvis=[]
        for c in m.cubos:
            y=float(bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mat),superficie[c.uuid])[:,1].min());yvis.append(y)
            if y<minimo[0]:minimo=(y,t,c.nome)
        for bone,a,b in [('waist','hips','TorsoHips'),('chest','TorsoHips','torso'),('tail_1','hips','tail_mid')]:
            o=m.ossos[bone];pt=bbmodelo.aplicar(mat[bone],[o.origem])[0]
            juntas.extend([fora(m,m.cubo(a),mat,pt),fora(m,m.cubo(b),mat,pt)])
        ty=min(float(bbmodelo.caixa_mundo(m,m.cubo(n),mat)[0][1]) for n in ['tail_mid','tail_base'])
        if .40<=t<=g.SAI:solo.append(abs(ty-g.CHAO))
        if g.SAI<t<g.POUSA and min(yvis)>g.CHAO+.05:voo.append(t)
        for lado in ['left','right']:
            c=m.cubo('toe_'+lado+'_1');pt=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mat),[(c.de+c.ate)/2])[0]
            if .82<=t<=.88:altura.append(abs(float(pt[1])-g.altura_peito(m)))
            if .54<=t<=.69:
                fy=min(float(bbmodelo.caixa_mundo(m,c,mat)[0][1]) for c in m.cubos if c.osso=='foot_'+lado)
                passos.append(fy)
            if .82<=t<=.88:trajeto.append(pt.tolist())
        nn=np.array([bbmodelo.matriz_cubo(m,c,mat)[:3,0] for c in fans]);leque.append(float(abs(nn@nn.T-abertura).max()))
    for t in [0,g.DURACAO]:
        mat=bbmodelo.matrizes_ossos(m,fn(t))
        for n in mat:np.testing.assert_allclose(mat[n],rest[n],atol=2e-5)
    a,v,f,grav=g.cinematica(m)
    assert max(juntas)<1e-5
    assert max(solo)<.025
    assert max(altura)<.025
    assert min(passos)>.5
    assert voo and max(voo)-min(voo)>.1
    assert max(leque)<1e-6
    assert v[1]>10 and v[2]<-10 and grav>0
    return {'minimo_y_visivel':minimo,'juntas_fora_dos_volumes_max':max(juntas),'erro_apoio_cauda_max':max(solo),
            'fase_aerea_completa':[min(voo),max(voo)],'patas_livres_na_carga_min_y':min(passos),
            'altura_peito_base':g.altura_peito(m),'erro_altura_impacto_max':max(altura),
            'abertura_leque_erro_max':max(leque),'velocidade_soltar_cauda':v.tolist(),
            'avanco_durante_voo':float(a[2]-f[2]),'gravidade_visual':grav,'inicio_fim_neutros':True,
            'impacto_patas_amostras':trajeto}


def aprovados(m):
    antes=bbmodelo.ler(g.FONTE);porid={c.uuid:c for c in m.cubos};res={}
    for nome,dur in [('attack_stomp',1.25),('attack_spin',1.65)]:
        aa=g.v5.leitor_linear(antes,nome);bb=g.v5.leitor_linear(m,nome);erro=0
        for t in np.linspace(0,dur,int(round(dur*240))+1):
            ma=bbmodelo.matrizes_ossos(antes,aa(t));mb=bbmodelo.matrizes_ossos(m,bb(t))
            for c in antes.cubos:
                pa=bbmodelo.aplicar(bbmodelo.matriz_cubo(antes,c,ma),bbmodelo.cantos(c));pb=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,porid[c.uuid],mb),bbmodelo.cantos(c))
                erro=max(erro,float(np.linalg.norm(pa-pb,axis=1).max()))
        assert erro<1e-8;res[nome]={'desvio_cantos_max':erro,'amostragem_hz':240,'chaves_originais_preservadas':True}
    return res


def main():
    pa=argparse.ArgumentParser(description=__doc__);pa.add_argument('--poses',action='store_true');pa.add_argument('--sem-gif',action='store_true');a=pa.parse_args()
    if a.poses:
        m=bbmodelo.ler(g.FONTE);g.preparar_rig(m);fn=lambda t:g.pose(m,t)
    else:
        m=bbmodelo.ler(g.SAIDA);fn=g.v5.leitor_linear(m,g.NOME)
    pasta=g.PASTA;pasta.mkdir(exist_ok=True)
    rel=conferir(m,fn);rel.update(r5.r4.medir(m,fn,g.DURACAO,60 if a.poses else 240))
    rel['impacto_patas_amostras']=rel['impacto_patas_amostras'][::4]
    assert rel['minimo_y_visivel'][0]>g.CHAO-.025
    if not a.poses:
        assert rel['nova_penetracao_pena_perna'][0]<.05
        (pasta/'aprovados-preservados.json').write_text(json.dumps(aprovados(m),indent=2)+'\n',encoding='utf-8')
        _,tr=r5.r4.anterior.leitor(m,next(v for v in m.animacoes if v['name']==g.NOME))
        maior=max(float(abs(np.diff(np.array([v for _,v in ch['rotation']]),axis=0)).max()) for ch in tr.values())
        desloc=np.array([v for _,v in tr['body']['position']]);passo=float(np.linalg.norm(np.diff(desloc,axis=0),axis=1).max())
        assert maior<30 and passo<1
        rel.update(variacao_euler_chave_max=maior,passo_bacia_chave_max=passo)
    (pasta/('medidas-planejadas-superficies.json' if a.poses else 'medidas-impulso.json')).write_text(json.dumps(rel,indent=2)+'\n',encoding='utf-8')
    print('Juntas',rel['juntas_fora_dos_volumes_max'],'apoio cauda',rel['erro_apoio_cauda_max'],'fase aérea',rel['fase_aerea_completa'])
    print('Altura peito',rel['altura_peito_base'],'erro impacto',rel['erro_altura_impacto_max'],'avanço',rel['avanco_durante_voo'])
    print('Chão',rel['minimo_y_visivel'],'pena/perna',rel['nova_penetracao_pena_perna'])
    folha(m,fn,pasta,'poses-planejadas.png' if a.poses else 'poses-impulso.png')
    if not a.poses and not a.sem_gif:gif(m,fn,pasta)


if __name__=='__main__':main()
