---
tipo: sessao
data: 2026-10-21
fase: 10
ia: claude
---

# Sessão — piloto do pavão v3 com o Koromon como gabarito

**Pedido:** enviar os commits do Codex e começar o piloto do método. O pavão é reconstruído com a construção do Koromon, conforme [[2026-10-21-retomada-claude]] e [[aprendizado-por-gabaritos]].

**Entrada nova:** prancha padrão do usuário, com o conceito à esquerda e frente | lado / costas | 3/4 à direita. `criaturas nova --prancha` corta os quadros e apaga os rótulos (commit `0586b56`). A prancha do pavão está guardada em `modelos/criatura-pavao/revisao-v3/prancha.webp`. Os arquivos `e1-*.png` da ficha não foram trocados.

**Feito:** o gerador `modelos/criatura-pavao/revisao-v3-koromon.py` cria a `revisao-v3/criatura-pavao-e1-v3.bbmodel`. As versões anteriores e o ensaio ficaram intactos.
- O corpo segue o gabarito: 2 volumes de mesma largura, com o de baixo avançando 1 unidade para formar a mandíbula e a boca. Mede 15 × 11 × 12, contra 12 × 11 × 11 no Koromon, porque largura e profundidade vêm da prancha.
- O rosto é só pintado, a 1 texel por unidade, num atlas 64×64 em Box UV:
  - olhos de 5×5 com brilho, que continuam 2 px na lateral;
  - gema em losango de 3×3 entre os olhos;
  - boca com os cantos subindo e 4 dentes de 1 px.
- As penas são a tira dobrada do gabarito (sobe, vai para trás, ponta com ocelo), com recorte alfa.
  - **Diferença 1:** a tira foi dividida em esquerda e direita para manter os ossos e os clipes `idle`/`walk` aprovados no ensaio.
  - **Diferença 2:** um plano complementar virado para o lado, porque a vista de lado da prancha mostra a pena (no Koromon as antenas somem de perfil).
  - **Diferença 3:** inclinação de −8° em vez de −17,5°, para bater com a altura do pico no perfil.

**Validação:** 0 erros e 0 avisos na geometria, 0 erros e 0 avisos nas animações. `comparar-referencias` contra o Koromon:

| medida | Koromon | v2 | v3 |
|---|---|---|---|
| volumes do corpo | 2 | 3 | 2 |
| texels por altura | 11 | 27 | 11 |
| opacidade dos planos das penas | 0,48 | 0,38 | 0,50 |
| área das penas vista de cima | 1,14 | 0,08 | 1,03 |

A largura do corpo, a largura das penas e a área de perfil divergem de propósito, pela prancha. Folha comparada com a prancha em `revisao-v3/comparacao-prancha.png`.

**Limites honestos:**
- O corpo é caixa, como no gabarito; a prancha é uma bola peluda.
- As penas ficam menores e mais esquemáticas que na ilustração.
- Em 3/4, o plano da frente e o plano lateral se cruzam.
- As animações passaram na validação, mas não conferi quadro a quadro com os novos pivôs.

Arte ainda **não aprovada**: aguarda o usuário.

**Próximo:** ajustar pelo retorno do usuário. Depois, registrar a correspondência pavão↔Koromon como o primeiro caso do piloto de 12 (ficha de construção por parte) e passar para um caso com gabarito oculto.

## Retorno do usuário e segunda rodada (mesma data)

**Nota do usuário:** a v2 tinha nota 4 e a v3 subiu para 6. Com as correções dele no modelo foi para 7, e ele espera 8,5–9 com a textura certa. As animações estão ótimas.

**O que o usuário corrigiu à mão no modelo** (guardado em `revisao-v3/historico/20261021-2031-antes-da-textura.bbmodel`):
- a cabeça e o corpo ficaram 1 px mais estreitos de cada lado (largura 13);
- o corpo ganhou 1 px para trás;
- os planos laterais das penas saíram;
- os planos dos ocelos foram girados e reposicionados;
- as penas da direita passaram a espelhar a ilha de UV das penas da esquerda.

Ele também exportou `modelos/criatura-pavao/model.animation.json` e `textura.png`.

**Defeitos de textura que ele apontou, e a correção** (`revisao-v3-koromon.py --so-textura`, que repinta só o corpo e mantém a geometria e as penas dele):
1. **Olho:** havia um pedaço na lateral enquanto o olho fechava inteiro na frente. Agora o olho tem 6×5 e é desenrolado na quina como no gabarito: 4 colunas na frente e 2 na lateral, com o contorno fechando na lateral. A pupila fica no meio da parte da frente e o brilho fica no alto, à esquerda de quem olha.
2. **Boca:** estava descontínua e o topo do lábio ficava na cor do corpo. Agora a boca é uma faixa escura contínua: o topo do degrau da mandíbula, a linha da frente e a dobra na lateral. Os dentes ficam pendurados logo abaixo.
3. **Manchas aleatórias:** saíram. As faces são chapadas, com o topo claro e a base escura.

**Ajuste de UV:** a ilha do volume de cima tinha ficado com v = −1, ou seja, uma linha fora da textura, depois da edição. Ela voltou para [0, 0]. Mudou só o UV, não a forma.

**Validação:** 0 erros. Os 2 avisos vêm de penas que se interpenetram, o que é esperado em planos cruzados e vem da edição do usuário.

