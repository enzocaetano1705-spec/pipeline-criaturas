"""Gera as animações de locomoção da preguiça num .bbmodel novo, com prévias em GIF.

Uso: uv run python scripts/fera-animacao/gerar.py <base-com-garras.bbmodel> <pasta-saida>

Grava <pasta>/fera-sombras-e3-animacoes.bbmodel (cópia da base + clipes), animacoes.json (duração,
loop, velocidade de deslocamento para o jogo), previa-<clipe>.gif (lado e 3/4) e relatorio.json.
Se a base tiver pálpebras (palpebras.py), cada clipe ganha uma piscada (PISCADA_POR_CLIPE) e sai
previa-piscadas.gif (close da cabeça em volta da piscada de cada clipe). Também gera o combate:
combat_ready (guarda em tripé), combat_enter e combat_exit (combate.py).
As chaves são assadas (30 por segundo, sem Molang), como o Roblox precisa. Não anima `root`.
"""

from __future__ import annotations

import json
import math
import shutil
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
from clips import FPS, PISCADAS, Locomocao, piscar_em, repetir, transicao  # noqa: E402
from combate import Combate  # noqa: E402
from pose import Rig, chaves, rx  # noqa: E402

from criaturas import bbmodelo, motor, render  # noqa: E402


VOLTAS = {"walk": 2, "run": 5}  # passadas por loop (uma piscada por loop)
# quando cada clipe pisca (início, em s) e o jeito: devagar parada, rápido correndo, na antecipação
# das transições e virando a cabeça no idle
PISCADA_POR_CLIPE = {
    "idle": (2.6, "lenta"), "walk": (1.9, "normal"), "run": (1.62, "rapida"),
    "run_start": (0.06, "rapida"), "run_stop": (0.12, "normal"),
    "combat_ready": (0.9, "normal"), "combat_enter": (0.04, "rapida"), "combat_exit": (0.3, "normal"),
    # golpes: aperta os olhos no impacto (dá peso ao golpe)
    "attack_1": (0.18, "rapida"), "attack_2": (0.30, "rapida"),
    "skill1_throw": (0.28, "rapida"), "skill1_wait": (0.55, "normal"), "skill1_catch": (0.16, "rapida"),
    "skill1_strike_a": (0.14, "rapida"), "skill1_strike_b": (0.14, "rapida"), "skill2": (1.10, "normal"),
}


def r3(v):
    return [round(float(x), 3) for x in v]


def para_ops(nome, T, loop, quadros):
    ops = [{"op": "add_animation", "name": nome, "length": round(T, 4), "loop": "loop" if loop else "once",
            "snapping": FPS}]
    todas, anterior = [], None
    for t, pose in quadros:
        anterior = chaves(pose, anterior)
        todas.append((t, anterior))
    # trilha de posição inteira (com os zeros) para todo osso que translada em algum quadro do clipe:
    # sem a chave zero no começo/fim, o Blockbench segura o primeiro/último valor fora dela
    move = {o for _t, ch in todas for o, e in ch.items() if "posicao" in e and np.any(np.abs(e["posicao"]) > 1e-4)}
    trilhas = {}
    for t, ch in todas:
        for osso, e in ch.items():
            if "rotacao" in e:
                trilhas.setdefault((osso, "rotation"), []).append((round(t, 4), r3(e["rotacao"])))
            if osso in move:
                trilhas.setdefault((osso, "position"), []).append((round(t, 4), r3(e.get("posicao", np.zeros(3)))))
    for (osso, canal), chs in trilhas.items():
        for i, (t, v) in enumerate(chs):
            # chave no meio de um trecho parado (igual à anterior e à seguinte) não muda nada: fica de fora
            if 0 < i < len(chs) - 1 and v == chs[i - 1][1] and v == chs[i + 1][1]:
                continue
            ops.append({"op": "set_keyframe", "animation": nome, "bone": osso, "channel": canal,
                        "time": t, "value": v, "interpolation": "linear"})
    return ops


