"""Confere os clipes salvos, apoios, fases arbitrárias e interrupções; gera prévias."""
import argparse
import copy
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
g=carregar('corrida_f2','animar-corrida-pavao-f2.py')
r4=carregar('revisor_combate_v4','revisar-combate-pavao-f2-v4.py')
pv=r4.previa


class Salvo:
    def __init__(self,m):
        self.m=m
        self.fn={n:g.v9.v5.leitor_linear(m,n) for n in g.CLIPES}

    def raw(self,phase,w):
        return g.misturar(self.m,self.fn['walk_blend']((phase%1)*1.2),self.fn['run']((phase%1)*g.PERIODO),w)

    def lift(self,p):
        mats=bbmodelo.matrizes_ossos(self.m,p)
        bottom=min(bbmodelo.caixa_mundo(self.m,c,mats)[0][1] for c in self.m.cubos if c.nome.startswith(('toe_','tarsus_')))
        return max(0,float(g.v4.CHAO-bottom))

    def blend(self,phase,w):
        p=self.raw(phase,w)
        p['body']['posicao']=np.array(p['body']['posicao'])+[0,self.lift(p),0]
        return p


def preservar(m):
    src=bbmodelo.ler(g.FONTE)
    for field in ['elements','textures','groups','outliner']: assert m.bruto[field]==src.bruto[field],field
    for a in src.animacoes:
        b=copy.deepcopy(a)
        for v in b['animators'].values():v.setdefault('keyframes',[])
        assert b==next(v for v in m.animacoes if v['uuid']==a['uuid']),a['name']
    return [a['name'] for a in src.animacoes]


def conferir(m,s):
    rel={'fonte_sha256':g.v9.sha(g.SAIDA),'preservados':preservar(m),'clipes':{},'fase_compartilhada':True}
    for nome,d in g.CLIPES.items():
        fn=s.fn[nome]
        a=next(a for a in m.animacoes if a['name']==nome)
        assert len(a['animators'])==len(m.ossos)
        for v in a['animators'].values():
            assert all(k['channel']!='scale' for k in v['keyframes'])
        medidas=r4.medir(m,fn,d,240)
        assert medidas['minimo_y_visivel'][0]>=g.v4.CHAO-.025,(nome,medidas)
        assert medidas['nova_penetracao_pena_perna'][0]<.05,(nome,medidas)
        if nome in ['run','walk_blend','idle_blend']:
            p0,p1=fn(0),fn(d)
            for n in m.ossos:np.testing.assert_allclose(p0[n]['rotacao'],p1[n]['rotacao'],atol=1e-5)
            np.testing.assert_allclose(p0['body']['posicao'],p1['body']['posicao'],atol=1e-5)
        rel['clipes'][nome]=medidas
    # Pés em apoio não patinam se a raiz avança na velocidade medida da passada.
    erros=[];patinagem=[];voos=[]
    for side in ['left','right']:
        last=None
        for phase in np.linspace(0,1,481):
            p=s.fn['run'](float(phase)*g.PERIODO);mats=bbmodelo.matrizes_ossos(m,p)
            c=m.cubo('toe_'+side+'_1');actual=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mats),[(c.de+c.ate)/2])[0]
            expected,ang,contact=g.alvo_pe(m,float(phase),side)
            erros.append(float(np.linalg.norm(actual-expected)))
            if contact:
                # A ponta frontal, não o centro do pé que rola no impulso.
                tip=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mats),[[expected[0],c.de[1],c.de[2]]])[0]
                tip[2]-=g.RUN_DISTANCIA*phase
                if last is not None:patinagem.append(float(np.linalg.norm(tip-last)))
                last=tip
            else:last=None
    for phase in np.linspace(0,1,481):
        mat=bbmodelo.matrizes_ossos(m,s.fn['run'](float(phase)*g.PERIODO))
        yy=[min(bbmodelo.caixa_mundo(m,c,mat)[0][1] for c in m.cubos if c.osso=='foot_'+side) for side in ['left','right']]
        if min(yy)>g.v4.CHAO+.15:voos.append(float(phase))
    # 0,04 unidade < 0,3% do comprimento da perna; apoio tem gate próprio mais estrito.
    assert max(erros)<.04 and max(patinagem)<.03 and voos,(max(erros),max(patinagem),voos)
    rel.update(erro_trajetoria_pes_max=max(erros),deriva_apoio_por_amostra_max=max(patinagem),fases_aereas=voos)
    # Entradas e saídas têm poses iguais aos loops na fase indicada, não ao frame zero.
    for n,w0,w1 in [('run_start',0,1),('run_stop',1,0)]:
        phase=g.CLIPES[n]*(1/1.2+1/g.PERIODO)/2
        for t,p in [(0,s.blend(0,w0)),(g.CLIPES[n],s.blend(phase,w1))]:
            a=bbmodelo.matrizes_ossos(m,s.fn[n](t));b=bbmodelo.matrizes_ossos(m,p)
            assert max(np.max(abs(a[k]-b[k])) for k in a)<.003,(n,t)
    # Interromper em qualquer fase/peso não troca o apoio nem reinicia o ciclo.
    pior=(0,None);piso=100
    for w in np.linspace(0,1,9):
        med=r4.medir(m,lambda t:s.blend(t,float(w)),1,120)
        if med['nova_penetracao_pena_perna'][0]>pior[0]:pior=(med['nova_penetracao_pena_perna'][0],float(w))
        piso=min(piso,med['minimo_y_visivel'][0])
    assert pior[0]<.05 and piso>=g.v4.CHAO-.025,(pior,piso)
    rel['misturas_arbitrarias']={'penetracao_max':pior,'piso':piso,'fases':121,'pesos':9,
       'compensacao_vertical_de_referencia':True,'validacao_offline_sem_integracao_no_jogo':True}
    return rel


