# F2 — bote baixo v3

**Histórico rejeitado pelo usuário em 24/10.** Cauda e plumagem apresentaram problemas visuais
não capturados pelas verificações desta versão. Novo repertório e rig em `../ataque-v4/LEIA-ME.md`;
não adotar este bote no jogo. O restante descreve a entrega original.

Primeira etapa do repertório autorizado pelo usuário depois da discussão em
`docs/sessoes/2026-10-23-direcao-combate-f2.md`. Nova proposta artística, ainda em avaliação.

Abrir **criatura-pavao-e2-ataque-v3.bbmodel**, aba Animate, selecionar **attack_physical**
e tocar. Duração **1,20 s**, uma execução. `previa-bote.gif` repete o mesmo clipe a **1×**,
em 3/4 e perfil, com câmera/piso fixos e sem pausa extra inserida no GIF.

## Movimento

| Tempo aproximado | Ação |
|---|---|
| 0,00–0,12 s | Cabeça encontra o alvo baixo antes da preparação do tronco. |
| 0,12–0,28 s | Agachamento e compressão das duas pernas, com os pés apoiados. |
| 0,28–0,34 s | Impulso nos dedos e decolagem. |
| 0,34–0,57 s | Salto baixo, pernas recolhem sob a bacia e as duas patas avançam juntas. Penas abrem, cauda equilibra e pescoço recolhe para observar a região do contato. |
| 0,57–0,67 s | Patas descem sobre o alvo; mãos fecham perto do peito, com contato breve. |
| 0,67–0,80 s | Recolhimento das patas para aterrissar. |
| 0,80–0,96 s | Pouso e absorção nas pernas; cabeça e cauda recuperam. |
| 0,96–1,20 s | Acomodação das penas e retorno à pose de entrada. |

A coreografia é própria do F2 e usa a direção de predador com duas patas autorizada pelo usuário.
As referências e limites da analogia com aves de rapina/canguru permanecem na nota de direção.
Este bote não apoia o peso na cauda ou nas penas e não mantém a criatura presa a uma vítima.
A cabeça acompanha a ação; este clipe não força uma bicotada de DPS como etapa obrigatória.
A bicotada da v2 permanece como estudo aproveitável naquela versão.

As curvas de pose usam Hermite monótona, preservando velocidade em pontos intermediários de um
movimento contínuo. A IK mantém o plano de flexão original da perna e a família de dobra do joelho.
Usar só a rotação mais curta do quadril torcia a coxa na fase de recolhimento; o polo derivado do
plano original corrige essa orientação sem inverter o joelho. Curvas assadas em chaves a 120 Hz.

## Rig e preservação

- Fonte manual sem garras das mãos: **59 cubos**, uma textura 256×256. Cubos, UVs, textura e
  geometria em repouso conferidos contra a fonte. Nenhuma peça nova ou proporção alterada.
- Penas do cotovelo sob `forearm_*`, pivô no cotovelo. Herdam ombro/antebraço e abrem localmente;
  não há cancelamento inverso que as mantenha paradas enquanto os braços se movem.
- Dois grupos neutros novos, `leg_plumage_left/right`, filhos das coxas com pivô no joelho,
  permitem recolher a plumagem das pernas no agachamento e pouso. Total: **29 grupos**.
  As penas continuam seguindo a coxa; sua dobra local evita cruzar o piso.
- Idle/walk conservam chaves e curvas originais. Os dois grupos novos ficam neutros nesses clipes.
  O vínculo corrigido das penas do cotovelo também vale durante idle/walk.
- Sem escala animada, fórmulas Molang ou controladores de IK necessários no jogo.
- Fonte manual, propostas anteriores e exportações Roblox preservadas. Os hashes constam
  em `proveniencia.json`; `--refazer` recusa uma saída editada à mão ou fonte diferente.

## Verificação das chaves salvas

- Estrutura e bote: **zero erros/avisos** do motor externo; animação amostrada a 120 Hz,
  tolerância de afundamento 0,05 e separação de juntas 0,75 unidade.
- Medição independente a **240 Hz**: apoio com erro máximo **0,003359 unidade**, trajetória
  livre com desvio máximo **0,057135 unidade** da curva analítica entre chaves.
- Mínimo global **Y=0,085124**, piso de referência **Y=0,087410**: diferença de 0,002286 unidade
  na interpolação do apoio. Sem geometria significativamente abaixo do piso.
- As duas patas ficam no ar aproximadamente de **0,338 a 0,783 s** e encontram juntas um alvo
  baixo de **4×3×7 unidades**, em X=±2, Z=−14…−7, entre **0,575 e 0,671 s**. Interseção SAT de
  cubos orientados dos dedos com a caixa, não apenas sobreposição de AABBs da criatura inteira.
- Pivôs das penas coincidem com os cotovelos; início/fim neutros, sem deslocamento acumulado.
  Rotações contínuas entre chaves, sem volta de 180°; orientação frontal do corpo preservada.
- Idle/walk: zero erros e o mesmo aviso preexistente do dedo traseiro esquerdo do walk
  (0,34 unidade sob o piso a 0,267 s). Fonte de comparação registrada na v2; não veio deste bote.
- Bloqueio inicial em três poses e duas vistas, seguido de revisão das poses finais e prévia
  nativa no Blockbench. Reabrir de fato o projeto após mudar o arquivo: `blockbench_launch`
  pode apenas selecionar uma aba já aberta com a versão anterior em memória.

As medições verificam estrutura, continuidade, chão e alcance de um caso de alvo baixo.
A avaliação do comportamento e da força do golpe continua sendo artística. O salto visual e
o avanço curto da malha estão no clipe; deslocar o modelo no cenário, selecionar alvos, causar
dano, captura e varredura de combate são integração futura de gameplay.

## Reproduzir

```powershell
uv run python scripts/animar-bote-pavao-f2-v3.py --medir
uv run python scripts/revisar-bote-pavao-f2-v3.py --poses
uv run python scripts/animar-bote-pavao-f2-v3.py
uv run python scripts/revisar-bote-pavao-f2-v3.py
```

O gerador recusa saída existente; `--refazer` permite refazer somente a própria geração,
se os hashes ainda coincidirem. `poses-bloqueio.png` registra o estudo inicial, antes dos
refinamentos de abertura das penas e recolhimento do pescoço. `poses-bote.png` e o GIF são finais.
Operações, proveniência, marcadores propostos e relatórios ficam nesta pasta.

**Próximo:** avaliar este bote no Blockbench, depois derivar o rasante frontal para grupos e
estudar a repulsão dupla/apoio sólido da cauda. Esses outros dois golpes ainda não foram criados.
O repertório foi autorizado; a linguagem do bote está sendo entregue primeiro para revisão.
