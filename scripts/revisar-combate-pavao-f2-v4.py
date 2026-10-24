"""Confere superfícies opacas, fixações e apoios dos três ataques F2 v4."""
import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from criaturas import bbmodelo, roblox_infra

RAIZ=Path(__file__).resolve().parents[1]


def carregar(nome,arquivo):
    s=importlib.util.spec_from_file_location(nome,RAIZ/'scripts'/arquivo)
    mod=importlib.util.module_from_spec(s);s.loader.exec_module(mod);return mod


criador=carregar('combate_v4','animar-combate-pavao-f2-v4.py')
previa=carregar('previa_v3','revisar-bote-pavao-f2-v3.py')
anterior=carregar('leitor_v2','revisar-ataque-pavao-f2-v2.py')


def amostras_opacas(m,c):
    return criador.superficie_opaca(m,c,False)


def profundidade(p,c):
    return np.maximum(0,np.minimum(p-c.de,c.ate-p).min(axis=1))


def medir(m,pose,dur,fps=120):
    resto=bbmodelo.matrizes_ossos(m)
    solidos=[c for c in m.cubos if np.all(c.tamanho>1e-5) and
             (c.nome.startswith(('leg_','shin_','tarsus_','toe_')) or c.nome=='hips')]
    penas=[c for c in m.cubos if c.nome.startswith('leg_') and '_feather_' in c.nome]
    pontos={c.uuid:amostras_opacas(m,c) for c in penas}
    superficie={c.uuid:criador.superficie_opaca(m,c) for c in m.cubos}
    pares={}
    for c in penas:
        mundo=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,resto),pontos[c.uuid])
        for s in solidos:
            p=bbmodelo.aplicar(np.linalg.inv(bbmodelo.matriz_cubo(m,s,resto)),mundo)
            pares[c.uuid,s.uuid]=profundidade(p,s)
    pior=(0,None,None,None);minimo=(100,None,None);min_opaco=(100,None,None);caixa_transparente=(100,None,None)
    for t in np.linspace(0,dur,int(round(dur*fps))+1):
        t=float(t);mats=bbmodelo.matrizes_ossos(m,pose(t))
        inversas={s.uuid:np.linalg.inv(bbmodelo.matriz_cubo(m,s,mats)) for s in solidos}
        for c in m.cubos:
            y=float(bbmodelo.caixa_mundo(m,c,mats)[0][1])
            if y<caixa_transparente[0]:caixa_transparente=(y,t,c.nome)
            y=float(bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mats),superficie[c.uuid])[:,1].min())
            if y<minimo[0]:minimo=(y,t,c.nome)
        for c in penas:
            mundo=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mats),pontos[c.uuid])
            y=float(mundo[:,1].min())
            if y<min_opaco[0]:min_opaco=(y,t,c.nome)
            for s in solidos:
                dep=profundidade(bbmodelo.aplicar(inversas[s.uuid],mundo),s)
                novo=float(np.maximum(0,dep-pares[c.uuid,s.uuid]).max())
                if novo>pior[0]:pior=(novo,t,c.nome,s.nome)
    return {'minimo_y_visivel':minimo,'minimo_penas_opacas_centros':min_opaco,
            'nova_penetracao_pena_perna':pior,'minimo_caixas_inclui_transparencia':caixa_transparente}


def folha(m,poses,pasta,nome_saida='poses-combate.png'):
    im=Image.new('RGB',(768,690),(246,248,251))
    dados=[('attack_stomp',[.425,.575,.90]),('attack_spin',[.40,.60,.76]),('attack_tail_kick',[.36,.60,.94])]
    for j,(nome,tempos) in enumerate(dados):
        fn=poses[nome];proj=previa.projetor(m,fn,np.linspace(0,criador.CLIPES[nome],30),'3/4',256,200)
        for i,t in enumerate(tempos):im.paste(previa.quadro(m,fn,t,proj,nome),(i*256,j*230))
    im.save(pasta/nome_saida)


