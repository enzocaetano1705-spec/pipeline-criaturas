"""Gera as animações de locomoção da preguiça num .bbmodel novo, com prévias em GIF.

Uso: uv run python scripts/fera-animacao/gerar.py <base-com-garras.bbmodel> <pasta-saida>

Grava <pasta>/fera-sombras-e3-animacoes.bbmodel (cópia da base + clipes), animacoes.json (duração,
loop, velocidade de deslocamento para o jogo), previa-<clipe>.gif (lado e 3/4) e relatorio.json.
Se a base tiver pálpebras (palpebras.py), grava também o clipe `blink` (camada que só mexe nelas) e
previa-blink.gif (close da cabeça em idle, walk e run com a piscada por cima).
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
from clips import FPS, Locomocao, transicao  # noqa: E402
from pose import Rig, chaves, rx  # noqa: E402

from criaturas import bbmodelo, motor, render  # noqa: E402


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
    for t, ch in todas:
        for osso, e in ch.items():
            if "rotacao" in e:
                ops.append({"op": "set_keyframe", "animation": nome, "bone": osso, "channel": "rotation",
                            "time": round(t, 4), "value": r3(e["rotacao"]), "interpolation": "linear"})
            if osso in move:
                ops.append({"op": "set_keyframe", "animation": nome, "bone": osso, "channel": "position",
                            "time": round(t, 4), "value": r3(e.get("posicao", np.zeros(3))), "interpolation": "linear"})
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


def gif_piscada(rig, locomocao, blink, destino, janela=1.4):
    """Close da cabeça (câmera seguindo) em idle, walk e run, com a piscada tocando por cima no meio."""
    m = rig.m
    cab = [c for c in m.cubos if c.osso == "head"]
    paineis = []
    for nome, quadros in locomocao:
        ciclo = quadros[:-1]  # o último quadro do loop repete o primeiro
        n = int(round(janela * FPS))
        sel = [ciclo[i % len(ciclo)] for i in range(n)]
        i0 = n // 2 - len(blink) // 2
        ims = []
        for i, (_t, pose) in enumerate(sel):
            p = dict(pose)
            if 0 <= i - i0 < len(blink):
                p.update(blink[i - i0][1])
            mats = rig.mats(p)
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
    quadros_gif = []
    for i in range(n):
        f = Image.new("RGB", (sum(p[i].width + 4 for p in paineis), max(p[i].height for p in paineis)), (255, 255, 255))
        x = 0
        for p in paineis:
            f.paste(p[i], (x, 0))
            x += p[i].width + 4
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
    T_walk, walk, info_w = loc.walk()
    T_run, run, info_r = loc.run()
    inicio_run, fim_run = run[0][1], idle[0][1]

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

    clipes = [("idle", T_idle, True, idle), ("walk", T_walk, True, walk), ("run", T_run, True, run),
              ("run_start", 0.5, False, partida), ("run_stop", 0.7, False, parada)]
    tem_palpebras = all(o in rig.ossos for o in ("eyelid_left", "eyelid_right"))
    if tem_palpebras:
        T_blink, blink, _ = loc.piscar()
        clipes.append(("blink", T_blink, False, blink))
    ops = []
    for nome, T, loop, quadros in clipes:
        ops += para_ops(nome, T, loop, quadros)
    arquivo = pasta / "fera-sombras-e3-animacoes.bbmodel"
    shutil.copyfile(base, arquivo)
    motor.editar(arquivo, ops)
    val = motor.validar_animacoes(arquivo)
    erros, avisos, linhas = motor.resumo_validacao(val) if isinstance(val, dict) else (0, 0, [str(val)[:200]])

    corpo = [c for c in clipes if c[0] != "blink"]
    for nome, T, loop, quadros in corpo:
        gif(rig, quadros, pasta / f"previa-{nome}.gif", nome)
    tiras(rig, corpo, pasta / "tiras.png")
    if tem_palpebras:
        gif_piscada(rig, [(n, q) for n, _T, _l, q in corpo if n in ("idle", "walk", "run")], blink, pasta / "previa-blink.gif")

    uni = 16.0  # unidades por bloco
    anim = {
        "clipes": {n: {"duracao": round(T, 3), "loop": lp} for n, T, lp, _q in clipes},
        "deslocamento": {
            "walk": {"unidades_por_s": round(info_w["curso"] / T_walk, 2), "blocos_por_s": round(info_w["curso"] / T_walk / uni, 3)},
            "run": {"unidades_por_s": round(info_r["curso"] / T_run, 2), "blocos_por_s": round(info_r["curso"] / T_run / uni, 3)},
        },
        "nota": "Mover o modelo nessa velocidade (× escala do Studio) para os pés não patinarem.",
    }
    if tem_palpebras:
        anim["clipes"]["blink"].update({
            "camada": True, "ossos": ["eyelid_left", "eyelid_left_lower", "eyelid_right", "eyelid_right_lower"],
            "intervalo_s": [2.5, 6.0],
            "nota": "Tocar por cima de idle, walk e run (e do que vier depois) num intervalo aleatório: só mexe nas "
                    "pálpebras, por posição. Se o exportador gravar poses dos outros ossos, zerar o peso delas "
                    "(como o papel 'upper' do AnimationDriver).",
        })
    (pasta / "animacoes.json").write_text(json.dumps(anim, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rel = {"arquivo": arquivo.name, "chaves": sum(1 for o in ops if o["op"] == "set_keyframe"),
           "validacao_animacoes": {"erros": erros, "avisos": avisos, "linhas": linhas[:8]},
           "segundos": round(time.time() - t0, 1)}
    (pasta / "relatorio.json").write_text(json.dumps(rel, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{arquivo.name}: {len(clipes)} clipes, {rel['chaves']} chaves · validação: {erros} erros, {avisos} avisos")
    for l in linhas[:6]:
        print("  " + l)
    print(f"walk {anim['deslocamento']['walk']} · run {anim['deslocamento']['run']} · {rel['segundos']} s")


if __name__ == "__main__":
    main()
