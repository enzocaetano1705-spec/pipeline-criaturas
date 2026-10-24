---
tipo: sessao
data: 2026-10-24
fase: 10
ia: codex
status: cauda-corrigida-chute-cedo-aguarda-avaliacao
---

# F2 v9 — chute no impulso e ataque mais curto

**Pedido ao usuário:** avaliar o ritmo de `attack_tail_kick` na nova v9:
`modelos/criatura-pavao/f2/ataque-v9/criatura-pavao-e2-ataque-v9.bbmodel`.
Arquivo aberto em Animate; prévia em `previa-ritmo.gif` a 1×.
Cauda/leque da v8 preservados; pisão e spin continuam aprovados.

## Retorno e execução

Usuário considerou a v8 quase perfeita. Com a cauda corrigida, percebeu que o chute
antecipado da v7 tinha melhor potência/timing. Pediu retomá-lo e acelerar levemente
a animação para ataques frequentes; a espera pela descida deixou de ser requisito.

- V9 de 2,15 s: ~24,56% menor que os 2,85 s da v8. Carga até 0,50 s, soltura 0,66 s,
  início da extensão ~0,636 s, impacto ~0,763 s, pouso 1,30 s e neutro em 2,15 s.
- Extensão/recolhimento retomam a v7, em relação à descarga. Peito, braços e cabeça
  retomam o acento e voltam à recuperação da v8 antes do pouso. O acento tardio
  fica suprimido para não produzir um segundo golpe.
- Recolhimento segura a orientação dos dedos até a preparação do pouso, liberando
  uma pena do tornozelo que era atravessada se os dedos relaxassem cedo demais.
- Corpo, quadril, apoio, cauda em J e leque reaproveitam as curvas salvas da v8,
  incluindo as amostras de apoio refinadas. Os tempos são remapeados por fase;
  inserções nas quebras do remapeamento preservam a interpolação.
- Nenhuma operação de rig, geometria, UV ou textura. 63 cubos/53 grupos; só
  `attack_tail_kick` substituído em cópia protegida por hash, com a v8 intacta.

## Conferência

Rig, elementos, outliner, atlas e curvas dos demais clipes são iguais à v8: isso
comprova o mesmo resultado em qualquer instante para idle/walk/pisão/spin, inclusive
suas curvas não lineares. Comparação densa dos cantos caudais entre fases equivalentes
da v8/v9 confere que a mudança de ritmo conserva a correção da cauda e do leque.

Arquivo salvo conferido por piso opaco, penas/pernas, leque/cauda, apoio, encaixes,
largura, repouso e continuidade. Extensão das patas no impacto e ocorrência antes
do ápice verificadas explicitamente. Os metadados antigos de golpe descendente
foram substituídos no relatório. Resultados em `medidas-ritmo.json` e
`aprovados-preservados.json`, com tolerâncias da v8.

Resultado salvo: desvio máximo dos cantos caudais ~0,0000585 unidade nas mesmas
fases; erro da extensão no impacto ~0,0000146. Novos contatos pena/perna máximos
~0,00902 unidade; piso mínimo Y=0,08136 para chão Y=0,08741. Continuidade máxima
de Euler entre chaves ~13,35°. Ápice em ~1,017 s, depois do impacto de ~0,763 s.

Motor: estrutura sem erros/avisos; ataque sem erros ou juntas soltas. Aviso de
retângulo transparente de `fan_5` abaixo do piso, distinguido pelo teste de alfa.
Prévia: 2,15 s a 50 fps, mais 0,30 s de pausa. Carga e impacto conferidos no Blockbench.

Scripts `animar-ritmo-cauda-pavao-f2-v9.py` e `revisar-ritmo-cauda-pavao-f2-v9.py`;
lote em `ritmo.ops.json`, mapa de tempos/hashes em `proveniencia.json`.

**Próximo:** avaliação do ritmo/feeling da v9, seguida da integração/exportação dos
movimentos aprovados. Não adotada no Roblox; nenhuma definição de dano/física de
gameplay ou mudança de arquitetura/dependências. Fonte manual e arquivos alheios
à revisão ficam preservados e fora do commit.

Commit: `Retoma chute no impulso e encurta ataque do F2 para 2,15 segundos` (consultar git log).
