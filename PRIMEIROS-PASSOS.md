# Primeiros passos

O que só você pode fazer (instalar, fazer login, clicar em apps) e o que colar no Claude Code. Leva uns 20 minutos, uma vez só.

## 1. Instalar o que falta
No PowerShell. Instale só o que faltar; o verificador do passo 3 diz o quê.
```powershell
winget install --id Git.Git -e
winget install --id GitHub.cli -e
winget install --id OpenJS.NodeJS.LTS -e
winget install --id astral-sh.uv -e
winget install --id JannisX11.Blockbench -e
winget install --id Obsidian.Obsidian -e
claude update
```
Depois, feche e abra o terminal para o PATH atualizar.

## 2. Login no GitHub e identidade dos commits
```powershell
gh auth login
git config --global user.name "Seu Nome"
git config --global user.email "seu-email"
```
No `gh auth login`, escolha: GitHub.com → HTTPS → Yes (autenticar o Git) → Login with a web browser. No e-mail, pode usar o endereço "noreply" que o GitHub mostra em Settings › Emails.

## 3. Colocar o kit no lugar e conferir
Descompacte o kit em `C:\Users\<você>\dev\`, para ficar `C:\Users\<você>\dev\pipeline-criaturas\`. Evite pastas sincronizadas pelo OneDrive. Depois rode:
```powershell
cd $HOME\dev\pipeline-criaturas
powershell -ExecutionPolicy Bypass -File scripts\verificar-ambiente.ps1
```

## 4. Blockbench (uma vez)
1. File › Plugins › Load Plugin from URL › `https://jasonjgardner.github.io/blockbench-mcp-plugin/mcp.js`
2. Settings › General: desmarque **Enable risky_eval**. A IA não precisa rodar JavaScript arbitrário dentro do app.
3. O app só precisa estar aberto quando o Claude Code for exportar para o Roblox (Fase 8). O resto roda sem ele.

## 5. Obsidian (uma vez)
1. Open folder as vault › escolha `pipeline-criaturas\docs`.
2. Pronto. O Claude Code escreve as notas como arquivos e o Obsidian só mostra; não precisa de plugin nem de MCP.

Se instalar o plugin Obsidian Git mais tarde, deixe o auto-commit desligado enquanto o Claude Code trabalha: dois robôs fazendo commit ao mesmo tempo geram conflito.

## 6. Abrir o Claude Code e colar o prompt
```powershell
cd $HOME\dev\pipeline-criaturas
claude --permission-mode auto
```
- Na primeira vez ele pergunta se você confia na pasta: responda sim.
- Modelo: `/model sonnet` para as fases 0, 1 e 6 a 9; `/model opus` para as fases 2 a 5 (o núcleo difícil). Assim o limite do plano Pro rende mais.

**Prompt da primeira sessão:**
```text
Você vai construir o pipeline de criaturas 3D deste repositório, de forma autônoma, enquanto eu desenho a primeira criatura. Tudo o que já foi decidido está nos arquivos; não refaça a pesquisa.

1. Leia AGENTS.md, docs/00-indice.md, docs/plano-construcao.md e docs/convencoes.md. Abra as notas de docs/pesquisa/ só quando uma tarefa precisar, procurando pelo assunto.
2. Execute a Fase 0 do plano. Autorizo explicitamente:
   - criar o repositório PRIVADO "pipeline-criaturas" na minha conta do GitHub com
     gh repo create pipeline-criaturas --private --source . --remote origin --push
     (origin é o único remoto; todo push vai só para ele);
   - clonar https://github.com/jasonjgardner/blockbench-mcp-plugin em externos/blockbench-mcp-plugin, fixar no commit 141ef78fa59eb697895ab73d4757d874ab8a2711 e rodar npm install --omit=dev lá dentro;
   - instalar dependências Python com uv neste projeto.
3. Depois siga as fases em ordem, sem esperar por mim, até chegar a um PARE do plano ou terminar a Fase 9. A cada item: testes passando, caixa marcada no plano e commit só dos arquivos que você mudou. A cada fase: tag fase-N, push e uma nota curta em docs/sessoes/.
4. Pare e me chame se precisar que eu instale, faça login ou clique em algo; se uma ação fosse apagar ou sobrescrever algo que você não criou; ou se surgir uma decisão que muda a arquitetura. Escreva a pergunta no topo da nota da sessão.
5. Eu estou trabalhando em docs/criaturas/. Não edite nem faça commit dos meus arquivos lá enquanto a ficha estiver com status: rascunho.

Comece agora pela Fase 0 e me avise em uma linha quando cada fase terminar.
```

## 7. Sessões seguintes
Ao abrir a segunda sessão, rode `/mcp` e confira se o `bbmodel` está conectado (na primeira ele aparece como falhou, porque o motor só é baixado durante a Fase 0).

Quando o limite renovar ou você abrir uma sessão nova:
```text
Continue o pipeline de criaturas. Leia docs/plano-construcao.md, a nota mais recente de docs/sessoes/ e git log --oneline -15, e retome do primeiro item não marcado, com as regras do AGENTS.md e as mesmas autorizações da primeira sessão (push só para origin; não mexer em docs/criaturas/ em rascunho).
```
Esse mesmo texto funciona no Codex ou no Antigravity abertos nesta pasta, porque os dois leem o `AGENTS.md`. Sem MCP, eles chamam o motor pelo comando que está no `AGENTS.md`.

## 8. Quando a sua criatura estiver pronta
Mude a ficha para `status: pronta-para-modelagem`.

- Se o pipeline ainda estiver em construção:
  ```text
  A ficha docs/criaturas/<nome>/ficha.md está pronta-para-modelagem. Use essa criatura como teste real nas fases que faltam, além das sintéticas.
  ```
- Se a Fase 9 já terminou:
  ```text
  A ficha docs/criaturas/<nome>/ficha.md está pronta-para-modelagem. Execute a Fase 10: rode o pipeline estágio por estágio, parando na classificação (eu confirmo a categoria na ficha) e na folha de vistas (eu aprovo), e registre o que falhar na lista de melhorias do plano.
  ```

## O que nunca é automático
Logins, instaladores, o plugin do Blockbench, abrir a pasta no Obsidian e importar no Roblox Studio exigem você. Todo o resto o Claude Code faz sozinho e registra em `docs/`.