def gif(rig, quadros, destino, titulo):
    m = rig.m
    todos = [rig.mats(p) for _t, p in quadros[::2]]
    lo, hi = np.full(3, np.inf), np.full(3, -np.inf)
    for mats in todos:
        a, b = bbmodelo.limites(m, mats)
        lo, hi = np.minimum(lo, a), np.maximum(hi, b)
    lo[1] = min(lo[1], 0.0)
    imgs = []
    for (t, _p), mats in zip(quadros[::2], todos):
        lado = render.renderizar(m, (90, 4), escala=4.2, limites=(lo, hi), mats=mats, fundo=(236, 238, 242))[0]
        tq = render.renderizar(m, (35, 16), escala=4.2, limites=(lo, hi), mats=mats, fundo=(236, 238, 242))[0]
        f = Image.new("RGB", (lado.width + tq.width + 6, max(lado.height, tq.height)), (255, 255, 255))
        f.paste(lado, (0, 0))
        f.paste(tq, (lado.width + 6, 0))
        d = ImageDraw.Draw(f)
        y_chao = lado.height - 8 - int((0 - lo[1]) * 4.2)
        d.line([(0, y_chao), (lado.width, y_chao)], fill=(150, 150, 160))
        d.text((4, 2), f"{titulo}  t={t:.2f}s", fill=(40, 40, 50))
        imgs.append(f.convert("P", palette=Image.ADAPTIVE, colors=128))
    imgs[0].save(destino, save_all=True, append_images=imgs[1:], duration=int(2000 / FPS), loop=0, disposal=2)


