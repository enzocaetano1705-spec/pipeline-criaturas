"""Corrida própria do F2 e família de transições com fase contínua.

As fontes manuais e os clipes aprovados permanecem intactos. Escrita pelo motor.
"""
import argparse
import copy
import importlib.util
import json
import math
import shutil
from pathlib import Path

import numpy as np
from criaturas import bbmodelo, motor

RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ataque_v9', RAIZ/'scripts/animar-ritmo-cauda-pavao-f2-v9.py')
v9 = importlib.util.module_from_spec(spec); spec.loader.exec_module(v9)
v4 = v9.v5.v4
FONTE = v9.SAIDA
PASTA = FONTE.parent.parent/'corrida-v1'
SAIDA = PASTA/'criatura-pavao-e2-corrida-v1.bbmodel'
PERIODO = .72
APOIO = .40
PASSADA = 12.8
WALK_DISTANCIA = 8/.6
RUN_DISTANCIA = PASSADA/APOIO
WALK_VELOCIDADE = WALK_DISTANCIA/1.2
RUN_VELOCIDADE = RUN_DISTANCIA/PERIODO
FPS = 120
CLIPES = {'run': PERIODO, 'run_start': .54, 'run_stop': .60,
          'walk_blend': 1.2, 'idle_blend': 2.4}


def suave(x):
    x = float(np.clip(x, 0, 1))
    return x*x*x*(10+x*(-15+6*x))


def leitor(m, nome):
    """Catmull-Rom uniforme das chaves numéricas existentes; sem alterar a fonte."""
    a = next(a for a in m.animacoes if a['name'] == nome)
    nomes = {b.uuid: n for n, b in m.ossos.items()}; trilhas = {}
    for uid, b in a['animators'].items():
        for k in b.get('keyframes', []):
            assert len(k['data_points']) == 1 and k['interpolation'] in ['linear', 'catmullrom']
            v = [float(k['data_points'][0][q]) for q in ['x', 'y', 'z']]
            trilhas.setdefault((nomes[uid], k['channel']), []).append((float(k['time']), np.array(v), k['interpolation']))
    trilhas = {k: sorted(v, key=lambda x:x[0]) for k,v in trilhas.items()}
    def pose(t):
        p = {n: {'rotacao': np.zeros(3)} for n in m.ossos}
        p['body']['posicao'] = np.zeros(3)
        for (n,c), keys in trilhas.items():
            tt = [k[0] for k in keys]; i = max(0, min(len(keys)-2, int(np.searchsorted(tt,t,side='right'))-1))
            if len(keys) == 1 or t <= tt[0]: v = keys[0][1]
            elif t >= tt[-1]: v = keys[-1][1]
            else:
                u = (t-tt[i])/(tt[i+1]-tt[i]); b,c1 = keys[i][1],keys[i+1][1]
                if keys[i][2] == 'linear': v = b+(c1-b)*u
                else:
                    a0,d = keys[max(0,i-1)][1],keys[min(len(keys)-1,i+2)][1]
                    v = .5*((2*b)+(-a0+c1)*u+(2*a0-5*b+4*c1-d)*u*u+(-a0+3*b-3*c1+d)*u*u*u)
            p[n][{'rotation':'rotacao','position':'posicao','scale':'escala'}[c]] = np.array(v)
        return p
    return pose


def misturar(m,a,b,w):
    """Mesmos pesos por osso; rotação pelo arco curto, posição linear."""
    p = {}
    for n in m.ossos:
        ra = bbmodelo.matriz_rotacao(a.get(n,{}).get('rotacao',[0,0,0]))
        rb = bbmodelo.matriz_rotacao(b.get(n,{}).get('rotacao',[0,0,0]))
        rr = ra if np.linalg.norm(ra-rb)<1e-8 else v4.misturar(ra,rb,w)
        p[n] = {'rotacao':v9.euler(rr)}
    p['body']['posicao'] = (1-w)*np.array(a['body'].get('posicao',[0,0,0]))+w*np.array(b['body'].get('posicao',[0,0,0]))
    return p


def alvo_pe(m,fase,lado):
    ph = (fase + (0 if lado=='left' else .5)) % 1
    centro = v4.centro_pe(m,lado)
    if ph < APOIO:
        q = ph/APOIO
        ang = -20*suave((q-.65)/.35)
        alvo = v4.apoio(m,lado,ang)
        alvo[2] += -PASSADA/2+PASSADA*q
    else:
        u = (ph-APOIO)/(1-APOIO)
        # Hermite: o pé continua recuando ao sair/entrar no apoio, sem quina no trajeto.
        tang = PASSADA/APOIO*(1-APOIO)
        z = (2*u**3-3*u*u+1)*PASSADA/2 + (u**3-2*u*u+u)*tang
        z += (-2*u**3+3*u*u)*(-PASSADA/2)+(u**3-u*u)*tang
        ang = -20*(1-suave(u/.18))+14*math.sin(math.pi*u)**2
        alvo = v4.apoio(m,lado,ang)
        alvo[2] += z
        alvo[1] += 4.2*math.sin(math.pi*u)**2
    # Trilhos paralelos; mantém a largura natural, sem cruzar os pés.
    alvo[0] = np.copysign(5.4,centro[0])
    alvo[2] += .5 if lado=='left' else -.5
    return alvo,ang,ph<APOIO


