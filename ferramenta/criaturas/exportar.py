"""`criaturas exportar <pasta> --estagio eN [--destino roblox,minecraft] [--geckolib]`.

8.1 Minecraft (Bedrock): geometria pelo motor (bbmodel_export_bedrock_geometry), animações por um
    exportador próprio (o motor não exporta animação Bedrock) e a textura.
    Com --geckolib, os mesmos arquivos com os nomes que o GeckoLib espera.
8.2 Roblox: cópia do modelo com a textura ×8, aberta no Blockbench desktop e exportada pelo
    export_model (codec gltf, binário, textura embutida, armadura e animações) -> .glb.
8.3 Verificações do .glb: validador glTF da Khronos sem erros, até 20 mil triângulos, nomes de
    ossos e locators preservados.
Saídas em modelos/<nome>/export/{minecraft,roblox,geckolib}/.
"""

import base64
import json
import shutil
import struct
import subprocess
from pathlib import Path

from PIL import Image

from criaturas import bbmodelo, desktop, estado, motor, relatorio
from criaturas.caminhos import RAIZ, pasta_modelo, relativo
from criaturas.cubificar import contexto, sha256
from criaturas.etapas import etapa
from criaturas.relatorio import msg
from criaturas.texturizar import _data_url
from criaturas.validar import modelo_atual

MAX_TRIANGULOS = 20000
VALIDADOR = RAIZ / "ferramenta" / "js" / "validar-gltf.mjs"
OPCOES_GLTF = {"encoding": "binary", "embed_textures": True, "armature": True, "animations": True}


# ---------- Minecraft ----------

