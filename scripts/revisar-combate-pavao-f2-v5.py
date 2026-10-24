"""Prévia e conferência da v5: spin articulado, cauda aberta e pisão protegido."""
import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image
from criaturas import bbmodelo

RAIZ=Path(__file__).resolve().parents[1]


def carregar(nome,arquivo):
    s=importlib.util.spec_from_file_location(nome,RAIZ/'scripts'/arquivo)
    mod=importlib.util.module_from_spec(s);s.loader.exec_module(mod);return mod


g=carregar('criador_v5','animar-combate-pavao-f2-v5.py')
r4=carregar('revisor_v4','revisar-combate-pavao-f2-v4.py')


def folha(m,poses,pasta,nome_saida='poses-combate.png'):
    im=Image.new('RGB',(768,720),(246,248,251))
    for j,(nome,vista,tempos) in enumerate([
        ('attack_spin','3/4',[.36,.64,1.02]),('attack_spin','lado',[.36,.64,1.02]),
        ('attack_tail_kick','lado',[.42,.72,.99])]):
        fn=poses[nome];proj=r4.previa.projetor(m,fn,np.linspace(0,g.CLIPES[nome],40),vista,256,210)
        for i,t in enumerate(tempos):im.paste(r4.previa.quadro(m,fn,t,proj,nome),(i*256,j*240))
    im.save(pasta/nome_saida)


def gifs(m,poses,pasta):
    conjunto=[]
    for nome,d in g.CLIPES.items():
        fn=poses[nome];tt=np.arange(0,d,.02)
        proj=[r4.previa.projetor(m,fn,tt,v,384,300) for v in ['3/4','lado']]
        frames=[]
        for t in list(tt)+[d]*15:
            im=Image.new('RGB',(768,327),(246,248,251))
            for i,p in enumerate(proj):im.paste(r4.previa.quadro(m,fn,t,p,nome),(i*384,0))
            frames.append(im)
        frames[0].save(pasta/(nome+'.gif'),save_all=True,append_images=frames[1:],duration=20,loop=0)
        conjunto.extend(frames)
    conjunto[0].save(pasta/'previa-combate.gif',save_all=True,append_images=conjunto[1:],duration=20,loop=0)


def conferir(m,nome,fn,dur):
    repouso=bbmodelo.matrizes_ossos(m);raizes=[];solo=[];laminas=[];cauda=[];solas=[];abertura=[];voo=[];ponta=[]
    fans=[c for c in m.cubos if c.osso.startswith('tail_blade_')]
    ns=[bbmodelo.matriz_cubo(m,c,repouso)[:3,0] for c in fans]
    baseline=np.array(ns)@np.array(ns).T
    for t in np.linspace(0,dur,int(round(dur*240))+1):
        t=float(t);p=fn(t);mat=bbmodelo.matrizes_ossos(m,p)
        for c in m.cubos:
            if c.osso.startswith(('tail_blade_','ankle_blade_','elbow_blade_')):
                b=m.ossos[c.osso];a=bbmodelo.aplicar(mat[b.nome],[b.origem])[0];q=bbmodelo.aplicar(mat[b.pai],[b.origem])[0]
                raizes.append(float(np.linalg.norm(a-q)))
        for lado in ['left','right']:
            y=min(float(bbmodelo.caixa_mundo(m,c,mat)[0][1]) for c in m.cubos if c.osso=='foot_'+lado)
            if nome=='attack_spin' and lado=='left':
                solo.append(abs(y-g.CHAO));c=m.cubo('toe_left_1')
                apoio=np.array([(c.de[0]+c.ate[0])/2,c.de[1],c.de[2]])
                q=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mat),[apoio])[0]
                ponta.append(float(np.linalg.norm(q[[0,2]]-apoio[[0,2]])))
            if nome=='attack_spin' and lado=='right' and .56<=t<=.80:voo.append(y)
            if nome=='attack_tail_kick' and .70<=t<=.75:solas.append(y)
        if nome=='attack_spin' and .46<=t<=.90:
            for c in m.cubos:
                if (c.nome.startswith('wing_') and c.tamanho[2]>24) or c.osso.startswith('tail_blade_'):
                    laminas.append(abs(float(bbmodelo.matriz_cubo(m,c,mat)[1,0])))
        if nome=='attack_tail_kick':
            norms=[bbmodelo.matriz_cubo(m,c,mat)[:3,0] for c in fans]
            abertura.append(float(abs(np.array(norms)@np.array(norms).T-baseline).max()))
            if .40<=t<=1.10:
                cmin=min(float(bbmodelo.caixa_mundo(m,m.cubo(n),mat)[0][1]) for n in ['tail_mid','tail_base'])
                cauda.append(abs(cmin-g.CHAO))
    for t in [0,dur]:
        mat=bbmodelo.matrizes_ossos(m,fn(t))
        for n in mat:np.testing.assert_allclose(mat[n],repouso[n],atol=2e-5)
    return {'fixacao_raizes_max':max(raizes),'apoio_pata_spin_erro':max(solo,default=0),
            'normal_laminas_spin_min':min(laminas,default=1),'apoio_solid_cauda_erro':max(cauda,default=0),
            'abertura_leque_diferenca_max':max(abertura,default=0),'solas_impacto_min_y':min(solas,default=None),
            'pata_direita_livre_min_y':min(voo,default=None),'ponta_apoio_deriva_xz_max':max(ponta,default=0),'inicio_fim_neutros':True}


