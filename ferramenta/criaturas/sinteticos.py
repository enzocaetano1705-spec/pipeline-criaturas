"""Criaturas sintéticas com a verdade conhecida (ferramenta/testes/sinteticos/*.json).

Cada definição lista as partes centrais e as do lado esquerdo (-X), em unidades do modelo.
As do lado direito saem espelhadas em X. Uma parte vira um osso (pivô na junta) e um cubo.
"""

import json
from pathlib import Path

import numpy as np

from criaturas import motor, ops, relatorio
from criaturas.caminhos import MODELOS, RAIZ

PASTA = RAIZ / "ferramenta" / "testes" / "sinteticos"
SAIDA = MODELOS / "_sinteticos"
NOMES = ("quadrupede", "bipede-cauda", "alado")


def _espelhar_x(v):
    return [-v[0], v[1], v[2]]


def carregar(nome: str) -> dict:
    """Definição com as partes da direita já espelhadas e simetria/espelho preenchidos."""
    d = json.loads((PASTA / f"{nome}.json").read_text(encoding="utf-8"))
    partes = []
    for p in d["partes"]:
        p = dict(p)
        if p["id"].endswith("_left"):
            direita = dict(p)
            direita["id"] = p["id"][: -len("_left")] + "_right"
            if direita["pai"] and direita["pai"].endswith("_left"):
                direita["pai"] = direita["pai"][: -len("_left")] + "_right"
            a, b = _espelhar_x(p["from"]), _espelhar_x(p["to"])
            direita["from"] = [min(a[0], b[0]), a[1], a[2]]
            direita["to"] = [max(a[0], b[0]), b[1], b[2]]
            direita["pivo"] = _espelhar_x(p["pivo"])
            direita["simetria"], direita["espelho"] = "direita", p["id"]
            p["simetria"], p["espelho"] = "esquerda", direita["id"]
            partes += [p, direita]
        else:
            p.setdefault("simetria", "central")
            p.setdefault("espelho", None)
            partes.append(p)
    d["partes"] = partes
    return d


def plano_cubos(definicao: dict) -> dict:
    """Plano de cubos (contrato plano_cubos) de uma definição sintética."""
    cores = definicao["papeis_cor"]
    ossos = [{"nome": "root", "pai": None, "pivo": [0, 0, 0]}]
    cubos = []
    for p in definicao["partes"]:
        ossos.append({"nome": p["id"], "pai": p["pai"] or "root", "pivo": p["pivo"]})
        cubo = {"nome": f"{p['id']}_cube", "osso": p["id"], "parte": p["id"], "tipo": p["tipo"],
                "from": p["from"], "to": p["to"], "cor": cores[p["papel_cor"]]}
        if p["simetria"] == "direita":
            cubo["espelho_de"] = f"{p['espelho']}_cube"
            cubo["mirror_uv"] = True
        cubos.append(cubo)
    offsets, (largura, altura) = ops.distribuir_uv(cubos)
    for c in cubos:
        c["uv_offset"] = offsets[c["nome"]]
        c.pop("espelho_de", None)
    return {"nome": definicao["nome"], "formato": "bedrock", "resolucao": {"largura": largura, "altura": altura},
            "ossos": ossos, "cubos": cubos, "locators": []}


def cores_por_cubo(plano: dict) -> dict[str, str]:
    return {c["nome"]: c["cor"] for c in plano["cubos"] if c.get("cor")}


def renderizar_conceito(arquivo: Path, plano: dict, pasta: Path, lado_maior: int = 1024) -> dict[str, Path]:
    """Imagens de "conceito" da sintética (e1-frente/lado/costas/conceito.png), na mesma escala.

    Fazem o papel das imagens do usuário nos testes das Fases 2 e 3.
    """
    from criaturas import bbmodelo, render

    modelo = bbmodelo.ler(arquivo)
    lo, hi = bbmodelo.limites(modelo)
    maior = max(float(np.max(hi - lo)) * 1.15, 1.0)
    escala = (lado_maior - 2 * 48) / maior
    saidas = {}
    for vista, nome_arq in (("frente", "e1-frente.png"), ("lado", "e1-lado.png"), ("costas", "e1-costas.png"), ("3/4", "e1-conceito.png")):
        im, _, _, _ = render.renderizar(modelo, vista, escala=escala, margem=48, cores=cores_por_cubo(plano), limites=(lo, hi))
        pasta.mkdir(parents=True, exist_ok=True)
        im.save(pasta / nome_arq)
        saidas[vista] = pasta / nome_arq
    return saidas


