# F3 — braço direito com tempo próprio

Arquivo: `criatura-pavao-e3-combate-v7.bbmodel`.
Fonte preservada: `../animacoes-v6/criatura-pavao-e3-combate-v6.bbmodel`.

O braço esquerdo da criatura mantém todas as chaves da v6: levantamento
rápido, floreio em 0,70–1,23 s e apoio no ombro até 1,65 s.
O direito completa o saque e baixa a espada em um gesto mais lento,
chegando à postura de arrasto em 1,65 s, junto do outro braço.

Somente os canais do braço, antebraço, mão direita e `tail_fan_06` na
`combat_enter` foram revistos. Os outros animadores, doze clipes, geometria,
textura, UVs e rig são preservados integralmente. As wings continuam presas
às suas raízes. Nenhum arquivo manual foi sobrescrito.

## Como foi feito

A trajetória direita anterior à aceleração conjunta serve de referência,
com tempo independente e desaceleração gradual. O torso atual recebe essa
trajetória, conservando a preensão e a flexão do cotovelo no eixo anatômico.
A compensação até o alvo de arrasto entra progressivamente, sem trocar
a espada de lugar em um quadro. A saída coincide com a `combat_ready`.

As chaves não uniformes do lado esquerdo ficam intactas. Chaves adicionais
do direito têm espaçamento de até 1/240 s; coincidências muito próximas
da grade com as chaves existentes são evitadas.

## Reprodução

```powershell
uv run python scripts/animar-combate-pavao-f3-v7.py --animar --validar --previas
```

`validacao.json`: conferência das chaves salvas a 240 amostras/s, preservação
exata do esquerdo e dos doze clipes, empunhadura, penas, chão, juntas,
floreio e conexões. `validacao-motor.json`: verificação pelo motor externo.
Prévia: `combat_enter.gif`. Avaliação artística do novo ritmo pendente.
