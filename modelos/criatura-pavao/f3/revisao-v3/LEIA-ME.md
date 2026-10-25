# F3 — identidade da F2 e penas empunhadas

**Avaliação artística pendente.** Abra `criatura-pavao-e3-v3b.bbmodel` no Blockbench.
`apresentacao.png` mostra 3/4; `folha.png` reúne frente, perfil, costas e 3/4.

## Origem e escopo

O usuário editou a v2b: bico simplificado, peito maior, pescoço encurtado, cristas
reposicionadas e pernas mais anguladas. Também decidiu substituir as lâminas dos
antebraços por duas penas seguradas pelas extremidades dos braços.
`origem-manual.bbmodel` é um snapshot do projeto aberto, incluindo mudanças que
ainda não estavam no arquivo salvo: 117 peças. Os arquivos manuais foram preservados.

Na proposta atual:

- Cabeça completa da F2 aprovada, com sete peças, olhos laterais e quatro planos
  de crista. Geometria, pivôs, rotações, UV e textura copiados sem escala; somente
  translação para encaixar na F3.
- Peitoral e dimensões de pernas, quadril/plumagem e cauda preservados da edição.
  Tronco inclinado 16° a partir da cintura; cauda elevada 8° como contrapeso.
- Antebraços recolhidos, carpo compacto e pinça de dois dedos opostos. Cada espada
  é uma pena recortada em um plano, com haste sólida fina segurada pela pinça.
- Ombro → braço → antebraço → `hand_*` → `feather_sword_*`. `hand_*` representa
  a articulação terminal da pinça. Locators na pegada, base e ponta da arma.
- Pivôs dos joelhos ajustados às posições da geometria editada pelo usuário.
- Pintura original da F3 remapeada para rampas menos saturadas da F2. Atlas 512
  mantém a densidade dos pixels e separa a textura exata da cabeça. Reparadas as
  ilhas do peito/canelas que ficaram parcialmente vazias após redimensionamento.

## Conferências

103 peças, 34 ossos, uma textura incorporada e nenhum clipe. Motor: zero erros,
zero peças soltas, zero assimetrias, zero UVs fora do atlas. 128 avisos de
sobreposição AABB em camadas e encaixes; não equivalem a garantia de ausência de
interseções em futuras poses. Piso opaco mínimo ~0,234 unidade.

O teste numérico compara as sete peças da cabeça após retirar a translação e
compara seus UVs e a região integral de textura com a F2. As transparências já
existentes em `beak.south/down` foram mantidas para preservar exatamente a fonte.
Não há novas faces sólidas transparentes. Rotações de conferência do punho mantêm
o encaixe da espada, sem salvar animações. Roblox/colisões não foram alterados.

## Reproduzir

`uv run python scripts/revisar-identidade-pavao-f3.py` gera os lotes e a nova cópia
pelo motor externo. `--regenerar` exige que o hash da saída ainda seja o gerado.
Depois de qualquer edição manual, a próxima revisão precisa de outro arquivo.
`geracao.json`, `revisao.json` e `ajustes.ops.json` registram fontes e verificações.

Próximo: revisão da forma pelo usuário, antes de animações e exportação.
