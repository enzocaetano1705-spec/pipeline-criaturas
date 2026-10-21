---
tags: [pesquisa, pipeline-criaturas, categorias, classificação]
data: 2026-10-21
---

# Categorias de criaturas: regras de modelagem por tipo (21/out/2026)

Complementa [[estilo-blocky-referencias]] (regras por estágio). Aqui as criaturas são separadas por tipo de corpo e nicho, para que cada categoria tenha regras próprias, e definimos como o Claude classifica uma imagem enviada pelo usuário.

## Dados e método
- Cobblemon: 905 modelos. Plano de corpo = formato de corpo oficial do Pokédex (14 formatos, dados abertos do PokeAPI no GitHub), corrigido pela postura real do modelo (ex.: oficial "quadrúpede" mas modelo de pé com 2 pernas e 2 braços → bípede). Nicho = tipo, grupo de ovo, gênero biológico ("Fox Pokémon") e listas curadas por nome.
- Digimod: 270 modelos classificados só pela morfologia visível (pernas, braços, asas, cauda, nadadeiras, movimento), que é o que um classificador de imagem consegue ver.
- Pose de repouso aplicada; medianas (p25–p75). Unidades: cabeça % volume (volume sólido sob o osso da cabeça ÷ total), crânio % altura, olho % altura total, perna % altura, cauda comprimento ÷ altura, cauda % volume, envergadura ÷ altura, corpo comprimento ÷ altura, focinho ÷ profundidade do crânio, orelha ÷ altura do crânio.
- Precisão do método: mesmo com acesso ao esqueleto, a morfologia visível concorda com a categoria oficial em 65% dos casos. Confusões principais: cabeça-corpo × amorfo sem membros (64), bípede com cauda × humanoide (36, cauda pequena), inseto × quadrúpede (23, contagem de patas), cabeça-corpo × humanoide (22). Por isso o classificador sugere até 3 categorias.

## Taxonomia
### Nível 1 — plano de corpo (decide esqueleto, rig e animações base)
| Categoria | Pista visual |
|---|---|
| Bípede com cauda | de pé em 2 pernas, cauda ≥ ~1/4 da altura (dinos, dragões de pé, roedores tipo Pikachu, primatas) |
| Humanoide | de pé em 2 pernas, sem cauda ou cauda pequena, braços |
| Quadrúpede | 4 pernas, coluna horizontal |
| Alado | um par de asas como traço principal (aves, morcegos, alguns dragões) |
| Serpentiforme | corpo longo sem pernas (cobras, dragões orientais, vermes, lesmas) |
| Peixe/aquático | nadadeiras, sem pernas |
| Inseto/artrópode | 6+ patas, carapaça ou 2+ pares de asas |
| Cabeça-corpo | o corpo é a cabeça; membros mínimos ou nenhum (bolas, blobs, bebês Digimon) |
| Tentáculos/multípede | tentáculos ou muitas patas |
| Múltiplos corpos | várias cabeças/corpos (trios, enxames) |

### Nível 2 — nicho (refina proporções e detalhes)
dragão, dinossauroide/kaiju, réptil/anfíbio, canídeo, felino, ungulado (cascos), roedor/pequeno mamífero, urso, primata, ave, morcego, peixe/aquático, serpente/verme, inseto/artrópode, amorfo/fantasma, planta, mineral/objeto, humanoide, fada/fofo. Um nicho pode aparecer em vários planos (dragões: 30 bípedes com cauda, 12 serpentiformes, 6 quadrúpedes, 5 alados).

## Regras por plano de corpo (Cobblemon)
| Plano | n | Cabeça %vol | Perna %alt | Cauda (×alt; %vol) | Envergadura | Corpo compr. | Cubos | Planos | Andar |
|---|---|---|---|---|---|---|---|---|---|
| Bípede com cauda | 220 | 29% | 33% | 0,60; 6% | — | 0,34 | 70 | 43% | 1,5 s |
| Humanoide | 137 | 31% | 29% | 0,44; 3% | — | 0,42 | 58 | 42% | 1,5 s |
| Quadrúpede | 134 | 24% | 47% | 0,55; 1% | — | 0,76 | 60 | 43% | 1,33 s |
| Alado | 77 | 17% | 30% | 0,68; 6% | 2,5× | 0,64 | 76 | 50% | 1,33 s (68% voam) |
| Serpentiforme | 37 | 28% | — | 0,72; 12% | — | 0,65 | 44 | 40% | 3,0 s |
| Peixe | 45 | 37% (crânio 63% da altura) | — | 1,5; 15% | — | 1,0 | 37 | 56% | 60% nadam |
| Inseto | 65 | 27% (olho 19%) | 33% | 1,1; 16% (abdômen) | 2,0× | 0,81 | 47 | 48% | 1,33 s |
| Cabeça-corpo | 149 | 55% | 16% | 0,51; 3% | — | 0,51 | 41 | 46% | 2,15 s |
| Tentáculos | 21 | 35% | — | tentáculos 72% do volume, ~14 segmentos | — | 0,62 | 53 | 40% | 4 s |

