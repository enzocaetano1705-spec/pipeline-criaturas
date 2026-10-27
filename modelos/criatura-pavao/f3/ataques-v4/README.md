# F3 — amplitude do Low e anatomia do Cross

Revisão das três imagens anotadas em `referencias/`, em uma cópia nova da
v3. Modelo editável: `criatura-pavao-e3-ataques-v4.bbmodel`.

- **Low (1,65 s):** varredura de aproximadamente 166° no espaço global,
  com giro adicional do tronco e pivô nos apoios. A espada prolonga o
  antebraço durante o corte. O braço esquerdo permanece junto à guarda
  aprovada, fora da trajetória do direito.
- **Cross (2,40 s):** primeira fatiada diagonal ascendente, conduzida pelo
  ombro com cotovelo externo e espada alinhada ao antebraço. O trecho ativo
  direito dura cerca de três vezes o da v3. Na recuperação o cotovelo
  recolhe, e as penas abrem para fora mantendo a raiz presa. A segunda
  fatiada inclina 15° para a direita da criatura, formando a diagonal oposta.
  Essa mudança substitui, a pedido do usuário, a descida vertical antes aprovada.

Geometria, hierarquia, UVs e atlas preservados: 93 cubos, 41 grupos e os
outros 19 clipes. Os dois ataques começam e terminam na guarda aprovada.
Spin permanece adiado na v1. Nenhuma mudança no Studio ou na lógica de pet.

## Conferência

`validacao-ataques.json` registra o arquivo salvo com interpolação linear
e semântica numérica nativa, 240 Hz e duas fases de amostragem. Verifica
empunhadura, articulações, âncoras das penas, continuidade angular, apoios,
piso, separação dos braços, eixo da espada e fio no plano do corte.

O teste novo de superfície opaca das penas contra peito/pescoço desconta
somente a sobreposição já existente na guarda aprovada. `regressao-v3.json`
mostra que esse teste detecta a falha relatada na versão anterior; é um
registro de falha esperada da fonte, não da v4. O exame da v4 usa 60 Hz.
As sondagens não substituem hitboxes do jogo nem uma avaliação anatômica humana.

No arquivo final: desvio antebraço/espada <0,004°, fio até 5,31° e folga
entre cápsulas dos braços >1,95 unidades Low / >4,82 Cross. Nas amostras
não houve penetração nova das penas nos volumes principais do peito/pescoço
nem das lâminas no corpo. O teste de regressão acusa 2,90 unidades na v3.

O proxy legado de punho, baseado no repouso mantídeo, fica registrado como
diagnóstico. O aceite usa o eixo geométrico pedido, preensão e movimento
articular; não interpreta aquele proxy como amplitude clínica do punho.

`validacao-motor.json` contém a conferência independente de estrutura e
dos dois clipes a 120 Hz. `attack_low.gif`, `attack_cross.gif` (frontal) e
`attack_cross-3q.gif` foram capturados no Blockbench, com câmera fixa por
clipe. `poses-nativas.png` reúne nove poses. Parâmetros e hash da captura
ficam em `previas-nativas.json`. A avaliação artística continua com o usuário.
Foram capturados 50/72/72 quadros. Ao descartar a vista, o plugin emite um
erro conhecido do listener `onContextMenu` depois de remover o registro;
o helper trata esse caso e a lista de vistas confirmou a limpeza.

## Reprodução

Na raiz do repositório:

```powershell
uv run python scripts/animar-golpes-pavao-f3-v4.py --gerar --validar
```

`--clipes attack_cross` atualiza só o Cross após a geração completa.
`--nativo` exige esta versão aberta e captura as prévias. A escrita usa o
motor externo em lotes, com proteção por hash contra edições manuais e
decimais explícitos nas chaves. As fontes anteriores permanecem intactas.
