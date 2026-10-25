"""Amostra também a tolerância temporal nativa do Blockbench 5.2.2.

Código próprio a partir do comportamento observado: chaves a menos de
1/1200 s do cursor prevalecem sobre a interpolação. Não usa código do app.
"""
import numpy as np


class NativeSaved:
    def __init__(self,reader):
        self.reader=reader;self.channels=reader.channels;self.durations=reader.durations

    def effective_time(self,name,t,bone='forearm_left',field='rotacao'):
        ts,_=self.channels[name][bone][field];k=int(np.searchsorted(ts,t,side='left'))
        if k and abs(t-ts[k-1])<1/1200:return float(ts[k-1])
        if k<len(ts) and abs(t-ts[k])<1/1200:return float(ts[k])
        return t

    def pose(self,name,t):
        pose={}
        for bone,channels in self.channels[name].items():
            pose[bone]={}
            for field,(ts,values) in channels.items():
                k=int(np.searchsorted(ts,t,side='left'))
                if k and abs(t-ts[k-1])<1/1200:value=values[k-1]
                elif k<len(ts) and abs(t-ts[k])<1/1200:value=values[k]
                else:value=np.array([np.interp(t,ts,values[:,i]) for i in range(3)])
                pose[bone][field]=value.copy()
        return pose


def audit(v,file,names,output):
    m=v.bbmodelo.ler(file);ideal=v.v2.review.Saved(m);native=NativeSaved(ideal);rig=v.new_rig(m)
    result={'arquivo':str(file),'clipes':{}}
    for name in names:
        duration=ideal.durations[name];grip=dock=crest=0.;worst={};rootgap=0.
        # Fases fora da grade: a validação antiga em 240 Hz escondia a diferença.
        times=np.unique(np.r_[np.arange(0,duration,1/120)+.00047,np.arange(0,duration,1/120)+.00219])
        for t in times[times<duration]:
            p=native.pose(name,float(t));q=ideal.pose(name,float(t))
            if name.endswith('upper'):
                if hasattr(v,'compose_base'):
                    base=v.compose_base(rig,name,float(t),saved=native);a={**base,**p}
                    base=v.compose_base(rig,name,float(t),saved=ideal);b={**base,**q}
                else:
                    d=v.ENTER if name.startswith('combat_enter') else v.EXIT
                    base=rig.saved.pose('walk',(v.phase(t,d,name.startswith('combat_exit'))%1)*1.5)
                    a={**base,**p};b={**base,**q}
                p,q=a,b
            a=rig.mats(p);b=rig.mats(q)
            rootgap=max(rootgap,float(np.linalg.norm(p['tail_1'].get('posicao',[0,0,0]))))
            for side in v.SIDES:
                w=rig.weapons[side];wg=v.point(a[w['name']],w['grip'])
                state=v.review8.state(v,name,float(t),side)
                if state=='hand':
                    e=float(np.linalg.norm(wg-v.point(a['hand_'+side],rig.grips[side])))
                    if e>grip:grip=e;worst['mao']=[side,float(t)]
                elif state=='tail':
                    e=float(np.linalg.norm(wg-v.point(a['tail_1'],w['grip'])))
                    if e>dock:dock=e;worst['cauda']=[side,float(t)]
            for n in ['feather_left_1','feather_left_2','feather_right_1','feather_right_2']:
                p0=m.ossos[n].origem+[0,5,0]
                crest=max(crest,float(np.linalg.norm(v.point(a[n],p0)-v.point(b[n],p0))))
        varying=[ts for channels in ideal.channels[name].values() for ts,values in channels.values()
                 if np.max(np.ptp(values,axis=0))>1e-7]
        aligned=all(np.array_equal(ts,varying[0]) for ts in varying)
        result['clipes'][name]={'erro_preensao_nativo':grip,'erro_cauda_nativo':dock,
            'desvio_crista_nativo_vs_linear':crest,'deslocamento_raiz_cauda':rootgap,
            'canais_no_mesmo_relogio':aligned,'piores_tempos':worst}
        print(name,round(grip,4),round(dock,4),round(crest,4),'sincrono',aligned,flush=True)
    v.g.dump(output,result)
    return result