def construir(nome: str, destino: Path | None = None) -> Path:
    """Gera plano-cubos.json, ops.json, verdade.json e o .bbmodel da sintética. Devolve o .bbmodel."""
    definicao = carregar(nome)
    pasta = Path(destino or SAIDA / nome / "e1")
    plano = plano_cubos(definicao)
    lote = ops.gerar_ops(plano)
    relatorio.gravar_json(pasta / "plano-cubos.json", plano, "plano_cubos")
    relatorio.gravar_json(pasta / "ops.json", {"operations": lote})
    relatorio.gravar_json(pasta / "verdade.json", definicao)
    arquivo = pasta / f"{nome}-e1.bbmodel"
    motor.criar(arquivo, nome, plano["resolucao"]["largura"], plano["resolucao"]["altura"])
    motor.editar(arquivo, lote)
    return arquivo


FICHAS = SAIDA / "fichas"
ESTAGIO_FICHA = {"inicial": "1 de 3", "meio": "2 de 3", "final": "3 de 3"}


def pasta_ficha(nome: str) -> Path:
    """Pasta que faz o papel de docs/criaturas/<nome>/ para a sintética (o pipeline grava em modelos/_sint-<nome>/)."""
    return FICHAS / f"_sint-{nome}"


def escrever_ficha(definicao: dict, pasta: Path, altura_blocos: float) -> Path:
    cat = definicao["categoria"]
    texto = f"""---
tipo: ficha-criatura
nome: sint-{definicao['nome']}
status: pronta-para-modelagem
destino: [roblox, minecraft]
estilo: cobblemon
estagios: 1
---

# Sintética {definicao['nome']}

**Ideia em uma frase:** {definicao['descricao']}

**Motivos que atravessam a linhagem (2 ou 3 traços que nunca somem):** cores de {', '.join(definicao['papeis_cor'])}

## Estágio 1 — {definicao['nome']}
- **Estágio:** {ESTAGIO_FICHA[definicao['estagio_tabela']]}
- **Categoria (seu palpite):** {cat['plano']} › {cat['nicho']}
- **Categoria confirmada:** {cat['plano']} › {cat['nicho']}
- **Altura no jogo (blocos):** {altura_blocos:.3f}
- **Imagens:** e1-conceito.png, e1-frente.png, e1-lado.png, e1-costas.png
- **O que a imagem não mostra bem:** nada; é sintética
- **Partes finas (viram planos):** {', '.join(p['id'] for p in definicao['partes'] if p['tipo'] == 'plano') or 'nenhuma'}
- **Rosto:** olhos em adesivo
- **Jeito de se mover:** padrão do plano de corpo

### Prompt usado
```text
synthetic {cat['plano']} {cat['nicho']} test creature, full body, plain white background
```
"""
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "ficha.md").write_text(texto, encoding="utf-8")
    return pasta / "ficha.md"


def construir_todas() -> list[str]:
    """Constrói as sintéticas: verdade em modelos/_sinteticos/<nome>/e1/ e ficha com imagens em fichas/_sint-<nome>/."""
    from criaturas import bbmodelo, render

    linhas = []
    for nome in NOMES:
        arquivo = construir(nome)
        pasta = arquivo.parent
        plano = json.loads((pasta / "plano-cubos.json").read_text(encoding="utf-8"))
        modelo = bbmodelo.ler(arquivo)
        render.folha(modelo, cores=cores_por_cubo(plano), titulo=nome).save(pasta / "vistas.png")
        ficha = pasta_ficha(nome)
        renderizar_conceito(arquivo, plano, ficha)
        lo, hi = bbmodelo.limites(modelo)
        escrever_ficha(carregar(nome), ficha, float(hi[1] - lo[1]) / 16)
        linhas.append(f"{nome}: {len(plano['cubos'])} cubos -> {pasta.relative_to(RAIZ).as_posix()}/vistas.png; ficha em {ficha.relative_to(RAIZ).as_posix()}")
    return linhas


