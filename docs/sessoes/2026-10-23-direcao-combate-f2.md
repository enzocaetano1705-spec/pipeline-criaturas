---
tipo: sessao
data: 2026-10-23
fase: 10
ia: codex
status: proposta-de-direcao-em-discussao
---

# F2 — direção do combate após avaliação da v2

## Retorno do usuário e restrições atuais

- Chutes da v2 rejeitados: humanizados e pouco anatômicos. Bicotada é aproveitável,
  mas falta vida ao conjunto. Alcance geométrico correto não equivale a comportamento convincente.
- Referência proposta pelo usuário: salto com as duas patas sincronizadas, mãos contendo e bico
  atacando, como uma interpretação do comportamento de aves de rapina em um híbrido com mãos.
- Farm frequente e grupos de criaturas pequenas: prender-se ao alvo para começar a atacar
  prejudicaria o fluxo. Contato breve e ataques independentes são uma direção a explorar.
- Usuário propôs também apoio de cauda e extensão simultânea das pernas, inspirado no canguru.
- A exigência anterior de 0,3–0,4 s/alta frequência foi relaxada. DPS alto pode vir de skills mágicas
  no futuro. Não continuar otimizando o ataque físico em torno da cadência da v2.
- Pedido desta etapa: ajudar a pensar o conjunto de golpes e sua linguagem corporal.
  As ideias abaixo são propostas artísticas; ainda não são clipes feitos ou decisões aprovadas.

## Conferência do modelo

Fonte manual permanece com SHA256
`4ee150999774ac5f9b8036487040904ee95243d58e9efc002534654a398d3bad`.
59 cubos, 27 grupos; garras das mãos continuam removidas pelo usuário, mãos presentes.
Não presumir dedos/garras articulados: o rig atual tem `forearm_*` com as mãos e `foot_*`
com os dedos rígidos. Fechar a silhueta dos membros é possível sem inventar articulações.

A cauda tem volumes `tail_mid` (5×3,5×7,5) e `tail_base` (3×2,5×6,5), ligados ao mesmo `tail_1`;
grande parte do comprimento visual vem das penas/leque. Não há cadeia de vértebras que permita
curvá-la como a de um canguru. Um apoio convincente teria de usar a parte sólida, deixar as penas
livres e posicionar o peso sobre o contato. A geometria sozinha não informa resistência estrutural.
O apoio ainda precisa ser testado em poses; se o leque sustentar o corpo ou a bacia ficar sem apoio,
preferir o pequeno salto com contrapeso da cauda. Nenhuma alteração de anatomia está autorizada
por esta proposta nem é necessária para discutir os movimentos.

## Proposta de repertório

Identidade comum: atenção dirigida ao alvo → compressão do corpo → ação das duas patas →
contato breve → pouso/retomada. As mãos trabalham perto do corpo; penas e cauda respondem à força.
Usar essa identidade em todos os clipes e variar a direção do esforço conforme o encontro.

| Situação | Proposta | Função no jogo |
|---|---|---|
| Pequeno isolado | **Bote baixo:** agacha, pequeno salto à frente, patas sincronizadas descem sobre a região do alvo; mãos fecham a silhueta perto do peito e cabeça acompanha para baixo. Bicotada baixa pode entrar como golpe seguinte independente. | Ataque completo ao pousar; dispensa permanecer agarrado e troca de alvo logo após a recuperação. |
| Grupo de pequenos | **Rasante frontal:** salto baixo um pouco mais longo, patas avançam e fazem uma varredura descendente moderadamente aberta, pouso além/na borda da região atingida. Mãos recolhem; leques abrem no impulso e acomodam na aterrissagem. | Área frontal curta acompanhando o trajeto real; vários inimigos próximos podem ser alcançados numa passagem. Alcance lateral a confirmar nas poses. |
| Médio/grande ou inimigo muito próximo | **Repulsão dupla:** recuo da bacia, preparação das duas patas sob o ventre e projeção simultânea à frente. Mãos fazem contenção/empurrão curto quando há superfície alcançável; bico oferece seguimento frontal. | Impacto concentrado e possível afastamento no gameplay futuro; não exige segurar o inimigo. Apoio de cauda é uma hipótese condicionada à pose. |

