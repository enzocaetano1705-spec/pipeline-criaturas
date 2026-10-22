"""Revisão artística original do pavão e1: três volumes, seis penas em planos.

Usa operações em lote do motor Blockbench e conserva os ossos e clipes do ensaio.
O atlas é pintado neste script, sem incorporar material das referências externas.
"""

import json
import math
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from criaturas import bbmodelo, motor, render, texturizar, animar

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "estudo-referencias" / "pavao-planos-animado.bbmodel"
DEST = ROOT / "revisao-v2"
FILE = DEST / "criatura-pavao-e1-v2.bbmodel"
RES = 128
P = {
    "main": "#30b9b4", "light": "#5bd1c3", "shade": "#239e9f",
    "deep": "#126b7a", "navy": "#173d50", "dark": "#132e3a",
    "green": "#54b88f", "green_light": "#87d19e", "gold": "#edb33c",
    "amber": "#db872d", "brown": "#724022", "cream": "#fff2c4",
    "white": "#ffffff", "blush": "#80d0b2",
}


def specifications():
    # Corpo arredondado por três grandes volumes de degraus discretos.
    cubes = [
        ("body_cube", "body", [-8, 2.5, -6], [8, 12, 6]),
        ("body_crown", "body", [-6.5, 11.7, -5.5], [6.5, 14, 5.5]),
        ("body_cube_2", "body", [-6.7, 0.5, -5.7], [6.7, 3, 5.7]),
    ]
    for side in ("left", "right"):
        sign = -1 if side == "left" else 1
        rects = [((1.5, 5.8), (11.8, 20.0)),
                 ((5.1, 12.8), (17.5, 21.7)),
                 ((11.8, 19.4), (16.5, 21.7))]
        # (min_x,max_x) em módulo e (min_y,max_y), numa mesma ordem de raiz a ponta.
        for part, (xs, ys) in enumerate(rects, 1):
            x0, x1 = (-xs[1], -xs[0]) if sign < 0 else xs
            cubes.append((f"feather_{side}_{part}_cube", f"feather_{side}_{part}",
                          [x0, ys[0], 0], [x1, ys[1], 0]))
    return cubes


def atlas_layout(cubes):
    tiles = []
    for name, bone, a, b in cubes:
        sx, sy, sz = [q - p for p, q in zip(a, b)]
        faces = {"north": (sx, sy), "south": (sx, sy)}
        if bone == "body":
            faces.update({"east": (sz, sy), "west": (sz, sy),
                          "up": (sx, sz), "down": (sx, sz)})
        for face, (w, h) in faces.items():
            tiles.append((name, face, max(2, int(math.ceil(w * 2))), max(2, int(math.ceil(h * 2)))))
    # Shelf packing by height preserves dedicated islands for both sides of each plane.
    tiles.sort(key=lambda x: (-x[3], -x[2], x[0], x[1]))
    x = y = shelf = 0
    result = {}
    for name, face, w, h in tiles:
        if x + w + 1 > RES:
            x, y, shelf = 0, y + shelf + 1, 0
        if y + h + 1 > RES:
            raise RuntimeError(f"Atlas {RES}x{RES} insuficiente em {name}:{face}")
        result[(name, face)] = [x, y, x + w, y + h]
        x += w + 1
        shelf = max(shelf, h)
    return result


def draw_eye(d, cx, cy):
    d.ellipse((cx-4.4, cy-4.4, cx+4.4, cy+4.5), fill=P["dark"])
    d.ellipse((cx-3.3, cy-3.9, cx+3.4, cy+3.5), fill=P["cream"])
    d.ellipse((cx-2.9, cy-2.8, cx+2.9, cy+3.6), fill=P["amber"])
    d.ellipse((cx-2.2, cy-0.5, cx+2.1, cy+3.5), fill=P["brown"])
    d.ellipse((cx-1.6, cy-0.9, cx+1.4, cy+1.7), fill=P["dark"])
    d.ellipse((cx-2.0, cy-2.9, cx+0.2, cy-0.6), fill=P["white"])
    d.point((round(cx+2.2), round(cy+1.5)), fill=P["cream"])


