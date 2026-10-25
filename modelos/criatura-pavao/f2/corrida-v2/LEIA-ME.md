# F2 — corrida v2, corpo acompanhando as passadas

Abrir `criatura-pavao-e2-corrida-v2.bbmodel` em Animate. Esta revisão atende ao
retorno sobre o corpo rígido da v1. A frequência continua em **0,72 s por ciclo**.

- Corpo comprime no apoio e sobe no impulso; deslocamento lateral acompanha a
  transferência de peso, com pequeno movimento para a frente/para trás.
- Bacia e tronco giram em contraposição; cintura e peito flexionam com tempos
  diferentes. O movimento deixa de se cancelar ao chegar à parte superior do corpo.
- Pescoço/cabeça respondem parcialmente ao impacto; cauda reage com atraso e os
  braços acompanham o ritmo, mantendo as lâminas presas aos antebraços.
- Patas recalculadas por IK para o quadril móvel. Mantidos os pontos de contato,
  a passada, o impulso dos dedos e a fase aérea. Recolhimento mais baixo dá espaço
  à compressão do corpo sem dobrar excessivamente as articulações.

No ciclo salvo, comparar `medidas-corrida.json`, seção `resposta_corporal`: o curso
vertical de `body` passa de aproximadamente 2,2 para 3,3 unidades; o balanço mundial
de pitch do peito passa de aproximadamente 1° para 5,5°. A cabeça também deixa de
ficar quase travada. A intenção é dar peso/elasticidade, com postura de corrida.

## Clipes

| Nome | Duração | Encaixe final |
|---|---:|---|
| `run` | 0,72 s, loop | volta à mesma pose/fase |
| `run_start` | 0,54 s | retomar `run` em 0,432 s |
| `run_stop` | 0,60 s | retomar `walk_blend` em 0,800 s |

Entrada/frenagem refeitas com o novo movimento corporal e os mesmos tempos/fases.
`idle`, `walk`, os três ataques e os aliases `walk_blend`/`idle_blend` são idênticos
à v1. Mesmos rig, 63 cubos/53 grupos, textura e UV. V1 e fonte manual preservadas.
Os detalhes de futura integração continuam no LEIA-ME da v1 e em `locomocao.json`.
Esta entrega contém somente animações/metadados para avaliação no Blockbench.

## Conferência

`medidas-corrida.json`: arquivo salvo, trajetória/apoio dos pés, piso opaco,
penas/pernas, fase aérea, loops, encaixes e comparação do movimento corporal.
As misturas de referência incluem compensação vertical offline; a reprodução
interrompível no jogo continua sendo uma etapa futura.

`validacao-*.json`: gates do motor. `proveniencia.json`/`balanco.ops.json`: hashes
e operações do motor externo. As fontes nunca são sobrescritas.

Prévias a 1×: `previa-corrida.gif`, `previa-transicoes.gif` e `comparacao-v1-v2.gif`.
Folha de poses em `poses-corrida.png`.

Gerar: `uv run python scripts/animar-balanco-corrida-pavao-f2-v2.py`.
Rever: `uv run python scripts/revisar-balanco-corrida-pavao-f2-v2.py`.
`--refazer` só aceita saída ainda idêntica à proveniência; edições manuais exigem
outra versão.
