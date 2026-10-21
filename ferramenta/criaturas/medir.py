"""`criaturas medir <pasta> --estagio eN`: leitura.json + máscaras do preparo -> medidas.json.

1. Encosta cada caixa da leitura nas bordas reais da máscara, dentro de uma margem.
2. Calibra a escala da vista lateral pela frontal (chão em comum; topo das partes vistas nas duas).
3. Combina frente (x, y) e lado (z, y) em caixas 3D, em unidades, na escala da altura alvo
   (a da ficha, ou a mediana do estágio e da categoria).
4. Completa o que nenhuma vista mostra: espelho, parte irmã, profundidade estimada pela categoria.

Eixos (docs/convencoes.md): Y para cima, frente em -Z, lado esquerdo em -X, chão em y = 0.
"""

from pathlib import Path

import numpy as np
from PIL import Image

from criaturas import contratos, relatorio, tabelas
from criaturas.caminhos import pasta_estagio, pasta_modelo, relativo
from criaturas.etapas import etapa
from criaturas.relatorio import msg

CELULAS = 32
MARGEM_ENCOSTO = 1.5  # células
DIFERENCA_VISTAS = 0.10
ESPESSURA_ADESIVO = 0.01


# ---------- encostar nas bordas ----------

LIMIAR_COR = 40.0  # distância de cor entre pixels vizinhos que conta como borda
FORCA_MINIMA = 0.35  # fração da largura da caixa em que a borda aparece
PENALIDADE_DISTANCIA = 0.15  # por célula de distância da proposta


def _escolher_borda(forca: np.ndarray, proposta: float, margem: float, px_celula: float) -> float:
    """Posição j (borda entre os pixels j-1 e j) com a maior força menos a penalidade de distância.

    `forca[j]` vai de 0 a 1; o vetor tem n+1 posições (as pontas são as bordas da imagem).
    """
    n = len(forca)
    a, b = max(0, int(np.floor(proposta - margem))), min(n - 1, int(np.ceil(proposta + margem)))
    melhor, nota_melhor = proposta, -np.inf
    for j in range(a, b + 1):
        if forca[j] < FORCA_MINIMA:
            continue
        nota = forca[j] - PENALIDADE_DISTANCIA * abs(j - proposta) / px_celula
        if nota > nota_melhor:
            melhor, nota_melhor = float(j), nota
    return melhor


def _forca_bordas(mascara: np.ndarray, muda: np.ndarray | None, eixo: int, faixa: tuple[int, int]) -> np.ndarray:
    """Força de borda ao longo de um eixo, medida nas linhas (eixo=1) ou colunas (eixo=0) de `faixa`.

    Silhueta: quanto a cobertura muda entre vizinhos (com fundo fora da imagem).
    Cor: fração das linhas da faixa em que a cor muda (pega partes dentro de outras).
    """
    r0, r1 = faixa
    corte = mascara[r0:r1, :] if eixo == 1 else mascara[:, r0:r1].T
    cobertura = np.concatenate([[0.0], corte.mean(0), [0.0]])
    forca = np.abs(np.diff(cobertura))
    if muda is not None:
        cm = muda[r0:r1, :] if eixo == 1 else muda[:, r0:r1].T
        forca_cor = np.concatenate([cm.mean(0), [0.0]])
        forca = np.maximum(forca, forca_cor)
    return forca


