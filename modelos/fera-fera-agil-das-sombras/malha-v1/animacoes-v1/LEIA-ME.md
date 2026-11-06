# Animações v1 — locomoção da preguiça rogue (06/11/2026)

Atual: **r08/fera-sombras-e3-animacoes.bbmodel** (base `rig-v4/base-rig-v4.bbmodel`).

**r08 (juntas da guarda):** retorno: "a ideia da postura ficou bem legal, mas a junta com as costas
está desconexa, o ombro parece invertido com relação ao cotovelo e a relação das coxas com as pernas
fica meio estranha nessa postura baixa". Causas vistas de perto:
- costas: o tronco dobrava 28° para a frente bem na emenda com a pelve (e torcia 10° ali); os blocos
  são rígidos, então abria uma fresta clara. Agora a coluna fica reta e a inclinação vem do corpo
  inteiro (empina 26°, torce 24°); repouso, idle e guarda ficam com a mesma emenda contínua.
- ombro e cotovelo, coxa e canela: a IK girava cada osso pelo caminho mínimo e deixava solto o giro em
  volta do próprio eixo; o joelho e o cotovelo dobravam fora do eixo do bloco. `pose.ik(...,
  charneira=True)` leva também o eixo da junta do repouso para o eixo novo: os dois ossos dobram em
  volta do mesmo eixo, como dobradiça (só no combate; walk e run aprovados seguem iguais). O
  cotovelo aponta para onde aponta no repouso, girado com o tronco.
- ombro: com o corpo empinado, o braço "neutro" do repouso aponta para a frente; levar a garra de trás
  para trás do quadril girava o bloco do braço (5×9×8) e a ponta de cima dele saía pelo ombro. A
  guarda agora tem as duas garras à frente: a da frente estendida e baixa, a de trás dobrada perto do
  peito, armada.
- coxa: base um pouco menos funda (agacha 3,0 em vez de 5,0) e joelho menos aberto; a coxa fica na
  diagonal em vez de deitada.
Conferido no Blockbench de trás, de cima, de lado e de 3/4. Validação: 0 erros, 0 avisos.

**r07 (piscada em todas as animações e postura de combate):** retorno sobre a r06: "uma animação só
para blink não faz sentido, deve piscar em todas as animações, inclusive as de combate"; "pode aplicar
a postura de tripé mas não pode ficar ridículo... precisa ser maneiro, igual o Greninja".
- Piscada dentro de cada clipe (`piscar_em` em `clips.py`, tempos em `PISCADA_POR_CLIPE` no
  `gerar.py`): lenta no idle (preguiça; fecha enquanto vira a cabeça), normal no walk, rápida no run,
  na antecipação de run_start, na derrapada de run_stop, na guarda, na entrada e na saída do combate.
  Para cada loop ter uma piscada só, num ritmo natural, o walk passou a ter 2 passadas (3,2 s) e o
  run 5 (3,3 s); a velocidade de deslocamento é a mesma. O clipe `blink` separado saiu.
- Postura de combate (`combate.py`): tripé de assassino, não urso em pé. O corpo empina 36° em volta
  do quadril e a cauda apoia no chão atrás com a ponta subindo pouco (erguida demais lembra esquilo);
  base baixa, larga e escalonada, joelhos bem dobrados, pé de trás na ponta (pronto para o bote);
  tronco curvado para a frente, corpo torcido 26° mostrando o ombro, cabeça baixa e firme no alvo;
  garra da frente baixa apontando para o alvo, garra de trás recolhida atrás do quadril com o cotovelo
  para baixo (para cima virava asa de frango). Respira pesado, a garra da frente se crispa e estala
  aberta uma vez por loop, ponta da cauda e cachecol não param.
- `combat_enter`: encolhe e fecha as garras (antecipação), pulinho, cai na base com as garras
  estalando abertas; o pulo esconde a troca de lugar dos pés. `combat_exit`: pulinho de volta para a
  base do idle. Nas duas, mão, garra e cauda nunca entram no chão.
