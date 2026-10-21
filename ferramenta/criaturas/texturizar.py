"""`criaturas texturizar <pasta> --estagio eN`: pinta a textura a partir das vistas do conceito.

5.1 Cada face de cubo amostra a vista correspondente, pelo mapeamento mundo -> imagem do medir:
    frente (north) <- frente; laterais (west/east) <- lado; costas (south) <- costas;
    topo e base <- cor média das bordas vizinhas. Um texel só é amostrado se o próprio cubo
    (ou um adesivo dele) é o que aparece naquele pixel; o resto é preenchido a partir dos vizinhos.
5.2 Paleta de até 5 cores base + 2 de destaque, rampas OKLCH, sombreado pintado (topo mais claro,
    base mais escura, AO simples nas dobras) e limpeza de pixels isolados.
5.3 Adesivos do rosto (olhos, pupilas, pálpebras, boca) são cubos próprios e pegam a cor da sua região.
    Com --olho-pintado (estilo Digimod) eles são removidos e o olho fica pintado na cabeça.
5.4 Planos têm recorte: o alfa vem da silhueta da parte na vista.
5.5 textura-roblox.png: ampliada ×8 por vizinho mais próximo, com a cor das ilhas espalhada por 2 px.
"""

import base64
import io
from pathlib import Path

import numpy as np
from PIL import Image

from criaturas import bbmodelo, cores, motor, relatorio, render
from criaturas.caminhos import relativo
from criaturas.cubificar import contexto, sha256
from criaturas.etapas import etapa
from criaturas.relatorio import msg
from criaturas.validar import modelo_atual

CELULAS = 32
FACE_VISTA = {"north": "frente", "south": "costas", "west": "lado", "east": "lado"}
ROBLOX_FATOR = 8
ROBLOX_MARGEM = 2
DELTA_E_MAX = 10.0
ADESIVOS_ROSTO = ("eye_", "pupil_", "eyelid_", "mouth", "brow_")


# ---------- projeção das vistas ----------

def projecao_da_vista(vista: str, mapa: dict, u: float, tamanho: tuple[int, int]) -> render.Projecao:
    """Projeção que leva o mundo ao pixel do recorte preparado (mesma grade do medir)."""
    largura, altura = tamanho
    px = altura / CELULAS
    k = u * mapa["fator"]
    direita = {"frente": (-1, 0, 0), "lado": (0, 0, 1), "costas": (1, 0, 0)}[vista]
    frente = {"frente": (0, 0, 1), "lado": (1, 0, 0), "costas": (0, 0, -1)}[vista]
    return render.Projecao(np.array(direita, float), np.array([0, 1.0, 0]), np.array(frente, float),
                           px / k, -mapa["centro"] * k, CELULAS * k, 0, (largura, altura))


