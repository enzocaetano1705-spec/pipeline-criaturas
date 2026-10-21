"""`criaturas ficha <pasta>`: lê docs/criaturas/<nome>/ficha.md e grava modelos/<nome>/entrada.json.

Formato da ficha: docs/criaturas/_modelo/ficha.md. Requisitos das imagens: docs/criaturas/LEIA-ME.md.
"""

import re
from pathlib import Path

import yaml
from PIL import Image

from criaturas import relatorio, tabelas
from criaturas.caminhos import pasta_modelo, relativo
from criaturas.etapas import etapa
from criaturas.relatorio import msg

NOME_MODELO = "nome-da-linhagem"
VISTAS = ("conceito", "frente", "lado", "costas")
LADO_MIN, LADO_MAX = 1024, 1536

# rótulo do campo na ficha (sem acento, minúsculo) -> chave em entrada.json
CAMPOS = {
    "estagio": "estagio",
    "categoria seu palpite": "categoria_palpite",
    "categoria confirmada": "categoria_confirmada",
    "altura no jogo blocos": "altura_blocos",
    "imagens": "imagens_listadas",
    "o que a imagem nao mostra bem": "nao_mostra",
    "partes finas viram planos": "partes_finas",
    "rosto": "rosto",
    "jeito de se mover": "movimento",
}


class FichaInvalida(ValueError):
    pass


