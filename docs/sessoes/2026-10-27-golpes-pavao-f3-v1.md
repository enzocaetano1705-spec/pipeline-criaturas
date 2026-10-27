---
tipo: sessao
data: 2026-10-27
fase: 10
ia: codex
status: aguardando-revisao-artistica
---

# F3 — talho baixo, cruzado e giro de ceifa

**Para avaliar:** três ataques na cópia nova
`f3/ataques-v1/criatura-pavao-e3-ataques-v1.bbmodel`.
Blockbench ficou com janela vazia após abrir o arquivo e o MCP não respondeu;
pedido ao usuário para reabrir/reativar o servidor. Captura nativa pendente;
três GIFs locais e uma folha de poses estão disponíveis.

**Pedido e aprovação anterior:** usuário aprovou as seis corridas/transições
da v1 e autorizou animar as três ideias de golpe para dar feedback.
Espadas/penas são o foco; o bico deixa de ser aparato de combate na F3.

**Feito:** `attack_low` (1,15 s), `attack_cross` (1,50 s) e `attack_spin`
(1,75 s). Talho rasante direito para alvos baixos; dois cortes diagonais
alternados para médios/grandes; volta de 360° para área. Cada ação distribui
peso/torção entre patas, quadril e tronco, com reação da cabeça, cristas,
penas e cauda. Esquerda continua sendo o lado do ombro, direita o do arrasto.
Todos partem e voltam à mesma guarda aprovada. Sem alterações no Studio.

19 clipes anteriores comparados integralmente por UUID/conteúdo; 93 cubos,
41 grupos, outliner, UVs e atlas preservados. Fontes manuais intactas.
Total: 22 clipes. Fonte SHA-256:
`8520d957178d02497615fb0b608a8768ea9b82d8363795054ba17db7b1ea3618`.
Saída SHA-256:
`006093385217323fab2df3f4278d5b7b74147b94570d16553f71d32f3f1c2299`.

**Referências:** movimentos aprovados da própria F3 e a tradução primária
do Memorial da Prattica do Montante (1651), Myers/Hick, hospedada pelo
Oakeshott Institute. Consulta para passos, eixo da volta e peso nos cortes;
adaptação original à criatura, sem copiar arquivos/animações de terceiros.
Link no README da versão.

**Conferência:** três clipes passaram na leitura linear do arquivo salvo e
no avaliador local com semântica nativa, em duas fases temporais, a 240 Hz.
Pés apoiados, lâminas acima do piso, mãos rigidamente vinculadas, cotovelos
com eixo estável, alcance e âncoras dentro dos limites. Conexões à guarda:
erro máximo de matriz de 1,1e-14. Sondagem opaca a 36 Hz sem nova penetração
de espada nos volumes principais do corpo. Motor externo a 120 Hz:
zero erros/avisos em estrutura, chaves, piso e separação.
Dez testes da serialização decimal passaram nesta sessão.

**Ajustes técnicos:** giro tinha singularidade na decomposição Euler do
corpo próximo de 90°, que introduzia desvios entre chaves. Corpo do giro
passou a usar canais Euler diretos, com patas recalculadas em mundo; a
conferência densa do arquivo passou sem relaxar as tolerâncias. Espadas
amarradas às mãos após o IK; bases das penas ancoradas. Gravação em lote
pelo motor externo, saída protegida por hash e relógio comum de 120 Hz.

**Prévias e limite atual:** capturas via MCP não foram concluídas porque
o aplicativo apresentou janela vazia e conexão recusada. Computer Use
confirmou a janela; nenhum reinício forçado ou fechamento de outros arquivos.
Reserva em software lê as chaves salvas com semântica numérica nativa;
câmera fixa, grade de chão e três GIFs a cerca de 30 fps. Folha de poses
768×768 conferida. Isso não substitui revisão de reprodução/FPS no aplicativo.

**Arquivos:** dois scripts em `scripts/`; modelo, metadados de impacto,
relatórios, hashes, README e prévias em `f3/ataques-v1/`. Estado, ficha,
plano e retomada atualizados no vault `docs/`. Base Git: `9792913`.
Fase 10 continua aberta. Não houve mudança de arquitetura ou dependências.

**Próximo passo:** feedback artístico dos três golpes e conferência nativa
quando o Blockbench voltar a responder. Depois, ajustar timing/poses conforme
o retorno. Integração de dano, interrupções, hitboxes e pet permanece futura.