- `gerar.py` tira chaves repetidas no meio de trechos parados (o arquivo não incha com as pálpebras
  escondidas). 15 538 chaves, 4,8 MB. Validação: 0 erros, 0 avisos.

**r06 (pés retos e piscada):** run aprovado ("agora ficou bem bom"). O usuário endireitou os pés no
Blockbench (rotação Y do cubo de ±35° para ±5°: os dedos apontavam para fora) e pediu uma piscada sem
escala para idle, walk e run.
- Pés: `trazer_edicao.py` leu a aba aberta (exportada sem salvar) e levou a rotação para o rig
  (`rig-v4/base-pes.bbmodel`, diferença em `rig-v4/edicao-pes.json`). Só o cubo gira em torno do
  próprio centro; o tornozelo continua onde está. Medido: nenhuma fresta, pernas × braços 3,0 no walk e
  3,4 no run (nenhum quadro encosta), 0 erros, 0 avisos.
- Piscada (`palpebras.py` → `rig-v4/base-rig-v4.bbmodel`): os olhos são pintados nas laterais do
  focinho (`head_2`). Cada olho ganhou duas tiras de pálpebra, cada uma no seu osso, escondidas 0,4
  atrás da face: `eyelid_<lado>` (pele por cima do olho e a borda escura da pálpebra) e
  `eyelid_<lado>_lower` (pele sobre o resto do olho). A piscada empurra os ossos para fora pela
  posição (0,46): só a de cima = meio fechado; as duas = fechado (a linha emenda na listra escura da
  cara). Mostradas, ficam 0,06 à frente da face, passam um pixel além do contorno do olho (pela
  fresta só aparece pele) e têm as bordas transparentes (sem filete pegando luz). A textura delas foi
  feita com os pixels do próprio olho (pele no lugar da íris) e foi para um canto livre do atlas (UV
  1,1 e 1,7): 128 pixels novos, nenhum pixel usado mudou. Conferido no Blockbench de quatro ângulos
  (`r06/previa-blink-blockbench.png`).
- Clipe `blink` (0,17 s: meio, fechado, fechado, meio, aberto) só mexe nas 4 pálpebras. É uma
  camada: o jogo toca por cima de idle, walk e run num intervalo aleatório de 2,5–6 s (anotado no
  `animacoes.json`). Embutir nos loops não serve: o run dura 0,66 s e piscaria 1,5 vez por segundo.
  `previa-blink.gif` mostra a piscada por cima dos três.
- `gerar.py` agora grava a trilha de posição inteira (com os zeros) de todo osso que translada em
  algum quadro; antes a chave zero do começo/fim era pulada e o Blockbench segurava o valor vizinho.

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

## Preparo do rig
- `base-garras.bbmodel`: 6 ossos novos `claw_<lado>_<1..3>`, pivô na base de cada garra.
- `base-rig.bbmodel`: pivôs de `shin_*` e `foot_*` movidos para onde estão os cubos que o usuário
  recuou (joelho no topo da canela, tornozelo na base dela, na altura do pé). Sem isso o pé girava
  em torno de um ponto 3 unidades à frente e se soltava da canela.
- `rig-v3/base-rig-v3.bbmodel`: pernas recuadas pelo usuário, com os pivôs (`pernas_recuadas.py`).
- `rig-v4/base-pes.bbmodel`: pés endireitados pelo usuário (`trazer_edicao.py`).
- `rig-v4/base-rig-v4.bbmodel`: + 4 ossos de pálpebra com as tiras e a textura delas (`palpebras.py`).

```powershell
uv run python scripts/fera-animacao/trazer_edicao.py <rig-v3>/base-rig-v3.bbmodel <aba-exportada>.bbmodel <rig-v4>/base-pes.bbmodel edicao-pes
uv run python scripts/fera-animacao/palpebras.py <rig-v4>/base-pes.bbmodel <rig-v4>/base-rig-v4.bbmodel
```
`trazer_edicao.py` serve para qualquer edição futura de cubos feita na aba aberta: compara pelo uuid,
copia from/to/origin/rotation, leva pivô mudado junto e recusa rotação de repouso em osso.

