"""`criaturas preparar <pasta> --estagio eN`: imagens do estágio -> modelos/<nome>/eN/preparo/.

Por vista (conceito, frente, lado, costas), grava:
  <vista>-recorte.png   recortada na silhueta, com alfa, na escala comum (mesma altura de silhueta)
  <vista>-768.png       até 768 px, fundo branco
  <vista>-grade.png     até 768 px, com grade numerada (linhas a cada 1/32 da altura, rótulos 0–32)
  <vista>-mascara.png   máscara da silhueta (branco = criatura) na escala comum
e preparo.json com os números de cada vista (tamanho da célula, nº de células, espelhamento).

Coordenadas da grade: origem no canto superior esquerdo do recorte; 1 célula = 1/32 da altura
da silhueta; y = 32 é o chão. A vista "lado" deve mostrar a frente da criatura à esquerda;
se o conceito vier virado, use --espelhar-lado.
"""

from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from criaturas import relatorio
from criaturas.caminhos import pasta_estagio, relativo
from criaturas.etapas import etapa
from criaturas.relatorio import msg

VISTAS = ("conceito", "frente", "lado", "costas")
CELULAS = 32
LADO_768 = 768
MARGEM_GRADE = 34  # espaço para os rótulos, em px
ALTURA_COMUM = 1024  # altura da silhueta nos recortes, em px
TOLERANCIA_FUNDO = 28.0  # distância de cor (0–441) até a cor do fundo
MIN_COMPONENTE = 0.002  # componentes menores que isso (fração da silhueta) viram fundo
SATURACAO_SOMBRA = 0.12  # sombra de chão: cinza quase sem cor…
BRILHO_SOMBRA = 0.45  # …e não tão escura quanto o contorno preto do desenho


# ---------- máscara ----------

def _rotulos(mascara: np.ndarray) -> tuple[np.ndarray, int]:
    """Componentes conexos (4-vizinhança) de uma máscara booleana."""
    h, w = mascara.shape
    rot = np.zeros((h, w), np.int32)
    atual = 0
    ys, xs = np.nonzero(mascara)
    for y0, x0 in zip(ys, xs):
        if rot[y0, x0]:
            continue
        atual += 1
        rot[y0, x0] = atual
        fila = deque([(y0, x0)])
        while fila:
            y, x = fila.popleft()
            for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= ny < h and 0 <= nx < w and mascara[ny, nx] and not rot[ny, nx]:
                    rot[ny, nx] = atual
                    fila.append((ny, nx))
    return rot, atual