def _numero(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        raise ValueError(f"chave com Molang ({v!r}): o pipeline só assa números") from None


def animacoes_bedrock(modelo: bbmodelo.Modelo, identificador: str) -> dict:
    """Animações do .bbmodel 5.0 no formato Bedrock (1.8.0).

    Sinais: os .bbmodel 5.0 guardam posição X e rotação X e Y com o sinal trocado em relação ao
    layout 4.x, que é o que o Bedrock lê (ver bbmodel_convert_legacy no motor). Aqui eles são desfeitos.
    """
    saida = {}
    for anim in modelo.animacoes:
        ossos = {}
        for animador in anim.get("animators", {}).values():
            if animador.get("type", "bone") != "bone":
                continue
            canais = {}
            for k in sorted(animador.get("keyframes", []), key=lambda k: k["time"]):
                p = k["data_points"][0]
                x, y, z = (_numero(p[e]) for e in ("x", "y", "z"))
                if k["channel"] == "rotation":
                    v = [-x, -y, z]
                elif k["channel"] == "position":
                    v = [-x, y, z]
                else:
                    v = [x, y, z]
                v = [round(c, 4) + 0.0 for c in v]
                chave = f"{round(float(k['time']), 4):g}"
                if "." not in chave:
                    chave += ".0"
                valor = {"post": v, "lerp_mode": "catmullrom"} if k.get("interpolation") == "catmullrom" else v
                canais.setdefault(k["channel"], {})[chave] = valor
            if canais:
                ossos[animador["name"]] = canais
        loop = {"loop": True, "hold": "hold_on_last_frame"}.get(anim.get("loop"), False)
        corpo = {"animation_length": float(anim["length"]), "bones": ossos}
        if loop:
            corpo = {"loop": loop, **corpo}
        saida[f"animation.{identificador}.{anim['name']}"] = corpo
    return {"format_version": "1.8.0", "animations": saida}


def exportar_minecraft(arquivo: Path, textura: Path | None, destino: Path, identificador: str, geckolib: bool = False) -> dict:
    destino.mkdir(parents=True, exist_ok=True)
    geo = destino / f"{identificador}.geo.json"
    r = motor.exportar_bedrock(arquivo, geo)
    dados = json.loads(geo.read_text(encoding="utf-8"))
    for g in dados.get("minecraft:geometry", []):
        g["description"]["identifier"] = f"geometry.{identificador}"
    geo.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    modelo = bbmodelo.ler(arquivo)
    anim = destino / f"{identificador}.animation.json"
    anim.write_text(json.dumps(animacoes_bedrock(modelo, identificador), ensure_ascii=False, indent=1), encoding="utf-8")
    arquivos = [geo, anim]
    if textura and textura.exists():
        shutil.copy(textura, destino / f"{identificador}.png")
        arquivos.append(destino / f"{identificador}.png")
    if geckolib:
        # o GeckoLib lê os mesmos formatos (geo Bedrock e animações Bedrock) com estes nomes de pasta
        gk = destino.parent / "geckolib"
        for sub, origem in (("geo", geo), ("animations", anim)):
            (gk / sub).mkdir(parents=True, exist_ok=True)
            arquivos.append(Path(shutil.copy(origem, gk / sub / origem.name)))
        if textura and textura.exists():
            (gk / "textures").mkdir(parents=True, exist_ok=True)
            arquivos.append(Path(shutil.copy(textura, gk / "textures" / f"{identificador}.png")))
    return {"arquivos": arquivos, "pulados": r.get("skipped", []), "animacoes": len(modelo.animacoes)}


# ---------- Roblox ----------

def copia_roblox(arquivo: Path, textura_roblox: Path, destino: Path, base: str) -> Path:
    """Cópia do .bbmodel com a textura ampliada (a resolução do projeto não muda: as UVs continuam valendo).

    O nome leva um pedaço do hash do conteúdo: o Blockbench reaproveita a aba de um arquivo já aberto
    sem reler o disco, então um conteúdo novo precisa de um nome novo (o mesmo conteúdo pode reaproveitar).
    """
    import numpy as np

    destino.mkdir(parents=True, exist_ok=True)
    with Image.open(textura_roblox) as im:
        tex = np.asarray(im.convert("RGBA"))
    marca = sha256(arquivo)[:8]
    for velha in destino.glob(f"{base}.*.bbmodel"):  # cópias anteriores, feitas por aqui
        if velha.name != f"{base}.{marca}.bbmodel":
            velha.unlink()
    copia = destino / f"{base}.{marca}.bbmodel"
    if not copia.exists():
        shutil.copy(arquivo, copia)
        op = {"op": "update_texture", "target": 0, "source": _data_url(tex), "width": tex.shape[1], "height": tex.shape[0]}
        if (json.loads(arquivo.read_text(encoding="utf-8")).get("textures") or [{}])[0].get("group") == "":
            op["material"] = None  # o Blockbench desktop grava group "" e o motor o lê como um material sem nome
        motor.editar(copia, [op, {"op": "set_model_properties", "name": copia.stem}])
    return copia


def exportar_glb(copia: Path, saida: Path) -> dict:
    """Abre a cópia no Blockbench desktop e exporta o .glb pelo export_model (conteúdo embutido na resposta)."""
    if not desktop.respondendo():
        desktop.abrir(copia)
    else:
        desktop.abrir(copia, esperar_ms=30000)
    info = json.loads(desktop.texto(desktop.chamar("get_capabilities")))
    projeto = info.get("project", {}).get("name")
    if projeto != copia.stem:
        raise desktop.DesktopErro(f"o projeto ativo no Blockbench é {projeto!r}, não {copia.stem!r}")
    r = desktop.chamar("export_model", {"codec_id": "gltf", "options": OPCOES_GLTF, "result_format": "embedded",
                                        "max_content_length": 2_000_000})
    blob = next((c["resource"]["blob"] for c in r["content"] if c.get("type") == "resource" and "blob" in c.get("resource", {})), None)
    if blob is None:
        raise desktop.DesktopErro("o export_model não devolveu o .glb (grande demais para vir embutido?)")
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_bytes(base64.b64decode(blob))
    return {"bytes": saida.stat().st_size}


ESCALA_GLTF = 1 / 16  # o exportador glTF do Blockbench usa 1 bloco = 1 unidade


def acrescentar_locators(caminho: Path, modelo: bbmodelo.Modelo) -> list[str]:
    """Põe cada locator como nó filho do osso dele no .glb (o exportador do Blockbench não leva locators).

    No Roblox, Bone herda de Attachment: o nó importado serve de ponto de ancoragem. A translação é
    (posição - pivô do osso) em unidades glTF, no referencial do osso, como os outros nós do arquivo.
    """
    dados = caminho.read_bytes()
    tam_json = struct.unpack("<I", dados[12:16])[0]
    gltf = json.loads(dados[20:20 + tam_json].decode("utf-8"))
    resto = dados[20 + tam_json:]  # chunk BIN, intacto
    por_nome = {n.get("name"): i for i, n in enumerate(gltf["nodes"]) if "mesh" not in n}
    existentes = {n.get("name") for n in gltf["nodes"]}
    criados = []
    for loc in modelo.locators:
        if loc.nome in existentes or loc.osso not in por_nome:
            continue
        osso = modelo.ossos[loc.osso]
        t = [round(float(v) * ESCALA_GLTF, 6) for v in (loc.posicao - osso.origem)]
        gltf["nodes"].append({"name": loc.nome, "translation": t})
        pai = gltf["nodes"][por_nome[loc.osso]]
        pai.setdefault("children", []).append(len(gltf["nodes"]) - 1)
        criados.append(loc.nome)
    if criados:
        novo = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
        novo += b" " * ((4 - len(novo) % 4) % 4)
        total = 12 + 8 + len(novo) + len(resto)
        caminho.write_bytes(b"glTF" + struct.pack("<II", 2, total) + struct.pack("<I", len(novo)) + b"JSON" + novo + resto)
    return criados


def json_do_glb(caminho: Path) -> dict:
    dados = caminho.read_bytes()
    if dados[:4] != b"glTF":
        raise ValueError(f"{caminho.name} não é um .glb")
    tamanho = struct.unpack("<I", dados[12:16])[0]
    return json.loads(dados[20:20 + tamanho].decode("utf-8"))


def verificar_glb(caminho: Path, modelo: bbmodelo.Modelo) -> tuple[list, list, dict]:
    erros, avisos, resumo = [], [], {}
    proc = subprocess.run(["node", str(VALIDADOR), str(caminho)], capture_output=True, text=True, encoding="utf-8", timeout=300)
    if proc.returncode != 0:
        erros.append(msg("validador", f"o validador glTF não rodou: {proc.stderr.strip()[:300]}"))
        return erros, avisos, resumo
    v = json.loads(proc.stdout.strip().splitlines()[-1])
    resumo["validador"] = {"erros": v["erros"], "avisos": v["avisos"]}
    if v["erros"]:
        erros += [msg("gltf", f"{m['codigo']}: {m['texto']} ({m.get('ponteiro', '')})") for m in v["mensagens"] if m["gravidade"] == 0]
    avisos += [msg("gltf", f"{m['codigo']}: {m['texto']}") for m in v["mensagens"] if m["gravidade"] == 1][:5]
    tri = (v.get("info") or {}).get("totalTriangleCount", 0)
    resumo["triangulos"] = tri
    if tri > MAX_TRIANGULOS:
        erros.append(msg("triangulos", f"{tri} triângulos (limite do Roblox: {MAX_TRIANGULOS})"))
    nos = {n.get("name") for n in json_do_glb(caminho).get("nodes", [])}
    ossos = set(modelo.ossos) - {"root"}
    faltam_ossos = sorted(o for o in ossos if o not in nos)
    faltam_locs = sorted(l.nome for l in modelo.locators if l.nome not in nos)
    resumo["nos"] = len(nos)
    if faltam_ossos:
        erros.append(msg("ossos", "ossos sem nó no .glb: " + ", ".join(faltam_ossos[:8])))
    if faltam_locs:
        avisos.append(msg("locators", "locators sem nó no .glb (viram Attachments à mão no Studio): " + ", ".join(faltam_locs[:8])))
    resumo["animacoes"] = len(json_do_glb(caminho).get("animations", []))
    return erros, avisos, resumo


# ---------- CLI ----------

@etapa("exportar")
def cmd_exportar(args) -> int:
    pasta = Path(args.pasta)
    nome = pasta.resolve().name
    ctx = contexto(nome, args.estagio)
    destino_est = ctx["destino"]
    arquivo = modelo_atual(destino_est, ctx["relatorio"])
    if arquivo is None:
        print("exportar: nenhum .bbmodel (rode cubificar antes)")
        return 1
    estado.adotar_e_avisar(destino_est, arquivo, nome, args.estagio, "exportar")
    base = arquivo.stem.split(".v")[0]
    identificador = base.replace("-", "_")
    destinos = [d.strip() for d in (args.destino or ",".join(ctx["entrada"].get("destino") or ["roblox"])).split(",") if d.strip()]
    export = pasta_modelo(nome) / "export"
    erros, avisos, resumo, arquivos = [], [], {}, []
    modelo = bbmodelo.ler(arquivo)
    if "minecraft" in destinos or args.geckolib:
        try:
            r = exportar_minecraft(arquivo, destino_est / "textura.png", export / "minecraft", identificador, args.geckolib)
            arquivos += r["arquivos"]
            resumo["minecraft"] = {"animacoes": r["animacoes"], "pulados": r["pulados"]}
            if r["pulados"]:
                avisos.append(msg("bedrock_pulados", f"elementos fora da geometria Bedrock: {r['pulados']}"))
        except (motor.MotorErro, ValueError) as e:
            erros.append(msg("minecraft", str(e)))
    if "roblox" in destinos:
        textura_roblox = destino_est / "textura-roblox.png"
        if not textura_roblox.exists():
            erros.append(msg("roblox", "falta textura-roblox.png (rode texturizar antes)"))
        else:
            try:
                copia = copia_roblox(arquivo, textura_roblox, export / "roblox", base)
                glb = export / "roblox" / f"{base}.glb"
                exportar_glb(copia, glb)
                acrescentar_locators(glb, modelo)
                e, a, res = verificar_glb(glb, modelo)
                erros += e
                avisos += a
                resumo["roblox"] = res
                arquivos.append(glb)
            except (desktop.DesktopErro, motor.MotorErro, ValueError, OSError) as e:
                erros.append(msg("roblox", f"{e} (plano B: exportador glTF próprio ainda não existe)"))
    ok = not erros
    relatorio.registrar(destino_est, nome, args.estagio, "exportar", ok, erros=erros, avisos=avisos,
                        arquivos=[relativo(a) for a in arquivos], resumo=resumo)
    linhas = [f"exportar {arquivo.name} -> {', '.join(destinos)}{' + geckolib' if args.geckolib else ''}: {'OK' if ok else 'COM ERROS'}"]
    if "roblox" in resumo:
        r = resumo["roblox"]
        linhas.append(f"  roblox: {r.get('triangulos', '?')} triângulos, {r.get('nos', '?')} nós, {r.get('animacoes', '?')} animações, "
                      f"validador {r.get('validador', {}).get('erros', '?')} erros")
    if "minecraft" in resumo:
        linhas.append(f"  minecraft: geo + {resumo['minecraft']['animacoes']} animações + textura")
    linhas += [f"  {relativo(a)}" for a in arquivos[:6]]
    linhas += relatorio.linhas_mensagens("Erros", erros)
    linhas += relatorio.linhas_mensagens("Avisos", avisos)
    relatorio.imprimir(linhas)
    return 0 if ok else 1