def gif_piscadas(rig, itens, destino, antes=0.4, depois=0.6):
    """Close da cabeça (câmera seguindo) em volta da piscada de cada clipe: itens = [(nome, quadros, t0)]."""
    m = rig.m
    cab = [c for c in m.cubos if c.osso == "head"]
    paineis = []
    for nome, quadros, t0 in itens:
        # todos os painéis alinhados no início da piscada (clipe curto repete o primeiro/último quadro)
        i0 = next(i for i, (t, _p) in enumerate(quadros) if t >= t0 - 1e-6)
        idx = [min(max(i0 + k, 0), len(quadros) - 1) for k in range(-int(antes * FPS), int(depois * FPS))]
        sel = [quadros[i] for i in idx]
        ims = []
        for _t, pose in sel:
            mats = rig.mats(pose)
            lo, hi = np.full(3, np.inf), np.full(3, -np.inf)
            for c in cab:
                a, b = bbmodelo.caixa_mundo(m, c, mats)
                lo, hi = np.minimum(lo, a), np.maximum(hi, b)
            centro = (lo + hi) / 2
            im = render.renderizar(m, (60, 10), escala=13, limites=(centro - 9, centro + 9), mats=mats, fundo=(236, 238, 242))[0]
            ImageDraw.Draw(im).text((4, 2), nome, fill=(40, 40, 50))
            ims.append(im)
        paineis.append(ims)
    n = min(len(p) for p in paineis)
    cols = 3
    w, h = paineis[0][0].width + 4, paineis[0][0].height + 4
    quadros_gif = []
    for i in range(n):
        f = Image.new("RGB", (w * min(cols, len(paineis)), h * ((len(paineis) + cols - 1) // cols)), (255, 255, 255))
        for j, p in enumerate(paineis):
            f.paste(p[i], ((j % cols) * w, (j // cols) * h))
        quadros_gif.append(f.convert("P", palette=Image.ADAPTIVE, colors=160))
    quadros_gif[0].save(destino, save_all=True, append_images=quadros_gif[1:], duration=int(1000 / FPS), loop=0, disposal=2)


def tiras(rig, clipes, destino, n=8):
    """Uma linha por clipe com n quadros de lado (para revisar o movimento numa imagem)."""
    linhas = []
    for nome, T, _loop, quadros in clipes:
        idx = np.linspace(0, len(quadros) - 1, n).round().astype(int)
        mats_l = [rig.mats(quadros[i][1]) for i in idx]
        lo, hi = np.full(3, np.inf), np.full(3, -np.inf)
        for mats in mats_l:
            a, b = bbmodelo.limites(rig.m, mats)
            lo, hi = np.minimum(lo, a), np.maximum(hi, b)
        lo[1] = min(lo[1], 0.0)
        ims = []
        for i, mats in zip(idx, mats_l):
            im = render.renderizar(rig.m, (90, 4), escala=2.6, limites=(lo, hi), mats=mats, fundo=(236, 238, 242))[0]
            d = ImageDraw.Draw(im)
            y_chao = im.height - 8 - int((0 - lo[1]) * 2.6)
            d.line([(0, y_chao), (im.width, y_chao)], fill=(150, 150, 160))
            d.text((3, 2), f"{nome} {quadros[i][0]:.2f}", fill=(40, 40, 50))
            ims.append(im)
        linha = Image.new("RGB", (sum(i.width for i in ims), max(i.height for i in ims)), (255, 255, 255))
        x = 0
        for im in ims:
            linha.paste(im, (x, 0))
            x += im.width
        linhas.append(linha)
    W = max(l.width for l in linhas)
    folha = Image.new("RGB", (W, sum(l.height for l in linhas)), (255, 255, 255))
    y = 0
    for l in linhas:
        folha.paste(l, (0, y))
        y += l.height
    if folha.width > 1400:
        f = 1400 / folha.width
        folha = folha.resize((1400, int(folha.height * f)), Image.LANCZOS)
    folha.save(destino)


def main():
    base, pasta = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    if pasta.exists() and any(pasta.iterdir()):
        raise SystemExit(f"{pasta} já tem arquivos; use uma pasta nova")
    pasta.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    rig = Rig(bbmodelo.ler(base))
    loc = Locomocao(rig)

    T_idle, idle, _ = loc.idle()
    T_w1, walk1, info_w1 = loc.walk()
    T_r1, run1, info_r1 = loc.run()
    # uma piscada por loop num ritmo natural: o walk vira 2 passadas (3,2 s) e o run 5 (3,3 s);
    # a velocidade de deslocamento não muda (curso e tempo multiplicados juntos)
    T_walk, walk, info_w = VOLTAS["walk"] * T_w1, repetir(walk1, T_w1, VOLTAS["walk"]), {"curso": info_w1["curso"] * VOLTAS["walk"]}
    T_run, run, info_r = VOLTAS["run"] * T_r1, repetir(run1, T_r1, VOLTAS["run"]), {"curso": info_r1["curso"] * VOLTAS["run"]}

    def acento_partida(t, w, pose):
        pose["body"]["posicao"] = pose["body"]["posicao"] + np.array([0.0, -1.1 * math.sin(math.pi * w), 0.0])
        if t < 0.16:  # recua antes de mergulhar (antecipação)
            pose["body"]["matriz"] = pose["body"]["matriz"] @ rx(6 * math.sin(math.pi * t / 0.16))
        loc.garras(pose, dobra=min(1.0, t / 0.18) ** 0.7)  # recolhe as garras antes das mãos tocarem o chão
        loc.plantar_pernas(pose)
        loc.cauda_acima_do_chao(pose)

    def acento_parada(t, w, pose):
        # derrapa nos nós das mãos: tomba para a frente, passa do ponto para trás e assenta (gordura)
        tomba = -9 * math.sin(math.pi * min(1.0, t / 0.32)) + 4 * math.sin(math.pi * min(1.0, max(0.0, (t - 0.3) / 0.3)))
        pose["body"]["matriz"] = pose["body"]["matriz"] @ rx(tomba)
        pose["torso"]["matriz"] = pose["torso"]["matriz"] @ rx(0.6 * tomba * (t > 0.08))
        abre = min(1.0, max(0.0, (t - 0.32) / 0.22))
        loc.garras(pose, dobra=1.0 - abre * 1.15 if abre < 1 else 0.0)  # garras abrem com um estalo
        loc.plantar_pernas(pose)
        loc.cauda_acima_do_chao(pose)

    partida = transicao(idle[0][1], run[0][1], 0.5, acento_partida)
    parada = transicao(run[0][1], idle[0][1], 0.7, acento_parada)

    # combate: guarda em tripé, entrar e sair
    cmb = Combate(loc)
    T_g, guarda, _ = cmb.guarda()
    entrada = cmb.entrar(idle[0][1], guarda[0][1])
    saida = cmb.sair(guarda[0][1], idle[0][1])

    clipes = [("idle", T_idle, True, idle), ("walk", T_walk, True, walk), ("run", T_run, True, run),
              ("run_start", 0.5, False, partida), ("run_stop", 0.7, False, parada),
              ("combat_ready", T_g, True, guarda), ("combat_enter", entrada[-1][0], False, entrada),
              ("combat_exit", saida[-1][0], False, saida)]
    # golpes (ataque básico e habilidades), com a anatomia dos braços corrigida em cada pose-chave
    ajustes = {}
    infos = {}
    for nome, (T, quadros, loop, info) in cmb.golpes(relatorio=ajustes).items():
        clipes.append((nome, T, loop, quadros))
        infos[nome] = info
    tem_palpebras = all(o in rig.ossos for o in ("eyelid_left", "eyelid_right"))
    piscadas = {}
    if tem_palpebras:
        for nome, _T, _l, quadros in clipes:
            t_p, tipo = PISCADA_POR_CLIPE[nome]
            piscar_em(quadros, t_p, tipo)
            piscadas[nome] = {"t": t_p, "tipo": tipo, "duracao": round(len(PISCADAS[tipo]) / FPS, 3)}
    ops = []
    for nome, T, loop, quadros in clipes:
        ops += para_ops(nome, T, loop, quadros)
    arquivo = pasta / "fera-sombras-e3-animacoes.bbmodel"
    shutil.copyfile(base, arquivo)
    motor.editar(arquivo, ops)
    val = motor.validar_animacoes(arquivo)
    erros, avisos, linhas = motor.resumo_validacao(val) if isinstance(val, dict) else (0, 0, [str(val)[:200]])

    for nome, T, loop, quadros in clipes:
        gif(rig, quadros, pasta / f"previa-{nome}.gif", nome)
    tiras(rig, clipes, pasta / "tiras.png")
    if tem_palpebras:
        gif_piscadas(rig, [(n, q, piscadas[n]["t"]) for n, _T, _l, q in clipes], pasta / "previa-piscadas.gif")

    uni = 16.0  # unidades por bloco
    anim = {
        "clipes": {n: {"duracao": round(T, 3), "loop": lp, **({"piscada": piscadas[n]} if n in piscadas else {}),
                       **infos.get(n, {})}
                   for n, T, lp, _q in clipes},
        "deslocamento": {
            "walk": {"unidades_por_s": round(info_w["curso"] / T_walk, 2), "blocos_por_s": round(info_w["curso"] / T_walk / uni, 3)},
            "run": {"unidades_por_s": round(info_r["curso"] / T_run, 2), "blocos_por_s": round(info_r["curso"] / T_run / uni, 3)},
        },
        "nota": "Mover o modelo nessa velocidade (× escala do Studio) para os pés não patinarem. Cada clipe "
                "já pisca sozinho (pálpebras por posição, sem escala); walk tem 2 passadas e run 5 para a "
                "piscada cair a cada ~3 s.",
    }
    (pasta / "animacoes.json").write_text(json.dumps(anim, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rel = {"arquivo": arquivo.name, "chaves": sum(1 for o in ops if o["op"] == "set_keyframe"),
           "validacao_animacoes": {"erros": erros, "avisos": avisos, "linhas": linhas[:8]},
           "ajustes_anatomia": {n: [[t, {l: list(v) for l, v in r.items()}] for t, r in lst] for n, lst in ajustes.items()},
           "segundos": round(time.time() - t0, 1)}
    (pasta / "relatorio.json").write_text(json.dumps(rel, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{arquivo.name}: {len(clipes)} clipes, {rel['chaves']} chaves · validação: {erros} erros, {avisos} avisos")
    for l in linhas[:6]:
        print("  " + l)
    print(f"walk {anim['deslocamento']['walk']} · run {anim['deslocamento']['run']} · {rel['segundos']} s")


if __name__ == "__main__":
    main()