def encostar(caixa, mascara: np.ndarray, cor: np.ndarray | None = None,
             margem_celulas: float = MARGEM_ENCOSTO, passadas: int = 2) -> list[float]:
    """Caixa [x0, y0, x1, y1] em células -> caixa encostada nas bordas reais (células).

    Bordas da silhueta (máscara) e, se houver a imagem, bordas de cor, para partes por dentro de
    outras (mandíbula na frente da cabeça). Vence a borda mais forte e mais perto da proposta.
    """
    h, w = mascara.shape
    px = h / CELULAS
    x0, y0, x1, y1 = (v * px for v in caixa)
    m = margem_celulas * px
    muda_x = muda_y = None
    if cor is not None:
        c = cor.astype(float)
        muda_x = np.zeros((h, w), bool)
        muda_y = np.zeros((h, w), bool)
        muda_x[:, 1:] = np.linalg.norm(c[:, 1:] - c[:, :-1], axis=2) > LIMIAR_COR
        muda_y[1:, :] = np.linalg.norm(c[1:] - c[:-1], axis=2) > LIMIAR_COR
    for _ in range(passadas):
        r0, r1 = int(np.clip(min(y0, y1), 0, h - 1)), int(np.clip(max(y0, y1), 1, h))
        c0, c1 = int(np.clip(min(x0, x1), 0, w - 1)), int(np.clip(max(x0, x1), 1, w))
        if r1 <= r0 or c1 <= c0:
            break
        fx = _forca_bordas(mascara, muda_x, 1, (r0, r1))
        fy = _forca_bordas(mascara, muda_y, 0, (c0, c1))
        x0, x1 = _escolher_borda(fx, x0, m, px), _escolher_borda(fx, x1, m, px)
        y0, y1 = _escolher_borda(fy, y0, m, px), _escolher_borda(fy, y1, m, px)
    return [round(v / px, 3) for v in (x0, y0, x1, y1)]


# ---------- calibração entre vistas ----------

def calibrar(caixas_a: dict, caixas_b: dict) -> float:
    """Fator a em y_a = 32 - a·(32 - y_b): chão em comum.

    Cada borda horizontal (topo e base) de parte vista nas duas vistas dá uma razão; a mediana
    resiste às bordas escondidas numa das vistas (o topo do corpo atrás da cabeça, de frente).
    """
    razoes = []
    for pid, ca in caixas_a.items():
        cb = caixas_b.get(pid)
        if cb is None:
            continue
        for ia in (1, 3):
            alt_a, alt_b = CELULAS - ca[ia], CELULAS - cb[ia]
            if alt_a > 2 and alt_b > 2:
                razoes.append(alt_a / alt_b)
    return float(np.median(razoes)) if razoes else 1.0


# ---------- combinar ----------

def _irma(pid: str) -> str | None:
    for a, b in (("leg_back_", "leg_front_"), ("leg_front_", "leg_back_"), ("shin_back_", "shin_front_"),
                 ("shin_front_", "shin_back_"), ("foot_back_", "foot_front_"), ("foot_front_", "foot_back_")):
        if pid.startswith(a):
            return b + pid[len(a):]
    return None


def _espelhar_id(pid: str) -> str | None:
    if pid.endswith("_left") or "_left_" in pid:
        return pid.replace("_left", "_right")
    if pid.endswith("_right") or "_right_" in pid:
        return pid.replace("_right", "_left")
    return None