Bicotada v2: preservar como estudo aproveitável, dar participação ao corpo/pescoço e direção do olhar,
considerar baixa/frontal para o ponto de contato. Golpes independentes permitem escolher ordem e
interromper a sequência quando o alvo morre; não exigir salto + captura + loop de bicadas em todo encontro.
Se imobilização longa for desejada mais tarde, tratá-la como habilidade específica de alvo único.

Área física corresponde ao trajeto das patas/corpo que de fato passa pelo alvo. As penas ornamentais
não fundamentam por si só dano distante ou uma área circular ampla; esse alcance pode ter solução mágica
posterior, se o usuário quiser. Não definir dimensões numéricas de hitbox antes de aprovar o movimento.

## Papel de cada conjunto e qualidade do movimento

- Patas: impulso, contato e aterrissagem, com as duas cadeias recolhidas sob a bacia antes da extensão.
  Manter a leitura digitígrada; conferir quadril/joelho/tornozelo, inclusive o osso aparente que é o tarso.
- Mãos: conter, recolher ou empurrar na distância que os braços curtos permitem. Em alvo muito baixo,
  podem acompanhar a captura sem simular contato impossível. Não virar socos/armas de longo alcance.
- Bico: golpe preciso e seguimento do contato, com duas alturas se necessário.
- Penas: abertura de ameaça e silhueta, resposta ao impulso/frenagem, ligação contínua ao cotovelo.
  Abertura e atraso de acomodação não comprovam sustentação aerodinâmica ou voo.
- Cauda: contrapeso na mudança de inclinação e no salto; apoio breve somente se a parte sólida,
  o piso e a distribuição do peso sustentarem a leitura. Leque livre e movimento secundário discreto.
- Vida: cabeça encontra o alvo antes da bacia; compressão legível, aceleração no contato,
  absorção da aterrissagem e penas acomodando depois do tronco. Evitar braços/pernas como pistões,
  pose idêntica congelada entre todos os golpes, tremor aleatório ou velocidade uniforme.

Faixa inicial para experimentar botes: aproximadamente 0,8–1,2 s, sem transformar essa estimativa
em requisito. Priorizar peso e leitura. Primeiro conferir três poses principais de perfil/3/4
e uma prévia simples no tempo real; só então refinar curvas, apoio/penas e assar as chaves finais.

## Referências novas e limites da analogia

- [Fowler et al., 2009 — morfologia e contenção de presas por aves de rapina](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0007999):
  a estratégia muda com tamanho da presa; pés, peso corporal e bico têm funções complementares.
  O F2 não é uma águia real, e ataques de passagem para farm são uma adaptação ao jogo.
- [O'Connor et al., 2014 — contribuição da cauda na locomoção pentápede](https://www.sfu.ca/locomotionlab/assets/oconnor-etal-kangaroo-tail-and-locomotion2014.pdf):
  medição experimental de suporte e propulsão por cauda muscular de cangurus. O estudo é de
  locomoção, não de combate; não demonstra que a cauda do F2 suporte seu corpo.

**Feito:** estudo do retorno, inspeção pontual do rig/cauda e proposta deste repertório.
Parada a prévia rejeitada e selecionada a bicotada aproveitável no Blockbench. Nenhum modelo,
animação ou exportação foi alterado nesta discussão. Documentação de retomada atualizada.

**Próximo passo recomendado:** experimentar primeiro o bote baixo/rasante em poses simples,
pois resolve o encontro frequente de farm e estabelece a identidade corporal. Testar a escora de
cauda antes de prometer a repulsão apoiada; sequência de captura longa fica como opção futura.
Continuar a conversa artística com o usuário; não tratar esta proposta como aprovada.
