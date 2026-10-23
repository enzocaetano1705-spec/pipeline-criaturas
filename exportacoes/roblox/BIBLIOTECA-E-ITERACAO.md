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

## O que significa a colisão atual

`Hitbox` é o bloqueio de locomoção e o PrimaryPart. Seu envelope usa os volumes 3D diretamente no
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

O Roblox anima a aparência por Bones sem atualizar a forma física da malha. Portanto, o salto visual
do F1 não levanta automaticamente quem está sobre ele. Colisão por segmento animado, montaria,
transporte do jogador e caixas de dano exigem comportamento de gameplay, a definir depois.
[Rigging e colisão](https://create.roblox.com/docs/art/modeling/rigging).

## Próximos testes de infraestrutura

- Testar Reimport real de uma revisão, verificando IDs, hierarquia, atributos e repetição do preparo.
- Revisar no jogo a sensação do bloqueio do corpo agora que a caixa visual foi removida.
- Definir retenção do histórico e uso em outros jogos antes de qualquer limpeza online.
- Ampliar os perfis físicos quando o piloto trouxer outra anatomia.
