# Pavão F3 — primeira proposta editável

**Esta v1 foi rejeitada pelo usuário com 3/10.** O `.bbmodel` recebeu tentativas
de edição manual e foi preservado. A proposta atual é a v4 em
`revisao-v4/criatura-pavao-e3-v4.bbmodel`; veja `revisao-v4/LEIA-ME.md` e
`estado-atual.json`. As informações abaixo descrevem a primeira entrega.

Abra `criatura-pavao-e3.bbmodel` no Blockbench. A textura está embutida; o PNG
externo é uma cópia para pintura. `folha.png` resume frente, lado, costas e 3/4.

## Modelo

- Estágio 3 de 3; ave bípede com cauda e proporções humanoides.
- 91 peças, 49 grupos/ossos e nove locators. Atlas original 256×256, Box UV.
- Corpo/cauda sólidos; plumagem em planos recortados. Duas plumas de crista,
  três lâminas por antebraço e leque caudal de seis penas com ocelos.
- Ombro → braço → antebraço → mão. As lâminas são filhas do antebraço.
  Quadril → coxa → canela → pé; penas dos tornozelos acompanham a canela.
  Cauda em três segmentos, com o leque ligado aos segmentos correspondentes.
- Frente −Z, Y para cima, direita da criatura +X. Altura inicial ~64,2 unidades
  (quatro blocos), proposta ajustável; não é escala final do jogo.
- Sem clipes de animação nesta etapa. A postura e as juntas ficam disponíveis
  para a revisão da forma antes de desenvolver o repertório de combate.

As quatro artes são a fonte do desenho, preservadas em `docs/criaturas/`.
`imagens-fonte.json` registra originais/hashes. A vista lateral esconde uma das
duas plumas da cabeça. Referência a Jesmon é funcional, sem adicionar partes
ou flutuação. A cauda tem sustentação volumétrica sob as penas, não só cartões.

## Conferência e limites

`revisao.json` registra o hash conferido: hierarquia válida, sem peças soltas,
simetria dos pares, UVs dentro do atlas, faces sólidas sem transparência,
planos com pixels opacos e piso mínimo opaco ~0,004 unidade.
O motor acusa 122 sobreposições AABB: inclui camadas de penas, caixas de planos
rotacionados e encaixes volumétricos. Não significa 122 falhas visuais nem uma
garantia de ausência de interseções durante poses futuras. A amostragem das
lâminas/leque não encontra passagem distal por mãos ou cauda; restam dois
contatos pequenos de inserção das penas com a própria canela (~0,37 unidade).
O modelo ainda aguarda avaliação artística. Colisão e importação da F3 no
Roblox não foram validadas nesta etapa.

## Reproduzir e preservar edições

`uv run python scripts/revisar-pavao-f3.py` verifica a versão salva.
`scripts/modelar-pavao-f3.py` gerou lotes pelo motor externo do Blockbench.
`--refazer` só funciona se o hash ainda for o da saída gerada. Depois de suas
edições, alterações por código devem produzir uma nova versão `.bbmodel`.
Não regenere o arquivo manual para recuperar a proposta anterior: use o Git.
