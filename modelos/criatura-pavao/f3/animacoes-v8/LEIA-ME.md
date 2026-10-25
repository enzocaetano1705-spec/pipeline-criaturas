# F3 — transições, descanso e saída de combate

Base aprovada: `../animacoes-v7/criatura-pavao-e3-combate-v7.bbmodel`.
Modelo: `criatura-pavao-e3-combate-v8.bbmodel`.

Preservados integralmente: `idle`, `walk`, `combat_ready`, `combat_walk` e
`combat_enter`. Mesma geometria, textura, UVs, hierarquia e pivôs.

## Animações completadas

| Clipe | Duração | Movimento |
|---|---:|---|
| `combat_enter_walk` | 1,65 s | Saque aprovado durante a marcha; floreio só da esquerda, que termina no ombro; direita termina no arrasto. |
| `combat_enter_upper` | 1,65 s | Camada superior do saque para composição com a locomoção. |
| `combat_walk_start` | 0,60 s | Aceleração da guarda parada até a marcha de combate. |
| `combat_walk_stop` | 0,60 s | Desaceleração da marcha até a guarda parada. |
| `combat_idle` | 7,15 s | Cravar e soltar a direita, descansar três segundos, recuperar e guardar ambas na cauda. |
| `combat_idle_resume` | 1,10 s | Recuperar a espada solta e retornar à guarda com as duas armas. |
| `combat_exit` | 1,80 s | Guardar as penas enquanto caminha e retornar à marcha pacífica. |
| `combat_exit_upper` | 1,80 s | Camada superior da saída. |

Todos são clipes de execução única. A `combat_ready` aprovada continua sendo
a guarda em loop; `combat_idle` é a sequência de descanso e saída parada.

## Descanso

1. Parte da guarda aprovada, com a esquerda no ombro.
2. A direita varre por fora do corpo, sobe e é cravada com reação do tronco,
   pescoço, cauda e penas. Aproximadamente metade da lâmina fica enterrada.
3. A mão solta a arma; ela permanece imóvel no mundo enquanto a criatura
   respira. A pausa vai de 1,25 a 4,25 s.
4. Reagarra e recupera a direita, retornando à guarda em 5,35 s.
5. Guarda as duas penas nos encaixes originais da cauda, encerrando no `idle`.

A compensação da espada solta está nas chaves do próprio rig. O modelo
não ganhou cópias de armas nem alterações de tamanho.

## Composição futura

`animacoes.json` contém fases de conexão, máscara superior e marcadores de
preensão, soltura, descanso e encaixe. As camadas superiores substituem os
canais da máscara; não são aditivas. As prévias dessas camadas compõem a
marcha pacífica para mostrar a intenção.

As conexões verificadas usam as fases declaradas. Interrupções em uma fase
arbitrária exigirão mistura dos estados na integração futura. A retomada
parte da pausa do descanso; ela recupera a arma antes de voltar à locomoção.
Este pacote prepara as animações; a lógica do pet permanece para depois.

## Reprodução e conferência

```powershell
uv run python scripts/animar-combate-pavao-f3-v8.py --estudo
uv run python scripts/animar-combate-pavao-f3-v8.py --animar --validar
uv run python scripts/animar-combate-pavao-f3-v8.py --previas --folha
```

Escrita em lote pelo motor externo e saída protegida por hash. Relatórios
em `validacao.json` e `validacao-motor*.json`; GIFs ao lado do modelo e folha
em `poses.png`. Avaliação artística dos oito clipes novos pendente.
