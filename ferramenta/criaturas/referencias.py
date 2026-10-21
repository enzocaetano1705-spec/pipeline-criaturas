"""Consulta modelos externos sem alterar os originais, com cache agregado externo.

O catálogo guarda metadados e medidas agregadas. Nunca exporta coordenadas, UVs,
texturas nem valores de chaves de animação dos modelos de referência.
"""

import argparse
import itertools
import json
import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

import numpy as np

from criaturas import bbmodelo, relatorio
from criaturas.caminhos import chave

BIBLIOTECA_PADRAO = Path.home() / "Downloads" / "referencias-criaturas"
CACHE = ".catalogo-estrutural.json"
VERSAO = 1
VOCABULARIO = {
    "penas": {"feather", "feathers", "plume", "plumes", "quill", "pena", "penas"},
    "asas": {"wing", "wings", "asa", "asas"},
    "antenas": {"antenna", "antennas", "antennae", "antena", "antenas"},
    "orelhas": {"ear", "ears", "orelha", "orelhas"},
    "cauda": {"tail", "tails", "cauda"},
    "bico": {"beak", "bico"},
    "chifres": {"horn", "horns", "chifre", "chifres"},
    "nadadeiras": {"fin", "fins", "flipper", "nadadeira", "nadadeiras"},
    "tentaculos": {"tentacle", "tentacles", "tentaculo", "tentaculos"},
    "bracos": {"arm", "arms", "forearm", "hand", "hands", "braco", "bracos"},
    "pernas": {"leg", "legs", "foot", "feet", "paw", "paws", "shin", "perna", "pernas"},
    "pescoco": {"neck", "pescoco"},
    "cabeca": {"head", "skull", "cabeca", "cranio"},
    "corpo": {"body", "torso", "trunk", "corpo"},
}


