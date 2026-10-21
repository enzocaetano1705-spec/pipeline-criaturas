"""`criaturas validar <pasta> --estagio eN`: bbmodel_validate do motor + verificações próprias.

Próprias:
- tamanhos inteiros (planos e adesivos podem ter um eixo 0) e simetria esquerda/direita;
- orçamento de cubos do estágio;
- todas as partes da leitura presentes como ossos;
- fração de cabeça do modelo comparada com a da imagem (não com a tabela).
Grava validacao.json e a etapa no relatório. Erro do motor ou próprio -> código 1.
"""

from pathlib import Path

import numpy as np

from criaturas import bbmodelo, motor, relatorio
from criaturas.caminhos import relativo
from criaturas.cubificar import contexto
from criaturas.etapas import etapa
from criaturas.relatorio import msg

TOLERANCIA_CABECA = 0.10
CELULAS = 32


def modelo_atual(destino: Path, rel: dict) -> Path | None:
    """O .bbmodel que o último cubificar gravou."""
    nome = rel.get("etapas", {}).get("cubificar", {}).get("resumo", {}).get("arquivo")
    if nome and (destino / nome).exists():
        return destino / nome
    candidatos = sorted(destino.glob("*.bbmodel"), key=lambda p: p.stat().st_mtime)
    return candidatos[-1] if candidatos else None


def verificacoes_proprias(modelo: bbmodelo.Modelo, leitura: dict | None, plano: dict | None) -> tuple[list, list, dict]:
    erros, avisos, resumo = [], [], {}
    por_nome = {c.nome: c for c in modelo.cubos}
    for c in modelo.cubos:
        tam = c.ate - c.de
        nao_inteiro = [i for i in range(3) if tam[i] > 1e-6 and abs(tam[i] - round(tam[i])) > 1e-6]
        if nao_inteiro:
            erros.append(msg("tamanho_inteiro", f"{c.nome}: tamanho {tam.round(3).tolist()} não é inteiro", c.nome))
        if "_left" in c.nome:
            par = por_nome.get(c.nome.replace("_left", "_right"))
            if par is None:
                erros.append(msg("simetria", f"{c.nome}: sem o par _right", c.nome))
            elif not (np.allclose(par.de[1:], c.de[1:]) and np.allclose(par.ate[1:], c.ate[1:])
                      and np.isclose(par.de[0], -c.ate[0]) and np.isclose(par.ate[0], -c.de[0])):
                erros.append(msg("simetria", f"{c.nome} e {par.nome} não são espelho um do outro", c.nome))
    if plano and plano.get("orcamento"):
        o = plano["orcamento"]
        resumo["orcamento"] = o
        if len(modelo.cubos) > o["limite"]:
            avisos.append(msg("orcamento", f"{len(modelo.cubos)} cubos passa do limite {o['limite']}"))
    if leitura:
        faltam = [p["id"] for p in leitura["partes"] if p["id"] not in modelo.ossos]
        if faltam:
            erros.append(msg("parte_faltando", "partes da leitura sem osso: " + ", ".join(faltam)))
        # cabeça do modelo × cabeça da imagem (frente), ambas como fração da altura
        cab = next((p for p in leitura["partes"] if p["id"] == "head" and "frente" in p["caixas"]), None)
        if cab and "head_cube" in por_nome:
            lo, hi = bbmodelo.limites(modelo)
            altura = hi[1] - lo[1]
            hc = por_nome["head_cube"]
            frac_modelo = float((hc.ate[1] - hc.de[1]) / altura)
            y0, y1 = cab["caixas"]["frente"][1], cab["caixas"]["frente"][3]
            frac_imagem = (y1 - y0) / CELULAS
            resumo["cabeca"] = {"modelo": round(frac_modelo, 3), "imagem": round(frac_imagem, 3)}
            if frac_imagem > 0 and abs(frac_modelo - frac_imagem) / frac_imagem > TOLERANCIA_CABECA:
                avisos.append(msg("cabeca", f"cabeça {frac_modelo:.0%} da altura no modelo e {frac_imagem:.0%} na imagem"))
    return erros, avisos, resumo


def validar(arquivo: Path, leitura: dict | None = None, plano: dict | None = None) -> dict:
    res_motor = motor.validar(arquivo)
    e_motor, a_motor, mensagens = motor.resumo_validacao(res_motor)
    modelo = bbmodelo.ler(arquivo)
    erros, avisos, resumo = verificacoes_proprias(modelo, leitura, plano)
    erros = [msg("motor", m) for m in mensagens if m.startswith("[error]")] + erros
    avisos = [msg("motor", m) for m in mensagens if not m.startswith("[error]")] + avisos
    return {"arquivo": arquivo.name, "motor": {"erros": e_motor, "avisos": a_motor}, "cubos": len(modelo.cubos),
            "ossos": len(modelo.ossos), "erros": erros, "avisos": avisos, "resumo": resumo,
            "ok": e_motor == 0 and not erros}


@etapa("validar")
def cmd_validar(args) -> int:
    pasta = Path(args.pasta)
    nome = pasta.resolve().name
    ctx = contexto(nome, args.estagio)
    destino = ctx["destino"]
    arquivo = modelo_atual(destino, ctx["relatorio"])
    if arquivo is None:
        print("validar: nenhum .bbmodel (rode cubificar antes)")
        return 1
    leitura = relatorio.ler_json(destino / "leitura.json") if (destino / "leitura.json").exists() else None
    plano = relatorio.ler_json(destino / "plano-cubos.json") if (destino / "plano-cubos.json").exists() else None
    try:
        r = validar(arquivo, leitura, plano)
    except motor.MotorErro as e:
        print(f"validar: {e}")
        return 1
    caminho = relatorio.gravar_json(destino / "validacao.json", r)
    relatorio.registrar(destino, nome, args.estagio, "validar", r["ok"], erros=r["erros"], avisos=r["avisos"],
                        arquivos=[relativo(caminho)], resumo={"motor": r["motor"], **r["resumo"]})
    linhas = [f"validar {arquivo.name}: {'OK' if r['ok'] else 'COM ERROS'} — motor {r['motor']['erros']} erros, "
              f"{r['motor']['avisos']} avisos; {r['cubos']} cubos, {r['ossos']} ossos"]
    if "cabeca" in r["resumo"]:
        c = r["resumo"]["cabeca"]
        linhas.append(f"  cabeça: {c['modelo']:.0%} da altura no modelo, {c['imagem']:.0%} na imagem")
    linhas += relatorio.linhas_mensagens("Erros", r["erros"])
    linhas += relatorio.linhas_mensagens("Avisos (explique os que ficarem)", r["avisos"])
    relatorio.imprimir(linhas)
    return 0 if r["ok"] else 1
