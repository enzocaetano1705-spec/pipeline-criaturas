"""`criaturas rig <pasta> --estagio eN`: recalcula os locators padrão pelos cubos atuais (item 6.1)."""

from pathlib import Path

from criaturas import motor, relatorio
from criaturas.caminhos import relativo
from criaturas.cubificar import contexto, sha256
from criaturas.etapas import etapa
from criaturas.relatorio import msg
from criaturas.rig import sincronizar
from criaturas.validar import modelo_atual


@etapa("rig")
def cmd_rig(args) -> int:
    pasta = Path(args.pasta)
    nome = pasta.resolve().name
    ctx = contexto(nome, args.estagio)
    destino = ctx["destino"]
    arquivo = modelo_atual(destino, ctx["relatorio"])
    if arquivo is None:
        print("rig: nenhum .bbmodel (rode cubificar antes)")
        return 1
    hashes = ctx["relatorio"].get("hashes", {})
    if hashes.get(arquivo.name) and hashes[arquivo.name] != sha256(arquivo):
        print(f"rig: {arquivo.name} foi editado à mão; rode cubificar (ele grava uma versão nova) antes")
        return 1
    try:
        r = sincronizar(arquivo)
    except motor.MotorErro as e:
        print(f"rig: {e}")
        return 1
    avisos = [msg("locator_extra", f"{n}: não é padrão (mantido)") for n in r["extras"]]
    relatorio.registrar(destino, nome, args.estagio, "rig", True, avisos=avisos, arquivos=[relativo(arquivo)],
                        resumo=r, hashes={arquivo.name: sha256(arquivo)})
    relatorio.imprimir([f"rig {arquivo.name}: {len(r['locators'])} locators padrão "
                        f"({len(r['criados'])} criados, {len(r['trocados'])} reposicionados)",
                        "  " + ", ".join(r["locators"])] + relatorio.linhas_mensagens("Avisos", avisos))
    return 0

