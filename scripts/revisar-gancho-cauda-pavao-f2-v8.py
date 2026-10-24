"""Confere J, leque externo, chute descendente e preservação dos clipes anteriores."""
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
g=carregar('gancho_v8','animar-gancho-cauda-pavao-f2-v8.py')
r7=carregar('revisor_v7','revisar-catapulta-pavao-f2-v7.py')
previa=r7.previa


def aprovados(m):
    antes=bbmodelo.ler(g.FONTE);res={};porid={c.uuid:c for c in m.cubos}
    neutros={'tail_mid_flex_2','tail_mid_flex_3','tail_base_flex_2','tail_base_flex_3','tail_hook'}
    for clip in antes.animacoes:
        nome=clip['name'];dur=clip['length']
        if nome==g.NOME:continue
        copia=copy.deepcopy(clip)
        for v in copia.get('animators',{}).values():v.setdefault('keyframes',[])
        assert copia==next(a for a in m.animacoes if a['uuid']==clip['uuid'])
        for n in neutros:
            if n not in antes.ossos:continue
            assert antes.ossos[n].uuid not in clip.get('animators',{})
            np.testing.assert_allclose(m.ossos[n].rotacao,0)
        if nome not in ['attack_stomp','attack_spin']:
            for n,o in antes.ossos.items():
                p=m.ossos[n].pai
                if p=='tail_hook':p='tail_2'
                assert p==o.pai
                if n not in neutros:np.testing.assert_allclose(m.ossos[n].origem,o.origem)
                np.testing.assert_allclose(m.ossos[n].rotacao,o.rotacao)
            res[nome]={'chaves_originais_preservadas':True,'articulacoes_modificadas_neutras':True}
            continue
        aa=g.v5.leitor_linear(antes,nome);bb=g.v5.leitor_linear(m,nome);erro=0
        for t in np.linspace(0,dur,int(round(dur*240))+1):
            ma=bbmodelo.matrizes_ossos(antes,aa(t));mb=bbmodelo.matrizes_ossos(m,bb(t))
            for c in antes.cubos:
                x=bbmodelo.aplicar(bbmodelo.matriz_cubo(antes,c,ma),bbmodelo.cantos(c));y=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,porid[c.uuid],mb),bbmodelo.cantos(c))
                erro=max(erro,float(np.linalg.norm(x-y,axis=1).max()))
        assert erro<1e-8;res[nome]={'desvio_geometrico_max':erro,'amostragem_hz':240,'chaves_originais_preservadas':True}
    assert m.bruto['elements']==antes.bruto['elements'] and m.bruto['textures']==antes.bruto['textures']
    res['geometria_uv_atlas_identicos']=True
    return res


