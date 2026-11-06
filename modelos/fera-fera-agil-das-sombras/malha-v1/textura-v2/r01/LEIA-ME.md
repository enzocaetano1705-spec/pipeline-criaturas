# Execução interrompida — não usar como revisão

A primeira operação `update_texture` falhou porque a exportação do Blockbench
trazia uma referência vazia de material. O `.bbmodel` nesta pasta é ainda a cópia
da entrada, sem o atlas novo aplicado. A operação foi corrigida para remover
explicitamente essa referência vazia (`material: null`).

Resultado atual: `../r05/fera-sombras-e3-textura-r05.bbmodel`.
