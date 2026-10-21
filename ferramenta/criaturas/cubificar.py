"""`criaturas cubificar <pasta> --estagio eN`: medidas (+ leitura e categoria) -> plano-cubos.json -> ops.json -> .bbmodel.

Regras (docs/plano-construcao.md 4.2 e docs/convencoes.md):
- uma parte vira um osso com o mesmo id e um cubo; pivô na junta com o pai;
- tamanhos inteiros; partes centrais simétricas em x = 0; a direita é o espelho exato da esquerda (mirror_uv);
- parte encosta no pai sem atravessar; plano entra 1 unidade no pai (senão o validador acusa peça solta);
- correntes (cauda, pescoço, tentáculo) dadas como uma peça viram N segmentos (os da leitura, ou a
  mediana da categoria), afinando até 70% na ponta;
- locators padrão; orçamento de cubos do estágio (aviso acima de p75 × 1,3);
- nunca sobrescreve um .bbmodel editado à mão: grava <nome>-eN.v2.bbmodel (v3…) e avisa.
"""

import hashlib
import math
import re
from pathlib import Path

import numpy as np

from criaturas import contratos, motor, ops, relatorio, rig, tabelas
from criaturas.caminhos import pasta_estagio, pasta_modelo, relativo
from criaturas.etapas import etapa
from criaturas.relatorio import msg

AFINAMENTO_PONTA = 0.7
FOLGA_CONTATO = 1.5  # vão até isso (em unidades) é fechado encostando a parte no pai
ENTRADA_PLANO = 1.0
ORCAMENTO_FATOR = 1.3
COR_PADRAO = "#a0a0aa"


# ---------- geometria das partes ----------

def _caixa(p):
    a, b = np.asarray(p["from"], float), np.asarray(p["to"], float)
    return np.minimum(a, b), np.maximum(a, b)


def _por(p, de, ate):
    p["from"], p["to"] = [float(x) for x in de], [float(x) for x in ate]


def arredondar(partes: list[dict]) -> None:
    """Tamanhos inteiros (≥ 1 nos eixos não finos) e posições em meia unidade, com simetria."""
    por_id = {p["id"]: p for p in partes}
    for p in partes:
        if p.get("simetria") == "direita" and p.get("espelho") in por_id:
            continue  # sai do espelho, depois
        de, ate = _caixa(p)
        tam = ate - de
        novo_de, novo_ate = de.copy(), ate.copy()
        for eixo in range(3):
            fino = tam[eixo] < 1e-6 and p["tipo"] != "volume"
            if fino:
                c = round(de[eixo] * 2) / 2 if p["tipo"] != "adesivo" else de[eixo]
                novo_de[eixo] = novo_ate[eixo] = c
                continue
            t = max(1, int(round(tam[eixo])))
            centro = (de[eixo] + ate[eixo]) / 2
            if eixo == 0 and p.get("simetria", "central") == "central" and abs(centro) < 0.75:
                inicio = -t / 2  # simétrica em x = 0 (meia unidade quando a largura é ímpar)
            else:
                inicio = math.floor(centro - t / 2 + 0.5)
            novo_de[eixo], novo_ate[eixo] = inicio, inicio + t
        _por(p, novo_de, novo_ate)
    for p in partes:
        if p.get("simetria") == "direita" and p.get("espelho") in por_id:
            e = por_id[p["espelho"]]
            de, ate = _caixa(e)
            _por(p, [-ate[0], de[1], de[2]], [-de[0], ate[1], ate[2]])


def _eixo_contato(c, pai):
    """Eixo em que filho e pai menos se sobrepõem (onde fica a junta) e a sobreposição em cada eixo."""
    (c0, c1), (p0, p1) = c, pai
    sobre = np.minimum(c1, p1) - np.maximum(c0, p0)
    escala = np.maximum(np.minimum(c1 - c0, p1 - p0), 1e-6)
    return int(np.argmin(sobre / escala)), sobre


ESPESSURA_ADESIVO = 0.01