def corrida(m,fase):
    fase %= 1
    a = 2*math.pi*fase; batida = math.cos(2*a-.8*math.pi)
    p = {n:{'rotacao':[0,0,0]} for n in m.ossos}
    p['body'] = {'rotacao':[-18+1.5*batida,1.6*math.sin(a),1.2*math.sin(a)],
                 'posicao':[.18*math.sin(a),-1.0-1.1*batida,0]}
    p['pelvis']['rotacao'] = [-4,1.8*math.sin(a-.3),0]
    p['waist']['rotacao'] = [-7,-1.2*math.sin(a-.2),-.5*math.sin(a)]
    p['chest']['rotacao'] = [-6-1.0*batida,-1.6*math.sin(a-.2),-.5*math.sin(a)]
    # Pescoço projetado e cabeça estabilizada, sem bicar a cada passada.
    p['neck_1']['rotacao'] = [24+.7*batida,.4*math.sin(a),0]
    p['head']['rotacao'] = [11-.9*batida,-math.sin(a),-.2*math.sin(a)]
    p['tail_1']['rotacao'] = [10-1.1*batida,-2.8*math.sin(a-.55),-.8*math.sin(a-.4)]
    p['tail_2']['rotacao'] = [.7*math.sin(2*a-.7),-1.1*math.sin(a-.8),0]
    for lado,s in [('left',1),('right',-1)]:
        p['arm_'+lado]['rotacao'] = [10+2.0*s*math.sin(a-.2),0,s*8]
        p['forearm_'+lado]['rotacao'] = [-18-1.3*s*math.sin(a-.5),0,0]
        # Longas lâminas ficam rígidas nos antebraços, todas herdando os pais corretos.
        p['wing_'+lado]['rotacao'] = [0,0,s*2]
    v4.alinhar_penas_pernas(m,p,1.25)
    for lado in ['left','right']:
        for i,ang in enumerate([-5,-10,-15],1):
            p[f'ankle_blade_{lado}_{i}']['rotacao'][0]=ang
    parent = bbmodelo.matrizes_ossos(m,p)['waist']; r = parent[:3,:3]; o = m.ossos['body'].origem
    for lado in ['left','right']:
        alvo,ang,_ = alvo_pe(m,fase,lado)
        rs = v4.perna(m,lado,v9.euler(r),parent[:3,3]-o+r@o,alvo,ang)
        for n,rr in zip(['leg_','shin_','foot_'],rs): p[n+lado]['rotacao'] = rr
    return p


class Familia:
    def __init__(self,m):
        self.m=m; self.walk_original=leitor(m,'walk'); self.idle_original=leitor(m,'idle')

    def suporte(self,p):
        mats=bbmodelo.matrizes_ossos(self.m,p)
        partes=[c for c in self.m.cubos if c.nome.startswith(('toe_','tarsus_'))]
        return min(float(bbmodelo.caixa_mundo(self.m,c,mats)[0][1]) for c in partes)

    def walk(self,t):
        p=self.walk_original(t)
        v4.alinhar_penas_pernas(self.m,p,1.25)
        for lado in ['left','right']:
            for i,ang in enumerate([-5,-10,-15],1):p[f'ankle_blade_{lado}_{i}']['rotacao'][0]=ang
        # Corrige o pequeno afundamento que já existia no walk, apenas no alias novo.
        p['body']['posicao'][1]+=max(0,v4.CHAO-self.suporte(p))
        return p

    def idle(self,t):
        p=self.idle_original(t)
        for b in p.values(): b.pop('escala',None) # escala de osso não existe no Roblox
        p['body']['posicao'][1]+=max(0,v4.CHAO-self.suporte(p))
        return p

    def blend(self,fase,w):
        p=misturar(self.m,self.walk((fase%1)*1.2),corrida(self.m,fase),w)
        p['body']['posicao'][1]+=max(0,v4.CHAO-self.suporte(p))
        return p

    def transicao(self,nome,t):
        d=CLIPES[nome];u=float(np.clip(t/d,0,1));w=suave(u)
        if nome=='run_stop': w=1-w
        # Integral analítica da frequência; a fase nunca volta ao zero na troca.
        integ=u**6-3*u**5+2.5*u**4
        f0,f1=(1/1.2,1/PERIODO) if nome=='run_start' else (1/PERIODO,1/1.2)
        fase=d*(f0*u+(f1-f0)*integ)
        return self.blend(fase,w)

    def pose(self,nome,t):
        if nome=='run': return corrida(self.m,t/PERIODO)
        if nome=='walk_blend': return self.walk(t)
        if nome=='idle_blend': return self.idle(t)
        return self.transicao(nome,t)


