"""Executado SOMENTE por blender --background --factory-startup --python.

Cria uma cena isolada, assa canais locais, exporta GLB e mede a malha avaliada.
O segundo processo importa GLB; compara superfícies e pivôs a 120 Hz.
"""

import hashlib
import json
import math
import sys
import time
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).parent))
from movimento import ordered, pose

UNIT = 1/16
RATE = 240  # inclui subframes entre as chaves de autoria a 120 Hz.
# Canônico (X,Y,Z) -> Blender (X,-Z,Y), incluindo escala. glTF volta para Y-up.
C = np.array([[UNIT, 0, 0, 0], [0, 0, -UNIT, 0], [0, UNIT, 0, 0], [0, 0, 0, 1.]])
CI = np.linalg.inv(C)


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def canonical(points):
    p = np.array(points, float)
    return np.column_stack((p[:, 0], p[:, 2], -p[:, 1])) / UNIT


def converted(point):
    return (C @ np.array([*point, 1.]))[:3]


def evaluated(mesh):
    deps = bpy.context.evaluated_depsgraph_get()
    obj = mesh.evaluated_get(deps)
    data = obj.to_mesh()
    points = canonical([obj.matrix_world @ v.co for v in data.vertices])
    obj.to_mesh_clear()
    return points


def obb_penetration(a, b):
    """SAT de caixas orientadas; AABB sozinho acusa falso contato quando o body gira."""
    aa = [a[i]-a[0] for i in (1, 2, 4)]
    bb = [b[i]-b[0] for i in (1, 2, 4)]
    axes = [*aa, *bb, *[np.cross(x, y) for x in aa for y in bb]]
    depth = float("inf")
    for axis in axes:
        size = np.linalg.norm(axis)
        if size < 1e-8:
            continue
        axis = axis/size
        pa, pb = a@axis, b@axis
        overlap = min(pa.max(), pb.max())-max(pa.min(), pb.min())
        if overlap <= 1e-6:
            return 0.
        depth = min(depth, float(overlap))
    return depth


def make_scene(job, atlas, geometry, dest):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.name = job["id"]
    scene.render.fps = job["animacao"]["fps"]
    scene.unit_settings.system = "NONE"
    scene.unit_settings.scale_length = 1
    arm_data = bpy.data.armatures.new("Skeleton")
    arm = bpy.data.objects.new("Skeleton", arm_data)
    scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    rest = [{"nome": "Raiz", "pai": None, "pivo": [0, 0, 0]}, *ordered(job["plano"]["ossos"])]
    for spec in rest:
        bone = arm_data.edit_bones.new(spec["nome"])
        bone.head = converted(spec["pivo"])
        # Todos os eixos locais em repouso são identidade; pivô define a junta.
        bone.tail = bone.head + Vector((0., .05, 0.))
        parent = "Raiz" if spec["nome"] == "root" else spec["pai"]
        if parent:
            bone.parent = arm_data.edit_bones[parent]
        bone.use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")
    data = bpy.data.meshes.new("Cubos")
    data.from_pydata([converted(p) for p in geometry["vertices"]], [], geometry["faces"])
    data.update()
    uv = data.uv_layers.new(name="UVMap")
    for poly, coords in zip(data.polygons, geometry["uvs"]):
        poly.use_smooth = False
        for loop, coord in zip(poly.loop_indices, coords):
            uv.data[loop].uv = coord
    mesh = bpy.data.objects.new("Raiz", data)
    scene.collection.objects.link(mesh)
    for name in sorted(set(geometry["ossos_vertices"])):
        vg = mesh.vertex_groups.new(name=name)
        vg.add([i for i, n in enumerate(geometry["ossos_vertices"]) if n == name], 1., "REPLACE")
    mod = mesh.modifiers.new("SkinRigida", "ARMATURE")
    mod.object = arm
    mod.use_deform_preserve_volume = False
    material = bpy.data.materials.new("PixelMatte")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    principled = nodes.get("Principled BSDF")
    principled.inputs["Metallic"].default_value = 0
    principled.inputs["Roughness"].default_value = 1
    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "Atlas"
    tex.image = bpy.data.images.load(str(dest / atlas["imagens"]["base"]["roblox"]))
    tex.image.pack()
    tex.interpolation = "Closest"
    tex.extension = "EXTEND"
    material.node_tree.links.new(tex.outputs["Color"], principled.inputs["Base Color"])
    material.node_tree.links.new(tex.outputs["Alpha"], principled.inputs["Alpha"])
    # glTF reconhece o alpha threshold a partir do dithered, sem nós proprietários no arquivo.
    material.surface_render_method = "DITHERED"
    material.use_backface_culling = True
    mesh.data.materials.append(material)
    for loc in job["plano"]["locators"]:
        obj = bpy.data.objects.new(loc["nome"], None)
        scene.collection.objects.link(obj)
        obj.parent = arm
        obj.parent_type = "BONE"
        obj.parent_bone = loc["osso"]
        # Parenting de empty ao bone considera a cauda do bone, não a cabeça.
        pos = converted(loc["posicao"])
        head = arm.data.bones[loc["osso"]].head_local
        obj.location = Vector(pos) - head - Vector((0., .05, 0.))
    return arm, mesh, tex