class Vista:
    def __init__(self, nome, imagem: Image.Image, proj: render.Projecao, ids: np.ndarray):
        rgba = np.asarray(imagem.convert("RGBA"))
        self.nome, self.rgb, self.alfa, self.proj, self.ids = nome, rgba[..., :3], rgba[..., 3] > 127, proj, ids

    def amostrar(self, pontos: np.ndarray, aceitos: set[int]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """(cores, visível, dentro da silhueta) de pontos do mundo."""
        p = self.proj.pixel(pontos)
        x = np.clip(np.floor(p[:, 0]).astype(int), 0, self.rgb.shape[1] - 1)
        y = np.clip(np.floor(p[:, 1]).astype(int), 0, self.rgb.shape[0] - 1)
        fora = (p[:, 0] < 0) | (p[:, 1] < 0) | (p[:, 0] >= self.rgb.shape[1]) | (p[:, 1] >= self.rgb.shape[0])
        visivel = np.isin(self.ids[y, x], list(aceitos)) & ~fora & self.alfa[y, x]
        return self.rgb[y, x], visivel, self.alfa[y, x] & ~fora


# ---------- texels ----------

def texels_da_face(cubo: bbmodelo.Cubo, face: str, matriz: np.ndarray):
    """(coordenadas [N, 2] dos texels, pontos do mundo [N, 3]) de uma face, ou None se ela não tem área."""
    uv = cubo.faces.get(face, {}).get("uv")
    if uv is None:
        return None
    u1, v1, u2, v2 = uv
    if abs(u2 - u1) < 1e-9 or abs(v2 - v1) < 1e-9:
        return None
    a, b = cubo.de - cubo.inflate, cubo.ate + cubo.inflate
    lim = np.stack([a, b])
    cantos = np.array([[lim[i, 0], lim[j, 1], lim[k, 2]] for i, j, k in render.CANTOS_FACE[face]])
    cantos = bbmodelo.aplicar(matriz, cantos)
    us = np.arange(int(np.floor(min(u1, u2))), int(np.ceil(max(u1, u2))))
    vs = np.arange(int(np.floor(min(v1, v2))), int(np.ceil(max(v1, v2))))
    U, V = np.meshgrid(us, vs)
    U, V = U.ravel(), V.ravel()
    s = (U + 0.5 - u1) / (u2 - u1)
    t = (V + 0.5 - v1) / (v2 - v1)
    pontos = cantos[0] + s[:, None] * (cantos[1] - cantos[0]) + t[:, None] * (cantos[2] - cantos[0])
    return np.stack([U, V], 1), pontos


def _normal(face, matriz):
    n = matriz[:3, :3] @ np.array(render.NORMAIS[face], float)
    return n / np.linalg.norm(n)


def _espessura_zero(cubo) -> int | None:
    tam = cubo.ate - cubo.de
    finos = [i for i in range(3) if tam[i] < 1e-6]
    return finos[0] if finos else None


def _preencher(tex, conhecido, regiao):
    """Espalha as cores conhecidas para os texels desconhecidos da região (vizinho mais próximo, por camadas)."""
    falta = regiao & ~conhecido
    feito = conhecido & regiao
    while falta.any():
        novo = np.zeros_like(falta)
        acumulado = np.zeros(tex.shape[:2] + (3,), float)
        n = np.zeros(tex.shape[:2], float)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            viz = np.roll(np.roll(feito, dy, 0), dx, 1)
            cor = np.roll(np.roll(tex[..., :3].astype(float), dy, 0), dx, 1)
            m = falta & viz
            acumulado[m] += cor[m]
            n[m] += 1
            novo |= m
        if not novo.any():
            break
        tex[novo, :3] = (acumulado[novo] / n[novo, None]).astype(np.uint8)
        feito |= novo
        falta &= ~novo
    return falta  # o que não deu para alcançar


# ---------- pintura ----------

def pintar(modelo: bbmodelo.Modelo, vistas: dict[str, Vista], cores_parte: dict[str, str], olho_pintado: bool = False) -> dict:
    """Textura RGBA (resolução do modelo) + estatísticas. Não usa a textura antiga do modelo."""
    larg, alt = modelo.resolucao
    tex = np.zeros((alt, larg, 4), np.uint8)
    conhecido = np.zeros((alt, larg), bool)
    amostrado = np.zeros((alt, larg), bool)  # texels que vieram direto de uma vista (o que se vê)
    regiao_volume = np.zeros((alt, larg), bool)
    regiao_plano = np.zeros((alt, larg), bool)
    face_de = {}  # (u, v) -> (cubo, face) para o sombreado
    mats = bbmodelo.matrizes_ossos(modelo)
    indice = {c.nome: i for i, c in enumerate(modelo.cubos)}
    filhos_adesivo = {}
    for c in modelo.cubos:
        osso = modelo.ossos.get(c.osso)
        if _espessura_zero(c) is not None and c.nome.startswith(ADESIVOS_ROSTO) and osso and osso.pai:
            pai_cubo = f"{osso.pai}_cube"
            filhos_adesivo.setdefault(pai_cubo, set()).add(indice[c.nome])
    stats = {"amostrados": 0, "preenchidos": 0, "transparentes_volume": 0}
    medias_parte = {}
    pontos_cubo = {}
    for c in modelo.cubos:
        if c.mirror_uv:
            continue  # a ilha é a do cubo espelhado (lado esquerdo)
        m = bbmodelo.matriz_cubo(modelo, c, mats)
        fino = _espessura_zero(c)
        aceitos = {indice[c.nome]} | filhos_adesivo.get(c.nome, set())
        base = cores.de_hex(cores_parte.get(c.nome, "#a0a0aa"))
        for face in render.CANTOS_FACE:
            r = texels_da_face(c, face, m)
            if r is None:
                continue
            (uv, pontos) = r
            U, V = uv[:, 0] % larg, uv[:, 1] % alt
            for (uu, vv) in zip(U, V):
                face_de[(int(uu), int(vv))] = (c.nome, face)
            pontos_cubo.setdefault(c.nome, []).append(pontos)
            if fino is None:
                regiao_volume[V, U] = True
            vista_nome = FACE_VISTA.get(face)
            if face in ("up", "down") or vista_nome is None:
                continue
            vista = vistas.get(vista_nome)
            consulta = pontos
            if vista is None and fino is not None and face == "south":
                vista = vistas.get("frente")  # plano sem vista de trás: as duas faces saem da frente
            if vista is None:
                continue  # volume sem essa vista: fica para o preenchimento
            if face == "east":
                consulta = pontos * np.array([-1, 1, 1])  # o lado de +X usa o lado esquerdo espelhado
            cor, visivel, silhueta = vista.amostrar(consulta, aceitos if face != "east" else _aceitos_espelho(modelo, c, indice, filhos_adesivo))
            tex[V[visivel], U[visivel], :3] = cor[visivel]
            conhecido[V[visivel], U[visivel]] = True
            amostrado[V[visivel], U[visivel]] = True
            if fino is not None and not c.nome.startswith(ADESIVOS_ROSTO):
                # plano: recorte pela silhueta da vista (fora dela, transparente); a cor só onde a parte aparece
                tex[V, U, 3] = np.where(silhueta, 255, 0)
                regiao_plano[V[silhueta], U[silhueta]] = True
            else:
                tex[V, U, 3] = 255  # volume e adesivo: sempre opacos
                if fino is not None:
                    regiao_plano[V, U] = True
            stats["amostrados"] += int(visivel.sum())
            if visivel.any() and face == "north":
                medias_parte[c.nome] = cor[visivel].astype(float).mean(0)
        # cor de reserva da parte, para o que nenhuma vista mostra
        if c.nome not in medias_parte:
            medias_parte[c.nome] = base.astype(float)

    # topo e base: cor média das bordas das faces vizinhas (o que já foi amostrado no cubo)
    for c in modelo.cubos:
        if c.mirror_uv:
            continue
        m = bbmodelo.matriz_cubo(modelo, c, mats)
        cores_laterais = []
        for face in ("north", "south", "east", "west"):
            r = texels_da_face(c, face, m)
            if r is None:
                continue
            uv, _ = r
            U, V = uv[:, 0] % larg, uv[:, 1] % alt
            ok = conhecido[V, U]
            if ok.any():
                cores_laterais.append(tex[V[ok], U[ok], :3].astype(float))
        media = np.concatenate(cores_laterais).mean(0) if cores_laterais else medias_parte[c.nome]
        for face in ("up", "down"):
            r = texels_da_face(c, face, m)
            if r is None:
                continue
            uv, _ = r
            U, V = uv[:, 0] % larg, uv[:, 1] % alt
            if _espessura_zero(c) is not None:
                tex[V, U, :3] = media.astype(np.uint8)
                tex[V, U, 3] = 255 if _espessura_zero(c) == 1 else tex[V, U, 3]
            else:
                tex[V, U, :3] = media.astype(np.uint8)
                tex[V, U, 3] = 255
            conhecido[V, U] = True

    # buracos: vizinho mais próximo dentro da ilha; o que sobrar, cor da parte
    regiao = regiao_volume | regiao_plano
    stats["preenchidos"] = int((regiao & ~conhecido).sum())
    falta = _preencher(tex, conhecido, regiao)
    if falta.any():
        for (uu, vv), (nome, _) in face_de.items():
            if falta[vv, uu]:
                tex[vv, uu, :3] = medias_parte.get(nome, np.array([160, 160, 170])).astype(np.uint8)
    tex[regiao_volume, 3] = 255
    stats["transparentes_volume"] = int((regiao_volume & (tex[..., 3] == 0)).sum())
    return {"textura": tex, "face_de": face_de, "regiao_volume": regiao_volume, "amostrado": amostrado,
            "stats": stats, "pontos_cubo": pontos_cubo}


def _aceitos_espelho(modelo, cubo, indice, filhos_adesivo):
    """Para a face +X: quem aparece no lado esquerdo no lugar espelhado (o próprio cubo central ou o par _left)."""
    nome = cubo.nome
    par = nome.replace("_right", "_left") if "_right" in nome else nome
    aceitos = {indice.get(par, indice[nome])} | filhos_adesivo.get(par, set()) | filhos_adesivo.get(nome, set())
    return aceitos


def sombrear_e_quantizar(tex: np.ndarray, face_de: dict, modelo: bbmodelo.Modelo, n_base: int = 5, n_destaque: int = 2) -> dict:
    """Paleta + rampas + sombreado pintado + AO simples + limpeza. Altera `tex` e devolve a paleta."""
    opaco = tex[..., 3] > 0
    if not opaco.any():
        return {"paleta": [], "papeis": []}
    pal, papeis = cores.paleta(tex[opaco, :3], n_base, n_destaque)
    indices = np.full(tex.shape[:2], -1, int)
    indices[opaco] = cores.mais_proxima(tex[opaco, :3], pal)

    # limpeza: texel cujos 4 vizinhos da mesma face concordam numa outra cor vira essa cor
    alt, larg = indices.shape
    novo = indices.copy()
    for (uu, vv), chave in face_de.items():
        if indices[vv, uu] < 0:
            continue
        viz = [indices[vv + dy, uu + dx] for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))
               if 0 <= vv + dy < alt and 0 <= uu + dx < larg and face_de.get((uu + dx, vv + dy)) == chave]
        if len(viz) >= 3 and len(set(viz)) == 1 and viz[0] != indices[vv, uu] and viz[0] >= 0:
            novo[vv, uu] = viz[0]
    indices = novo

    # sombreado: topo +1, base -1; AO: texel lateral cujo ponto, meio passo para fora, cai dentro de outro cubo
    mats = bbmodelo.matrizes_ossos(modelo)
    caixas = [(c.nome, *bbmodelo.caixa_mundo(modelo, c, mats)) for c in modelo.cubos if _espessura_zero(c) is None]
    nivel = np.zeros(tex.shape[:2], int)
    pontos_face = {}
    for c in modelo.cubos:
        if c.mirror_uv:
            continue
        m = bbmodelo.matriz_cubo(modelo, c, mats)
        for face in render.CANTOS_FACE:
            r = texels_da_face(c, face, m)
            if r is None:
                continue
            uv, pontos = r
            U, V = uv[:, 0] % larg, uv[:, 1] % alt
            n = _normal(face, m)
            if n[1] > 0.7:
                nivel[V, U] = 1
            elif n[1] < -0.7:
                nivel[V, U] = -1
            if _espessura_zero(c) is None and abs(n[1]) < 0.7:
                fora = pontos + n * 0.5
                ao = np.zeros(len(pontos), bool)
                for nome, lo, hi in caixas:
                    if nome == c.nome:
                        continue
                    ao |= np.all((fora > lo + 1e-6) & (fora < hi - 1e-6), axis=1)
                nivel[V[ao], U[ao]] = -1
            pontos_face[(c.nome, face)] = (U, V)
    rampas = [cores.rampa(p) for p in pal]
    for i, rp in enumerate(rampas):
        for k, cor in rp.items():
            sel = (indices == i) & (nivel == k)
            tex[sel, :3] = cor
    return {"paleta": [cores.para_hex(p) for p in pal], "papeis": papeis, "indices": indices}


