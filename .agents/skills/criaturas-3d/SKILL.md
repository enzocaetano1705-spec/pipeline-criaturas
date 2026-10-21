---
name: criaturas-3d
description: Transforma o conceito de uma criatura (imagens + prompt numa ficha em docs/criaturas/<nome>/) em modelo 3D cubificado estilo Cobblemon/Digimod, com textura, ossos, locators e animações, exportado para Roblox (.glb) e Minecraft (Bedrock/GeckoLib). Use ao modelar, revisar ou exportar uma criatura deste repositório, ou para checar se uma ficha está pronta.
---

# Criaturas 3D — pipeline

Você conduz o pipeline; o código faz a parte espacial. A IA só faz duas coisas que exigem olhar imagens: o **checklist** de classificação e a **leitura** das partes. Todo o resto é `uv run criaturas …`.

## Quando usar
- **O usuário anexou imagens de uma criatura no chat, ou mandou um print pedindo um ajuste no modelo: siga `chat.md` (nesta pasta).**
- Uma ficha em `docs/criaturas/<nome>/ficha.md` está com `status: pronta-para-modelagem`.
- Pedirem para refazer uma etapa (textura, animação, exportação) de uma criatura já modelada.
- Pedirem para conferir uma linhagem (vários estágios).

**Nunca** mexa numa pasta de `docs/criaturas/` cuja ficha está com `status: rascunho`: nem editar, nem commit.

## Antes de começar
- Trabalhe na raiz do repositório (onde estão `pyproject.toml` e `AGENTS.md`).
- O motor headless precisa existir em `externos/blockbench-mcp-plugin` (item 0.3 do plano). Sem ele, as etapas falham com "motor headless não instalado".
- Só a exportação para o Roblox precisa do Blockbench desktop aberto com o plugin MCP. O resto roda sem abrir app nenhum.
- `<pasta>` é a pasta da criatura (`docs/criaturas/<nome>`). As saídas vão para `modelos/<nome da pasta>/eN/`. Nas sintéticas de teste a pasta é `modelos/_sinteticos/fichas/_sint-<nome>` e a saída vai para `modelos/_sint-<nome>/`.
- **Nota da sessão:** `docs/sessoes/AAAA-MM-DD-<nome>.md`, no formato de `docs/sessoes/_modelo.md`. Perguntas e pedidos ao usuário vão no topo dela.

## Passo a passo (para cada estágio: e1, e2…)
O atalho `uv run criaturas tudo <pasta> --estagio eN` roda as etapas de código em ordem e **para sozinho** onde precisa de você (checklist, leitura, categoria, folha). Rode-o, faça o que ele pedir e rode de novo. Ele mostra uma linha por etapa: para ver os avisos de uma etapa, rode-a sozinha (`uv run criaturas <etapa> <pasta> --estagio eN`) ou leia `avisos` em `modelos/<nome>/eN/relatorio.json`. Nas sintéticas o `tudo` não para na folha: abra `folha.png` uma vez assim mesmo.

1. **Ficha.** `uv run criaturas ficha <pasta>`
   - Corrija só o que você criou. Erro na ficha do usuário vira pergunta para ele (nota da sessão).
2. **Preparo.** `uv run criaturas preparar <pasta> --estagio eN`
   - Abra `modelos/<nome>/eN/preparo/lado-768.png` **só se** desconfiar do lado: a frente da criatura tem que estar à esquerda. Se estiver à direita, rode de novo com `--espelhar-lado`.
3. **Classificação** (pule se a ficha já tem `Categoria confirmada`).
   - Siga `classificar.md` (nesta pasta): olhe `frente-grade.png`, escreva `modelos/<nome>/eN/checklist.json`.
   - `uv run criaturas classificar <pasta> --estagio eN`
   - **PARE** (criatura real): mostre as 3 sugestões ao usuário e espere `Categoria confirmada` na ficha. Se ele escolher diferente da sugestão 1: `--registrar-escolha "plano › nicho"`.
4. **Leitura.** Siga `ler.md` (nesta pasta): olhe `frente-grade.png` e `lado-grade.png`, escreva `modelos/<nome>/eN/leitura.json`.
5. **Medição.** `uv run criaturas medir <pasta> --estagio eN`
   - Aviso de "diferença entre vistas" numa parte: confira só a caixa dessa parte. Se ela está certa e a diferença é porque a parte fica escondida numa vista (corpo atrás da cabeça, de frente), o aviso é esperado: siga e cite-o numa linha da nota.
6. **Cubos.** `uv run criaturas cubificar <pasta> --estagio eN`, depois `uv run criaturas validar <pasta> --estagio eN`.
   - `validar` tem que dar 0 erros. Avisos que ficarem precisam de uma explicação na nota.
7. **Folha de vistas.** `uv run criaturas folha <pasta> --estagio eN` → `modelos/<nome>/eN/folha.png` (768 × 384).
   - Olhe a folha **uma vez**. Compare com o conceito: proporções, partes faltando, lado trocado.
   - **PARE** (criatura real): mostre a folha ao usuário e espere a aprovação. Depois: `tudo --folha-aprovada`.
