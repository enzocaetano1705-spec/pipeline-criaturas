"""F2 v9: mantém a cauda v8, retoma o chute v7 e encurta o ataque para 2,15 s."""
import argparse
import copy
import importlib.util
import json
import shutil
from pathlib import Path

import numpy as np
from criaturas import bbmodelo,motor

RAIZ=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('gancho_v8',RAIZ/'scripts/animar-gancho-cauda-pavao-f2-v8.py')
v8=importlib.util.module_from_spec(s);s.loader.exec_module(v8)
v5=v8.v5
FONTE=v8.SAIDA
PASTA=FONTE.parent.parent/'ataque-v9'
SAIDA=PASTA/'criatura-pavao-e2-ataque-v9.bbmodel'
NOME=v8.NOME
DURACAO=2.15
CHAO=v8.CHAO
C=v8.C
sha=v8.sha
euler=v8.euler
ANTIGOS=np.array([0,.62,.82,1.17,1.70,2.85])
NOVOS=np.array([0,.50,.66,.96,1.30,2.15])
CARGA=.50
SAI=.66
POUSA=1.30
INICIO_CHUTE=float(np.interp(.79,ANTIGOS,NOVOS))
IMPACTO=float(np.interp(.94,ANTIGOS,NOVOS))
FIM_GOLPE=float(np.interp(1.17,ANTIGOS,NOVOS))
TRONCO=['chest','neck_1','head','arm_left','arm_right','forearm_left','forearm_right']
PERNAS=[a+b for a in ['leg_','shin_','foot_'] for b in ['left','right']]


def tempo_fonte(t):return float(np.interp(t,NOVOS,ANTIGOS))
def tempo_novo(s):return float(np.interp(s,ANTIGOS,NOVOS))


class Movimento:
    def __init__(self,m):
        self.m=m;self.v8=v5.leitor_linear(m,NOME)
        self.v7=v5.leitor_linear(bbmodelo.ler(v8.v7.SAIDA),NOME)
        self.landing=float(self.v8(v8.POUSA)['body']['posicao'][2])

    def pose_fonte(self,s):
        p=self.v8(float(s));m=self.m
        # Recupera os acentos do golpe v7; volta à recuperação da v8 antes do pouso.
        w=C(s,[(0,0),(.60,0),(.79,1),(1.54,1),(1.70,0),(v8.DURACAO,0)])
        anterior=self.v7(min(float(s),v8.v7.DURACAO))
        for n in TRONCO:
            a=np.array(p[n]['rotacao']);b=np.array(anterior[n]['rotacao'])
            p[n]['rotacao']=((1-w)*a+w*b).tolist()
        if .38<=s<v8.POUSA:
            parent=bbmodelo.matrizes_ossos(m,p)['waist'];r=parent[:3,:3];o=m.ossos['body'].origem
            for lado in ['left','right']:
                c=v5.v4.centro_pe(m,lado);h=bbmodelo.aplicar(parent,[m.ossos['leg_'+lado].origem])[0]
                tuck=np.array([c[0],h[1]-5.2,h[2]-7.0]);hit=np.array([np.copysign(4.7,c[0]),h[1]+5.5,h[2]-16.3])
                entrada=C(s,[(.38,0),(.54,1),(v8.POUSA,1)])
                golpe=C(s,[(.38,0),(.79,0),(.87,.60),(.94,1),(1.02,1),(1.17,0),(v8.POUSA,0)])
                saida=C(s,[(.38,0),(v8.POUSA-.16,0),(v8.POUSA,1)])
                a=(1-entrada)*(v5.v4.apoio(m,lado,-45)+[0,0,7.5])+entrada*((1-golpe)*tuck+golpe*hit)
                a=(1-saida)*a+saida*(c+[0,0,self.landing])
                ang=C(s,[(.38,-45),(.54,10),(.79,12),(.94,70),(1.02,70),(1.17,15),(1.54,15),(v8.POUSA,0)])
                rs=v5.v4.perna(m,lado,euler(r),parent[:3,3]-o+r@o,a,ang)
                for n,rr in zip(['leg_','shin_','foot_'],rs):p[n+lado]={'rotacao':rr}
        return p

    def pose(self,t):return self.pose_fonte(tempo_fonte(t))