def body_tile(name, face, width, height):
    base = P["main"]
    if face in ("up",): base = P["light"]
    if face in ("down",): base = P["deep"]
    if face in ("east", "west"): base = P["shade"]
    img = Image.new("RGBA", (width, height), base)
    d = ImageDraw.Draw(img)
    # Grupos de penugem marcados à mão, poucos blocos de cor, sem ruído aleatório.
    for x, y in ((3, 3), (width-5, 5), (5, height-5), (width-7, height-4),
                 (width//4, height-3), (3*width//4, height//3)):
        if 0 <= x < width and 0 <= y < height:
            d.line((x, y, x+2, y+1), fill=P["light"] if (x+y)%3 else P["deep"])
    if face == "north" and name == "body_cube":
        # Rosto 34x20+ texels; a expressão é o elemento mais legível da criatura.
        cx = width/2
        for px in (0.28*width, 0.72*width):
            draw_eye(d, px, 0.42*height)
        d.arc((0.1*width, 0.38*height, 0.9*width, 0.93*height), 7, 170,
              fill=P["dark"], width=2)
        d.line((0.14*width, 0.70*height, 0.24*width, 0.80*height), fill=P["dark"], width=1)
        d.line((0.86*width, 0.70*height, 0.76*width, 0.80*height), fill=P["dark"], width=1)
        # Dentes pequenos e pontudos; cinco ao longo do sorriso.
        for fx, down in ((0.20, 1), (0.34, -1), (0.51, 1), (0.67, -1), (0.81, 1)):
            x = int(fx*width)
            y = int((0.78 - 0.05*math.cos((fx-.5)*math.pi))*height)
            if down > 0:
                d.polygon([(x-2,y-1),(x+2,y-1),(x,y+3)],fill=P["cream"])
            else:
                d.polygon([(x-2,y+1),(x+2,y+1),(x,y-3)],fill=P["cream"])
        d.point((round(cx), height-3), fill=P["shade"])
        # Cilhos externos ampliam a expressão preservando o desenho original.
        d.line((int(width*.12),int(height*.29),int(width*.20),int(height*.22)),fill=P["dark"],width=1)
        d.line((int(width*.80),int(height*.22),int(width*.88),int(height*.29)),fill=P["dark"],width=1)
        for px,py in ((5,4),(width-6,4),(3,height-5),(width-4,height-5)):
            d.point((px,py),fill=P["gold"])
    elif face == "north" and name == "body_crown":
        # Losango dourado na testa, uma única marca central.
        cx,cy=width//2,max(2,int(height*.49))
        d.polygon([(cx,cy-4),(cx+3,cy),(cx,cy+4),(cx-3,cy)], fill=P["brown"])
        d.polygon([(cx,cy-3),(cx+2,cy),(cx,cy+3),(cx-2,cy)], fill=P["gold"])
        d.polygon([(cx,cy-2),(cx+1,cy-1),(cx,cy)], fill=P["cream"])
        for x,y in ((3,1),(width-4,2),(6,height-2),(width-7,height-2)):
            d.point((x,y),fill=P["gold"])
    elif face == "north" and name == "body_cube_2":
        d.line((2,height-2,width-3,height-2),fill=P["deep"],width=1)
        for x in (width//4,width//2,3*width//4):
            d.line((x,height-4,x+2,height-3),fill=P["light"])
    elif face == "south":
        for x,y in ((5,5),(width//2,4),(width-6,8),(width//3,height-4)):
            if y<height: d.line((x,y,x+2,y+2),fill=P["light"])
    elif face in ("east","west"):
        d.line((width-3,2,width-3,height-3),fill=P["deep"])
        d.line((2,height-4,6,height-3),fill=P["green"])
    return img


def feather_tile(name, face, w, h):
    side = "left" if "_left_" in name else "right"
    part = int(name.rsplit("_",2)[1])
    spec = next(spec for spec in specifications() if spec[0] == name)
    a,b = spec[2:]
    img = Image.new("RGBA",(w,h),(0,0,0,0))
    # Pintura paramétrica em pixels: bordas recortadas, nervura e ocelo.
    data=np.zeros((h,w,4),dtype=np.uint8)
    rgb={key:tuple(bytes.fromhex(c[1:])) for key,c in P.items()}
    for iy in range(h):
        y=b[1]-(iy+.5)/h*(b[1]-a[1])
        for ix in range(w):
            x=a[0]+(ix+.5)/w*(b[0]-a[0])
            if face == "north": x=b[0]-(ix+.5)/w*(b[0]-a[0])
            t=abs(x)
            visible=False
            col="main"
            if part==1:
                # Cabo curvo e afinado, emergindo do alto da cabeça.
                center=12.3+1.28*(t-1.7)+.11*(t-1.7)**2
                radius=.26+.17*(t-1.7)
                visible=1.7<=t<=5.8 and abs(y-center)<radius
                col="deep" if y<center-.12 else "shade"
            elif part==2:
                center=19.5+1.2*math.sin((t-5.2)/7.5*math.pi)
                radius=.66+.43*math.sin(max(0,min(1,(t-5.2)/7.5))*math.pi)
                visible=5.2<=t<=12.8 and abs(y-center)<radius
                col="deep" if y<center-.25 else "main"
            else:
                u=(t-11.8)/7.6
                center=20.2-2.0*u+.10*math.sin(u*math.pi)
                radius=.2+1.65*max(0,math.sin(u*math.pi))**.55
                # Serrilhas discretas das bárbulas, sem peças adicionais.
                notch=(int(t*3.5)+int(y*5))%13==0
                visible=0<=u<=1 and abs(y-center)<radius-(.18 if notch else 0)
                col="green" if u>.38 else "main"
                if abs(y-center)<.13:col="deep"
                oc=((t-16.0)/1.48)**2+((y-19.0)/1.25)**2
                if oc<1.0:col="green_light"
                if oc<.51:col="deep"
                if oc<.22:col="navy"
                if oc<.055:col="dark"
                if oc<.75 and oc>.51 and y<19.0:col="gold"
            if visible:
                # Um toque de contraste no eixo, mantendo a folhagem simples.
                if part<3 and (int(t*2)+int(y*2))%19==0:col="light"
                data[iy,ix,:3]=rgb[col]
                data[iy,ix,3]=255
    return Image.fromarray(data,"RGBA")


def main():
    if DEST.exists():
        raise SystemExit("A revisão-v2 já existe; preserve-a e crie outro identificador.")
    DEST.mkdir(parents=True)
    shutil.copy2(SOURCE, FILE)
    cubes=specifications()
    rects=atlas_layout(cubes)
    model=bbmodelo.ler(FILE)
    operations=[{"op":"remove_node","target":c.nome} for c in model.cubos]
    operations.append({"op":"set_model_properties","resolution":{"width":RES,"height":RES}})
    for side in ("left","right"):
        sign=-1 if side=="left" else 1
        # Y faz o arco existir também na silhueta lateral; pivôs seguem a curva.
        operations.extend([
            {"op":"update_node","target":f"feather_{side}_1",
             "origin":[sign*2.4,13.1,0],"rotation":[4,-sign*42,0]},
            {"op":"update_node","target":f"feather_{side}_2",
             "origin":[sign*5.5,19.3,0],"rotation":[0,0,0]},
            {"op":"update_node","target":f"feather_{side}_3",
             "origin":[sign*12.0,20.0,0],"rotation":[0,0,0]},
        ])
    for name,bone,a,b in cubes:
        faces={face:{"uv":uv} for (n,face),uv in rects.items() if n==name}
        operations.append({"op":"add_cube","name":name,"parent":bone,"from":a,"to":b,
                           "box_uv":False,"mirror_uv":False,"faces":faces})
    (DEST/"geometria.ops.json").write_text(json.dumps({"operations":operations},ensure_ascii=False,indent=2),encoding="utf-8")
    motor.editar(FILE,operations)
    edited=bbmodelo.ler(FILE)
    tex=Image.new("RGBA",(RES,RES),(0,0,0,0))
    for (name,face),(x0,y0,x1,y1) in rects.items():
        if name.startswith("feather_"):
            tile=feather_tile(name,face,x1-x0,y1-y0)
        else:
            tile=body_tile(name,face,x1-x0,y1-y0)
        tex.paste(tile,(x0,y0))
    tex.save(DEST/"textura.png")
    texturizar.aplicar_no_modelo(FILE,np.asarray(tex),edited,[])
    model=bbmodelo.ler(FILE)
    render.folha(model,lado_px=360,titulo="Pavão e1 | revisão v2").save(DEST/"folha.png")
    geometry=motor.validar(FILE)
    aerr,awarn,amessages=animar.validar_animacoes(FILE)
    geom=motor.resumo_validacao(geometry)
    report={"pecas":len(model.cubos),"solidos":3,"planos":6,"ossos":len(model.ossos),
            "atlas":[RES,RES],"validacao_geometria":{"erros":geom[0],"avisos":geom[1],"mensagens":geom[2]},
            "validacao_animacoes":{"erros":aerr,"avisos":awarn,"mensagens":amessages},
            "animacoes":[a.get('name') for a in model.animacoes],
            "origem":"arte e pintura próprias; técnicas estudadas em Koromon e Harpymon"}
    (DEST/"relatorio.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Criado: {FILE}")
    print(f"Peças: {len(model.cubos)} (3 volumes + 6 planos), atlas: {RES}²")
    print(f"Geometria: {geom[0]} erros e {geom[1]} avisos; animações: {aerr} erros e {awarn} avisos")
    print(f"Prévia: {DEST/'folha.png'}")


if __name__=="__main__":
    main()
