"""Acompanhamento do .bbmodel entre o pipeline e as edições à mão no Blockbench.

Depois de cada escrita do pipeline, o arquivo é copiado para eN/.estado/ultimo.bbmodel e o hash vai
para o relatório. Se o arquivo mudou fora do pipeline, `adotar` compara com essa cópia, registra o
que mudou em eN/historico.jsonl e passa a tratar a versão do usuário como a atual. As etapas
seguintes trabalham em cima dela; nada que o usuário fez é desfeito.
"""

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

import numpy as np

from criaturas import bbmodelo, relatorio
from criaturas.relatorio import msg

PASTA_ESTADO = ".estado"


def sha256(caminho: Path) -> str:
    return hashlib.sha256(Path(caminho).read_bytes()).hexdigest()


def _retrato(destino: Path) -> Path:
    return Path(destino) / PASTA_ESTADO / "ultimo.bbmodel"


def registrar(destino: Path, arquivo: Path) -> str:
    """Guarda o retrato do arquivo como o último estado conhecido. Devolve o hash."""
    r = _retrato(destino)
    r.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(arquivo, r)
    return sha256(arquivo)


def historico(destino: Path, origem: str, texto: str, mudancas: list[str] | None = None, **extra) -> None:
    linha = {"quando": datetime.now().isoformat(timespec="seconds"), "origem": origem, "texto": texto,
             "mudancas": mudancas or [], **extra}
    with (Path(destino) / "historico.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(linha, ensure_ascii=False) + "\n")


def ler_historico(destino: Path, ultimas: int = 10) -> list[dict]:
    arq = Path(destino) / "historico.jsonl"
    if not arq.exists():
        return []
    return [json.loads(l) for l in arq.read_text(encoding="utf-8").splitlines() if l.strip()][-ultimas:]


# ---------- diferença ----------

def _hash_json(dados) -> str:
    return hashlib.sha256(json.dumps(dados, sort_keys=True, default=str).encode()).hexdigest()[:12]


def _animacoes(modelo: bbmodelo.Modelo) -> dict[str, str]:
    saida = {}
    for a in modelo.animacoes:
        chaves = sorted((an.get("name"), k["channel"], round(float(k["time"]), 4), json.dumps(k["data_points"], sort_keys=True))
                        for an in a.get("animators", {}).values() for k in an.get("keyframes", []))
        saida[a["name"]] = _hash_json([a.get("length"), a.get("loop"), chaves])
    return saida


def _textura(modelo: bbmodelo.Modelo) -> str | None:
    fontes = [t.get("source", "") for t in modelo.bruto.get("textures", [])]
    return _hash_json(fontes) if fontes else None


def diferenca(antes: bbmodelo.Modelo, depois: bbmodelo.Modelo) -> dict:
    """O que mudou de `antes` para `depois`, em listas curtas e legíveis."""
    m = []
    ca, cd = {c.nome: c for c in antes.cubos}, {c.nome: c for c in depois.cubos}
    for n in sorted(set(cd) - set(ca)):
        c = cd[n]
        m.append(f"cubo novo {n} em {c.osso} ({(c.ate - c.de).round(2).tolist()})")
    for n in sorted(set(ca) - set(cd)):
        m.append(f"cubo removido {n}")
    for n in sorted(set(ca) & set(cd)):
        a, d = ca[n], cd[n]
        partes = []
        if not (np.allclose(a.de, d.de) and np.allclose(a.ate, d.ate)):
            if np.allclose(a.ate - a.de, d.ate - d.de):
                partes.append(f"movido {(d.de - a.de).round(2).tolist()}")
            else:
                partes.append(f"tamanho {(a.ate - a.de).round(2).tolist()} -> {(d.ate - d.de).round(2).tolist()}")
        if not np.allclose(a.rotacao, d.rotacao):
            partes.append(f"rotação {d.rotacao.round(1).tolist()}")
        if a.osso != d.osso:
            partes.append(f"osso {a.osso} -> {d.osso}")
        if a.faces != d.faces and not partes:
            partes.append("UV")
        if partes:
            m.append(f"cubo {n}: " + ", ".join(partes))
    oa, od = antes.ossos, depois.ossos
    for n in sorted(set(od) - set(oa)):
        m.append(f"osso novo {n} (pai {od[n].pai})")
    for n in sorted(set(oa) - set(od)):
        m.append(f"osso removido {n}")
    for n in sorted(set(oa) & set(od)):
        a, d = oa[n], od[n]
        if a.pai != d.pai or not np.allclose(a.origem, d.origem) or not np.allclose(a.rotacao, d.rotacao):
            m.append(f"osso {n}: pivô {d.origem.round(2).tolist()}, rotação {d.rotacao.round(1).tolist()}, pai {d.pai}")
    la, ld = {l.nome: l for l in antes.locators}, {l.nome: l for l in depois.locators}
    for n in sorted(set(ld) ^ set(la)):
        m.append(f"locator {'novo' if n in ld else 'removido'} {n}")
    for n in sorted(set(la) & set(ld)):
        if not np.allclose(la[n].posicao, ld[n].posicao):
            m.append(f"locator {n} movido para {ld[n].posicao.round(2).tolist()}")
    aa, ad = _animacoes(antes), _animacoes(depois)
    animacoes_mudadas = sorted(n for n in set(aa) | set(ad) if aa.get(n) != ad.get(n))
    for n in animacoes_mudadas:
        estado = "nova" if n not in aa else "removida" if n not in ad else "alterada"
        m.append(f"animação {n} {estado}")
    textura = _textura(antes) != _textura(depois)
    if textura:
        m.append("textura alterada")
    return {"mudancas": m, "animacoes": animacoes_mudadas, "textura": textura}


# ---------- adoção ----------

def adotar(destino: Path, arquivo: Path, nome: str, estagio: str) -> dict | None:
    """Se o arquivo mudou desde o último estado do pipeline, registra e adota. Devolve a diferença (ou None)."""
    destino = Path(destino)
    rel_arq = destino / "relatorio.json"
    rel = relatorio.ler_json(rel_arq) if rel_arq.exists() else {}
    esperado = rel.get("hashes", {}).get(arquivo.name)
    atual = sha256(arquivo)
    if esperado is None or esperado == atual:
        return None
    retrato = _retrato(destino)
    dif = diferenca(bbmodelo.ler(retrato), bbmodelo.ler(arquivo)) if retrato.exists() else \
        {"mudancas": ["(sem retrato anterior: mudanças não detalhadas)"], "animacoes": [], "textura": False}
    historico(destino, "mao", "edição no Blockbench adotada", dif["mudancas"], animacoes=dif["animacoes"], textura=dif["textura"])
    # o que o usuário mexeu à mão fica protegido contra regeneração automática
    protegidas = set(rel.get("protegido", {}).get("animacoes", [])) | set(dif["animacoes"])
    protegido = {"animacoes": sorted(protegidas), "textura": bool(rel.get("protegido", {}).get("textura")) or dif["textura"]}
    registrar(destino, arquivo)
    relatorio.registrar(destino, nome, estagio, "adotar", True, avisos=[msg("mao", t) for t in dif["mudancas"][:20]],
                        resumo={"mudancas": len(dif["mudancas"])}, hashes={arquivo.name: atual})
    rel = relatorio.ler_json(rel_arq)
    rel["protegido"] = protegido
    relatorio.gravar_json(rel_arq, rel)
    return dif


def protegido(destino: Path) -> dict:
    rel_arq = Path(destino) / "relatorio.json"
    rel = relatorio.ler_json(rel_arq) if rel_arq.exists() else {}
    return rel.get("protegido", {"animacoes": [], "textura": False})


def depois_de_escrever(destino: Path, arquivo: Path) -> dict[str, str]:
    """Chame depois que o pipeline escreveu o .bbmodel: atualiza o retrato e devolve {arquivo: hash} para o relatório."""
    return {Path(arquivo).name: registrar(destino, arquivo)}


def liberar(destino: Path, textura: bool = False, animacoes: list[str] | None = None) -> None:
    """Tira a proteção (o usuário pediu para regenerar com --forcar)."""
    rel_arq = Path(destino) / "relatorio.json"
    if not rel_arq.exists():
        return
    rel = relatorio.ler_json(rel_arq)
    p = rel.get("protegido", {"animacoes": [], "textura": False})
    if textura:
        p["textura"] = False
    if animacoes:
        p["animacoes"] = [a for a in p.get("animacoes", []) if a not in animacoes]
    rel["protegido"] = p
    relatorio.gravar_json(rel_arq, rel)


def adotar_e_avisar(destino: Path, arquivo: Path, nome: str, estagio: str, etapa: str) -> None:
    dif = adotar(destino, arquivo, nome, estagio)
    if dif:
        print(f"{etapa}: adotei a sua edição no Blockbench ({len(dif['mudancas'])} mudança(s); ver historico.jsonl)")
