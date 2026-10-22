"""Pavão F2, rodada 3 (22/10): penas das pernas, pivôs, textura corrigida e walk de avestruz.

O walk é próprio, passo a passo de um avestruz andando:
- cada perna: apoio em 60% do ciclo (o pé fica plantado enquanto o quadril leva a perna de +A para −A) e balanço em
  40% (o joelho e o tornozelo dobram, o pé sobe, passa por baixo do corpo e estica antes de tocar o chão);
- corpo: rola para o lado da perna de apoio, gira um pouco na direção do passo, arfa 2× por ciclo; a altura vem da
  correção de contato (o pé mais baixo encosta no chão);
- pescoço e cabeça: "head-bob" de ave, o pescoço vai e volta 2× por ciclo e a cabeça compensa para ficar estável;
- cauda e asas: balanço contrário ao do corpo, com atraso; braços acompanham a perna oposta.
O idle aprovado não é tocado.
"""

import importlib.util
import math
import shutil
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image

from criaturas import animar, bbmodelo, motor, ops

AQUI = Path(__file__).resolve().parent
FILE = AQUI / "criatura-pavao-e2.bbmodel"
_sp = importlib.util.spec_from_file_location("fin", AQUI / "finalizar-f2.py")
fin = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(fin)

T = 1.2  # ciclo do walk (s)
APOIO = 0.6  # fração do ciclo com o pé no chão


# ------------------------------------------------------------------ penas das pernas
def penas_das_pernas(modelo):
    """Penas penduradas mais perto da coxa que do ombro vão para o osso da perna (andam com ela)."""
    W = fin.mundo(modelo)
    cub = {c.nome: c for c in modelo.cubos}
    cw = {n: bbmodelo.aplicar(W[n], fin.centro(cub[n])[None])[0] for n in cub}
    lote, n = [], {"left": 0, "right": 0}
    for c in modelo.cubos:
        if not c.nome.startswith("wing_") or "feather" not in c.nome:
            continue
        s = "left" if "left" in c.nome else "right"
        (pa, pb), _ = fin.pontas(c, W[c.uuid])
        base = min((pa, pb), key=lambda p: min(np.linalg.norm(p - cw[f"upper_arm_{s}"]), np.linalg.norm(p - cw[f"thigh_{s}"])))
        if np.linalg.norm(base - cw[f"thigh_{s}"]) < np.linalg.norm(base - cw[f"upper_arm_{s}"]):
            n[s] += 1
            lote.append({"op": "update_node", "target": c.uuid, "parent": f"leg_{s}", "name": f"leg_{s}_feather_{n[s]}"})
    return lote, n


# ------------------------------------------------------------------ walk
def _sinal(modelo, osso, eixo, alvo_nome, mede):
    """Sinal de rotação (±1) em `osso` que aumenta `mede(ponto do alvo)` (ex.: sobe o pé ou leva para a frente)."""
    c = next(c for c in modelo.cubos if c.nome == alvo_nome)
    ctr = fin.centro(c)[None]
    vals = []
    for s in (1, -1):
        rot = [0, 0, 0]
        rot[eixo] = 15 * s
        mats = bbmodelo.matrizes_ossos(modelo, {osso: {"rotacao": rot}})
        vals.append(mede(bbmodelo.aplicar(bbmodelo.matriz_cubo(modelo, c, mats), ctr)[0]))
    return 1 if vals[0] > vals[1] else -1


def suave(x):
    return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, x)))


PASSADA = 8.0  # comprimento do passo do dedo (unidades)
ALTURA_PE = 3.0  # quanto o pé sobe no balanço
AMOSTRAS_IK = 48


def _corpo(t):
    """Movimento do corpo (rotação e posição) no instante t: rola para a perna de apoio, gira com o passo, arfa e
    sobe e desce 2× por ciclo (mais alto no meio do apoio, como um pêndulo invertido)."""
    w = 2 * math.pi / T
    rot = (1.5 * math.sin(2 * w * t), 4 * math.sin(w * t), 2.5 * math.sin(w * t))
    pos = (0, 0.45 * math.cos(2 * w * t), 0)
    return rot, pos