def medir(leitura: dict, mascaras: dict[str, np.ndarray], altura_alvo: float, *, categoria: dict | None = None,
          estagio: str | None = None, cores: dict[str, np.ndarray] | None = None) -> dict:
    """Medidas (contrato medidas) a partir da leitura e das máscaras {vista: bool[H, W]}.

    `cores` = {vista: RGB[H, W, 3]} dos recortes, para encostar também nas bordas de cor.
    """
    cores = cores or {}
    contratos.validar("leitura", leitura)
    if "frente" not in mascaras:
        raise ValueError("medir precisa da vista de frente (preparo/frente-mascara.png)")
    avisos = []
    u = altura_alvo / CELULAS  # unidades por célula na frente

    # 1. encostar
    caixas = {v: {} for v in ("frente", "lado", "costas")}
    for p in leitura["partes"]:
        for vista, caixa in p["caixas"].items():
            if vista in mascaras:
                caixas[vista][p["id"]] = encostar(caixa, mascaras[vista], cores.get(vista))

    # 2. calibrar lado e costas pela frente
    fator = {"frente": 1.0}
    for vista in ("lado", "costas"):
        if caixas[vista]:
            fator[vista] = calibrar(caixas["frente"], caixas[vista])

    def y_frente(vista, y):
        return CELULAS - fator[vista] * (CELULAS - y)

    # centros: x pela frente do body (ou da silhueta); z pelo lado do body
    def centro_x(vista):
        c = caixas[vista].get("body")
        if c:
            return (c[0] + c[2]) / 2
        cols = np.nonzero(mascaras[vista].any(0))[0]
        return (cols.min() + cols.max() + 1) / 2 / (mascaras[vista].shape[0] / CELULAS)

    cx = {v: centro_x(v) for v in ("frente", "costas") if caixas[v] or v in mascaras}
    if "costas" in mascaras and not caixas["costas"]:
        fator["costas"] = 1.0  # sem caixas nas costas: mesma altura de silhueta que a frente
    cz = None
    if caixas["lado"]:
        c = caixas["lado"].get("body")
        if c:
            cz = (c[0] + c[2]) / 2
        else:
            cols = np.nonzero(mascaras["lado"].any(0))[0]
            cz = (cols.min() + cols.max() + 1) / 2 / (mascaras["lado"].shape[0] / CELULAS)

    # 3. faixas por eixo, em unidades
    partes = {p["id"]: dict(p) for p in leitura["partes"]}
    faixas: dict[str, dict] = {}
    for pid, p in partes.items():
        f = {"x": None, "y": None, "z": None, "fonte_z": None, "ys": {}}
        if pid in caixas["frente"]:
            x0, y0, x1, y1 = caixas["frente"][pid]
            f["x"] = sorted([(cx["frente"] - x0) * u, (cx["frente"] - x1) * u])
            f["ys"]["frente"] = ((CELULAS - y1) * u, (CELULAS - y0) * u)
        elif pid in caixas["costas"]:
            x0, y0, x1, y1 = caixas["costas"][pid]
            k = fator["costas"] * u
            f["x"] = sorted([(x0 - cx["costas"]) * k, (x1 - cx["costas"]) * k])
        if pid in caixas["costas"]:
            _, y0, _, y1 = caixas["costas"][pid]
            f["ys"]["costas"] = ((CELULAS - y_frente("costas", y1)) * u, (CELULAS - y_frente("costas", y0)) * u)
        if pid in caixas["lado"] and cz is not None:
            z0, y0, z1, y1 = caixas["lado"][pid]
            k = fator["lado"] * u
            f["z"] = sorted([(z0 - cz) * k, (z1 - cz) * k])
            f["fonte_z"] = "lado"
            f["ys"]["lado"] = ((CELULAS - y_frente("lado", y1)) * u, (CELULAS - y_frente("lado", y0)) * u)
        if f["ys"]:
            # oclusão só encolhe uma parte numa vista: a união das vistas é a melhor estimativa
            f["y"] = [min(a for a, _ in f["ys"].values()), max(b for _, b in f["ys"].values())]
            if "frente" in f["ys"] and "lado" in f["ys"]:
                hf = f["ys"]["frente"][1] - f["ys"]["frente"][0]
                hl = f["ys"]["lado"][1] - f["ys"]["lado"][0]
                if max(hf, hl) > 0 and abs(hf - hl) / max(hf, hl) > DIFERENCA_VISTAS:
                    avisos.append(msg("diferenca_vistas", f"{pid}: altura {hf:.1f} na frente e {hl:.1f} no lado "
                                      f"({abs(hf - hl) / max(hf, hl):.0%}); parte escondida numa vista?", pid))
        faixas[pid] = f

    # 4a. lado direito não listado: espelha o esquerdo
    for pid, p in list(partes.items()):
        outro = p.get("espelho") or (_espelhar_id(pid) if p["simetria"] != "central" else None)
        if outro and outro not in partes:
            q = dict(p)
            q["id"], q["espelho"] = outro, pid
            q["simetria"] = "direita" if p["simetria"] == "esquerda" else "esquerda"
            if q.get("pai"):
                q["pai"] = _espelhar_id(q["pai"]) or q["pai"]  # forearm_left -> arm_left vira arm_right
            partes[outro] = q
            fo = {k: (list(v) if isinstance(v, list) else v) for k, v in faixas[pid].items()}
            fo["ys"] = dict(faixas[pid]["ys"])
            if fo["x"] is not None:
                fo["x"] = sorted([-fo["x"][0], -fo["x"][1]])
            faixas[outro] = fo
            p["espelho"] = outro

    # 4b. completar eixos faltando pelo espelho e pela irmã
    for pid, f in faixas.items():
        par = partes[pid].get("espelho")
        if par in faixas:
            g = faixas[par]
            if f["x"] is None and g["x"] is not None:
                f["x"] = sorted([-g["x"][0], -g["x"][1]])
            if f["z"] is None and g["z"] is not None:
                f["z"], f["fonte_z"] = list(g["z"]), g["fonte_z"]
            if f["y"] is None and g["y"] is not None:
                f["y"] = list(g["y"])
        irma = _irma(pid)
        if f["x"] is None and irma in faixas and faixas[irma]["x"] is not None:
            f["x"] = list(faixas[irma]["x"])

    # 4c. o que ainda falta: estimativa pela categoria e pelo pai
    ordem = _ordem_hierarquia(partes)
    corpo_compr = None
    if categoria:
        corpo_compr = tabelas.mediana(categoria["nicho"], estagio, "corpo_compr_alt") or tabelas.mediana(categoria["plano"], estagio, "corpo_compr_alt")
    saida = []
    for pid in ordem:
        p, f = partes[pid], faixas[pid]
        pai = faixas.get(p.get("pai")) if p.get("pai") else None
        if f["y"] is None:
            f["y"] = list(pai["y"]) if pai and pai["y"] else [0.0, u]
        if f["x"] is None:
            # seção mais ou menos redonda: a menor dimensão que se vê (cauda: a altura, não o comprimento)
            altura_parte = f["y"][1] - f["y"][0]
            largura = min(altura_parte, f["z"][1] - f["z"][0]) if f["z"] else altura_parte
            centro = (pai["x"][0] + pai["x"][1]) / 2 if pai and pai["x"] else 0.0
            f["x"] = [centro - largura / 2, centro + largura / 2]
            avisos.append(msg("x_estimado", f"{pid}: largura estimada (não aparece na frente)", pid))
        if f["z"] is None:
            if p["tipo"] == "adesivo" and pai and pai["z"]:
                f["z"] = [pai["z"][0] - ESPESSURA_ADESIVO] * 2
                f["fonte_z"] = "estimada"
            elif pid == "body" and corpo_compr and (categoria or {}).get("plano") != "cabeça-corpo":
                # cabeça-corpo (bola, blob) cai no else: profundidade = largura, seção redonda
                prof = corpo_compr * altura_alvo
                f["z"], f["fonte_z"] = [-prof / 2, prof / 2], "tabela"
            else:
                prof = 0.0 if p["tipo"] != "volume" else (f["x"][1] - f["x"][0])
                centro = (pai["z"][0] + pai["z"][1]) / 2 if pai and pai["z"] else 0.0
                f["z"], f["fonte_z"] = [centro - prof / 2, centro + prof / 2], "estimada"
        de = [f["x"][0], f["y"][0], f["z"][0]]
        ate = [f["x"][1], f["y"][1], f["z"][1]]
        if p["tipo"] in ("plano", "adesivo"):
            de, ate = _achatar(p, pid, de, ate, caixas, pai)
        parte = {"id": pid, "pai": p.get("pai"), "tipo": p["tipo"], "simetria": p["simetria"],
                 "espelho": p.get("espelho"), "from": [round(v, 2) for v in de], "to": [round(v, 2) for v in ate],
                 "profundidade": f["fonte_z"] or "estimada"}
        for k in ("rotacao_repouso", "papel_cor", "segmentos"):
            if k in p:
                parte[k] = p[k]
        if p["tipo"] == "volume" and p["simetria"] == "central" and pid in caixas["frente"]:
            fs = fatias(caixas["frente"][pid], mascaras["frente"], cx["frente"], u, de, ate)
            if fs:
                parte["fatias"] = fs
        saida.append(parte)
        f["x"], f["y"], f["z"] = [de[0], ate[0]], [de[1], ate[1]], [de[2], ate[2]]
        if parte["profundidade"] != "lado" and p["tipo"] == "volume" and caixas["lado"]:
            avisos.append(msg("profundidade_estimada", f"{pid}: profundidade estimada (não aparece no lado)", pid))
    if not caixas["lado"]:
        avisos.append(msg("sem_lado", "sem vista lateral: profundidades estimadas pela categoria"))
    # mapeamento mundo -> grade de cada vista, para a textura (Fase 5):
    #   frente: x_cel = centro - x/(u·fator); costas: x_cel = centro + x/(u·fator); lado: z_cel = centro + z/(u·fator)
    #   y_cel = 32 - y/(u·fator) nas três
    mapeamento = {}
    if "frente" in cx:
        mapeamento["frente"] = {"centro": round(cx["frente"], 4), "fator": 1.0}
    if "costas" in cx:
        mapeamento["costas"] = {"centro": round(cx["costas"], 4), "fator": round(fator["costas"], 5)}
    if cz is not None:
        mapeamento["lado"] = {"centro": round(cz, 4), "fator": round(fator["lado"], 5)}
    return {"altura_alvo_unidades": round(altura_alvo, 3), "unidades_por_celula": round(u, 4),
            "fator_vistas": {k: round(v, 4) for k, v in fator.items()}, "mapeamento": mapeamento,
            "partes": saida, "avisos": avisos}