def separar_frontmatter(texto: str) -> tuple[dict, str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", texto, re.S)
    if not m:
        raise FichaInvalida("a ficha não começa com o bloco --- de frontmatter")
    meta = yaml.safe_load(m.group(1)) or {}
    if not isinstance(meta, dict):
        raise FichaInvalida("o frontmatter não é um dicionário YAML")
    return meta, m.group(2)


def _sem_comentarios(texto: str) -> str:
    return re.sub(r"<!--.*?-->", "", texto, flags=re.S)


def _linha_negrito(corpo: str, rotulo: str) -> str:
    m = re.search(rf"^\*\*{re.escape(rotulo)}[^*]*\*\*\s*(.*)$", corpo, re.M)
    return m.group(1).strip() if m else ""


def _secoes_estagio(corpo: str) -> list[tuple[int, str, str]]:
    """[(numero, nome, texto da seção)] para cada '## Estágio N — Nome'."""
    padrao = re.compile(r"^##\s+Est[aá]gio\s+(\d+)\s*(?:[—–-]\s*(.*))?$", re.M)
    achados = list(padrao.finditer(corpo))
    secoes = []
    for i, m in enumerate(achados):
        fim = achados[i + 1].start() if i + 1 < len(achados) else len(corpo)
        proxima = re.search(r"^##\s", corpo[m.end():fim], re.M)
        if proxima:
            fim = m.end() + proxima.start()
        secoes.append((int(m.group(1)), (m.group(2) or "").strip(), corpo[m.end():fim]))
    return secoes


def _campos(secao: str) -> dict:
    campos = {}
    for m in re.finditer(r"^-\s*\*\*(.+?):?\*\*:?\s*(.*)$", secao, re.M):
        rotulo = tabelas.chave(m.group(1))
        if rotulo in CAMPOS:
            campos[CAMPOS[rotulo]] = m.group(2).strip()
    return campos


def _prompt(secao: str) -> str:
    m = re.search(r"###\s*Prompt usado\s*\n```[a-z]*\n(.*?)```", secao, re.S)
    texto = m.group(1).strip() if m else ""
    return "" if texto.startswith("cole aqui") else texto


def _categoria(texto: str):
    """'quadrúpede › canídeo' (ou com >, /, -) -> {'plano', 'nicho'}; None se vazio."""
    if not texto:
        return None
    partes = [p.strip() for p in re.split(r"\s*(?:›|>|»|→)\s*", texto) if p.strip()]
    if len(partes) != 2:
        raise ValueError(f"use 'plano › nicho' (recebi: {texto})")
    try:
        plano = tabelas.resolver_categoria(partes[0], "plano")[1]
    except tabelas.CategoriaDesconhecida:
        raise ValueError(f"'{partes[0]}' não é um plano de corpo conhecido") from None
    try:
        nicho = tabelas.resolver_categoria(partes[1], "nicho")[1]
    except tabelas.CategoriaDesconhecida:
        raise ValueError(f"'{partes[1]}' não é um nicho conhecido") from None
    return {"plano": plano, "nicho": nicho}


def _numero(texto: str):
    if not texto:
        return None
    m = re.search(r"\d+(?:[.,]\d+)?", texto)
    return float(m.group(0).replace(",", ".")) if m else None


def _conferir_imagem(caminho: Path, eid: str, vista: str, avisos: list) -> None:
    try:
        with Image.open(caminho) as im:
            maior = max(im.size)
    except OSError:
        avisos.append(msg("imagem_ilegivel", f"{eid}: {caminho.name} não abre como imagem"))
        return
    if not LADO_MIN <= maior <= LADO_MAX:
        avisos.append(msg("tamanho_imagem", f"{eid}: {caminho.name} tem lado maior {maior} px (recomendado {LADO_MIN}–{LADO_MAX})"))


def ler_ficha(pasta: Path) -> dict:
    """Normaliza a ficha num dict no formato do contrato `entrada` (com erros e avisos)."""
    pasta = Path(pasta)
    arquivo = pasta / "ficha.md"
    if not arquivo.exists():
        raise FichaInvalida(f"não achei {relativo(arquivo)}")
    meta, corpo = separar_frontmatter(arquivo.read_text(encoding="utf-8"))
    corpo = _sem_comentarios(corpo)
    erros, avisos = [], []

    nome = str(meta.get("nome") or "")
    if not nome:
        erros.append(msg("sem_nome", "frontmatter sem 'nome'"))
    elif nome == NOME_MODELO:
        erros.append(msg("nome_modelo", "'nome' ainda é o do modelo (nome-da-linhagem)"))
    elif not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", nome):
        erros.append(msg("nome_invalido", f"'nome' deve ter minúsculas, sem acento, com hífen: {nome}"))
    if nome and nome != NOME_MODELO and nome != pasta.name:
        avisos.append(msg("nome_pasta", f"'nome' ({nome}) difere do nome da pasta ({pasta.name})"))

    status = meta.get("status", "rascunho")
    if status == "rascunho":
        avisos.append(msg("rascunho", "ficha com status: rascunho; o pipeline só modela pronta-para-modelagem"))
    destino = meta.get("destino") or []
    destino = [destino] if isinstance(destino, str) else list(destino)
    if not destino:
        erros.append(msg("sem_destino", "frontmatter sem 'destino' (roblox e/ou minecraft)"))
    estilo = meta.get("estilo", "cobblemon")
    n_estagios = meta.get("estagios")

    titulo_m = re.search(r"^#\s+(.+)$", corpo, re.M)
    titulo = titulo_m.group(1).strip() if titulo_m else ""
    ideia = _linha_negrito(corpo, "Ideia em uma frase")
    motivos = _linha_negrito(corpo, "Motivos que atravessam a linhagem")
    if not ideia:
        avisos.append(msg("sem_ideia", "'Ideia em uma frase' vazia"))
    if not motivos:
        avisos.append(msg("sem_motivos", "'Motivos que atravessam a linhagem' vazio"))

    estagios = []
    for numero, nome_est, secao in _secoes_estagio(corpo):
        eid = f"e{numero}"
        campos = _campos(secao)
        texto_est = campos.get("estagio", "")
        est_tabela = None
        try:
            est_tabela = tabelas.resolver_estagio(texto_est)
        except KeyError:
            erros.append(msg("estagio_invalido", f"{eid}: 'Estágio' não reconhecido: {texto_est}"))
        if not texto_est:
            erros.append(msg("sem_estagio", f"{eid}: campo 'Estágio' vazio (ex.: 1 de 3)"))

        confirmada = None
        try:
            confirmada = _categoria(campos.get("categoria_confirmada", ""))
        except (ValueError, KeyError) as e:
            erros.append(msg("categoria_invalida", f"{eid}: 'Categoria confirmada' — {str(e).strip(chr(39))}"))
        if not campos.get("categoria_palpite"):
            avisos.append(msg("sem_palpite", f"{eid}: 'Categoria (seu palpite)' vazia"))

        altura = _numero(campos.get("altura_blocos", ""))
        if campos.get("altura_blocos") and altura is None:
            erros.append(msg("altura_invalida", f"{eid}: 'Altura no jogo' não é um número"))

        imagens = {}
        for vista in VISTAS:
            caminho = pasta / f"{eid}-{vista}.png"
            imagens[vista] = caminho.name if caminho.exists() else None
            if caminho.exists():
                _conferir_imagem(caminho, eid, vista, avisos)
        if not imagens["conceito"]:
            erros.append(msg("sem_conceito", f"{eid}: falta {eid}-conceito.png (obrigatória)"))
        for vista in ("frente", "lado"):
            if not imagens[vista]:
                texto = f"{eid}: falta {eid}-{vista}.png"
                if vista == "lado":
                    texto += " (a profundidade será estimada pela tabela)"
                avisos.append(msg(f"sem_{vista}", texto))

        prompt = _prompt(secao)
        if not prompt:
            erros.append(msg("sem_prompt", f"{eid}: falta o prompt usado na imagem principal"))
        for campo, rotulo in (("nao_mostra", "O que a imagem não mostra bem"), ("partes_finas", "Partes finas"),
                              ("rosto", "Rosto"), ("movimento", "Jeito de se mover")):
            if not campos.get(campo):
                avisos.append(msg(f"sem_{campo}", f"{eid}: '{rotulo}' vazio"))

        estagios.append({
            "id": eid,
            "nome": nome_est if nome_est and nome_est != "Nome" else "",
            "estagio": texto_est,
            "estagio_tabela": est_tabela,
            "estagio_cobblemon": tabelas.estagio_cobblemon(texto_est) if texto_est else None,
            "categoria_palpite": campos.get("categoria_palpite") or None,
            "categoria_confirmada": confirmada,
            "altura_blocos": altura,
            "imagens": imagens,
            "nao_mostra": campos.get("nao_mostra", ""),
            "partes_finas": campos.get("partes_finas", ""),
            "rosto": campos.get("rosto", ""),
            "movimento": campos.get("movimento", ""),
            "prompt": prompt,
        })

    if not estagios:
        erros.append(msg("sem_estagios", "nenhuma seção '## Estágio N — Nome' na ficha"))
    if isinstance(n_estagios, int) and n_estagios != len(estagios):
        erros.append(msg("n_estagios", f"frontmatter diz estagios: {n_estagios}, mas a ficha tem {len(estagios)} seção(ões)"))
    linhagem = pasta / "linhagem.png"
    if not linhagem.exists() and len(estagios) > 1:
        avisos.append(msg("sem_linhagem", "falta linhagem.png (recomendada)"))

    return {
        "nome": nome if re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", nome or "") else pasta.name.strip("_") or "sem-nome",
        "titulo": titulo,
        "status": status if status in ("rascunho", "pronta-para-modelagem", "em-modelagem", "modelada") else "rascunho",
        "destino": [d for d in destino if d in ("roblox", "minecraft")] or ["roblox"],
        "estilo": estilo if estilo in ("cobblemon", "digimod") else "cobblemon",
        "pasta": relativo(pasta),
        "ideia": ideia,
        "motivos": motivos,
        "imagem_linhagem": linhagem.name if linhagem.exists() else None,
        "estagios": estagios,
        "erros": erros,
        "avisos": avisos,
    }


@etapa("ficha")
def cmd_ficha(args) -> int:
    pasta = Path(args.pasta)
    try:
        entrada = ler_ficha(pasta)
    except FichaInvalida as e:
        print(f"ficha: {e}")
        return 1
    destino = pasta_modelo(pasta.resolve().name)
    caminho = relatorio.gravar_json(destino / "entrada.json", entrada, "entrada")
    relatorio.registrar(destino, entrada["nome"], None, "ficha", not entrada["erros"],
                        erros=entrada["erros"], avisos=entrada["avisos"], arquivos=[relativo(caminho)],
                        resumo={"estagios": len(entrada["estagios"]), "status": entrada["status"]})
    linhas = [f"ficha {entrada['nome']}: {len(entrada['estagios'])} estágio(s), status {entrada['status']}"]
    for e in entrada["estagios"]:
        vistas = ", ".join(v for v, arq in e["imagens"].items() if arq) or "nenhuma imagem"
        cat = e["categoria_confirmada"]
        cat = f"{cat['plano']} › {cat['nicho']}" if cat else "categoria não confirmada"
        linhas.append(f"  {e['id']} {e['estagio'] or '?'} ({e['estagio_tabela'] or '?'}): {vistas}; {cat}")
    linhas += relatorio.linhas_mensagens("Erros", entrada["erros"], 8)
    linhas += relatorio.linhas_mensagens("Avisos", entrada["avisos"], 4)
    linhas.append(f"gravado: {relativo(caminho)}")
    relatorio.imprimir(linhas)
    return 1 if entrada["erros"] else 0