def _fundo_pelas_bordas(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Fundo liso: pixels parecidos com a cor das bordas e ligados a elas. Devolve (fundo, cor)."""
    borda = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]]).astype(float)
    cor = np.median(borda, axis=0)
    parecido = np.linalg.norm(rgb.astype(float) - cor, axis=2) < TOLERANCIA_FUNDO
    # sombra no chão: cinza de pouca saturação, mais escuro que o fundo, na parte de baixo e ligado a ele
    f = rgb.astype(float) / 255
    brilho, saturacao = f.max(2), f.max(2) - f.min(2)
    baixo = np.zeros(parecido.shape, bool)
    baixo[int(parecido.shape[0] * 0.6):] = True
    sombra = baixo & (saturacao < SATURACAO_SOMBRA) & (brilho > BRILHO_SOMBRA) & (brilho < cor.max() / 255)
    parecido |= sombra
    semente = np.zeros_like(parecido)
    semente[0, :], semente[-1, :], semente[:, 0], semente[:, -1] = parecido[0, :], parecido[-1, :], parecido[:, 0], parecido[:, -1]
    rot, _ = _rotulos(parecido)
    ligados = np.unique(rot[semente & parecido])
    ligados = ligados[ligados > 0]
    return np.isin(rot, ligados), cor


def mascara_da_imagem(im: Image.Image) -> tuple[np.ndarray, str]:
    """(máscara da criatura, método). Usa o alfa se houver transparência; senão o fundo liso das bordas."""
    rgba = np.asarray(im.convert("RGBA"))
    alfa = rgba[..., 3]
    if (alfa < 250).mean() > 0.01:
        mascara, metodo = alfa > 127, "alfa"
    else:
        fundo, _ = _fundo_pelas_bordas(rgba[..., :3])
        mascara, metodo = ~fundo, "bordas"
    # limpa respingos: tira componentes pequenos
    rot, n = _rotulos(mascara)
    if n > 1:
        tamanhos = np.bincount(rot.ravel())
        tamanhos[0] = 0
        minimo = max(16, int(MIN_COMPONENTE * tamanhos.sum()))
        mascara = np.isin(rot, np.nonzero(tamanhos >= minimo)[0])
    return mascara, metodo


# ---------- imagens de saída ----------

def _fonte(tamanho: int):
    for nome in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(nome, tamanho)
        except OSError:
            continue
    return ImageFont.load_default()


def com_fundo_branco(rgba: Image.Image) -> Image.Image:
    base = Image.new("RGB", rgba.size, (255, 255, 255))
    base.paste(rgba, mask=rgba.split()[3])
    return base


def reduzir(im: Image.Image, lado: int = LADO_768) -> Image.Image:
    escala = min(1.0, lado / max(im.size))
    if escala >= 1.0:
        return im.copy()
    return im.resize((max(1, round(im.width * escala)), max(1, round(im.height * escala))), Image.LANCZOS)


def imagem_com_grade(recorte: Image.Image, lado: int = LADO_768) -> tuple[Image.Image, float, float]:
    """Recorte com grade numerada. Devolve (imagem, px por célula, nº de células na largura)."""
    celulas_largura = CELULAS * recorte.width / recorte.height
    util = lado - MARGEM_GRADE - 4
    px = min(util / CELULAS, util / celulas_largura)
    w, h = max(1, round(celulas_largura * px)), max(1, round(CELULAS * px))
    conteudo = com_fundo_branco(recorte.resize((w, h), Image.LANCZOS))
    img = Image.new("RGB", (w + MARGEM_GRADE + 4, h + MARGEM_GRADE + 4), (255, 255, 255))
    img.paste(conteudo, (MARGEM_GRADE, MARGEM_GRADE))
    d = ImageDraw.Draw(img, "RGBA")
    fonte = _fonte(11)
    for i in range(CELULAS + 1):
        y = MARGEM_GRADE + i * px
        forte = i % 4 == 0
        d.line([(MARGEM_GRADE, y), (MARGEM_GRADE + w, y)], fill=(255, 40, 40, 150 if forte else 60), width=1)
        if i % 2 == 0:
            d.text((2, y - 6), f"{i:>2}", fill=(200, 0, 0), font=fonte)
    for j in range(int(np.floor(celulas_largura)) + 1):
        x = MARGEM_GRADE + j * px
        forte = j % 4 == 0
        d.line([(x, MARGEM_GRADE), (x, MARGEM_GRADE + h)], fill=(40, 40, 255, 150 if forte else 60), width=1)
        if j % 4 == 0:
            d.text((x - 5, 4 if j % 8 == 0 else 16), str(j), fill=(0, 0, 200), font=fonte)
    return img, px, celulas_largura


def preparar_vista(caminho: Path, espelhar: bool = False) -> dict:
    """Recorta uma imagem na silhueta e devolve as imagens e os números da vista."""
    with Image.open(caminho) as im:
        im = im.convert("RGBA")
    if espelhar:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    mascara, metodo = mascara_da_imagem(im)
    if not mascara.any():
        raise ValueError(f"{caminho.name}: não achei a criatura (fundo ocupa a imagem toda)")
    ys, xs = np.nonzero(mascara)
    caixa = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    rgba = np.asarray(im).copy()
    rgba[..., 3] = np.where(mascara, 255, 0)
    recorte = Image.fromarray(rgba).crop(caixa)
    fator = ALTURA_COMUM / recorte.height
    recorte = recorte.resize((max(1, round(recorte.width * fator)), ALTURA_COMUM), Image.LANCZOS)
    mascara_rec = np.asarray(recorte)[..., 3] > 127
    return {
        "recorte": recorte,
        "mascara": mascara_rec,
        "metodo_fundo": metodo,
        "tamanho_original": list(im.size),
        "caixa_original": list(caixa),
        "fator_escala": fator,
        "espelhada": espelhar,
        "fracao_borda": float(np.concatenate([mascara[0], mascara[-1], mascara[:, 0], mascara[:, -1]]).mean()),
    }


def preparar_estagio(pasta_imagens: Path, estagio: str, destino: Path, espelhar_lado: bool = False) -> dict:
    """Prepara todas as vistas existentes de um estágio. Devolve o conteúdo de preparo.json."""
    destino.mkdir(parents=True, exist_ok=True)
    info = {"estagio": estagio, "celulas_altura": CELULAS, "altura_silhueta_px": ALTURA_COMUM, "vistas": {}, "avisos": []}
    for vista in VISTAS:
        origem = Path(pasta_imagens) / f"{estagio}-{vista}.png"
        if not origem.exists():
            continue
        v = preparar_vista(origem, espelhar=espelhar_lado and vista == "lado")
        v["recorte"].save(destino / f"{vista}-recorte.png")
        Image.fromarray((v["mascara"] * 255).astype(np.uint8)).save(destino / f"{vista}-mascara.png")
        reduzir(com_fundo_branco(v["recorte"])).save(destino / f"{vista}-768.png")
        grade, px, celulas_largura = imagem_com_grade(v["recorte"])
        grade.save(destino / f"{vista}-grade.png")
        info["vistas"][vista] = {
            "origem": relativo(origem),
            "metodo_fundo": v["metodo_fundo"],
            "tamanho_original": v["tamanho_original"],
            "caixa_original": v["caixa_original"],
            "fator_escala": round(v["fator_escala"], 5),
            "espelhada": v["espelhada"],
            "celulas_largura": round(celulas_largura, 3),
            "px_por_celula_grade": round(px, 3),
            "margem_grade_px": MARGEM_GRADE,
            "recorte": f"{vista}-recorte.png",
            "grade": f"{vista}-grade.png",
            "img768": f"{vista}-768.png",
            "mascara": f"{vista}-mascara.png",
        }
        if v["fracao_borda"] > 0.02:
            info["avisos"].append(msg("silhueta_cortada", f"{vista}: a criatura encosta na borda da imagem (corpo cortado?)"))
        if v["metodo_fundo"] == "bordas" and v["fracao_borda"] > 0.5:
            info["avisos"].append(msg("fundo_nao_liso", f"{vista}: fundo não parece liso; confira a máscara"))
    if "frente" not in info["vistas"] and "conceito" not in info["vistas"]:
        raise ValueError(f"{estagio}: nenhuma imagem de frente ou conceito em {relativo(pasta_imagens)}")
    if "lado" not in info["vistas"]:
        info["avisos"].append(msg("sem_lado", f"{estagio}: sem vista lateral; a profundidade será estimada"))
    return info


@etapa("preparar")
def cmd_preparar(args) -> int:
    pasta = Path(args.pasta)
    nome = pasta.resolve().name
    destino_estagio = pasta_estagio(nome, args.estagio)
    destino = destino_estagio / "preparo"
    try:
        info = preparar_estagio(pasta, args.estagio, destino, espelhar_lado=args.espelhar_lado)
    except (ValueError, OSError) as e:
        relatorio.registrar(destino_estagio, nome, args.estagio, "preparar", False, erros=[msg("preparo", str(e))])
        print(f"preparar: {e}")
        return 1
    caminho = relatorio.gravar_json(destino / "preparo.json", info)
    relatorio.registrar(destino_estagio, nome, args.estagio, "preparar", True, avisos=info["avisos"],
                        arquivos=[relativo(caminho)], resumo={"vistas": list(info["vistas"])})
    linhas = [f"preparar {nome} {args.estagio}: {len(info['vistas'])} vista(s)"]
    for vista, v in info["vistas"].items():
        linhas.append(f"  {vista:<8} fundo por {v['metodo_fundo']:<6} {v['celulas_largura']:.1f} × 32 células"
                      + ("  (espelhada)" if v["espelhada"] else ""))
    linhas += relatorio.linhas_mensagens("Avisos", info["avisos"])
    linhas.append(f"grades: {relativo(destino)}/<vista>-grade.png")
    relatorio.imprimir(linhas)
    return 0
