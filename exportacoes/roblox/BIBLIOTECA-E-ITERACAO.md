# Biblioteca e iteração de criaturas

## Usar pastas e atualizar uma versão

No Studio, abra **Window → Asset Manager → My Inventory**. O inventário pessoal é o lugar adequado
para organizar uploads antigos de vários projetos. Crie pastas como `Criaturas/Aprovados`,
`Criaturas/Testes`, `Criaturas/Historico` e `Outros projetos`.

O Asset Manager permite selecionar vários itens, agrupá-los numa pasta e arrastar a seleção para outra
pasta do mesmo inventário. Para reorganizar, navegue até a pasta: arraste/movimentação ficam desativados
nos resultados de busca, e `Recent Uploads` é uma vista de organização somente leitura.
Não foi confirmada seleção por retângulo nessa interface.
[Documentação oficial](https://create.roblox.com/docs/projects/assets/manager).

Para testar uma nova versão, use **Reimport** no Model existente (`Alt+Shift+R`). O Studio lembra o
arquivo e as opções; nomes e hierarquia estáveis permitem atualizar as malhas correspondentes.
Depois, execute novamente a receita de preparo. Isso precisa ser validado com o rig do projeto;
não foi feito um reimport automatizado nesta sessão.
[Documentação oficial](https://create.roblox.com/docs/art/modeling/reimport).

Atualizar o Model existente evita acumular cópias no Explorer. Reimport não executa uma limpeza do
inventário online; a retenção dos uploads continua sendo uma tarefa separada.

No Explorer, duplicar/copiar um Model reaproveita os IDs de malhas e imagens. Remover uma instância
do place não remove o upload da conta. Arquivamento online afeta a disponibilidade do asset em jogos;
primeiro é necessário identificar seu uso. O histórico local deste pipeline só move Models para
ServerStorage, preservando os uploads.
[Gestão e arquivamento de assets](https://create.roblox.com/docs/projects/assets).

## Fonte, exportação e revisão

1. A fonte editável continua no `.bbmodel` e seu histórico local/Git.
2. `criaturas.json` registra a criatura, fonte, estágio, escala e opções de exportação.
3. `uv run python scripts/exportar-roblox.py [Nome]` gera o GLB e `Nome-importacao.json`.
4. `uv run python scripts/preparar-roblox.py [Nome]` gera `Nome-preparar.luau` e o catálogo.
5. Na primeira importação, o usuário importa o GLB com rig Custom. Para as seguintes, priorize Reimport.
6. Rode a receita correspondente no Studio, por MCP ou barra de comandos; confira textura, walk e colisão.

Os GLBs atuais não mudaram nesta etapa de infraestrutura; não é preciso importá-los novamente.
O preparo físico já foi reaplicado nos dois pavões, mantendo as escalas/posições editadas pelo usuário.

Cada manifesto liga a fonte, o GLB e a configuração por SHA256. A geração de receita recusa fonte,
exportação ou configuração desatualizada. O Model preparado recebe `PipelineCriaturaId`,
`PipelineFonteSHA256`, `PipelineGLBSHA256` e `PipelineColisao`.

As receitas geradas usam a escala do registro para novas importações. Para instâncias que o usuário
já redimensionou, gere com `--preservar-escala`. A receita lê o perfil físico da fonte; ela não mede a
crista/asa/cauda para decidir o bloqueio do personagem.

## Operações em lote no place

`gerenciar-criaturas.luau` trabalha com a seleção de Models no Explorer. A ação padrão é **AUDITAR**,
que retorna um inventário dos ativos, histórico e outros Models soltos. Para executar outra ação,
troque `ACAO` no começo do script ou peça à IA para rodar pelo MCP:

| Ação | Resultado |
|---|---|
| `ADOTAR` | Coloca as importações selecionadas na pasta ativa e guarda as revisões anteriores. Rodar preparo depois. |
| `ARQUIVAR` | Move os Models preparados selecionados para o histórico em ServerStorage. |
| `RESTAURAR` | Restaura revisões selecionadas se não existir um ativo com o mesmo ID. Rodar preparo depois. |

O script verifica o lote antes de mover itens. Recusa IDs fora do registro, seleções repetidas da mesma
criatura e conflitos de restauração. Mantém nomes originais e usa sufixos únicos no histórico.
O lote participa do Undo do Studio; quando o MCP já possui uma gravação, a gravação externa é usada.
Não executa exclusão permanente, limpeza de RBX_ANIMSAVES nem arquivamento de assets da conta.

A consulta de inventário em `auditorias/2026-10-23-inventario.json` retornou 16 Models e 20 Images
(limite por tipo do conector). Nomes iguais não comprovam conteúdo duplicado. A ausência de referência
neste place não comprova que o asset pode ser removido de outros jogos.

## Perfis de colisão

O perfil é escolhido por criatura. **F1 e F2 usam o perfil composto v2.** O usuário aprovou o resultado
do F2 e pediu o mesmo acompanhamento de animação no F1. A caixa simples v1 permanece disponível para
outros casos. A malha visual continua sem colisão nos dois pavões.

### Caixa simples v1

No perfil v1, `Hitbox` é o bloqueio de locomoção e o PrimaryPart. Seu envelope usa os volumes 3D diretamente no
osso `body`, excluindo planos e ossos filhos. O envelope desce até a base da malha para apoiar o NPC
no chão. É um bloqueio estático aproximado do corpo, não uma superfície exata de cada pena/perna.

Para outra anatomia, configure no registro, por exemplo:

```json
"colisao": {"osso": "body", "cubos": ["hips", "torso", "shoulders", "TorsoHips"]}
```

Sem `cubos`, entram todos os volumes sólidos diretamente nesse osso. Se o osso ou os volumes não
existirem, a geração para com erro; a ferramenta não inventa uma forma física. Esta v1 é para criaturas
terrestres do pipeline Bedrock 5.0 e depende do registro e das convenções. Novas anatomias e formatos
precisam de conferência; não é uma garantia de compatibilidade com qualquer arquivo arbitrário.

O Roblox anima a aparência por Bones sem atualizar a forma física da malha. A caixa v1 fica parada
durante esse movimento. No v2, o módulo atualiza peças físicas separadas a partir da pose; o salto
do F1 passou a mover também essas superfícies. Montaria e caixas de dano exigem comportamento de gameplay.
[Rigging e colisão](https://create.roblox.com/docs/art/modeling/rigging).

### Colisão composta v2

```json
"colisao": {"tipo": "composta_ossos", "planos_alfa": true, "espessura_planos": 0.25, "max_partes": 192}
```

Cada cubo sólido gera uma caixa com sua rotação real, local ao Bone correspondente. Cada plano é
recortado em retângulos de pixels opacos (alfa >= 128), considerando as duas faces e UV invertida.
Os retângulos recebem espessura de 0,25 unidade Blockbench; os vazios transparentes ficam livres.
Não há extensão dos volumes até o chão. O F2 resulta em **37 caixas sólidas e 124 placas**.
O F1 usa **2 caixas sólidas e 28 placas**, acompanhando body e os seis ossos das penas.
O limite é de 192 partes por criatura; excedê-lo interrompe a geração e exige revisão explícita.
Planos com rotação de UV e arquivos sem textura incorporada ainda são recusados nesta modalidade.

`Hitbox` continua PrimaryPart/referência de frente, mas tem `CanCollide/CanQuery = false`.
As superfícies físicas estão em `ColisoresPipeline`. O ModuleScript `ColisaoOssos` acompanha
`Bone.TransformedWorldCFrame` em `PreSimulation`, agrupando a atualização com `BulkMoveTo`.
A prévia `TocarAnimacao` inicia esse módulo no cliente, onde a animação local de teste é avaliada.

**Integração futura:** o módulo deve rodar no mesmo simulador que avalia a animação. Transformações de
Bone não são replicadas; integrar animações publicadas e autoridade de colisão de um jogo multiplayer
exige esse planejamento. Não executar atualizadores concorrentes no cliente e servidor. O teste atual
comprova a prévia local do Studio e as posições de repouso do Edit, sem implementar montaria/transporte.
[Propriedades de Bone](https://create.roblox.com/docs/reference/engine/classes/Bone).

Na amostra de 45 frames de um único F2: desvio posicional medido zero, movimento dos colisores até
2,002 studs; chamada Lua de atualização em média 0,077 ms e máximo 0,248 ms. Isso não mede o custo total
da física nem garante desempenho com muitos NPCs. Perfis de menor detalhe/distância ficam para ensaio
de população. A folha técnica em `auditorias/2026-10-23-f2-colisao-composta.png` compara repouso e volumes.

F1 validado depois da aprovação do F2: salto de um colisor do corpo de 0,561 stud, desvio posicional
medido zero, sem giro do body. Avatar sobre o F1 variou 0,574 stud em altura e manteve apoio em todos
os frames da amostra após acomodação. É contato físico observado na prévia, sem driver de passageiros.

## Próximos testes de infraestrutura

- Testar Reimport real de uma revisão, verificando IDs, hierarquia, atributos e repetição do preparo.
- Revisar no jogo a sensação do bloqueio do corpo agora que a caixa visual foi removida.
- Definir retenção do histórico e uso em outros jogos antes de qualquer limpeza online.
- Ampliar os perfis físicos quando o piloto trouxer outra anatomia.
