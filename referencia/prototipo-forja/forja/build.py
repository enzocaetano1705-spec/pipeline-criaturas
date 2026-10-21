"""One call does everything: solve -> judge -> bake texture -> export -> render."""
import json
import os

from . import check, export_bb, render, texture


def build(model, out="out", sheet=True, gifs=True, rays=40, quiet=False):
    os.makedirs(out, exist_ok=True)
    model.finalize()
    pre = check.Report(model.name)
    check.fix_zfighting(model, pre)
    tex = texture.bake(model, rays=rays)
    rep = check.run(model, tex)
    rep.lines[2:2] = pre.lines
    base = os.path.join(out, model.name)
    export_bb.write(model, tex, base + ".bbmodel")
    from PIL import Image
    Image.fromarray(tex.image, "RGBA").save(base + "_textura.png")
    files = [base + ".bbmodel", base + "_textura.png"]
    if sheet:
        render.contact_sheet(model, tex, title=f"{model.name}  texel={model.texel}").save(base + "_previa.png")
        files.append(base + "_previa.png")
    if gifs:
        for an in model.anims:
            files.append(render.anim_gif(model, tex, an, f"{base}_{an.name}.gif"))
    if model.sockets:
        socks = {s.name: {"bone": s.box.bone.name, "pos": [round(float(v), 3) for v in s.point]}
                 for s in model.sockets}
        with open(base + "_sockets.json", "w") as fh:
            json.dump(socks, fh, indent=1)
        files.append(base + "_sockets.json")
    with open(base + "_relatorio.txt", "w") as fh:
        fh.write(rep.text + "\n")
    if not quiet:
        print(rep.text)
        print("      arquivos: " + ", ".join(os.path.basename(f) for f in files))
    model._tex = tex
    model._report = rep
    return rep


def build_series(models, out="out", **kw):
    """Build every stage, then compare them side by side at the same scale."""
    reps = [build(m, out, **kw) for m in models]
    txt = check.check_series(models)
    print(txt)
    path = os.path.join(out, f"{models[0].name}_serie.png")
    render.series_sheet([(m, m._tex) for m in models],
                        labels=[f"{i + 1}. {m.name}" for i, m in enumerate(models)]).save(path)
    print(f"      arquivos: {os.path.basename(path)}")
    return reps, txt
