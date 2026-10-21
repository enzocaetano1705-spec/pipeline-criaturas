"""Liga cada subcomando da CLI à função que o implementa.

Uma etapa ainda não implementada não aparece em FUNCOES e cai no esboço da CLI.
"""

FUNCOES: dict = {}


def etapa(nome: str):
    def registrar(func):
        FUNCOES[nome] = func
        return func
    return registrar


def carregar() -> None:
    """Importa os módulos que registram etapas com @etapa."""
    from criaturas import animar, classificar, cubificar, ficha, folha, linhagem, medir, preparar, rig_etapa, texturizar, validar  # noqa: F401


def opcoes(nome: str, parser) -> None:
    """Opções extras de cada subcomando."""
    if nome == "preparar":
        parser.add_argument("--espelhar-lado", action="store_true",
                            help="espelha a vista lateral (use se a frente da criatura aponta para a direita)")
    if nome == "classificar":
        parser.add_argument("--registrar-escolha", metavar="'plano › nicho'",
                            help="registra a categoria escolhida pelo usuário (se diferente da sugestão 1)")
    if nome == "folha":
        parser.add_argument("--motor", action="store_true", help="vistas pelo render headless do motor (precisa de GPU)")
    if nome == "texturizar":
        parser.add_argument("--olho-pintado", action="store_true", help="estilo Digimod: tira os adesivos do olho e deixa o olho pintado na cabeça")
    if nome == "animar":
        parser.add_argument("--so-base", action="store_true", help="só idle, walk e blink")
    if nome == "tudo":
        parser.add_argument("--ate", help="para depois desta etapa")
