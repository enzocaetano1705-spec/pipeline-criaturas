"""`criaturas folha <pasta> --estagio eN`: as 4 vistas do modelo ao lado do conceito, numa imagem de até 768 px.

Layout 768 × 384: o conceito à esquerda (384 × 384) e frente, lado, costas e 3/4 à direita (2 × 2 de 192).
Usa o renderizador próprio; com --motor, as vistas vêm do render headless do motor (precisa de GPU).
A cor vem da textura do .bbmodel, se houver; senão das cores do plano de cubos.
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from criaturas import bbmodelo, motor, relatorio, render
from criaturas.caminhos import relativo
from criaturas.cubificar import contexto
from criaturas.etapas import etapa
from criaturas.relatorio import msg
from criaturas.validar import modelo_atual

LARGURA, ALTURA = 768, 384
VISTAS_MOTOR = {"frente": "front", "lado": "left", "costas": "back", "3/4": "three-quarter"}


def _caber(im: Image.Image, lado: int) -> Image.Image:
    escala = min(lado / im.width, lado / im.height)
    return im.resize((max(1, round(im.width * escala)), max(1, round(im.height * escala))), Image.LANCZOS)


def montar(conceito: Image.Image | None, vistas: dict[str, Image.Image], titulo: str = "") -> Image.Image:
    folha = Image.new("RGB", (LARGURA, ALTURA), render.FUNDO)
    d = ImageDraw.Draw(folha)
    if conceito is not None:
        c = _caber(conceito.convert("RGB"), ALTURA - 24)
        folha.paste(c, ((ALTURA - c.width) // 2, 12 + (ALTURA - 24 - c.height) // 2))
        d.text((6, 4), "conceito", fill=(80, 84, 96))
    q = ALTURA // 2
    for k, nome in enumerate(render.FOLHA):
        if nome not in vistas:
            continue
        x, y = ALTURA + (k % 2) * q, (k // 2) * q
        v = _caber(vistas[nome], q - 16)
        folha.paste(v, (x + (q - v.width) // 2, y + 12 + (q - 16 - v.height) // 2))
        d.text((x + 4, y + 2), nome, fill=(80, 84, 96))
    d.line([(ALTURA, 0), (ALTURA, ALTURA)], fill=(200, 204, 212))
    d.line([(ALTURA, q), (LARGURA, q)], fill=(214, 216, 222))
    d.line([(ALTURA + q, 0), (ALTURA + q, ALTURA)], fill=(214, 216, 222))
    if titulo:
        d.text((6, ALTURA - 14), titulo, fill=(80, 84, 96))
    return folha


def vistas_proprias(arquivo: Path, cores: dict | None) -> dict[str, Image.Image]:
    modelo = bbmodelo.ler(arquivo)
    lo, hi = bbmodelo.limites(modelo)
    escala = 360 / max(float(np.max(hi - lo)), 1.0)
    return {v: render.renderizar(modelo, v, escala=escala, cores=cores, limites=(lo, hi))[0] for v in render.FOLHA}


def vistas_do_motor(arquivo: Path) -> dict[str, Image.Image]:
    caminhos = motor.folha_de_contato(arquivo)
    return {nosso: Image.open(caminhos[deles]).convert("RGB") for nosso, deles in VISTAS_MOTOR.items() if deles in caminhos}


def conceito_preparado(destino: Path) -> Image.Image | None:
    for vista in ("conceito", "frente"):
        arq = destino / "preparo" / f"{vista}-768.png"
        if arq.exists():
            return Image.open(arq)
    return None


@etapa("folha")
def cmd_folha(args) -> int:
    pasta = Path(args.pasta)
    nome = pasta.resolve().name
    ctx = contexto(nome, args.estagio)
    destino = ctx["destino"]
    arquivo = modelo_atual(destino, ctx["relatorio"])
    if arquivo is None:
        print("folha: nenhum .bbmodel (rode cubificar antes)")
        return 1
    plano_arq = destino / "plano-cubos.json"
    cores = None
    if plano_arq.exists():
        cores = {c["nome"]: c["cor"] for c in relatorio.ler_json(plano_arq)["cubos"] if c.get("cor")}
    avisos = []
    try:
        vistas = vistas_do_motor(arquivo) if args.motor else vistas_proprias(arquivo, cores)
    except motor.MotorErro as e:
        avisos.append(msg("render_motor", f"render do motor falhou ({e}); usando o próprio"))
        vistas = vistas_proprias(arquivo, cores)
    folha = montar(conceito_preparado(destino), vistas, titulo=arquivo.stem)
    caminho = destino / "folha.png"
    folha.save(caminho)
    relatorio.registrar(destino, nome, args.estagio, "folha", True, avisos=avisos, arquivos=[relativo(caminho)],
                        resumo={"tamanho": list(folha.size), "render": "motor" if args.motor and not avisos else "próprio"})
    linhas = [f"folha: {relativo(caminho)} ({folha.width}×{folha.height})"]
    linhas += relatorio.linhas_mensagens("Avisos", avisos)
    from criaturas.classificar import _eh_teste

    if not _eh_teste(pasta):
        linhas.append("PARE (criatura real): mostre a folha ao usuário e espere a aprovação antes de texturizar.")
    relatorio.imprimir(linhas)
    return 0
