"""Mede a execução deste pedido pelos contadores locais; não estima preço da assinatura."""
import json,os,sys,hashlib
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'modelos/fera-fera-agil-das-sombras/organico-v1/auditoria'
MARK='produzi mais referencias e quero que você modele'


def snapshot(label,marker=MARK,out=OUT):
    tid=os.environ.get('CODEX_THREAD_ID','01a1a8db-ce59-72c1-b93b-4defb4f868f3')
    paths=list((Path.home()/'.codex/sessions').rglob('*'+tid+'*.jsonl'))
    if len(paths)!=1:raise RuntimeError('Registro único deste chat não localizado')
    latest=None;start=None;event_at=None
    for line in paths[0].open(encoding='utf-8'):
        row=json.loads(line);p=row.get('payload',{})
        if row.get('type')=='event_msg' and p.get('type')=='token_count':
            latest=(p.get('info') or {}).get('total_token_usage');event_at=row.get('timestamp')
        if row.get('type')=='response_item' and p.get('type')=='message' and p.get('role')=='user':
            text='\n'.join(str(c.get('text','')) for c in p.get('content',[]) if isinstance(c,dict))
            if marker in text:start={'timestamp':row.get('timestamp'),'acumulado':latest.copy()}
    if not start or not latest:raise RuntimeError('Início do pedido ou contador indisponível')
    keys=('input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens','total_tokens')
    delta={k:latest[k]-start['acumulado'][k] for k in keys}
    delta['uncached_input_tokens']=delta['input_tokens']-delta['cached_input_tokens']
    data={'etapa':label,'instante_utc':datetime.now(timezone.utc).isoformat(),'inicio_pedido':start,
          'ultimo_evento_uso_utc':event_at,'acumulado_atual':latest,'consumo_desde_pedido':delta,
          'preco':None,'percentual_assinatura_atribuivel':None,
          'limites':['contador atualizado apenas até o último evento disponível','cache está incluído na entrada; raciocínio está incluído na saída','inclui preparação/revisão/documentação deste pedido','sem divisão artificial por MCP ou tempo de subprocesso']}
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    path=out/(label+'.json')
    if path.exists():raise RuntimeError('Checkpoint já existe; escolha outro rótulo')
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'etapa':label,'tokens':delta},ensure_ascii=False))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('etapa')
    parser.add_argument('--marcador',default=MARK)
    parser.add_argument('--saida',type=Path,default=OUT)
    args=parser.parse_args()
    snapshot(args.etapa,args.marcador,args.saida)
