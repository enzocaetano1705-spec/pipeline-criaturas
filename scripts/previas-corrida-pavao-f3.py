"""Prévias do Blockbench real por suas ferramentas MCP, sem código no aplicativo."""
import base64
import io
import json
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image,ImageDraw


class Client:
    def __init__(self,root):
        self.url=json.loads((root/'.mcp.json').read_text())['mcpServers']['blockbench']['url']
        self.headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream'};self.id=0
        self.request('initialize',{'protocolVersion':'2024-11-05','capabilities':{},
            'clientInfo':{'name':'previas-corridas-f3','version':'1.0'}})

    def request(self,method,params):
        self.id+=1
        req=urllib.request.Request(self.url,json.dumps({'jsonrpc':'2.0','id':self.id,'method':method,'params':params}).encode(),self.headers)
        with urllib.request.urlopen(req,timeout=120) as response:
            data=response.read().decode();session=response.headers.get('Mcp-Session-Id')
            if session:self.headers['Mcp-Session-Id']=session
        if data.startswith(('event:','data:')):data=next(line[6:] for line in data.splitlines() if line.startswith('data: '))
        result=json.loads(data)
        if 'error' in result:raise RuntimeError(result['error'])
        return result['result']

    def call(self,name,**kwargs):
        result=self.request('tools/call',{'name':name,'arguments':kwargs})
        if result.get('isError'):raise RuntimeError(result)
        return result


def decoded(result):
    image=next(x for x in result['content'] if x['type']=='image')
    return Image.open(io.BytesIO(base64.b64decode(image['data']))).convert('RGBA')


def gif(v,client,view,sequence,path,fps=24):
    frames=[];labels=[];bounds=None
    for name,t,label in sequence:
        client.call('animation_timeline',action='set_time',animation_id=name,time=float(t))
        im=decoded(client.call('capture_screenshot',view=view,max_size=640))
        box=im.getbbox()
        if bounds is None:bounds=box
        else:bounds=(min(bounds[0],box[0]),min(bounds[1],box[1]),max(bounds[2],box[2]),max(bounds[3],box[3]))
        frames.append(im);labels.append(label)
    # Um único recorte para a sequência inteira: a oscilação não é estabilizada pela câmera.
    bounds=(max(0,bounds[0]-12),max(0,bounds[1]-12),min(frames[0].width,bounds[2]+12),min(frames[0].height,bounds[3]+12))
    rendered=[]
    for im,label in zip(frames,labels):
        im=im.crop(bounds);bg=Image.new('RGBA',im.size,(238,242,244,255));bg.alpha_composite(im)
        output=Image.new('RGB',(bg.width,bg.height+25),(238,242,244));output.paste(bg.convert('RGB'),(0,25))
        ImageDraw.Draw(output).text((8,6),label,fill=(25,40,50));rendered.append(output)
    rendered[0].save(path,save_all=True,append_images=rendered[1:],duration=round(1000/fps),loop=0,disposal=2)
    return len(rendered)


def chain(v,combat,fps=20):
    walk=v.walk_name(combat);run=v.run_name(combat);start=run+'_start';stop=run+'_stop'
    a,per=v.WALK[combat],v.PERIOD[combat]
    start_phase,_=v.timing(start,v.CLIPS[start]);stop_phase,_=v.timing(stop,v.CLIPS[stop])
    segments=[(walk,0,a),(start,0,v.CLIPS[start]),
              (run,(start_phase%1)*per,2*per-(start_phase%1)*per),
              (stop,0,v.CLIPS[stop]),(walk,(stop_phase%1)*a,a-(stop_phase%1)*a)]
    sequence=[];ends=np.cumsum([d for n,b,d in segments]);starts=np.r_[0,ends[:-1]]
    for t in np.arange(0,ends[-1]-1e-7,1/fps):
        i=int(np.searchsorted(ends,t,side='right'));name,begin,duration=segments[i]
        period=v.CLIPS[name] if name in v.CLIPS else a
        sequence.append((name,(begin+t-starts[i])%period,f'{name} | {t:.2f} s'))
    return sequence


def capture(v):
    client=Client(v.ROOT);info=client.call('get_project_info')
    data=info.get('structuredContent') or json.loads(next(x['text'] for x in info['content'] if x['type']=='text'))
    assert Path(data['project']['save_path']).resolve()==v.FILE.resolve(),'Abra a versão de corrida antes de capturar.'
    view='corrida_f3_preview';client.call('create_offscreen_view',id=view,width=640,height=560,antialias=False,copy_view='none')
    counts={};cleanup='ok'
    try:
        client.call('animation_timeline',action='pause',animation_id='run')
        client.call('set_camera_angle',view=view,projection='perspective',position=[85,51,-125],target=[0,26,8],fov=37,max_size=640)
        for name,duration in v.CLIPS.items():
            n=round(duration*24)
            sequence=[(name,float(t),f'{name} | {t:.2f} s') for t in np.arange(n)*duration/n]
            counts[name]=gif(v,client,view,sequence,v.OUT/(name+'.gif'),fps=n/duration)
            print('Prévia nativa:',name,counts[name],'quadros',flush=True)
        for combat in [False,True]:
            key='sequencia-combate' if combat else 'sequencia-pacifica'
            counts[key]=gif(v,client,view,chain(v,combat),v.OUT/(key+'.gif'),fps=20)
            print('Sequência nativa:',key,counts[key],'quadros',flush=True)
        sheet=Image.new('RGB',(768,640),(238,242,244));draw=ImageDraw.Draw(sheet)
        for i,(name,t) in enumerate([('run',0),('run',.18),('run',.38),('combat_run',0),('combat_run',.20),('combat_run',.44)]):
            client.call('animation_timeline',action='set_time',animation_id=name,time=t)
            im=decoded(client.call('capture_screenshot',view=view,max_size=640));box=im.getbbox();im=im.crop(box);im.thumbnail((250,288))
            bg=Image.new('RGBA',im.size,(238,242,244,255));bg.alpha_composite(im)
            x=i%3*256;y=i//3*320;sheet.paste(bg.convert('RGB'),(x+(256-im.width)//2,y+26+(288-im.height)//2))
            draw.text((x+5,y+7),f'{name} {t:.2f} s',fill=(25,40,50))
        sheet.save(v.OUT/'poses-nativas.png')
    finally:
        try:client.call('delete_offscreen_view',view=view)
        except RuntimeError as error:
            if 'onContextMenu is not defined' not in str(error):raise
            # Algumas versões do plugin removem o registro e só então falham
            # ao soltar um listener. As capturas já estão concluídas.
            cleanup='registro removido; plugin informou onContextMenu is not defined no descarte do listener'
        finally:client.call('animation_timeline',action='set_time',animation_id='run',time=0)
    v.g.dump(v.OUT/'previas-nativas.json',{'modelo':str(v.FILE),'saida_sha256':v.g.sha(v.FILE),'fps_clipes_aproximado':24,
        'fps_sequencias':20,'quadros':counts,'camera_fixa':True,'limpeza_view':cleanup,
        'sequencias':'walk -> start -> run -> stop -> walk, com fases corretas nos encaixes; sem lógica de gameplay'})
