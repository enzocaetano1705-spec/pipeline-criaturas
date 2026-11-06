---
tipo: decisao
data: 2026-11-05
status: ensaio autorizado; não altera o gerador padrão
---

# 0013 — Malha 3D do usuário como entrada da cubificação

**Contexto:** os ensaios da preguiça (comparativo, orgânico, gabarito) tentavam deduzir a forma a
partir de imagens e gastaram muitas rodadas de IA. O usuário baixou gratuitamente, do Tripo, o
FBX texturizado da mesma criatura (sem esqueleto) e pediu a conversão direta para o Blockbench.

**Decisão:** aceitar uma malha 3D fornecida pelo usuário (FBX/GLB/OBJ) como fonte de forma e cor.
A conversão é só código, em `scripts/malha-para-cubos/`: Blender headless gera voxels coloridos;
Python detecta pontas e juntas, segmenta por osso, cobre cada parte com poucos cubos alinhados e
grava o `.bbmodel` pelo motor (`bbmodel_create`/`bbmodel_edit`), com os nomes de ossos e
locators de `docs/convencoes.md`. Resultados em `modelos/<criatura>/malha-vN/`.
A decisão 0012 continua valendo: nada é extraído de serviço pago; a malha é um arquivo que o
próprio usuário baixou.

**Alternativas descartadas:**
- Voxelizar e exportar direto: centenas de cubos em degrau, contra a direção de arte.
- Montar cubo a cubo por MCP ou por imagens: caro em tokens e já reprovado nos ensaios.
- Auto-rig por IA (UniRig etc.): instalação e GPU; fica como plano B se as regras falharem.

**Consequências:** a forma deixa de depender de rodadas de IA; a IA confere uma imagem de juntas
e a folha. Novas dependências: nenhuma (Blender já instalado, numpy/Pillow já no projeto).
Regras de papéis só existem para "bípede com cauda". A licença da malha é do serviço que a gerou
(no plano grátis do Tripo costuma ser licença aberta com atribuição): conferir antes de publicar.
Para desfazer, basta não usar a pasta `scripts/malha-para-cubos/`.

## Atualização 2026-11-05 — planos recortados e textura projetada

Para bater com a referência, a fita do cachecol e a juba viraram planos de espessura zero com
recorte por transparência (como as penas do Pavão; no Roblox o preparo já usa `SurfaceAppearance`
com `AlphaMode.Transparency`). A textura de conferência passou a ser projetada da malha a 2 px por
unidade (512² sobre UV 256², a mesma densidade do Pavão F3). Escolha de estilo do usuário: base da
v4 com cauda e garras da v6 (`--estilo equilibrio`, padrão); a v6 inteira fica em `--estilo anatomia`.
