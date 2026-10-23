"""Catálogo local, perfil físico e receitas do preparo Roblox. Não altera as fontes artísticas."""
import hashlib
import json
from pathlib import Path

import numpy as np

from criaturas import bbmodelo
from criaturas.render import CANTOS_FACE


def hash_arquivo(arquivo: Path) -> str:
    return hashlib.sha256(arquivo.read_bytes()).hexdigest()


def hash_config(criatura: dict) -> str:
    campos = ("nome", "fonte", "arquivo", "escala_studio", "colisao", "material_pbr", "espelhar_atlas", "superamostrar")
    return hashlib.sha256(json.dumps({k:criatura.get(k) for k in campos}, sort_keys=True).encode()).hexdigest()


def perfil_colisao(arquivo: Path, osso: str = "body", nomes: list[str] | None = None) -> dict:
    """Envelope do corpo sólido no referencial do Bone, em unidades Blockbench.

    Não usa a caixa inteira da criatura. Planos, crista, asas, cauda e ossos filhos
    não ampliam o bloqueio de locomoção. Outros corpos podem escolher osso/cubos explicitamente.
    """
    modelo = bbmodelo.ler(arquivo)
    if osso not in modelo.ossos:
        raise ValueError(f"falta o osso de colisão {osso!r}; configure a parte física")
    cubos = [c for c in modelo.cubos if c.osso == osso and np.all(c.tamanho > 1e-5)
             and (nomes is None or c.nome in nomes)]
    if nomes and set(nomes) != {c.nome for c in cubos}:
        raise ValueError("peças de colisão ausentes, planas ou em outro osso")
    if not cubos:
        raise ValueError(f"nenhum volume sólido em {osso!r}; configure a parte física")
    matrizes = bbmodelo.matrizes_ossos(modelo)
    bone = np.eye(4)
    bone[:3, 3] = modelo.ossos[osso].origem
    inversa = np.linalg.inv(matrizes[osso] @ bone)
    pontos = np.concatenate([bbmodelo.aplicar(inversa @ bbmodelo.matriz_cubo(modelo, c, matrizes),
                                            bbmodelo.cantos(c)) for c in cubos])
    return {"versao": 1, "osso": osso, "min": pontos.min(0).round(6).tolist(),
            "max": pontos.max(0).round(6).tolist(), "cubos": [c.nome for c in cubos],
            "tipo": "corpo_estatico_ate_o_chao", "fonte_sha256": hash_arquivo(arquivo)}


