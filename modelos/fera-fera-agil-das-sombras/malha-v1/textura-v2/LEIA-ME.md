# Revisão da textura — 06/11/2026

Atual: **r05/fera-sombras-e3-textura-r05.bbmodel**, aberto em uma nova aba do
Blockbench. `r05/comparacao.png` mostra antes/depois; `r05/blockbench.png` é a
conferência nativa, em viewport privado, sem alterar a câmera do usuário.

`entrada-blockbench.bbmodel` é a exportação da aba recebida. Geometria e pixels
foram comparados ao v11 salvo: nenhuma diferença. Nenhuma fonte anterior foi
sobrescrita. As cinco imagens apontando defeitos estão em `referencias/`.

Correções: pano com cores contínuas, sem moldura em cada face; remoção do vinho
solto no pelo; parte da lâmina central que atravessa o manto pintada como tecido;
marca do ombro definida em 3D, atravessando as UVs; máscara facial simplificada,
olho inteiro por lateral e nariz no alto do focinho; pequenos componentes de cor
isolados limpos e quatro pixels órfãos de alfa retirados dos planos.

Preservados exatamente: elementos, tamanhos/rotações/pivôs, UV, grupos,
hierarquia, animações e locators. 31 cubos + 14 planos, 31 ossos, 10 locators.
Atlas 512² sobre UV 256², sem aumentar artificialmente a resolução. O hash da
assinatura estrutural está em `r05/relatorio.json`. Validação: zero erros,
57 avisos de interpenetração da geometria de entrada. Não são uma aprovação
artística nem uma validação de deformação/animação.

O teto de área da limpeza é pequeno; marcas grandes continuam vindo da malha.
Não se pretendeu substituir todo o acabamento de pelo. A forma da gola, a fita
e suas interseções continuam sendo as do modelo que o usuário aprovou no Claude.

Reproduzir sem sobrescrever a versão aberta:

```powershell
uv run python scripts/malha-para-cubos/retocar.py modelos/fera-fera-agil-das-sombras/malha-v1/textura-v2/entrada-blockbench.bbmodel modelos/fera-fera-agil-das-sombras/malha-v1/textura-v2/retoque.json modelos/fera-fera-agil-das-sombras/malha-v1/textura-v2/nova-revisao/fera-sombras-e3-textura.bbmodel
```

As operações reais de `update_texture` estão no `ops.json` de cada revisão.
O código mantém a fonte como somente leitura e recusa um destino existente.
R02–r04 são estudos intermediários; r01 falhou antes de aplicar a textura.
O contador em `auditoria/` pertence a este pedido; tokens processados, cache e
saída não são preço nem percentual da assinatura.
