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
- `textura-v2/r05/fera-sombras-e3-textura-r05.bbmodel`: revisão rejeitada pelo usuário por simplificação excessiva da textura; preservada como histórico.
- `textura-v3/r03/fera-sombras-e3-textura-v3-r03.bbmodel`: revisão atual, com a gola editada pelo usuário, UV da gola separada e textura anterior recuperada com reparos localizados. Prévia nativa em `textura-v3/r03/previa-nativa.png`. Avaliação artística pendente.

Para refazer: ver `scripts/malha-para-cubos/LEIA-ME.md`.

Modelo mais recente (textura): `textura-v4/r03/fera-sombras-e3-textura-v4-r03.bbmodel` — ver `textura-v4/LEIA-ME.md`.