**Lições para o método** (vão para o caso pavão↔Koromon do piloto):
- Traço que dobra a quina (olho, boca) é pintado numa coordenada desenrolada. O contorno fecha num lado só.
- A boca no degrau da mandíbula ocupa o topo do degrau, além da frente.
- Na escala de 1 texel por unidade, ruído aleatório lê como sujeira. Detalhe só onde tem intenção.
- Proporção: a prancha pedia uma cabeça mais estreita do que a minha medida (o pelo engana a largura). Penas: planos girados resolvem melhor que a tira lateral complementar.

## Terceira rodada: penugem procedural

**Retorno do usuário:** ele mesmo corrigiu a boca a pincel. Foram 13 pixels na faixa do lábio (linha 46 do atlas), e a frente ficou "90%". O resto do corpo estava praticamente cor sólida, com pontos de sombra sem sentido. Ele pediu algo mais natural, sem padrão bem definido, parecendo penas em pixel art, com sombras e cores levemente destoantes onde fizer sentido.

**Feito** (`revisao-v3-koromon.py --penugem`):
- Laterais, costas, topo e base receberam a penugem. Tufos espalhados numa grade irregular, no máximo um por célula 3×3 e em cerca de 60% das células. Cada tufo tem brilho em cima e um "v" de sombra embaixo.
- Por baixo dos tufos:
  - um degradê de volume pontilhado (Bayer 2×2): claro em cima e escuro embaixo, com sombra sob o volume de cima e costas mais escuras;
  - manchas de tom e áreas um pouco mais verdes, feitas com ruído suave.
- Pintinhas douradas aparecem só no brilho de alguns tufos.
- Na frente, só o fundo liso recebeu uma versão suave, de um tom.
- Ficaram intactos, conferido pixel a pixel contra o backup: olhos, gema, boca, dentes, a faixa do lábio pintada pelo usuário e todas as penas.

**Tentativas descartadas:**
- escamas 3×2 e 4×3 em fileiras: liam como tijolo ou faixas, padrão rígido demais.

**Lições para o método:**
- A 1 texel por unidade, a "vida" vem da combinação: degradê de volume pontilhado + ruído de baixa frequência + marcas pequenas espalhadas sem grade visível.
- Fileiras regulares viram tijolo.
- Proteger o que o usuário pintou: repintar só por face e por região, e conferir os pixels dele depois.

## Quarta rodada: plumagem com padrão de pena

**Retorno do usuário:** ficou melhor, mas penas não são tão sem padrão assim. Os 10% que faltavam no rosto são justamente essa textura do resto do corpo.

**Feito:**
- **Desenho da pena:** penas de 4 texels em fileiras de 2, cada fileira deslocada meia pena, como telhas. Cada pena tem o alto claro, o miolo na cor da pena, as laterais um tom abaixo e a ponta escura que cai entre as duas penas de baixo. É isso que forma o recorte em escama.
- **Irregularidade controlada:**
  - tom sorteado por pena;
  - pontas que às vezes faltam ou se alongam;
  - fileiras com um desvio ocasional;
  - ruído suave de cor (mais fraco que na rodada anterior);
  - pontilhado leve sobre o degradê de volume.
- **Rosto:** a mesma plumagem no fundo, com contraste de um tom. Agora o rosto é refeito a partir do desenho (olhos, gema, boca, dentes e queixo de `cor_corpo`) e só o fundo recebe a plumagem.

**Problema encontrado:** o Blockbench do usuário estava com o arquivo antigo aberto. Ao salvar a correção da boca, ele regravou `uv_offset [0, -1]` no volume de cima, o que deslocou a textura da cabeça 1 linha. A gema e o alto dos olhos apareciam cortados no render.
- `--penugem` agora reposiciona o UV quando encontra isso.
- O usuário precisa fechar e reabrir o `.bbmodel` antes de editar de novo.

O lábio pintado pelo usuário e as penas foram conferidos pixel a pixel: estão iguais.

**Lição:** antes de qualquer pintura por código, ler o UV real do arquivo salvo. Uma edição à mão feita sobre o arquivo antigo aberto desfaz mudanças de UV sem aviso.

## Fechamento

O usuário fez os últimos retoques à mão (31 px de boca e queixo) e aprovou: **nota 8,5** ("100%"). A cópia da versão aprovada está em `revisao-v3/historico/20261021-2051-aprovada-8-5.bbmodel`. Ficha do caso: [[piloto-01-pavao-koromon]].

O `--penugem` deixou de repor o UV sozinho: a versão aprovada tem `[0, −1]`, e para repor agora é preciso pedir com `--repor-uv`.

## Roblox: linha transparente atrás da cabeça

**Relato do usuário:** no Studio, uma linha de pixels atrás da cabeça ficou transparente.

**Causa:** o `uv_offset [0, −1]` gravado pelo Blockbench deixa a última linha do topo da cabeça fora da textura (v = −1). O Blockbench repete a linha da borda (o sampler do `.glb` também pede clamp), mas o Roblox dá a volta e lê a linha 63 do atlas, que é transparente.

**Correção:** `revisao-v3-koromon.py --corrigir-topo`:
- a ilha volta para `[0, 0]`;
- a pintura dela desce 1 linha, e a linha que o clamp repetia foi duplicada;
- conferido: **0 de 1744 texels** mudaram de cor em relação ao aprovado.

O `.glb` foi reexportado: validador sem erros, UV em v ∈ [0,0002; 0,9998]. Restam 4 vértices com u = −0,00024, o recuo de borda do exportador, abaixo de 1/60 de texel.

**Lição:** antes de exportar para o Roblox, recusar qualquer UV fora de [0, 1]. O Roblox ignora o clamp do glTF.

**Confirmado pelo usuário:** com o `.glb` novo e o preparo, a linha sumiu e o pavão está certo no Roblox.