def conferir(m,fn,fps):
    r4=r7.r6.r5.r4;rest=bbmodelo.matrizes_ossos(m)
    fans=[c for c in m.cubos if c.osso.startswith('tail_blade_')];shaft=[m.cubo(n) for n in g.PARTES]
    surf={c.uuid:g.v5.v4.superficie_opaca(m,c) for c in m.cubos};pts={c.uuid:g.v5.v4.superficie_opaca(m,c,False) for c in fans};base={}
    for c in fans:
        w=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,rest),pts[c.uuid])
        for q in shaft:base[c.uuid,q.uuid]=r4.profundidade(bbmodelo.aplicar(np.linalg.inv(bbmodelo.matriz_cubo(m,q,rest)),w),q)
    minimo=(100,None,None);pior=(0,None,None,None);juntas=[];solo=[];voo=[];leque=[];largura=[];folgas=[];j={}
    normals=np.array([bbmodelo.matriz_cubo(m,c,rest)[:3,0] for c in fans]);gram=normals@normals.T
    xs=np.concatenate([bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,rest),surf[c.uuid])[:,0] for c in fans]);largura_base=float(np.ptp(xs))
    for t in np.linspace(0,g.DURACAO,int(round(g.DURACAO*fps))+1):
        t=float(t);p=fn(t);mat=bbmodelo.matrizes_ossos(m,p);ys=[]
        for c in m.cubos:
            y=float(bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mat),surf[c.uuid])[:,1].min());ys.append(y)
            if y<minimo[0]:minimo=(y,t,c.nome)
        inversas={q.uuid:np.linalg.inv(bbmodelo.matriz_cubo(m,q,mat)) for q in shaft}
        for c in fans:
            w=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mat),pts[c.uuid])
            for q in shaft:
                novo=float(np.maximum(0,r4.profundidade(bbmodelo.aplicar(inversas[q.uuid],w),q)-base[c.uuid,q.uuid]).max())
                if novo>pior[0]:pior=(novo,t,c.nome,q.nome)
        for bone,a,b in [('waist','hips','TorsoHips'),('chest','TorsoHips','torso'),('tail_1','hips','tail_mid')]+[(g.CAUDA[i],g.PARTES[i-1],g.PARTES[i]) for i in range(1,6)]:
            o=m.ossos[bone];pt=bbmodelo.aplicar(mat[bone],[o.origem])[0]
            juntas.extend([r7.r6.fora(m,m.cubo(a),mat,pt),r7.r6.fora(m,m.cubo(b),mat,pt)])
        ty=min(float(bbmodelo.caixa_mundo(m,c,mat)[0][1]) for c in shaft)
        if .34<=t<=g.SAI:solo.append(abs(ty-g.CHAO))
        if g.SAI<t<g.POUSA and min(ys)>g.CHAO+.05:voo.append(t)
        normals=np.array([bbmodelo.matriz_cubo(m,c,mat)[:3,0] for c in fans]);leque.append(float(abs(normals@normals.T-gram).max()))
        xs=np.concatenate([bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mat),surf[c.uuid])[:,0] for c in fans]);largura.append(abs(float(np.ptp(xs))-largura_base))
        # As articulações dobram para o lado fechado, evitando fendas na curva.
        for n in g.CAUDA[1:]:
            a=p[n]['rotacao'][0];folgas.append(max(0,-a) if n=='tail_mid_flex_2' else max(0,a))
    for t in [0,g.DURACAO]:
        mat=bbmodelo.matrizes_ossos(m,fn(t))
        for n in mat:np.testing.assert_allclose(mat[n],rest[n],atol=2e-5)
    mat=bbmodelo.matrizes_ossos(m,fn(g.CARGA));c=m.cubo('tail_base_3');pt=(c.de+c.ate)/2;pt[2]=c.ate[2]
    tip=bbmodelo.aplicar(bbmodelo.matriz_cubo(m,c,mat),[pt])[0];root=bbmodelo.aplicar(mat['tail_1'],[m.ossos['tail_1'].origem])[0]
    r=bbmodelo.matriz_cubo(m,c,mat);j={'ponta_em_relacao_raiz_z':float(tip[2]-root[2]),'ponta_acima_apoio':float(tip[1]-g.CHAO),'ponta_tangente_y':float(r[1,2]),'ponta_tangente_z':float(r[2,2])}
    a,v,f,grav=g.cinematica(m);apice=g.SAI+v[1]/grav;inicio=apice+.035;hit=apice+.165
    assert minimo[0]>g.CHAO-.025,minimo
    assert pior[0]<.05,pior
    assert max(juntas)<1e-5 and max(solo)<.025,(max(juntas),max(solo))
    assert max(largura)<1e-6 and max(folgas)<1e-5,(max(largura),max(folgas))
    assert j['ponta_em_relacao_raiz_z']>3 and j['ponta_acima_apoio']>1 and j['ponta_tangente_y']>0 and j['ponta_tangente_z']>0,j
    assert v[1]>35 and v[2]<-15 and hit<g.POUSA-.2
    assert g.SAI<apice<inicio<hit and v[1]-grav*(hit-g.SAI)<0
    return {'minimo_y_visivel':minimo,'nova_penetracao_leque_cauda':pior,'juntas_fora_volumes_max':max(juntas),'apoio_cauda_erro_max':max(solo),
            'largura_leque_erro_max':max(largura),'normais_leque_variacao_max':max(leque),'rotacao_contraria_juntas_max':max(folgas),'curva_J':j,'fase_aerea_completa':[min(voo),max(voo)],
            'lancamento_velocidade':v.tolist(),'subida_apos_lancamento':float(v[1]**2/(2*grav)),'apice_s':apice,'inicio_chute_s':inicio,'impacto_s':hit,
            'velocidade_vertical_inicio_chute':float(v[1]-grav*(inicio-g.SAI)),'velocidade_vertical_impacto':float(v[1]-grav*(hit-g.SAI)),'inicio_fim_neutros':True}


