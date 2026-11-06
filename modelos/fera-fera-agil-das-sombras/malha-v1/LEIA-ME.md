# malha-v1 — preguiça rogue a partir do FBX do Tripo

- `entrada/fera-tripo.fbx`: malha baixada pelo usuário (Tripo, plano grátis). `entrada/conceito.png`: conceito e3.
- `entrada/renders/`: malha original renderizada no Blender (lado e 3/4).
- `voxels.npz` / `voxels.json`: voxels de 0,5 unidade com cor da superfície.
- `juntas.json`, `diagnostico-juntas.png`: pontas, papéis e ossos detectados.
- `diagnostico-partes.png`: segmentação (uma cor por osso).
- `fera-sombras-e3-malha.bbmodel`: protótipo v11 do Claude (31 cubos + 14 planos, 31 ossos, 10 locators).
- `ops.json`: lote enviado ao `bbmodel_edit`. `textura-bloqueio.png`: cores medianas por face.
- `comparacao.png`: malha × cubos (render do motor). `folha.png`: conceito + 4 vistas.
- `relatorio.json`: métricas da conversão v11 e validação (0 erros; sobreposições nas juntas documentadas).
- `textura-v2/r05/fera-sombras-e3-textura-r05.bbmodel`: revisão atual da textura, em nova aba, preservando exatamente a estrutura do v11. Antes/depois em `textura-v2/r05/comparacao.png`; captura nativa em `textura-v2/r05/blockbench.png`. Avaliação visual pendente.

Para refazer: ver `scripts/malha-para-cubos/LEIA-ME.md`.
