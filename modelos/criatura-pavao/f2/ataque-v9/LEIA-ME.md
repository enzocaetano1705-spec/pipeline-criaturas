# F2 v9 — chute no impulso, ataque de 2,15 s

Avaliar somente `attack_tail_kick`. O usuário considerou a v8 quase perfeita e pediu
retomar o tempo/força do chute da v7, com menos espera, além de encurtar a animação
para uso repetido. A forma corrigida da cauda da v8 foi mantida.

## Ritmo

| Fase | v8 | v9 |
| --- | ---: | ---: |
| Fim da carga | 0,62 s | 0,50 s |
| Soltura da cauda | 0,82 s | 0,66 s |
| Impacto das patas | 1,424 s | 0,763 s |
| Pouso | 1,70 s | 1,30 s |
| Fim da animação | 2,85 s | 2,15 s |

Redução total de ~24,56%. A extensão das patas começa ~0,636 s: perto da descarga,
com impacto durante a subida. O acento de peito, braços e cabeça retoma a v7 e
se mistura novamente à recuperação da v8. O recolhimento mantém os dedos em
posição que libera a plumagem dos tornozelos.

## Preservação

Mesmo rig, 63 cubos/53 grupos, geometria, UV e atlas da v8. Nenhuma operação de
geometria/rig; somente `attack_tail_kick` foi substituído. Idle, walk, pisão e spin
mantêm exatamente as curvas originais sobre o mesmo rig/elementos.

As curvas de corpo, quadril e cauda da v8 foram reaproveitadas, incluindo as amostras
refinadas de apoio. Seus tempos foram remapeados por fase, com inserção das quebras
do remapeamento. A conferência compara os mesmos cantos da cauda e das penas entre
v8/v9 em fases correspondentes, além dos contatos por alfa e da extensão do chute.

## Arquivos e reprodução

- `criatura-pavao-e2-ataque-v9.bbmodel`: proposta para avaliação no Blockbench.
- `previa-ritmo.gif`: 1×, duas vistas, animação de 2,15 s mais pausa final de 0,30 s.
- `poses-ritmo.png`: carga, descarga, impacto cedo, recolhimento, pouso e neutro.
- `medidas-ritmo.json`: conferência do arquivo salvo; tempos expressos na v9.
- `aprovados-preservados.json`: igualdade de curvas/rig/elementos dos demais clipes.
- `ritmo.ops.json`: lote aplicado pelo motor externo.
- `animacoes.json`: marcadores propostos, ainda não integrados ao gameplay.
- `proveniencia.json`: hashes, fontes e mapa de tempos.
- `validacao-estrutura.json` / `validacao-ataque.json`: diagnósticos do motor.

```powershell
uv run python scripts/revisar-ritmo-cauda-pavao-f2-v9.py
```

Gerador: `scripts/animar-ritmo-cauda-pavao-f2-v9.py`. `--refazer` só substitui uma
saída própria com hash íntegro e a mesma fonte. Fonte manual e versões anteriores
ficam protegidas. Nenhuma exportação/adoção no Roblox nesta revisão.

Tolerâncias herdadas da v8: 0,05 unidade para novos contatos opacos, 0,025 para piso,
0,002 para diferença dos cantos caudais após remapear tempos. Inserções de penas
existentes em repouso são descontadas; não se alega contato matematicamente nulo.
O aviso genérico de chão inclui regiões transparentes e é conferido por alfa.
