---
tipo: decisao
data: 2026-11-05
status: ensaio autorizado; não altera o gerador padrão
---

# 0012 — Reconstruir com gabarito e conferir a projeção

O usuário rejeitou a silhueta/textura do ensaio orgânico e forneceu seis capturas
do mesmo modelo em giro, pedindo construção sobre o perfil e uso das vistas como
gabarito também para futuros modelos cubificados. A decisão 0006 já permite
comparação por correspondências; este pedido autoriza o ensaio de reconstrução.

Preservar as capturas, segmentar o fundo variável e registrar câmera/escala,
landmarks e dimensões por parte. Perfil esquerdo determina a distribuição de
comprimento/altura; frente/costas e superior/inferior restringem largura/volume.
As ilustrações ficam como fonte de cor. Registrar diferenças sem misturar poses
incompatíveis ou usar proporções anteriores como verdade.

Construção isolada em `scripts/gabarito-fera/`, resultados em `gabarito-v1/`.
Adicionar a imagem como fundo/referência no `.blend` e produzir sobreposição
de silhuetas referência/render, com excesso, falta e IoU. A referência de fundo
não participa do render da geometria nem da máscara medida.

As câmeras do serviço não foram fornecidas. Hipótese ortográfica e ajustes de
câmera devem ser explícitos; não prometer coincidência 100% ou geometria única a
partir das capturas. Ajuste 2D global serve à calibração e não deve deformar cada
parte para maquiar erros. Quantidade de faces e integridade técnica continuam
separadas da aprovação artística. Não pintar antes de conferir a forma.

Não extrair malha/dados ocultos do serviço. As únicas fontes são as imagens
fornecidas. O resultado é reconstrução de referência conhecida, com consumo
registrado desde o novo pedido. Não substituir o pipeline padrão ou apresentar
este caso como evidência de generalização para outras criaturas.