def conferir_movimento(m,nome,pose,dur):
    repouso=bbmodelo.matrizes_ossos(m);fixacoes=[];trajetos=[];contato=[];planos=[];apoios=[];solas=[]
    for t in np.linspace(0,dur,int(round(dur*240))+1):
        t=float(t);p=pose(t);mats=bbmodelo.matrizes_ossos(m,p)
        ideal=bbmodelo.matrizes_ossos(m,criador.pose(m,nome,t))
        for c in m.cubos:
            if c.osso and c.osso.startswith(('tail_blade_','ankle_blade_')):
                o=m.ossos[c.osso];raiz=o.origem
                atual=bbmodelo.aplicar(mats[o.nome],[raiz])[0]
                esperado=bbmodelo.aplicar(mats[o.pai],[raiz])[0]
                fixacoes.append(float(np.linalg.norm(atual-esperado)))
            if c.osso and c.osso.startswith('elbow_blades_'):
                base=criador.ponto_face(m,c);pai=m.ossos[c.osso].pai
                atual=bbmodelo.aplicar(mats[c.osso],[base])[0]
                esperado=bbmodelo.aplicar(mats[pai],[base])[0]
                fixacoes.append(float(np.linalg.norm(atual-esperado)))
        # União física da parte sólida da cauda ao quadril.
        raiz=criador.ponto_face(m,m.cubo('tail_mid'))
        fixacoes.append(float(np.linalg.norm(bbmodelo.aplicar(mats['tail_1'],[raiz])[0]-bbmodelo.aplicar(mats['body'],[raiz])[0])))
        for lado in ['left','right']:
            c=m.cubo('toe_'+lado+'_1');centro=(c.de+c.ate)/2
            atual=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mats),[centro])[0]
            alvo=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,ideal),[centro])[0]
            trajetos.append(float(np.linalg.norm(atual-alvo)))
            yy=min(float(bbmodelo.caixa_mundo(m,c,mats)[0][1]) for c in m.cubos if c.osso=='foot_'+lado)
            if nome=='attack_stomp' and ((lado=='right' and .18<=t<=.70) or (lado=='left' and .575<=t<=.90)):
                apoios.append(abs(yy-criador.CHAO))
            if nome=='attack_tail_kick' and .60<=t<=.66:solas.append(yy)
        if nome=='attack_tail_kick' and .34<=t<=.98:
            v=bbmodelo.aplicar(mats['tail_1'],[criador.contato_cauda(m)])[0]
            contato.append(float(np.linalg.norm(v-[0,criador.CHAO,25])))
        if nome=='attack_spin' and .46<=t<=.76:
            for c in m.cubos:
                if c.osso.startswith(('tail_blade_','elbow_blades_')):
                    normal=bbmodelo.matriz_cubo(m,c,mats)[:3,0]
                    planos.append(abs(float(normal[1])))
    for t in [0,dur]:
        p=pose(t);mats=bbmodelo.matrizes_ossos(m,p)
        for n in mats:np.testing.assert_allclose(mats[n],repouso[n],atol=2e-5)
    assert max(fixacoes)<1e-6
    assert max(trajetos)<.10
    if apoios:assert max(apoios)<.04
    if contato:assert max(contato)<.02
    if planos:assert min(planos)>.999
    if solas:assert min(solas)>10
    return {'inicio_fim_neutros_matrizes':True,'fixacao_raizes_max':max(fixacoes),
            'erro_trajeto_pe_max':max(trajetos),'erro_solo_patas_apoiadas_max':max(apoios,default=0),
            'erro_contato_cauda_max':max(contato,default=0),'normal_vertical_laminas_min':min(planos,default=1),
            'solas_no_impacto_y_min':min(solas,default=None)}