def conferir_pisao(m):
    antes=bbmodelo.ler(g.FONTE);fn=g.leitor_linear(antes,'attack_stomp');depois=g.leitor_linear(m,'attack_stomp')
    porid={c.uuid:c for c in m.cubos};erro=(0,None,None)
    for t in np.linspace(0,1.25,301):
        aa=bbmodelo.matrizes_ossos(antes,fn(t));bb=bbmodelo.matrizes_ossos(m,depois(t))
        for c in antes.cubos:
            a=bbmodelo.aplicar(bbmodelo.matriz_cubo(antes,c,aa),bbmodelo.cantos(c))
            b=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,porid[c.uuid],bb),bbmodelo.cantos(c))
            e=float(np.linalg.norm(a-b,axis=1).max())
            if e>erro[0]:erro=(e,float(t),c.nome)
    assert erro[0]<.015
    return {'amostragem_hz':240,'erro_max_cantos':erro,'trajetorias_e_chaves_originais_preservadas':True,
            'observacao':'Compensação numérica só da pena direita 7, reparentada ao antebraço; demais peças idênticas.'}


def conferir_continuidade(m):
    res={}
    for a in m.animacoes:
        if a['name'] not in g.CLIPES:continue
        _,tr=r4.anterior.leitor(m,a);pior=(0,None)
        for n,ch in tr.items():
            assert 'scale' not in ch
            vv=np.array([v for _,v in ch['rotation']]);maximo=float(abs(np.diff(vv,axis=0)).max())
            if maximo>pior[0]:pior=(maximo,n)
        assert pior[0]<35,pior
        vv=np.array([v for _,v in tr['body']['position']]);passo=float(np.linalg.norm(np.diff(vv,axis=0),axis=1).max())
        assert passo<1
        res[a['name']]={'maior_variacao_euler_por_chave':pior,'maior_passo_bacia_por_chave':passo,'sem_escala':True,'loop':a['loop']}
    return res


def main():
    pa=argparse.ArgumentParser(description=__doc__);pa.add_argument('--poses',action='store_true');pa.add_argument('--sem-gifs',action='store_true');a=pa.parse_args()
    if a.poses:
        m=bbmodelo.ler(g.FONTE);g.preparar_rig(m);poses={n:lambda t,n=n:g.pose(m,n,t) for n in g.CLIPES}
    else:
        m=bbmodelo.ler(g.SAIDA);poses={n:r4.anterior.leitor(m,next(v for v in m.animacoes if v['name']==n))[0] for n in g.CLIPES}
    pasta=g.PASTA;pasta.mkdir(exist_ok=True)
    medidas={n:r4.medir(m,poses[n],d,60 if a.poses else 240) for n,d in g.CLIPES.items()}
    for n,d in g.CLIPES.items():
        medidas[n].update(conferir(m,n,poses[n],d))
        if not a.poses:
            r=medidas[n]
            assert r['minimo_y_visivel'][0]>g.CHAO-.025
            assert r['nova_penetracao_pena_perna'][0]<.05
            assert r['fixacao_raizes_max']<1e-6
            assert r['normal_laminas_spin_min']>.998
            assert r['apoio_pata_spin_erro']<.025
            assert r['apoio_solid_cauda_erro']<.025
            assert r['abertura_leque_diferenca_max']<1e-6
        print(n,json.dumps(medidas[n]))
    if not a.poses:
        (pasta/'pisao-preservado.json').write_text(json.dumps(conferir_pisao(m),indent=2)+'\n',encoding='utf-8')
        (pasta/'continuidade.json').write_text(json.dumps(conferir_continuidade(m),indent=2)+'\n',encoding='utf-8')
    (pasta/('medidas-planejadas-superficies.json' if a.poses else 'medidas-superficies.json')).write_text(json.dumps(medidas,indent=2)+'\n',encoding='utf-8')
    folha(m,poses,pasta,'poses-planejadas.png' if a.poses else 'poses-combate.png')
    if not a.poses and not a.sem_gifs:gifs(m,poses,pasta)


if __name__=='__main__':main()
