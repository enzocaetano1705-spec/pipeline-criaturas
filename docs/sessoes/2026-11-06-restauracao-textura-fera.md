---
tipo: sessao
data: 2026-11-06
fase: recuperação da direção artística da textura
ia: codex
status: v3/r03 entregue para avaliação visual
---

# Preguiça rogue — preservar o desenho, corrigir localmente

**Revisão:** conferir a nova aba `fera-sombras-e3-textura-v3-r03` e a captura
`modelos/fera-fera-agil-das-sombras/malha-v1/textura-v3/r03/previa-nativa.png`.
Aprovação artística pendente; permanece o ponto de revisão da skill antes de
animação/exportação. O escopo desta rodada é a textura e a correção UV necessária.

**Retorno:** usuário afirmou que a textura anterior era mais bonita, apesar
dos erros. R05 ficou limpa, mas excessivamente plana. Também alterou a modelagem
do cachecol e enviou captura da aparência original da malha Tripo: máscara escura
forte, olho âmbar, nariz com narinas, pelo em manchas grandes, pano com dobras e
broche dourado. Assumir que faltava apenas “limpar” foi uma falha da r05.

**Preservação:** exportação independente da aba ativa, com quatro operações
Resize no histórico, em `textura-v3/entrada-editada.bbmodel`. Gola agora
15×15×3; demais cubos iguais. Nenhuma aba/arquivo editado pelo usuário foi salvo
por cima. Referência e hashes no manifesto desta pasta.

**UV:** o resize recalculou o Box UV da gola e gerou 220 texels em conflito com
ilhas do focinho, cabeça, canela e braço. Nova ilha em [0,96], dentro do mesmo
atlas. Após isso, zero colisões; somente faces/uv_offset da gola diferem da
estrutura editada. Nenhum tamanho, rotação, pivô, grupo ou locator foi alterado.

**Textura:** `scripts/malha-para-cubos/restaurar.py`, separado da simplificação
anterior. Recupera diretamente o atlas v11 preservado, mantendo RGB/alpha das
faces protegidas. Patches localizados nos olhos (desenho original e máscara,
reposicionados na lateral com margem de um texel; fragmento da frente retirado),
nariz com narinas e luz/sombra, manchas vinho isoladas, pano com cinco tons,
dobras contínuas e broche dourado facetado. Recorte da fita preservado; somente
quatro texels órfãos de alfa da juba removidos, sem alterar suas cores.

**Atual:** `textura-v3/r03/fera-sombras-e3-textura-v3-r03.bbmodel`, 31 cubos +
14 planos, 31 ossos, 10 locators. Atlas 512² / UV 256², 52 cores. Modelo aberto
em nova aba; entrada editada e r05 rejeitada preservadas. R01/r02 são estudos.

**Conferência:** reprodução exata do atlas pela função de pintura, assinatura
de geometria/rig igual à entrada, demais UVs iguais, faces protegidas comparadas
uma a uma (também as espelhadas), motor com zero erros e os mesmos 57 avisos
de interpenetração. Conferência nativa por MCP em viewport privado, sem mover
a câmera do usuário. Capturas locais de rosto e cachecol e folha nativa 768×414.
Software auxiliar mostra linhas tracejadas nas interseções do pano; a conferência
nativa é a referência de apresentação. Sem novo serviço de geração/dependência.

**Incidente de captura:** PNG do cachecol excedeu o limite de 64 KB do executor
JavaScript. Captura reduzida em WebP, obtida pela API do plugin, permitiu salvar
a evidência sem alterar o modelo nem o atlas PNG. O checkpoint de consumo é
específico deste retorno, em `textura-v3/auditoria/`; não equivale a preço.

**Próximo:** avaliar a recuperação do desenho e do contraste. Não marcar r05
como aprovada, não retomar o gerador orgânico e não regenerar a geometria sobre
as edições do usuário. Eventuais novas correções continuam em versões novas.