def conferir_chaves(m):
    saida={}
    for a in m.animacoes:
        if a['name'] not in criador.CLIPES:continue
        _,trilhas=anterior.leitor(m,a);maior=0
        for n,canais in trilhas.items():
            assert 'scale' not in canais
            vv=np.array([v for _,v in canais['rotation']])
            maior=max(maior,float(abs(np.diff(vv,axis=0)).max()))
        assert maior<25
        r={'maior_variacao_euler_por_chave':maior,'sem_escala':True,'loop':a['loop'],'duracao':a['length']}
        if a['name']=='attack_spin':
            vals=trilhas['combat_pivot']['rotation'];tt=np.array([t for t,_ in vals]);yaw=np.array([v[1] for _,v in vals])
            r.update(volta_de_graus=float(yaw[-1]-yaw[0]),giro_ativo_graus=float(np.interp(.76,tt,yaw)-np.interp(.46,tt,yaw)))
            assert abs(yaw[-1]-360)<1e-8
        saida[a['name']]=r
    return saida


def gifs(m,poses,pasta):
    conjunto=[]
    nomes={'attack_stomp':'PISAO - alvo baixo','attack_spin':'GIRO CORTANTE - area','attack_tail_kick':'APOIO NA CAUDA - alvo alto'}
    for nome,d in criador.CLIPES.items():
        fn=poses[nome];tempos=np.arange(0,d,.02)
        projs=[previa.projetor(m,fn,tempos,v,384,300) for v in ['3/4','lado']]
        frames=[]
        for t in tempos:
            im=Image.new('RGB',(768,327),(246,248,251))
            for i,proj in enumerate(projs):im.paste(previa.quadro(m,fn,t,proj,nomes[nome]),(i*384,0))
            frames.append(im)
        final=Image.new('RGB',(768,327),(246,248,251))
        for i,proj in enumerate(projs):final.paste(previa.quadro(m,fn,d,proj,nomes[nome]),(i*384,0))
        frames.extend([final]*15)
        frames[0].save(pasta/(nome+'.gif'),save_all=True,append_images=frames[1:],duration=20,loop=0)
        conjunto.extend(frames)
    conjunto[0].save(pasta/'previa-combate.gif',save_all=True,append_images=conjunto[1:],duration=20,loop=0)


def main():
    pa=argparse.ArgumentParser(description=__doc__);pa.add_argument('--poses',action='store_true')
    pa.add_argument('--medir',action='store_true');pa.add_argument('--so-previas',action='store_true');args=pa.parse_args()
    if args.poses or args.medir:
        m=bbmodelo.ler(criador.FONTE);criador.preparar_rig(m)
        poses={n:lambda t,n=n:criador.pose(m,n,t) for n in criador.CLIPES}
    else:
        m=bbmodelo.ler(criador.SAIDA)
        poses={n:anterior.leitor(m,next(a for a in m.animacoes if a['name']==n))[0] for n in criador.CLIPES}
    pasta=criador.PASTA;pasta.mkdir(exist_ok=True)
    if args.so_previas:
        gifs(m,poses,pasta);print('Prévia a 1x: 50 fps, pausas de 0,30 s entre golpes.');return
    medidas={n:medir(m,poses[n],d,60 if args.poses or args.medir else 240) for n,d in criador.CLIPES.items()}
    if not args.poses and not args.medir:
        (pasta/'medidas-continuidade.json').write_text(json.dumps(conferir_chaves(m),indent=2)+'\n',encoding='utf-8')
        for n,d in criador.CLIPES.items():
            r=medidas[n];r.update(conferir_movimento(m,n,poses[n],d))
            assert r['minimo_y_visivel'][0]>=criador.CHAO-.025
            assert r['nova_penetracao_pena_perna'][0]<.05
    nome_medidas='medidas-superficies-planejadas.json' if args.poses or args.medir else 'medidas-superficies.json'
    (pasta/nome_medidas).write_text(json.dumps(medidas,indent=2)+'\n',encoding='utf-8')
    for n,r in medidas.items():print(n,json.dumps(r))
    if not args.medir:folha(m,poses,pasta,'poses-planejadas.png' if args.poses else 'poses-combate.png')
    if not args.poses and not args.medir:gifs(m,poses,pasta)


if __name__=='__main__':main()
