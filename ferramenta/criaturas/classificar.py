"""`criaturas classificar <pasta> --estagio eN`: checklist.json -> classificacao.json.

Pontua os 10 planos de corpo e os 19 nichos (mais "outros") com regras tiradas de
docs/pesquisa/categorias-criaturas.md (pistas visuais, marcas registradas e pares que se
confundem) e das faixas de referencia/medidas.json. Devolve até 3 sugestões (plano › nicho).

A IA preenche o checklist (skills/criaturas-3d/classificar.md); o código só pontua.
"""

import json
import math
import re
from datetime import datetime
from pathlib import Path

from criaturas import contratos, relatorio, tabelas
from criaturas.caminhos import REFERENCIA, chave, pasta_estagio, pasta_modelo, relativo
from criaturas.etapas import etapa
from criaturas.relatorio import msg

CORRECOES = REFERENCIA / "correcoes-classificacao.jsonl"
PESO_CERTEZA = {"visível": 1.0, "incerto": 0.6, "oculto": 0.3}

# palavras -> números (mesma escala das medidas)
QUALITATIVO = {
    "cabeca": {"pequena": 0.15, "media": 0.3, "grande": 0.45, "enorme": 0.65},
    "focinho": {"nenhum": None, "curto": 0.3, "medio": 0.55, "longo": 0.95, "bico": 0.64},
    "orelhas": {"nenhuma": None, "pequenas": 0.6, "medias": 0.8, "grandes": 1.05, "enormes": 1.45},
    "olhos": {"pequenos": 0.07, "medios": 0.12, "grandes": 0.18},
    "cauda": {"curta": 0.3, "media": 0.6, "longa": 0.9, "muito longa": 1.3},
    "pescoco": {"nenhum": 0, "curto": 1, "medio": 2, "longo": 3},
    "corpo": {"curto": 0.3, "medio": 0.55, "comprido": 0.85},
}


# ---------- checklist -> traços ----------