def cubos_das_fatias(p: dict) -> list[tuple[list, list]] | None:
    """Cubos inteiros das fatias de uma parte arredondada, dentro da caixa final dela (simétricos em x = 0)."""
    fs = p.get("fatias")
    if not fs:
        return None
    de, ate = _caixa(p)
    fs = sorted(fs, key=lambda f: f["y"][0])
    y_lo, y_hi = fs[0]["y"][0], fs[-1]["y"][1]
    escala = (ate[1] - de[1]) / max(y_hi - y_lo, 1e-6)
    # bordas em y inteiras, distribuídas na altura final
    bordas = sorted({int(round(de[1] + (f["y"][0] - y_lo) * escala)) for f in fs} | {int(round(ate[1]))})
    bordas[0] = int(round(de[1]))
    cubos = []
    largura_max, prof_max = ate[0] - de[0], ate[2] - de[2]
    lmax_fatias = max(f["x"][1] - f["x"][0] for f in fs)
    for i, (a, b) in enumerate(zip(bordas, bordas[1:])):
        if b <= a:
            continue
        f = min(fs, key=lambda f: abs((f["y"][0] - y_lo) * escala + de[1] - a))
        frac = (f["x"][1] - f["x"][0]) / max(lmax_fatias, 1e-6)
        w = max(1, int(round(largura_max * frac)))
        d = max(1, int(round(prof_max * frac)))
        cz = (de[2] + ate[2]) / 2
        z0 = math.floor(cz - d / 2 + 0.5)
        cubos.append(([-w / 2, a, z0], [w / 2, b, z0 + d]))
    return cubos if len(cubos) >= 2 else None


def colar_adesivos(partes: list[dict]) -> None:
    """Adesivo (olho, boca, marca) fica 0,01 à frente da face do pai e dentro dela (o pai pode ter mudado no arredondamento)."""
    por_id = {p["id"]: p for p in partes}
    for p in partes:
        pai = por_id.get(p.get("pai"))
        if p["tipo"] != "adesivo" or pai is None:
            continue
        de, ate = _caixa(p)
        p0, p1 = _caixa(pai)
        if pai.get("_cubos"):
            # pai em fatias: a face é a da fatia na altura do centro do adesivo
            yc = (de[1] + ate[1]) / 2
            cubo = min(pai["_cubos"], key=lambda c: 0 if c[0][1] <= yc <= c[1][1] else min(abs(yc - c[0][1]), abs(yc - c[1][1])))
            p0, p1 = np.asarray(cubo[0], float), np.asarray(cubo[1], float)
        fino = int(np.argmin(ate - de))
        frente = (de[fino] + ate[fino]) / 2 <= (p0[fino] + p1[fino]) / 2
        valor = p0[fino] - ESPESSURA_ADESIVO if frente else p1[fino] + ESPESSURA_ADESIVO
        de[fino] = ate[fino] = valor
        for eixo in range(3):
            if eixo == fino:
                continue
            t = min(ate[eixo] - de[eixo], p1[eixo] - p0[eixo])
            de[eixo] = min(max(de[eixo], p0[eixo]), p1[eixo] - t)
            ate[eixo] = de[eixo] + t
        _por(p, de, ate)


def resolver_contatos(partes: list[dict], avisos: list) -> None:
    """Fecha vãos pequenos, desfaz interpenetração de volumes e enterra planos 1 unidade no pai."""
    por_id = {p["id"]: p for p in partes}
    for p in partes:
        pai = por_id.get(p.get("pai"))
        if pai is None or p["tipo"] == "adesivo":
            continue
        c0, c1 = _caixa(p)
        p0, p1 = _caixa(pai)
        eixo, sobre = _eixo_contato((c0, c1), (p0, p1))
        cc, pc = (c0 + c1) / 2, (p0 + p1) / 2
        fora = cc[eixo] > pc[eixo]  # o filho está do lado + do pai nesse eixo
        if p["tipo"] == "plano":
            fino = [i for i in range(3) if c1[i] - c0[i] < 1e-6]
            eixos = [i for i in range(3) if i not in fino]
            # junta do plano: eixo não fino com menor sobreposição
            eixo = min(eixos, key=lambda i: sobre[i] / max(min(c1[i] - c0[i], p1[i] - p0[i]), 1e-6))
            fora = cc[eixo] > pc[eixo]
            if fora:
                c0[eixo] = min(c0[eixo], p1[eixo] - ENTRADA_PLANO)
            else:
                c1[eixo] = max(c1[eixo], p0[eixo] + ENTRADA_PLANO)
            _por(p, c0, c1)
            continue
        if np.all(sobre > 1e-6):
            # atravessa o pai: recua a borda de dentro até encostar
            if fora:
                c0[eixo] = p1[eixo]
            else:
                c1[eixo] = p0[eixo]
            if c1[eixo] - c0[eixo] < 1:
                avisos.append(msg("contato", f"{p['id']}: quase toda dentro de {pai['id']}; mantida encostada", p["id"]))
                if fora:
                    c1[eixo] = c0[eixo] + 1
                else:
                    c0[eixo] = c1[eixo] - 1
            _por(p, c0, c1)
        elif sobre[eixo] < -1e-6:
            outros = [i for i in range(3) if i != eixo]
            if all(sobre[i] > 0 for i in outros) and -sobre[eixo] <= FOLGA_CONTATO:
                if fora:
                    c0[eixo] = p1[eixo]
                else:
                    c1[eixo] = p0[eixo]
                _por(p, c0, c1)
            elif -sobre[eixo] > FOLGA_CONTATO:
                avisos.append(msg("solta", f"{p['id']}: longe de {pai['id']} ({-sobre[eixo]:.1f} u)", p["id"]))


