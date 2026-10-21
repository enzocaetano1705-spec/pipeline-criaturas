# pipeline-criaturas

Transforma o conceito de uma criatura (imagens livres + o prompt usado) em modelo 3D cubificado no estilo Cobblemon/Digimod, com textura, ossos, locators e animações, pronto para Roblox e Minecraft.

- **Começar:** [PRIMEIROS-PASSOS.md](PRIMEIROS-PASSOS.md)
- **Regras para IAs:** [AGENTS.md](AGENTS.md)
- **Plano e status:** [docs/plano-construcao.md](docs/plano-construcao.md)
- **Preparar uma criatura:** [docs/criaturas/LEIA-ME.md](docs/criaturas/LEIA-ME.md)

## Estrutura
```
AGENTS.md, CLAUDE.md     regras para qualquer IA (o CLAUDE.md importa o AGENTS.md)
.mcp.json                servidores MCP do Blockbench (headless e desktop)
.claude/settings.json    permissões do Claude Code
docs/                    cofre do Obsidian: plano, convenções, decisões, sessões, criaturas, pesquisa
referencia/              medidas agregadas, exemplo verificado do motor, protótipo antigo
modelos/                 saída do pipeline, uma pasta por criatura
scripts/                 verificador de ambiente (e, depois, sincronização das skills)
ferramenta/, skills/     criados pelo Claude Code nas Fases 0 a 9
externos/                motor headless clonado e fixado (fora do Git)
```

## Licenças de terceiros
- O motor headless e o plugin do Blockbench (`jasonjgardner/blockbench-mcp-plugin`) são GPL-3.0. Este repositório só os chama como programa separado; nenhum código deles é copiado.
- `referencia/medidas.json` contém apenas estatísticas agregadas medidas no Cobblemon (modelos CC BY-NC 3.0) e no The Digimod. Nenhum modelo, textura ou animação desses projetos está aqui.
