# AGENTS.md — pipeline de criaturas 3D

Regras para qualquer IA que trabalhe neste repositório (Claude Code, Codex, Antigravity, Gemini CLI…). Curto de propósito: os detalhes estão em `docs/`.

## O que é
Um pipeline que transforma o conceito de uma criatura (imagens geradas livremente + o prompt usado) em modelo 3D cubificado no estilo Cobblemon/Digimod, com textura, ossos, locators e animações. Destino principal: jogos no Roblox com arte estilo Minecraft. Secundário: mods de Minecraft. Toda criatura tem linhagem de evolução.

## Comece por aqui, nesta ordem
1. `docs/plano-construcao.md`: fases, status (caixas marcadas) e critérios de aceite.
2. A nota mais recente em `docs/sessoes/` e `git log --oneline -15`: onde a última sessão parou.
3. `docs/convencoes.md`: unidades, eixos, nomes de ossos, locators e animações, pastas e formatos.

Leia `docs/pesquisa/` só quando a tarefa pedir, e procure por assunto (grep) em vez de ler as notas inteiras.

## Regras de ouro
1. **A forma vem da imagem do usuário.** A IA não inventa partes nem proporções. O prompt é contexto secundário: só preenche o que a imagem não mostra. Se o prompt contradiz a imagem, vale a imagem, e o conflito entra no relatório.
2. **Estágio e categoria são entradas obrigatórias.** As faixas de `referencia/medidas.json` preenchem medidas que a imagem não mostra e geram avisos. Elas nunca forçam a forma.
3. **Código primeiro.** Escreva e rode scripts; leia relatórios curtos. Nunca monte um modelo cubo a cubo por chamadas de MCP: edições sempre em lote (`ops.json` → `bbmodel_edit`).
4. **Bibliotecas Cobblemon/Digimod ficam fora do repositório.** Podem ser abertas, renderizadas e estudadas para comparar ilustração, volumes, UV, ossos e mecanismos. No repositório entram ferramentas de consulta, conclusões, metadados e números agregados; nunca os arquivos de geometria, textura, animação ou código desses mods. As criaturas são originais. Siga `skills/criaturas-3d/referencias.md`.
5. **O servidor MCP do Blockbench é GPL-3.0.** Use-o como programa separado (MCP ou `externos/blockbench-mcp-plugin/headless/call.ts`). Não copie código dele para `ferramenta/`.
6. **Nunca sobrescreva um `.bbmodel` editado à mão.** Grave uma versão nova e avise.

## Economia de tokens
- Imagens: veja só as versões de até 768 px geradas pela ferramenta, e no máximo uma folha de vistas por iteração.
- Scripts imprimem um resumo de até 20 linhas; os detalhes ficam em JSON no disco.
- Não leia arquivos grandes inteiros (`referencia/medidas.json`, `.bbmodel`, logs). Consulte com `uv run criaturas medidas …`, jq ou um trecho de Python.
- Não refaça pesquisa que já está registrada em `docs/`.

## Git e documentação
- Faça um commit por item concluído do plano, com mensagem em português. Adicione só os arquivos que você mudou: nunca use `git add -A` nem `git add .`.
- Os arquivos do usuário em `docs/criaturas/<nome>/` não são editados nem entram em commit enquanto a ficha estiver com `status: rascunho`.
- Ao fim de cada fase: testes passando → caixas marcadas no plano → tag `fase-N` → push (só para `origin`) → nota curta em `docs/sessoes/AAAA-MM-DD-fase-N.md` (use o modelo `docs/sessoes/_modelo.md`).
- Uma decisão que muda arquitetura, formato ou dependência ganha uma nota curta em `docs/decisoes/` (modelo na pasta).
- Nunca faça push --force, não reescreva histórico, não apague arquivos que você não criou e não escreva segredos em arquivos.

## Quando parar e chamar o usuário
- É preciso instalar, fazer login ou clicar em algo (Blockbench, Obsidian, GitHub, Roblox Studio).
- Uma ação destrutiva ou irreversível atingiria algo que você não criou.
- Uma decisão muda a arquitetura ou contradiz uma decisão registrada.
- Chegou a um ponto de parada do pipeline numa criatura real: confirmar a categoria ou aprovar a folha de vistas. O teste de importação no Roblox vira um pedido na nota da sessão e não bloqueia.

Escreva a pergunta no topo da nota da sessão e pare.

## Comandos
- Modelar uma criatura: siga `skills/criaturas-3d/SKILL.md` (passos, pontos de parada e regras de tokens).
- Buscar/inspecionar referências: `uv run criaturas referencias --help`. Biblioteca padrão: `~/Downloads/referencias-criaturas/`; estudos visuais e catálogos detalhados permanecem nela.
- Ajuda da ferramenta: `uv run criaturas --help`; atalho: `uv run criaturas tudo <pasta> --estagio eN`.
- Testes: `uv run pytest -q` (cerca de 3 min; o teste do Roblox é pulado com o Blockbench fechado).
- Depois de editar `skills/`: `uv run python scripts/sincronizar-skills.py` e `uv run python scripts/empacotar-skill-chat.py`.
- Dependências JS (validador glTF): `npm install --omit=dev` em `ferramenta/js`.
- Motor headless do Blockbench sem MCP: `externos/blockbench-mcp-plugin/node_modules/bun/bin/bun.exe run externos/blockbench-mcp-plugin/headless/call.ts --root modelos <ferramenta> @args.json` (exemplo completo em `referencia/exemplo-headless/`). O `call.ts` sobe o servidor chamando `bun` pelo nome: ponha `externos/blockbench-mcp-plugin/node_modules/bun/bin` no PATH antes, senão sai "MCP error -32000: Connection closed". A ponte Python (`motor.py`) faz isso sozinha.

## Ambiente
Windows 10/11 nativo (Git Bash ou PowerShell), Node 23.6 ou mais novo, uv, Git e GitHub CLI. O motor headless roda a partir do clone fixado em `externos/blockbench-mcp-plugin` (item 0.3 do plano), tanto pelo MCP quanto pelo `call.ts`. Abra a IA sempre na raiz do repositório: os caminhos do `.mcp.json` são relativos a ela.
