---
tipo: sessao
data: 2026-10-25
fase: 10
ia: codex
status: aguardando-revisao-artistica
---

# F3 — flicks de animação e superfícies coincidentes

**Complemento posterior:** [[2026-10-25-flicks-numericos-pavao-f3-v10]]
identifica a causa dos flicks persistentes: expoentes como `1e-8` eram lidos
como -8 pelo Molang. A conferência numérica anterior não capturava isso.
V10 corrige a serialização e reduz as chaves do descanso; sincronização
temporal, isoladamente, não eliminava o problema.

**Para avaliar:** reprodução dos nove clipes corrigidos na v9, já aberta no
Blockbench. Depois dos reparos aprovados, trabalhar os golpes.

**Retorno:** v8 em geral boa, com flicks de crista nas saídas e outros clipes,
cauda deslocando no enter_upper, penas-espadas flickando no próprio saque e
tremedeira no saque andando.

**Causas identificadas:**

- No Blockbench 5.2.2, valores perto de chaves usam tolerância de 1/1200 s.
  Reduzir cada canal separadamente deixava compensações fora de sincronia.
  A validação anterior usava interpolação linear ideal e grade regular.
- A crista tinha planos de espessura zero com ambas as faces habilitadas.
  O modo automático do formato usa render dos dois lados: faces opostas
  coincidentes disputavam profundidade.
- O losango da ponta de cada espada sobrepõe a lâmina. As superfícies estavam
  separadas por apenas cerca de 0,00001 unidade: outra disputa de profundidade.
- Rebater waist/tail_1 contra uma base diferente acrescentava translações na
  raiz da cauda nas camadas superiores.
- Inclinar a espada do floreio com o torso andando forçava a correção do piso
  a quase esticar completamente o cotovelo, gerando uma inversão rápida de ritmo.

**Feito:** nova v9 a partir da v8. Relógio comum para os canais variáveis;
preensão rígida quando a espada está na mão e encaixe na cauda recalculado.
Crista suavizada, quatro planos com espessura mínima de 0,01 unidade. Faces
largas de duas pontas recuadas 0,01; X/Y, contorno, atlas e UVs iguais.
Nove clipes corrigidos, mesmos nomes/durações/marcadores. Quatro ciclos
aprovados mantêm exatamente seus canais: idle, walk, combat_ready e combat_walk.

**Saque andando:** plano do floreio estável no mundo e ombro acompanha o corpo.
Flexão mínima do cotovelo passa de aproximadamente 5,85° para 34,26°, evitando
o quase travamento. Ritmo e sentido do golpe mantidos.

**Camadas:** máscara local do companheiro completo: enter_upper de enter_walk,
exit_upper de exit. Corpo/bacia/pernas vêm desse companheiro no mesmo tempo.
Sem adicionar deslocamento artificial em waist/tail_1; raiz caudal permanece
presa mesmo ao visualizar a camada isolada. Não há lógica de pet/Roblox.

**Verificações:** poses salvas a 240 amostras/s passaram; nova conferência com
tolerância nativa, fora da grade, também passou nos nove clipes. Testados
apoios, preensão, encaixe, arma solta, raízes, juntas, conexões e máscaras.
Motor externo: zero erros/avisos nos três grupos, com profundidade intencional
de descanso e camadas conferidas em contexto pelo verificador próprio.
Espessuras e afastamento das faces medidos; seis capturas reais antes/depois
em `comparacao-nativa.png`, mais nove GIFs. Modelo/caminho confirmados pelo MCP.

**Ajuste da conferência:** o cursor em 0,00047 s ainda mostra a chave inicial
no aplicativo; o teste do eixo da junta usa o tempo efetivamente avaliado,
mantendo a exceção já existente dos endpoints pacíficos aprovados.

**Implementação:** gerador v9 e auditor de flicks; verificador v8 recebe
opções compatíveis de amostragem nativa/composição, sem mudar seu padrão.
Investigação do comportamento nativo pelo programa instalado e MCP, sem
incorporar código externo. Nenhuma dependência nova, nenhuma fonte manual
sobrescrita. Fase 10 aberta. Base anterior: commit `2ef8f39`.

**Próximo:** avaliação visual dos reparos; golpes depois.
