@AGENTS.md

## Só para o Claude Code
- Rode em modo auto: `claude --permission-mode auto`.
- Os servidores MCP do projeto estão em `.mcp.json`:
  - `bbmodel` (headless) lê, edita em lote, valida, renderiza e exporta `.bbmodel` sem abrir o app. Fica restrito à pasta `modelos/`.
  - `blockbench` (desktop) só responde com o Blockbench aberto e o plugin MCP carregado. Use-o para inspecionar, polir e exportar glTF.
- O servidor desktop tem cerca de 135 ferramentas, que carregam sob demanda pela busca de ferramentas. Prefira o `bbmodel` e os scripts.
- Na primeira sessão o `bbmodel` aparece como "failed": o motor só existe depois do item 0.3. Os scripts usam o `call.ts` e não dependem do MCP; a partir da sessão seguinte (ou de um reconectar em `/mcp`) ele conecta.
- Não use subagentes para tarefas pequenas. Use-os só para vasculhar muitos arquivos.