def bake(job, arm):
    fps = job["animacao"]["fps"]
    specs = {b["nome"]: b for b in job["plano"]["ossos"]}
    actions = {}
    for clip, duration in job["animacao"]["duracoes"].items():
        action = bpy.data.actions.new(clip)
        arm.animation_data_create()
        arm.animation_data.action = action
        previous = {}
        for frame in range(round(duration*fps)+1):
            world, _ = pose(job, clip, frame/fps)
            for name in ["Raiz", *[b["nome"] for b in ordered(job["plano"]["ossos"])]]:
                pb = arm.pose.bones[name]
                if name == "Raiz":
                    basis = np.eye(4)
                else:
                    parent = specs[name]["pai"]
                    current = C @ world[name] @ CI
                    parent_world = C @ world[parent] @ CI if parent else np.eye(4)
                    local_rest = np.array(pb.bone.matrix_local)
                    if parent:
                        local_rest = np.linalg.inv(np.array(arm.data.bones[parent].matrix_local)) @ local_rest
                    basis = np.linalg.inv(local_rest) @ np.linalg.inv(parent_world) @ current
                pb.matrix_basis = Matrix(basis.tolist())
                pb.rotation_mode = "QUATERNION"
                # Mesmo hemisfério: elimina saltos de sinal entre quaternions equivalentes.
                q = pb.rotation_quaternion.copy()
                if name in previous and q.dot(previous[name]) < 0:
                    q.negate()
                    pb.rotation_quaternion = q
                previous[name] = q.copy()
                pb.keyframe_insert("location", frame=frame, group=name)
                pb.keyframe_insert("rotation_quaternion", frame=frame, group=name)
            bpy.context.view_layer.update()
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        for key in fc.keyframe_points:
                            key.interpolation = "LINEAR"
        action.use_fake_user = True
        actions[clip] = action
    arm.animation_data.action = None
    return actions


def select_action(arm, action):
    arm.animation_data_create()
    arm.animation_data.action = action
    if action.slots:
        arm.animation_data.action_slot = action.slots[0]