def imagens(m,s):
    fn=s.fn['run'];tt=np.arange(0,g.PERIODO,.02)
    projs=[pv.projetor(m,fn,tt,v,384,300) for v in ['3/4','lado']];frames=[]
    for t in tt:
        im=Image.new('RGB',(768,327),'white')
        for i,p in enumerate(projs):im.paste(pv.quadro(m,fn,t,p,'run 1x'),(i*384,0))
        frames.append(im)
    frames[0].save(g.PASTA/'previa-corrida.gif',save_all=True,append_images=frames[1:],duration=20,loop=0)
    # Walk → partida → run → frenagem → walk; os loops usam a fase de saída.
    a,b,d,e=.6,.54,.60,1.0
    phase1=b*(1/1.2+1/g.PERIODO)/2;phase2=d*(1/1.2+1/g.PERIODO)/2
    c=(3-phase1)*g.PERIODO # termina o run na fase exata de entrada do run_stop salvo
    total=a+b+c+d+e
    def demo(t):
        if t<a:return s.fn['walk_blend'](((t-a)/1.2)%1*1.2)
        if t<a+b:return s.fn['run_start'](t-a)
        if t<a+b+c:return s.fn['run'](((t-a-b)/g.PERIODO+phase1)%1*g.PERIODO)
        if t<a+b+c+d:return s.fn['run_stop'](t-a-b-c)
        phase=phase2+(t-a-b-c-d)/1.2
        return s.fn['walk_blend']((phase%1)*1.2)
    tempos=np.arange(0,total,.02);proj=pv.projetor(m,demo,tempos,'lado',768,345);frames=[]
    for t in tempos:
        label='walk' if t<a else 'partida' if t<a+b else 'run' if t<a+b+c else 'frenagem' if t<a+b+c+d else 'walk'
        frames.append(pv.quadro(m,demo,t,proj,label+' 1x'))
    durations=[20]*len(frames);durations[-1]=max(10,round((total-float(tempos[-1]))*100)*10)
    frames[0].save(g.PASTA/'previa-transicoes.gif',save_all=True,append_images=frames[1:],duration=durations,loop=0)
    # Uma folha por iteração, escala fixa entre postura de andar/correr.
    both=lambda t:s.fn['walk_blend'](0) if t<0 else fn(t)
    proj=pv.projetor(m,both,[-1,0,.12,.24,.36,.48],'lado',256,275)
    im=Image.new('RGB',(768,604),'white')
    for i,t in enumerate([-1,0,.12,.24,.36,.48]):im.paste(pv.quadro(m,both,t,proj,'walk' if t<0 else 'run'),(i%3*256,i//3*302))
    im.save(g.PASTA/'poses-corrida.png')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--sem-imagens',action='store_true');args=ap.parse_args()
    m=bbmodelo.ler(g.SAIDA);s=Salvo(m);rel=conferir(m,s)
    (g.PASTA/'medidas-corrida.json').write_text(json.dumps(rel,indent=2)+'\n',encoding='utf-8')
    print('Preservados:',', '.join(rel['preservados']))
    print('Pés: erro',rel['erro_trajetoria_pes_max'],'deriva/amostra',rel['deriva_apoio_por_amostra_max'])
    print('Misturas:',rel['misturas_arbitrarias'])
    if not args.sem_imagens:imagens(m,s);print('Prévias a 1× e folha de poses geradas.')


if __name__=='__main__':main()