PREENCHIMENTO_FATIAR = 0.85  # silhueta que enche menos que isso da caixa é arredondada (bola, gota)
ALTURA_MIN_FATIAR = 6.0  # unidades


def fatias(caixa, mascara: np.ndarray, centro_x: float, u: float, de, ate) -> list[dict] | None:
    """Camadas horizontais que seguem a silhueta de uma parte arredondada (vista de frente).

    Cada camada tem a largura da silhueta naquela altura (percentis 20–80 das bordas, para os fiapos
    de pelo não alargarem) e a profundidade na mesma proporção largura/profundidade da parte.
    None se a parte já é quase um retângulo ou é pequena.
    """
    altura_u = ate[1] - de[1]
    largura_u = ate[0] - de[0]
    if altura_u < ALTURA_MIN_FATIAR or largura_u < ALTURA_MIN_FATIAR:
        return None
    px = mascara.shape[0] / CELULAS
    x0, y0, x1, y1 = caixa
    r0, r1 = int(y0 * px), int(np.ceil(y1 * px))
    c0, c1 = int(x0 * px), int(np.ceil(x1 * px))
    recorte = mascara[r0:r1, c0:c1]
    if recorte.size == 0 or recorte.mean() >= PREENCHIMENTO_FATIAR:
        return None
    n = int(np.clip(round(altura_u / 3), 3, 6))
    proporcao_z = (ate[2] - de[2]) / max(largura_u, 1e-6)
    centro_z = (ate[2] + de[2]) / 2
    saida = []
    limites = np.linspace(0, recorte.shape[0], n + 1).astype(int)
    for a, b in zip(limites, limites[1:]):
        inicios, fins = [], []
        for linha in recorte[a:b]:
            cols = np.nonzero(linha)[0]
            if len(cols):
                inicios.append(cols.min())
                fins.append(cols.max() + 1)
        if not inicios:
            continue
        xa = (c0 + np.percentile(inicios, 20)) / px
        xb = (c0 + np.percentile(fins, 80)) / px
        xs = sorted([(centro_x - xa) * u, (centro_x - xb) * u])
        ys = [(CELULAS - (r0 + b) / px) * u, (CELULAS - (r0 + a) / px) * u]
        prof = (xs[1] - xs[0]) * proporcao_z
        saida.append({"x": [round(v, 2) for v in xs], "y": [round(v, 2) for v in ys],
                      "z": [round(centro_z - prof / 2, 2), round(centro_z + prof / 2, 2)]})
    return saida if len(saida) >= 2 else None