def measure(job, arm, mesh, actions, geometry):
    scene = bpy.context.scene
    fps = job["animacao"]["fps"]
    rest = {b["nome"]: np.array(b["pivo"], float) for b in job["plano"]["ossos"]}
    source = np.array(geometry["vertices"])
    samples, metrics = {}, {}
    for clip, duration in job["animacao"]["duracoes"].items():
        select_action(arm, actions[clip])
        poses, frames = [], []
        min_floor, max_skin, max_foot, max_step, max_locator = 1e10, 0., 0., 0., 0.
        support_slip, max_penetration, worst_pair = 0., 0., None
        velocities, contacts, bounds = [], [], []
        previous = None
        n = round(duration*RATE)
        for i in range(n+1):
            t = i/RATE
            frame = t*fps
            scene.frame_set(math.floor(frame), subframe=frame-math.floor(frame))
            bpy.context.view_layer.update()
            pts = evaluated(mesh)
            world, feet = pose(job, clip, t)
            expected = np.empty_like(source)
            for j, bone in enumerate(geometry["ossos_vertices"]):
                expected[j] = (world[bone] @ np.array([*(source[j]-rest[bone]), 1]))[:3]
            max_skin = max(max_skin, float(np.max(np.linalg.norm(pts-expected, axis=1))))
            min_floor = min(min_floor, float(pts[:, 1].min()))
            pose_bones = {pb.name: canonical([arm.matrix_world @ pb.head])[0].tolist() for pb in arm.pose.bones}
            locators = {}
            for loc in job["plano"]["locators"]:
                actual = canonical([bpy.data.objects[loc["nome"]].matrix_world.translation])[0]
                expected_loc = (world[loc["osso"]] @ np.array([*(np.array(loc["posicao"])-rest[loc["osso"]]), 1]))[:3]
                max_locator = max(max_locator, float(np.linalg.norm(actual-expected_loc)))
                locators[loc["nome"]] = actual.tolist()
            for side in ("left", "right"):
                max_foot = max(max_foot, float(np.linalg.norm(np.array(pose_bones[f"foot_{side}"])-feet[side]["alvo"])))
            if previous is not None:
                max_step = max(max_step, float(np.max(np.linalg.norm(pts-previous, axis=1))))
            previous = pts
            # AABB só para pares afastados da hierarquia: triagem conservadora, não teste exato de colisão.
            cube_bounds = {}
            for piece in geometry["pecas"]:
                p = pts[piece["indices"]]
                cube_bounds[piece["nome"]] = p
            pairs = [("arm_left_cube", "body_cube"), ("arm_right_cube", "body_cube"),
                     ("foot_left_cube", "foot_right_cube"), ("head_cube", "tail_2_cube")]
            for a, b in pairs:
                if a in cube_bounds and b in cube_bounds:
                    penetration = obb_penetration(cube_bounds[a], cube_bounds[b])
                    if penetration > max_penetration:
                        max_penetration, worst_pair = penetration, [a, b, round(t, 4)]
            poses.append({"t": round(t, 7), "vertices": pts.round(7).tolist(), "pivos": pose_bones, "locators": locators})
            frames.append(pts)
            contacts.append(feet)
        # Compensa deslocamento do corpo pelo avanço esperado no mundo durante apoio.
        if clip in ("walk", "run"):
            stance = job["animacao"][f"apoio_{clip}"]
            speed = job["animacao"][f"passo_{clip}"]/(stance*duration)
            for side in ("left", "right"):
                for i in range(1, len(poses)):
                    if contacts[i][side]["apoio"] and contacts[i-1][side]["apoio"]:
                        a = np.array(poses[i-1]["pivos"][f"foot_{side}"])
                        b = np.array(poses[i]["pivos"][f"foot_{side}"])
                        delta = b-a-np.array([0, 0, speed/RATE])
                        support_slip = max(support_slip, float(np.linalg.norm(delta)))
        seam = float(np.max(np.abs(frames[0]-frames[-1])))
        seam_velocity = float(np.max(np.abs((frames[1]-frames[0])-(frames[-1]-frames[-2])))*RATE)
        # Projeção do pivô body, só diagnóstico aproximado de equilíbrio, não centro de massa.
        balance = []
        for i, sample in enumerate(poses):
            support = [np.array(sample["pivos"][f"foot_{s}"])[[0, 2]] for s in ("left", "right") if contacts[i][s]["apoio"]]
            if support:
                center = np.array(sample["pivos"]["body"])[[0, 2]]
                # margem do pé da fixture; é envelope de apoio, não solver dinâmico.
                low, high = np.min(support, axis=0)-[.8, 2.], np.max(support, axis=0)+[.8, .8]
                balance.append(float(max(0., *(low-center), *(center-high))))
        metrics[clip] = {"piso_min_unidades": round(min_floor, 6), "erro_skin_unidades": round(max_skin, 6),
                         "erro_pe_ik_unidades": round(max_foot, 6), "erro_locators_unidades": round(max_locator, 6),
                         "passo_max_por_amostra": round(max_step, 6),
                         "loop_erro_unidades": round(seam, 6), "loop_erro_velocidade": round(seam_velocity, 6),
                         "deslizamento_apoio_por_amostra": round(support_slip, 6),
                         "triagem_obb_penetracao": round(max_penetration, 6), "triagem_pior_par": worst_pair,
                         "projecao_body_fora_apoio_max": round(max(balance, default=0.), 6), "amostras": n+1, "taxa_hz": RATE}
        samples[clip] = poses
    return metrics, samples


