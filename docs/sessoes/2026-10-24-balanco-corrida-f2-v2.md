---
tipo: sessao
data: 2026-10-24
fase: 10
ia: codex
status: revisao-entregue-aguarda-avaliacao
---

# F2 — corrida v2 com resposta do corpo

**Pedido ao usuário:** avaliar a corrida v2 em
`modelos/criatura-pavao/f2/corrida-v2/criatura-pavao-e2-corrida-v2.bbmodel`.
Aberta no Blockbench, Animate, `run` em loop. Comparação a 1× em
`corrida-v2/comparacao-v1-v2.gif`; sequência com partida/frenagem em
`previa-transicoes.gif`.

## Retorno e ajuste

O usuário apontou que o corpo da v1 ficava estável demais, dando a impressão de
pernas aceleradas isoladamente. O principal cancelamento acontecia no peito e na
cabeça: as oscilações dos segmentos quase se anulavam no mundo.

- Mais compressão/impulso vertical e deslocamento lateral de peso, com pequeno
  avanço/recuo do tronco ao longo da passada.
- Contraposição de bacia/cintura e flexão do peito em fases diferentes; pescoço
  e cabeça compensam parcialmente, mantendo resposta visível ao impacto.
- Cauda responde com atraso, braços acompanham e penas longas seguem rigidamente
  seus antebraços, com os vínculos corrigidos anteriormente.
- Pernas recalculadas por IK para acompanhar o quadril móvel sem alterar os
  apoios, a passada ou a frequência. Recolhimento mais baixo permite a compressão
  sem fechar excessivamente as articulações.
- `run_start` e `run_stop` refeitos para o novo balanço. Durações 0,72/0,54/0,60 s
  e fases de saída 0,60/2⁄3 mantidas.

Mesmos 63 cubos/53 grupos, rig, atlas e UV. Sete clipes idênticos à fonte v1:
idle, walk, três ataques e os aliases walk_blend/idle_blend. Apenas os três clipes
de corrida substituídos numa nova cópia. V1 e arquivo manual permanecem intactos.
Escopo continua sendo somente animações para avaliação no Blockbench; nenhuma
ação no Roblox Studio nem lógica de pet/reprodução.

## Conferência

Arquivo salvo medido a 240 amostras/s, comparado com a v1:

- Curso Y do corpo: 2,2 → 3,3 unidades; pitch mundial do peito: ~0,98° → ~5,49°.
- Roll do peito: ~1,90° → ~5,84°; yaw: ~0,70° → ~3,37°.
- A cabeça deixa a compensação quase total; pitch mundial ~0,58° → ~6,13°.
- Piso opaco Y≈0,08741, sem novas penetrações pena/perna nos clipes e nas misturas
  de referência. Erro de trajetória dos dedos ≈0,02928 unidade; deriva de apoio
  por amostra ≈0,001043 unidade. Fase aérea, loops e encaixes conferidos.
- Estrutura/animações no motor: 0 erros/0 avisos; sem juntas soltas.

As misturas de referência usam compensação vertical offline; não são validação
de reprodução no Roblox. A futura implementação de comandos interrompidos continua
fora desta entrega, conforme orientação do usuário.

Scripts `animar-balanco-corrida-pavao-f2-v2.py` e
`revisar-balanco-corrida-pavao-f2-v2.py`; operações, hashes, medidas, validações,
folha e prévias na pasta `corrida-v2`. Reutilizados o motor e os revisores existentes;
nenhuma mudança de arquitetura/dependências.

**Próximo:** avaliação artística do balanço e das transições da v2 no Blockbench.
Integração/exportação somente quando solicitada.

Commit: `Dá balanço ao corpo do F2 na corrida e ajusta as transições` (consultar git log).