def operacoes(m,f):
    ops=[]
    for nome,d in CLIPES.items():
        ops.append({'op':'add_animation','name':nome,'length':d,'loop':'once' if nome in ['run_start','run_stop'] else 'loop','snapping':FPS})
        taxa=240 if nome=='run' else FPS
        tt=np.linspace(0,d,int(math.ceil(d*taxa))+1); pp=[f.pose(nome,float(t)) for t in tt]
        for n in m.ossos:
            # Até os canais neutros entram: o Animator precisa de contribuições em ambos os loops.
            for canal,campo in [('rotation','rotacao'),('position','posicao')]:
                if campo=='posicao' and n!='body': continue
                vv=np.array([p.get(n,{}).get(campo,[0,0,0]) for p in pp],float)
                if canal=='rotation': vv=v4.continuidade(vv)
                # Canais constantes precisam só de duas chaves.
                ids=[0,len(tt)-1] if np.max(np.ptp(vv,axis=0))<1e-8 else range(len(tt))
                for i in ids: ops.append({'op':'set_keyframe','animation':nome,'bone':n,'channel':canal,'time':round(float(tt[i]),6),'value':vv[i].round(6).tolist(),'interpolation':'linear'})
    return ops


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--refazer',action='store_true');ap.add_argument('--bloqueio',action='store_true');args=ap.parse_args()
    m=bbmodelo.ler(FONTE);f=Familia(m);PASTA.mkdir(exist_ok=True)
    # Verifica alcance antes de iniciar a gravação em lotes.
    for fase in np.linspace(0,1,241): corrida(m,float(fase))
    if args.bloqueio:
        spec=importlib.util.spec_from_file_location('previa_corrida',RAIZ/'scripts/revisar-bote-pavao-f2-v3.py')
        pv=importlib.util.module_from_spec(spec);spec.loader.exec_module(pv)
        from PIL import Image
        fn=lambda t:corrida(m,t/PERIODO)
        proj=pv.projetor(m,fn,np.linspace(0,PERIODO,37),'lado',256,275)
        im=Image.new('RGB',(768,604),'white')
        for i,t in enumerate([0,.10,.20,.30,.40,.50]): im.paste(pv.quadro(m,fn,t,proj,'corrida'),(i%3*256,i//3*302))
        im.save(PASTA/'poses-corrida.png');print('Bloqueio/alcance prontos.');return
    sha=v9.sha;original=sha(FONTE);prov=PASTA/'proveniencia.json'
    if SAIDA.exists():
        velho=json.loads(prov.read_text()) if prov.exists() else {}
        if not args.refazer or velho.get('saida_sha256')!=sha(SAIDA) or velho.get('fonte_sha256')!=original: raise SystemExit('Saída existente/editada preservada; criar outra versão.')
    ops=operacoes(m,f)
    (PASTA/'corrida.ops.json').write_text(json.dumps(ops,separators=(',',':'))+'\n',encoding='utf-8')
    shutil.copy2(FONTE,SAIDA);motor.editar(SAIDA,ops);novo=bbmodelo.ler(SAIDA)
    for campo in ['elements','textures','groups','outliner']: assert novo.bruto[campo]==m.bruto[campo],campo
    for a in m.animacoes:
        b=copy.deepcopy(a)
        for c in b.get('animators',{}).values(): c.setdefault('keyframes',[])
        assert b==next(c for c in novo.animacoes if c['uuid']==a['uuid'])
    assert sha(FONTE)==original
    prov.write_text(json.dumps({'fonte':FONTE.relative_to(RAIZ).as_posix(),'fonte_sha256':original,'saida_sha256':sha(SAIDA),'operacoes':len(ops),'clipes':CLIPES,'rig_geometria_uv_atlas_preservados':True},indent=2)+'\n',encoding='utf-8')
    shutil.copy2(FONTE.parent/'animacoes.json',PASTA/'animacoes.json')
    dados={'versao':1,'ciclo_run_s':PERIODO,'ciclo_walk_s':1.2,'velocidade_walk_unidades_s':WALK_VELOCIDADE,'velocidade_run_unidades_s':RUN_VELOCIDADE,'distancia_ciclo_walk':WALK_DISTANCIA,'distancia_ciclo_run':RUN_DISTANCIA,'apoio_run':APOIO,
           'run_start':{'duracao':.54,'fase_inicial':0,'fase_final':.54*(1/1.2+1/PERIODO)/2,'loop_destino':'run','tempo_loop_destino_s':.432},'run_stop':{'duracao':.60,'fase_inicial':0,'fase_final':.60*(1/1.2+1/PERIODO)/2,'loop_destino':'walk_blend','tempo_loop_destino_s':.8},'loops_compativeis_mistura':['idle_blend','walk_blend','run'],'transicoes_walk_run':['run_start','run_stop'],'integracao_no_jogo':'futura; esta entrega contém apenas animações e metadados'}
    (PASTA/'locomocao.json').write_text(json.dumps(dados,indent=2)+'\n',encoding='utf-8')
    print('Corrida e transições criadas:',len(ops),'operações;',len(novo.animacoes),'clipes; fonte preservada.')


if __name__=='__main__': main()
