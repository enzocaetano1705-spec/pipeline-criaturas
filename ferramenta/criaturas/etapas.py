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
    from criaturas import classificar, ficha, medir, preparar  # noqa: F401


def opcoes(nome: str, parser) -> None:
    """Opções extras de cada subcomando."""
    if nome == "preparar":
        parser.add_argument("--espelhar-lado", action="store_true",
                            help="espelha a vista lateral (use se a frente da criatura aponta para a direita)")
    if nome == "classificar":
        parser.add_argument("--registrar-escolha", metavar="'plano › nicho'",
                            help="registra a categoria escolhida pelo usuário (se diferente da sugestão 1)")
    if nome == "tudo":
        parser.add_argument("--ate", help="para depois desta etapa")