Cabeça %vol / altura no jogo (blocos) por estágio:
| Plano | Inicial | Meio | Final | Único | Lendário |
|---|---|---|---|---|---|
| Bípede com cauda | 54% / 0,9 | 25% / 1,4 | 19% / 2,3 | 27% / 1,6 | 43% / 3,0 (n=5) |
| Humanoide | 52% / 0,9 | 65% / 1,2 (n=18) | 22% / 2,1 | 33% / 1,8 | 5% / 2,9 (n=6) |
| Quadrúpede | 38% / 0,9 | 16% / 1,4 | 15% / 2,0 | 13% / 2,1 | — |
| Alado | 37% / 0,7 | 22% / 1,2 | 11% / 2,0 | 23% / 1,3 | 9% / 4,2 |
| Serpentiforme | 30% / 0,9 | 38% / 1,2 | 12% / 1,7 | 15% / 0,9 | — |
| Peixe | 39% / 0,8 | 37% / 1,2 | 31% / 1,8 | 31% / 1,9 | — |
| Inseto | 32% / 0,5 | — | 15% / 1,4 | — | — |
| Cabeça-corpo | 72% / 0,7 | 43% / 1,3 | 38% / 1,9 | 51% / 1,2 | — |
| Tentáculos | 64% / 0,8 | — | 11% / 2,6 | — | — |

## Regras por nicho (Cobblemon)
| Nicho | n | Cabeça %vol (inicial → final) | Focinho ÷ crânio | Cauda (×alt; %vol; segmentos) | Marca registrada | Andar |
|---|---|---|---|---|---|---|
| Dragão | 35 | 40% → 7% (final 3,7 blocos) | 0,82 | 0,80; 13%; 5 | pescoço de 3 segmentos, olhos pequenos (8%), 72 cubos | 2,0 s |
| Dinossauroide/kaiju | 29 | 37% → 15% | 1,09 (o mais longo) | 0,66; 11%; 4 | sólido (40% planos), corpo comprido 0,53 | 3,5 s (o mais lento) |
| Réptil/anfíbio | 49 | 43% → 11% | 0,60 | 0,58; 5%; 3 | olhos grandes (16%), corpo comprido 0,65, 24% nadam | 1,58 s |
| Canídeo | 36 | 42% → 20% | 0,52 | 0,62; 6% (cheia); 4 | orelhas = altura do crânio, pernas 45% | 1,29 s |
| Felino | 22 | 59% → 30% (cabeça grande até o fim) | 0,27 (curto) | 0,68; 1% (fina); 6 (flexível) | 54% planos (bigodes, pelos), corpo 0,50 | 1,33 s |
| Ungulado | 41 | 26% → 13% (final 2,7 blocos) | 0,58 | 0,38 (curta); 0%; 2 | pernas mais longas (46%), orelhas pequenas (0,63) | 1,17 s (o mais rápido) |
| Roedor/pequeno mamífero | 63 | 36% → 22% | 0,41 | 0,82 (longa); 2%; 3 | maioria de pé (42 de 63), pernas curtas 29% | 1,25 s |
| Urso | 10 | 68% → 7% (maior queda) | 0,57 | 0,16 (mínima) | corpo curto, de pé | 1,5 s |
| Primata | 20 | 71% → 35% | 0,29 (curto) | 0,73; 4%; 6 (preênsil) | corpo curtíssimo 0,23, 88 cubos | 2,0 s |
| Ave | 72 | 38% → 11% | 0,64 (bico) | 0,60 (leque); 4% | envergadura 2,5× altura, 50% planos (penas), 53% voam | 1,33 s |
| Morcego | 7 | cabeça 58% | 0,39 | — | envergadura 3,4×, orelhas 1,44× crânio, 100% voam | — |
| Peixe/aquático | 57 | 40% → 30% (quase não encolhe) | 0,67 | 1,32; 13% | crânio 58% da altura, 37 cubos (o mais simples), 50% planos | — |
| Serpente/verme | 38 | 30% → 14% | 1,0 | 0,81; 13% | olhos grandes (17%), corpo comprido 0,89 | 1,0 s |
| Inseto/artrópode | 88 | 29% → 15% | 0,43 | abdômen 0,90; 19%; 5 | olhos 18% (os maiores), antenas 1,5× crânio, envergadura 1,9× | 1,54 s |
| Amorfo/fantasma | 62 | 81% → 33% | 0,85 | — | cabeça domina até o meio, 21% voam | 2,5 s (flutua) |
| Planta | 58 | 90% → 44% | — | curta | pernas curtas (20%) | 1,33 s |
| Mineral/objeto | 56 | 26% → 7% | 0,78 | curta | sólido (32% planos) | 2,65 s (pesado) |
| Humanoide | 79 | 47% → 22% (lendário 5%) | 0,61 | 0,46 | olhos menores (8%), corpo curto 0,34, 32% planos | 1,33 s |

