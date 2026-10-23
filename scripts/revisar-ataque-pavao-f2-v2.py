"""Mede as chaves salvas e produz a prévia da família de ataques F2 v2."""
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from criaturas import bbmodelo, render

RAIZ=Path(__file__).resolve().parents[1]
PASTA=RAIZ/'modelos/criatura-pavao/f2/ataque-v2'
ARQUIVO=PASTA/'criatura-pavao-e2-ataque-v2.bbmodel'


def leitor(m,a):
    nomes={b.uuid:n for n,b in m.ossos.items()};trilhas={}
    for uid,animador in a['animators'].items():
        canais={}
        for k in animador.get('keyframes',[]):
            v=k['data_points'][0]
            assert k['interpolation']=='linear'
            canais.setdefault(k['channel'],[]).append((k['time'],[float(v[x]) for x in ['x','y','z']]))
        trilhas[nomes[uid]]={c:sorted(vals) for c,vals in canais.items()}
    def pose(t):
        p={}
        for osso,canais in trilhas.items():
            for canal,vals in canais.items():
                tt,vv=zip(*vals)
                v=np.array([np.interp(t,tt,[v[i] for v in vv]) for i in range(3)])
                p.setdefault(osso,{})[{'rotation':'rotacao','position':'posicao','scale':'escala'}[canal]]=v
        return p
    return pose,trilhas


def sobrepoe(m,c,mats,alvo):
    """SAT entre o cubo orientado e a caixa do alvo; também aceita planos."""
    mc=bbmodelo.matriz_cubo(m,c,mats);pw=bbmodelo.aplicar(mc,bbmodelo.cantos(c))
    lo,hi=np.array(alvo)
    pa=np.array([[x,y,z] for x in [lo[0],hi[0]] for y in [lo[1],hi[1]] for z in [lo[2],hi[2]]])
    e=np.eye(3);r=mc[:3,:3].T
    for eixo in [*e,*r,*[np.cross(a,b) for a in e for b in r]]:
        if np.linalg.norm(eixo)<1e-8:continue
        a,b=pw@eixo,pa@eixo
        if a.max()<b.min()-1e-8 or b.max()<a.min()-1e-8:return False
    return True


