# Textura recuperada, gola editada — 06/11/2026

Atual: **r03/fera-sombras-e3-textura-v3-r03.bbmodel**, aberto em nova aba.
`r03/previa-nativa.png` reúne duas capturas do Blockbench. O render por software
é auxiliar: nas interseções do manto ele apresenta linhas tracejadas que não
aparecem da mesma forma no render nativo, que orientou a conferência final.

O usuário reprovou a simplificação da r05. Esta revisão usa o atlas anterior
do Claude (`../textura-v2/entrada-blockbench.bbmodel`) e a geometria da aba que
o usuário acabou de editar (`entrada-editada.bbmodel`). A referência visual
original do Tripo está preservada em `referencia-original.png`.

As quatro operações Resize aumentaram a gola para 15×15×3, de [-7.5,21.5,-16.25]
a [7.5,36.5,-13.25]. O Box UV passou a invadir 220 texels de outras ilhas.
Somente a UV da gola foi movida para [0,96]; geometria/pivôs/ossos/locators e
demais UVs são exatamente os da edição do usuário. Atlas 512², UV 256².

Mantidos da textura anterior: manchas de pelo, sombras, juba, cauda e detalhes
dos membros. `r03/relatorio.json` lista as peças cujas seis faces foram
comparadas pixel a pixel, incluindo membros espelhados. Alterações localizadas:
olho original reposicionado para dentro da face lateral, fragmento duplicado
retirado da frente; nariz com volume e narinas; pequenos pontos vinho isolados;
quatro texels de alfa órfãos da juba. Cores da juba permanecem idênticas.

Pano redesenhado com cinco tons vinho e campos de dobra contínuos entre faces,
mantendo o contorno recortado da fita. Broche dourado facetado na lateral da gola,
conforme a referência. Paleta completa com 52 cores, sem suavização do atlas.

Zero erros, 57 avisos de interpenetração idênticos aos da entrada editada;
zero colisões UV. Verificação estrutural ignora somente as UVs autorizadas da
gola. Atlas reproduzido exatamente pelo script. Avaliação artística pendente.

```powershell
uv run python scripts/malha-para-cubos/restaurar.py modelos/fera-fera-agil-das-sombras/malha-v1/textura-v2/entrada-blockbench.bbmodel modelos/fera-fera-agil-das-sombras/malha-v1/textura-v3/entrada-editada.bbmodel modelos/fera-fera-agil-das-sombras/malha-v1/textura-v3/arte.json modelos/fera-fera-agil-das-sombras/malha-v1/textura-v3/nova-revisao/fera-sombras-e3-textura.bbmodel
```

Não sobrescrever nenhum modelo aberto. O script recusa destino existente e usa
o motor para `update_node` da UV e `update_texture`. Não altera o conversor padrão.
