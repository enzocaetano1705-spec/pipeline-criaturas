"""`criaturas tudo <pasta> --estagio eN [--ate etapa] [--folha-aprovada]`: roda as etapas em ordem.

Para quando uma etapa falha, quando falta um arquivo que só a IA escreve (checklist.json, leitura.json)
e nos pontos de parada de uma criatura real: categoria não confirmada (classificar) e folha de vistas
ainda não aprovada pelo usuário (use --folha-aprovada depois que ele aprovar).
"""

import argparse
import contextlib
import io
from pathlib import Path

from criaturas import relatorio
from criaturas.caminhos import pasta_estagio
from criaturas.classificar import _eh_teste
from criaturas.etapas import FUNCOES, etapa

ORDEM = ["ficha", "preparar", "classificar", "medir", "cubificar", "validar", "folha",
         "texturizar", "rig", "animar", "validar", "exportar"]
DA_IA = {"classificar": ("checklist.json", "skills/criaturas-3d/classificar.md"),
         "medir": ("leitura.json", "skills/criaturas-3d/ler.md")}


def _args(etapa_nome: str, base) -> argparse.Namespace:
    padrao = {"pasta": base.pasta, "estagio": base.estagio, "comando": etapa_nome, "espelhar_lado": False,
              "registrar_escolha": None, "motor": False, "olho_pintado": False, "so_base": False,
              "destino": None, "geckolib": False}
    return argparse.Namespace(**padrao)


@etapa("tudo")
def cmd_tudo(args) -> int:
    pasta = Path(args.pasta)
    destino = pasta_estagio(pasta.resolve().name, args.estagio)
    teste = _eh_teste(pasta)
    linhas = [f"tudo {pasta.resolve().name} {args.estagio}:"]
    ate = args.ate
    if ate and ate not in ORDEM:
        print(f"tudo: etapa desconhecida em --ate: {ate} (use uma de {', '.join(dict.fromkeys(ORDEM))})")
        return 1
    codigo = 0
    for nome in ORDEM:
        if nome in DA_IA and not (destino / DA_IA[nome][0]).exists():
            # classificar sem checklist ainda pode seguir se a categoria já está confirmada na ficha
            if nome == "classificar" and _categoria_confirmada(pasta, args.estagio):
                linhas.append("  classificar  pulado: categoria já confirmada na ficha")
                continue
            linhas.append(f"  PARE antes de {nome}: falta {DA_IA[nome][0]} — siga {DA_IA[nome][1]} e rode tudo de novo")
            codigo = 3
            break
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            r = FUNCOES[nome](_args(nome, args))
        primeira = (saida.getvalue().strip().splitlines() or [""])[0]
        linhas.append(f"  {nome:<11} {'ok' if r == 0 else f'código {r}'}  {primeira[:90]}")
        if r != 0:
            if r == 3:
                linhas.append("  PARE: categoria não confirmada; preencha 'Categoria confirmada' na ficha")
            codigo = r
            break
        if nome == "folha" and not teste and not args.folha_aprovada:
            linhas.append("  PARE: mostre a folha ao usuário; depois da aprovação rode tudo --folha-aprovada")
            codigo = 3
            break
        if nome == ate:
            break
    relatorio.imprimir(linhas)
    return codigo


def _categoria_confirmada(pasta: Path, estagio: str) -> bool:
    from criaturas.cubificar import contexto

    ctx = contexto(pasta.resolve().name, estagio)
    return bool(ctx["estagio"].get("categoria_confirmada"))
