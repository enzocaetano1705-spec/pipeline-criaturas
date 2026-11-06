# Animações v1 — locomoção da preguiça rogue (06/11/2026)

Atual: **r05/fera-sombras-e3-animacoes.bbmodel** (base `rig-v3/base-rig-v3.bbmodel`).

**r05 (run refeito):** retorno "o walk ficou bom; no run a frente parece fazer 2 ciclos e a traseira 1,
balança demais, não parece galope, a cauda mexe estranho e partes se desconectam". Medido na r04:
quique do corpo, deslocamento do tronco e cachecol batiam 2× por passada e a mola da gordura tremia na
própria frequência; o tronco transladava 2,8 unidades (abria fresta) e girava 16°, a cauda 20°.
Agora o run é um galope rotativo (trás esq., trás dir., frente dir., frente esq., voo recolhido) de
0,66 s em que tudo que balança está travado na fase da passada (`medir.py`: todos os canais do corpo
com 1 ciclo por passada), só o `body` translada, coluna estica/encolhe uma vez, gordura = mesmo
balanço com fase atrasada, cauda e cachecol em onda uma vez por passada, elevação da cauda fixa
(sem correção quadro a quadro). Nenhuma fresta nas juntas; pernas e braços a no mínimo 3,4 de
distância (nenhum quadro encosta); 0 erros, 0 avisos. Walk igual à r04.

**r04:** o usuário recuou as pernas no Blockbench (coxa +10 em Z, canela e pé +9) porque nas
animações elas entravam nos braços. `scripts/fera-animacao/pernas_recuadas.py` levou essa edição para
o rig movendo também os pivôs (quadril, joelho e tornozelo andam com os seus cubos; geometria em
`edicao-pernas.json`). O plano de pelo do quadril tinha um tufo que encostava na coxa e ficou boiando:
`limpar_ilhas.py` tirou (36 texels). A passada agora mede as patas de trás a partir do tornozelo de
repouso. Medido: antes as pernas encostavam nos braços em 25/25 quadros do walk e 7/10 do run; agora
a menor distância é 3,2 e nenhum quadro encosta. Validação: 0 erros, 0 avisos. O marcador
`loc_ground`, que tinha ido junto na seleção (+11 em Z, atrás dos pés), ficou no lugar original.

r03 (anterior) usava a geometria da `textura-v4/r03`.

Ideia do usuário: preguiça-gigante pesada, com camada de gordura, mas muito veloz. Andando e correndo
vira quadrúpede apoiada nos nós das mãos, com as garras dobradas para dentro (como tamanduás e
preguiças-gigantes faziam), e o corpo todo balança.

## Preparo do rig (só pivôs e ossos; geometria/UV/textura iguais, conferido)
- `base-garras.bbmodel`: 6 ossos novos `claw_<lado>_<1..3>`, pivô na base de cada garra.
- `base-rig.bbmodel`: pivôs de `shin_*` e `foot_*` movidos para onde estão os cubos que o usuário
  recuou (joelho no topo da canela, tornozelo na base dela, na altura do pé). Sem isso o pé girava
  em torno de um ponto 3 unidades à frente e se soltava da canela.

## Clipes (chaves assadas a 30/s, sem Molang; `root` não é animado)
| clipe | duração | loop | o que faz |
|---|---|---|---|
| `idle` | 4,0 s | sim | de pé, curvada, lenta: respira, olha devagar para um lado e para o outro, espreguiça as garras |
| `walk` | 1,6 s | sim | quatro apoios em sequência lateral, nos nós das mãos, garras dobradas; peso passando de lado a lado, barriga atrasada |
| `run` | 0,66 s | sim | galope rotativo (trás esq., trás dir., frente dir., frente esq., voo recolhido), tudo no ritmo da passada: coluna estica/encolhe uma vez, gordura no mesmo balanço com atraso, cabeça firme, cauda e cachecol em onda |
| `run_start` | 0,5 s | não | recua, recolhe as garras com estalo e mergulha para os quatro apoios |
| `run_stop` | 0,7 s | não | derrapa nos nós das mãos, passa do ponto, assenta e abre as garras |

Peso sem escala (o Roblox não anima escala de osso): no walk, tronco e pescoço seguem o corpo por
molas amortecidas (atrasam e passam do ponto); no run não há mola solta (ela tremia no próprio ritmo
e brigava com a passada): a gordura é o mesmo balanço do corpo com a fase atrasada. Cauda e cachecol
em onda da base para a ponta. Mãos e pés pisam no chão por IK. Validação do motor: 0 erros, 0 avisos (nada afunda, nada se solta). As
posições das juntas foram conferidas contra o motor do Blockbench (`bbmodel_sample_pose`).

`animacoes.json`: duração/loop e velocidade de deslocamento (walk 0,47 bloco/s; run 2,84 blocos/s)
para o jogo mover o modelo sem os pés patinarem. Prévias: `previa-<clipe>.gif` (lado e 3/4) e
`tiras.png` (8 quadros por clipe).

```powershell
uv run python scripts/fera-animacao/gerar.py modelos/fera-fera-agil-das-sombras/malha-v1/animacoes-v1/rig-v3/base-rig-v3.bbmodel modelos/fera-fera-agil-das-sombras/malha-v1/animacoes-v1/r05
uv run python scripts/fera-animacao/medir.py modelos/fera-fera-agil-das-sombras/malha-v1/animacoes-v1/rig-v3/base-rig-v3.bbmodel run
```
`medir.py` diz quantos ciclos por passada cada canal faz (tudo deve dar 1 no run), quais ossos
transladam, as frestas nas juntas e a menor distância entre pernas e braços.
Parâmetros de cada marcha (duração, curso, altura do quique, gordura, cauda, cachecol) ficam em
`scripts/fera-animacao/clips.py` (`walk()`, `run()`, `pose_idle()`).

## Próximo (na ordem combinada)
Postura de combate e ataque básico; depois as habilidades. Habilidade 1 (decidida com o usuário):
uma garra arremessada ricocheteia marcando os inimigos da onda, volta para a mão e então a preguiça
teleporta e dá um golpe curto em cada marcado. Habilidade 2: sequência focada no chefe.
