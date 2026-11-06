# Animações v1 — locomoção da preguiça rogue (06/11/2026)

Atual: **r03/fera-sombras-e3-animacoes.bbmodel** (textura e geometria da `textura-v4/r03`, aprovada).

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
| `run` | 0,62 s | sim | galope pesado: patas da frente juntas e depois as de trás, coluna encolhe/estica, quique forte, gordura sacudindo, cabeça firme, cauda de contrapeso e cachecol em onda |
| `run_start` | 0,5 s | não | recua, recolhe as garras com estalo e mergulha para os quatro apoios |
| `run_stop` | 0,7 s | não | derrapa nos nós das mãos, passa do ponto, assenta e abre as garras |

Peso sem escala (o Roblox não anima escala de osso): tronco e pescoço seguem o corpo por molas
amortecidas (atrasam e passam do ponto), cauda e cachecol em onda da base para a ponta. Mãos e pés
pisam no chão por IK. Validação do motor: 0 erros, 0 avisos (nada afunda, nada se solta). As
posições das juntas foram conferidas contra o motor do Blockbench (`bbmodel_sample_pose`).

`animacoes.json`: duração/loop e velocidade de deslocamento (walk 0,47 bloco/s; run 2,67 blocos/s)
para o jogo mover o modelo sem os pés patinarem. Prévias: `previa-<clipe>.gif` (lado e 3/4) e
`tiras.png` (8 quadros por clipe).

```powershell
uv run python scripts/fera-animacao/gerar.py modelos/fera-fera-agil-das-sombras/malha-v1/animacoes-v1/base-rig.bbmodel modelos/fera-fera-agil-das-sombras/malha-v1/animacoes-v1/r04
```
Parâmetros de cada marcha (duração, curso, altura do quique, gordura, cauda, cachecol) ficam em
`scripts/fera-animacao/clips.py` (`walk()`, `run()`, `pose_idle()`).

## Próximo (na ordem combinada)
Postura de combate e ataque básico; depois as habilidades. Habilidade 1 (decidida com o usuário):
uma garra arremessada ricocheteia marcando os inimigos da onda, volta para a mão e então a preguiça
teleporta e dá um golpe curto em cada marcado. Habilidade 2: sequência focada no chefe.
