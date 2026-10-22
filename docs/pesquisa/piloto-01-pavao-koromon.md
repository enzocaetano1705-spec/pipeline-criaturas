---
tipo: caso-piloto
caso: 1 de 12
data: 2026-10-21
criatura: criatura-pavao (e1, baby, 1 de 3)
gabarito: Koromon (The Digimod, babies2/koromon.bbmodel)
modo: analogia (recolor estrutural)
nota_final: 8.5
---

# Caso 1 — pavão baby ↔ Koromon

Primeiro caso do piloto descrito em [[aprendizado-por-gabaritos]]. O registro do trabalho está em [[2026-10-21-piloto-pavao-v3]].

## Entrada
- Prancha padrão do usuário: conceito, frente, lado, costas e 3/4 (`modelos/criatura-pavao/revisao-v3/prancha.webp`).
- Gabarito estrutural: o Koromon, escolhido pelo usuário. As antenas do Koromon correspondem às penas do pavão.

## Correspondência por parte

| parte do pavão | solução do gabarito | adaptação |
|---|---|---|
| corpo | 2 volumes de mesma largura; o de baixo avança 1 e forma a mandíbula | 13 × 11 × 13 (o usuário ajustou largura e profundidade) |
| rosto | só pintado, 1 texel por unidade, atlas 64×64, olho que dobra a quina | olho 6×5 desenrolado (4 colunas na frente, 2 na lateral); gema 3×3; boca no topo do degrau da mandíbula |
| penas | tira de planos dobrada, inclinada, com recorte alfa | 2 tiras (uma por lado) para manter ossos e animações; planos dos ocelos girados pelo usuário |
| ossos e animação | `entity`/`body` | ossos do ensaio próprio (`idle`/`walk`), aprovados sem mudança |
| pele | faces chapadas com leve chanfro | plumagem em escama (fileiras desencontradas) com variação, degradê e ruído suave |

## Evolução da nota (dada pelo usuário)

| versão | nota | o que mudou |
|---|---|---|
| v2 (método anterior) | 4 | 3 volumes, atlas 128, densidade 27 texels por altura |
| v3 gerada pela construção do gabarito | 6 | 2 volumes e mandíbula, atlas 64, densidade 11 (igual ao gabarito) |
| + correções do usuário no modelo | 7 | cabeça −1 px de cada lado, +1 px para trás, penas laterais removidas, ocelos girados |
| + textura corrigida (olho na quina, boca contínua, sem manchas) | — | — |
| + plumagem com padrão de pena e retoques do usuário (boca e queixo, 31 px) | **8,5** | versão aprovada |

## O que o usuário ainda fez à mão (o método deve aprender)
1. **Proporção:** a cabeça ficou 1 px mais estreita de cada lado e 1 px mais funda. O pelo da ilustração faz a largura parecer maior.
2. **Penas:** saíram os planos laterais complementares, e os planos dos ocelos foram girados (cerca de 57° em Y e 114° em Z). Isso resolve o perfil melhor que a tira lateral.
3. **Boca e queixo:** retoques a pincel no volume de baixo (linhas 46–50 do atlas), por duas vezes.
4. **UV:** o arquivo aprovado tem `uv_offset [0, −1]` no volume de cima. Isso veio do Blockbench e foi mantido assim, porque a versão foi aprovada nesse estado.

## Regras extraídas
- Use a construção do gabarito por função, não por contagem de peças. Copie a densidade de textura e o tamanho do atlas.
- Olho e boca que dobram a quina são pintados numa coordenada desenrolada, com o contorno fechando num lado só.
- A 1 texel por unidade, ruído aleatório parece sujeira e fileiras regulares parecem tijolo. A pena convincente fica no meio: escama em fileiras desencontradas, com variação por pena.
- Antes de pintar por código, leia o UV do arquivo salvo e preserve os pixels que o usuário pintou (confira depois, pixel a pixel).
- Pergunte ao usuário pelas animações à parte. Aqui, as do ensaio foram aprovadas desde o início.

## Arquivos
- Modelo aprovado: `modelos/criatura-pavao/revisao-v3/criatura-pavao-e1-v3.bbmodel`. Textura: `modelos/criatura-pavao/textura.png`.
- Gerador: `modelos/criatura-pavao/revisao-v3-koromon.py` (`--refazer`, `--so-textura`, `--penugem`).
- Diagnóstico por partes: `revisao-v3/comparacao-koromon-v3.json`. Histórico das versões do usuário: `revisao-v3/historico/`.

## Exportação
- **Roblox:** confirmado no Studio pelo usuário em 21/10/2026, com escala 3×, alfa por `SurfaceAppearance` e `idle` tocando. Arquivos em `modelos/criatura-pavao/export/roblox/` (`.glb` e `preparar-no-studio.luau`).
- **Minecraft:** não exportado ainda. O usuário considera certo que funciona, porque é o formato nativo do Blockbench.
