---
tipo: sessao
data: 2026-10-25
fase: 10
ia: codex
status: aguardando-revisao-artistica
---

# F3 — postura pacífica e combate com penas da cauda

**Avaliação para o usuário:** revisar os oito clipes no novo arquivo aberto no
Blockbench, principalmente o saque, a espada sobre o ombro e a marcha de combate.

**Pedido:** preservar a edição manual com braços de louva-a-deus e espadas antigas
removidas. Corrigir o pescoço de cor sólida, criar idle/walk pacíficos próximos da
F2 e postura ereta de combate, retirando da cauda as penas 04/06 como espadas
grandes. Descanso com uma lâmina no ombro e a outra cravada no chão; guardar ao sair.

**Feito:** snapshot `f3/animacoes-v1/origem-manual.bbmodel`, 93 blocos/41 grupos.
Saída `criatura-pavao-e3-animacoes-v1b.bbmodel`. Mesmos UUIDs, posições, dimensões,
rotações e pintura dos blocos manuais, exceto UV/pintura do pescoço inferior.
Nova ilha por face, padrão de pixels na paleta do corpo e faixa ventral clara;
158 pixels novos, sem atingir UVs das outras partes. Nenhuma fonte manual sobrescrita.

**Rig:** pivôs de pescoço/cabeça, braços/punhos e pernas alinhados às juntas
atuais. Penas 04/06 controladas por chaves relativas a `body`, compensando sua
transformação para acompanhar cauda ou mãos. As seis peças das penas continuam
únicas, com a espessura manual. Marcadores de mãos, bases/pontas das armas e
encaixes na cauda atualizados. A plumagem dorsal se recolhe em combate para
liberar o caminho da lâmina sobre o ombro.

**Clipes:** `idle` (3,2 s), `walk` (1,5 s), `combat_enter` (3,4 s),
`combat_idle` (3 s), `combat_walk` (1,8 s), `combat_exit` (2,8 s),
`combat_walk_start`/`combat_walk_stop` (0,8 s cada). Saque com pega esquerda
em 0,92 s e direita em 1,08 s, impacto em 2,46 s. Guarda de volta em 1,95/2,12 s.
O impacto não se repete no idle. Respiração, transferência de peso, torção
oposta de bacia/peito, estabilização parcial da cabeça e atraso de plumagem/cauda.

**Problemas corrigidos durante a verificação:** a interpolação Euler e um alvo de
cotovelo quase alinhado ao punho produziam torção entre chaves. Corrigidos o plano
do cotovelo, arcos do saque e representação angular contínua. Depois de soltar
as armas, braços retornam por interpolação das juntas; não se força a mão a
passar por uma singularidade. Entrada amostrada a 120 Hz, demais clipes a 60 Hz.
A espada é extraída primeiro e depois transportada para a caminhada.

**Verificações:** arquivo efetivamente salvo, com subamostras entre chaves;
apoios dos pés, mão/empunhadura, arma embainhada, raiz imóvel, costuras dos loops,
conexões de pose e integridade da geometria/UV. Diagnósticos completos em
`validacao*.json`. Estrutura: zero erros, 191 avisos herdados da origem manual;
motor de animação nos ciclos sem penetração intencional: zero erros/avisos.
41 testes de animação, renderização, textura e contratos passaram.

**Referências:** F2 aprovada, estudo do tarso do avestruz de Schaller et al. (2009)
e transporte/guarda de espada em Hutton (1892). Links e adaptações em
`f3/animacoes-v1/REFERENCIAS.md`; sem incorporar arquivos de mods.

**Limites:** avaliação artística pendente. A ponta enterrada é intencional;
não há colisão/dano, comportamento de pet ou integração no Studio. Transições de
caminhada conectam à fase zero; interrupções e mistura em fases arbitrárias
serão resolvidas na futura integração. Não se afirma simulação biológica exata.

**Decisões:** nenhuma mudança de arquitetura/dependências. Escrita pelo motor
externo, proteção por hash e nova saída. Fase 10 continua aberta, sem nova tag.

**Próximo:** avaliação do usuário e eventuais ajustes artísticos antes de exportar.
