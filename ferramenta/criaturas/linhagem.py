"""`criaturas linhagem <pasta>`: compara os estágios da linhagem com a assinatura de evolução.

7.1 Por par de estágios seguidos (eN -> eN+1), mede no .bbmodel de cada um a altura, a fração de
    volume da cabeça, o olho, o nº de cubos, o ciclo do walk e a postura, e compara com
    referencia/medidas.json (assinatura_evolucao): OK, aviso ou erro. Grava uma imagem com os
    estágios lado a lado na mesma escala.
7.2 Motivos que atravessam a linhagem: sobreposição de paleta entre estágios, aviso abaixo de 50%.
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from criaturas import bbmodelo, cores, relatorio, render, tabelas
from criaturas.caminhos import pasta_estagio, pasta_modelo, relativo
from criaturas.etapas import etapa
from criaturas.relatorio import msg

SOBREPOSICAO_MIN = 0.5
DELTA_E_MESMA_COR = 15.0
NICHOS_CABECA_FIXA = ("peixe/aquático", "planta", "amorfo/fantasma")


def metricas(modelo: bbmodelo.Modelo) -> dict:
    """Medidas do estágio, no mesmo sentido das de medidas.json (frações da altura e do volume)."""
    mats = bbmodelo.matrizes_ossos(modelo)
    lo, hi = bbmodelo.limites(modelo, mats)
    altura = float(hi[1] - lo[1])
    volume = {c.nome: float(np.prod(np.maximum(c.ate - c.de, 0))) for c in modelo.cubos}
    total = sum(volume.values()) or 1.0

    def descendentes(osso):
        saida, fila = set(), [osso]
        while fila:
            o = fila.pop()
            saida.add(o)
            fila += modelo.filhos(o)
        return saida

    cabeca = None
    if "head" in modelo.ossos:
        ossos = descendentes("head")
        cabeca = sum(v for c, v in volume.items() if modelo.cubo(c).osso in ossos) / total
    olhos = [c for c in modelo.cubos if c.nome.startswith("eye_")]
    olho = float(np.mean([c.ate[1] - c.de[1] for c in olhos])) / altura if olhos else None
    andar = next((float(a["length"]) for a in modelo.animacoes if a.get("name") == "walk"), None)
    comprimento = float(hi[2] - lo[2])
    return {"altura": round(altura, 3), "altura_blocos": round(altura / 16, 3), "cabeca_vol": None if cabeca is None else round(cabeca, 4),
            "olho_alt": None if olho is None else round(olho, 4), "cubos": len(modelo.cubos), "andar_s": andar,
            "ereto": round(altura / max(comprimento, 1e-6), 3)}


def chave_par(estagio_a: str | None, estagio_b: str | None) -> str | None:
    """'1º de 3 → 2º de 3' (assinatura_evolucao.cobblemon) a partir dos estágios cobblemon dos dois lados."""
    if not estagio_a or not estagio_b:
        return None
    pares = tabelas.dados()["assinatura_evolucao"]["cobblemon"]
    k = f"{estagio_a} → {estagio_b}"
    if k in pares:
        return k
    if estagio_a == "bebê":
        return "bebê → básico"
    return None


def comparar(a: dict, b: dict, par: str | None, nicho: str | None = None) -> dict:
    """Razões e diferenças de a -> b, com o veredito de cada uma e o geral."""
    regras = tabelas.dados()["assinatura_evolucao"]["regras_validacao_sugeridas"]
    faixa = tabelas.dados()["assinatura_evolucao"]["cobblemon"].get(par, {}) if par else {}
    itens, erros, avisos = {}, [], []

    def alvo(medida):
        f = faixa.get(medida, {}).get("p25_med_p75")
        return [f[0], f[2]] if f else regras.get(medida, {}).get("alvo")

    altura_x = b["altura"] / a["altura"]
    itens["altura_x"] = round(altura_x, 3)
    r = regras["altura_x"]
    if altura_x <= r["erro_se_menor_ou_igual"]:
        erros.append(msg("altura", f"altura ×{altura_x:.2f}: o estágio seguinte não cresce"))
    elif altura_x < r["aviso_se_menor_que"]:
        avisos.append(msg("altura", f"altura ×{altura_x:.2f} (cresce pouco; abaixo de ×{r['aviso_se_menor_que']})"))
    elif alvo("altura_x") and not alvo("altura_x")[0] <= altura_x <= alvo("altura_x")[1] * 1.15:
        avisos.append(msg("altura", f"altura ×{altura_x:.2f} fora do típico {alvo('altura_x')}"))

    cubos_x = b["cubos"] / max(a["cubos"], 1)
    itens["cubos_x"] = round(cubos_x, 3)
    if cubos_x < 1.0:
        avisos.append(msg("cubos", f"cubos ×{cubos_x:.2f}: o estágio seguinte tem menos peças"))

    if a["cabeca_vol"] is not None and b["cabeca_vol"] is not None:
        delta = b["cabeca_vol"] - a["cabeca_vol"]
        itens["cabeca_vol_delta"] = round(delta, 4)
        if delta > regras["cabeca_vol_delta"]["aviso_se_maior_que"] and nicho not in NICHOS_CABECA_FIXA:
            avisos.append(msg("cabeca", f"a cabeça cresce ({delta:+.0%} do volume); normal é encolher {alvo('cabeca_vol_delta')}"))
    if a["olho_alt"] is not None and b["olho_alt"] is not None:
        delta = b["olho_alt"] - a["olho_alt"]
        itens["olho_alt_delta"] = round(delta, 4)
        if delta > regras["olho_alt_delta"]["aviso_se_maior_que"]:
            avisos.append(msg("olho", f"o olho cresce ({delta:+.1%} da altura)"))
    if a["andar_s"] and b["andar_s"]:
        x = b["andar_s"] / a["andar_s"]
        itens["andar_s_x"] = round(x, 3)
        if x < 1.0:
            avisos.append(msg("andar", f"walk ×{x:.2f}: a evolução anda mais rápido (o normal é igual ou mais devagar)"))
    itens["ereto_x"] = round(b["ereto"] / max(a["ereto"], 1e-6), 3)

    # evolução invertida: menor, cabeça maior e menos peças ao mesmo tempo
    invertidos = sum([altura_x < 1.0, itens.get("cabeca_vol_delta", 0) > 0, cubos_x < 1.0])
    if invertidos >= 2 and not erros:
        erros.append(msg("invertida", "evolução invertida (menor, cabeça maior ou menos peças)"))
    veredito = "erro" if erros else "aviso" if avisos else "ok"
    return {"par": par, "itens": itens, "veredito": veredito, "erros": erros, "avisos": avisos}


def paleta_de(textura: Image.Image | None) -> list[str]:
    if textura is None:
        return []
    a = np.asarray(textura.convert("RGBA"))
    opaco = a[..., 3] > 0
    if not opaco.any():
        return []
    pal, _ = cores.paleta(a[opaco, :3])
    return [cores.para_hex(p) for p in pal]


def sobreposicao(pal_a: list[str], pal_b: list[str]) -> float | None:
    """Fração das cores de a que reaparecem em b (ΔE < 15)."""
    if not pal_a or not pal_b:
        return None
    b = [cores.de_hex(x) for x in pal_b]
    achadas = sum(1 for x in pal_a if min(cores.delta_e(cores.de_hex(x), y) for y in b) < DELTA_E_MESMA_COR)
    return achadas / len(pal_a)


def imagem_lado_a_lado(modelos: list[tuple[str, bbmodelo.Modelo]], altura_px: int = 360) -> Image.Image:
    """Estágios em 3/4, na mesma escala (o maior ocupa a altura), alinhados pelo chão."""
    # na 3/4 a profundidade também ocupa altura na imagem: mede a altura projetada numa escala de teste
    teste = 10.0
    maior = max(render.renderizar(m, "3/4", escala=teste, margem=0)[0].height for _, m in modelos)
    escala = teste * (altura_px - 40) / max(maior, 1)
    ims = [render.renderizar(m, "3/4", escala=escala, margem=10)[0] for _, m in modelos]
    largura = sum(im.width for im in ims) + 10 * (len(ims) + 1)
    folha = Image.new("RGB", (largura, altura_px), render.FUNDO)
    d = ImageDraw.Draw(folha)
    x = 10
    for (rotulo, _), im in zip(modelos, ims):
        folha.paste(im, (x, altura_px - 10 - im.height))
        d.text((x + 2, 4), rotulo, fill=(80, 84, 96))
        x += im.width + 10
    d.line([(0, altura_px - 11), (largura, altura_px - 11)], fill=(200, 204, 212))
    return folha


def avaliar(estagios: list[dict], nicho: str | None = None) -> dict:
    """`estagios` = [{id, modelo (bbmodelo.Modelo), estagio_cobblemon}] em ordem. Devolve o relatório da linhagem."""
    medidas = {e["id"]: metricas(e["modelo"]) for e in estagios}
    paletas = {e["id"]: paleta_de(e["modelo"].textura) for e in estagios}
    pares, erros, avisos = [], [], []
    for a, b in zip(estagios, estagios[1:]):
        par = chave_par(a.get("estagio_cobblemon"), b.get("estagio_cobblemon"))
        r = comparar(medidas[a["id"]], medidas[b["id"]], par, nicho)
        r["de"], r["para"] = a["id"], b["id"]
        s = sobreposicao(paletas[a["id"]], paletas[b["id"]])
        r["itens"]["paleta_sobreposicao"] = None if s is None else round(s, 2)
        if s is not None and s < SOBREPOSICAO_MIN:
            r["avisos"].append(msg("paleta", f"só {s:.0%} das cores de {a['id']} continuam em {b['id']} (motivo de cor some?)"))
            if r["veredito"] == "ok":
                r["veredito"] = "aviso"
        for m in r["erros"]:
            erros.append({**m, "texto": f"{a['id']}→{b['id']}: {m['texto']}"})
        for m in r["avisos"]:
            avisos.append({**m, "texto": f"{a['id']}→{b['id']}: {m['texto']}"})
        pares.append(r)
    veredito = "erro" if erros else "aviso" if avisos else "ok"
    return {"estagios": medidas, "paletas": paletas, "pares": pares, "veredito": veredito, "erros": erros, "avisos": avisos}


@etapa("linhagem")
def cmd_linhagem(args) -> int:
    from criaturas.validar import modelo_atual

    pasta = Path(args.pasta)
    nome = pasta.resolve().name
    entrada_arq = pasta_modelo(nome) / "entrada.json"
    if not entrada_arq.exists():
        print("linhagem: falta entrada.json (rode ficha antes)")
        return 1
    entrada = relatorio.ler_json(entrada_arq)
    estagios, faltam = [], []
    for e in entrada["estagios"]:
        destino = pasta_estagio(nome, e["id"])
        rel = relatorio.ler_json(destino / "relatorio.json") if (destino / "relatorio.json").exists() else {}
        arquivo = modelo_atual(destino, rel) if destino.exists() else None
        if arquivo is None:
            faltam.append(e["id"])
            continue
        estagios.append({"id": e["id"], "modelo": bbmodelo.ler(arquivo), "estagio_cobblemon": e.get("estagio_cobblemon")})
    if len(estagios) < 2:
        print(f"linhagem: precisa de 2 estágios modelados (faltam: {', '.join(faltam) or 'nenhum'})")
        return 1
    nicho = next(((e.get("categoria_confirmada") or {}).get("nicho") for e in entrada["estagios"] if e.get("categoria_confirmada")), None)
    r = avaliar(estagios, nicho)
    imagem = imagem_lado_a_lado([(e["id"], e["modelo"]) for e in estagios])
    destino = pasta_modelo(nome)
    imagem.save(destino / "linhagem.png")
    saida = {**r, "imagem": "linhagem.png", "faltam": faltam}
    caminho = relatorio.gravar_json(destino / "linhagem.json", saida)
    relatorio.registrar(destino, nome, None, "linhagem", r["veredito"] != "erro", erros=r["erros"], avisos=r["avisos"],
                        arquivos=[relativo(caminho), relativo(destino / "linhagem.png")], resumo={"veredito": r["veredito"]})
    linhas = [f"linhagem {nome}: {r['veredito'].upper()} ({len(estagios)} estágios)"]
    for p in r["pares"]:
        it = p["itens"]
        linhas.append(f"  {p['de']}→{p['para']}: altura ×{it['altura_x']}, cubos ×{it['cubos_x']}, "
                      f"cabeça {it.get('cabeca_vol_delta', '?')}, paleta {it.get('paleta_sobreposicao', '?')} — {p['veredito']}")
    linhas += relatorio.linhas_mensagens("Erros", r["erros"])
    linhas += relatorio.linhas_mensagens("Avisos", r["avisos"])
    linhas.append(f"  imagem: {relativo(destino / 'linhagem.png')}")
    relatorio.imprimir(linhas)
    return 1 if r["veredito"] == "erro" else 0