# ---------- correntes ----------

CORRENTE = re.compile(r"^(tail|neck|tentacle(?:_\d+)?)_(\d+)$")


def dividir_correntes(partes: list[dict], categoria: dict | None, estagio: str | None, avisos: list) -> list[dict]:
    """Corrente dada como uma peça só (tail_1 sem tail_2) vira N segmentos afinando."""
    ids = {p["id"] for p in partes}
    saida = []
    for p in partes:
        m = CORRENTE.match(p["id"])
        if not m or p["tipo"] != "volume" or f"{m.group(1)}_{int(m.group(2)) + 1}" in ids or int(m.group(2)) != 1:
            saida.append(p)
            continue
        n = p.get("segmentos")
        if not n and categoria:
            medida = {"tail": "cauda_segmentos", "neck": "pescoco_segmentos"}.get(m.group(1).split("_")[0])
            if medida:
                n = tabelas.mediana(categoria["nicho"], estagio, medida) or tabelas.mediana(categoria["plano"], estagio, medida)
        n = int(round(n or 1))
        de, ate = _caixa(p)
        tam = ate - de
        eixo = int(np.argmax(tam))
        if n <= 1 or tam[eixo] < 2 * n:
            saida.append(p)
            continue
        # a corrente cresce para longe do pai: o primeiro segmento fica do lado do pai
        pai = next((q for q in partes if q["id"] == p.get("pai")), None)
        sentido = 1
        if pai is not None:
            pc = (np.asarray(pai["from"]) + np.asarray(pai["to"])) / 2
            sentido = 1 if (de[eixo] + ate[eixo]) / 2 >= pc[eixo] else -1
        cortes = np.round(np.linspace(0, tam[eixo], n + 1)).astype(int)
        anterior = p.get("pai")
        for i in range(n):
            seg = dict(p)
            seg["id"] = f"{m.group(1)}_{i + 1}"
            seg["pai"] = anterior
            seg.pop("segmentos", None)
            s_de, s_ate = de.copy(), ate.copy()
            if sentido > 0:
                s_de[eixo], s_ate[eixo] = de[eixo] + cortes[i], de[eixo] + cortes[i + 1]
            else:
                s_de[eixo], s_ate[eixo] = ate[eixo] - cortes[i + 1], ate[eixo] - cortes[i]
            fator = 1 - (1 - AFINAMENTO_PONTA) * (i / max(n - 1, 1))
            for outro in range(3):
                if outro == eixo:
                    continue
                t = max(1, int(round(tam[outro] * fator)))
                centro = (de[outro] + ate[outro]) / 2
                s_de[outro], s_ate[outro] = centro - t / 2, centro + t / 2
            if p.get("rotacao_repouso"):
                seg["rotacao_repouso"] = [r / n for r in p["rotacao_repouso"]]
            _por(seg, s_de, s_ate)
            saida.append(seg)
            anterior = seg["id"]
        avisos.append(msg("corrente", f"{p['id']} dividida em {n} segmentos", p["id"]))
    return saida


# ---------- plano de cubos ----------

def pivo(p: dict, pai: dict | None) -> list[float]:
    """Pivô na junta: centro da parte, com o eixo da junta na face que encosta no pai."""
    de, ate = _caixa(p)
    centro = (de + ate) / 2
    if pai is None:
        return [round(float(x), 2) for x in centro]
    p0, p1 = _caixa(pai)
    eixo, _ = _eixo_contato((de, ate), (p0, p1))
    pc = (p0 + p1) / 2
    centro[eixo] = de[eixo] if centro[eixo] > pc[eixo] else ate[eixo]
    return [round(float(x), 2) for x in centro]


