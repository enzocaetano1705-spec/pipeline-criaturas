"""Revisa o bote F2 v3; --poses mostra o bloqueio antes de assar o arquivo."""
import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from criaturas import bbmodelo, render

RAIZ=Path(__file__).resolve().parents[1]


def carregar(nome,arquivo):
    s=importlib.util.spec_from_file_location(nome,RAIZ/'scripts'/arquivo)
    mod=importlib.util.module_from_spec(s);s.loader.exec_module(mod);return mod


def projetor(m,pose,tempos,vista,w=384,h=320):
    f,r,u=render.camera(*render.VISTAS[vista]);pts=[]
    for t in tempos:
        mats=bbmodelo.matrizes_ossos(m,pose(float(t)))
        pts.extend(bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mats),bbmodelo.cantos(c)) for c in m.cubos)
    pts=np.concatenate(pts);dx=pts@r;dy=pts@u
    esc=min((w-32)/(dx.max()-dx.min()),(h-35)/(dy.max()-dy.min()))
    return render.Projecao(r,u,f,esc,float(dx.min()),float(dy.max()),16,(w,h))


def quadro(m,pose,t,proj,titulo):
    mats=bbmodelo.matrizes_ossos(m,pose(float(t)))
    im,mask,_,_=render.renderizar(m,mats=mats,projecao=proj,fundo=(246,248,251))
    # Piso e marca central são referências de contato, sem introduzir peças no modelo.
    piso=Image.new('RGB',im.size,(246,248,251));d=ImageDraw.Draw(piso)
    for z in [-16,0,16,32]:
        p=proj.pixel([[-14,.08741,z],[14,.08741,z]])
        d.line([tuple(v) for v in p],fill=(211,219,226),width=1)
    for x in [-8,0,8]:
        p=proj.pixel([[x,.08741,-22],[x,.08741,35]])
        d.line([tuple(v) for v in p],fill=(211,219,226),width=1)
    piso.paste(im,(0,0),Image.fromarray((mask*255).astype('uint8')))
    cel=Image.new('RGB',(im.width,im.height+27),(246,248,251));cel.paste(piso,(0,27))
    ImageDraw.Draw(cel).text((8,8),f'{titulo} | {t:.3f}s',fill=(25,35,40))
    return cel


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--poses',action='store_true')
    args=parser.parse_args();criador=carregar('bote_v3','animar-bote-pavao-f2-v3.py')
    pasta=criador.PASTA;pasta.mkdir(exist_ok=True)
    if args.poses:
        m=bbmodelo.ler(criador.FONTE);criador.preparar_rig(m);pose=lambda t:criador.pose(m,t)
        folha=Image.new('RGB',(768,600),(246,248,251))
        for j,vista in enumerate(['3/4','lado']):
            proj=projetor(m,pose,np.linspace(0,1.2,37),vista,256,270)
            for i,(t,n) in enumerate([(.24,'comprime'),(.56,'contato baixo'),(.84,'absorve pouso')]):
                folha.paste(quadro(m,pose,t,proj,n),(i*256,j*300))
        folha.save(pasta/'poses-bloqueio.png');print('Bloqueio: poses-bloqueio.png (768x600).');return
    anterior=carregar('revisao_v2','revisar-ataque-pavao-f2-v2.py')
    m=bbmodelo.ler(criador.SAIDA);a=next(a for a in m.animacoes if a['name']==criador.NOME)
    pose,trilhas=anterior.leitor(m,a)
    minimo=(float('inf'),None,None);apoio=[];trajeto=[];penas=[];alturas=[];contatos=[];giro_max=0.;frente=[]
    alvo=([-2,.08741,-14],[2,3.08741,-7])
    for t in np.linspace(0,criador.DURACAO,289):
        t=float(t);p=pose(t);mats=bbmodelo.matrizes_ossos(m,p)
        frente.append(float(mats['body'][2,2]))
        for c in m.cubos:
            y=float(bbmodelo.caixa_mundo(m,c,mats)[0][1])
            if y<minimo[0]:minimo=(y,t,c.nome)
        arma=[];baixos=[]
        for lado in ['left','right']:
            toe=m.cubo('toe_'+lado+'_1');centro=(toe.de+toe.ate)/2
            atual=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,toe,mats),[centro])[0]
            esperado,_,plantado=criador.alvo_pe(m,t,lado)
            e=float(np.linalg.norm(atual-esperado));trajeto.append(e)
            if plantado:apoio.append(e)
            w=m.ossos['wing_'+lado];f=m.ossos['forearm_'+lado]
            penas.append(float(np.linalg.norm(bbmodelo.aplicar(mats[w.nome],[w.origem])[0]-bbmodelo.aplicar(mats[f.nome],[f.origem])[0])))
            dedos=[c for c in m.cubos if c.osso=='foot_'+lado];arma.extend(dedos)
            baixos.append(min(float(bbmodelo.caixa_mundo(m,c,mats)[0][1]) for c in dedos))
        alturas.append((t,*baixos))
        if .50<=t<=.68:
            lados=[lado for lado in ['left','right'] if any(anterior.sobrepoe(m,c,mats,alvo) for c in arma if c.osso=='foot_'+lado)]
            if lados:contatos.append((round(t,6),lados))
    for n,canais in trilhas.items():
        for canal,vals in canais.items():
            vv=np.array([v for _,v in vals])
            if canal=='rotation':giro_max=max(giro_max,float(np.max(abs(np.diff(vv,axis=0)))))
            np.testing.assert_allclose(vv[0],0,atol=1e-6);np.testing.assert_allclose(vv[-1],0,atol=1e-6)
    ambos=[r for r in contatos if len(r[1])==2]
    voo=[t for t,esq,di in alturas if min(esq,di)>.3]
    assert ambos,'as duas patas precisam encontrar o alvo pequeno na mesma fase'
    assert voo,'o salto precisa ter fase aérea nas duas patas'
    assert max(apoio)<.04 and max(trajeto)<.3
    assert minimo[0]>=.08741-.02 and max(penas)<1e-6
    assert giro_max<25,'descontinuidade de Euler entre chaves'
    assert min(frente)>.75,'a frente do corpo inverteu ou girou além do bote proposto'
    assert all('scale' not in canais for canais in trilhas.values())
    medidas={'fps_medicao':240,'duracao':a['length'],'loop':a['loop'],'minimo_y':minimo,
        'erro_apoio_max':max(apoio),'erro_trajeto_max':max(trajeto),'pena_cotovelo_max':max(penas),
        'maior_variacao_euler_por_chave':giro_max,'alinhamento_frente_min':min(frente),
        'inicio_fim_neutros':True,'sem_escala':True,
        'fase_aerea':{'inicio':min(voo),'fim':max(voo)},'caixa_alvo_pequeno':alvo,
        'contatos_ambas_patas':{'inicio':ambos[0][0],'fim':ambos[-1][0],'amostras':len(ambos)},
        'observacao':'Ensaio geométrico de animação; sem física, dano, deslocamento ou captura de inimigo no jogo.'}
    (pasta/'medidas-bote.json').write_text(json.dumps(medidas,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Medição: apoio',round(max(apoio),6),'chão',round(minimo[0],6),'trajeto livre',round(max(trajeto),6))
    print('Patas simultâneas no alvo:',ambos[0][0],'a',ambos[-1][0],'; voo:',round(min(voo),3),'a',round(max(voo),3))
    tempos=np.arange(60)/50;frames=[]
    for vista in ['3/4','lado']:
        proj=projetor(m,pose,tempos,vista,384,320)
        lista=[]
        for t in tempos:
            fase='mira' if t<.12 else 'comprime' if t<.28 else 'impulso' if t<.38 else 'bote' if t<.60 else 'recolhe' if t<.8 else 'pouso' if t<.96 else 'acomoda'
            lista.append(quadro(m,pose,float(t),proj,vista+' - '+fase))
        frames.append(lista)
    gif=[]
    for esq,di in zip(*frames):
        im=Image.new('RGB',(768,347));im.paste(esq,(0,0));im.paste(di,(384,0));gif.append(im)
    gif[0].save(pasta/'previa-bote.gif',save_all=True,append_images=gif[1:],duration=20,loop=0)
    folha=Image.new('RGB',(768,600),(246,248,251))
    for i,t in enumerate([0,.24,.44,.59,.84,1.2]):
        proj=projetor(m,pose,tempos,'3/4',256,270)
        folha.paste(quadro(m,pose,t,proj,'bote'),(i%3*256,i//3*300))
    folha.save(pasta/'poses-bote.png')
    print('Prévia 768x347, 50 fps, velocidade 1x; folha 768x600.')


if __name__=='__main__':main()
