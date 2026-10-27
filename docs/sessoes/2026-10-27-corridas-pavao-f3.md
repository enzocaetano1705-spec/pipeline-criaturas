---
tipo: sessao
data: 2026-10-27
fase: 10
ia: codex
status: aprovado-pelo-usuario
---

# F3 — corridas pacífica/armada e suas transições

**Retorno em 27/10:** usuário aprovou as seis animações ("estão ótimas as
animações") e passou aos golpes. Continuação em [[2026-10-27-golpes-pavao-f3-v1]].

**Para avaliar:** `f3/corrida-v1/criatura-pavao-e3-corrida-v1.bbmodel`,
aberta no Blockbench. Conferir os seis clipes novos antes dos golpes.

**Pedido:** acrescentar Run, Combat_run e suas versões Start/Stop à base
aprovada. Interpretado como seis clipes: `run`, `run_start`, `run_stop`,
`combat_run`, `combat_run_start` e `combat_run_stop`.

**Referências e direção:** corrida v2 da F2, aprovada pelo usuário em 24/10,
e as marchas pacífica/armada da F3. Tronco mais baixo, centro de massa sobre
as pernas, cauda como contrapeso e braços recolhidos fora de combate. Com
armas, passada pesada e inclinação intermediária, preservando os lados
aprovados: esquerda no ombro, direita em arrasto. Sem trocar geometria,
anatomia ou direção das espadas.

**Feito:** nova cópia a partir da v10. Seis clipes, durações 0,84/0,60/0,66 s
e 0,96/0,66/0,72 s respectivamente. 19 clipes no total; os treze anteriores
preservados integralmente, assim como 93 cubos/41 grupos, atlas, UVs e rig.
Nada no Roblox Studio foi alterado.

Corpo comprime e impulsiona em cada passada; bacia/peito se contrapõem sem
anular o balanço mundial. Pescoço/cabeça compensam parcialmente; cristas,
penas e cauda respondem em fases diferentes. Pernas em IK, rolagem sobre os
dedos no impulso, breve fase aérea, bases das penas ancoradas. Armas mantêm
o vínculo na cauda ou nas mãos; o arrasto é calculado pelo piso real da lâmina.

**Transições:** pesos quinticos e integral da frequência da passada.
Metadados indicam origem/destino e fase/tempo exatos. As partidas terminam
em poses gravadas explicitamente nos loops. A futura lógica deverá respeitar
essas fases e misturar o estado atual quando um comando interromper uma
transição. Os clipes não implementam essa lógica de pet.

**Verificações:** seis clipes passaram no leitor linear e no leitor nativo
com deslocamentos de 0,00047 e 0,00219 s, a 240 amostras/s. Apoios, piso,
preensão da lâmina inteira, encaixe na cauda, âncoras, alcance, juntas,
fase aérea, balanço do corpo e fechamento dos loops conferidos. Comparação
a 1/60 s das bordas: desvio dos pivôs <0,004 unidade, orientação <0,022°
contra a continuação da base. Motor externo: zero erros/avisos de animação
e estrutura, aceitando planos/cristas finas herdadas de 0,01 unidade.
Dez testes da serialização decimal passaram; não há expoentes nas chaves.

**Ajustes técnicos durante a conferência:** gravação da pose exata de
chegada nos loops; relógio comum apenas na cadeia de tronco/braço direito
para conservar o arrasto na tolerância nativa. Restante dos canais reduzido
com limites de erro para evitar densidade excessiva. A v10 permanece intacta.

**Prévias:** seis GIFs individuais e duas sequências completas, capturadas
do Blockbench via MCP em vista privada com câmera fixa. `poses-nativas.png`
tem seis instantes. Ao descartar a vista, o plugin informou um erro de listener
`onContextMenu`; a lista de vistas confirmou que o registro privado já havia
sido removido. O helper agora trata esse erro conhecido e restaura a timeline.
As capturas foram concluídas; o plugin externo não foi modificado.

**Arquivos:** gerador, revisor e helper de prévias em `scripts/`; modelo,
metadados, hashes, relatórios e GIFs em `f3/corrida-v1/`. Estado atual, ficha,
plano e retomada atualizados no vault `docs/`. Fase 10 continua aberta.
Base anterior: commit `9072269`.

**Próximo passo após aprovação:** golpes da F3, conforme a nota de continuação.