def imagens(m,fn,planejado=False):
    tt=np.arange(0,g.DURACAO,.02);proj=previa.projetor(m,fn,tt,'lado',256,300)
    tail=copy.copy(m);tail.cubos=[m.cubo(n) for n in g.PARTES];tp=previa.projetor(tail,fn,[g.CARGA],'lado',256,300)
    a,v,_,grav=g.cinematica(m);apice=g.SAI+v[1]/grav
    im=Image.new('RGB',(768,654),(246,248,251))
    for i,(t,n) in enumerate([(g.CARGA,'carga J'),(g.CARGA,'cauda sem penas'),(.90,'lancado'),(apice,'patas recolhidas'),(apice+.165,'chute na descida'),(g.POUSA,'pouso')]):
        mm,pp=(tail,tp) if i==1 else (m,proj);im.paste(previa.quadro(mm,fn,t,pp,n),(i%3*256,i//3*327))
    im.save(g.PASTA/('poses-planejadas.png' if planejado else 'poses-gancho.png'))
    if planejado:return
    projs=[previa.projetor(m,fn,tt,v,384,300) for v in ['3/4','lado']];frames=[]
    for t in list(tt)+[g.DURACAO]*15:
        fase='apoio e carga J' if t<g.SAI else 'lancado - recolhido' if t<apice+.035 else 'chute na descida' if t<apice+.335 else 'pouso e recuperacao'
        im=Image.new('RGB',(768,327),(246,248,251))
        for i,pr in enumerate(projs):im.paste(previa.quadro(m,fn,t,pr,fase),(i*384,0))
        frames.append(im)
    duracoes=[20]*len(tt)
    duracoes[-1]=round((g.DURACAO-float(tt[-1]))*1000)
    duracoes.extend([20]*15)
    frames[0].save(g.PASTA/'previa-gancho.gif',save_all=True,append_images=frames[1:],duration=duracoes,loop=0)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--poses',action='store_true');args=ap.parse_args()
    if args.poses:m=bbmodelo.ler(g.FONTE);g.preparar_rig(m);fn=lambda t:g.pose(m,t)
    else:m=bbmodelo.ler(g.SAIDA);fn=g.v5.leitor_linear(m,g.NOME)
    g.PASTA.mkdir(exist_ok=True);rel=conferir(m,fn,60 if args.poses else 240)
    rel.update(r7.r6.r5.r4.medir(m,fn,g.DURACAO,60 if args.poses else 240))
    assert rel['nova_penetracao_pena_perna'][0]<.05,rel['nova_penetracao_pena_perna']
    if not args.poses:
        (g.PASTA/'aprovados-preservados.json').write_text(json.dumps(aprovados(m),indent=2)+'\n',encoding='utf-8')
        _,tr=r7.r6.r5.r4.anterior.leitor(m,next(v for v in m.animacoes if v['name']==g.NOME))
        maior=max(float(abs(np.diff(np.array([v for _,v in ch['rotation']]),axis=0)).max()) for ch in tr.values())
        pos=np.array([v for _,v in tr['body']['position']]);passo=float(np.linalg.norm(np.diff(pos,axis=0),axis=1).max())
        assert maior<30 and passo<1,(maior,passo)
        rel.update(variacao_euler_chave_max=maior,passo_bacia_chave_max=passo)
    (g.PASTA/('medidas-planejadas-superficies.json' if args.poses else 'medidas-gancho.json')).write_text(json.dumps(rel,indent=2)+'\n',encoding='utf-8')
    print('J',rel['curva_J'],'leque/cauda',rel['nova_penetracao_leque_cauda'])
    print('Apice',rel['apice_s'],'inicio chute',rel['inicio_chute_s'],'impacto',rel['impacto_s'],'velocidade Y',rel['velocidade_vertical_impacto'])
    print('Chão',rel['minimo_y_visivel'],'penas/pernas',rel['nova_penetracao_pena_perna'],'juntas',rel['juntas_fora_volumes_max'])
    imagens(m,fn,args.poses)


if __name__=='__main__':main()
