import json
import shutil

import pytest

from criaturas import cli, motor, sinteticos
from criaturas.caminhos import MODELOS

pytestmark = pytest.mark.skipif(not motor.disponivel(), reason="motor headless não instalado")


def test_tudo_para_sem_leitura_e_segue_com_ela(capsys):
    sinteticos.construir_todas()
    ficha = sinteticos.pasta_ficha("alado")
    alvo = MODELOS / ficha.name
    shutil.rmtree(alvo, ignore_errors=True)
    try:
        assert cli.main(["tudo", str(ficha)]) == 3
        assert "falta leitura.json" in capsys.readouterr().out
        info = json.loads((alvo / "e1" / "preparo" / "preparo.json").read_text(encoding="utf-8"))
        (alvo / "e1" / "leitura.json").write_text(json.dumps(sinteticos.leitura_da_verdade("alado", info, 1.0, 0)), encoding="utf-8")
        assert cli.main(["tudo", str(ficha), "--ate", "animar"]) == 0
        texto = capsys.readouterr().out
        assert len(texto.splitlines()) <= 20 and "animar" in texto
        rel = json.loads((alvo / "e1" / "relatorio.json").read_text(encoding="utf-8"))["etapas"]
        for etapa in ("preparar", "medir", "cubificar", "validar", "folha", "texturizar", "rig", "animar"):
            assert rel[etapa]["ok"], etapa
        assert "exportar" not in rel
    finally:
        shutil.rmtree(alvo, ignore_errors=True)