def _ordem_hierarquia(partes: dict) -> list[str]:
    feitos, ordem = set(), []

    def visitar(pid, pilha=()):
        if pid in feitos or pid in pilha:
            return
        pai = partes[pid].get("pai")
        if pai in partes:
            visitar(pai, pilha + (pid,))
        feitos.add(pid)
        ordem.append(pid)

    for pid in partes:
        visitar(pid)
    return ordem


def _achatar(p, pid, de, ate, caixas, pai):
    """Plano e adesivo: espessura zero no eixo fino (o que nenhuma vista mostra de frente)."""
    de, ate = list(de), list(ate)
    if p["tipo"] == "adesivo":
        eixo = 2
    elif pid not in caixas["lado"]:
        eixo = 2  # visto de frente e invisível de perfil: fino em z
    elif pid not in caixas["frente"] and pid not in caixas["costas"]:
        eixo = 0  # visto de perfil e invisível de frente: fino em x
    else:
        eixo = int(np.argmin([ate[i] - de[i] for i in range(3)]))
    if p["tipo"] == "adesivo" and pai and pai["z"]:
        de[2] = ate[2] = pai["z"][0] - ESPESSURA_ADESIVO
    else:
        meio = (de[eixo] + ate[eixo]) / 2
        de[eixo] = ate[eixo] = meio
    return de, ate


