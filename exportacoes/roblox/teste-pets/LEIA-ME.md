# Laboratório de pets — testesblockbench.rbxl

Teste local solicitado pelo usuário para comparar F1/F2/F3 no motor. Fontes em
Luau, sem dependências ou publicação de animações, sem DataStore. Os modelos
originais permanecem na pasta `criaturas modeladas blockbench`; o laboratório usa
cópias em namespaces marcados com `PetTestOwned`.

## Controles

- **F1 / F2 / F3** na interface: trocar forma. O nível é mantido.
- **Shift** pressionado: jogador corre; pet troca para corrida. Soltar desacelera.
- **Clique no cubo vermelho**: selecionar alvo e começar ataques automáticos.
- **R / Recall**: cancelar dano pendente e retornar ao acompanhamento.
- **Q / Área**, apenas F2: executar spin, cooldown de **3 segundos desde o início**.
  Se já estiver atacando, aguarda o golpe terminar. Recall cancela a fila.
- **F3: sequência**: alternar entre sequência Low → Left → Combo e cada golpe
  isolado. Todos podem ser ensaiados nos dois tamanhos de alvo.
- **− / +**: nível de 1 a 100 para comparar dano. Eliminações também concedem XP.
- **Restaurar HP**: reiniciar os cubos; após morrer, renascem em 3 segundos.

F2 usa pisão no cubo pequeno e catapulta no grande. O spin é a única skill.
F1 ainda não tem clipes de ataque/corrida: neste laboratório usa walk acelerado e
uma investida curta provisória para causar dano, claramente indicada no status.

## Instalar / atualizar

1. Importe os GLBs atualizados de `../pavao/` pelo importador 3D, rig **Custom**.
   Importação e upload de assets são ações humanas, conforme o guia do pipeline.
2. Adote cada nova revisão na pasta ativa, preservando a anterior no histórico.
   Execute sua receita `Pavao_Fx-preparar.luau`. Preserve a escala manual do F2.
3. `uv run python scripts/gerar-teste-pets.py` na raiz atualiza Config e Instalar.
4. Execute `Instalar.luau` no MCP **Edit** ou barra de comandos, com Play parado.
   A execução via MCP usa a gravação de histórico já aberta pela ferramenta;
   pela barra de comandos inicia sua própria gravação.
5. Aperte Play. A interface só libera formas com hash de fonte e todos os clipes
   exigidos. Reinstale em Edit depois de preparar uma nova importação.

O instalador recusa nomes ocupados por objetos externos. Reinstalação substitui
apenas seus scripts, templates, clipes compartilhados e alvos. Não remove uploads,
não publica o place, não modifica a geometria nem os clipes da fonte artística.

## Organização

- `ReplicatedStorage.PipelinePetTest`: Config, AnimationDriver, remotes e animações
  compartilhadas por forma, evitando clonagem de milhares de Poses a cada pet.
- `ServerStorage.PipelinePetTestTemplates`: rigs preparados, sem clipes duplicados.
- `ServerScriptService.PipelinePetTest`: servidor e criação dos alvos.
- `StarterPlayer.StarterPlayerScripts.PipelinePetClient`: interface e reprodução.
- `Workspace.PipelinePetTest`: alvos no Edit e pets durante Play.

O movimento usa a frente da Hitbox e o chão sob o body; não a orientação da malha
nem a altura da pequena peça de referência. Aceleração, frenagem e crossfades
interrompíveis tratam mudanças frequentes de Shift. Os offsets de fase de chegada
vêm dos metadados dos clipes. A F3 usa as camadas superiores de saque/guarda sobre
locomoção; Poses estruturais fora da máscara têm peso zero, preservando as pernas.
Ataques completos têm prioridade maior. Colisores continuam seguindo os Bones.

Dano, cooldown, nível e seleção são validados no servidor; o cliente só solicita
comandos e reproduz feedback/animações. Os instantes de dano seguem HitFrame;
Combo tem dois impactos. Distância de ataque é uma aproximação para ensaio, sem
colisão exata do fio da espada. Caminho direto sobre piso simples, sem Pathfinding.

IDs temporários de KeyframeSequence são registrados em cada cliente para teste
no Studio. Para publicar um jogo, será necessário publicar as animações e trocar
esse carregamento por IDs autorizados; não confundir este laboratório com a
integração final de NPCs. Referência: [KeyframeSequenceProvider](https://create.roblox.com/docs/reference/engine/classes/KeyframeSequenceProvider).

## Conferência no Play

Verificar troca das três formas, Shift curto/repetido, parada, seleção de ambos os
cubos, HP/dano nos marcadores, Q e cooldown, cancelamento por R, nível, respawn do
jogador e retorno ao Edit sem erros. A aprovação visual dos ataques exportados
continua sendo uma avaliação separada da implementação do laboratório.
