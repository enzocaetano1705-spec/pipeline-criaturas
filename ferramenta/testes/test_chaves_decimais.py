"""Regressão dos saltos de penas por expoentes interpretados como Molang."""
from decimal import Decimal

import pytest

from criaturas import motor


@pytest.mark.parametrize('value', [1e-8, -8.2e-7, '-6.5e-7', 1e20, 0, -0.0, 23.456789])
def test_chave_e_decimal_exato(value):
    out=motor._valor_chave(value)
    assert 'e' not in out.lower()
    assert Decimal(out)==Decimal(str(value))


def test_editar_normaliza_sem_mutar_operacoes(monkeypatch, tmp_path):
    received=[]
    monkeypatch.setattr(motor,'chamar',lambda tool,args,root: received.extend(args['operations']) or {})
    ops=[{'op':'set_keyframe','value':[1e-8,'math.sin(query.anim_time)',0]}]
    motor.editar(tmp_path/'x.bbmodel',ops,raiz=tmp_path)
    assert received[0]['value']==['0.00000001','math.sin(query.anim_time)','0']
    assert ops[0]['value'][0]==1e-8


@pytest.mark.parametrize('value',[float('nan'),float('inf')])
def test_chave_nao_finita_e_rejeitada(value):
    with pytest.raises(ValueError):motor._valor_chave(value)
