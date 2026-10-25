---
tipo: sessao
data: 2026-10-25
fase: 10
ia: codex
status: aguardando-revisao-artistica
---

# F3 — cabeça da F2, postura aviana e duas penas empunhadas

**Avaliação para o usuário:** conferir a v3b aberta no Blockbench e sua folha de
vistas. A forma aguarda aprovação antes de animações/exportação, conforme a
skill `criaturas-3d` e o pedido de trabalhar primeiro o modelo.

**Retorno e autorização:** usuário tornou a v2 aceitável com alterações manuais
no bico, peito, pescoço, cristas e pernas. Substituiu lâminas anexas aos braços
por duas penas seguradas. Pediu conversa antes de editar; após proposta de
pinças pequenas e postura aviana, autorizou aplicar as mudanças e mostrar.
Exigiu cabeça precisamente igual à F2, olhos laterais, cristas finas, paleta
menos saturada, penas finas nas espadas e manutenção da cauda mais espessa.

**Feito:** snapshot do projeto aberto (117 peças), preservando inclusive edições
não salvas. Nova saída `f3/revisao-v3/criatura-pavao-e3-v3b.bbmodel`, 103 peças,
34 ossos, atlas 512 e zero clipes. Sete peças da cabeça da F2 aprovada copiadas
sem escala; somente translação. Peitoral/dimensões das pernas e cauda preservados.
Tronco inclinado 16°, cauda elevada 8°, pescoço compacto, antebraços recolhidos e
pinças com dois dedos. Duas espadas em planos recortados, com haste sólida,
ossos próprios sob a pegada e locators de base/ponta. Joelhos alinhados às edições.
Paleta remapeada sem apagar padrões; reparadas ilhas UV do peito e canelas.

**Verificação:** zero erros do motor, peças soltas, assimetrias e UVs fora.
Dimensões preservadas conferidas por peça. Cabeça/UV/textura iguais à F2;
desvio geométrico numérico máximo ~7e-15. Encaixe da arma com desvio zero em
rotações do punho. Piso mínimo opaco ~0,234. 128 avisos de sobreposição AABB
em camadas e encaixes. Duas transparências inferiores/posteriores do bico já
existentes na F2 preservadas; nenhuma face sólida nova transparente.
MCP confirmou a v3b e o atlas incorporado; conferida a prévia no aplicativo.

**Problemas e contornos:** exportação desktop registrava material vazio; atualização
da textura limpa esse vínculo. Crista direita tem UV por face espelhado, preservado
explicitamente. Gerar Box UV novo para ela mudaria a aparência da cabeça.
Sem mudanças de arquitetura/dependências e sem ações no Roblox Studio.

**Próximo:** avaliação artística da v3b. Edições manuais exigem nova versão;
não regerar a v2b nem a v3b depois de editadas. F2 permanece finalizada por ora.
