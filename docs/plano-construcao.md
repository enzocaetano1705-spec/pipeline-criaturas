---
tags: [plano, pipeline-criaturas]
status: em andamento
---

# Plano de construção do pipeline

Qualquer IA continua daqui. Siga as fases em ordem. Cada fase entrega a **versão mínima que passa no aceite**; refinamentos vão para a lista do fim. Marque `[x]` ao concluir cada item (um commit por item).

**Modelo sugerido** (o usuário escolhe ao abrir a sessão): `Sonnet` para rotina, `Opus` para o núcleo difícil.

**Motor headless fixado:** `jasonjgardner/blockbench-mcp-plugin` no commit `141ef78fa59eb697895ab73d4757d874ab8a2711` (v1.10.1, 16/out/2026). Trocar a versão exige uma nota em `docs/decisoes/`.

| Fase | Entrega | Modelo | Status |
|---|---|---|---|
| 0 | Ambiente, GitHub e motor headless | Sonnet | ☑ |
| 1 | Contratos, CLI, criaturas sintéticas e renderizador | Sonnet | ☑ |
| 2 | Preparo de imagem e classificação | Opus | ☑ |
| 3 | Leitura semântica e medição | Opus | ☑ |
| 4 | Cubificador e folha de vistas | Opus | ☑ |
| 5 | Textura | Opus | ☑ |
| 6 | Rig, locators e animações | Sonnet | ☑ |
| 7 | Validação da linhagem | Sonnet | ☑ |
| 8 | Exportação Roblox e Minecraft | Sonnet | ☑ |
| 9 | Skill e documentação | Sonnet | ☑ |
| 10 | Primeira criatura real (com o usuário) | Opus | ☐ |

---

## Fase 0 — Ambiente, GitHub e motor headless
- [x] 0.1 Conferir e registrar versões na nota da sessão: `git --version`, `gh auth status`, `node --version` (23.6 ou mais para render), `uv --version` e, no Claude Code, `claude mcp list`. Se faltar algo: **PARE** e passe o comando de instalação de `PRIMEIROS-PASSOS.md`.
- [x] 0.2 Repositório:
  - `git init -b main`, se a pasta ainda não for um repositório.
  - Conferir `git config user.name` e `user.email`. Se faltar, **PARE**: não invente identidade.
  - Commit inicial do kit, sem as pastas de criatura que o usuário já tenha começado em `docs/criaturas/` (entram só `LEIA-ME.md`, `_modelo/` e `_testes/`).
  - `gh repo create pipeline-criaturas --private --source . --remote origin --push`.
- [x] 0.3 Motor headless local:
  - `git clone https://github.com/jasonjgardner/blockbench-mcp-plugin externos/blockbench-mcp-plugin`
  - `git -C externos/blockbench-mcp-plugin checkout 141ef78fa59eb697895ab73d4757d874ab8a2711`
  - `npm install --omit=dev` dentro dele (isso traz o Bun).
  - Rodar o teste de fumaça de `referencia/exemplo-headless/` em `modelos/_fumaca/`: `bbmodel_validate` com 0 erros e um `.geo.json` exportado.
- [x] 0.4 Render headless (precisa de GPU; baixa cerca de 130 MB na primeira vez): `bbmodel_contact_sheet` do modelo de fumaça.
  - Funcionou: registre.
  - Falhou: registre o erro. A folha de vistas usa o renderizador próprio (item 1.7).
  - Em qualquer caso, confira no render o lado direito (+X) e corrija `docs/convencoes.md` se preciso.
- [x] 0.5 MCPs no Claude Code:
  - `bbmodel` usa o clone do item 0.3, então só conecta numa sessão aberta depois dele (ou ao reconectar em `/mcp`). Nesta sessão, use o `call.ts`. Anote na nota da sessão que o usuário deve conferir com `/mcp` na próxima abertura.
  - `blockbench` só conecta com o app aberto e o plugin carregado. Se não estiver, anote e siga: só bloqueia na Fase 8.
