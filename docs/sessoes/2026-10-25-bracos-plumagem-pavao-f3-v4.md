---
tipo: sessao
data: 2026-10-25
fase: 10
ia: codex
status: aguardando-revisao-artistica
---

# F3 v4 — braços humanoides e plumagem da F2

**Avaliação para o usuário:** conferir a nova v4 aberta no Blockbench e a folha
de vistas. A revisão da forma antecede animações/exportação na skill
`criaturas-3d`; esta entrega atende ao pedido de correções do modelo.

**Retorno:** v3 melhorou bastante, mas braços de louva-a-deus foram descartados.
Usuário pediu braços humanoides sem dedos, mais inclinação, cauda mais elevada,
duas lâminas finas baseadas nas penas dos cotovelos da F2 com contorno de espadas,
penas longas da F2 nas costas e asas da F2 nos cotovelos.

**Feito:** snapshot da aba ativa antes de editar, em `f3/revisao-v4/origem-aberta.bbmodel`.
A aba era a prévia v3; pivôs dos joelhos alinhados às canelas na nova cópia.
Saída `f3/revisao-v4/criatura-pavao-e3-v4.bbmodel`, com 111 peças/38 ossos/atlas 512.
Braços humanoides com mãos em blocos, duas espadas com padrão amostrado da pena
longa original da F2. Seis penas longas dorsais, presas ao tronco, e seis penas
menores em leques nos cotovelos, presas ao antebraço. A origem das 12 peças,
escalas e UVs está em `revisao.json`. Mais 6° de inclinação e elevação caudal;
cabeça continua igual à F2, deslocada para encaixar no novo pescoço.

**Verificado:** motor sem erros, peças soltas ou assimetrias; zero UVs fora ou
novas faces sólidas transparentes. Cabeça/UV/textura conferem com F2; 12 penas
com dimensões escaladas/UV de origem corretos. Encaixe das espadas com desvio
zero ao girar punhos. Zero dedos/pinças. Piso mínimo ~0,234. 279 avisos de
sobreposição AABB; amostragem adicional dos pixels opacos não encontra penetrações
distais >0,15 das penas novas em sólidos no repouso. Afastadas as duas penas
dorsais inferiores para evitar inserção no leque caudal. Isso não testa animações.
MCP confirmou a v4, atlas e aparência; câmera mostra ambas as lâminas.

**Decisões:** mudança artística autorizada pelo usuário; nenhuma alteração de
arquitetura/dependências. Nenhum clipe criado e nenhuma ação no Roblox Studio.

**Próximo:** avaliação artística da v4; futuras alterações após edições manuais
devem produzir outra versão. Fase 10 permanece em andamento.