def _num(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def normalizar(checklist: dict) -> dict:
    """Traços numéricos e categóricos com o peso de cada um (pela certeza; fonte tabela pesa 0)."""
    itens = checklist["itens"]
    t, peso = {}, {}

    def item(nome):
        it = itens.get(nome)
        if not it:
            return None, 0.0
        w = 0.0 if it["fonte"] == "tabela" else PESO_CERTEZA[it["certeza"]]
        return it["valor"], w

    def qual(grupo, valor):
        return QUALITATIVO[grupo].get(chave(str(valor)), None) if isinstance(valor, str) else None

    def pôr(nome, valor, w):
        if valor is not None:
            t[nome], peso[nome] = valor, w

    v, w = item("postura")
    pôr("postura", chave(str(v)) if v is not None else None, w)

    v, w = item("pernas")
    if isinstance(v, dict):
        pôr("pernas", _num(v.get("n")), w)
        pôr("perna_alt", _num(v.get("frac_alt")), w)
    else:
        pôr("pernas", _num(v), w)

    v, w = item("bracos")
    pôr("bracos", _num(v.get("n") if isinstance(v, dict) else v), w)

    v, w = item("asas")
    if isinstance(v, dict):
        pôr("asas_pares", _num(v.get("pares")), w)
        pôr("envergadura_alt", _num(v.get("envergadura_alt")), w)
        if v.get("tipo"):
            pôr("asas_tipo", chave(v["tipo"]), w)
    else:
        pôr("asas_pares", _num(v), w)

    v, w = item("cauda")
    if isinstance(v, dict):
        pôr("tem_cauda", 1.0, w)
        comp = _num(v.get("comprimento_alt"))
        pôr("cauda_compr_alt", comp if comp is not None else qual("cauda", v.get("comprimento")), w)
        if v.get("grossura"):
            pôr("cauda_grossura", chave(v["grossura"]), w)
        pôr("cauda_segmentos", _num(v.get("segmentos")), w)
        if v.get("leque"):
            pôr("cauda_leque", 1.0, w)
    elif isinstance(v, str):
        pôr("tem_cauda", 0.0 if chave(v) in ("nenhuma", "nao", "sem") else 1.0, w)
        pôr("cauda_compr_alt", qual("cauda", v), w)
    elif v is not None:
        pôr("tem_cauda", 1.0 if _num(v) else 0.0, w)

    v, w = item("nadadeiras")
    pôr("nadadeiras", _num(v.get("n") if isinstance(v, dict) else v), w)

    v, w = item("pescoco")
    pôr("pescoco_segmentos", _num(v.get("segmentos")) if isinstance(v, dict) else qual("pescoco", v), w)

    v, w = item("cabeca")
    pôr("cranio_alt", _num(v.get("frac_alt")) if isinstance(v, dict) else qual("cabeca", v), w)

    v, w = item("focinho")
    if isinstance(v, dict):
        pôr("focinho_cranio", _num(v.get("razao_cranio")), w)
        if v.get("bico"):
            pôr("bico", 1.0, w)
    elif isinstance(v, str):
        pôr("focinho_cranio", qual("focinho", v), w)
        if chave(v) == "bico":
            pôr("bico", 1.0, w)

    v, w = item("orelhas")
    pôr("orelha_cranio", _num(v.get("razao_cranio")) if isinstance(v, dict) else qual("orelhas", v), w)

    v, w = item("olhos")
    pôr("olho_alt", _num(v.get("frac_alt")) if isinstance(v, dict) else qual("olhos", v), w)

    v, w = item("cobertura")
    if v:
        pôr("cobertura", chave(v if isinstance(v, str) else " ".join(v)), w)

    v, w = item("extras")
    if v:
        lista = v if isinstance(v, list) else [v]
        t["extras"] = {chave(str(x)) for x in lista}
        peso["extras"] = w

    v, w = item("corpo")
    pôr("corpo_compr_alt", _num(v.get("compr_alt")) if isinstance(v, dict) else qual("corpo", v), w)

    if t.get("bico"):
        t.setdefault("extras", set()).add("bico")
        peso.setdefault("extras", peso.get("bico", 1.0))
    return {"tracos": t, "peso": peso}


# ---------- regras ----------

def _tem(t, *palavras):
    extras = t.get("extras", set())
    return any(any(p in e for e in extras) for p in palavras)


def _cobertura(t, *tipos):
    c = t.get("cobertura", "")
    return any(x in c for x in tipos)


def regras_plano(t: dict) -> dict[str, list[tuple[float, str]]]:
    """Pontos (log) e motivo de cada plano de corpo. Positivo apoia, negativo afasta."""
    pernas, bracos = t.get("pernas"), t.get("bracos", 0) or 0
    asas, nad = t.get("asas_pares", 0) or 0, t.get("nadadeiras", 0) or 0
    cauda = t.get("cauda_compr_alt")
    sem_cauda = t.get("tem_cauda") == 0.0
    postura = t.get("postura", "")
    bipede = "bipede" in postura or (pernas == 2 and "quadrupede" not in postura)
    cabeca = t.get("cranio_alt")
    r = {p: [] for p in tabelas.planos()}

    q = r["quadrúpede"]
    if pernas == 4:
        q.append((2.0, "4 patas"))
    if "quadrupede" in postura:
        q.append((1.5, "coluna horizontal"))
    if pernas is not None and pernas != 4:
        q.append((-2.0, f"{pernas:g} pernas"))

    b = r["bípede com cauda"]
    h = r["humanoide"]
    if bipede and pernas == 2:
        b.append((2.0, "de pé em 2 pernas"))
        h.append((2.0, "de pé em 2 pernas"))
    elif pernas is not None and pernas != 2:
        b.append((-2.0, f"{pernas:g} pernas"))
        h.append((-2.0, f"{pernas:g} pernas"))
    if cauda is not None and cauda >= 0.25:
        b.append((2.0, f"cauda longa ({cauda:.2f}× a altura)"))
        h.append((-1.5 if cauda >= 0.4 else -0.5, "tem cauda"))
    elif sem_cauda or (cauda is not None and cauda < 0.25):
        b.append((-2.0, "sem cauda longa"))
        h.append((1.5, "sem cauda ou cauda pequena"))
    if bracos >= 2:
        h.append((1.0, "braços"))
        b.append((0.3, "braços"))

    a = r["alado"]
    if asas == 1:
        a.append((3.0, "um par de asas"))
    elif asas >= 2:
        a.append((1.0, f"{asas:g} pares de asas"))
    elif asas == 0 and "asas_pares" in t:
        a.append((-3.0, "sem asas"))
    if (t.get("envergadura_alt") or 0) >= 1.5:
        a.append((1.0, f"envergadura {t['envergadura_alt']:.1f}× a altura"))

    s = r["serpentiforme"]
    if pernas == 0 and nad == 0:
        s.append((1.5, "sem pernas"))
        if (t.get("corpo_compr_alt") or 0) >= 0.8 or (cauda or 0) >= 0.8:
            s.append((2.0, "corpo longo"))
    elif pernas:
        s.append((-2.5, "tem pernas"))
    if "rastejante" in postura:
        s.append((1.5, "rasteja"))

    p = r["peixe"]
    if nad >= 1:
        p.append((2.5, f"{nad:g} nadadeira(s)"))
        if pernas == 0:
            p.append((1.5, "sem pernas"))
    else:
        p.append((-2.0, "sem nadadeiras"))
    if "nadando" in postura:
        p.append((1.5, "nada"))

    i = r["inseto"]
    if pernas is not None and pernas >= 6:
        i.append((3.5, f"{pernas:g} patas"))
    if asas >= 2:
        i.append((2.5, f"{asas:g} pares de asas"))
    if t.get("asas_tipo") == "inseto":
        i.append((1.5, "asas de inseto"))
    if _tem(t, "antena"):
        i.append((1.0, "antenas"))
    if _tem(t, "carapaca") or _cobertura(t, "carapaca"):
        i.append((0.5, "carapaça"))
    if not i:
        i.append((-2.0, "menos de 6 patas"))

    c = r["cabeça-corpo"]
    if cabeca is not None:
        if cabeca >= 0.6:
            c.append((3.0, f"cabeça {cabeca:.0%} da altura"))
        elif cabeca >= 0.5:
            c.append((1.5, f"cabeça {cabeca:.0%} da altura"))
        elif cabeca < 0.35:
            c.append((-2.0, "cabeça pequena"))
    if (t.get("perna_alt") or 1) <= 0.15 or pernas == 0:
        c.append((0.8, "membros mínimos"))
    if _tem(t, "flutua"):
        c.append((0.5, "flutua"))

    tm = r["tentáculos/multípede"]
    if _tem(t, "tentac"):
        tm.append((3.5, "tentáculos"))
    if pernas is not None and pernas >= 8:
        tm.append((2.0, f"{pernas:g} patas"))
    if not tm:
        tm.append((-2.0, "sem tentáculos"))

    m = r["múltiplos corpos"]
    if _tem(t, "multiplas cabecas", "multiplos corpos", "varias cabecas", "enxame", "trio"):
        m.append((4.0, "várias cabeças ou corpos"))
    else:
        m.append((-2.5, "um corpo só"))
    return r


def regras_nicho_categoricas(t: dict) -> dict[str, list[tuple[float, str]]]:
    """Marcas registradas de cada nicho (tabela 'Regras por nicho' e 'Pares que se confundem')."""
    pernas, bracos = t.get("pernas"), t.get("bracos", 0) or 0
    asas = t.get("asas_pares", 0) or 0
    grossa = t.get("cauda_grossura")
    cauda = t.get("cauda_compr_alt")
    r = {n: [] for n in tabelas.nichos()}

    def add(n, pts, motivo, cond=True):
        if cond:
            r[n].append((pts, motivo))

    pelo, escama, pena = _cobertura(t, "pelo"), _cobertura(t, "escama"), _cobertura(t, "pena")
    add("dragão", 0.8, "escamas", escama)
    add("dragão", 1.0, "asas", asas >= 1)
    add("dragão", 0.8, "chifres", _tem(t, "chifre"))
    add("dragão", 0.5, "chamas", _tem(t, "chama", "fogo"))
    add("dinossauroide/kaiju", 0.6, "escamas", escama)
    add("dinossauroide/kaiju", -1.0, "asas", asas >= 1)
    add("réptil/anfíbio", 0.6, "escamas ou pele lisa", escama or _cobertura(t, "pele", "gosma"))
    add("réptil/anfíbio", 0.4, "olhos grandes", (t.get("olho_alt") or 0) >= 0.15)
    add("canídeo", 0.8, "pelo", pelo)
    add("canídeo", 0.6, "cauda cheia", grossa in ("grossa", "media"))
    add("canídeo", 0.4, "4 patas", pernas == 4)
    add("felino", 0.8, "pelo", pelo)
    add("felino", 1.2, "bigodes", _tem(t, "bigode"))
    add("felino", 0.6, "cauda fina", grossa == "fina")
    add("felino", -0.6, "cauda cheia", grossa == "grossa")
    add("ungulado", 2.0, "cascos", _tem(t, "casco"))
    add("ungulado", 0.6, "chifres", _tem(t, "chifre"))
    add("ungulado", 0.4, "pelo", pelo)
    add("roedor/pequeno mamífero", 0.6, "pelo", pelo)
    add("urso", 0.6, "pelo", pelo)
    add("urso", 0.6, "cauda mínima", cauda is not None and cauda <= 0.2)
    add("primata", 0.4, "pelo", pelo)
    add("primata", 0.6, "braços", bracos >= 2)
    add("ave", 2.0, "penas", pena)
    add("ave", 2.0, "bico", _tem(t, "bico"))
    add("ave", 1.0, "cauda em leque", bool(t.get("cauda_leque")))
    add("ave", 1.0, "asas de penas", t.get("asas_tipo") == "penas")
    add("ave", -1.5, "asas de membrana", t.get("asas_tipo") == "membrana")
    add("morcego", 2.0, "asas de membrana", t.get("asas_tipo") == "membrana")
    add("morcego", 0.4, "pelo", pelo)
    add("morcego", -1.5, "penas ou bico", pena or _tem(t, "bico"))
    add("peixe/aquático", 2.5, "nadadeiras", (t.get("nadadeiras") or 0) >= 1)
    add("peixe/aquático", 0.4, "escamas", escama)
    cabeca_domina = (t.get("cranio_alt") or 0) >= 0.5
    # sem pernas só aponta para serpente se o corpo não é a própria cabeça (bola de pelo, blob)
    add("serpente/verme", 1.5, "sem pernas", pernas == 0 and not t.get("nadadeiras") and not cabeca_domina)
    add("serpente/verme", -1.5, "o corpo é a cabeça", cabeca_domina)
    add("serpente/verme", 0.4, "escamas", escama)
    add("serpente/verme", -1.5, "nadadeiras", (t.get("nadadeiras") or 0) >= 1)
    add("inseto/artrópode", 2.0, "antenas", _tem(t, "antena"))
    add("inseto/artrópode", 1.0, "carapaça", _tem(t, "carapaca") or _cobertura(t, "carapaca"))
    add("inseto/artrópode", 2.0, "6+ patas", pernas is not None and pernas >= 6)
    add("inseto/artrópode", 1.5, "asas de inseto", t.get("asas_tipo") == "inseto")
    add("amorfo/fantasma", 1.5, "gosma", _cobertura(t, "gosma"))
    add("amorfo/fantasma", 1.5, "flutua", _tem(t, "flutua"))
    add("planta", 2.5, "cobertura de planta", _cobertura(t, "planta"))
    add("planta", 2.0, "folhas", _tem(t, "folha", "flor"))
    add("mineral/objeto", 2.5, "pedra ou metal", _cobertura(t, "pedra", "metal", "cristal"))
    add("humanoide", 0.6, "pele", _cobertura(t, "pele"))
    add("humanoide", 1.0, "de pé com braços", bracos >= 2 and pernas == 2)
    add("fada/fofo", 0.5, "flutua", _tem(t, "flutua"))
    add("fada/fofo", 1.0, "cabeça e olhos grandes", cabeca_domina and (t.get("olho_alt") or 0) >= 0.13)
    add("outros", -1.0, "categoria de reserva")
    # quem tem marca registrada própria e não mostrou nenhuma perde um pouco
    for n, marca in (("ave", pena or _tem(t, "bico")), ("peixe/aquático", (t.get("nadadeiras") or 0) >= 1),
                     ("planta", _cobertura(t, "planta") or _tem(t, "folha")),
                     ("mineral/objeto", _cobertura(t, "pedra", "metal")), ("inseto/artrópode", pernas is not None and pernas >= 6 or _tem(t, "antena"))):
        add(n, -1.5, "sem a marca registrada", not marca)
    return r


MEDIDAS_NICHO = {
    "focinho_cranio": "focinho/crânio", "orelha_cranio": "orelha/crânio", "cauda_compr_alt": "cauda",
    "cauda_segmentos": "segmentos da cauda", "pescoco_segmentos": "pescoço", "envergadura_alt": "envergadura",
    "perna_alt": "pernas", "corpo_compr_alt": "corpo",
}
INTEIROS = {"cauda_segmentos", "pescoco_segmentos"}


def _semelhanca(x: float, faixa, medida: str) -> float:
    """Log-semelhança (≤ 0) de x com a faixa [p25, mediana, p75]."""
    p25, med, p75 = faixa
    if medida in INTEIROS:
        sigma = max((p75 - p25) / 1.349, 0.75)
        z = (x - med) / sigma
    else:
        if x <= 0 or med <= 0:
            return -2.0 if x > 0.05 else 0.0
        sigma = max(math.log(max(p75, 1e-3) / max(p25, 1e-3)) / 1.349, 0.18)
        z = (math.log(x) - math.log(med)) / sigma
    return max(-0.5 * z * z, -4.0)


def regras_nicho_numericas(t: dict, peso: dict) -> dict[str, list[tuple[float, str]]]:
    r = {}
    for nicho in tabelas.nichos():
        f = tabelas.dados()["nichos"][nicho]
        lista = []
        for medida, rotulo in MEDIDAS_NICHO.items():
            x, faixa = t.get(medida), f.get(medida)
            if x is None or not isinstance(faixa, list):
                continue
            # +0,5 para quem bate com a faixa: vira traço que justifica; longe da faixa fica negativo
            s = (_semelhanca(x, faixa, medida) + 0.5) * peso.get(medida, 1.0)
            lista.append((s, f"{rotulo} {x:g} (típico {faixa[1]:g})" if s > 0 else f"{rotulo} {x:g} longe de {faixa[1]:g}"))
        r[nicho] = lista
    return r


def compatibilidade(plano: str, nicho: str) -> float:
    comuns = tabelas.dados()["nichos"][nicho].get("planos_mais_comuns", [])
    if plano in comuns:
        return (1.0, 0.6, 0.3)[comuns.index(plano)]
    return -1.2


# ---------- pontuação ----------

def _soma(lista, peso=1.0):
    return sum(p for p, _ in lista) * peso


def _motivos(lista, n=3):
    return [m for p, m in sorted(lista, key=lambda x: -x[0]) if p > 0][:n]


def pontuar(checklist: dict, n: int = 3) -> list[dict]:
    """Até n sugestões {plano, nicho, confianca, tracos} ordenadas pela confiança."""
    norm = normalizar(checklist)
    t, peso = norm["tracos"], norm["peso"]
    rp = regras_plano(t)
    rn_cat = regras_nicho_categoricas(t)
    rn_num = regras_nicho_numericas(t, peso)
    pares = []
    for plano, lp in rp.items():
        sp = _soma(lp)
        for nicho in tabelas.nichos():
            sn = _soma(rn_cat[nicho]) + _soma(rn_num[nicho])
            total = sp + sn + compatibilidade(plano, nicho)
            pares.append((total, plano, nicho, (lp, rn_cat[nicho] + rn_num[nicho])))
    maximo = max(p[0] for p in pares)
    soma_exp = sum(math.exp(p[0] - maximo) for p in pares)
    pares.sort(key=lambda p: -p[0])
    saida = []
    for total, plano, nicho, (m_plano, m_nicho) in pares[:n]:
        # 1 traço que sustenta o plano + 2 que sustentam o nicho (os que separam vizinhos)
        tracos = _motivos(m_plano, 1) + [m for m in _motivos(m_nicho, 3) if m not in _motivos(m_plano, 1)][:2]
        saida.append({"plano": plano, "nicho": nicho, "confianca": round(math.exp(total - maximo) / soma_exp, 3),
                      "tracos": tracos})
    # renormaliza entre as sugestões mostradas, para os % somarem 100
    s = sum(x["confianca"] for x in saida) or 1.0
    for x in saida:
        x["confianca"] = round(x["confianca"] / s, 3)
    return saida


def estagio_aparente(checklist: dict, plano: str) -> dict:
    """Estágio pelo tamanho da cabeça e do olho, comparados com as medianas do plano por estágio."""
    t = normalizar(checklist)["tracos"]
    cab, olho = t.get("cranio_alt"), t.get("olho_alt")
    melhor, dist_melhor = None, math.inf
    for est in ("inicial", "meio", "final"):
        d, usados = 0.0, 0
        for x, medida in ((cab, "cranio_alt"), (olho, "olho_alt")):
            m = tabelas.mediana(plano, est, medida)
            if x and m:
                d += abs(math.log(x / m))
                usados += 1
        if usados and d < dist_melhor:
            melhor, dist_melhor = est, d
    return {"estagio_tabela": melhor or "inicial", "cabeca_alt": cab, "olho_alt": olho,
            "nota": "pela cabeça e pelo olho" if melhor else "sem cabeça nem olho medidos; assumido inicial"}


def classificar(checklist: dict) -> dict:
    contratos.validar("checklist", checklist)
    sugestoes = pontuar(checklist)
    return {"sugestoes": sugestoes, "estagio_aparente": estagio_aparente(checklist, sugestoes[0]["plano"]),
            "conflitos": checklist.get("conflitos", []), "categoria_usada": None}


# ---------- ficha e correções ----------

SECAO = "## Classificação sugerida"


def secao_ficha(estagio: str, classificacao: dict) -> str:
    linhas = [f"### {estagio}"]
    for i, s in enumerate(classificacao["sugestoes"], 1):
        linhas.append(f"{i}. {s['plano']} › {s['nicho']} — {s['confianca']:.0%}: {', '.join(s['tracos']) or 'sem traços fortes'}")
    ea = classificacao["estagio_aparente"]
    linhas.append(f"Estágio aparente: {ea['estagio_tabela']} ({ea['nota']})")
    if classificacao.get("conflitos"):
        linhas.append("Conflitos imagem × prompt (vale a imagem): " + "; ".join(c["item"] for c in classificacao["conflitos"]))
    linhas.append("Escolha 1, 2, 3 ou outra categoria e preencha **Categoria confirmada** no estágio.")
    return "\n".join(linhas)


def atualizar_ficha(ficha: Path, estagio: str, classificacao: dict) -> None:
    """Acrescenta (ou troca) a subseção do estágio em '## Classificação sugerida', no fim da ficha."""
    texto = ficha.read_text(encoding="utf-8")
    bloco = secao_ficha(estagio, classificacao)
    if SECAO not in texto:
        texto = texto.rstrip() + f"\n\n{SECAO}\n<!-- gerado por criaturas classificar -->\n\n{bloco}\n"
    else:
        antes, depois = texto.split(SECAO, 1)
        padrao = re.compile(rf"^### {estagio}\n.*?(?=^### |\Z)", re.S | re.M)
        depois = padrao.sub(bloco + "\n\n", depois) if padrao.search(depois) else depois.rstrip() + f"\n\n{bloco}\n"
        texto = antes + SECAO + depois
    ficha.write_text(texto.rstrip() + "\n", encoding="utf-8")


def registrar_correcao(criatura: str, estagio: str, checklist: dict, classificacao: dict, escolha: dict,
                       arquivo: Path = CORRECOES) -> bool:
    """Anexa a escolha do usuário se ela difere da sugestão 1. Devolve True se registrou."""
    s1 = classificacao["sugestoes"][0]
    if (s1["plano"], s1["nicho"]) == (escolha["plano"], escolha["nicho"]):
        return False
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    linha = {"quando": datetime.now().isoformat(timespec="seconds"), "criatura": criatura, "estagio": estagio,
             "escolha": escolha, "sugestoes": classificacao["sugestoes"], "checklist": checklist}
    with arquivo.open("a", encoding="utf-8") as f:
        f.write(json.dumps(linha, ensure_ascii=False) + "\n")
    return True


def _eh_teste(pasta: Path) -> bool:
    partes = [p.lower() for p in pasta.resolve().parts]
    return pasta.resolve().name.startswith("_sint-") or "_testes" in partes


@etapa("classificar")
def cmd_classificar(args) -> int:
    from criaturas.ficha import _categoria

    pasta = Path(args.pasta)
    nome = pasta.resolve().name
    destino = pasta_estagio(nome, args.estagio)
    arq_check = destino / "checklist.json"
    if not arq_check.exists():
        print(f"classificar: falta {relativo(arq_check)}.")
        print("Preencha-o seguindo skills/criaturas-3d/classificar.md (a IA olha a imagem com grade) e rode de novo.")
        relatorio.registrar(destino, nome, args.estagio, "classificar", False, erros=[msg("sem_checklist", "falta checklist.json")])
        return 1
    checklist = relatorio.ler_json(arq_check)
    try:
        resultado = classificar(checklist)
    except contratos.ContratoInvalido as e:
        print(f"classificar: checklist inválido — {e}")
        return 1

    entrada_arq = pasta_modelo(nome) / "entrada.json"
    entrada = relatorio.ler_json(entrada_arq) if entrada_arq.exists() else None
    est = next((e for e in (entrada or {}).get("estagios", []) if e["id"] == args.estagio), None)
    confirmada = est.get("categoria_confirmada") if est else None

    if args.registrar_escolha:
        try:
            escolha = _categoria(args.registrar_escolha)
        except (ValueError, KeyError) as e:
            print(f"classificar: escolha inválida — {e}")
            return 1
        registrou = registrar_correcao(nome, args.estagio, checklist, resultado, escolha)
        print("correção registrada em referencia/correcoes-classificacao.jsonl" if registrou
              else "escolha igual à sugestão 1; nada a registrar")
        confirmada = confirmada or escolha

    s1 = resultado["sugestoes"][0]
    avisos = []
    if confirmada:
        resultado["categoria_usada"] = {**confirmada, "fonte": "confirmada"}
        if (confirmada["plano"], confirmada["nicho"]) != (s1["plano"], s1["nicho"]) and not args.registrar_escolha:
            avisos.append(msg("difere_sugestao", f"categoria confirmada ({confirmada['plano']} › {confirmada['nicho']}) difere da sugestão 1"))
    elif _eh_teste(pasta):
        resultado["categoria_usada"] = {"plano": s1["plano"], "nicho": s1["nicho"], "fonte": "sugestao_1"}

    if est and est.get("estagio_tabela") and est["estagio_tabela"] != resultado["estagio_aparente"]["estagio_tabela"]:
        avisos.append(msg("estagio_aparente", f"a ficha diz {est['estagio_tabela']}, a cabeça e o olho parecem {resultado['estagio_aparente']['estagio_tabela']}"))

    caminho = relatorio.gravar_json(destino / "classificacao.json", resultado, "classificacao")
    ficha = pasta / "ficha.md"
    if ficha.exists() and entrada and entrada.get("status") != "rascunho":
        atualizar_ficha(ficha, args.estagio, resultado)

    parar = resultado["categoria_usada"] is None
    relatorio.registrar(destino, nome, args.estagio, "classificar", not parar, avisos=avisos, arquivos=[relativo(caminho)],
                        resumo={"sugestao_1": f"{s1['plano']} › {s1['nicho']}", "parar": parar})
    linhas = [f"classificar {nome} {args.estagio}:"]
    for i, s in enumerate(resultado["sugestoes"], 1):
        linhas.append(f"  {i}. {s['plano']} › {s['nicho']} — {s['confianca']:.0%}: {', '.join(s['tracos'])}")
    ea = resultado["estagio_aparente"]
    linhas.append(f"  estágio aparente: {ea['estagio_tabela']} ({ea['nota']})")
    linhas += relatorio.linhas_mensagens("Avisos", avisos)
    if parar:
        linhas.append("PARE: preencha 'Categoria confirmada' na ficha (1, 2, 3 ou outra) antes de seguir.")
    else:
        cu = resultado["categoria_usada"]
        linhas.append(f"categoria usada: {cu['plano']} › {cu['nicho']} ({cu['fonte']})")
    relatorio.imprimir(linhas)
    return 3 if parar else 0
