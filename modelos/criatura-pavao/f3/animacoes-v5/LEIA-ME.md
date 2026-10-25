# F3 — respiração pesada e saque contínuo

Arquivo: `criatura-pavao-e3-combate-v5.bbmodel`.
Fonte preservada: `../animacoes-v4/criatura-pavao-e3-combate-v4.bbmodel`.
Somente `combat_ready` e `combat_enter` revistos. Os demais onze clipes,
incluindo `combat_walk`, mantêm exatamente os canais e tempos da fonte.

## Respiração da guarda

Mesmo loop de 2,4 s e mesma postura base, agora com mais peso:

- Corpo sobe/desce 1 unidade entre os extremos, antes 0,36.
- Inclinação do peito varia 5,6°, antes 1,8°.
- Cintura e pescoço acompanham; cabeça permanece parcialmente estabilizada.
- Cauda e plumagem respondem com leve atraso em relação ao peito.
- Solas e ponta da espada de descanso conservam apoio; roots das wings fixas.

O quadro zero continua igual à postura da marcha aprovada. Não muda o porte,
a geometria, o atlas nem a hierarquia da criatura.

## Saque sem a pausa intermediária

O novo trecho vai de 0,40 a 1,15 s. Retira a volta à guarda baixa e a pausa
antes de elevar o braço. A mão descreve um arco para fora e para cima até
a extensão aprovada, passando por um guia em 0,56 s sem zerar a velocidade.

Posição, orientação da espada e orientação preferida do ombro usam curvas
com velocidade contínua. Preservam as velocidades de entrada/saída da fonte.
Não há nova pausa no meio nem movimento de baixar a mão para depois subir.
O outro braço conserva o gesto de levar a espada ao arrasto.

Até 0,40 s e a partir de 1,15 s, o `combat_enter` mantém as poses aprovadas da v4.
Inclui o mesmo floreio de 360° em uma só espada, com inclinação de 30°, a descida
ao ombro e o final na guarda. Duração total mantida em 2,1 s.

## Reprodução e conferência

```powershell
uv run python scripts/animar-combate-pavao-f3-v5.py --animar --validar --previas --folha
```

Gravação pelo motor externo, em versão nova e protegida por hash. Conferência
das chaves salvas a 240 amostras/s: preservação dos clipes, geometria/UV/rig,
apoios, empunhadura, wings, cotovelos, punhos, orientação, loops, conexões,
velocidade sem pausa no arco e igualdade do trecho aprovado após a extensão.
Relatórios em `validacao.json` e `validacao-motor.json`.

Prévia da respiração e do saque nos GIFs; comparativos em `poses.png`.
Avaliação artística destes dois ajustes pendente. Demais clipes de transição,
camadas, descanso e saída permanecem adiados. Sem ações no Roblox Studio.
