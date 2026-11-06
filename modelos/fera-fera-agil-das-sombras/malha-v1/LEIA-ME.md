# malha-v1 — preguiça rogue a partir do FBX do Tripo

- `entrada/fera-tripo.fbx`: malha baixada pelo usuário (Tripo, plano grátis). `entrada/conceito.png`: conceito e3.
- `entrada/renders/`: malha original renderizada no Blender (lado e 3/4).
- `voxels.npz` / `voxels.json`: voxels de 0,5 unidade com cor da superfície.
- `juntas.json`, `diagnostico-juntas.png`: pontas, papéis e ossos detectados.
- `diagnostico-partes.png`: segmentação (uma cor por osso).
- `fera-sombras-e3-malha.bbmodel`: modelo cubificado (38 cubos, 28 ossos, 10 locators).
- `ops.json`: lote enviado ao `bbmodel_edit`. `textura-bloqueio.png`: cores medianas por face.
- `comparacao.png`: malha × cubos (render do motor). `folha.png`: conceito + 4 vistas.
- `relatorio.json`: métricas (malha coberta 92%, IoU 3D 62%) e validação (0 erros).

Para refazer: ver `scripts/malha-para-cubos/LEIA-ME.md`.
