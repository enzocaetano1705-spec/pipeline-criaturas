"""Catálogo local, perfil físico e receitas do preparo Roblox. Não altera as fontes artísticas."""
import hashlib
import json
from pathlib import Path

import numpy as np

from criaturas import bbmodelo


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


def manifesto(raiz: Path, criatura: dict) -> dict:
    fonte = raiz / criatura["fonte"]
    glb = raiz / criatura["arquivo"]
    config = criatura.get("colisao", {})
    perfil = perfil_colisao(fonte, config.get("osso", "body"), config.get("cubos"))
    perfil["glb_sha256"] = hash_arquivo(glb)
    return {"versao": 1, "id": criatura["nome"], "fonte": criatura["fonte"],
            "config_sha256": hash_config(criatura),
            "fonte_sha256": hash_arquivo(fonte), "arquivo": criatura["arquivo"],
            "glb_sha256": hash_arquivo(glb), "escala_studio": criatura["escala_studio"],
            "colisao": perfil,
            "material_pbr": criatura.get("material_pbr", False),
            "espelhar_atlas": criatura.get("espelhar_atlas", False),
            "superamostrar": criatura.get("superamostrar")}


def receita_preparo(fonte: str, item: dict, preservar_escala: bool = False) -> str:
    texto = fonte.replace('local NOME = "Pavao_F2"', f'local NOME = {json.dumps(item["id"])}', 1)
    if not preservar_escala:
        texto = texto.replace('local ESCALA = nil', f'local ESCALA = {float(item["escala_studio"]):g}', 1)
    perfil = json.dumps(item["colisao"], ensure_ascii=False, separators=(",", ":"))
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
