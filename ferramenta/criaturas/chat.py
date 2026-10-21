"""Comandos do fluxo pelo chat: o usuário anexa imagens e pede ajustes em texto; a IA usa estes comandos.

  nova     cria docs/criaturas/<nome>/ a partir das imagens anexadas (conceito, frente, lado, costas) e preenche a ficha
  ver      folha (conceito + 4 vistas) do estado atual e a lista de peças, para conferir o que o usuário relatou
  quadro   as 4 vistas num instante de uma animação (para "a animação buga nesse frame")
  aplicar  aplica um lote de operações do bbmodel_edit escrito pela IA (correção por código) e valida
  adotar   registra as edições que o usuário fez à mão no Blockbench e passa a partir delas
"""

import argparse
import json
import re
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

from criaturas import bbmodelo, estado, folha, motor, relatorio, render
from criaturas.caminhos import RAIZ, chave, relativo
from criaturas.cubificar import contexto
from criaturas.etapas import etapa
from criaturas.relatorio import msg
from criaturas.validar import modelo_atual, verificacoes_proprias

CRIATURAS = RAIZ / "docs" / "criaturas"
VISTAS = ("conceito", "frente", "lado", "costas")


# ---------- nova ----------

def nome_valido(texto: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", chave(texto).replace(" ", "-"))).strip("-")


def escrever_ficha(pasta: Path, nome: str, estagios: dict[str, dict], destino: list[str], estilo: str) -> None:
    linhas = ["---", "tipo: ficha-criatura", f"nome: {nome}", "status: pronta-para-modelagem",
              f"destino: [{', '.join(destino)}]", f"estilo: {estilo}", f"estagios: {len(estagios)}", "---", "",
              f"# {nome.replace('-', ' ').title()}", "", "**Ideia em uma frase:** (criada pelo chat)", "",
              "**Motivos que atravessam a linhagem (2 ou 3 traços que nunca somem):**", ""]
    for eid, e in sorted(estagios.items()):
        n = eid[1:]
        imagens = ", ".join(f"{eid}-{v}.png" for v in VISTAS if (pasta / f"{eid}-{v}.png").exists())
        linhas += [f"## Estágio {n} — {e.get('nome') or nome}",
                   f"- **Estágio:** {e.get('estagio') or f'{n} de {max(len(estagios), 1)}'}",
                   f"- **Categoria (seu palpite):** {e.get('categoria') or ''}",
                   f"- **Categoria confirmada:** {e.get('confirmada') or ''}",
                   f"- **Altura no jogo (blocos):** {e.get('altura') or ''}",
                   f"- **Imagens:** {imagens}",
                   f"- **O que a imagem não mostra bem:** {e.get('nao_mostra') or ''}",
                   "- **Partes finas (viram planos):**", "- **Rosto:**", "- **Jeito de se mover:**", "",
                   f"![[{eid}-conceito.png]]", "", "### Prompt usado", "```text", e.get("prompt") or "", "```", ""]
    (pasta / "ficha.md").write_text("\n".join(linhas), encoding="utf-8")


def ler_estagios_da_ficha(pasta: Path) -> dict[str, dict]:
    """Os campos que `nova` preenche, lidos de volta (para acrescentar um estágio sem perder os outros)."""
    from criaturas.ficha import ler_ficha

    e = {}
    for est in ler_ficha(pasta)["estagios"]:
        cat = est.get("categoria_confirmada")
        e[est["id"]] = {"nome": est.get("nome"), "estagio": est.get("estagio"), "categoria": est.get("categoria_palpite"),
                        "confirmada": f"{cat['plano']} › {cat['nicho']}" if cat else "", "altura": est.get("altura_blocos"),
                        "nao_mostra": est.get("nao_mostra"), "prompt": est.get("prompt")}
    return e


@etapa("nova")
def cmd_nova(args) -> int:
    nome = nome_valido(args.nome)
    if not nome:
        print("nova: nome inválido")
        return 1
    pasta = CRIATURAS / nome
    if (pasta / "ficha.md").exists():
        texto = (pasta / "ficha.md").read_text(encoding="utf-8")
        if re.search(r"^status:\s*rascunho", texto, re.M):
            print(f"nova: {relativo(pasta)} existe e está em rascunho; não mexo (é do usuário)")
            return 1
    eid = args.estagio
    imagens = {v: getattr(args, v) for v in VISTAS if getattr(args, v)}
    if "conceito" not in imagens and "frente" not in imagens:
        print("nova: preciso pelo menos do conceito ou da frente (--conceito/--frente <arquivo>)")
        return 1
    pasta.mkdir(parents=True, exist_ok=True)
    for vista, origem in imagens.items():
        with Image.open(origem) as im:
            im = im.convert("RGBA")
            if max(im.size) > 1536:  # requisito: lado maior até 1536 px
                f = 1536 / max(im.size)
                im = im.resize((round(im.width * f), round(im.height * f)), Image.LANCZOS)
            im.save(pasta / f"{eid}-{vista}.png")
    estagios = ler_estagios_da_ficha(pasta) if (pasta / "ficha.md").exists() else {}
    atual = estagios.get(eid, {})
    for campo, valor in (("estagio", args.estagio_texto), ("categoria", args.categoria), ("confirmada", args.categoria),
                         ("altura", args.altura), ("prompt", args.prompt), ("nao_mostra", args.nao_mostra)):
        if valor:
            atual[campo] = valor
    estagios[eid] = atual
    escrever_ficha(pasta, nome, estagios, [d.strip() for d in args.destino.split(",")], args.estilo)
    linhas = [f"nova {nome} {eid}: {', '.join(imagens)} -> {relativo(pasta)}"]
    if "lado" not in imagens:
        linhas.append("  aviso: sem a vista de lado a profundidade fica estimada; peça a lateral ao usuário")
    if not args.categoria:
        linhas.append("  categoria ainda não confirmada: o pipeline vai pedir (classificar)")
    linhas.append(f"  próximo: uv run criaturas tudo {relativo(pasta)} --estagio {eid}")
    relatorio.imprimir(linhas)
    return 0


# ---------- ver ----------

def resumo_pecas(modelo: bbmodelo.Modelo, limite: int = 12) -> list[str]:
    mats = bbmodelo.matrizes_ossos(modelo)
    por_osso = {}
    for c in modelo.cubos:
        lo, hi = bbmodelo.caixa_mundo(modelo, c, mats)
        por_osso.setdefault(c.osso or "(sem osso)", []).append((c.nome, hi - lo))
    linhas = []
    for osso, cubos in list(por_osso.items())[:limite]:
        tams = "; ".join(f"{n.removesuffix('_cube')} {'×'.join(f'{v:g}' for v in t.round(1))}" for n, t in cubos[:3])
        pai = modelo.ossos[osso].pai if osso in modelo.ossos else None
        linhas.append(f"  {osso:<16} pai {pai or '-':<12} {tams}{' …' if len(cubos) > 3 else ''}")
    if len(por_osso) > limite:
        linhas.append(f"  … e mais {len(por_osso) - limite} ossos (lista completa: uv run criaturas ver … --tudo)")
    return linhas


@etapa("ver")
def cmd_ver(args) -> int:
    pasta = Path(args.pasta)
    nome = pasta.resolve().name
    ctx = contexto(nome, args.estagio)
    destino = ctx["destino"]
    arquivo = modelo_atual(destino, ctx["relatorio"])
    if arquivo is None:
        print("ver: ainda não há modelo (rode tudo)")
        return 1
    estado.adotar_e_avisar(destino, arquivo, nome, args.estagio, "ver")
    modelo = bbmodelo.ler(arquivo)
    cores = None
    if (destino / "plano-cubos.json").exists():
        cores = {c["nome"]: c["cor"] for c in relatorio.ler_json(destino / "plano-cubos.json")["cubos"] if c.get("cor")}
    imagem = folha.montar(folha.conceito_preparado(destino), folha.vistas_proprias(arquivo, cores), titulo=arquivo.stem)
    caminho = destino / "ver.png"
    imagem.save(caminho)
    erros, avisos, _ = verificacoes_proprias(modelo, None, None)
    e_motor, a_motor, mensagens = motor.resumo_validacao(motor.validar(arquivo))
    linhas = [f"ver {arquivo.name}: {len(modelo.cubos)} cubos, {len(modelo.ossos)} ossos, {len(modelo.locators)} locators, "
              f"{len(modelo.animacoes)} animações, textura {'sim' if modelo.textura else 'não'}",
              f"  imagem: {relativo(caminho)}  |  validação: {e_motor + len(erros)} erros, {a_motor} avisos"]
    linhas += [f"  ! {m[:110]}" for m in mensagens[:3]] + [f"  ! {e['texto'][:110]}" for e in erros[:2]]
    linhas += resumo_pecas(modelo, 40 if args.tudo else 10)
    ultimas = estado.ler_historico(destino, 2)
    for h in ultimas:
        linhas.append(f"  histórico {h['quando'][11:16]} {h['origem']}: {h['texto'][:70]}")
    relatorio.imprimir(linhas if not args.tudo else linhas[:60])
    return 0


# ---------- quadro ----------

VISTAS_MOTOR = {"frente": "front", "lado": "left", "costas": "back", "3/4": "three-quarter"}


@etapa("quadro")
def cmd_quadro(args) -> int:
    pasta = Path(args.pasta)
    nome = pasta.resolve().name
    ctx = contexto(nome, args.estagio)
    destino = ctx["destino"]
    arquivo = modelo_atual(destino, ctx["relatorio"])
    if arquivo is None:
        print("quadro: ainda não há modelo")
        return 1
    estado.adotar_e_avisar(destino, arquivo, nome, args.estagio, "quadro")
    modelo = bbmodelo.ler(arquivo)
    anim = next((a for a in modelo.animacoes if a["name"] == args.anim), None)
    if anim is None:
        print(f"quadro: não há animação {args.anim!r} (há: {', '.join(a['name'] for a in modelo.animacoes)})")
        return 1
    t = min(max(args.tempo, 0.0), float(anim["length"]))
    try:
        caminhos = motor.folha_de_contato(arquivo, clip=args.anim, time=t, views=list(VISTAS_MOTOR.values()))
        vistas = {n: Image.open(caminhos[m]).convert("RGB") for n, m in VISTAS_MOTOR.items() if m in caminhos}
        pose = motor.chamar("bbmodel_sample_pose", {"file": motor.relativo(arquivo), "animation": args.anim, "time": t})
    except motor.MotorErro as e:
        print(f"quadro: {e}")
        return 1
    tempo_txt = f"{t:.2f}".replace(".", "_")
    caminho = destino / f"quadro-{args.anim}-{tempo_txt}.png"
    folha.montar(vistas.get("3/4"), vistas, titulo=f"{args.anim} t={t:.2f}s").save(caminho)
    lo = (pose.get("bounds") or {}).get("min", [0, 0, 0])
    linhas = [f"quadro {args.anim} em {t:.2f} s de {float(anim['length']):.2f} s: {relativo(caminho)}",
              f"  ponto mais baixo y={lo[1]:.2f} (chão do repouso = 0)"]
    for b in (pose.get("bones") or [])[:10]:
        rot = b.get("rotation") or [0, 0, 0]
        pos = b.get("position") or [0, 0, 0]
        linhas.append(f"  {b['bone']:<16} rot {[round(x, 1) for x in rot]} pos {[round(x, 2) for x in pos]}")
    relatorio.imprimir(linhas)
    return 0


# ---------- aplicar ----------

@etapa("aplicar")
def cmd_aplicar(args) -> int:
    pasta = Path(args.pasta)
    nome = pasta.resolve().name
    ctx = contexto(nome, args.estagio)
    destino = ctx["destino"]
    arquivo = modelo_atual(destino, ctx["relatorio"])
    if arquivo is None:
        print("aplicar: ainda não há modelo")
        return 1
    estado.adotar_e_avisar(destino, arquivo, nome, args.estagio, "aplicar")
    dados = json.loads(Path(args.ops).read_text(encoding="utf-8"))
    operacoes = dados["operations"] if isinstance(dados, dict) else dados
    antes = bbmodelo.ler(arquivo)
    copia = destino / estado.PASTA_ESTADO / "antes-de-aplicar.bbmodel"
    copia.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(arquivo, copia)
    try:
        motor.editar(arquivo, operacoes)
        e_motor, a_motor, mensagens = motor.resumo_validacao(motor.validar(arquivo))
        e_anim, a_anim, m_anim = motor.resumo_validacao(motor.validar_animacoes(arquivo)) if bbmodelo.ler(arquivo).animacoes else (0, 0, [])
    except motor.MotorErro as e:
        shutil.copy(copia, arquivo)  # lotes acima de 450 operações não são atômicos: volta ao que era
        print(f"aplicar: {e} (nada foi mudado)")
        return 1
    dif = estado.diferenca(antes, bbmodelo.ler(arquivo))
    from datetime import datetime

    guardado = destino / "correcoes" / f"{datetime.now():%Y%m%d-%H%M%S}.json"
    guardado.parent.mkdir(parents=True, exist_ok=True)
    relatorio.gravar_json(guardado, {"motivo": args.motivo, "operations": operacoes})
    estado.historico(destino, "ia", args.motivo or "correção por código", dif["mudancas"], operacoes=len(operacoes),
                     lote=relativo(guardado))
    # o que a IA corrigiu a pedido do usuário também não deve ser regerado sem pedir
    rel = relatorio.ler_json(destino / "relatorio.json")
    prot = rel.get("protegido", {"animacoes": [], "textura": False})
    prot["animacoes"] = sorted(set(prot.get("animacoes", [])) | set(dif["animacoes"]))
    prot["textura"] = bool(prot.get("textura")) or dif["textura"]
    rel["protegido"] = prot
    relatorio.gravar_json(destino / "relatorio.json", rel)
    erros = [msg("motor", m) for m in mensagens + m_anim if m.startswith("[error]")]
    relatorio.registrar(destino, nome, args.estagio, "aplicar", not erros, erros=erros,
                        avisos=[msg("motor", m) for m in mensagens + m_anim if not m.startswith("[error]")],
                        resumo={"operacoes": len(operacoes), "motivo": args.motivo}, hashes=estado.depois_de_escrever(destino, arquivo))
    linhas = [f"aplicar {len(operacoes)} operação(ões) em {arquivo.name}: {args.motivo or ''}",
              f"  validação: {e_motor} erros e {a_motor} avisos na geometria; {e_anim} erros e {a_anim} avisos nas animações"]
    linhas += [f"  {m}" for m in dif["mudancas"][:12]]
    linhas += [f"  ! {m[:110]}" for m in (mensagens + m_anim)[:4]]
    linhas.append(f"  para desfazer: copie {relativo(copia)} por cima do modelo e rode adotar")
    relatorio.imprimir(linhas)
    return 0 if not erros else 1


# ---------- adotar ----------

@etapa("adotar")
def cmd_adotar(args) -> int:
    pasta = Path(args.pasta)
    nome = pasta.resolve().name
    ctx = contexto(nome, args.estagio)
    destino = ctx["destino"]
    arquivo = modelo_atual(destino, ctx["relatorio"])
    if arquivo is None:
        print("adotar: ainda não há modelo")
        return 1
    dif = estado.adotar(destino, arquivo, nome, args.estagio)
    if dif is None:
        print(f"adotar: {arquivo.name} está igual ao último estado do pipeline; nada a adotar")
        return 0
    linhas = [f"adotar {arquivo.name}: {len(dif['mudancas'])} mudança(s) feitas à mão"]
    linhas += [f"  {m}" for m in dif["mudancas"][:15]]
    prot = estado.protegido(destino)
    if prot.get("textura") or prot.get("animacoes"):
        linhas.append(f"  protegido contra regeneração: {'textura; ' if prot.get('textura') else ''}{', '.join(prot.get('animacoes', []))}")
    relatorio.imprimir(linhas)
    return 0


def opcoes(nome: str, parser: argparse.ArgumentParser) -> None:
    if nome == "nova":
        for v in VISTAS:
            parser.add_argument(f"--{v}", help=f"imagem da vista {v} (qualquer formato; vira PNG)")
        parser.add_argument("--estagio-texto", help="como na ficha: '1 de 3', '2 de 3'…")
        parser.add_argument("--categoria", help="'plano › nicho', se o usuário já disse")
        parser.add_argument("--altura", help="altura no jogo em blocos")
        parser.add_argument("--prompt", help="o prompt exato da imagem principal")
        parser.add_argument("--nao-mostra", help="o que a imagem não mostra bem")
        parser.add_argument("--destino", default="roblox", help="roblox, minecraft ou os dois")
        parser.add_argument("--estilo", default="cobblemon", choices=["cobblemon", "digimod"])
    elif nome == "ver":
        parser.add_argument("--tudo", action="store_true", help="lista todas as peças")
    elif nome == "quadro":
        parser.add_argument("--anim", required=True, help="nome da animação (idle, walk…)")
        parser.add_argument("--tempo", type=float, default=0.0, help="instante em segundos")
    elif nome == "aplicar":
        parser.add_argument("ops", help="arquivo JSON com a lista de operações do bbmodel_edit (ou {operations: [...]})")
        parser.add_argument("--motivo", help="o que o usuário pediu, em poucas palavras (vai para o histórico)")