# ---------- CLI ----------

def carregar_mascaras(preparo: Path) -> dict[str, np.ndarray]:
    mascaras = {}
    for vista in ("frente", "lado", "costas"):
        arq = preparo / f"{vista}-mascara.png"
        if arq.exists():
            with Image.open(arq) as im:
                mascaras[vista] = np.asarray(im.convert("L")) > 127
    return mascaras


def carregar_cores(preparo: Path) -> dict[str, np.ndarray]:
    cores = {}
    for vista in ("frente", "lado", "costas"):
        arq = preparo / f"{vista}-recorte.png"
        if arq.exists():
            with Image.open(arq) as im:
                rgba = np.asarray(im.convert("RGBA")).astype(float)
            # fundo branco onde não há criatura, para a borda da silhueta não contar duas vezes
            alfa = rgba[..., 3:4] / 255
            cores[vista] = (rgba[..., :3] * alfa + 255 * (1 - alfa)).astype(np.uint8)
    return cores


def altura_alvo(entrada: dict | None, estagio_id: str, categoria: dict | None) -> tuple[float, str]:
    est = next((e for e in (entrada or {}).get("estagios", []) if e["id"] == estagio_id), {})
    if est.get("altura_blocos"):
        return est["altura_blocos"] * 16, "ficha"
    tab = est.get("estagio_tabela")
    for cat in ((categoria or {}).get("nicho"), (categoria or {}).get("plano")):
        if cat:
            m = tabelas.mediana(cat, tab, "altura_blocos")
            if m:
                return m * 16, "tabela"
    raise ValueError("sem altura: preencha 'Altura no jogo' na ficha ou confirme a categoria")


@etapa("medir")
def cmd_medir(args) -> int:
    pasta = Path(args.pasta)
    nome = pasta.resolve().name
    destino = pasta_estagio(nome, args.estagio)
    erros = []
    leitura_arq = destino / "leitura.json"
    if not leitura_arq.exists():
        print(f"medir: falta {relativo(leitura_arq)}. Siga skills/criaturas-3d/ler.md e rode de novo.")
        return 1
    entrada_arq = pasta_modelo(nome) / "entrada.json"
    entrada = relatorio.ler_json(entrada_arq) if entrada_arq.exists() else None
    classif_arq = destino / "classificacao.json"
    categoria = relatorio.ler_json(classif_arq).get("categoria_usada") if classif_arq.exists() else None
    est = next((e for e in (entrada or {}).get("estagios", []) if e["id"] == args.estagio), {})
    categoria = categoria or est.get("categoria_confirmada")
    try:
        alvo, fonte = altura_alvo(entrada, args.estagio, categoria)
        resultado = medir(relatorio.ler_json(leitura_arq), carregar_mascaras(destino / "preparo"), alvo,
                          categoria=categoria, estagio=est.get("estagio_tabela"), cores=carregar_cores(destino / "preparo"))
    except (ValueError, contratos.ContratoInvalido) as e:
        erros.append(msg("medir", str(e)))
        relatorio.registrar(destino, nome, args.estagio, "medir", False, erros=erros)
        print(f"medir: {e}")
        return 1
    resultado["fonte_altura"] = fonte
    caminho = relatorio.gravar_json(destino / "medidas.json", resultado, "medidas")
    relatorio.registrar(destino, nome, args.estagio, "medir", True, avisos=resultado["avisos"], arquivos=[relativo(caminho)],
                        resumo={"partes": len(resultado["partes"]), "altura": alvo})
    linhas = [f"medir {nome} {args.estagio}: {len(resultado['partes'])} partes, altura {alvo:.1f} u ({fonte}), "
              f"lado×{resultado['fator_vistas'].get('lado', 0):.3f}"]
    for p in resultado["partes"][:10]:
        tam = [b - a for a, b in zip(p["from"], p["to"])]
        linhas.append(f"  {p['id']:<18} {tam[0]:5.1f} × {tam[1]:5.1f} × {tam[2]:5.1f}  ({p['profundidade']})")
    if len(resultado["partes"]) > 10:
        linhas.append(f"  … e mais {len(resultado['partes']) - 10} partes")
    linhas += relatorio.linhas_mensagens("Avisos", resultado["avisos"], 4)
    relatorio.imprimir(linhas)
    return 0