def trilhas(m):
    clip=next(a for a in m.animacoes if a['name']==NOME);nomes={o.uuid:o.nome for o in m.ossos.values()};out={}
    for uid,a in clip['animators'].items():
        if uid not in nomes:continue
        for k in a.get('keyframes',[]):
            assert k['interpolation']=='linear'
            dp=k['data_points'][0];v=np.array([float(dp.get(q,0)) for q in ['x','y','z']])
            out.setdefault((nomes[uid],k['channel']),[]).append((float(k['time']),v))
    for v in out.values():v.sort(key=lambda a:a[0])
    return out


def operacoes(m,mov):
    ops=[{'op':'remove_animation','animation':NOME},{'op':'add_animation','name':NOME,'length':DURACAO,'loop':'once','snapping':120}]
    for (n,canal),vals in trilhas(m).items():
        if n in PERNAS+TRONCO and canal=='rotation':continue
        tt=np.array([t for t,_ in vals]);vv=np.array([v for _,v in vals])
        # Preserva as amostras de apoio refinadas da v8 e insere as quebras da mudança de ritmo.
        for s in sorted(set(tt.tolist()+ANTIGOS.tolist())):
            v=[float(np.interp(s,tt,vv[:,j])) for j in range(3)]
            ops.append({'op':'set_keyframe','animation':NOME,'bone':n,'channel':canal,'time':round(tempo_novo(s),6),'value':v,'interpolation':'linear'})
    ss=np.array(sorted(set(np.linspace(0,v8.DURACAO,343).tolist()+ANTIGOS.tolist()+[.38,.54,.79,.87,.94,1.02,1.17,1.54])))
    pp=[mov.pose_fonte(s) for s in ss]
    for n in PERNAS+TRONCO:
        vv=v5.v4.continuidade(np.array([p[n]['rotacao'] for p in pp]))
        for i,s in enumerate(ss):ops.append({'op':'set_keyframe','animation':NOME,'bone':n,'channel':'rotation','time':round(tempo_novo(s),6),'value':vv[i].round(6).tolist(),'interpolation':'linear'})
    return ops


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--refazer',action='store_true');args=ap.parse_args()
    original=sha(FONTE);m=bbmodelo.ler(FONTE);mov=Movimento(m);ops=operacoes(m,mov)
    prov=PASTA/'proveniencia.json'
    if SAIDA.exists():
        velho=json.loads(prov.read_text()) if prov.exists() else {}
        if not args.refazer or velho.get('saida_sha256')!=sha(SAIDA) or velho.get('fonte_sha256')!=original:raise SystemExit('Saída existente/editada preservada; criar outra versão.')
    PASTA.mkdir(exist_ok=True);(PASTA/'ritmo.ops.json').write_text(json.dumps(ops,separators=(',',':'))+'\n',encoding='utf-8')
    shutil.copy2(FONTE,SAIDA);motor.editar(SAIDA,ops);novo=bbmodelo.ler(SAIDA)
    for campo in ['elements','textures','groups','outliner']:assert novo.bruto[campo]==m.bruto[campo],campo
    for a in m.animacoes:
        if a['name']==NOME:continue
        aa=copy.deepcopy(a)
        for b in aa.get('animators',{}).values():b.setdefault('keyframes',[])
        assert aa==next(b for b in novo.animacoes if b['uuid']==a['uuid'])
    assert sha(FONTE)==original
    prov.write_text(json.dumps({'fonte':FONTE.relative_to(RAIZ).as_posix(),'fonte_sha256':original,'saida_sha256':sha(SAIDA),'operacoes':len(ops),'duracao':DURACAO,'tempos_fonte':ANTIGOS.tolist(),'tempos_novos':NOVOS.tolist(),'rig_geometria_uv_atlas_preservados':True},indent=2)+'\n',encoding='utf-8')
    marc=json.loads((FONTE.parent/'animacoes.json').read_text());marc[NOME]={'HitFrame':round(IMPACTO,6),'RecoveryStart':round(FIM_GOLPE,6),'CancelOpen':round(tempo_novo(2.01),6)}
    (PASTA/'animacoes.json').write_text(json.dumps(marc,indent=2)+'\n',encoding='utf-8')
    print('Criada v9:',DURACAO,'s; início chute',round(INICIO_CHUTE,3),'impacto',round(IMPACTO,3),';',len(ops),'operações.')


if __name__=='__main__':main()
