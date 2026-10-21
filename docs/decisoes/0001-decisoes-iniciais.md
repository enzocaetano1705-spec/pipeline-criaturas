---
tipo: decisao
data: 2026-10-21
status: vigente
---

# 0001 — Decisões iniciais do pipeline

Tomadas na pesquisa feita no app Claude, antes de existir código. Os detalhes estão em [[00-handoff-pipeline-criaturas]].

## Abordagem
1. **Código em vez de MCP passo a passo.** O MCP que monta cubo a cubo gasta muitos tokens. A IA escreve e roda scripts e lê relatórios curtos; imagem só na conferência (uma folha de 4 vistas, ~800 tokens).
2. **A IA não inventa a forma.** O carisma vem do conceito do usuário. A IA faz a leitura semântica; o código faz a parte espacial. No protótipo Forja, a textura calculada agradou e a forma inventada por molde ficou sem carisma.
3. **Separar design de tradução.** O gerador de imagens cria livremente, sem forçar estilo cubo; o pipeline traduz para cubos.
4. **Estágio e categoria são entradas obrigatórias**, porque médias gerais não servem: um bebê Digimon é 100% cabeça e um estágio final de dragão tem ~7%.
5. **Classificação com a imagem primeiro.** O prompt só preenche o que a imagem não mostra e a imagem vence conflitos. Saem até 3 sugestões, e o usuário escolhe ou cria uma categoria.
6. **Cobblemon e Digimod só como estudo.** Extraímos números agregados; nada de geometria, textura, animação ou código.

## Ferramentas
7. **Blockbench no centro.** O `.bbmodel` é a fonte do modelo: grupos são ossos, locators são pontos de ancoragem.
8. **Motor:** servidor MCP headless do `jasonjgardner/blockbench-mcp-plugin` (GPL-3.0), fixado no commit `141ef78`. Edita em lote, valida geometria e animações, renderiza e exporta Bedrock, Java e Modded Entity. O servidor desktop do mesmo projeto fica para inspeção, polimento e export glTF com armadura. Testado em 21/out/2026: criar → editar em lote → validar → validar animações → exportar Bedrock funcionou com Node 22 e o Bun instalado pelo npm. O MCP roda a partir de um clone local fixado (`node externos/.../bin/blockbench-mcp-headless.mjs`) em vez de `npx github:…#commit`, porque o npx com commit fixado falhou no teste (erro "GitFetcher requires an Arborist constructor") e o clone local não depende de download a cada sessão.
9. **Blockbench → Roblox:** glTF com armadura e animações → Importador 3D do Roblox (rig Custom: MeshPart + Bones). A textura pixelada é ampliada por vizinho mais próximo, porque o Roblox filtra texturas de malha.
10. **Python 3.12 + uv** para a ferramenta (imagem, geometria, testes); Node/Bun só para o motor.

## Organização
11. **Repositório privado no GitHub; `docs/` é o cofre do Obsidian.** Markdown puro, legível por qualquer IA. Rollback pelo Git, com tags no fim de cada fase.
12. **`AGENTS.md` é a regra comum.** O `CLAUDE.md` importa o `AGENTS.md` com `@AGENTS.md`. A skill fica em `skills/` e é copiada para `.claude/skills/` (Claude Code) e `.agents/skills/` (Codex e Antigravity).
13. **Claude Code em modo auto**, com permissões negando leitura de segredos. O classificador do modo auto já bloqueia force push, `curl | bash` e apagar arquivos que existiam antes da sessão.