def retangulos_mascara(mascara: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Une spans iguais em linhas consecutivas sem preencher nenhum pixel transparente."""
    mascara = np.asarray(mascara,bool)
    horizontais = _retangulos_linhas(mascara)
    verticais = [(y0,x0,y1,x1) for x0,y0,x1,y1 in _retangulos_linhas(mascara.T)]
    return min((horizontais,verticais),key=len)


def _retangulos_linhas(mascara: np.ndarray) -> list[tuple[int, int, int, int]]:
    ativos, saida = {}, []
    for y, linha in enumerate(mascara):
        bordas = np.diff(np.r_[False, linha, False].astype(int))
        spans = list(zip(np.flatnonzero(bordas == 1), np.flatnonzero(bordas == -1)))
        novos = {}
        for x0, x1 in spans:
            novos[(x0, x1)] = ativos.pop((x0, x1), (int(x0), y, int(x1), y))[:3] + (y + 1,)
        saida.extend(ativos.values())
        ativos = novos
    return saida + list(ativos.values())


def mascara_plano(modelo: bbmodelo.Modelo, cubo: bbmodelo.Cubo) -> tuple[np.ndarray, list[int]]:
    """Alfa das duas faces largas em coordenadas físicas crescentes; UV invertida é respeitada."""
    eixos = np.flatnonzero(cubo.tamanho > 1e-5).tolist()
    if len(eixos) != 2 or modelo.textura is None:
        raise ValueError(f"plano {cubo.nome}: precisa de duas dimensões e textura incorporada")
    tex = np.asarray(modelo.textura)
    sx, sy = tex.shape[1] / modelo.resolucao[0], tex.shape[0] / modelo.resolucao[1]
    faces, passos = [], np.ones(2, int)
    for nome, cantos in CANTOS_FACE.items():
        face = cubo.faces.get(nome, {})
        if face.get("texture") is None or not face.get("uv"):
            continue
        pts = cubo.de + np.array(cantos) * cubo.tamanho
        eu, ev = pts[1] - pts[0], pts[2] - pts[0]
        if np.linalg.norm(np.cross(eu, ev)) < 1e-8:
            continue
        if face.get("rotation", 0):
            raise ValueError(f"plano {cubo.nome}: rotação de UV ainda não suportada no perfil físico")
        u0, v0, u1, v1 = face["uv"]
        for i, eixo in enumerate(eixos):
            n = abs((u1-u0)*sx) if abs(eu[eixo]) > 1e-8 else abs((v1-v0)*sy)
            passos[i] = max(passos[i], int(np.ceil(n)))
        faces.append((pts[0], eu, ev, face["uv"]))
    if not faces or max(passos) > 512:
        raise ValueError(f"plano {cubo.nome}: faces/UV incompatíveis com perfil físico")
    x, y = np.meshgrid((np.arange(passos[0])+.5)/passos[0], (np.arange(passos[1])+.5)/passos[1])
    p = np.broadcast_to(cubo.de, (*x.shape, 3)).copy()
    p[..., eixos[0]] += x * cubo.tamanho[eixos[0]]
    p[..., eixos[1]] += y * cubo.tamanho[eixos[1]]
    mascara = np.zeros(x.shape, bool)
    for p0, eu, ev, (u0,v0,u1,v1) in faces:
        u = u0 + ((p-p0) @ eu) / (eu @ eu) * (u1-u0)
        v = v0 + ((p-p0) @ ev) / (ev @ ev) * (v1-v0)
        tx, ty = np.floor(u*sx).astype(int), np.floor(v*sy).astype(int)
        if tx.min() < 0 or ty.min() < 0 or tx.max() >= tex.shape[1] or ty.max() >= tex.shape[0]:
            raise ValueError(f"plano {cubo.nome}: UV fora da textura")
        mascara |= tex[ty,tx,3] >= 128
    return mascara, eixos


def perfil_composto(arquivo: Path, config: dict) -> dict:
    """Caixas orientadas por cubo e retângulos opacos dos planos, locais a cada Bone."""
    modelo = bbmodelo.ler(arquivo)
    matrizes = bbmodelo.matrizes_ossos(modelo)
    espessura = float(config.get("espessura_planos", .25))
    if not 0 < espessura <= 1:
        raise ValueError("espessura_planos deve estar entre 0 e 1 unidade Blockbench")
    pecas = []
    for cubo in modelo.cubos:
        if cubo.nome in config.get("excluir_cubos", []):
            continue
        if cubo.osso not in modelo.ossos:
            raise ValueError(f"cubo {cubo.nome}: falta osso físico")
        bone = np.eye(4); bone[:3,3] = modelo.ossos[cubo.osso].origem
        local = np.linalg.inv(matrizes[cubo.osso] @ bone) @ bbmodelo.matriz_cubo(modelo,cubo,matrizes)
        caixas = []
        dimensoes = np.count_nonzero(cubo.tamanho > 1e-5)
        if dimensoes == 3:
            caixas.append((cubo.de-cubo.inflate, cubo.ate+cubo.inflate))
        elif dimensoes == 2 and config.get("planos_alfa", True):
            mascara, eixos = mascara_plano(modelo,cubo)
            for x0,y0,x1,y1 in retangulos_mascara(mascara):
                a, b = cubo.de.copy(), cubo.ate.copy()
                for eixo, p0,p1,n in zip(eixos,(x0,y0),(x1,y1),(mascara.shape[1],mascara.shape[0])):
                    a[eixo] += p0/n*cubo.tamanho[eixo]
                    b[eixo] = cubo.de[eixo] + p1/n*cubo.tamanho[eixo]
                eixo = next(i for i in range(3) if i not in eixos)
                a[eixo] -= espessura/2; b[eixo] += espessura/2
                caixas.append((a,b))
        for a,b in caixas:
            centro = bbmodelo.aplicar(local, [(a+b)/2])[0]
            pecas.append({"nome":cubo.nome, "cubo_uuid":cubo.uuid, "osso":cubo.osso,
                          "tamanho":(b-a).round(6).tolist(),
                          "cf":np.r_[centro,local[:3,:3].flatten()].round(9).tolist(),
                          "plano":bool(dimensoes==2)})
    limite = int(config.get("max_partes", 192))
    if not 1 <= limite <= 192:
        raise ValueError("max_partes deve estar entre 1 e 192")
    if not pecas or len(pecas) > limite:
        raise ValueError(f"perfil composto: {len(pecas)} partes, limite {limite}; revisar simplificação explicitamente")
    return {"versao":2,"tipo":"composta_ossos", "pecas":pecas,
            "cubos":list(dict.fromkeys(p["cubo_uuid"] for p in pecas)),
            "fonte_sha256":hash_arquivo(arquivo),"espessura_planos":espessura}


def manifesto(raiz: Path, criatura: dict) -> dict:
    fonte = raiz / criatura["fonte"]
    glb = raiz / criatura["arquivo"]
    config = criatura.get("colisao", {})
    tipo = config.get("tipo", "corpo_estatico_ate_o_chao")
    if tipo == "composta_ossos":
        perfil = perfil_composto(fonte,config)
    elif tipo == "corpo_estatico_ate_o_chao":
        perfil = perfil_colisao(fonte, config.get("osso", "body"), config.get("cubos"))
    else:
        raise ValueError(f"tipo de colisão desconhecido: {tipo}")
    perfil["glb_sha256"] = hash_arquivo(glb)
    return {"versao": 1, "id": criatura["nome"], "fonte": criatura["fonte"],
            "config_sha256": hash_config(criatura),
            "fonte_sha256": hash_arquivo(fonte), "arquivo": criatura["arquivo"],
            "glb_sha256": hash_arquivo(glb), "escala_studio": criatura["escala_studio"],
            "colisao": perfil,
            "material_pbr": criatura.get("material_pbr", False),
            "espelhar_atlas": criatura.get("espelhar_atlas", False),
            "superamostrar": criatura.get("superamostrar")}


def receita_preparo(fonte: str, item: dict, preservar_escala: bool = False, modulo_colisao: str | None = None) -> str:
    texto = fonte.replace('local NOME = "Pavao_F2"', f'local NOME = {json.dumps(item["id"])}', 1)
    if not preservar_escala:
        texto = texto.replace('local ESCALA = nil', f'local ESCALA = {float(item["escala_studio"]):g}', 1)
    perfil = json.dumps(item["colisao"], ensure_ascii=False, separators=(",", ":"))
    if item["colisao"].get("versao") == 2 and not modulo_colisao:
        raise ValueError("perfil composto exige o módulo de colisão")
    if modulo_colisao:
        texto = texto.replace("-- @COLISAO_OSSOS@",modulo_colisao,1)
    return texto.replace('local PERFIL_JSON = nil', f'local PERFIL_JSON = [==[{perfil}]==]', 1)


def conferir_manifesto(raiz: Path, criatura: dict, item: dict) -> None:
    """Uma receita antiga não pode aplicar a colisão de outra revisão a uma malha nova."""
    if (item.get("versao") != 1 or item.get("id") != criatura["nome"]
            or item.get("fonte") != criatura["fonte"] or item.get("arquivo") != criatura["arquivo"]):
        raise ValueError("manifesto pertence a outra criatura ou formato")
    if item.get("config_sha256") != hash_config(criatura):
        raise ValueError("configuração mudou; exporte novamente antes do preparo")
    if (item["fonte_sha256"] != hash_arquivo(raiz / criatura["fonte"])
            or item["glb_sha256"] != hash_arquivo(raiz / criatura["arquivo"])):
        raise ValueError("fonte/exportação mudou; exporte novamente antes do preparo")
    if (item["colisao"].get("fonte_sha256") != item["fonte_sha256"]
            or item["colisao"].get("glb_sha256") != item["glb_sha256"]):
        raise ValueError("perfil físico não corresponde ao manifesto")