- [x] 0.6 Python:
  - `pyproject.toml` na raiz, pacote em `ferramenta/criaturas/`, testes em `ferramenta/testes/`, Python 3.12.
  - Dependências mínimas: numpy, pillow, pyyaml, jsonschema e pytest. Cada dependência pesada nova ganha uma nota de decisão.
  - `uv sync`; `uv run criaturas --help` responde.
- [x] 0.7 Nota da sessão, tag `fase-0`, push.

**Aceite:** repositório privado no GitHub com o kit; fumaça headless com 0 erros; `uv run criaturas --help` funcionando.

## Fase 1 — Contratos, CLI, criaturas sintéticas e renderizador
- [x] 1.1 Esquemas JSON em `ferramenta/criaturas/contratos/` para `entrada`, `checklist`, `classificacao`, `leitura`, `medidas`, `plano_cubos` e `relatorio`, com exemplos válidos em `ferramenta/testes/exemplos/`.
- [x] 1.2 CLI `criaturas` com os subcomandos `ficha`, `preparar`, `classificar`, `medir`, `cubificar`, `texturizar`, `rig`, `animar`, `validar`, `folha`, `linhagem`, `exportar`, `medidas` e `tudo`.
  - Podem nascer como esboço que avisa "ainda não implementado".
  - Todos recebem `<pasta-da-criatura> [--estagio eN]`, imprimem um resumo de até 20 linhas e gravam JSON.
- [x] 1.3 `criaturas medidas <plano|nicho> [estagio]` completo: lê `referencia/medidas.json` e imprime as faixas.
- [x] 1.4 `criaturas ficha <pasta>` completo: lê o `ficha.md` (frontmatter e seções), confere as imagens obrigatórias e os tamanhos e grava `modelos/<nome>/entrada.json`, com erros claros quando faltar algo.
- [x] 1.5 Ponte Python para o motor (`ferramenta/criaturas/motor.py`): chama o `call.ts` com os argumentos num arquivo, devolve JSON e trata erros. Teste: recriar o modelo de fumaça pela ponte.
- [x] 1.6 Três criaturas sintéticas em `ferramenta/testes/sinteticos/` (quadrúpede, bípede com cauda, alado), feitas com ops próprios e com a verdade conhecida (medidas de cada parte).
- [x] 1.7 Renderizador próprio mínimo: porte do `render.py` da Forja lendo `.bbmodel`. Vistas ortográficas de frente, lado, costas e 3/4, fundo liso e luz chapada. Serve para as imagens de teste e como reserva da folha de vistas.

**Aceite:** `uv run pytest -q` verde; `criaturas medidas dragão final` imprime as faixas; `criaturas ficha docs/criaturas/_modelo` aponta os campos que faltam; as sintéticas têm vistas renderizadas.

## Fase 2 — Preparo de imagem e classificação
- [x] 2.1 `preparar`: lê as imagens do estágio e grava em `modelos/<nome>/eN/preparo/` a imagem recortada, a versão de até 768 px, a versão de até 768 px com grade numerada (linhas a cada 1/32 da altura, rótulos de 0 a 32) e a máscara.
  - Fundo: usa o alfa se houver; senão segmenta o fundo liso a partir das bordas; `rembg` só como extra opcional.
  - Recorta na silhueta e iguala a escala entre as vistas pela altura.
- [x] 2.2 Contrato do checklist morfológico com os itens de `docs/pesquisa/categorias-criaturas.md` (seção "Passo de classificação"). Cada item tem valor, certeza (visível, incerto ou oculto) e fonte (imagem ou prompt).
- [x] 2.3 Protocolo da IA, escrito em `skills/criaturas-3d/classificar.md`:
  1. Só a imagem com grade, com o prompt escondido → checklist.
  2. Lê o prompt e preenche apenas os itens incertos ou ocultos.
  3. Lista os conflitos.