def main():
    spec=importlib.util.spec_from_file_location('criador_f2_v2',RAIZ/'scripts/animar-ataque-pavao-f2-v2.py')
    criador=importlib.util.module_from_spec(spec);spec.loader.exec_module(criador)
    m=bbmodelo.ler(ARQUIVO);original=bbmodelo.ler(criador.FONTE)
    anims={a['name']:a for a in m.animacoes if a['name'] in criador.CLIPES}
    leitores={n:leitor(m,a) for n,a in anims.items()};rel={};menores=[];maiores=[]
    chao=.08741
    alvos={'pequeno':([ -1.5,chao,-16],[1.5,chao+3,-10]),
           'medio':([-3,chao,-22],[3,chao+14,-16]),
           'grande':([-4,chao,-24],[4,chao+48,-20])}
    guarda=None
    for nome,a in anims.items():
        estilo,dur=criador.CLIPES[nome];pose,trilhas=leitores[nome]
        minimo=(float('inf'),None,None);apoios=[];erros=[];penas=[];envelope=[]
        contatos={n:[] for n in alvos}
        for t in np.linspace(0,dur,int(round(dur*240))+1):
            t=float(t);p=pose(t);mat=bbmodelo.matrizes_ossos(m,p)
            lo,hi=bbmodelo.limites(m,mat);menores.append(lo);maiores.append(hi)
            for c in m.cubos:
                v=float(bbmodelo.caixa_mundo(m,c,mat)[0][1])
                if v<minimo[0]:minimo=(v,t,c.nome)
            ideal=criador.pose(m,t,estilo,dur)
            idealmat=bbmodelo.matrizes_ossos(m,ideal)
            etapa=estilo;local=t
            if estilo=='chain':
                etapa,local=('left',t) if t<.4 else ('peck',t-.4) if t<.7 else ('right',t-.7)
            for lado in ['left','right']:
                toe=m.cubo('toe_'+lado+'_1');centro=(toe.de+toe.ate)/2
                atual=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,toe,mat),[centro])[0]
                esperado=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,toe,idealmat),[centro])[0]
                erro=float(np.linalg.norm(atual-esperado));erros.append(erro)
                if etapa=='peck' or lado!=etapa:apoios.append(erro)
                w=m.ossos['wing_'+lado];f=m.ossos['forearm_'+lado]
                penas.append(float(np.linalg.norm(bbmodelo.aplicar(mat[w.nome],[w.origem])[0]-bbmodelo.aplicar(mat[f.nome],[f.origem])[0])))
            ativo=(.07<=local<=.17) if etapa=='peck' else (.12<=local<=.26)
            arma=[c for c in m.cubos if c.nome in ['beak','beak_tip']] if etapa=='peck' else [c for c in m.cubos if c.nome.startswith('toe_'+etapa+'_')]
            if ativo:
                for c in arma:
                    envelope.extend([v.tolist() for v in bbmodelo.caixa_mundo(m,c,mat)])
                for n,alvo in alvos.items():
                    if any(sobrepoe(m,c,mat,alvo) for c in arma):contatos[n].append(round(t,6))
        inicio,fim=pose(0),pose(dur)
        for n in inicio:
            for c in inicio[n]:np.testing.assert_allclose(inicio[n][c],fim[n][c],atol=1e-6)
        if guarda is None:guarda=inicio
        else:
            for n in guarda:
                for c in guarda[n]:np.testing.assert_allclose(guarda[n][c],inicio[n][c],atol=1e-6)
        assert max(erros)<.35 and max(apoios)<.04,'desvio excessivo entre chaves'
        assert max(penas)<1e-6,'pena separada do cotovelo'
        assert minimo[0]>=chao-.02,'geometria abaixo do chão'
        assert all('scale' not in c for c in trilhas.values())
        rel[nome]={'duracao':dur,'loop':a['loop'],'amostras':int(round(dur*240))+1,
            'chaves':sum(len(v) for c in trilhas.values() for v in c.values()),'minimo_y':minimo,
            'erro_trajetoria_max':max(erros),'erro_apoio_max':max(apoios),'distancia_pena_cotovelo_max':max(penas),
            'inicio_igual_fim':True,'guarda_comum':True,'sem_escala':True,
            'arma_ativa_min':np.min(envelope,axis=0).tolist(),'arma_ativa_max':np.max(envelope,axis=0).tolist(),
            'contatos_alvos_geometricos':{n:({'primeiro':ts[0],'ultimo':ts[-1],'amostras':len(ts)} if ts else None) for n,ts in contatos.items()}}
        print(nome,'apoio',round(max(apoios),6),'chão',round(minimo[0],6),'alvos',[n for n,ts in contatos.items() if ts])
    for nome in ['attack_physical','attack_physical_right']:
        assert rel[nome]['contatos_alvos_geometricos']['pequeno']
        assert rel[nome]['contatos_alvos_geometricos']['medio']
    assert rel['attack_peck']['contatos_alvos_geometricos']['grande']
    for lado in ['left','right']:assert m.ossos['wing_'+lado].pai=='forearm_'+lado
    assert m.bruto['elements']==original.bruto['elements'] and m.bruto['textures']==original.bruto['textures']
    (PASTA/'medidas-ataque.json').write_text(json.dumps({'fps_medicao':240,'unidade':'Blockbench',
        'alvos_geometricos':alvos,'clipes':rel,'observacao':'Ensaio geométrico de alcance; sem física/dano/seleção de alvo do Roblox.'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # Enquadramento fixo por projeção dos vértices reais: evita espaço vazio da AABB diagonal.
    frames=[];pose=leitores['attack_chain_preview'][0];tempos=np.arange(55)/50
    for vista in ['3/4','lado']:
        f,r,u=render.camera(*render.VISTAS[vista]);pontos=[]
        for t in tempos:
            mats=bbmodelo.matrizes_ossos(m,pose(float(t)))
            pontos.extend(bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mats),bbmodelo.cantos(c)) for c in m.cubos)
        pontos=np.concatenate(pontos);dx=pontos@r;dy=pontos@u
        esc=min(356/(dx.max()-dx.min()),300/(dy.max()-dy.min()))
        proj=render.Projecao(r,u,f,esc,float(dx.min()),float(dy.max()),10,(376,324))
        quadros=[]
        for t in tempos:
            im,_,_,_=render.renderizar(m,vista,mats=bbmodelo.matrizes_ossos(m,pose(float(t))),projecao=proj,fundo=(248,249,252))
            cel=Image.new('RGB',(384,356),(248,249,252));cel.paste(im,(4,29))
            nome='chute esquerdo' if t<.4 else 'bicotada' if t<.7 else 'chute direito'
            ImageDraw.Draw(cel).text((8,8),f'{vista} | {t:.2f}s | {nome}',fill=(25,35,40));quadros.append(cel)
        frames.append(quadros)
    compostos=[]
    for a,b in zip(*frames):
        im=Image.new('RGB',(768,356),(248,249,252));im.paste(a,(0,0));im.paste(b,(384,0));compostos.append(im)
    compostos[0].save(PASTA/'previa-ataque.gif',save_all=True,append_images=compostos[1:],duration=20,loop=0)
    folha=Image.new('RGB',(768,540),(248,249,252))
    for i,t in enumerate([0,.144,.224,.514,.844,1.1]):
        im=frames[0][min(54,int(round(t*50)))].resize((256,237),Image.Resampling.NEAREST)
        folha.paste(im,(i%3*256,i//3*270+27))
        ImageDraw.Draw(folha).text((i%3*256+8,i//3*270+8),f'{t:.3f}s',fill=(25,35,40))
    folha.save(PASTA/'poses-ataque.png')
    print('Prévia 768x356, 50 fps, velocidade 1x, sem pausa extra; folha 768x540.')


if __name__=='__main__':main()
