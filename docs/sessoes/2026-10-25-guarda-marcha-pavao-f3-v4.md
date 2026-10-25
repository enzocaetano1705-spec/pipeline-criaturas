---
tipo: sessao
data: 2026-10-25
fase: 10
ia: codex
status: aguardando-revisao-artistica
---

# F3 — marcha aprovada vira a postura da guarda

**Avaliação para o usuário:** conferir a nova `combat_ready` e o final do
`combat_enter` na v4. `combat_walk` aprovada e preservada integralmente.

**Retorno:** usuário considerou a marcha perfeita e o saque sensacional.
A nova guarda deve ser a postura da marcha, parada, com uma espada no ombro
e outra no arrasto. Depois da extração conjunta, cada braço segue seu gesto:
a espada do chão vai direto ao arrasto; só a do ombro faz o floreio e repousa.

**Lados:** confirmado com o usuário manter os mesmos braços da marcha aprovada.
No rig, esquerdo sustenta a espada no ombro e direito sustenta a do chão.
Não inverter a marcha em resposta à descrição visual inicial dos lados.

**Feito:** fonte v3 preservada; saída nova em `f3/animacoes-v4/`.
Somente `combat_ready` e `combat_enter` substituídos. Demais onze clipes,
incluindo a marcha aprovada, mantêm os mesmos canais e tempos. Geometria,
textura, UVs e hierarquia preservados.

**Guarda:** 2,4 s, com o quadro zero exatamente igual à marcha no tempo zero.
Mesma inclinação corporal, patas escalonadas, uma espada apoiada no ombro e
outra no chão. Respiração discreta de corpo, pescoço, cauda e plumagem;
recalcula apoio das solas e da espada sem descolar as wings.

**Saque:** 2,1 s. Até 0,50 s mantém a extração aprovada. A espada do chão segue
para o arrasto até 0,90 s. A do ombro mantém a volta de 360° aprovada em
1,15–1,68 s, inclinada 30° para fora, e passa a repousar sobre o ombro em
1,70–2,10 s. Dois passos curtos acomodam as patas na base da marcha.
O final coincide com a nova guarda parada.

**Verificações:** chaves salvas a 240 amostras/s: clipes preservados,
guarda igual à marcha, contato da espada no piso, floreio em um só braço,
preservação do floreio aprovado, empunhadura, wings, eixos/limites das juntas,
apoio dos pés, continuidade e conexões. Relatórios e prévias na pasta da v4.
Todas as verificações passaram. Motor de animação: zero erros e zero avisos
nos dois clipes revistos. Guarda/marcha em quadro zero: desvio de matriz zero;
contato da espada de descanso com erro inferior a 0,000018 unidade.
V4 aberta e conferida no Blockbench via MCP, com `combat_ready` selecionada.
O validador comum ganhou parâmetros opcionais para conferir floreio unilateral;
o comportamento padrão da v3 continua verificando as duas espadas.

**Problema corrigido na revisão:** a troca do gesto para o ombro começava entre
duas chaves de 120 Hz e afetava a interpolação do último instante do floreio.
A recuperação começa agora numa chave em 1,70 s, depois da volta completa.

**Decisões:** revisão das animações desta criatura, sem mudança de arquitetura,
formato ou dependências. Fonte/edições do usuário preservadas. Sem ações no
Roblox Studio. Base anterior: commit `1415c2d`. Fase 10 continua aberta.

**Próximo:** avaliação da guarda e do final do saque; depois derivar os clipes
adiados desta postura. Não considerar start/stop, variantes andando, camadas,
descanso ou saída anteriores automaticamente adaptados à nova base.
