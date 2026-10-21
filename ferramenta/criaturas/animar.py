"""`criaturas animar <pasta> --estagio eN`: animações procedurais assadas em chaves (sem Molang).

Ideia de referencia/prototipo-forja/forja/anim.py, com os nomes de docs/convencoes.md:
movimento é uma função do tempo por plano de corpo, amostrada em chaves catmullrom com a
primeira e a última iguais (loop sem emenda). O contato com o chão é corrigido quadro a quadro
pela cinemática do próprio modelo: no walk e no run o pé mais baixo fica no chão (o corpo sobe e
desce sozinho); nas outras, nada afunda abaixo do repouso.

Primeiro idle, walk e blink; depois run, cry, hurt, faint, sleep, fly (com asas) e swim (aquáticos).
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from criaturas import bbmodelo, motor, relatorio
from criaturas.caminhos import relativo
from criaturas.cubificar import contexto, sha256
from criaturas.etapas import etapa
from criaturas.relatorio import msg
from criaturas.validar import modelo_atual

TAU = 2 * np.pi
CICLO_WALK = {"inicial": 1.33, "meio": 1.5, "final": 2.0, "único": 1.5, "lendário": 2.0}
AMOSTRAS = 12
BASE = ("idle", "walk", "blink")
EXTRAS = ("run", "cry", "hurt", "faint", "sleep", "fly", "swim")


@dataclass
class Rig:
    """Ossos do modelo agrupados pelo papel, lidos dos nomes padrão."""
    body: str | None = None
    head: str | None = None
    jaw: str | None = None
    pernas: dict = field(default_factory=dict)  # nome -> lado (+1 direita, -1 esquerda) e frente/trás
    bracos: list = field(default_factory=list)
    asas: list = field(default_factory=list)
    orelhas: list = field(default_factory=list)
    olhos: list = field(default_factory=list)
    palpebras: list = field(default_factory=list)
    cauda: list = field(default_factory=list)
    pescoco: list = field(default_factory=list)
    nadadeiras: list = field(default_factory=list)
    tentaculos: list = field(default_factory=list)

    @classmethod
    def do_modelo(cls, modelo: bbmodelo.Modelo) -> "Rig":
        r = cls()
        nomes = set(modelo.ossos)
        r.body = "body" if "body" in nomes else None
        r.head = "head" if "head" in nomes else None
        r.jaw = "jaw" if "jaw" in nomes else None
        num = lambda s: int(re.search(r"(\d+)$", s).group(1))  # noqa: E731
        for n in sorted(nomes):
            pai = modelo.ossos[n].pai
            if re.match(r"^leg_", n) and not (pai or "").startswith(("leg_", "shin_")):
                r.pernas[n] = 1 if "right" in n else -1
            elif re.match(r"^arm_(left|right)$", n):
                r.bracos.append(n)
            elif re.match(r"^wing_(left|right)$", n):
                r.asas.append(n)
            elif n.startswith("ear_"):
                r.orelhas.append(n)
            elif re.match(r"^eye_(left|right)$", n):
                r.olhos.append(n)
            elif n.startswith("eyelid_"):
                r.palpebras.append(n)
            elif re.match(r"^tail_\d+$", n):
                r.cauda.append(n)
            elif re.match(r"^neck_\d+$", n):
                r.pescoco.append(n)
            elif n.startswith("fin_"):
                r.nadadeiras.append(n)
            elif n.startswith("tentacle_"):
                r.tentaculos.append(n)
        r.cauda.sort(key=num)
        r.pescoco.sort(key=num)
        return r


def _lado(nome: str) -> int:
    return 1 if "right" in nome else -1


class Clip:
    """Animação como funções do tempo; vira chaves em `assar`."""

    def __init__(self, nome: str, duracao: float, loop: str = "loop", amostras: int = AMOSTRAS, chao: str = "nao_afundar"):
        self.nome, self.duracao, self.loop, self.amostras, self.chao = nome, float(duracao), loop, amostras, chao
        self.trilhas: dict[str, dict[str, list]] = {}

    def add(self, osso, canal, f):
        if osso:
            self.trilhas.setdefault(osso, {}).setdefault(canal, []).append(f)
        return self

    def rot(self, osso, f):
        return self.add(osso, "rotation", f)

    def pos(self, osso, f):
        return self.add(osso, "position", f)

    def esc(self, osso, f):
        return self.add(osso, "scale", f)

    def valor(self, osso, canal, t):
        fs = self.trilhas.get(osso, {}).get(canal)
        if not fs:
            return None
        if canal == "scale":
            v = np.ones(3)
            for f in fs:
                v = v * np.asarray(f(t), float)
            return v
        return sum(np.asarray(f(t), float) for f in fs)

    def tempos(self):
        # no máximo 0,1 s entre chaves: o catmullrom entre chaves espaçadas pode afundar o que a correção não viu
        n = max(self.amostras, int(np.ceil(self.duracao / 0.1)))
        return np.linspace(0, self.duracao, n + 1)

    def pose(self, t) -> dict:
        p = {}
        for osso, canais in self.trilhas.items():
            for canal, chave in (("rotation", "rotacao"), ("position", "posicao"), ("scale", "escala")):
                v = self.valor(osso, canal, t)
                if v is not None:
                    p.setdefault(osso, {})[chave] = v
        return p


def _fase(t, periodo, fase=0.0):
    return TAU * (t / periodo + fase)


def balanco_corrente(c: Clip, corrente: list, periodo: float, amp: float, eixo: int = 1, atraso: float = 0.12, cresce: float = 1.15):
    for k, osso in enumerate(corrente):
        a = amp * cresce ** k

        def f(t, k=k, a=a):
            v = [0.0, 0.0, 0.0]
            v[eixo] = a * np.sin(_fase(t, periodo, -k * atraso))
            return v
        c.rot(osso, f)


# ---------- clipes por plano ----------

def idle(rig: Rig, plano: str, periodo: float = 2.4) -> Clip:
    c = Clip("idle", periodo)
    # respiração: o peito alarga (escala em x e z; em y afundaria as pernas filhas do corpo)
    c.esc(rig.body, lambda t: (1 + 0.025 * np.sin(_fase(t, periodo)), 1, 1 + 0.02 * np.sin(_fase(t, periodo))))
    c.rot(rig.head, lambda t: (2.5 * np.sin(_fase(t, periodo, 0.2)), 3 * np.sin(_fase(t, periodo, 0.1)), 0))
    balanco_corrente(c, rig.cauda, periodo, 6, eixo=1, atraso=0.08)
    balanco_corrente(c, rig.pescoco, periodo, 1.5, eixo=0, atraso=0.1, cresce=1.0)
    for b in rig.bracos:
        s = _lado(b)
        c.rot(b, lambda t, s=s: (2.5 * np.sin(_fase(t, periodo)), 0, -s * 2 * np.sin(_fase(t, periodo))))
    for a in rig.asas:
        s = _lado(a)
        c.rot(a, lambda t, s=s: (0, 0, -s * 6 * np.sin(_fase(t, periodo / 2))))
    for o in rig.orelhas:
        s = _lado(o)
        c.rot(o, lambda t, s=s: (0, 0, -s * 3 * np.sin(_fase(t, periodo, 0.3))))
    for n in rig.nadadeiras:
        c.rot(n, lambda t: (0, 8 * np.sin(_fase(t, periodo / 2)), 0))
    return c


def walk(rig: Rig, plano: str, periodo: float, nome: str = "walk", amp: float = 24.0) -> Clip:
    c = Clip(nome, periodo, chao="contato")
    pernas = rig.pernas
    if plano == "quadrúpede" or any("front" in p for p in pernas):
        # trote: diagonais juntas (frente-esquerda com trás-direita)
        for p in pernas:
            fase = 0.0 if (("front" in p) == ("left" in p)) else 0.5
            c.rot(p, lambda t, f=fase: (amp * np.sin(_fase(t, periodo, f)), 0, 0))
    elif plano == "inseto" or len(pernas) >= 6:
        # trípode: metade das patas de cada vez
        for i, p in enumerate(sorted(pernas)):
            fase = 0.0 if i % 2 == 0 else 0.5
            s = pernas[p]
            c.rot(p, lambda t, f=fase, s=s: (0, s * 0.7 * amp * np.sin(_fase(t, periodo, f)),
                                              s * 0.5 * amp * max(0.0, np.cos(_fase(t, periodo, f)))))
    elif pernas:
        for p in pernas:
            fase = 0.0 if "left" in p else 0.5
            c.rot(p, lambda t, f=fase: (amp * np.sin(_fase(t, periodo, f)), 0, 0))
        for b in rig.bracos:
            fase = 0.5 if "left" in b else 0.0
            c.rot(b, lambda t, f=fase: (0.7 * amp * np.sin(_fase(t, periodo, f)), 0, 0))
    else:
        # sem pernas (serpente, peixe, cabeça-corpo): ondula a corrente ou dá pulinhos
        if rig.cauda:
            balanco_corrente(c, rig.cauda, periodo, 14, eixo=1, atraso=0.15, cresce=1.1)
            c.rot(rig.body, lambda t: (0, 6 * np.sin(_fase(t, periodo, 0.15)), 0))
        else:
            c.chao = "nao_afundar"
            c.pos(rig.body, lambda t: (0, 2.5 * max(0.0, np.sin(_fase(t, periodo))), 0))
            c.esc(rig.body, lambda t: (1 + 0.06 * np.cos(_fase(t, periodo)) ** 2 * (np.sin(_fase(t, periodo)) < 0), 1, 1))
    c.rot(rig.head, lambda t: (2.5 * np.sin(2 * _fase(t, periodo) + 0.6), 0, 0))
    if pernas:
        balanco_corrente(c, rig.cauda, periodo, 8, eixo=1, atraso=0.12)
    for a in rig.asas:
        s = _lado(a)
        c.rot(a, lambda t, s=s: (0, 0, -s * 5 * np.sin(2 * _fase(t, periodo))))
    return c


def blink(rig: Rig) -> Clip | None:
    alvos = rig.palpebras or rig.olhos
    if not alvos:
        return None
    c = Clip("blink", 0.17, loop="once", amostras=4, chao="nenhum")
    for o in alvos:
        c.esc(o, lambda t: (1, 1 - 0.9 * np.sin(np.pi * min(max(t / 0.17, 0), 1)), 1))
    return c


def run(rig: Rig, plano: str) -> Clip:
    c = walk(rig, plano, 0.75, nome="run", amp=34.0)
    c.rot(rig.body, lambda t: (4 * np.sin(2 * _fase(t, 0.75)), 0, 0))
    return c


def cry(rig: Rig) -> Clip:
    c = Clip("cry", 1.5, loop="once")
    curva = lambda t: np.sin(np.pi * min(max(t / 1.5, 0), 1))  # noqa: E731
    c.rot(rig.head, lambda t: (-18 * curva(t), 0, 0))
    c.rot(rig.jaw, lambda t: (22 * curva(t), 0, 0))
    for o in rig.orelhas:
        c.rot(o, lambda t, s=_lado(o): (0, 0, -s * 10 * curva(t)))
    balanco_corrente(c, rig.cauda, 0.5, 10, eixo=1)
    return c


def hurt(rig: Rig) -> Clip:
    c = Clip("hurt", 0.5, loop="once")
    curva = lambda t: np.exp(-((t - 0.12) / 0.1) ** 2)  # noqa: E731
    c.rot(rig.body, lambda t: (-8 * curva(t), 0, 0))
    c.pos(rig.body, lambda t: (0, 0, 1.0 * curva(t)))
    c.rot(rig.head, lambda t: (-10 * curva(t), 0, 0))
    return c


def faint(rig: Rig) -> Clip:
    c = Clip("faint", 2.0, loop="hold")
    queda = lambda t: min(max((t - 0.2) / 1.2, 0), 1) ** 2  # noqa: E731
    c.rot(rig.body, lambda t: (0, 0, 80 * queda(t)))
    c.rot(rig.head, lambda t: (12 * queda(t), 0, 0))
    return c


def sleep(rig: Rig) -> Clip:
    c = Clip("sleep", 4.0)
    c.rot(rig.head, lambda t: (14 + 2 * np.sin(_fase(t, 4.0)), 0, 0))
    c.esc(rig.body, lambda t: (1 + 0.03 * np.sin(_fase(t, 4.0)), 1, 1 + 0.025 * np.sin(_fase(t, 4.0))))
    balanco_corrente(c, rig.cauda, 4.0, 3, eixo=1)
    for o in rig.orelhas:
        c.rot(o, lambda t, s=_lado(o): (0, 0, s * 12))
    return c


def fly(rig: Rig) -> Clip | None:
    if not rig.asas:
        return None
    periodo = 0.6
    c = Clip("fly", periodo, chao="nenhum")
    for a in rig.asas:
        s = _lado(a)
        c.rot(a, lambda t, s=s: (0, 0, -s * 35 * np.sin(_fase(t, periodo))))
    c.pos(rig.body, lambda t: (0, 3 + 0.6 * np.sin(_fase(t, periodo, 0.25)), 0))
    for p in rig.pernas:
        c.rot(p, lambda t: (25, 0, 0))
    balanco_corrente(c, rig.cauda, periodo, 5, eixo=0)
    return c


def swim(rig: Rig, plano: str) -> Clip | None:
    if not (rig.nadadeiras or plano in ("peixe", "serpentiforme")):
        return None
    periodo = 1.2
    c = Clip("swim", periodo, chao="nenhum")
    balanco_corrente(c, rig.cauda or rig.tentaculos, periodo, 16, eixo=1, atraso=0.15)
    c.rot(rig.body, lambda t: (0, 5 * np.sin(_fase(t, periodo, 0.1)), 0))
    for n in rig.nadadeiras:
        c.rot(n, lambda t, s=_lado(n): (0, 0, -s * 15 * np.sin(_fase(t, periodo / 2))))
    for p in rig.pernas:
        c.rot(p, lambda t, s=_lado(p): (20 * np.sin(_fase(t, periodo, 0.25 * s)), 0, 0))
    return c


# ---------- assar ----------

def _minimo_y(modelo, pose) -> float:
    mats = bbmodelo.matrizes_ossos(modelo, pose)
    return min(float(bbmodelo.aplicar(bbmodelo.matriz_cubo(modelo, c, mats), bbmodelo.cantos(c))[:, 1].min())
               for c in modelo.cubos if c.osso)


def assar(clip: Clip, modelo: bbmodelo.Modelo) -> dict[str, dict[str, list]]:
    """{osso: {canal: [(t, [x, y, z])]}}, com o chão corrigido e a última chave igual à primeira no loop."""
    tempos = clip.tempos()
    chaves: dict[str, dict[str, list]] = {}
    for osso, canais in clip.trilhas.items():
        if osso not in modelo.ossos:
            continue
        for canal in canais:
            chaves.setdefault(osso, {})[canal] = [(float(t), clip.valor(osso, canal, t)) for t in tempos]
    raiz = "body" if "body" in modelo.ossos else None
    if raiz and clip.chao != "nenhum":
        repouso = _minimo_y(modelo, None)
        correcoes = []
        for i, t in enumerate(tempos):
            pose = {o: {} for o in chaves}
            for o, cs in chaves.items():
                for canal, lista in cs.items():
                    pose[o][{"rotation": "rotacao", "position": "posicao", "scale": "escala"}[canal]] = lista[i][1]
            deficit = repouso - _minimo_y(modelo, pose)
            correcoes.append(deficit if clip.chao == "contato" else max(0.0, deficit))
        if any(abs(d) > 1e-3 for d in correcoes):
            pos = chaves.setdefault(raiz, {}).setdefault("position", [(float(t), np.zeros(3)) for t in tempos])
            chaves[raiz]["position"] = [(t, np.asarray(v, float) + [0, d, 0]) for (t, v), d in zip(pos, correcoes)]
    saida = {}
    for osso, cs in chaves.items():
        for canal, lista in cs.items():
            neutro = np.ones(3) if canal == "scale" else np.zeros(3)
            if all(np.allclose(v, neutro, atol=1e-3) for _, v in lista):
                continue
            if clip.loop == "loop":
                lista[-1] = (lista[-1][0], lista[0][1])
            saida.setdefault(osso, {})[canal] = [(round(t, 4), [round(float(x), 3) for x in v]) for t, v in lista]
    return saida


def ops_do_clipe(clip: Clip, chaves: dict, existentes: set[str]) -> list[dict]:
    lote = []
    if clip.nome in existentes:
        lote.append({"op": "remove_animation", "animation": clip.nome})
    lote.append({"op": "add_animation", "name": clip.nome, "length": round(clip.duracao, 4), "loop": clip.loop, "snapping": 24})
    for osso, cs in chaves.items():
        for canal, lista in cs.items():
            for t, v in lista:
                lote.append({"op": "set_keyframe", "animation": clip.nome, "bone": osso, "channel": canal,
                             "time": t, "value": v, "interpolation": "catmullrom"})
    return lote


def clipes(rig: Rig, plano: str, estagio: str | None, quais=BASE + EXTRAS) -> tuple[list[Clip], list]:
    avisos, saida = [], []
    ciclo = CICLO_WALK.get(estagio or "inicial", 1.33)
    fabrica = {"idle": lambda: idle(rig, plano), "walk": lambda: walk(rig, plano, ciclo), "blink": lambda: blink(rig),
               "run": lambda: run(rig, plano), "cry": lambda: cry(rig), "hurt": lambda: hurt(rig),
               "faint": lambda: faint(rig), "sleep": lambda: sleep(rig), "fly": lambda: fly(rig),
               "swim": lambda: swim(rig, plano)}
    for nome in quais:
        c = fabrica[nome]()
        if c is None:
            if nome == "blink":
                avisos.append(msg("sem_olhos", "blink: o modelo não tem ossos de olho ou pálpebra (olho pintado?)"))
            continue
        saida.append(c)
    return saida, avisos


def animar(arquivo: Path, plano: str, estagio: str | None, quais=BASE + EXTRAS) -> dict:
    modelo = bbmodelo.ler(arquivo)
    rig = Rig.do_modelo(modelo)
    lista, avisos = clipes(rig, plano, estagio, quais)
    existentes = {a.get("name") for a in modelo.animacoes}
    lote, resumo = [], {}
    for c in lista:
        chaves = assar(c, modelo)
        lote += ops_do_clipe(c, chaves, existentes)
        resumo[c.nome] = {"duracao": c.duracao, "loop": c.loop, "ossos": sorted(chaves)}
    motor.editar(arquivo, lote)
    return {"clipes": resumo, "avisos": avisos, "rig": rig}


def validar_animacoes(arquivo: Path) -> tuple[int, int, list[str]]:
    return motor.resumo_validacao(motor.validar_animacoes(arquivo))


@etapa("animar")
def cmd_animar(args) -> int:
    pasta = Path(args.pasta)
    nome = pasta.resolve().name
    ctx = contexto(nome, args.estagio)
    destino = ctx["destino"]
    arquivo = modelo_atual(destino, ctx["relatorio"])
    if arquivo is None:
        print("animar: nenhum .bbmodel (rode cubificar antes)")
        return 1
    hashes = ctx["relatorio"].get("hashes", {})
    if hashes.get(arquivo.name) and hashes[arquivo.name] != sha256(arquivo):
        print(f"animar: {arquivo.name} foi editado à mão; rode cubificar (ele grava uma versão nova) antes")
        return 1
    plano = (ctx["categoria"] or {}).get("plano", "quadrúpede")
    quais = BASE if args.so_base else BASE + EXTRAS
    try:
        r = animar(arquivo, plano, ctx["estagio"].get("estagio_tabela"), quais)
        erros, n_avisos, mensagens = validar_animacoes(arquivo)
    except motor.MotorErro as e:
        relatorio.registrar(destino, nome, args.estagio, "animar", False, erros=[msg("animar", str(e))])
        print(f"animar: {e}")
        return 1
    marcadores = {c: {"eventos": {}} for c in r["clipes"]}
    relatorio.gravar_json(destino / "animacoes.json", {"modelo": arquivo.name, "clipes": r["clipes"], "marcadores": marcadores})
    avisos = r["avisos"] + [msg("animacao", m) for m in mensagens if not m.startswith("[error]")]
    lista_erros = [msg("animacao", m) for m in mensagens if m.startswith("[error]")]
    relatorio.registrar(destino, nome, args.estagio, "animar", erros == 0, erros=lista_erros, avisos=avisos,
                        arquivos=[relativo(destino / "animacoes.json")],
                        resumo={"clipes": list(r["clipes"]), "erros": erros, "avisos": n_avisos},
                        hashes={arquivo.name: sha256(arquivo)})
    linhas = [f"animar {arquivo.name} ({plano}): {len(r['clipes'])} clipes — validação {erros} erros, {n_avisos} avisos"]
    for c, info in list(r["clipes"].items())[:10]:
        linhas.append(f"  {c:<7} {info['duracao']:.2f} s {info['loop']:<5} {len(info['ossos'])} ossos")
    linhas += relatorio.linhas_mensagens("Erros", lista_erros)
    linhas += relatorio.linhas_mensagens("Avisos", avisos, 4)
    relatorio.imprimir(linhas)
    return 0 if erros == 0 else 1