if __name__ == "__main__":
    import sys

    for fluxo in (sys.stdout,):
        fluxo.reconfigure(encoding="utf-8", errors="replace")
    print("\n".join(construir_todas()))


# ---------- leitura simulada (teste de ida e volta da Fase 3) ----------

def leitura_da_verdade(nome: str, preparo: dict, ruido: float = 1.0, semente: int = 0,
                       min_px: int = 30, lado_maior: int = 1024) -> dict:
    """Simula a IA: caixa de cada parte em cada vista onde ela aparece, na grade do preparo, com ruído.

    Usa os mesmos parâmetros de renderizar_conceito, para casar com as imagens preparadas.
    Lista só as partes centrais e as do lado esquerdo (a IA deixa o espelho para o código).
    """
    from criaturas import bbmodelo, render

    definicao = carregar(nome)
    plano = plano_cubos(definicao)
    arquivo = SAIDA / nome / "e1" / f"{nome}-e1.bbmodel"
    modelo = bbmodelo.ler(arquivo)
    lo, hi = bbmodelo.limites(modelo)
    maior = max(float(np.max(hi - lo)) * 1.15, 1.0)
    escala = (lado_maior - 2 * 48) / maior
    rng = np.random.default_rng(semente)
    indice = {c.nome: i for i, c in enumerate(modelo.cubos)}
    caixas = {p["id"]: {} for p in definicao["partes"]}
    for vista in ("frente", "lado"):
        _, _, ids, _ = render.renderizar(modelo, vista, escala=escala, margem=48, cores=cores_por_cubo(plano), limites=(lo, hi))
        info = preparo["vistas"][vista]
        x_ref, y_ref = info["caixa_original"][:2]
        k = info["fator_escala"] / (preparo["altura_silhueta_px"] / 32)
        for p in definicao["partes"]:
            ys, xs = np.nonzero(ids == indice[f"{p['id']}_cube"])
            if len(xs) < min_px:
                continue
            caixa = np.array([xs.min() - x_ref, ys.min() - y_ref, xs.max() + 1 - x_ref, ys.max() + 1 - y_ref], float) * k
            caixa += rng.uniform(-ruido, ruido, 4)
            caixas[p["id"]][vista] = [round(float(v), 1) for v in caixa]
    partes = []
    for p in definicao["partes"]:
        if p["simetria"] == "direita" or not caixas[p["id"]]:
            continue
        partes.append({"id": p["id"], "pai": p["pai"], "tipo": p["tipo"], "simetria": p["simetria"],
                       "espelho": p.get("espelho"), "caixas": caixas[p["id"]], "papel_cor": p["papel_cor"]})
    return {"vistas": {"frente": {"imagem": "preparo/frente-grade.png"}, "lado": {"imagem": "preparo/lado-grade.png"}},
            "partes": partes, "papeis_cor": definicao["papeis_cor"], "incertezas": []}


def parte_visivel(parte: dict, pai: dict | None) -> tuple[list, list]:
    """Caixa da parte sem o trecho enterrado no pai (planos entram 1 unidade para não ficarem soltos).

    É a forma que uma imagem mostra; o encaixe no pai é trabalho do cubificador.
    """
    de, ate = list(parte["from"]), list(parte["to"])
    if parte["tipo"] != "plano" or pai is None:
        return de, ate
    for eixo in range(3):
        a, b, pa, pb = de[eixo], ate[eixo], pai["from"][eixo], pai["to"][eixo]
        if b - a <= 0:
            continue
        if pa <= a < pb < b:
            de[eixo] = pb
        elif a < pa < b <= pb:
            ate[eixo] = pa
    return de, ate


