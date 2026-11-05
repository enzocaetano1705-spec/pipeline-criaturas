from pathlib import Path
import sys
from PIL import Image,ImageDraw,ImageFont
from comum import BASE


def montar():
    rev=sys.argv[1] if len(sys.argv)>1 else 'v1'
    sheet=Image.new('RGB',(768,768),'white')
    d=ImageDraw.Draw(sheet)
    font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',13)
    small=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',11)
    def tile(path,x,y,title,subtitle=''):
        im=Image.open(path).convert('RGBA')
        im.thumbnail((250,220),Image.Resampling.LANCZOS)
        bg=Image.new('RGBA',im.size,'white');bg.alpha_composite(im)
        sheet.paste(bg.convert('RGB'),(x+(256-im.width)//2,y+27+(222-im.height)//2))
        d.text((x+8,y+3),title,font=font,fill='#332c2a')
        if subtitle:d.text((x+8,y+20),subtitle,font=small,fill='#6d6360')
    tile(BASE/'entrada/conceito-768.png',0,0,'Referência aprovada','Preguiça gigante · rogue · F3')
    tile(BASE/f'previas-{rev}/blockbench-3-4.png',256,0,'A · autoria Blockbench','Render Blender · cores de bloqueio')
    tile(BASE/f'previas-{rev}/blender-3-4.png',512,0,'B · autoria Blender','Render Blender · cores de bloqueio')
    for row,author in enumerate(('blockbench','blender'),1):
        for col,view in enumerate(('frente','lado','costas')):
            tile(BASE/f'previas-{rev}/{author}-{view}.png',col*256,row*256,
                 f'{"A" if author=="blockbench" else "B"} · {view}',
                 'Mesma câmera e escala · pintura final pendente')
    for p in (256,512):
        d.line((p,0,p,768),fill='#e7e1df')
        d.line((0,p,768,p),fill='#e7e1df')
    sheet.save(BASE/f'comparativo-geometria-{rev}.png')
    print(BASE/f'comparativo-geometria-{rev}.png')


if __name__=='__main__':montar()