def plano_de_cubos(medidas: dict, nome: str, papeis_cor: dict | None = None, categoria: dict | None = None,
                   estagio: str | None = None, estagio_cobblemon: str | None = None,
                   *, poucas_formas: bool = False) -> tuple[dict, list]:
    """(plano-cubos, avisos) a partir das medidas; poucas_formas evita fatiar volumes."""
    avisos = []
    partes = [dict(p) for p in medidas["partes"]]
    partes = dividir_correntes(partes, categoria, estagio, avisos)
    arredondar(partes)
    resolver_contatos(partes, avisos)
    arredondar(partes)  # o contato pode ter deixado meia unidade
    if not poucas_formas:
        for p in partes:
            cs = cubos_das_fatias(p)
            if cs:
                p["_cubos"] = cs
    colar_adesivos(partes)
    por_id = {p["id"]: p for p in partes}
    cores = papeis_cor or {}
    ossos = [{"nome": "root", "pai": None, "pivo": [0, 0, 0]}]
    cubos = []
    for p in partes:
        pai = por_id.get(p.get("pai"))
        osso = {"nome": p["id"], "pai": p["pai"] if p.get("pai") in por_id else "root", "pivo": pivo(p, pai)}
        if p.get("rotacao_repouso") and any(p["rotacao_repouso"]):
            osso["rotacao"] = [round(float(r), 1) for r in p["rotacao_repouso"]]
        ossos.append(osso)
        caixas = p.get("_cubos") or [(p["from"], p["to"])]
        for i, (de, ate) in enumerate(caixas):
            cubo = {"nome": f"{p['id']}_cube" + (f"_{i + 1}" if i else ""), "osso": p["id"], "parte": p["id"], "tipo": p["tipo"],
                    "from": [round(float(v), 3) for v in de], "to": [round(float(v), 3) for v in ate],
                    "cor": cores.get(p.get("papel_cor"), COR_PADRAO)}
            if p.get("simetria") == "direita" and p.get("espelho") in por_id:
                cubo["mirror_uv"] = True
                cubo["espelho_de"] = f"{p['espelho']}_cube" + (f"_{i + 1}" if i else "")
            cubos.append(cubo)
    offsets, (largura, altura) = ops.distribuir_uv(cubos, margem=1)  # 1 texel entre ilhas: margem da versão Roblox
    for c in cubos:
        c["uv_offset"] = offsets[c["nome"]]
        c.pop("espelho_de", None)
    plano = {"nome": nome, "formato": "bedrock", "resolucao": {"largura": largura, "altura": altura},
             "ossos": ossos, "cubos": cubos, "locators": rig.locators(partes)}
    p75 = None
    if estagio_cobblemon and estagio_cobblemon in tabelas.dados()["estagios"]["cobblemon"]:
        p75 = tabelas.dados()["estagios"]["cobblemon"][estagio_cobblemon].get("cubos", [None, None, None])[2]
    if p75 is None and categoria:
        f = tabelas.faixas(categoria["nicho"], estagio) if estagio else tabelas.faixas(categoria["nicho"])
        p75 = (f.get("cubos") or [None, None, None])[2]
    if p75:
        plano["orcamento"] = {"cubos": len(cubos), "p75": p75, "limite": round(p75 * ORCAMENTO_FATOR, 1)}
        if len(cubos) > p75 * ORCAMENTO_FATOR:
            avisos.append(msg("orcamento", f"{len(cubos)} cubos passa de p75 × 1,3 = {p75 * ORCAMENTO_FATOR:.0f}"))
    contratos.validar("plano_cubos", plano)
    return plano, avisos


# ---------- .bbmodel ----------

def sha256(caminho: Path) -> str:
    return hashlib.sha256(Path(caminho).read_bytes()).hexdigest()


def destino_bbmodel(pasta: Path, base: str, hashes: dict) -> tuple[Path, str | None]:
    """Arquivo onde gravar: o normal, ou uma versão nova (.v2, .v3…) se o atual foi editado à mão."""
    arquivo = pasta / f"{base}.bbmodel"
    if not arquivo.exists():
        return arquivo, None
    if hashes.get(arquivo.name) == sha256(arquivo):
        return arquivo, None
    n = 2
    while (pasta / f"{base}.v{n}.bbmodel").exists() and hashes.get(f"{base}.v{n}.bbmodel") != sha256(pasta / f"{base}.v{n}.bbmodel"):
        n += 1
    return pasta / f"{base}.v{n}.bbmodel", f"{arquivo.name} foi editado à mão; a versão nova saiu em {base}.v{n}.bbmodel"