def versao_roblox(tex: np.ndarray, fator: int = ROBLOX_FATOR, margem: int = ROBLOX_MARGEM) -> np.ndarray:
    """Amplia por vizinho mais próximo e espalha a cor de cada ilha por `margem` px (sem mexer no alfa das ilhas)."""
    grande = np.repeat(np.repeat(tex, fator, 0), fator, 1).copy()
    ocupado = grande[..., 3] > 0
    for _ in range(margem):
        vizinho = np.zeros_like(ocupado)
        soma = np.zeros(grande.shape[:2] + (3,), float)
        n = np.zeros(grande.shape[:2], float)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            v = np.roll(np.roll(ocupado, dy, 0), dx, 1)
            c = np.roll(np.roll(grande[..., :3].astype(float), dy, 0), dx, 1)
            m = ~ocupado & v
            soma[m] += c[m]
            n[m] += 1
            vizinho |= m
        grande[vizinho, :3] = (soma[vizinho] / n[vizinho, None]).astype(np.uint8)
        grande[vizinho, 3] = 0  # margem: cor da ilha, transparente (só evita a borda escura no filtro)
        ocupado |= vizinho
    return grande


def conferir(modelo: bbmodelo.Modelo, tex: np.ndarray, regiao_volume: np.ndarray, vistas: dict[str, Vista],
             paleta: dict, amostrado: np.ndarray | None = None, n_base: int = 5, n_destaque: int = 2) -> tuple[list, list, dict]:
    """Aceite da Fase 5: sem buraco transparente em volume, nº de cores no limite, ΔE da cor de cada parte ≤ 10."""
    erros, avisos, resumo = [], [], {}
    buracos = int((regiao_volume & (tex[..., 3] == 0)).sum())
    if buracos:
        erros.append(msg("buraco", f"{buracos} texels transparentes em faces de volume"))
    n_cores = len(paleta.get("paleta", []))
    resumo["cores"] = n_cores
    if n_cores > n_base + n_destaque:
        erros.append(msg("cores", f"{n_cores} cores (limite {n_base} + {n_destaque})"))
    # ΔE: cor média da face da frente na textura × cor média da parte no conceito (onde ela aparece)
    frente = vistas.get("frente")
    if frente is not None:
        mats = bbmodelo.matrizes_ossos(modelo)
        indice = {c.nome: i for i, c in enumerate(modelo.cubos)}
        des = {}
        larg, alt = modelo.resolucao
        adesivos = {}
        for c in modelo.cubos:
            osso = modelo.ossos.get(c.osso)
            if _espessura_zero(c) is not None and c.nome.startswith(ADESIVOS_ROSTO) and osso and osso.pai:
                adesivos.setdefault(f"{osso.pai}_cube", []).append(indice[c.nome])
        for c in modelo.cubos:
            if c.mirror_uv:
                continue
            # mesmo conjunto de pixels que a pintura usou: o cubo e os adesivos dele (o olho está na face da cabeça)
            visivel = np.isin(frente.ids, [indice[c.nome]] + adesivos.get(c.nome, []))
            if visivel.sum() < 20:
                continue
            # mediana: a região da parte vem do modelo e pega uns pixels do vizinho na borda (olho de 1 unidade)
            conceito = np.median(frente.rgb[visivel].astype(float), axis=0)
            r = texels_da_face(c, "north", bbmodelo.matriz_cubo(modelo, c, mats))
            if r is None:
                continue
            uv, _ = r
            U, V = uv[:, 0] % larg, uv[:, 1] % alt
            ok = tex[V, U, 3] > 0
            if amostrado is not None and (ok & amostrado[V, U]).any():
                ok &= amostrado[V, U]  # só o que aparece (o topo da frente do corpo fica atrás da cabeça)
            if not ok.any():
                continue
            feito = np.median(tex[V[ok], U[ok], :3].astype(float), axis=0)
            des[c.nome.removesuffix("_cube")] = round(cores.delta_e(feito, conceito), 1)
        resumo["delta_e"] = des
        ruins = {k: v for k, v in des.items() if v > DELTA_E_MAX}
        if ruins:
            avisos.append(msg("delta_e", "ΔE acima de 10: " + ", ".join(f"{k} {v}" for k, v in ruins.items())))
    return erros, avisos, resumo


