# F3 — revisão do saque, descanso e saída de combate

Arquivo: `criatura-pavao-e3-combate-v2c.bbmodel`. Snapshot da aba do usuário em
`origem-revisada.bbmodel`. Mesma geometria de 93 blocos e mesma textura da v1b.
Avaliação artística pendente; esta entrega contém animações e metadados.

## Clipes

| Clipe | Duração | Uso |
|---|---:|---|
| `idle` / `walk` | 3,2 / 1,5 s | Aprovados; poses preservadas |
| `combat_enter` | 1,3 s | Saque parado, seguido do floreio e guarda pronta |
| `combat_enter_walk` | 1,3 s | Mesmo saque enquanto anda |
| `combat_enter_upper` | 1,3 s | Camada do saque, sem canais das pernas |
| `combat_ready` | 2,4 s, loop | Guarda armada; ambas as lâminas disponíveis |
| `combat_walk` | 1,8 s, loop | Uma lâmina no ombro; a outra arrasta no chão |
| `combat_walk_start` / `combat_walk_stop` | 0,6 s | Passagens entre guarda pronta e marcha |
| `combat_idle` | 7 s, sem loop | Cravar, soltar, descansar, recuperar e guardar |
| `combat_idle_resume` | 1 s | Recuperar a lâmina durante a pausa e retomar a guarda |
| `combat_exit` | 1,5 s | Guardar andando e continuar a marcha pacífica |
| `combat_exit_upper` | 1,5 s | Camada de guardar, sem canais das pernas |

O saque não contém o descanso. O floreio usa os punhos como pivô, com os braços,
peito e plumagem reagindo. O oito é inclinado para acomodar o comprimento das
grandes penas, mantendo as lâminas fora do tronco e do piso.

## Descanso parado

O `combat_idle` começa na guarda pronta: prepara e crava a espada direita,
solta a empunhadura e apoia a esquerda no ombro. Entre 1,1 e 4,1 s há três
segundos de respiração. Depois recupera a espada do chão e guarda as duas penas
na cauda. Termina na pose inicial de `idle`. A espada fica aproximadamente
metade abaixo do plano do solo, de forma intencional.

`combat_idle_resume` parte da pose da pausa e termina na guarda pronta. O futuro
controlador deve misturar a respiração da fase atual ao iniciar essa retomada;
os marcadores não implementam seleção de estados, alvos ou interrupção no jogo.

## Anatomia e vínculos

O ombro gira primeiro. O cotovelo usa um eixo de flexão/extensão calculado da
anatomia editada; os alvos não escolhem um novo plano arbitrário para a junta.
Ao retornar à marcha aprovada, há uma mistura curta para os canais já aprovados.

As penas 04/06 continuam sendo as mesmas peças. Seus controladores agora são
filhos das mãos: o vínculo é fixo quando empunhadas e compensado em chaves para
seguir a cauda ou permanecer no chão quando soltas. Não há cópias, trocas de
escala ou mudança de pai em execução. Os locators existentes continuam válidos.

Somente os canais desses controladores foram convertidos no idle/walk aprovados;
o relatório verifica que as poses em mundo permanecem iguais. A textura e a
geometria manual foram mantidas integralmente.

## Uso futuro das camadas

Os clipes `_upper` substituem os canais listados em `animacoes.json` sobre a
marcha pacífica. Não contêm raiz, corpo, bacia ou pernas. A postura foi transferida
para cintura/cauda e o vínculo das armas acompanha as mãos. A validação combina
essas camadas com 12 fases distintas da marcha e confere encaixes e pernas.

As prévias completas têm fases de início/fim registradas no manifesto. As
transições de caminhada começam na fase zero; a mistura entre estados/fases
arbitrárias permanece responsabilidade da futura integração.

## Conferência e reprodução

```powershell
uv run python scripts/animar-combate-pavao-f3-v2.py --preparar --animar
uv run python scripts/revisar-combate-pavao-f3-v2.py --validar --previas
```

Saída protegida por hash; alterações manuais exigem uma nova versão. A escrita
do modelo e das chaves passa pelo motor externo. Diagnósticos em `validacao*.json`.
O diagnóstico estrutural tem zero erros e 194 avisos de sobreposição/simetria;
a conferência direta preserva todos os blocos e a pintura da fonte. Nos clipes
sem enterro intencional, o validador de animação do motor não apresenta avisos.
As prévias possuem um piso auxiliar apenas no render, para mostrar a espada
enterrada. Nenhuma geometria de piso foi adicionada à criatura.

## Referência do floreio

[Wushu Ontario — Jian Wanhua](https://wushuontario.ca/?page_id=2462) descreve o
punho como pivô do oito da espada. A adaptação usa duas penas muito maiores que
uma espada de apresentação, arcos inclinados e reação do tronco. A referência
de Obi-Wan é a intenção gestual indicada pelo usuário, sem giro completo do corpo.