- [x] 2.4 `classificar` (código): pontua os 10 planos e os 19 nichos com regras tiradas das tabelas e dos "pares que se confundem".
  - Devolve até 3 sugestões (plano › nicho) com %, os 2 ou 3 traços que justificam cada uma e o estágio aparente (cabeça e olho comparados com a tabela).
  - Acrescenta a seção "Classificação sugerida" no fim da ficha.
  - **PARE** (só em criatura real): o pipeline só segue com `categoria_confirmada` preenchida na ficha. Nas sintéticas e nas imagens de `_testes/`, use a categoria verdadeira ou a sugestão 1 e continue.
- [x] 2.5 Registro de correções: quando o usuário escolhe algo diferente da sugestão 1, anexar checklist, sugestões e escolha em `referencia/correcoes-classificacao.jsonl` para recalibrar as regras depois.

**Aceite:** testes de pontuação com checklists sintéticos, incluindo os pares que se confundem; nas imagens de `docs/criaturas/_testes/` (se houver) sai a lista de 3 sugestões; cada classificação custa cerca de uma imagem de 768 px.

## Fase 3 — Leitura semântica e medição
- [x] 3.1 Contrato `leitura`:
  - vistas usadas;
  - partes com id padrão, pai, tipo (volume, plano ou adesivo), simetria e espelho;
  - caixa de cada parte por vista, em coordenadas da grade;
  - rotação de repouso aproximada;
  - papéis de cor;
  - incertezas, com como foram resolvidas.
- [x] 3.2 Protocolo da IA para a leitura, em `skills/criaturas-3d/ler.md`:
  - olhar só as versões com grade;
  - nunca inventar parte;
  - incerteza → prompt → faixa da categoria, marcada "da tabela".
- [x] 3.3 `medir`:
  - Encosta cada caixa nas bordas reais da máscara, dentro de uma margem.
  - Combina frente (x, y) e lado (z, y) em caixas 3D, em unidades, na escala da altura alvo (da ficha, ou a mediana do estágio e nicho).
  - Sem vista lateral: profundidade pela razão da categoria, marcada "estimada".
  - Diferença de mais de 10% entre vistas gera aviso.
- [x] 3.4 Teste de ida e volta: para cada sintética, renderizar as vistas, gerar a `leitura` a partir da verdade com ruído de ±1 célula da grade (simulando a IA), rodar `medir` e comparar com a verdade.

**Aceite:** erro de até 1 unidade ou 10% por dimensão em pelo menos 90% das partes das 3 sintéticas.

## Fase 4 — Cubificador e folha de vistas
- [x] 4.1 `cubificar`: leitura + medidas + categoria + estágio → `plano-cubos.json` → `ops.json` → `.bbmodel` pelo motor (formato bedrock, Box UV, tamanhos inteiros).
- [x] 4.2 Regras:
  - hierarquia e nomes de `docs/convencoes.md`, com pivôs nas juntas;
  - correntes (cauda, pescoço, tentáculos) com o nº de segmentos da categoria, afinando como a silhueta e com a rotação de repouso seguindo a linha central;
  - espelhamento da esquerda para a direita com `mirror_uv`;
  - planos para as partes do tipo plano;
  - locators padrão;
  - orçamento de cubos do estágio (aviso acima do p75 × 1,3).
- [x] 4.3 Nunca sobrescrever um `.bbmodel` editado à mão: o hash fica em `relatorio.json`, e se o arquivo mudou a saída nova vai para `.v2`.
- [x] 4.4 `validar`: `bbmodel_validate` com 0 erros e avisos explicados, mais verificações próprias:
  - tamanhos inteiros e simetria;
  - orçamento de cubos;
  - todas as partes da leitura presentes;
  - fração de cabeça do modelo comparada com a da imagem, não com a tabela.
