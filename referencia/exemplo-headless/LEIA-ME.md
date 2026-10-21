# Exemplo verificado do motor headless

Teste de fumaça da Fase 0. Mostra o fluxo "código primeiro": um lote de operações em JSON vira um `.bbmodel` válido, sem abrir o Blockbench e sem chamar o MCP cubo a cubo.

Verificado em 21/out/2026 com o commit `141ef78` (v1.10.1). Resultado: `bbmodel_validate` 0 erros e 0 avisos; `bbmodel_validate_animations` 0 erros; exportação Bedrock sem peças puladas.

## Arquivos
| Arquivo | O que é |
|---|---|
| `criar.json` | argumentos do `bbmodel_create` (formato `bedrock`, que força Box UV) |
| `ops-exemplo.json` | lote do `bbmodel_edit`: ossos, cubos com Box UV, um locator e uma animação `idle` |
| `arquivo.json` | argumentos de leitura e validação |
| `exportar-bedrock.json` | argumentos do `bbmodel_export_bedrock_geometry` |

Os caminhos dentro dos JSON são relativos à raiz `modelos/` passada em `--root`.

## Comandos (na raiz do repositório, depois do item 0.3)
Git Bash:
```bash
BUN=externos/blockbench-mcp-plugin/node_modules/bun/bin/bun.exe
CALL=externos/blockbench-mcp-plugin/headless/call.ts
$BUN run $CALL --root modelos bbmodel_create @referencia/exemplo-headless/criar.json
$BUN run $CALL --root modelos bbmodel_edit @referencia/exemplo-headless/ops-exemplo.json
$BUN run $CALL --root modelos bbmodel_validate @referencia/exemplo-headless/arquivo.json
$BUN run $CALL --root modelos bbmodel_validate_animations @referencia/exemplo-headless/arquivo.json
$BUN run $CALL --root modelos bbmodel_export_bedrock_geometry @referencia/exemplo-headless/exportar-bedrock.json
$BUN run $CALL --root modelos bbmodel_contact_sheet @referencia/exemplo-headless/arquivo.json   # precisa de GPU
```

PowerShell: troque as variáveis por `$BUN = "externos\blockbench-mcp-plugin\node_modules\bun\bin\bun.exe"` e `$CALL = "externos\blockbench-mcp-plugin\headless\call.ts"`, e chame com `& $BUN run $CALL --root modelos …`.

Para ver todas as ferramentas e operações: `$BUN run $CALL --root modelos --list`.

## Detalhes que pegaram no teste
- O id do formato Bedrock é `bedrock`. Com outro id (por exemplo `bedrock_entity`), o arquivo nasce sem Box UV.
- `bbmodel_edit` é atômico: se uma operação falha, nada é gravado. Rodar o mesmo lote duas vezes falha porque os nomes ficam duplicados ("root matches 2 group nodes"). Recrie o arquivo com `overwrite: true` antes de reaplicar.
- Cubos de grupos diferentes que se sobrepõem 1 unidade geram aviso de interpenetração. No exemplo, a cabeça encosta no corpo sem atravessar.
- O validador de animações pegou um pé afundando 0,6 unidade no chão no walk do protótipo Forja. Vale rodar sempre.
- O binário do Bun instalado pelo npm fica em `node_modules/bun/bin/bun.exe`, com esse nome em qualquer sistema.
