"""Traça regiões anatômicas do perfil; preserva vazios entre dedos fora das regiões."""
from pathlib import Path
import json,math
import numpy as np
from PIL import Image,ImageFilter

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'modelos/fera-fera-agil-das-sombras/gabarito-v1'


def simplify(points,eps):
    if len(points)<3:return points
    a,b=np.array(points[0],float),np.array(points[-1],float)
    direction=b-a;length=np.linalg.norm(direction)
    p=np.array(points,float)
    dist=np.linalg.norm(p-a,axis=1) if length<1e-9 else np.abs((direction[0]*(p[:,1]-a[1])-direction[1]*(p[:,0]-a[0]))/length)
    idx=int(dist.argmax())
    if dist[idx]<=eps:return [points[0],points[-1]]
    return simplify(points[:idx+1],eps)[:-1]+simplify(points[idx:],eps)


def trace(mask,box):
    x0,y0,x1,y1=box
    roi=np.zeros_like(mask);roi[y0:y1,x0:x1]=mask[y0:y1,x0:x1]
    roi=np.array(Image.fromarray(roi.astype('uint8')*255).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3)))>0
    edges={}
    for y,x in zip(*np.where(roi)):
        if y==0 or not roi[y-1,x]:edges.setdefault((x,y),[]).append((x+1,y))
        if x==roi.shape[1]-1 or not roi[y,x+1]:edges.setdefault((x+1,y),[]).append((x+1,y+1))
        if y==roi.shape[0]-1 or not roi[y+1,x]:edges.setdefault((x+1,y+1),[]).append((x,y+1))
        if x==0 or not roi[y,x-1]:edges.setdefault((x,y+1),[]).append((x,y))
    loops=[]
    while edges:
        start=next(iter(edges));point=start;loop=[]
        while True:
            loop.append(point)
            if point not in edges:break
            nxt=edges[point].pop()
            if not edges[point]:del edges[point]
            point=nxt
            if point==start:break
        if len(loop)>3:loops.append(loop)
    loop=max(loops,key=len)
    # Split a closed curve at a far vertex so RDP does not collapse the ring.
    a=np.array(loop[0]);k=int(np.argmax(np.linalg.norm(np.array(loop)-a,axis=1)))
    poly=simplify(loop[:k+1],1.4)[:-1]+simplify(loop[k:]+[loop[0]],1.4)[:-1]
    return [[int(x),int(y)] for x,y in poly]


def main():
    mask=np.array(Image.open(BASE/'entrada/perfil_esquerdo-mascara.png'))>127
    rois={'forearm_profile':[143,220,296,293],'leg_profile':[230,274,344,396],'torso_profile':[244,165,407,276],'mane_back_profile':[284,76,358,175]}
    data={name:{'roi':box,'poligono':trace(mask,box),'origem':'contorno da máscara da captura, simplificado a 1,4 px; fechamento morfológico de 1 pixel'} for name,box in rois.items()}
    (BASE/'entrada/contornos-partes.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for name,d in data.items():print(name,len(d['poligono']),'vértices do contorno')


if __name__=='__main__':main()
