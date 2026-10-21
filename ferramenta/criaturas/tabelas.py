"""Leitura de referencia/medidas.json: faixas [p25, mediana, p75] por categoria e estágio."""

import json
from functools import cache

from criaturas.caminhos import MEDIDAS_JSON, chave

ESTAGIOS_TABELA = ("inicial", "meio", "final", "único", "lendário")

# Estágio como escrito na ficha -> (por_estagio das tabelas, estagios.cobblemon). Ver docs/convencoes.md.
ESTAGIO_FICHA = {
    "1 de 3": ("inicial", "1º de 3"),
    "2 de 3": ("meio", "2º de 3"),
    "3 de 3": ("final", "3º de 3"),
    "1 de 2": ("inicial", "1º de 2"),
    "2 de 2": ("final", "2º de 2"),
    "1 de 1": ("único", "único"),
    "unico": ("único", "único"),
    "bebe": ("inicial", "bebê"),
    "bebe pre estagio": ("inicial", "bebê"),
    "lendario": ("lendário", "lendário/mítico"),
    "lendario mitico": ("lendário", "lendário/mítico"),
}

# Nome legível de cada medida, na ordem em que aparece no resumo.
ROTULOS = {
    "altura_blocos": "altura (blocos)",
    "cabeca_vol": "cabeça (% volume)",
    "cranio_alt": "crânio (% altura)",
    "olho_alt": "olho (% altura)",
    "perna_alt": "perna (% altura)",
    "corpo_compr_alt": "corpo compr./altura",
    "cauda_compr_alt": "cauda compr./altura",
    "cauda_vol": "cauda (% volume)",
    "cauda_segmentos": "segmentos da cauda",
    "pescoco_segmentos": "segmentos do pescoço",
    "envergadura_alt": "envergadura/altura",
    "focinho_cranio": "focinho/crânio",
    "orelha_cranio": "orelha/crânio",
    "cubos": "cubos",
    "planos_frac": "planos (% peças)",
    "andar_s": "ciclo do walk (s)",
}
PERCENTUAIS = {"cabeca_vol", "cranio_alt", "olho_alt", "perna_alt", "cauda_vol", "planos_frac"}


class CategoriaDesconhecida(KeyError):
    pass


@cache
def dados() -> dict:
    return json.loads(MEDIDAS_JSON.read_text(encoding="utf-8"))


def planos() -> list[str]:
    return list(dados()["planos_de_corpo"])


def nichos() -> list[str]:
    return list(dados()["nichos"])


def resolver_categoria(nome: str, tipo: str | None = None) -> tuple[str, str]:
    """('plano' ou 'nicho', nome oficial) a partir de um nome escrito de qualquer jeito.

    `tipo` restringe a busca a 'plano' ou 'nicho' (humanoide existe nos dois).
    """
    procurado = chave(nome)
    grupos = [(t, g) for t, g in (("plano", "planos_de_corpo"), ("nicho", "nichos")) if tipo in (None, t)]
    for t, grupo in grupos:
        for oficial in dados()[grupo]:
            if chave(oficial) == procurado:
                return t, oficial
    # prefixo único ("roedor" -> "roedor/pequeno mamífero", "tentaculos" -> "tentáculos/multípede")
    candidatos = [(t, o) for t, g in grupos for o in dados()[g] if procurado and chave(o).startswith(procurado)]
    if len(candidatos) == 1:
        return candidatos[0]
    raise CategoriaDesconhecida(nome)


def resolver_estagio(texto: str | None) -> str | None:
    """Nome do estágio nas tabelas (inicial, meio, final, único, lendário) ou None."""
    if texto is None or not str(texto).strip():
        return None
    k = chave(str(texto))
    for e in ESTAGIOS_TABELA:
        if chave(e) == k:
            return e
    if k in ESTAGIO_FICHA:
        return ESTAGIO_FICHA[k][0]
    for prefixo, (tabela, _) in ESTAGIO_FICHA.items():
        if k.startswith(prefixo):
            return tabela
    raise KeyError(f"estágio desconhecido: {texto}")


def estagio_cobblemon(texto: str) -> str | None:
    k = chave(texto)
    for prefixo, (_, cob) in ESTAGIO_FICHA.items():
        if k == prefixo or k.startswith(prefixo):
            return cob
    return None


def faixas(categoria: str, estagio: str | None = None) -> dict:
    """Faixas da categoria, do estágio se pedido. Inclui 'n', 'tipo', 'nome' e 'estagio'."""
    tipo, oficial = resolver_categoria(categoria)
    grupo = dados()["planos_de_corpo" if tipo == "plano" else "nichos"][oficial]
    base = {k: v for k, v in grupo.items() if k != "por_estagio"}
    est = resolver_estagio(estagio)
    if est:
        sub = grupo.get("por_estagio", {}).get(est)
        if sub is None:
            raise KeyError(f"{oficial} não tem dados para o estágio {est}")
        base = dict(sub)
    base.update({"tipo": tipo, "nome": oficial, "estagio": est})
    return base


def mediana(categoria: str, estagio: str | None, medida: str, padrao=None):
    """Mediana de uma medida; cai para a faixa geral da categoria se o estágio não tiver."""
    for est in (estagio, None):
        try:
            f = faixas(categoria, est)
        except KeyError:
            continue
        v = f.get(medida)
        if isinstance(v, list) and len(v) == 3:
            return v[1]
    return padrao


def formatar(valor, medida: str) -> str:
    if isinstance(valor, list) and len(valor) == 3:
        if medida in PERCENTUAIS:
            return " / ".join(f"{x * 100:.0f}%" for x in valor)
        return " / ".join(f"{x:g}" for x in valor)
    if isinstance(valor, float) and medida.endswith("_frac"):
        return f"{valor * 100:.0f}%"
    return str(valor)