def carregar_vistas(modelo: bbmodelo.Modelo, preparo: Path, medidas: dict) -> dict[str, Vista]:
    vistas = {}
    for nome, mapa in medidas.get("mapeamento", {}).items():
        arq = preparo / f"{nome}-recorte.png"
        if not arq.exists():
            continue
        im = Image.open(arq)
        proj = projecao_da_vista(nome, mapa, medidas["unidades_por_celula"], im.size)
        _, _, ids, _ = render.renderizar(modelo, projecao=proj, usar_textura=False)
        vistas[nome] = Vista(nome, im, proj, ids)
    return vistas


def _data_url(tex: np.ndarray) -> str:
    buf = io.BytesIO()
    Image.fromarray(tex, "RGBA").save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def aplicar_no_modelo(arquivo: Path, tex: np.ndarray, modelo: bbmodelo.Modelo, remover: list[str]) -> None:
    """Embute a textura no .bbmodel pelo motor (cria ou troca) e a atribui a todos os cubos."""
    alt, larg = tex.shape[:2]
    ja_tem = bool(modelo.bruto.get("textures"))
    op_tex = ({"op": "update_texture", "target": 0, "source": _data_url(tex), "width": larg, "height": alt} if ja_tem
              else {"op": "add_texture", "name": "textura", "source": _data_url(tex), "width": larg, "height": alt})
    lote = [op_tex] + [{"op": "remove_node", "target": n} for n in remover]
    restantes = [c.nome for c in modelo.cubos if c.nome not in remover]
    lote.append({"op": "assign_texture", "targets": restantes, "texture": 0 if ja_tem else "textura"})
    motor.editar(arquivo, lote)