def render_previews(job, arm, mesh, actions, dest):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 256
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.color = (.25, .25, .25)
    scene.view_settings.view_transform = "Standard"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.fps = job["animacao"]["fps"]
    target = Vector(converted((0, 10, .5)))
    data = bpy.data.cameras.new("PreviewCamera")
    camera = bpy.data.objects.new("PreviewCamera", data)
    scene.collection.objects.link(camera)
    data.type, data.ortho_scale = "ORTHO", 1.65
    scene.camera = camera
    for i, point in enumerate(((2, -3, 4), (-2, 1, 3))):
        light_data = bpy.data.lights.new(f"PreviewLight{i}", "AREA")
        light_data.energy, light_data.shape, light_data.size = (120 if i == 0 else 70), "DISK", 5
        light = bpy.data.objects.new(light_data.name, light_data)
        scene.collection.objects.link(light)
        light.location = point
    def snap(path, position):
        camera.location = position
        camera.rotation_euler = (target-camera.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
    select_action(arm, actions["idle"])
    scene.frame_set(0)
    views = {"frente": (0, 4, .65), "lado": (4, 0, .65), "costas": (0, -4, .65), "tres-quartos": (3, 4, 2.4)}
    for name, location in views.items():
        snap(dest/f"vista-{name}.png", location)
    for clip, duration in job["animacao"]["duracoes"].items():
        select_action(arm, actions[clip])
        for i in range(12):
            frame = duration*i/12*scene.render.fps
            scene.frame_set(int(frame), subframe=frame-int(frame))
            snap(dest/f"previa-{clip}-{i:02}.png", views["tres-quartos"])
    scene.camera = None
    # Previews não entram no GLB nem na cena de autoria salva.
    for obj in list(scene.objects):
        if obj.type in ("CAMERA", "LIGHT"):
            bpy.data.objects.remove(obj, do_unlink=True)


def build(job, dest):
    start = time.perf_counter()
    atlas = json.loads((dest/"atlas.json").read_text(encoding="utf-8"))
    geometry = json.loads((dest/"malha.json").read_text(encoding="utf-8"))
    arm, mesh, tex = make_scene(job, atlas, geometry, dest)
    actions = bake(job, arm)
    baked = time.perf_counter()
    metrics, samples = measure(job, arm, mesh, actions, geometry)
    dump(dest/"validacao-autoria.json", metrics)
    dump(dest/"amostras-autoria.json", samples)
    arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(dest/"criatura.blend"), check_existing=False)
    for variant, files in atlas["imagens"].items():
        tex.image = bpy.data.images.load(str(dest/files["roblox"]), check_existing=True)
        bpy.ops.export_scene.gltf(filepath=str(dest/f"{job['id']}-{variant}.glb"), export_format="GLB",
                                  export_yup=True, export_animations=True, export_animation_mode="ACTIONS",
                                  export_force_sampling=True, export_frame_range=False,
                                  export_frame_step=1, export_optimize_animation_size=False,
                                  export_def_bones=False, export_leaf_bone=False, export_materials="EXPORT",
                                  export_cameras=False, export_lights=False, export_extras=True)
    exported = time.perf_counter()
    tex.image = bpy.data.images.get(Path(atlas["imagens"]["base"]["roblox"]).name)
    render_previews(job, arm, mesh, actions, dest)
    dump(dest/"execucao-blender.json", {"versao": bpy.app.version_string, "build_hash": bpy.app.build_hash.decode(),
         "parametros": {"background": True, "factory_startup": True, "threads": 2, "fps": job["animacao"]["fps"], "seed": None},
         "duracoes_segundos": {"construcao_e_bake": baked-start, "medicao_e_exportacao": exported-baked,
                               "previas": time.perf_counter()-exported}})


