---
tipo: sessao
data: 2026-10-24
fase: 10
ia: codex
status: pisao-spin-aprovados-impulso-cauda-aguarda-avaliacao
---

# F2 v6 — carga, impulso da cauda e golpe aéreo

**Retorno posterior:** usuário pediu corrigir a dobra em L, transferir de fato o corpo sobre
a cauda e aumentar bastante o salto. A interpretação de peito como Y fixo foi corrigida.
Esta revisão é histórica; proposta atual em [[2026-10-24-catapulta-f2-v7]].

**Pedido ao usuário:** avaliar somente `attack_tail_kick` no arquivo
`modelos/criatura-pavao/f2/ataque-v6/criatura-pavao-e2-ataque-v6.bbmodel`, aberto em Animate.
Pisão e spin já aprovados, sem necessidade de nova avaliação. Prévia a 1× em `previa-impulso.gif`.

## Retorno

O usuário aprovou o spin v5 e pediu corrigir a relação anatômica de `hips`/`TorsoHips` com a cauda.
O ataque anterior ainda parecia apenas apoiar e chutar. A nova direção exige carregar o peso
na cauda, comprimi-la e usá-la como mola: impulso para a frente, pequeno salto e golpe das
duas patas à altura equivalente ao peito em repouso, aproveitando o movimento do corpo.

## Feito

- Nova v6, alterando apenas o ataque de cauda; duração 2,10 s, uma execução, chaves a 120 Hz.
- `pelvis` liga `hips` à raiz da cauda. `waist` articula `TorsoHips` pela união traseira dentro
  de `hips`, e carrega peito/pernas. IK usa o referencial real dessa ligação.
- Carga sobre a cauda sólida, patas recolhidas, curva carregada e extensão antes da soltura.
  Movimento aéreo recebe a velocidade da extensão no último instante de apoio, sem recomeçar do zero.
- Salto de ~0,70 a 1,12 s, avanço ~6,72 unidades Blockbench, duas patas à altura do peito base,
  recolhimento, pouso, absorção e recuperação com passos. Braços/tronco/cabeça acompanham a carga.
- Sem escala dos segmentos ou contração do leque. 59 cubos/48 grupos, geometria/UV/textura
  e repouso iguais à v5. Ops, scripts, marcadores propostos, relatórios, folha e GIF entregues.

## Verificação e problemas contornados

- Preservação de aprovados: chaves/curvas originais do pisão e spin iguais à v5;
  comparação geométrica nos 59 cubos a 240 Hz com **desvio zero** em ambos.
- Juntas quadril/ligação do torso/peito/cauda continuam dentro dos volumes que ligam;
  erro numérico máximo <7,2e-15 unidade. Não apenas pivôs coincidentes no vazio.
- Apoio sólido da cauda até 0,70 s; patas livres durante a carga. Fase completamente aérea
  ~0,704–1,113 s; altura do peito base Y=22,12025, erro máximo do golpe 0,01624 unidade.
- A trajetória usa velocidade herdada da descarga (+15 Y/−16 Z unidades/s); parâmetros
  são de animação em unidades do modelo, não a gravidade/runtime do Roblox.
- Chão mínimo visível Y=0,083084 (piso 0,087410); contatos de penas/pernas sem acréscimo
  significativo nas amostras opacas (máximo 0,00242 unidade).
- Estrutura sem erros/avisos e ataque sem erro/junta separada no motor. Aviso de caixa
  transparente de `fan_5` na soltura; medição dos cantos dos texels opacos passa pelo chão.
- Curvas de descarga com velocidade contínua na soltura e recuperação aérea da cauda.
  Piso/interpolação, orientação, pose inicial/final e abertura do leque conferidos no arquivo salvo.
- Carga e impacto conferidos no viewport nativo do Blockbench. Naturalidade continua sujeita
  à avaliação artística do usuário; o efeito de mola é a coreografia fictícia solicitada.

## Decisões

Dois grupos neutros no rig específico da criatura; sem alteração de formato/dependências
ou arquitetura do pipeline. Referências de movimento da v5 reutilizadas, sem repetir pesquisa.
Não exportado/adotado no Roblox nesta revisão. Gameplay e trajetória do modelo físico são etapa futura.

**Próximo:** retorno artístico sobre o impulso de cauda; depois integrar os movimentos aprovados.
Fonte manual, v5 e arquivos do usuário permanecem protegidos e fora deste commit.

Commit: `Cria impulso elástico de cauda do F2 e preserva ataques aprovados` (consultar git log).