## Clipes (chaves assadas a 30/s, sem Molang; `root` não é animado)
| clipe | duração | loop | piscada | o que faz |
|---|---|---|---|---|
| `idle` | 4,0 s | sim | lenta, 2,6 s | de pé, curvada, lenta: respira, olha devagar para um lado e para o outro, espreguiça as garras |
| `walk` | 3,2 s | sim | normal, 1,9 s | 2 passadas de quatro apoios em sequência lateral, nos nós das mãos, garras dobradas; peso passando de lado a lado, barriga atrasada |
| `run` | 3,3 s | sim | rápida, 1,62 s | 5 passadas de galope rotativo (trás esq., trás dir., frente dir., frente esq., voo recolhido), tudo no ritmo da passada |
| `run_start` | 0,5 s | não | rápida, 0,06 s | recua, recolhe as garras com estalo e mergulha para os quatro apoios |
| `run_stop` | 0,7 s | não | normal, 0,12 s | derrapa nos nós das mãos, passa do ponto, assenta e abre as garras |
| `combat_ready` | 3,2 s | sim | normal, 0,9 s | guarda em tripé de lutador (r08); respira pesado, garra da frente se crispa e estala |
| `combat_enter` | 0,6 s | não | rápida, 0,04 s | idle → guarda: antecipação, pulinho, cai na base com as garras estalando |
| `combat_exit` | 0,7 s | não | normal, 0,3 s | guarda → idle: pulinho de volta e solta as garras |

Peso sem escala (o Roblox não anima escala de osso): no walk, tronco e pescoço seguem o corpo por
molas amortecidas (atrasam e passam do ponto); no run não há mola solta (ela tremia no próprio ritmo
e brigava com a passada): a gordura é o mesmo balanço do corpo com a fase atrasada. Cauda e cachecol
em onda da base para a ponta. Mãos e pés pisam no chão por IK. Validação do motor: 0 erros, 0 avisos (nada afunda, nada se solta). As
posições das juntas foram conferidas contra o motor do Blockbench (`bbmodel_sample_pose`).

`animacoes.json`: duração/loop e velocidade de deslocamento (walk 0,47 bloco/s; run 2,84 blocos/s)
para o jogo mover o modelo sem os pés patinarem, e quando cada clipe pisca. Prévias:
`previa-<clipe>.gif` (lado e 3/4), `previa-piscadas.gif` (close da cabeça na piscada de cada clipe) e
`tiras.png` (8 quadros por clipe).

```powershell
uv run python scripts/fera-animacao/gerar.py modelos/fera-fera-agil-das-sombras/malha-v1/animacoes-v1/rig-v4/base-rig-v4.bbmodel modelos/fera-fera-agil-das-sombras/malha-v1/animacoes-v1/r08
uv run python scripts/fera-animacao/medir.py modelos/fera-fera-agil-das-sombras/malha-v1/animacoes-v1/rig-v4/base-rig-v4.bbmodel run
```
`medir.py` diz quantos ciclos por passada cada canal faz (tudo deve dar 1 no run), quais ossos
transladam, as frestas nas juntas e a menor distância entre pernas e braços.
Parâmetros de cada marcha (duração, curso, altura do quique, gordura, cauda, cachecol) ficam em
`scripts/fera-animacao/clips.py` (`walk()`, `run()`, `pose_idle()`); os da guarda em
`scripts/fera-animacao/combate.py` (`GUARDA`: empinar, torcer, agachar, base, punhos e direção das
garras, cauda, olhar).

## Próximo (na ordem combinada)
Ataque básico saindo e voltando para a guarda; depois as habilidades. Habilidade 1 (decidida com o usuário):
uma garra arremessada ricocheteia marcando os inimigos da onda, volta para a mão e então a preguiça
teleporta e dá um golpe curto em cada marcado. Habilidade 2: sequência focada no chefe.