def _alvo(p0, ph):
    """Onde o dedo deve estar (mundo) e se está no chão, na fase ph da perna."""
    if ph < APOIO:  # apoio: plantado, desliza para trás em velocidade constante (a criatura anda para −z)
        u = ph / APOIO
        return np.array([p0[0], p0[1], p0[2] - PASSADA / 2 + PASSADA * u]), True, 0.0
    u = (ph - APOIO) / (1 - APOIO)
    z = p0[2] + PASSADA / 2 - PASSADA * suave(u)
    return np.array([p0[0], p0[1] + ALTURA_PE * math.sin(math.pi * u), z]), False, u


def _nelder_mead(f, x0, passo=6.0, iters=160):
    n = len(x0)
    simplex = [np.array(x0, float)] + [np.array(x0, float) + passo * np.eye(n)[k] for k in range(n)]
    vals = [f(x) for x in simplex]
    for _ in range(iters):
        ordem = np.argsort(vals)
        simplex, vals = [simplex[k] for k in ordem], [vals[k] for k in ordem]
        centro = np.mean(simplex[:-1], axis=0)
        xr = centro + (centro - simplex[-1])
        fr = f(xr)
        if fr < vals[0]:
            xe = centro + 2 * (centro - simplex[-1])
            fe = f(xe)
            simplex[-1], vals[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < vals[-2]:
            simplex[-1], vals[-1] = xr, fr
        else:
            xc = centro + 0.5 * (simplex[-1] - centro)
            fc = f(xc)
            if fc < vals[-1]:
                simplex[-1], vals[-1] = xc, fc
            else:
                simplex = [simplex[0] + 0.5 * (x - simplex[0]) for x in simplex]
                vals = [f(x) for x in simplex]
    k = int(np.argmin(vals))
    return simplex[k], vals[k]


def resolver_pernas(modelo):
    """Ângulos (quadril, joelho, tornozelo em X) por amostra para cada perna, por cinemática inversa numérica."""
    mats0 = bbmodelo.matrizes_ossos(modelo)
    dedos = {s: next(c for c in modelo.cubos if c.nome == f"toe_{s}_1") for s in ("left", "right")}
    p0 = {s: bbmodelo.aplicar(bbmodelo.matriz_cubo(modelo, d, mats0), fin.centro(d)[None])[0] for s, d in dedos.items()}
    eixo_dedo = {s: int(np.argmax(d.ate - d.de)) for s, d in dedos.items()}
    ts = np.linspace(0, T, AMOSTRAS_IK, endpoint=False)
    saida = {s: [] for s in dedos}
    for s, fase in (("left", 0.0), ("right", 0.5)):
        x = np.zeros(3)
        d = dedos[s]
        for t in ts:
            ph = (t / T + fase) % 1.0
            alvo, no_chao, u = _alvo(p0[s], ph)
            rot_c, pos_c = _corpo(t)

            def custo(v):
                pose = {"body": {"rotacao": rot_c, "posicao": pos_c},
                        f"leg_{s}": {"rotacao": (v[0], 0, 0)}, f"shin_{s}": {"rotacao": (v[1], 0, 0)},
                        f"foot_{s}": {"rotacao": (v[2], 0, 0)}}
                mats = bbmodelo.matrizes_ossos(modelo, pose)
                m = bbmodelo.matriz_cubo(modelo, d, mats)
                p = bbmodelo.aplicar(m, fin.centro(d)[None])[0]
                eixo = m[:3, :3][:, eixo_dedo[s]]
                inclinacao = math.degrees(math.asin(max(-1, min(1, eixo[1] / np.linalg.norm(eixo)))))
                # no chão: dedo plano; no ar: dedos apontando para baixo (fechados), mais no meio do balanço
                alvo_incl = 0.0 if no_chao else -35 * math.sin(math.pi * u)
                err = np.sum((p - alvo)[1:] ** 2) * 4
                return err + 0.004 * (inclinacao - alvo_incl) ** 2 + 0.0004 * float(np.sum(v ** 2))

            x, _ = _nelder_mead(custo, x, passo=6.0 if t == 0 else 2.0)
            saida[s].append(x.copy())
    return ts, {s: np.array(v) for s, v in saida.items()}


def walk(modelo) -> animar.Clip:
    c = animar.Clip("walk", T, amostras=24, chao="nenhum")
    ts, angulos = resolver_pernas(modelo)

    def tabela(vals):
        tt = np.concatenate([ts, [T]])
        vv = np.concatenate([vals, vals[:1]])
        return lambda t: float(np.interp(t % T, tt, vv))

    for s in ("left", "right"):
        q, j, k = (tabela(angulos[s][:, i]) for i in range(3))
        c.rot(f"leg_{s}", lambda t, q=q: (q(t), 0, 0))
        c.rot(f"shin_{s}", lambda t, j=j: (j(t), 0, 0))
        c.rot(f"foot_{s}", lambda t, k=k: (k(t), 0, 0))
        braco = 1 if s == "left" else -1
        c.rot(f"arm_{s}", lambda t, b=braco: (6 * math.sin(2 * math.pi * t / T) * b, 0, 0))
        c.rot(f"wing_{s}", lambda t, b=braco: (0, 0, 3 * b * math.sin(4 * math.pi * t / T + 0.6)))
    w = 2 * math.pi / T
    c.rot("body", lambda t: _corpo(t)[0])
    c.pos("body", lambda t: _corpo(t)[1])
    # head-bob: pescoço vai e volta, cabeça compensa (fica quase parada no ar)
    c.rot("neck_1", lambda t: (7 * math.sin(2 * w * t + 0.4), -2 * math.sin(w * t), 0))
    c.rot("head", lambda t: (-8 * math.sin(2 * w * t + 0.4) - 1.5 * math.sin(2 * w * t), -2 * math.sin(w * t), 0))
    c.rot("tail_1", lambda t: (2 * math.sin(2 * w * t + 1.0), -6 * math.sin(w * t - 0.9), -3 * math.sin(w * t - 0.9)))
    penas = [n for n in modelo.ossos if n.startswith("feather_")]
    animar.balanco_penas(c, penas, T / 2, 2.5)
    return c


def medir_walk(modelo, clip, n=48):
    """Deslize do pé de apoio (quanto o dedo plantado anda em z) e quanto o corpo sobe e desce."""
    chaves = animar.assar(clip, modelo)
    ts = np.linspace(0, T, n, endpoint=False)

    def em(osso, canal, t):
        lista = chaves.get(osso, {}).get(canal)
        if not lista:
            return None
        tt = [a for a, _ in lista]
        return np.array([np.interp(t, tt, [v[i] for _, v in lista]) for i in range(3)])

    dedos = {s: next(c for c in modelo.cubos if c.nome == f"toe_{s}_1") for s in ("left", "right")}
    zs, ys, alturas = {"left": [], "right": []}, {"left": [], "right": []}, []
    for t in ts:
        pose = {}
        for o in chaves:
            p = {}
            for canal, k in (("rotation", "rotacao"), ("position", "posicao")):
                v = em(o, canal, t)
                if v is not None:
                    p[k] = v
            pose[o] = p
        mats = bbmodelo.matrizes_ossos(modelo, pose)
        for s, d in dedos.items():
            p = bbmodelo.aplicar(bbmodelo.matriz_cubo(modelo, d, mats), fin.centro(d)[None])[0]
            zs[s].append(p[2])
            ys[s].append(p[1])
        alturas.append((em("body", "position", t) if em("body", "position", t) is not None else np.zeros(3))[1])
    desl = []
    for s, f in (("left", 0.0), ("right", 0.5)):
        fase = ((ts / T) + f) % 1.0
        apoio = fase < APOIO * 0.9
        z = np.array(zs[s])[apoio]
        desl.append(float(np.ptp(z)))
    passo = [float(np.ptp(zs[s])) for s in zs]
    subida = [float(np.max(ys[s]) - np.min(ys[s])) for s in ys]
    return {"passo_z": [round(x, 2) for x in passo], "z_no_apoio": [round(x, 2) for x in desl],
            "pe_sobe": [round(x, 2) for x in subida], "corpo_sobe_desce": round(float(np.ptp(alturas)), 2)}


# ------------------------------------------------------------------ execução
def main():
    hist = AQUI / "historico"
    shutil.copy2(FILE, hist / f"{datetime.now():%Y%m%d-%H%M}-antes-da-rodada3.bbmodel")
    modelo = bbmodelo.ler(FILE)
    lote, n = penas_das_pernas(modelo)
    if lote:
        motor.editar(FILE, lote)
        print(f"penas das pernas: {n}")
        modelo = bbmodelo.ler(FILE)
    antes = fin.mundo(modelo)
    cantos = {c.uuid: bbmodelo.aplicar(antes[c.uuid], np.array([c.de, c.ate])) for c in modelo.cubos}
    lote, _ = fin.achatar_e_pivotar(modelo)
    motor.editar(FILE, lote)
    modelo = bbmodelo.ler(FILE)
    depois = fin.mundo(modelo)
    erro = max(float(np.abs(bbmodelo.aplicar(depois[c.uuid], np.array([c.de, c.ate])) - cantos[c.uuid]).max()) for c in modelo.cubos)
    print(f"pivôs nas juntas; desvio de geometria = {erro:.5f}")
    if erro > 0.01:
        raise SystemExit("geometria mudou; abortado")
    # textura: UV refeito e pintura (mesma linguagem; corrige tarsos, base do leque e penas das pernas)
    lista = [{"nome": c.uuid, "from": c.de.tolist(), "to": c.ate.tolist()} for c in modelo.cubos]
    offsets, (res, _) = ops.distribuir_uv(lista, margem=0, larguras=(64, 128, 256))
    motor.editar(FILE, [{"op": "set_model_properties", "resolution": {"width": res, "height": res}}] +
                 [{"op": "update_node", "target": c.uuid, "uv_offset": offsets[c.uuid]} for c in modelo.cubos])
    modelo = bbmodelo.ler(FILE)
    tex = fin.pintar(modelo, res)
    Image.fromarray(tex).save(AQUI / "textura.png")
    t0 = modelo.bruto["textures"][0]["uuid"]
    motor.editar(FILE, [{"op": "update_texture", "target": t0, "source": fin.texturizar._data_url(tex), "width": res,
                         "height": res, "material": None},
                        {"op": "assign_texture", "targets": [c.uuid for c in modelo.cubos], "texture": t0}])
    fin.acertar_uv_da_textura(FILE, res)
    modelo = bbmodelo.ler(FILE)
    # walk
    clip = walk(modelo)
    print("walk:", medir_walk(modelo, clip))
    existentes = {a.get("name") for a in modelo.animacoes}
    motor.editar(FILE, animar.ops_do_clipe(clip, animar.assar(clip, modelo), existentes))
    geo = motor.resumo_validacao(motor.validar(FILE.resolve()))
    aerr, awarn, amsg = animar.validar_animacoes(FILE)
    print(f"geometria {geo[0]} erros/{geo[1]} avisos; animações {aerr} erros/{awarn} avisos")
    for m in amsg[:5]:
        print("  ", m)


if __name__ == "__main__":
    if "--so-walk" in sys.argv:  # só troca o walk (textura e pivôs já feitos)
        m = bbmodelo.ler(FILE)
        clip = walk(m)
        motor.editar(FILE, animar.ops_do_clipe(clip, animar.assar(clip, m), {a.get("name") for a in m.animacoes}))
        print("walk gravado;", "animações:", animar.validar_animacoes(FILE)[:2])
    elif "--so-medir" in sys.argv:
        m = bbmodelo.ler(FILE)
        print(medir_walk(m, walk(m)))
    else:
        main()