- [x] 4.5 `folha`: as 4 vistas do modelo (render headless ou renderizador próprio) ao lado do conceito, numa única imagem de até 768 px.

**Aceite:** as 3 sintéticas validam com 0 erros e ficam a até 10% da verdade nas proporções de cabeça, corpo e membros; um modelo abre no Blockbench sem erro (pelo MCP desktop, se disponível).

## Fase 5 — Textura
- [x] 5.1 `texturizar`: cada face de cubo amostra a vista correspondente, usando o mapeamento imagem↔modelo da medição.
  - frente ← vista frontal; laterais ← vista lateral; costas ← vista de trás;
  - topo e base ← cor média das bordas vizinhas.
- [x] 5.2 Paleta:
  - quantizar nas cores da criatura (até 5 base e 2 de destaque), com rampas OKLCH;
  - sombreado pintado: topo mais claro, base mais escura e AO simples como na Forja;
  - limpar pixels isolados.
- [x] 5.3 Rosto em adesivos (olhos, pupilas, pálpebras e boca com regiões próprias), mais a opção "olho pintado" no estilo Digimod.
- [x] 5.4 Planos com recorte, com o alfa vindo da silhueta da parte.
- [x] 5.5 Versão Roblox: `textura-roblox.png`, ampliada ×8 por vizinho mais próximo, com 2 px de margem por ilha.

**Aceite:** nenhum buraco transparente em face de volume; nº de cores dentro do limite; cor média de cada parte a ΔE ≤ 10 do conceito; folha conferida uma vez.

## Fase 6 — Rig, locators e animações
- [x] 6.1 Locators padrão posicionados a partir das partes.
- [x] 6.2 Biblioteca procedural por plano de corpo, adaptando `referencia/prototipo-forja/forja/anim.py` aos nomes padrão.
  - Primeiro: `idle` (respiração), `walk` (marcha do plano, ciclo pelo estágio) e `blink`.
  - Depois: `run`, `cry`, `hurt`, `faint`, `sleep`, `fly` e `swim`.
- [x] 6.3 Chaves assadas (sem Molang), loop sem emenda, interpolação catmullrom.
- [x] 6.4 Validar com `bbmodel_validate_animations` (ground_sink, detachment) e `bbmodel_sample_pose`. O walk do protótipo afunda o pé 0,6 unidade: o teste tem que pegar isso.

**Aceite:** `idle`, `walk` e `blink` com 0 erros nas 3 sintéticas.

## Fase 7 — Validação da linhagem
- [x] 7.1 `linhagem`: compara os estágios com `assinatura_evolucao` em `referencia/medidas.json` (altura ×, Δ cabeça, cubos ×, Δ olho, andar ×, postura) e dá OK, aviso ou erro, mais uma imagem com os estágios lado a lado na mesma escala.
- [x] 7.2 Motivos que atravessam a linhagem: sobreposição de paleta entre estágios, com aviso abaixo de 50%.

**Aceite:** uma linhagem sintética invertida dá erro; uma linhagem normal passa.

## Fase 8 — Exportação Roblox e Minecraft
- [x] 8.1 Minecraft: `bbmodel_export_bedrock_geometry`, animações Bedrock (exportador próprio simples se o motor não tiver) e textura. GeckoLib quando pedido, com as regras do validador.
- [x] 8.2 Roblox:
  - Fazer uma cópia do modelo com a textura ampliada.
  - Exportar pelo servidor desktop com `export_model`, codec `gltf` e opções `encoding: "binary"`, `embed_textures: true`, `armature: true` e `animations: true` → `.glb`.
  - Chamar por script: um cliente MCP HTTP próprio, usando o SDK do MCP que está em `externos/`. Se o app estiver fechado, abrir com `blockbench_launch` e `wait_for_mcp_ms`.
  - Plano B se falhar: exportador glTF próprio.
- [x] 8.3 Verificações:
  - validador glTF da Khronos (pacote npm `gltf-validator`) sem erros;
  - até 20 mil triângulos;
  - nomes de ossos e locators preservados.
