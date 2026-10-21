"""Linha de comando `criaturas`. Cada subcomando imprime até 20 linhas e grava JSON em modelos/<nome>/."""

import argparse
import sys
from pathlib import Path

from criaturas import __version__, relatorio, tabelas
from criaturas.caminhos import pasta_estagio, pasta_modelo, relativo

# (subcomando, ajuda). A ordem é a do pipeline.
ETAPAS = [
    ("ficha", "lê a ficha.md, confere as imagens e grava modelos/<nome>/entrada.json"),
    ("preparar", "recorta as imagens do estágio e gera as versões de 768 px com grade"),
    ("classificar", "pontua plano de corpo e nicho a partir do checklist"),
    ("medir", "transforma a leitura em caixas 3D medidas na silhueta"),
    ("cubificar", "leitura + medidas -> plano de cubos -> ops -> .bbmodel"),
    ("texturizar", "pinta a textura a partir das vistas"),
    ("rig", "posiciona os locators padrão"),
    ("animar", "gera idle, walk e blink (e as outras do plano de corpo)"),
    ("validar", "bbmodel_validate e as verificações próprias"),
    ("folha", "folha de vistas do modelo ao lado do conceito"),
    ("linhagem", "compara os estágios com a assinatura de evolução"),
    ("exportar", "exporta para Roblox (.glb) e Minecraft (Bedrock)"),
    ("tudo", "roda as etapas em ordem, parando nos pontos de parada"),
]
SEM_ESTAGIO = {"ficha", "linhagem"}

# fluxo pelo chat (ferramenta/criaturas/chat.py)
CHAT = [
    ("nova", "cria a criatura em docs/criaturas/<nome>/ a partir das imagens anexadas no chat"),
    ("ver", "folha e lista de peças do modelo atual (para conferir um problema relatado)"),
    ("quadro", "as 4 vistas num instante de uma animação"),
    ("aplicar", "aplica um lote de operações (correção por código) e valida"),
    ("adotar", "registra as edições feitas à mão no Blockbench e segue a partir delas"),
]


def _saida_utf8() -> None:
    # No Windows o console usa cp1252 por padrão e os acentos saem quebrados.
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8", errors="replace")


def nome_da_pasta(pasta: str) -> str:
    return Path(pasta).resolve().name


def ainda_nao_implementado(args) -> int:
    """Esboço comum: avisa e registra no relatório, sem fingir que fez o trabalho."""
    nome = nome_da_pasta(args.pasta)
    estagio = getattr(args, "estagio", None)
    destino = pasta_estagio(nome, estagio) if estagio else pasta_modelo(nome)
    caminho = relatorio.registrar(destino, nome, estagio, args.comando, False,
                                  erros=[relatorio.msg("nao_implementado", f"{args.comando}: ainda não implementado")])
    relatorio.imprimir([f"{args.comando}: ainda não implementado.", f"relatório: {relativo(caminho)}"])
    return 2


def cmd_medidas(args) -> int:
    try:
        f = tabelas.faixas(args.categoria, args.estagio)
    except tabelas.CategoriaDesconhecida:
        print(f"categoria desconhecida: {args.categoria}")
        print("planos: " + ", ".join(tabelas.planos()))
        print("nichos: " + ", ".join(tabelas.nichos()))
        return 1
    except KeyError as e:
        print(str(e).strip("'\""))
        return 1
    linhas = []
    titulo = f"{f['tipo']} › {f['nome']}" + (f" — {f['estagio']}" if f["estagio"] else " — todos os estágios")
    if f.get("poucos_dados"):
        geral = tabelas.faixas(args.categoria)
        linhas.append(f"{titulo}: poucos dados (n={f['n']}); mostrando a faixa geral (n={geral['n']}).")
        f = geral
    else:
        linhas.append(f"{titulo} (n={f['n']})   [p25 / mediana / p75]")
    for medida, rotulo in tabelas.ROTULOS.items():
        if medida in f:
            linhas.append(f"  {rotulo:<22} {tabelas.formatar(f[medida], medida)}")
    extras = [f"{rotulo} {tabelas.formatar(f[k], k)}" for k, rotulo in (("voa_frac", "voam"), ("nada_frac", "nadam")) if k in f]
    if extras:
        linhas.append("  " + "; ".join(extras))
    relatorio.imprimir(linhas)
    return 0


def montar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="criaturas",
        description="Pipeline de criaturas 3D: conceito -> modelo cubificado, textura, rig e animações.",
    )
    parser.add_argument("--version", action="version", version=f"criaturas {__version__}")
    sub = parser.add_subparsers(dest="comando", metavar="<comando>")

    from criaturas import etapas

    etapas.carregar()

    for nome, ajuda in ETAPAS:
        p = sub.add_parser(nome, help=ajuda, description=ajuda)
        p.add_argument("pasta", help="pasta da criatura (ex.: docs/criaturas/raposa-de-fogo)")
        if nome not in SEM_ESTAGIO:
            p.add_argument("--estagio", default="e1", help="estágio (e1, e2…); padrão e1")
        etapas.opcoes(nome, p)
        p.set_defaults(func=etapas.FUNCOES.get(nome, ainda_nao_implementado))

    from criaturas import chat

    for nome, ajuda in CHAT:
        p = sub.add_parser(nome, help=ajuda, description=ajuda)
        if nome == "nova":
            p.add_argument("nome", help="nome da criatura (vira minúsculas, sem acento, com hífen)")
        else:
            p.add_argument("pasta", help="pasta da criatura (ex.: docs/criaturas/raposa-de-fogo)")
        p.add_argument("--estagio", default="e1", help="estágio (e1, e2…); padrão e1")
        chat.opcoes(nome, p)
        p.set_defaults(func=etapas.FUNCOES[nome])

    from criaturas import referencias

    p = sub.add_parser("referencias", help="busca e inspeciona modelos reais da biblioteca externa",
                       description="Consulta referências por estrutura, estágio, UV e animações sem alterar os modelos.")
    referencias.opcoes(p)
    p.set_defaults(func=referencias.cmd_referencias)

    from criaturas import comparar_referencias

    p = sub.add_parser("comparar-referencias", help="compara proporções e UV por partes mapeadas em dois .bbmodel",
                       description="Diagnóstico por analogia ou reconstrução; não aprova qualidade artística.")
    p.add_argument("caso", help="JSON com modo, âncora e seletores de referência/candidato")
    p.add_argument("--saida", required=True, help="relatório agregado JSON; preserva os modelos")
    p.set_defaults(func=comparar_referencias.cmd_comparar)

    p = sub.add_parser("medidas", help="faixas de referencia/medidas.json para um plano ou nicho",
                       description="Faixas [p25, mediana, p75] de um plano de corpo ou nicho, opcionalmente de um estágio.")
    p.add_argument("categoria", help="plano de corpo ou nicho (ex.: quadrúpede, dragão, roedor)")
    p.add_argument("estagio", nargs="?", help="inicial, meio, final, único, lendário ou como na ficha (2 de 3)")
    p.set_defaults(func=cmd_medidas)
    return parser


def main(argv: list[str] | None = None) -> int:
    _saida_utf8()
    parser = montar_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