8. **Textura.** `uv run criaturas texturizar <pasta> --estagio eN` (estilo Digimod: `--olho-pintado`).
   - Tem que sair sem erros (sem buraco, cores no limite). ΔE acima de 10 numa parte = aviso para olhar.
9. **Rig e animações.** `uv run criaturas rig <pasta> --estagio eN`, depois `uv run criaturas animar <pasta> --estagio eN` (`--so-base` para só idle, walk e blink).
   - A validação das animações tem que dar 0 erros.
10. **Exportação.** `uv run criaturas exportar <pasta> --estagio eN` (destino da ficha; `--destino roblox,minecraft`, `--geckolib`).
    - Roblox: o Blockbench desktop precisa estar aberto com o plugin MCP (o comando abre o app se puder). Saída em `modelos/<nome>/export/roblox/*.glb`.
    - O teste de importação no Roblox Studio é do usuário: escreva o pedido no topo da nota da sessão e siga.
11. **Linhagem** (depois de todos os estágios): `uv run criaturas linhagem <pasta>` → `modelos/<nome>/linhagem.png` e `.json`. Erro = evolução invertida; avise o usuário.

## Pontos de parada (escreva a pergunta no topo da nota da sessão e pare)
- Categoria não confirmada numa criatura real (passo 3).
- Folha de vistas ainda não aprovada numa criatura real (passo 7).
- Precisa instalar, fazer login ou clicar em algo.
- Algo apagaria ou sobrescreveria um arquivo que você não criou. O pipeline nunca sobrescreve um `.bbmodel` editado à mão: grava `.v2` e avisa. Respeite.
- Uma decisão que muda arquitetura ou contradiz `docs/decisoes/`.

Nas criaturas sintéticas (`modelos/_sinteticos/fichas/_sint-*`) e em `docs/criaturas/_testes/`, não pare: use a categoria verdadeira ou a sugestão 1, e a folha não precisa de aprovação.

## Regras de tokens
- Imagem só as de até 768 px que o pipeline gera (`*-grade.png`, `*-768.png`, `folha.png`). No máximo **uma folha por iteração**.
- Classificar custa uma imagem; ler custa no máximo duas (frente e lado com grade).
- Leia o resumo de até 20 linhas que cada comando imprime. Os detalhes ficam em JSON em `modelos/<nome>/eN/` (`relatorio.json` tem a última execução de cada etapa). Abra só o trecho que precisar.
- Não abra inteiros `referencia/medidas.json`, `.bbmodel` ou texturas. Para faixas da categoria: `uv run criaturas medidas <plano|nicho> [estágio]`.
- Nunca monte o modelo cubo a cubo por MCP: o código gera os lotes (`ops.json`) para o motor.
- Não refaça pesquisa: as regras estão em `docs/` e no código.

## Arquivos de uma criatura (`modelos/<nome>/`)
Além destes: `eN/ver.png`, `eN/quadro-*.png`, `eN/correcoes/*.json` (lotes do `aplicar`), `eN/historico.jsonl` (quem mudou o quê) e `eN/.estado/` (último estado conhecido).

| Arquivo | Quem escreve |
|---|---|
| `entrada.json` | `ficha` |
| `eN/preparo/*` | `preparar` |
| `eN/checklist.json`, `eN/leitura.json` | **você** (IA), pelos protocolos |
| `eN/classificacao.json`, `eN/medidas.json`, `eN/plano-cubos.json`, `eN/ops.json` | `classificar`, `medir`, `cubificar` |
| `eN/<nome>-eN.bbmodel` | `cubificar` (+ textura, locators e animações pelas etapas seguintes) |
| `eN/textura.png`, `eN/textura-roblox.png`, `eN/folha.png`, `eN/animacoes.json`, `eN/validacao.json` | as etapas de mesmo nome |
| `eN/relatorio.json` | todas: resultado, avisos e hash do `.bbmodel` |
| `export/roblox/*.glb` (+ a cópia `*.<hash>.bbmodel` com a textura ×8), `export/minecraft/*`, `export/geckolib/*` | `exportar` |
| `linhagem.json`, `linhagem.png` | `linhagem` |

## Problemas comuns
- **"falta checklist.json / leitura.json"**: é a sua parte; siga o protocolo e rode de novo.
- **"foi editado à mão"**: alguém mexeu no `.bbmodel`. Rode `cubificar` de novo: ele grava `.v2` e as etapas seguintes passam a usar a versão nova.
- **Exportação Roblox falha**: confira se o Blockbench está aberto e se `http://localhost:3000/bb-mcp` responde (Settings › Plugins: MCP Server).
- **`medir` erra uma parte escondida**: desenhe a caixa só onde a parte aparece; o código completa pelo espelho, pela parte irmã ou pela tabela.

## Referência
`docs/convencoes.md` (eixos, nomes, pastas) · `docs/plano-construcao.md` (fases e aceites) · `AGENTS.md` (regras de Git e de parada).
