"""Liga cada subcomando da CLI à função que o implementa.

Uma etapa ainda não implementada não aparece em FUNCOES e cai no esboço da CLI.
"""

FUNCOES: dict = {}


def etapa(nome: str):
    def registrar(func):
        FUNCOES[nome] = func
        return func
    return registrar


def opcoes(nome: str, parser) -> None:
    """Opções extras de cada subcomando."""
    if nome == "tudo":
        parser.add_argument("--ate", help="para depois desta etapa")
