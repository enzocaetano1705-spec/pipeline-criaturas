"""Acelera só o levantamento do braço na entrada em combate da F3.

Reparametriza a v5: saque 0–0,40 s intacto, subida de 0,75 para 0,30 s,
floreio e apoio apenas antecipados. Preserva todos os outros doze clipes.
"""
import argparse
import importlib.util
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('combate_f3_v3',ROOT/'scripts/animar-combate-pavao-f3-v3.py')
v3=importlib.util.module_from_spec(sp);sp.loader.exec_module(v3)
g=v3.g;v2=v3.v2
SOURCE=ROOT/'modelos/criatura-pavao/f3/animacoes-v5/criatura-pavao-e3-combate-v5.bbmodel'
OUT=ROOT/'modelos/criatura-pavao/f3/animacoes-v6'
FILE=OUT/'criatura-pavao-e3-combate-v6.bbmodel'
START=.40;LIFT_END=.70;OLD_LIFT_END=1.15;SHIFT=OLD_LIFT_END-LIFT_END
LENGTH=2.1-SHIFT
CLIPS={'combat_enter':round(LENGTH,8)}


def source_time(t):
    if t<=START:return float(t)
    if t>=LIFT_END:return float(min(2.1,t+SHIFT))
    u=(t-START)/(LIFT_END-START)
    ratio=(LIFT_END-START)/(OLD_LIFT_END-START)
    # Derivada 1 e aceleração 0 nas emendas: acelera apenas no miolo da subida.
    progress=ratio*u+(1-ratio)*g.smooth(u)
    return START+(OLD_LIFT_END-START)*progress


def inverse_time(t):
    if t<=START:return float(t)
    if t>=OLD_LIFT_END:return float(t-SHIFT)
    lo,hi=START,LIFT_END
    for _ in range(45):
        mid=(lo+hi)/2
        if source_time(mid)<t:lo=mid
        else:hi=mid
    return (lo+hi)/2


def key_times(m):
    anim=next(a for a in m.animacoes if a['name']=='combat_enter')
    times=np.unique([float(k['time']) for a in anim['animators'].values() for k in a.get('keyframes',[])])
    return times,np.array([round(inverse_time(float(t)),8) for t in times])


def bake():
    # Retém cada chave original. Reamostrar em grade mais espaçada durante a
    # aceleração descartaria poses e alteraria o contato da espada com o piso.
    m=v3.prepare();anim=next(a for a in m.animacoes if a['name']=='combat_enter')
    original_times,new_times=key_times(m);mapping=dict(zip(original_times,new_times))
    names={o.uuid:n for n,o in m.ossos.items()}
    ops=[{'op':'remove_animation','animation':'combat_enter'},
         {'op':'add_animation','name':'combat_enter','length':CLIPS['combat_enter'],'loop':'once','snapping':120}]
    for uid,a in anim['animators'].items():
        keys=a.get('keyframes',[])
        if keys:assert uid in names
        for ch in ['rotation','position']:
            channel=sorted([k for k in keys if k['channel']==ch],key=lambda k:k['time'])
            if not channel:continue
            ts=np.array([float(k['time']) for k in channel])
            values=np.array([[float(k['data_points'][0][v]) for v in 'xyz'] for k in channel])
            assert np.array_equal(ts,original_times) or np.max(np.ptp(values,axis=0))<1e-8
            for k,value in zip(channel,values):
                assert k['interpolation']=='linear'
                ops.append({'op':'set_keyframe','animation':'combat_enter','bone':names[uid],
                    'channel':ch,'time':float(mapping[float(k['time'])]),'value':value.tolist(),'interpolation':'linear'})
    g.dump(OUT/'_cache/ops-animacoes.json',ops);v3.motor.editar(FILE,ops)
    g.dump(OUT/'geracao.json',{'fonte_sha256':g.sha(SOURCE),'saida_sha256':g.sha(FILE),
        'clipes_revistos':list(CLIPS),'operacoes':len(ops),'chaves_originais_preservadas':len(ops)-2,
        'metodo':'Mesmos valores, tempos remapeados sem descartar chaves.'})
    print('Retemporizado:',FILE.name,flush=True)


class Rig(v3.Rig):
    def enter(self,t,moving=False):return self.saved.pose('combat_enter',source_time(t))


def checks(report,m,rig,saved):
    src=v3.bbmodelo.ler(SOURCE);original=v2.review.Saved(src);error=0.;time_error=0.
    old_ts,new_ts=key_times(src)
    for t in np.linspace(0,LENGTH,397):
        a=rig.mats(saved.pose('combat_enter',float(t)))
        exact=float(np.interp(t,new_ts,old_ts))
        time_error=max(time_error,abs(exact-source_time(float(t))))
        b=rig.mats(original.pose('combat_enter',exact))
        error=max(error,max(float(abs(a[n]-b[n]).max()) for n in a))
    report['erro_caminho_retemporizado_matriz']=error
    report['desvio_tempo_curva_continua_segundos']=time_error
    if error>.001:report['erros'].append('Retime alterou a trajetória original')
    if time_error>.0003:report['erros'].append('Interpolação temporal perdeu precisão')
    suffix=0.
    for t in np.linspace(LIFT_END,LENGTH,229):
        a=rig.mats(saved.pose('combat_enter',float(t)));b=rig.mats(original.pose('combat_enter',float(t+SHIFT)))
        suffix=max(suffix,max(float(abs(a[n]-b[n]).max()) for n in a))
    report['erro_floreio_e_final_apenas_antecipados']=suffix
    if suffix>.001:report['erros'].append('Floreio ou apoio mudou além de sua antecipação')
    report['tempos']={'saque_preservado_ate':START,'levantamento_antes':OLD_LIFT_END-START,
        'levantamento_agora':LIFT_END-START,'floreio_inicio':LIFT_END,'floreio_fim':1.68-SHIFT,
        'apoio_ombro_inicio':1.70-SHIFT,'final':LENGTH,'velocidade_media_subida':2.5}
    assert 'combat_ready' in report['clipes_preservados'] and 'combat_walk' in report['clipes_preservados']
    contact=0.
    for t in np.linspace(.90-SHIFT,LENGTH,289):
        # A espada termina a descida durante o trecho retimado; medir a partir
        # do momento real em que o tempo da fonte alcança 0,90 s.
        if source_time(float(t))<.90:continue
        mats=rig.mats(saved.pose('combat_enter',float(t)));w=rig.weapons['right'];mat=mats[w['name']]
        v=rig.weaponverts['right']@mat[:3,:3].T+g.point(mat,w['grip'])
        contact=max(contact,abs(float(v[:,1].min())))
    report['erro_contato_espada_do_chao']=contact
    if contact>.025:report['erros'].append('Espada do chão perdeu apoio')


v3.SOURCE=SOURCE;v3.OUT=OUT;v3.FILE=FILE;v3.CLIPS=CLIPS;v3.Rig=Rig
v3.FLOURISH_START=LIFT_END;v3.FLOURISH_END=1.68-SHIFT


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--animar',action='store_true')
    ap.add_argument('--validar',action='store_true');ap.add_argument('--previas',action='store_true');args=ap.parse_args()
    (OUT/'_cache').mkdir(parents=True,exist_ok=True)
    if args.animar:bake()
    if args.validar:v3.validate(list(CLIPS),flourish_sides=('left',),extra_checks=checks,preserve_draw_until=START)
    if args.previas:v3.previews(list(CLIPS))


if __name__=='__main__':main()
