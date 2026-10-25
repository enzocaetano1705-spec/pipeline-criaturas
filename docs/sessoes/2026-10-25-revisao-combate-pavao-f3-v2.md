---
tipo: sessao
data: 2026-10-25
fase: 10
ia: codex
status: aguardando-revisao-artistica
---

# F3 — saque rápido, floreio e descanso com espada solta

**Avaliação para o usuário:** conferir a v2c no Blockbench, especialmente os
ombros/cotovelos no saque, o floreio dos punhos e o descanso completo de 7 s.

**Retorno e esclarecimentos:** idle/walk aprovados. Saque v1 misturava funções
indevidamente e os cotovelos pareciam inverter. Usuário confirmou: floreio das
duas lâminas pelos punhos, sem giro completo do corpo; descanso com cerca de
três segundos de pausa, recuperação/guarda automáticas se permanecer parado.
O saque deve funcionar parado e andando; a saída direta deve funcionar andando.

**Feito:** snapshot da aba ativa em `f3/animacoes-v2/origem-revisada.bbmodel`.
Nova saída `criatura-pavao-e3-combate-v2c.bbmodel`, 93 blocos/41 grupos/mesma
textura. Geometria e pintura não alteradas. Idle/walk mantêm suas poses em mundo;
só os canais das penas foram convertidos para o novo vínculo com as mãos.

**Anatomia:** ombro orienta o alcance e o cotovelo flexiona/estende sobre um eixo
fixo derivado das juntas do modelo manual. Ombro gira antes da extensão até a
cauda; o retorno recolhe os braços após soltar as penas. Removida a escolha de
um plano arbitrário de cotovelo. Representações Euler contínuas e mistura curta
com a marcha aprovada evitam saltos nas conexões. Cintura, peito, cabeça, cauda
e plumagem reagem ao floreio.

**Conceito:** `combat_enter` agora dura 1,3 s e termina em guarda pronta, sem
cravar espada ou descansar. Inclui floreio duplo em oito inclinado. Versão
andando e camada superior separadas. `combat_walk` mantém uma espada no ombro
e arrasta a outra pelo solo. Start/stop duram 0,6 s e conectam à guarda pronta.

**Descanso:** `combat_idle` é uma sequência sem loop de 7 s: impacto em 0,65 s,
soltura da empunhadura e três segundos de pausa (1,1–4,1 s), recuperação e
guarda de ambas as penas. A espada direita fica aproximadamente metade enterrada
e não segue o punho solto. `combat_idle_resume` permite retomar a guarda a partir
da pausa. `combat_exit` (1,5 s) guarda andando e volta à marcha pacífica.

**Camadas:** armas filhas das mãos, com compensação assada para cauda/chão.
`combat_enter_upper` e `combat_exit_upper` não possuem canais de raiz, corpo,
bacia ou pernas. Validada a sobreposição a 12 fases da marcha. Nenhuma lógica
de pet/combate ou ação no Roblox Studio. As fases e marcadores do manifesto
preparam a integração futura; interrupções ainda precisam de seleção/mistura.

**Verificações:** 240 amostras/s no arquivo salvo, 480 no saque andando; encaixe mão/arma e cauda,
eixo/limites dos cotovelos, sola e lâminas no piso, profundidade e soltura da
espada, conexões, camadas e preservação das poses aprovadas. Poses de idle/walk
com desvio de matriz abaixo de 0,00003. Diagnósticos e GIFs na pasta da revisão.
41 testes de animação, renderização, textura e contratos passaram.
Motor: zero erros estruturais, 187 avisos AABB e sete de simetria; geometria
conferida como idêntica à fonte. Nos sete clipes sem enterro intencional,
zero erros/avisos de animação. Saque andando assado a 240 Hz para conferir
também o contato entre chaves. Base da revisão anterior: commit `fee1b28`.

**Problemas corrigidos na revisão:** conexões iniciais/finais com o balanço dos
braços da marcha e retomada da pausa; pequena penetração da lâmina durante a
passagem para o arrasto, corrigida pela trajetória de altura da mão. A penetração
deliberada ao cravar/recuperar é verificada separadamente.

**Referências:** estudo anterior da F2 e [glossário técnico de Wushu Ontario](https://wushuontario.ca/?page_id=2462),
Jian Wanhua com pivô no punho. Arcos adaptados ao comprimento das penas; sem
incorporar modelos, texturas, animações ou código de terceiros.

**Decisões:** ajuste de rig específico da criatura; sem mudar arquitetura,
formato ou dependências do pipeline. Fonte manual preservada. Fase 10 aberta.

**Próximo:** avaliação artística do usuário antes de exportar/integrar.