### Pares que se confundem e como separar
- Canídeo × felino: focinho 0,52 vs 0,27 do crânio; cabeça 30% vs 50%; cauda cheia de 4 segmentos vs fina de 6.
- Dragão × dinossauroide: pescoço 3 vs 2 segmentos; dragão costuma ter asas e olhos menores; dinossauroide tem o focinho mais longo e anda mais devagar.
- Ave × morcego: envergadura 2,5× vs 3,4×; morcego com orelhas enormes e cabeça grande; ave com cauda em leque de planos.
- Peixe × serpente: peixe tem crânio dominando a altura e nadadeiras; serpente tem corpo comprido e olhos grandes.
- Canídeo × ungulado: ungulado tem cabeça menor, pernas mais longas, cauda curta, orelhas pequenas.

## Digimod (morfologia visível)
| Plano | n | Cabeça %vol | Cubos | Rookie → Champion → Ultimate (cabeça; altura em unidades) |
|---|---|---|---|---|
| Humanoide | 99 | 22% | 30 | 41% → 23% → 12%; 27 → 39 → 51 |
| Bípede com cauda | 48 | 26% | 36 | 39% → 25% → 18%; 29 → 40 → 50 |
| Quadrúpede | 35 | 16% | 28 | 34% → 16% → 10%; 24 → 34 → 45 |
| Alado | 17 | 37% | 31 | poucos dados |
| Cabeça-corpo | 27 | 100% | 5 | bebês (Baby I/II), 12 unidades |
| Amorfo/sem membros | 29 | 18% | 16 | — |
- Digimon viram humanoides com frequência nos estágios altos (99 de 270). Dragões por nome (25): cabeça 20%.

## Passo de classificação (para a skill)
Entrada: imagem (idealmente também 3/4 ou folha frente/lado/costas) + o prompt usado para gerá-la.
1. Leitura só da imagem, com o prompt escondido. Preencher uma ficha morfológica, cada item marcado visível / incerto / oculto: postura, nº de pernas, braços, asas (pares, envergadura), cauda (comprimento, grossura), nadadeiras, pescoço, tamanho da cabeça, focinho, orelhas, olhos, cobertura (pelo, escama, pena, pedra, planta, gosma, metal), extras (chifres, juba, carapaça, chamas). Itens de profundidade (comprimento do corpo e da cauda, grossura de membros, patas escondidas) tendem a ficar incertos numa imagem frontal.
2. Conciliação com o prompt: o prompt só preenche itens incertos ou ocultos (ex.: "cauda grossa e longa" quando a cauda está atrás do corpo). Item visível não muda. Se o prompt contradiz algo visível, vale a imagem e a contradição é mostrada. O prompt pode reordenar candidatos, nunca criar um candidato sem apoio na imagem.
3. Comparar a ficha com as assinaturas das categorias (tabelas acima) → até 3 sugestões (plano › nicho) com % de confiança e os 2–3 traços que justificam, mais o estágio provável pela proporção da cabeça.
4. O usuário escolhe 1/2/3, outra existente, ou cria uma categoria nova (vira uma ficha nova no projeto). Cada escolha e correção fica registrada para ajustar as assinaturas.
5. A categoria escolhida carrega: faixas de proporção por estágio, modelo de esqueleto com nomes de ossos padrão, técnicas (planos para asas, nadadeiras, penas, orelhas), conjunto de animações e ritmo de andar.

Exemplo de saída esperada (ilustrativo):
```
Leitura (imagem): 4 patas, focinho curto, orelhas grandes, cauda longa e fina (incerta: atrás do corpo)
Prompt: "cauda longa e flexível" → confirma a cauda (item incerto)
1. Quadrúpede › felino — 70%: focinho curto, cabeça grande, cauda fina
2. Quadrúpede › canídeo — 20%: orelhas grandes, pernas longas
3. Bípede com cauda › roedor — 10%: postura ambígua na imagem
Estágio provável: inicial (cabeça ~55% do volume)
Escolha 1, 2, 3 ou outra categoria.
```

## Limitações
- Nichos por nome e gênero têm erros pontuais (ex.: alguns lagartos do grupo de ovo dragão foram para réptil). Categorias pequenas (morcego 7, urso 10, fada 12) têm números instáveis.
- Serpentes ficam esticadas na pose de repouso, inflando comprimento e altura.
- "Braço ÷ perna" saiu ruidoso (eixos diferentes) e não foi usado como regra.

## Fontes
- https://gitlab.com/cable-mc/cobblemon
- https://github.com/ginerJ/The-Digimod
- https://github.com/PokeAPI/pokeapi (pokemon_species.csv, pokemon_shapes.csv, pokemon_species_names.csv, pokemon_egg_groups.csv)
