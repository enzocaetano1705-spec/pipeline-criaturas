# F2 — corrida e transições v1

Abrir `criatura-pavao-e2-corrida-v1.bbmodel` no Blockbench, modo Animate.
Modelo, UV, atlas, hierarquia e os cinco clipes da v9 preservados. Esta é uma
proposta nova para avaliação; não substitui a fonte manual nem o modelo no Studio.

| Clipe | Duração | Uso |
|---|---:|---|
| `run` | 0,72 s, loop | Corrida com postura própria |
| `run_start` | 0,54 s | Andar → correr |
| `run_stop` | 0,60 s | Correr → andar |
| `walk_blend` | 1,20 s, loop | Walk com canais completos para a mistura futura |
| `idle_blend` | 2,40 s, loop | Idle com canais completos, sem escala de osso |

## Movimento

Tronco baixo e projetado, quadril/peito com contraposição, cabeça estabilizada,
cauda estendida como contrapeso e braços recolhidos. Os apoios alternam, com
compressão, impulso pela ponta dos dedos, recolhimento da pata e breve fase aérea.
Penas dos cotovelos seguem os antebraços; penas dos tornozelos abrem pela própria
raiz para liberar os pés. Nenhuma peça ou proporção nova.

A silhueta inclinada segue a referência cinematográfica solicitada. A mecânica
dos membros usa aves corredoras como referência; trata-se de uma criatura fictícia,
não de uma reconstrução científica de Velociraptor. A distinção apoio/balanço,
impulso distal e fase aérea se apoia no estudo de
[Rubenson et al. sobre corrida de avestruzes](https://pmc.ncbi.nlm.nih.gov/articles/PMC3061092/).

O `walk` original fica intacto. `walk_blend` reproduz suas curvas com chaves lineares,
abre ligeiramente as penas das pernas e compensa um pequeno afundamento preexistente
dos dedos. `idle_blend` também tem canais neutros para os ossos novos do rig; escala
de osso é omitida porque o Roblox não a reproduz. Ataques permanecem iguais à v9.

## Encaixes para a integração futura

As transições têm velocidade de progressão suave nas extremidades e conservam a
fase da passada. **Não reiniciar o loop no frame zero ao terminar uma transição.**

| Transição | Pose inicial | Pose final / ponto para retomar o loop |
|---|---|---|
| `run_start` | `walk_blend` em 0 s | `run` em 0,432 s, fase 0,60 |
| `run_stop` | `run` em 0 s | `walk_blend` em 0,800 s, fase 2/3 |

As transições são clipes de referência para esses apoios. Numa troca em outro ponto
da passada ou numa interrupção, o futuro controle precisará preservar a fase e
misturar a pose atual em vez de reiniciar esses clipes. Os loops têm contribuições
explícitas em todos os ossos para permitir isso. O Roblox oferece pesos e posição
de reprodução em [AnimationTrack](https://create.roblox.com/docs/reference/engine/classes/AnimationTrack).
Só os arquivos de animação e seus metadados foram preparados nesta entrega;
a lógica de pet/reprodução, a aceleração do deslocamento e os testes no Studio
ficam para outra etapa, conforme orientação do usuário.

`run_stop` termina em **walk**, não em repouso. Idle e parada completa poderão ser
conectados conforme o controle de movimento do jogo. As animações são no lugar:
o deslocamento físico futuro deve acompanhar a passada, não sair da MeshPart animada.

Em unidades do modelo, a corrida corresponde a 44,444 unidades/s e o walk a
11,111 unidades/s. Para studs/s: multiplicar por `escala_do_Model / 16`.
Esses números são referências de contato, não velocidades já aplicadas ao jogo.
Dados de fase/duração em `locomocao.json`; marcadores de combate preservados em
`animacoes.json`.

## Conferência e reprodução

- `medidas-corrida.json`: arquivo salvo, chão opaco, penas/pernas, trajetória dos
  pés, contato na esteira, fase aérea, costura dos loops e encaixes das transições.
  As misturas intermediárias do relatório incluem compensação vertical de referência
  offline; não comprovam o resultado de um controlador ainda não implementado.
- `validacao-estrutura.json` e `validacao-locomocao.json`: gates do motor.
- `previa-corrida.gif`: ciclo a 1×; `previa-transicoes.gif`: walk/partida/run/frenagem.
- `poses-corrida.png`: comparação com a postura de walk na mesma escala.
- `proveniencia.json` e `corrida.ops.json`: hashes e lote aplicado pelo motor externo.

Gerar: `uv run python scripts/animar-corrida-pavao-f2.py`.
Rever: `uv run python scripts/revisar-corrida-pavao-f2.py`.
`--refazer` só regenera uma saída ainda idêntica ao hash da proveniência;
uma edição manual exige outra versão.
