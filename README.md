# pipeline-criaturas

Transforma o conceito de uma criatura (imagens livres + o prompt usado) em modelo 3D cubificado no estilo Cobblemon/Digimod, com textura, ossos, locators e animações, pronto para Roblox e Minecraft.

- **Começar:** [PRIMEIROS-PASSOS.md](PRIMEIROS-PASSOS.md)
- **Regras para IAs:** [AGENTS.md](AGENTS.md)
- **Plano e status:** [docs/plano-construcao.md](docs/plano-construcao.md)
- **Preparar uma criatura:** [docs/criaturas/LEIA-ME.md](docs/criaturas/LEIA-ME.md)
- **Modelar uma criatura (IA):** [skills/criaturas-3d/SKILL.md](skills/criaturas-3d/SKILL.md)
- **Estudar referências reais:** [skills/criaturas-3d/referencias.md](skills/criaturas-3d/referencias.md) — ilustração, vistas, volumes, textura e animação antes de criar a geometria.
- **Ficha no chat do claude.ai:** envie `skills-chat/criaturas-3d-chat.zip` como skill

## Uso rápido
No chat: anexe o conceito, a frente e o lado da criatura e peça "modela essa criatura". A IA cria tudo, devolve a folha de vistas e ajusta pelo que você pedir (com print). Edições suas no Blockbench são acompanhadas (`skills/criaturas-3d/chat.md`).

Na linha de comando:
```
uv run criaturas --help                                  # todos os comandos
uv run criaturas tudo docs/criaturas/<nome> --estagio e1 # roda as etapas e para onde precisa da IA ou de você
uv run criaturas medidas dragão final                    # faixas de referência de uma categoria
uv run pytest -q                                         # testes (precisam do motor da Fase 0)
uv run python -m criaturas.sinteticos                    # recria as 3 criaturas sintéticas de teste
```
Etapas por estágio: `ficha` → `preparar` → `classificar` → `medir` → `cubificar` → `validar` → `folha` → `texturizar` → `rig` → `animar` → `exportar`; no fim, `linhagem`.

## Estrutura
```
AGENTS.md, CLAUDE.md     regras para qualquer IA (o CLAUDE.md importa o AGENTS.md)
.mcp.json                servidores MCP do Blockbench (headless e desktop)
.claude/settings.json    permissões do Claude Code
docs/                    cofre do Obsidian: plano, convenções, decisões, sessões, criaturas, pesquisa
referencia/              medidas agregadas, exemplo verificado do motor, protótipo antigo
modelos/                 saída do pipeline, uma pasta por criatura
scripts/                 verificador de ambiente, sincronização das skills, empacotamento da skill do chat
ferramenta/criaturas/    a ferramenta (CLI `criaturas`) e os contratos JSON
ferramenta/testes/       testes e as criaturas sintéticas com a verdade conhecida
ferramenta/js/           cliente MCP do Blockbench desktop e validador glTF (npm install em ferramenta/js)
skills/                  skill criaturas-3d (fonte; copiada para .claude/skills e .agents/skills)
skills-chat/             versão da skill para o chat do claude.ai (ZIP)
externos/                motor headless clonado e fixado (fora do Git)
```

## Licenças de terceiros
- O motor headless e o plugin do Blockbench (`jasonjgardner/blockbench-mcp-plugin`) são GPL-3.0. Este repositório só os chama como programa separado; nenhum código deles é copiado.
- O cliente MCP usa o SDK oficial do MCP (MIT) já instalado no clone do motor; o validador glTF é o `gltf-validator` da Khronos (Apache-2.0). Ver `docs/decisoes/0002-exportacao-roblox.md`.
- `referencia/medidas.json` contém apenas estatísticas agregadas medidas no Cobblemon (modelos CC BY-NC 3.0) e no The Digimod. Nenhum modelo, textura ou animação desses projetos está aqui.
