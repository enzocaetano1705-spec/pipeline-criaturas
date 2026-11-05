from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import sys

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'modelos/fera-fera-agil-das-sombras/organico-v1'
REV=sys.argv[1] if len(sys.argv)>1 else 'r03'


def main():
    folder=BASE/REV
    sheet=Image.new('RGB',(768,768),'#f6f4f1');d=ImageDraw.Draw(sheet)
    font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',14)
    small=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',11)
    def tile(file,x,y,w,h,title):
        im=Image.open(folder/file).convert('RGBA');im.thumbnail((w-10,h-29),Image.Resampling.LANCZOS)
        bg=Image.new('RGBA',im.size,'#f6f4f1');bg.alpha_composite(im)
        sheet.paste(bg.convert('RGB'),(x+(w-im.width)//2,y+25+(h-29-im.height)//2))
        d.text((x+8,y+5),title,font=font if w>200 else small,fill='#443a34')
    tile('3-4.png',0,0,384,384,'Orgânico · Blender · cores de estudo')
    tile('cinza.png',384,0,384,384,'Superfície cinza · mesma geometria')
    for i,(file,title) in enumerate((('frente.png','Frente'),('lado.png','Perfil'),('costas.png','Costas'),('rosto.png','Rosto / volume'))):
        tile(file,i*192,384,192,384,title)
    d.line((384,0,384,384),fill='#dbd5cf');d.line((0,384,768,384),fill='#dbd5cf')
    sheet.save(folder/'folha-geometria.png')
    print('Folha de revisão: '+str(folder/'folha-geometria.png'))


if __name__=='__main__':main()
