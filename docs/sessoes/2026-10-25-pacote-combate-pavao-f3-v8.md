---
tipo: sessao
data: 2026-10-25
fase: 10
ia: codex
status: aguardando-revisao-artistica
---

# F3 — pacote de transições a partir da base aprovada

**Para avaliar:** os oito clipes novos da v8 no Blockbench. Depois da revisão,
o próximo trabalho são os golpes da F3, partindo da guarda aprovada.

**Pedido:** usuário considerou a v7 perfeita e autorizou montar os clipes
que estavam adiados. Base aprovada: `idle`, `walk`, `combat_ready`,
`combat_walk` e `combat_enter`; todos preservados integralmente.

**Feito:** nova versão em `f3/animacoes-v8/`, com mesma geometria, textura,
UVs, pivôs e hierarquia. Completa `combat_enter_walk`, `combat_enter_upper`,
`combat_walk_start`, `combat_walk_stop`, `combat_idle`, `combat_idle_resume`,
`combat_exit` e `combat_exit_upper`. Treze clipes no arquivo, sem duplicar
armas. Esquerdo continua no ombro/floreio e direito no arrasto/descanso.

**Movimentos:** saque andando deriva do aprovado, com oscilações e passos
dos ciclos existentes. Start/stop conservam essa postura. Saída guarda as
penas nos encaixes reais da cauda, sem floreio reverso e sem torcer o eixo
dos cotovelos. Descanso parte da guarda, crava e solta a direita, respira
por três segundos, recupera a espada e guarda ambas; total de 7,15 s.
Retomada da pausa dura 1,10 s e termina na guarda. Corpo, pescoço, cauda e
plumagem acompanham o esforço e a respiração; a espada solta fica imóvel.

**Problemas e correções:** interpolar diretamente duas diagonais baixas
fazia a lâmina passar pelo chão. A preparação do descanso agora varre por
fora, conservando a altura da ponta antes da cravada. A trajetória de
recuperação dá espaço lateral ao punho. A amostragem inicial de 120 Hz
perdia precisão no floreio andando: preservadas as chaves não uniformes
da referência, acrescentadas amostras de 240 Hz e de 480 Hz no trecho mais
rápido. Elimina desvios entre chaves sem alterar o saque aprovado parado.

**Verificações:** estudo analítico e conferência das chaves salvas a 240
amostras/s passaram para os oito clipes: mãos/armas, encaixe na cauda,
imobilidade da arma solta, raízes das penas, apoio dos pés, limites/eixos de
juntas, raiz imóvel, conexões e máscaras. Cinco clipes aprovados, geometria
e atlas preservados exatamente. Motor externo: zero erros e zero avisos
nos três grupos de conferência. Descanso permite profundidade intencional;
nas camadas, o apoio é validado com a marcha composta pelo verificador
próprio. Relatórios, oito GIFs e folha de poses ao lado do modelo.

**Integração futura:** clipes de execução única, sem root motion. Metadados
registram fases de entrada/saída, máscara superior, preensão, soltura,
recuperação e encaixe. Camadas substituem canais da máscara, sem adição.
Conexões em fases declaradas verificadas; interrupções em fases arbitrárias
usarão mistura na integração. A retomada começa na pausa e recupera a arma
antes de andar. Nenhuma lógica de pet ou ação no Roblox Studio.

**Referências:** base F3 aprovada e estudos já registrados na v1/F2;
nenhuma nova geometria ou animação de terceiros incorporada.

**Decisões:** sem alteração de arquitetura, formato ou dependências. Fontes
manuais preservadas e escrita pelo motor externo. Base anterior: `6a41bca`.
Fase 10 continua aberta; aprovação artística dos novos clipes pendente.

**Próximo:** avaliar o pacote novo; depois trabalhar os golpes da F3.