def texturizar(arquivo: Path, preparo: Path, medidas: dict, cores_parte: dict[str, str], olho_pintado: bool = False) -> dict:
    modelo = bbmodelo.ler(arquivo)
    vistas = carregar_vistas(modelo, preparo, medidas)
    if "frente" not in vistas:
        raise ValueError("texturizar precisa da vista de frente e do mapeamento do medir")
    pintura = pintar(modelo, vistas, cores_parte, olho_pintado)
    paleta = sombrear_e_quantizar(pintura["textura"], pintura["face_de"], modelo)
    erros, avisos, resumo = conferir(modelo, pintura["textura"], pintura["regiao_volume"], vistas, paleta, pintura["amostrado"])
    remover = [c.nome for c in modelo.cubos if olho_pintado and c.nome.startswith(("eye_", "pupil_", "eyelid_"))]
    if "costas" not in vistas:
        avisos.append(msg("sem_costas", "sem vista de trás: as costas foram preenchidas pela cor das bordas"))
    return {"textura": pintura["textura"], "paleta": paleta, "erros": erros, "avisos": avisos,
            "resumo": {**resumo, **pintura["stats"]}, "remover": remover, "modelo": modelo}


@etapa("texturizar")
def cmd_texturizar(args) -> int:
    pasta = Path(args.pasta)
    nome = pasta.resolve().name
    ctx = contexto(nome, args.estagio)
    destino = ctx["destino"]
    arquivo = modelo_atual(destino, ctx["relatorio"])
    if arquivo is None or not (destino / "medidas.json").exists():
        print("texturizar: falta o .bbmodel ou o medidas.json (rode medir e cubificar)")
        return 1
    hashes = ctx["relatorio"].get("hashes", {})
    if hashes.get(arquivo.name) and hashes[arquivo.name] != sha256(arquivo):
        print(f"texturizar: {arquivo.name} foi editado à mão; rode cubificar (ele grava uma versão nova) antes")
        return 1
    medidas = relatorio.ler_json(destino / "medidas.json")
    plano = relatorio.ler_json(destino / "plano-cubos.json") if (destino / "plano-cubos.json").exists() else {"cubos": []}
    cores_parte = {c["nome"]: c["cor"] for c in plano["cubos"] if c.get("cor")}
    try:
        r = texturizar(arquivo, destino / "preparo", medidas, cores_parte, args.olho_pintado)
        Image.fromarray(r["textura"], "RGBA").save(destino / "textura.png")
        Image.fromarray(versao_roblox(r["textura"]), "RGBA").save(destino / "textura-roblox.png")
        aplicar_no_modelo(arquivo, r["textura"], r["modelo"], r["remover"])
    except (ValueError, motor.MotorErro) as e:
        relatorio.registrar(destino, nome, args.estagio, "texturizar", False, erros=[msg("texturizar", str(e))])
        print(f"texturizar: {e}")
        return 1
    ok = not r["erros"]
    relatorio.registrar(destino, nome, args.estagio, "texturizar", ok, erros=r["erros"], avisos=r["avisos"],
                        arquivos=[relativo(destino / "textura.png"), relativo(destino / "textura-roblox.png")],
                        resumo={**r["resumo"], "paleta": r["paleta"]["paleta"]}, hashes={arquivo.name: sha256(arquivo)})
    pal = r["paleta"]
    linhas = [f"texturizar {arquivo.name}: {len(pal['paleta'])} cores "
              f"({pal['papeis'].count('base')} base, {pal['papeis'].count('destaque')} destaque): {' '.join(pal['paleta'])}",
              f"  texels amostrados {r['resumo']['amostrados']}, preenchidos {r['resumo']['preenchidos']}"]
    if r["resumo"].get("delta_e"):
        pior = max(r["resumo"]["delta_e"].items(), key=lambda kv: kv[1])
        linhas.append(f"  ΔE por parte: pior {pior[0]} {pior[1]} (limite {DELTA_E_MAX:g})")
    if r["remover"]:
        linhas.append(f"  olho pintado: removidos {', '.join(r['remover'])}")
    linhas += relatorio.linhas_mensagens("Erros", r["erros"])
    linhas += relatorio.linhas_mensagens("Avisos", r["avisos"])
    linhas.append(f"  gravado: {relativo(destino / 'textura.png')}, textura-roblox.png e a textura embutida no .bbmodel")
    relatorio.imprimir(linhas)
    return 0 if ok else 1
