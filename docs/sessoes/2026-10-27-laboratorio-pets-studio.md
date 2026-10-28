---
tipo: sessao
data: 2026-10-27
fase: 11
ia: codex
status: instalado-testado-no-studio
---

# Laboratório de pets no Roblox Studio

**Ação manual restante:** salvar o arquivo local com **Ctrl+S**. A janela do Studio
estava minimizada e o controle de janela recusou ativação por intervenção do
usuário (`window is minimized` / `user input was detected`). As alterações foram
confirmadas no DataModel em Edit; gravação do `.rbxl` em disco não foi confirmada.

**Feito:** usuário pediu sistema básico de teste e confirmou explicitamente
`testesblockbench.rbxl` antes das alterações. O Blockbench MCP foi reativado pelo
usuário e F2/F3 importadas por ele pelo importador 3D; sem contornar uploads.

- F3 `ataques-v7` exportada: 22 clipes, 1.116 triângulos, UV [0,1], validador
  Khronos sem erros/avisos. GLB SHA-256
  `6c907ec5bb750a1927594f2372bc8161af0d69d625fdde75a180a3d66d9b43c8`.
- F2 atualizada: 10 clipes, escala manual **5,899576664** preservada. A antiga
  com só idle/walk foi movida reversivelmente para
  `ServerStorage.PipelinePetTestHistory.Pavao_F2_anterior_1793149499`.
- F1 preservada em escala 3,510144711; F3 em escala 3 do registro. Nenhuma fonte
  `.bbmodel` ou textura editada à mão foi sobrescrita.
- Receitas aplicadas: mapas importados preservados, Pixelated, colisores compostos
  acompanhando Bones (F2: 158; F3: 155). F3 sem script de prévia concorrente.
- Namespace `PipelinePetTest`: cópias dos rigs, biblioteca compartilhada de clipes,
  servidor de comandos/combate, interface e driver local com prioridades/mistura.
  Originais mantidos na pasta ativa; nenhuma publicação do place/animações.
- Shift corre; pet segue com aceleração/frenagem e transições interrompíveis.
  R cancela impactos pendentes e retorna ao jogador. Alvos vermelhos pequeno/grande
  com HP, números de dano e respawn; seleção por clique. Nível/XP e controles −/+.
- Q executa spin F2 com cooldown de 3 s e fila após golpe atual. F2 usa pisão no
  pequeno e catapulta no grande. F3 alterna Low/Left/Combo, também isoláveis no HUD.
  F1 usa caminhada acelerada e investida provisória: faltam clipes próprios.

**Problemas e correções:** exportação F3 excedia o teto de resposta MCP de 2 MB.
O exportador aguarda projeto ativo e usa arquivo temporário nativo quando o GLB
não vem embutido; falha não pode reutilizar arquivo antigo como falso sucesso.
Camadas superiores têm peso zero nos pais estruturais fora da máscara, preservando
as pernas. IDs temporários são registrados por cliente e reaproveitados por fonte.
Clipes comuns são pré-carregados entre frames. Barras/números são projetados no
HUD a partir dos cubos; espera explícita pelo Cubo evita corrida de replicação.
A tolerância de chegada ficava fora do alcance em alvos pequenos: margem corrigida
e F1/F3 retestadas com dano real no cubo pequeno.

**Conferência:** `uv run pytest ferramenta/testes/test_roblox_regressoes.py
ferramenta/testes/test_roblox_infra.py -q`: **14 passaram**. Sintaxe dos scripts
conferida no Studio e ensaios no Play, com console final sem erros:

- Interface seleciona as três formas. Shift: jogador 28, solto 16; pet corre e
  volta a velocidade zero/idle após mudanças rápidas de Shift.
- F1 pequeno: quatro impactos de 6 no ensaio final.
- F2 pequeno: pisão 14; spin 22 nos dois cubos no mesmo instante. HUD contou
  cooldown e nova solicitação durante a recarga não disparou outro spin.
  F2 grande: catapulta 24. R impediu novos impactos após cancelar.
- F3 pequeno, nível 1: Low 22, Left 28, Combo 22+44. Mesma sequência atingiu o
  grande no ensaio anterior (nível 2: 23, 30, 23+47). Sem Right.
- `combat_enter_upper` e `combat_run_start`/`combat_run` tocaram juntos durante
  aproximação com corrida. Respawn recriou um único pet, forma mantida, speed 16.
- Textura colorida observada no Studio e HUD/HP conferidos por captura. Aprovação
  artística do movimento no motor depende do retorno do usuário, não destes números.

**Limites:** movimento direto em piso simples, sem Pathfinding. Dano por alcance
aproximado/HitFrame, sem colisão exata do fio. Nível/XP só da sessão de teste.
Animações locais do Studio; publicação de IDs e integração multiplayer do jogo
principal permanecem futuras. Não foi iniciada nova arquitetura do projeto.

**Próximo passo:** usuário abrir Play e avaliar visualmente a integração. Usar
`exportacoes/roblox/teste-pets/LEIA-ME.md` para controles e reinstalação. Studio
deixado em Edit ao terminar. Sem tag de conclusão das fases 10/11.