def comparar_com_verdade(nome: str, medidas: dict, tolerancia: float = 1.0, relativa: float = 0.10) -> dict:
    """Erro por parte e por eixo (tamanho e centro). Uma parte passa se todo erro ≤ 1 unidade ou ≤ 10%.

    A origem em x e z é arbitrária (o medir centra no corpo), então as duas são alinhadas pelo
    centro do body antes de comparar; y fica como está (chão em 0 nas duas).
    """
    verdade = {p["id"]: p for p in carregar(nome)["partes"]}
    medidas_por_id = {p["id"]: p for p in medidas["partes"]}
    desloc = [0.0, 0.0, 0.0]
    if "body" in medidas_por_id:
        for eixo in (0, 2):
            desloc[eixo] = ((verdade["body"]["from"][eixo] + verdade["body"]["to"][eixo])
                            - (medidas_por_id["body"]["from"][eixo] + medidas_por_id["body"]["to"][eixo])) / 2
    resultado = {}
    for pid, v in verdade.items():
        m = medidas_por_id.get(pid)
        if m is None:
            resultado[pid] = {"ok": False, "motivo": "faltou"}
            continue
        v_de, v_ate = parte_visivel(v, verdade.get(v["pai"]) if v["pai"] else None)
        erros, ok = [], True
        for eixo in range(3):
            tam_v = v_ate[eixo] - v_de[eixo]
            tam_m = m["to"][eixo] - m["from"][eixo]
            cen_v = (v_ate[eixo] + v_de[eixo]) / 2
            cen_m = (m["to"][eixo] + m["from"][eixo]) / 2 + desloc[eixo]
            limite = max(tolerancia, relativa * abs(tam_v))
            e_tam, e_cen = abs(tam_m - tam_v), abs(cen_m - cen_v)
            erros.append((round(e_tam, 2), round(e_cen, 2)))
            ok &= e_tam <= limite and e_cen <= limite
        resultado[pid] = {"ok": bool(ok), "erros": erros}
    return resultado


# ---------- linhagem sintética (Fase 7) ----------

# (escala do corpo, escala relativa da cabeça) por estágio: cresce ~1,7× e a cabeça perde peso
ESTAGIOS_LINHAGEM = {"e1": (1.0, 1.0), "e2": (2.0, 0.72), "e3": (3.6, 0.52)}
COBBLEMON = {"e1": "1º de 3", "e2": "2º de 3", "e3": "3º de 3"}


def _escalar(definicao: dict, corpo: float, cabeca: float) -> dict:
    """Escala a criatura inteira por `corpo` e a subárvore da cabeça por `cabeca` em torno do pivô dela."""
    d = json.loads(json.dumps(definicao))
    filhos = {}
    for p in d["partes"]:
        filhos.setdefault(p["pai"], []).append(p["id"])
    da_cabeca, fila = set(), ["head"]
    while fila:
        o = fila.pop()
        da_cabeca.add(o)
        fila += filhos.get(o, [])
    piv = np.array(next(p["pivo"] for p in d["partes"] if p["id"] == "head"), float) * corpo
    for p in d["partes"]:
        for k in ("from", "to", "pivo"):
            v = np.array(p[k], float) * corpo
            if p["id"] in da_cabeca:
                v = piv + (v - piv) * cabeca
            p[k] = [round(float(x)) if k != "pivo" else round(float(x), 2) for x in v]
        for eixo in range(3):  # tamanho mínimo 1 fora dos eixos finos
            if p["to"][eixo] - p["from"][eixo] == 0 and p["tipo"] == "volume":
                p["to"][eixo] = p["from"][eixo] + 1
    return d


def construir_linhagem(invertida: bool = False, base: str = "quadrupede") -> dict[str, Path]:
    """Três estágios da sintética em modelos/_sinteticos/_linhagem[-invertida]/eN/. Devolve {eN: .bbmodel}."""
    definicao = carregar(base)
    pasta = SAIDA / ("_linhagem-invertida" if invertida else "_linhagem")
    escalas = dict(ESTAGIOS_LINHAGEM)
    if invertida:  # o "final" é o menor e com a cabeça maior
        escalas = {"e1": ESTAGIOS_LINHAGEM["e3"], "e2": ESTAGIOS_LINHAGEM["e2"], "e3": ESTAGIOS_LINHAGEM["e1"]}
    saida = {}
    for eid, (corpo, cabeca) in escalas.items():
        d = _escalar(definicao, corpo, cabeca)
        d["nome"] = f"{base}-{eid}"
        saida[eid] = construir_definicao(d, pasta / eid)
    return saida


def construir_definicao(definicao: dict, pasta: Path) -> Path:
    plano = plano_cubos(definicao)
    lote = ops.gerar_ops(plano)
    arquivo = Path(pasta) / f"{definicao['nome']}.bbmodel"
    motor.criar(arquivo, definicao["nome"], plano["resolucao"]["largura"], plano["resolucao"]["altura"])
    motor.editar(arquivo, lote)
    return arquivo