def compare_surface(a, b):
    # Export glTF divide vértices em costuras/normais. Hausdorff sobre vértices ignora a duplicação.
    distances = np.sum((a[:, None, :]-b[None, :, :])**2, axis=2)
    return float(math.sqrt(max(distances.min(axis=0).max(), distances.min(axis=1).max())))


def reimport(job, dest):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    # O importador converte segundos em frames na importação, usando o FPS corrente.
    bpy.context.scene.render.fps = job["animacao"]["fps"]
    bpy.ops.import_scene.gltf(filepath=str(dest/f"{job['id']}-base.glb"))
    arm = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
    # O importador cria Icosphere como custom_shape dos ossos; não é geometria do GLB.
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH" and o.find_armature() == arm]
    if len(meshes) != 1:
        raise ValueError(f"reimportação: {len(meshes)} malhas, esperado 1")
    mesh = meshes[0]
    expected = json.loads((dest/"amostras-autoria.json").read_text(encoding="utf-8"))
    # Importador cria NLA tracks, um por clipe; não misturar ações ao conferir.
    actions = {}
    for track in arm.animation_data.nla_tracks:
        for strip in track.strips:
            actions[track.name] = strip.action
        track.mute = True
    report = {}
    scene = bpy.context.scene
    scene.render.fps = job["animacao"]["fps"]
    for name, samples in expected.items():
        if name not in actions:
            # Nomes de actions podem ter sufixo do objeto; a correspondência tem de ser inequívoca.
            matches = [a for a in bpy.data.actions if a.name == name or a.name.startswith(name+"_")]
            if len(matches) != 1:
                raise ValueError("clipe reimportado ausente/ambíguo: "+name)
            actions[name] = matches[0]
        select_action(arm, actions[name])
        max_surface, max_pivot, max_locator = 0., 0., 0.
        for sample in samples:
            frame = sample["t"]*scene.render.fps
            scene.frame_set(math.floor(frame), subframe=frame-math.floor(frame))
            bpy.context.view_layer.update()
            max_surface = max(max_surface, compare_surface(evaluated(mesh), np.array(sample["vertices"])))
            for bone, target in sample["pivos"].items():
                if bone not in arm.pose.bones:
                    raise ValueError("osso perdido na reimportação: "+bone)
                actual = canonical([arm.matrix_world @ arm.pose.bones[bone].head])[0]
                max_pivot = max(max_pivot, float(np.linalg.norm(actual-target)))
            for loc, target in sample["locators"].items():
                actual = canonical([bpy.data.objects[loc].matrix_world.translation])[0]
                max_locator = max(max_locator, float(np.linalg.norm(actual-target)))
        report[name] = {"erro_superficie_unidades": round(max_surface, 7),
                        "erro_pivos_unidades": round(max_pivot, 7), "erro_locators_unidades": round(max_locator, 7),
                        "amostras": len(samples)}
    dump(dest/"validacao-reimportacao.json", {"clipes": report, "malhas": 1, "vertices_reimportados": len(mesh.data.vertices),
                                             "versao_blender": bpy.app.version_string})


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--")+1:]
    mode, folder = args
    dest = Path(folder)
    job = json.loads((dest/"entrada-normalizada.json").read_text(encoding="utf-8"))
    if mode == "construir":
        build(job, dest)
    elif mode == "reimportar":
        reimport(job, dest)
    else:
        raise ValueError("modo desconhecido")
