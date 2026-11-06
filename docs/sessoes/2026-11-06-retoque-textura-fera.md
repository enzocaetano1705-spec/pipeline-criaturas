---
tipo: sessao
data: 2026-11-06
fase: retoque da textura do protótipo Tripo -> Blockbench
ia: codex
status: revisão r05 entregue para avaliação visual
---

# Preguiça rogue — textura do cachecol, rosto e emendas

**Revisão visual:** conferir a nova aba `fera-sombras-e3-textura-r05` e
`modelos/fera-fera-agil-das-sombras/malha-v1/textura-v2/r05/comparacao.png`.
Antes de iniciar animação/exportação, vale a parada da skill
`skills/criaturas-3d/SKILL.md`: “Folha de vistas ainda não aprovada numa criatura real”.
Esta sessão entrega o retoque solicitado, sem inferir aprovação do usuário.

**Pedido:** usuário adotou o fluxo desenvolvido no Claude com malha baixada do
Tripo e conversão para Blockbench. Pediu limpar cachecol, focinho, olho dividido
na quina, descontinuidades e pixels soltos, preservando o modelo atual.
Preguiça gigante / rogue / F3 de 3, categoria já confirmada; não perguntar de novo.
O pedido anterior sobre UI do jogo foi cancelado pelo usuário e não gerou edições
no jogo nem no Studio.

**Entrada:** sessão do Claude em [[2026-11-05-malha-para-cubos]], decisão 0013,
branch atual `codex/direcao-arte-criaturas`, base `c649752`. Aba nativa
`fera-sombras-e3-malha.a12ba408`; exportação independente em
`textura-v2/entrada-blockbench.bbmodel`, SHA-256
`e18ecce8b1d38aac7b46836700ca1512603dae4af36a0606144154eceb3b15d9`.
Geometria e pixels idênticos à fonte salva; ajustes de pernas/cauda mantidos.
Referências com hashes em `textura-v2/referencias/manifesto.json`.

**Causas:** projeção da malha ao longo de normais diferentes gerava manchas de
pano no pelo; molduras por face reforçavam costuras e buracos aparentes; o mesmo
olho era projetado em faces concorrentes; a frente do focinho confundia nariz
com uma mancha retangular. O plano central de pelo também atravessa a gola.

**Correções:** script isolado `scripts/malha-para-cubos/retocar.py`, configurado
por `textura-v2/retoque.json`, sem mudar o conversor padrão. Reaproveita o atlas,
limpa pequenas ilhas de cor, tira vinho do pelo, desenha a marca do ombro em
coordenadas 3D contínuas, recompõe o pano na gola/costas e na região do plano
que a atravessa; refaz a máscara facial, um olho lateral por face, nariz menor
na parte alta da ponta do focinho. Mantém a expressão em pixels e a paleta
quente/vinho. Atualização do `.bbmodel` exclusivamente por `ops.json` → motor.

**Resultado atual:** `textura-v2/r05/fera-sombras-e3-textura-r05.bbmodel`.
14.446 texels alterados no atlas 512², UV 256². Assinatura de elementos/grupos/
outliner/animações/resolução exatamente igual à entrada:
`722b7051534e3a9d09cede04a30b9daa5e51b8e18b4feb2081a2eb848b1a7c11`.
31 cubos, 14 planos, 31 ossos, 10 locators. Quatro pixels órfãos removidos do
alfa; demais recortes preservados. Nada foi copiado sobre a fonte do usuário.

**Verificações:** compilação Python; reprodução do atlas r05 a partir da entrada
e configuração com igualdade byte a byte; comparação estrutural completa antes/
depois; motor com zero erros e 57 avisos de interpenetração, já presentes na
geometria recebida. Conferência MCP em nova aba do Blockbench: formato Bedrock,
45 elementos, 31 grupos, textura e render corretos. Captura nativa no viewport
offscreen em `r05/blockbench.png`; câmera do usuário preservada. Comparação
software e folha em até 768 px. Não se trata de teste de animação/Roblox.

**Incidentes:** r01 falhou antes de atualizar a textura porque a exportação
nativa contém material vazio. `material: null` resolve sem editar código GPL
do motor. R01 permaneceu identificada como falha. A limpeza desse diretório
temporário foi bloqueada pela revisão automática, sem motivo detalhado além
de “blocked by policy”; adotou-se a alternativa de preservá-lo e documentá-lo.
O descarte do viewport privado retornou `onContextMenu is not defined` no plugin;
isso não alterou o modelo ou a câmera visível. Sem instalação/dependência nova.

**Consumo:** checkpoint `textura-v2/auditoria/00-retoque-validado.json`, desde a
mensagem deste pedido. Até ele: 4.139.434 tokens processados, 3.952.640 de entrada
em cache, 155.158 de entrada sem cache e 31.636 de saída; raciocínio é subconjunto
da saída. O registro não inclui a documentação posterior ao checkpoint e não
equivale a preço em reais ou uso atribuível da assinatura. Sem geração paga.

**Próximo:** avaliação visual da r05. A forma da gola/fita continua sendo a do
protótipo aprovado no Claude; eventuais interseções/volume pedem revisão de
geometria separada. Refinos de pelo maiores, animação e exportação ficam após
essa avaliação, no escopo que o usuário pedir.