- [x] 8.4 Pedido ao usuário, no topo da nota da sessão: importar um `.glb` no Roblox Studio (Importador 3D, rig Custom) e contar o resultado. Não bloqueia: siga para a Fase 9 e ajuste quando o retorno vier.

**Aceite:** `.glb` válido. A confirmação no Roblox fica pendente até o usuário testar.

## Fase 9 — Skill e documentação
- [x] 9.1 `skills/criaturas-3d/SKILL.md` com menos de 200 linhas e `name` e `description` no frontmatter. Conteúdo:
  - quando usar;
  - passos com os comandos exatos;
  - pontos de parada;
  - regras de tokens.
  Os arquivos de apoio (`classificar.md`, `ler.md`) ficam na mesma pasta.
- [x] 9.2 `scripts/sincronizar-skills.py`: copia `skills/` para `.claude/skills/` (Claude Code) e `.agents/skills/` (Codex e Antigravity). Edite só `skills/`.
- [x] 9.3 Versão para o chat do claude.ai, em ZIP: só ficha, classificação e a checagem "pronta para modelagem", sem modelagem.
- [x] 9.4 Ensaio: uma sessão nova, sem contexto, roda o pipeline numa criatura sintética seguindo só a skill.

**Aceite:** ensaio sem intervenção; documentação atualizada.

## Fase 9b — Fluxo pelo chat (pedido do usuário, decisão 0003)
- [x] 9b.1 `nova`: criatura a partir das imagens anexadas (conceito, frente, lado), sem o usuário mexer em pastas.
- [x] 9b.2 `ver`, `quadro` e `aplicar`: conferir um problema relatado com print e corrigir por código.
- [x] 9b.3 `adotar`: edições à mão no Blockbench viram o estado atual; textura, animações e locators mexidos à mão ficam protegidos.
- [x] 9b.4 `skills/criaturas-3d/chat.md` com o ciclo de ajustes e as receitas de correção.

## Fase 10 — Primeira criatura real (com o usuário)
Começa quando `docs/criaturas/<nome>/ficha.md` estiver com `status: pronta-para-modelagem`.
- [ ] 10.1 Rodar estágio por estágio, com as paradas na categoria e na folha de vistas.
- [ ] 10.2 Registrar o que falhou na lista de melhorias abaixo e corrigir o que bloqueia.
- [ ] 10.3 Exportar para o Roblox e testar no Studio com o usuário.

**Ajuste solicitado durante a fase 10:**
- [x] Estudar referências por estrutura (ilustração, vistas reais, atlas, JSON e animações), acrescentar consulta local e estratégia `poucas_formas`, testar e registrar na skill. Decisão [[0005-estudar-referencias-por-estrutura]]. O ensaio técnico do pavão não conclui a revisão artística nem a importação no Roblox.
- [x] Auditar acervo e acrescentar diagnóstico por partes (`comparar-referencias`) com teste no pavão v2 rejeitado. Método e limites em [[aprendizado-por-gabaritos]], decisão [[0006-comparacao-por-partes-e-gabaritos]]. Não equivale a um gerador treinado.
- [ ] Curar piloto de exemplos com conceitos, correspondências e landmarks; medir reconstrução e extrapolação em casos reservados antes de decidir treinamento.

---

## Melhorias depois da primeira criatura (não fazer antes)
- Malha intermediária para formas difíceis (Hunyuan3D 3.1 grátis, 20 por dia; TRELLIS.2) com segmentação de partes, se a medição 2D não der conta.
- Leitura "estratégia B": o código propõe regiões numeradas e a IA só dá nome, se a leitura por caixas errar demais.
- Mais animações (ataques com marcadores de combate, expressões) e VFX nos locators.
- Teste automático no Roblox Studio pelo MCP do Studio.
- Processar várias criaturas em lote.