def _ler(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def _palavras(nome: str) -> set[str]:
    # leftWing, wing_left e wing2 são equivalentes; forehead não vira head.
    nome = re.sub(r"([a-z])([A-Z])", r"\1 \2", str(nome))
    return set(re.findall(r"[a-z]+", chave(nome)))


def _tags(nomes: list[str]) -> tuple[list[str], dict[str, list[str]]]:
    motivos = {}
    for tag, termos in VOCABULARIO.items():
        encontrados = sorted({n for n in nomes if _palavras(n) & termos})
        if encontrados:
            motivos[tag] = encontrados[:12]
    return sorted(motivos), motivos


def _vec(valor=None) -> np.ndarray:
    return np.asarray(valor if valor is not None else [0, 0, 0], dtype=float)


def _transformacao(pivo, rotacao) -> np.ndarray:
    rot = bbmodelo.matriz_rotacao(rotacao)
    m = np.eye(4)
    m[:3, :3], m[:3, 3] = rot, pivo - rot @ pivo
    return m


def _normalizar(dados: dict) -> tuple[dict, list[dict], str, dict]:
    """Normalização interna apenas; esses dados nunca entram no resumo gravado."""
    grupos, cubos = {}, []
    if "elements" in dados:
        for i, grupo in enumerate(dados.get("groups", [])):
            gid = grupo.get("uuid", f"group-{i}")
            grupos[gid] = {**grupo, "pai": None}
        elementos = {e.get("uuid", f"element-{i}"): e for i, e in enumerate(dados["elements"])}
        pai_elemento = {}

        def percorrer(nodes, pai=None):
            for node in nodes:
                if isinstance(node, str):
                    pai_elemento[node] = pai
                    if node in grupos:
                        grupos[node]["pai"] = pai
                    continue
                gid = node.get("uuid", f"outliner-{len(grupos)}")
                grupos[gid] = {**grupos.get(gid, {}), **node, "pai": pai}
                percorrer(node.get("children", []), gid)

        percorrer(dados.get("outliner", []))
        for eid, e in elementos.items():
            if e.get("type", "cube") == "cube" and "from" in e and "to" in e:
                cubos.append({"nome": e.get("name", "cube"), "pai": pai_elemento.get(eid),
                              "de": _vec(e["from"]), "ate": _vec(e["to"]),
                              "rotacao": _vec(e.get("rotation")), "pivo": _vec(e.get("origin")),
                              "uv": "box" if e.get("box_uv", dados.get("meta", {}).get("box_uv", True)) else "por_face"})
        for g in grupos.values():
            g["nome"], g["pivo"], g["rotacao"] = g.get("name", "group"), _vec(g.get("origin")), _vec(g.get("rotation"))
        formato = dados.get("meta", {}).get("model_format", dados.get("model_format", "bbmodel"))
        return grupos, cubos, formato, dados.get("resolution", {})

    geometrias = dados.get("minecraft:geometry", [])
    if not geometrias:
        geometrias = [v for k, v in dados.items() if k.startswith("geometry.") and isinstance(v, dict)]
    if not geometrias:
        raise ValueError("arquivo não é .bbmodel nem geometria Bedrock")
    resolucoes = []
    for gi, geo in enumerate(geometrias):
        desc = geo.get("description", geo)
        resolucoes.append({"width": desc.get("texture_width", desc.get("texturewidth")),
                           "height": desc.get("texture_height", desc.get("textureheight"))})
        for bi, b in enumerate(geo.get("bones", [])):
            gid = f"{gi}:{b.get('name', bi)}"
            grupos[gid] = {"nome": b.get("name", "bone"),
                           "pai": f"{gi}:{b['parent']}" if b.get("parent") else None,
                           "pivo": _vec(b.get("pivot")), "rotacao": _vec(b.get("rotation"))}
            for c in b.get("cubes", []):
                inicio, tamanho = _vec(c.get("origin")), _vec(c.get("size"))
                cubos.append({"nome": c.get("name", b.get("name", "cube")), "pai": gid,
                              "de": inicio, "ate": inicio + tamanho,
                              "rotacao": _vec(c.get("rotation")), "pivo": _vec(c.get("pivot", b.get("pivot"))),
                              "uv": "por_face" if isinstance(c.get("uv"), dict) else "box"})
    return grupos, cubos, "bedrock_geometry", resolucoes[0]


def _matrizes(grupos: dict) -> dict:
    prontas = {}

    def fazer(gid, pilha=()):
        if gid in prontas:
            return prontas[gid]
        if gid in pilha:
            raise ValueError("hierarquia de ossos contém um ciclo")
        g = grupos[gid]
        pai = g.get("pai")
        base = fazer(pai, pilha + (gid,)) if pai in grupos else np.eye(4)
        prontas[gid] = base @ _transformacao(g["pivo"], g["rotacao"])
        return prontas[gid]

    for gid in grupos:
        fazer(gid)
    return prontas


def _nomes_ancestrais(grupos, gid) -> list[str]:
    nomes, vistos = [], set()
    while gid in grupos and gid not in vistos:
        vistos.add(gid)
        nomes.append(grupos[gid]["nome"])
        gid = grupos[gid].get("pai")
    return nomes


def _numero(valor):
    try:
        n = float(valor)
        return n if math.isfinite(n) else None
    except (TypeError, ValueError):
        return None


def _tem_expressao(valor) -> bool:
    if isinstance(valor, dict):
        metadados = {"lerp_mode", "easing", "interpolation", "easingArgs", "easing_args"}
        return any(_tem_expressao(v) for k, v in valor.items() if k not in metadados)
    if isinstance(valor, list):
        return any(_tem_expressao(v) for v in valor)
    return isinstance(valor, str) and _numero(valor) is None


def _resumo_clip(nome, clip, nomes_ossos: set[str], *, bedrock=False) -> dict:
    canais, n_chaves, expressao = Counter(), 0, False
    if bedrock:
        usados = set(clip.get("bones", {}))
        for b in clip.get("bones", {}).values():
            for canal, valor in b.items():
                if canal not in ("rotation", "position", "scale"):
                    continue
                canais[canal] += 1
                n_chaves += len(valor) if isinstance(valor, dict) else 1
                expressao |= _tem_expressao(valor)
        duracao = clip.get("animation_length")
    else:
        usados = set()
        for animador in clip.get("animators", {}).values():
            if animador.get("type", "bone") != "bone":
                continue
            if animador.get("name"):
                usados.add(animador["name"])
            for k in animador.get("keyframes", []):
                canais[k.get("channel", "desconhecido")] += 1
                n_chaves += 1
                expressao |= _tem_expressao(k.get("data_points", []))
        duracao = clip.get("length")
    return {"nome": nome, "duracao_s": _numero(duracao), "loop": clip.get("loop"),
            "ossos_animados": len(usados), "ossos_ausentes": sorted(usados - nomes_ossos),
            "chaves": n_chaves, "canais": dict(canais), "usa_expressoes": bool(expressao)}


@lru_cache(maxsize=8)
def _biblioteca(path: str, mtime: int):
    return _ler(Path(path)).get("animations", {})


def inspecionar(caminho, *, dados=None, biblioteca=None) -> dict:
    """Resumo agregado de um arquivo explícito; não modifica o modelo original."""
    path = Path(caminho).resolve()
    bruto = _ler(path)
    grupos, cubos, formato, res = _normalizar(bruto)
    mats = _matrizes(grupos)
    volumes, pontos, pontos_cabeca, regioes = [], [], [], Counter()
    cubos_rotacionados = 0
    for c in cubos:
        tamanho = np.abs(c["ate"] - c["de"])
        volume = float(np.prod(tamanho))
        volumes.append(volume)
        ancestrais = _nomes_ancestrais(grupos, c["pai"])
        tags_ancestrais = set(_tags([c["nome"]] + ancestrais)[0])
        regiao = "cabeca" if "cabeca" in tags_ancestrais else "corpo" if "corpo" in tags_ancestrais else "outros"
        regioes[regiao] += volume
        herdada = any(np.any(grupos[g]["rotacao"]) for g in _ancestrais_ids(grupos, c["pai"]))
        cubos_rotacionados += bool(np.any(c["rotacao"]) or herdada)
        cantos = np.asarray(list(itertools.product(*zip(c["de"], c["ate"]))), dtype=float)
        m = mats.get(c["pai"], np.eye(4)) @ _transformacao(c["pivo"], c["rotacao"])
        mundo = bbmodelo.aplicar(m, cantos)
        pontos.extend(mundo)
        if regiao == "cabeca":
            pontos_cabeca.extend(mundo)
    tamanho = np.ptp(pontos, axis=0) if pontos else np.zeros(3)
    altura = max(float(tamanho[1]), 1e-9)
    total_volume = sum(volumes)
    nomes_ossos = {g["nome"] for g in grupos.values()}
    tags, motivos = _tags(sorted(nomes_ossos) + [c["nome"] for c in cubos])
    planos = sum(v <= 1e-9 for v in volumes)
    n = len(cubos)
    resumo = {
        "arquivo": str(path), "nome": bruto.get("name", path.name.removesuffix(".geo.json").removesuffix(".bbmodel")),
        "formato": formato, "contagem": {"pecas": n, "solidos": n - planos, "planos": planos, "ossos": len(grupos)},
        "orcamento_observado": {"pecas": n, "nota": "observação da referência, não meta para a criatura nova"},
        "tags": tags, "motivos_tags": motivos, "nomes_ossos": sorted(nomes_ossos),
        "rotacoes": {"pecas_com_rotacao_propria_ou_herdada": cubos_rotacionados,
                      "fracao": round(cubos_rotacionados / n, 4) if n else 0},
        "proporcoes": {"largura_altura": round(float(tamanho[0]) / altura, 4),
                       "profundidade_altura": round(float(tamanho[2]) / altura, 4)},
        "volumes": {"metrica": "soma das caixas locais sólidas, sem descontar sobreposição ou inflate",
                    "fracao_por_regiao": {k: round(v / total_volume, 4) if total_volume else 0 for k, v in sorted(regioes.items())},
                    "maior_peca_fracao": round(max(volumes, default=0) / total_volume, 4) if total_volume else 0},
        "texturas": {"resolucao_uv": [res.get("width"), res.get("height")],
                     "quantidade": len(bruto.get("textures", [])),
                     "dimensoes": [[t.get("width"), t.get("height")] for t in bruto.get("textures", [])],
                     "uv": dict(Counter(c["uv"] for c in cubos))},
        "animacoes": {"incorporadas": [], "selecionadas": [], "selecao_informada": bool(dados)},
        "limites": ["Tags descrevem nomes de peças/ossos; confirmar a função olhando as vistas.",
                    "Volumes e proporções são medidas agregadas; não constituem molde ou transferência de rig."],
    }
    if pontos_cabeca:
        resumo["proporcoes"]["altura_cabeca_fracao"] = round(float(np.ptp(pontos_cabeca, axis=0)[1]) / altura, 4)
    if n and total_volume and max(volumes) / total_volume >= 0.8 and not set(tags) & {"pernas", "bracos", "asas"}:
        resumo["tags"].append("corpo-dominante")
        resumo["motivos_tags"]["corpo-dominante"] = ["uma caixa reúne ao menos 80% do volume; sem nomes de membros reconhecidos"]
    animacoes = bruto.get("animations", [])
    if isinstance(animacoes, dict):
        resumo["animacoes"]["incorporadas"] = [_resumo_clip(k, a, nomes_ossos, bedrock=True) for k, a in animacoes.items()]
    else:
        resumo["animacoes"]["incorporadas"] = [_resumo_clip(a.get("name", "animation"), a, nomes_ossos) for a in animacoes]
    if dados:
        especie = _ler(Path(dados))
        resumo["evo_stage"] = especie.get("evo_stage")
        pedidos = especie.get("anims", [])
        pedidos = list(pedidos.values()) if isinstance(pedidos, dict) else pedidos
        libs = _biblioteca(str(Path(biblioteca).resolve()), Path(biblioteca).stat().st_mtime_ns) if biblioteca else {}
        for pedido in pedidos if isinstance(pedidos, list) else []:
            if not isinstance(pedido, str):
                continue
            matches = [k for k in libs if k == pedido or k.endswith("." + pedido)]
            if len(matches) == 1:
                clip = _resumo_clip(matches[0], libs[matches[0]], nomes_ossos, bedrock=True)
                clip.update({"solicitada": pedido, "encontrada": True})
            else:
                clip = {"solicitada": pedido, "encontrada": False,
                        "motivo": "nome ambíguo" if matches else "não encontrada na biblioteca informada"}
            resumo["animacoes"]["selecionadas"].append(clip)
    return resumo


def _ancestrais_ids(grupos, gid):
    vistos = set()
    while gid in grupos and gid not in vistos:
        vistos.add(gid)
        yield gid
        gid = grupos[gid].get("pai")


def _resolver(raiz, valor):
    if not valor:
        return None
    path = (raiz / str(valor).replace("\\", "/")).resolve()
    if not path.is_relative_to(raiz.resolve()):
        raise ValueError(f"índice aponta para fora da biblioteca: {valor}")
    return path


def _entradas(raiz: Path) -> list[dict]:
    indice = raiz / "indice-modelos.json"
    if indice.exists():
        rows = _ler(indice)
    elif (raiz / "resumo.json").exists() and isinstance(_ler(raiz / "resumo.json"), list):
        rows = _ler(raiz / "resumo.json")
    else:
        # Somente subbibliotecas imediatas conhecidas; não varre o computador.
        return [e for p in sorted(raiz.iterdir()) if p.is_dir() and
                ((p / "indice-modelos.json").exists() or (p / "resumo.json").exists()) for e in _entradas(p)]
    resultado = []
    for r in rows:
        editaveis = [_resolver(raiz, v) for v in r.get("bbmodel", [])]
        geo = _resolver(raiz, r.get("modelo") or r.get("arquivo"))
        if geo and geo.name.endswith(".geo.json"):
            editaveis.append(geo.with_name(geo.name.removesuffix(".geo.json") + ".bbmodel"))
        model = next((p for p in editaveis if p.exists()), geo)
        if not model or not model.exists():
            continue
        dados = _resolver(raiz, r.get("dados"))
        biblioteca = raiz / "animacoes" / "digimons_anims.json"
        resultado.append({"nome": r.get("nome", model.stem), "estagio": r.get("estagio"),
                          "evo_stage": r.get("evo_stage"), "biblioteca": str(raiz),
                          "arquivo": str(model), "geo": str(geo) if geo else None,
                          "dados": str(dados) if dados and dados.exists() else None,
                          "biblioteca_animacoes": str(biblioteca) if biblioteca.exists() else None,
                          "pecas": r.get("cubos_e_planos"), "tags": []})
    return resultado


def catalogar(biblioteca=BIBLIOTECA_PADRAO, *, analisar=False) -> list[dict]:
    """Lê índices existentes; análise semântica usa cache agregado incremental externo."""
    raiz = Path(biblioteca).expanduser().resolve()
    if not raiz.is_dir():
        raise ValueError(f"biblioteca não encontrada: {raiz}")
    rows = _entradas(raiz)
    if not analisar:
        return rows
    cache_path = raiz / CACHE
    try:
        cache = _ler(cache_path)
    except (OSError, ValueError):
        cache = {}
    cache_valido = isinstance(cache, dict) and cache.get("versao") == VERSAO
    cache = cache if cache_valido else {"versao": VERSAO, "arquivos": {}}
    alterado = not cache_valido
    for row in rows:
        path = Path(row["arquivo"])
        # Também invalida quando seleção de animações ou biblioteca muda.
        sources = [Path(p) for p in (row["arquivo"], row["dados"], row["biblioteca_animacoes"]) if p]
        assinatura = [[str(p), p.stat().st_mtime_ns, p.stat().st_size] for p in sources]
        cached = cache["arquivos"].get(str(path))
        if not cached or cached.get("assinatura") != assinatura:
            try:
                resumo = inspecionar(path, dados=row["dados"], biblioteca=row["biblioteca_animacoes"])
            except (OSError, ValueError, KeyError, TypeError) as e:
                resumo = {"erro": str(e)}
            cached = {"assinatura": assinatura, "resumo": resumo}
            cache["arquivos"][str(path)] = cached
            alterado = True
        row["estrutura"] = cached["resumo"]
        row["tags"] = cached["resumo"].get("tags", [])
        row["pecas"] = cached["resumo"].get("contagem", {}).get("pecas", row["pecas"])
    if alterado:
        cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    return rows


def buscar(biblioteca=BIBLIOTECA_PADRAO, consulta="", *, tags=(), estagio=None, limite=10) -> list[dict]:
    """Busca por nome ou indícios semânticos; filtros são explícitos e não taxonomia garantida."""
    rows = catalogar(biblioteca, analisar=bool(consulta or tags))
    tag_set = {chave(t).replace(" ", "-") for t in tags}
    palavras = chave(consulta).split()
    selecionados = []
    for row in rows:
        if estagio is not None and chave(str(estagio)) not in (chave(str(row.get("estagio"))), chave(str(row.get("evo_stage")))):
            continue
        if tag_set and not tag_set <= set(row["tags"]):
            continue
        campo = chave(" ".join([row["nome"], *row["tags"], *row.get("estrutura", {}).get("nomes_ossos", [])]))
        if palavras and not all(p in campo for p in palavras):
            continue
        score = (10 if chave(row["nome"]) == chave(consulta) else 0) + len(set(palavras) & set(chave(row["nome"]).split()))
        selecionados.append((score, row))
    return [r for _, r in sorted(selecionados, key=lambda pair: (-pair[0], pair[1]["nome"]))[:max(0, limite)]]


def opcoes(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("acao", choices=("listar", "buscar", "inspecionar"))
    parser.add_argument("alvo", nargs="?", help="texto para buscar ou caminho explícito do modelo")
    parser.add_argument("--biblioteca", type=Path, default=BIBLIOTECA_PADRAO, help="pasta externa que contém os índices")
    parser.add_argument("--tag", action="append", default=[], help="indício semântico; pode repetir (ex.: asas, penas)")
    parser.add_argument("--estagio", help="rótulo do índice ou evo_stage (ex.: 'Baby II', 1)")
    parser.add_argument("--limite", type=int, default=10)
    parser.add_argument("--dados", type=Path, help="JSON da espécie para inspecionar animações selecionadas")
    parser.add_argument("--animacoes", type=Path, help="biblioteca Bedrock de animações para a inspeção")
    parser.add_argument("--saida", type=Path, help="gravar somente o resumo agregado em JSON")


def cmd_referencias(args) -> int:
    try:
        if args.acao == "inspecionar":
            if not args.alvo:
                raise ValueError("inspecionar precisa de um caminho explícito")
            result = inspecionar(args.alvo, dados=args.dados, biblioteca=args.animacoes)
            c = result["contagem"]
            a = result["animacoes"]
            selecao = f"{len(a['selecionadas'])} selecionadas na espécie" if a['selecao_informada'] else "seleção da espécie não informada (--dados)"
            linhas = [f"{result['nome']}: {c['pecas']} peças ({c['solidos']} sólidas, {c['planos']} planos), {c['ossos']} ossos",
                      f"  UV {result['texturas']['resolucao_uv']}; rotacionadas {result['rotacoes']['fracao']:.0%}",
                      f"  tags por nomes: {', '.join(result['tags']) or 'nenhuma — conferir visualmente'}",
                      f"  animações: {len(a['incorporadas'])} incorporadas; {selecao}"]
        else:
            if args.acao == "buscar" and not (args.alvo or args.tag or args.estagio):
                raise ValueError("buscar precisa de texto, --tag ou --estagio")
            result = buscar(args.biblioteca, args.alvo or "", tags=args.tag, estagio=args.estagio, limite=args.limite)
            linhas = [f"referências: {len(result)} resultado(s) (limite {args.limite})"]
            linhas += [f"  {r['nome']}: {r['pecas'] if r['pecas'] is not None else '?'} peças; {r['estagio'] or 'estágio não informado'}; {', '.join(r['tags'])}" for r in result[:16]]
            linhas.append("Tags são indícios nos nomes; confirme a função nas vistas antes de usar.")
        if args.saida:
            args.saida.parent.mkdir(parents=True, exist_ok=True)
            args.saida.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            linhas.append(f"resumo: {args.saida}")
        relatorio.imprimir(linhas)
        return 0
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"referências: {e}")
        return 1
