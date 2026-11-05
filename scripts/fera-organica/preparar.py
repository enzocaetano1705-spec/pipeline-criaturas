from pathlib import Path
from hashlib import sha256
import json,shutil
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'modelos/fera-fera-agil-das-sombras/organico-v1'


def main():
    folder=BASE/'entrada';folder.mkdir(exist_ok=False)
    names={'conceito':'Fera-fera Ágil das Sombras.png','lado':'Rogue Tamanduá com Cauda Imponente.png',
           'costas':'Criatura Feral com Manto Vinho de Costas.png','frente':'Criatura Preguiça Guerreira em Pose Agressiva.png'}
    refs={}
    for view,name in names.items():
        src=Path.home()/'Downloads'/name
        dst=folder/(view+'.png');shutil.copy2(src,dst)
        with Image.open(src) as im:
            refs[view]={'origem':str(src),'arquivo':dst.name,'sha256':sha256(src.read_bytes()).hexdigest(),'tamanho':list(im.size)}
            im.convert('RGB').resize((round(im.width*min(1,768/max(im.size))),round(im.height*min(1,768/max(im.size))))).save(folder/(view+'-768.png'))
    brief={'nome':'Fera das Sombras — ensaio orgânico','estagio':'3 de 3','categoria':{'plano':'bípede com cauda','nicho':'outros'},'base':'preguiça gigante','arquetipo':'rogue',
           'referencias':refs,'precedencia':{'frente':'proporções/rosto/distribuição lateral','lado':'profundidade, inclinação do tronco, focinho e cauda','costas':'manto, bolsa, marcas dorsais','conceito':'identidade geral e hierarquia das formas'},
           'divergencias':['referências geradas não são projeções ortográficas perfeitamente concordantes','pose frontal abaixada e perfil mais alto: reconstruir repouso levemente agachado','comprimento das garras varia: preservar três garras longas por mão','tecido é um manto com uma ponta recortada longa, não asa','nomes dos arquivos não mudam a base confirmada de preguiça gigante'],
           'identidade':['focinho curto projetado e nariz escuro','olhos âmbar estreitos e máscara creme/marrom','juba voltada para trás sem orelhas inventadas','braços dominantes, três dedos/garras longas claras por mão','pernas compactas fletidas e três unhas escuras por pé','cauda grande peluda, larga no meio, ponta afinada e marca creme','manto vinho, broche/fivela dourados, faixas e bolsa na lateral esquerda'],
           'metodo':'escultura procedural por volumes/lofts próprios fundidos, mestre preservado, cópia reduzida para apresentação',
           'construcao':'somente Python executado por CLI; MCP só leitura/conferência','destino':'Roblox; importação/rig/pintura final fora desta revisão de geometria',
           'eixos_blender':{'cima':'+Z','frente':'-Y','direita':'+X'},'altura_tecnica_aproximada':3.8,
           'aprovacoes':{'categoria':True,'estagio':True,'imagens_entrada':True,'geometria':False,'pintura_final':False,'rig':False}}
    (folder/'briefing.json').write_text(json.dumps(brief,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Quatro referências preservadas, hashes e divergências registrados.')


if __name__=='__main__':main()
