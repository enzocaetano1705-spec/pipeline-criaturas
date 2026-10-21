"""Blockbench .bbmodel writer (Generic Model / 'free' format).

Written as format 4.10 with groups inside the outliner, which Blockbench 4.x reads natively
and Blockbench 5.x upgrades on load. Animation values are stored in the 4.x sign convention
(x of position/rotation and y of rotation negated); 5.x converts them back on open."""
import base64
import io
import json
import uuid
import numpy as np
from PIL import Image


def _r(v):
    return [round(float(x), 4) for x in v]


def _num(v):
    s = f"{float(v):.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def to_bbmodel(model, tex):
    png = io.BytesIO()
    Image.fromarray(tex.image, "RGBA").save(png, "PNG")
    src = "data:image/png;base64," + base64.b64encode(png.getvalue()).decode()
    size = tex.size

    elements = []
    for i, b in enumerate(model.boxes):
        faces = {}
        for key in ("north", "east", "south", "west", "up", "down"):
            rect = tex.rects.get((b.uuid, key))
            if rect is None:
                faces[key] = {"uv": [0, 0, 0, 0], "texture": None}
            else:
                x, y, w, h = rect
                faces[key] = {"uv": [x, y, x + w, y + h], "texture": 0}
        el = {"name": b.name, "box_uv": False, "rescale": False, "locked": False,
              "light_emission": 0, "render_order": "default", "allow_mirror_modeling": True,
              "from": _r(b.frm), "to": _r(b.to), "autouv": 0, "color": i % 8,
              "origin": _r(b.origin if b.origin is not None else b.bone.pivot),
              "faces": faces, "type": "cube", "uuid": b.uuid}
        if np.any(b.rot):
            el["rotation"] = _r(b.rot)
        if b.inflate:
            el["inflate"] = round(float(b.inflate), 4)
        elements.append(el)

    loc_by_bone = {}
    for s in model.sockets:
        elements.append({"name": s.name, "position": _r(s.point), "rotation": [0, 0, 0],
                         "ignore_inherited_scale": False, "visibility": True, "locked": False,
                         "type": "locator", "uuid": s.uuid})
        loc_by_bone.setdefault(s.box.bone, []).append(s.uuid)

    def group(bone):
        g = {"name": bone.name, "origin": _r(bone.pivot), "color": 0, "uuid": bone.uuid,
             "export": True, "mirror_uv": False, "isOpen": bone.parent is None, "locked": False,
             "visibility": True, "autouv": 0}
        if np.any(bone.rot):
            g["rotation"] = _r(bone.rot)
        g["children"] = ([b.uuid for b in bone.boxes] + loc_by_bone.get(bone, [])
                         + [group(ch) for ch in bone.children])
        return g

    outliner = [group(b) for b in model.bones if b.parent is None]
    textures = [{"path": "", "name": f"{model.name}.png", "folder": "", "namespace": "", "id": "0",
                 "group": "", "width": size, "height": size, "uv_width": size, "uv_height": size,
                 "particle": False, "use_as_default": False, "layers_enabled": False,
                 "sync_to_project": "", "render_mode": "default", "render_sides": "auto",
                 "pbr_channel": "color", "frame_time": 1, "frame_order_type": "loop",
                 "frame_order": "", "frame_interpolate": False, "visible": True, "internal": True,
                 "saved": False, "uuid": str(uuid.uuid4()), "relative_path": "", "source": src}]

    bone_by_name = {b.name: b for b in model.bones}
    animations = []
    for an in model.anims:
        animators = {}
        for bname, chans in an.keyframes().items():
            bone = bone_by_name.get(bname)
            if bone is None:
                continue
            kfs = []
            for ch, samples in chans.items():
                for t, v in samples:
                    x, y, z = (float(q) for q in v)
                    if ch == "rotation":
                        x, y = -x, -y
                    elif ch == "position":
                        x = -x
                    kfs.append({"channel": ch, "data_points": [{"x": _num(x), "y": _num(y), "z": _num(z)}],
                                "uuid": str(uuid.uuid4()), "time": round(t, 4), "color": -1,
                                "interpolation": "catmullrom"})
            animators[bone.uuid] = {"name": bone.name, "type": "bone", "keyframes": kfs}
        animations.append({"uuid": str(uuid.uuid4()), "name": an.name,
                           "loop": "loop" if an.loop else "once", "override": False,
                           "length": round(an.length, 4), "snapping": 24, "selected": False,
                           "anim_time_update": "", "blend_weight": "", "start_delay": "",
                           "loop_delay": "", "animators": animators})

    data = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False},
            "name": model.name, "model_identifier": "", "visible_box": [1, 1, 0],
            "variable_placeholders": "", "variable_placeholder_buttons": [],
            "timeline_setups": [], "unhandled_root_fields": {},
            "resolution": {"width": size, "height": size},
            "elements": elements, "outliner": outliner, "textures": textures}
    if animations:
        data["animations"] = animations
    return data


def write(model, tex, path):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(to_bbmodel(model, tex), fh, separators=(",", ":"))
    return path
