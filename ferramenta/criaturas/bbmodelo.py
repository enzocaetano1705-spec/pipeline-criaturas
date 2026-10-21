"""Leitura de .bbmodel (formato 5.0) para o código do pipeline: ossos, cubos, locators, textura.

Só leitura. Para escrever, use operações do motor (criaturas.ops / criaturas.motor).
"""

import base64
import io
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image


@dataclass
class Osso:
    nome: str
    uuid: str
    pai: str | None
    origem: np.ndarray
    rotacao: np.ndarray


@dataclass
class Cubo:
    nome: str
    uuid: str
    osso: str | None
    de: np.ndarray
    ate: np.ndarray
    origem: np.ndarray
    rotacao: np.ndarray
    inflate: float
    faces: dict
    mirror_uv: bool = False

    @property
    def tamanho(self) -> np.ndarray:
        return self.ate - self.de


@dataclass
class Locator:
    nome: str
    osso: str | None
    posicao: np.ndarray


@dataclass
class Modelo:
    nome: str
    resolucao: tuple[int, int]
    ossos: dict[str, Osso]
    cubos: list[Cubo]
    locators: list[Locator]
    textura: Image.Image | None = None
    animacoes: list[dict] = field(default_factory=list)
    bruto: dict = field(default_factory=dict, repr=False)

    def filhos(self, osso: str | None) -> list[str]:
        return [o.nome for o in self.ossos.values() if o.pai == osso]

    def cubo(self, nome: str) -> Cubo:
        for c in self.cubos:
            if c.nome == nome:
                return c
        raise KeyError(nome)


def _vec(v, padrao=(0, 0, 0)) -> np.ndarray:
    return np.array(v if v is not None else padrao, dtype=float)


def _textura(bruto: dict) -> Image.Image | None:
    for t in bruto.get("textures", []):
        fonte = t.get("source", "")
        if fonte.startswith("data:image/"):
            dados = base64.b64decode(fonte.split(",", 1)[1])
            return Image.open(io.BytesIO(dados)).convert("RGBA")
    return None


def ler(caminho) -> Modelo:
    bruto = json.loads(Path(caminho).read_text(encoding="utf-8"))
    grupos = {g["uuid"]: g for g in bruto.get("groups", [])}
    elementos = {e["uuid"]: e for e in bruto.get("elements", [])}
    pai_de: dict[str, str | None] = {}

    def percorrer(nos, pai_uuid):
        for no in nos:
            if isinstance(no, str):
                pai_de[no] = pai_uuid
            else:
                pai_de[no["uuid"]] = pai_uuid
                percorrer(no.get("children", []), no["uuid"])

    percorrer(bruto.get("outliner", []), None)

    def nome_grupo(uuid):
        return grupos[uuid]["name"] if uuid in grupos else None

    ossos = {}
    for uuid, g in grupos.items():
        ossos[g["name"]] = Osso(g["name"], uuid, nome_grupo(pai_de.get(uuid)), _vec(g.get("origin")), _vec(g.get("rotation")))
    cubos, locators = [], []
    for uuid, e in elementos.items():
        osso = nome_grupo(pai_de.get(uuid))
        if e.get("type", "cube") == "cube":
            de, ate = _vec(e["from"]), _vec(e["to"])
            cubos.append(Cubo(e["name"], uuid, osso, de, ate, _vec(e.get("origin"), (de + ate) / 2),
                              _vec(e.get("rotation")), float(e.get("inflate", 0) or 0), e.get("faces", {}),
                              bool(e.get("mirror_uv", False))))
        elif e.get("type") == "locator":
            locators.append(Locator(e["name"], osso, _vec(e.get("position"))))
    res = bruto.get("resolution", {})
    return Modelo(bruto.get("name", Path(caminho).stem), (int(res.get("width", 64)), int(res.get("height", 64))),
                  ossos, cubos, locators, _textura(bruto), bruto.get("animations", []), bruto)


# ---------- transformações ----------

def matriz_rotacao(graus) -> np.ndarray:
    """Rotação de Blockbench: graus em X, Y, Z aplicados na ordem Z·Y·X (matriz Rz·Ry·Rx)."""
    x, y, z = np.radians(np.asarray(graus, float))
    cx, sx, cy, sy, cz, sz = np.cos(x), np.sin(x), np.cos(y), np.sin(y), np.cos(z), np.sin(z)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rz @ ry @ rx


def _em_torno(pivo, rot) -> np.ndarray:
    m = np.eye(4)
    r = matriz_rotacao(rot)
    m[:3, :3] = r
    m[:3, 3] = pivo - r @ pivo
    return m


def matrizes_ossos(modelo: Modelo, pose: dict | None = None) -> dict[str, np.ndarray]:
    """Matriz 4×4 de mundo de cada osso.

    `pose` = {osso: {'rotacao': [x,y,z], 'posicao': [x,y,z], 'escala': [x,y,z]}} somada ao repouso
    (escala em torno do pivô, antes da rotação), como numa chave de animação do Blockbench.
    """
    pose = pose or {}
    feitas: dict[str, np.ndarray] = {}

    def matriz(nome):
        if nome in feitas:
            return feitas[nome]
        o = modelo.ossos[nome]
        extra = pose.get(nome, {})
        rot = o.rotacao + np.asarray(extra.get("rotacao", (0, 0, 0)), float)
        local = _em_torno(o.origem, rot)
        if "escala" in extra:
            s = np.eye(4)
            s[:3, :3] = np.diag(np.asarray(extra["escala"], float))
            s[:3, 3] = o.origem - s[:3, :3] @ o.origem
            local = local @ s
        if "posicao" in extra:
            t = np.eye(4)
            t[:3, 3] = np.asarray(extra["posicao"], float)
            local = t @ local
        m = (matriz(o.pai) if o.pai else np.eye(4)) @ local
        feitas[nome] = m
        return m

    for nome in modelo.ossos:
        matriz(nome)
    return feitas


def matriz_cubo(modelo: Modelo, cubo: Cubo, mats: dict[str, np.ndarray]) -> np.ndarray:
    base = mats[cubo.osso] if cubo.osso else np.eye(4)
    if np.any(cubo.rotacao):
        base = base @ _em_torno(cubo.origem, cubo.rotacao)
    return base


def aplicar(m: np.ndarray, pontos: np.ndarray) -> np.ndarray:
    pontos = np.asarray(pontos, float)
    return pontos @ m[:3, :3].T + m[:3, 3]


def cantos(cubo: Cubo) -> np.ndarray:
    a, b = cubo.de - cubo.inflate, cubo.ate + cubo.inflate
    return np.array([[x, y, z] for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])])


def caixa_mundo(modelo: Modelo, cubo: Cubo, mats=None) -> tuple[np.ndarray, np.ndarray]:
    mats = mats if mats is not None else matrizes_ossos(modelo)
    p = aplicar(matriz_cubo(modelo, cubo, mats), cantos(cubo))
    return p.min(0), p.max(0)


def limites(modelo: Modelo, mats=None) -> tuple[np.ndarray, np.ndarray]:
    mats = mats if mats is not None else matrizes_ossos(modelo)
    caixas = [caixa_mundo(modelo, c, mats) for c in modelo.cubos]
    return np.min([c[0] for c in caixas], 0), np.max([c[1] for c in caixas], 0)