def construir(plano: dict, pasta: Path, base: str, hashes: dict) -> tuple[Path, str | None, str]:
    """Grava ops.json e o .bbmodel pelo motor. Devolve (arquivo, aviso de versão, hash)."""
    lote = ops.gerar_ops(plano)
    relatorio.gravar_json(pasta / "ops.json", {"operations": lote})
    arquivo, aviso = destino_bbmodel(pasta, base, hashes)
    motor.criar(arquivo, base, plano["resolucao"]["largura"], plano["resolucao"]["altura"])
    motor.editar(arquivo, lote)
    return arquivo, aviso, sha256(arquivo)


def contexto(nome: str, estagio_id: str) -> dict:
    """Entrada, categoria e estágio de uma criatura, pelos arquivos já gravados."""
    destino = pasta_estagio(nome, estagio_id)
    entrada_arq = pasta_modelo(nome) / "entrada.json"
    entrada = relatorio.ler_json(entrada_arq) if entrada_arq.exists() else {}
    est = next((e for e in entrada.get("estagios", []) if e["id"] == estagio_id), {})
    classif = destino / "classificacao.json"
    categoria = relatorio.ler_json(classif).get("categoria_usada") if classif.exists() else None
    categoria = categoria or est.get("categoria_confirmada")
    rel = destino / "relatorio.json"
    return {"destino": destino, "entrada": entrada, "estagio": est, "categoria": categoria,
            "relatorio": relatorio.ler_json(rel) if rel.exists() else {}}


@etapa("cubificar")
def cmd_cubificar(args) -> int:
    pasta = Path(args.pasta)
    nome = pasta.resolve().name
    ctx = contexto(nome, args.estagio)
    destino = ctx["destino"]
    for arq in ("medidas.json", "leitura.json"):
        if not (destino / arq).exists():
            print(f"cubificar: falta {relativo(destino / arq)} (rode medir antes)")
            return 1
    medidas = relatorio.ler_json(destino / "medidas.json")
    leitura = relatorio.ler_json(destino / "leitura.json")
    base = f"{ctx['entrada'].get('nome') or nome}-{args.estagio}"
    try:
        plano, avisos = plano_de_cubos(medidas, base, leitura.get("papeis_cor"), ctx["categoria"],
                                       ctx["estagio"].get("estagio_tabela"), ctx["estagio"].get("estagio_cobblemon"),
                                       poucas_formas=leitura.get("modelagem", {}).get("abordagem") == "poucas_formas")
        relatorio.gravar_json(destino / "plano-cubos.json", plano, "plano_cubos")
        arquivo, aviso_versao, hash_ = construir(plano, destino, base, ctx["relatorio"].get("hashes", {}))
    except (ValueError, motor.MotorErro, contratos.ContratoInvalido) as e:
        relatorio.registrar(destino, nome, args.estagio, "cubificar", False, erros=[msg("cubificar", str(e))])
        print(f"cubificar: {e}")
        return 1
    if aviso_versao:
        avisos.append(msg("editado_a_mao", aviso_versao))
    relatorio.registrar(destino, nome, args.estagio, "cubificar", True, avisos=avisos,
                        arquivos=[relativo(destino / "plano-cubos.json"), relativo(destino / "ops.json"), relativo(arquivo)],
                        resumo={"cubos": len(plano["cubos"]), "ossos": len(plano["ossos"]), "arquivo": arquivo.name},
                        hashes={arquivo.name: hash_})
    from criaturas import estado

    estado.registrar(destino, arquivo)
    orc = plano.get("orcamento", {})
    linhas = [f"cubificar {nome} {args.estagio}: {len(plano['cubos'])} cubos, {len(plano['ossos'])} ossos, "
              f"{len(plano['locators'])} locators, textura {plano['resolucao']['largura']}×{plano['resolucao']['altura']}",
              f"  orçamento: {orc.get('cubos', '?')} de p75 {orc.get('p75', '?')} (limite {orc.get('limite', '?')})",
              f"  gravado: {relativo(arquivo)}"]
    linhas += relatorio.linhas_mensagens("Avisos", avisos)
    relatorio.imprimir(linhas)
    return 0
