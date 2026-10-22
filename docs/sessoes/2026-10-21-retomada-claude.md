---
tipo: retomada
data: 2026-10-21
fase: 10
ia: codex
status: pronto para continuidade no Claude
---

# Retomada no Claude — ponto exato de 21/10/2026

## Comece aqui

Abra o Claude Code na raiz `C:\Users\enzoc\dev\pipeline-criaturas`. O vault do Obsidian é a pasta `docs/`. Leia `AGENTS.md`, esta nota e [[aprendizado-por-gabaritos]] antes de retomar. O usuário pediu registrar o estado porque os limites do Codex estão acabando; não solicitou outra modelagem durante o registro.

**Estado decisivo: o modelo e a textura do pavão v2 foram REJEITADOS pelo usuário. As animações do ensaio foram consideradas boas.** A fase 10 continua aberta. Não tratar a v2 como aprovada, não exportá-la como resultado final e não pedir aprovação da mesma versão novamente.

## Objetivo vigente e preferências confirmadas

- Construir um método que use ilustração, render, geometria/JSON, atlas e animações de modelos refinados como exemplos verificáveis e gabaritos.
- Extrapolar soluções **por parte e função** para criaturas originais: corpo, rosto, penas, chifres, membros, proporções e articulações. O usuário fornecerá as vistas necessárias.
- O pavão baby é o caso inicial de adaptação de Koromon: corpo, localização do rosto e construção dos apêndices são a referência dominante. As orelhas/antenas da referência correspondem funcionalmente às penas ornamentais do pavão.
- Usar pouquíssimos volumes e planos grandes. Detalhes de rosto, penugem, dentes, gema e marcas ficam principalmente na pintura. Não arredondar automaticamente com dezenas de fatias/cubos.
- Estágio confirmado: **1 de 3**. Primeiro estágio pouco diferenciado; segundo avinídeo; terceiro avinídeo mais humanoide. Nome provisório: `criatura-pavao`.
- Categoria de trabalho: `cabeça-corpo › ave`; não reinterpretar isso como obrigação de acrescentar anatomia de ave. Não há pernas, braços, asas ou cauda na imagem do baby. As duas penas são ornamentos no topo.
- Conceito: turquesa, olhos âmbar grandes, sorriso com pequenos dentes, gema dourada e duas penas arqueadas com ocelos. Altura de trabalho provisória de 1 bloco; destino principal Roblox.
- A imagem do usuário governa as características e proporções. A analogia com Koromon governa a solução construtiva; a abertura das penas e os detalhes continuam específicos do pavão.

## Arquivos e versões para não confundir

Caminhos abaixo são relativos à raiz do repositório, salvo quando indicado.

| Arquivo/pasta | Estado e função |
|---|---|
| `docs/criaturas/criatura-pavao/ficha.md` | Ficha `pronta-para-modelagem`, com conceito e vistas recortadas ao lado |
| `modelos/criatura-pavao/e1/criatura-pavao-e1.bbmodel` | Versão principal simplificada anterior: 8 peças; não é a versão artística final aprovada |
| `modelos/criatura-pavao/e1/historico-versoes/antes-simplificacao-38.bbmodel` | Versão antiga com 38 peças, preservada como histórico; contraria a preferência vigente de simplicidade |
| `modelos/criatura-pavao/estudo-referencias/pavao-planos-animado.bbmodel` | Ensaio: 2 volumes, 6 planos, 12 ossos; fonte das animações a preservar |
| `modelos/criatura-pavao/estudo-referencias/previa-movimento.gif` | Prévia do movimento do ensaio |
| `modelos/criatura-pavao/revisao-v2/criatura-pavao-e1-v2.bbmodel` | V2 rejeitada: 3 volumes, 6 planos, atlas 128×128; material de comparação, não resultado final |
| `modelos/criatura-pavao/revisao-v2/folha.png` | Folha que evidencia os problemas da v2 |
| `modelos/criatura-pavao/revisao-arte-v2.py` | Gerador da v2; não executá-lo como se fosse uma correção aprovada |
| `modelos/criatura-pavao/diagnostico-referencias/caso-koromon-v2.json` | Mapeamento explícito corpo/ornamentos para comparação |
| `modelos/criatura-pavao/diagnostico-referencias/comparacao-koromon-v2.json` | Relatório agregado com hashes e 32 comparações |

Outros scripts reproduzíveis: `ensaio-referencias.py`, `simplificar-geometria.py`, `pintar-estilo-simples.py` e `refinar-geometria.py`, dentro de `modelos/criatura-pavao/`. Eles representam etapas históricas distintas; não rodar todos em sequência indiscriminadamente.

Animações próprias aprovadas no ensaio: `idle` (2,4 s) e `walk` (1,33 s), com movimento secundário nas penas. A v2 conservou esses clipes, mas alterou a construção e alguns pivôs. Preservar a intenção e conferir compatibilidade ao reconstruir. `blink` não foi implementado: olhos são pintados, ossos vazios não piscam.

## Referências externas disponíveis

Biblioteca: `C:\Users\enzoc\Downloads\referencias-criaturas`.

- 525 entradas indexadas: **522 The Digimod e 3 Cobblemon** (Goomy, Sliggoo e Goodra).
- Greninja, Ceruledge e Koraidon foram exemplos sugeridos pelo usuário, mas **não estão no catálogo local**.
- 461 projetos `.bbmodel` e 64 geometrias JSON escolhidos pelo catálogo; 460 projetos com textura embutida registrada. Existem duplicatas/recolors; 525 arquivos não significam 525 famílias independentes.
- Estudo pareado de Koromon: `estudos/koromon/estudo-koromon.md`, `estudo-koromon-768.png`, `resumo-inspecao.json` e `textura-original-64.png`.
- Modelo real de Koromon: `the-digimod/blockbench/babies2/koromon.bbmodel`.
- Índice: `.catalogo-estrutural.json`; fontes de Goomy: `linhagem-goomy/fontes.json`; índice Digimod: `the-digimod/indice-modelos.json`.
- Koromon tem **2 volumes e 4 planos**, com rosto pintado num atlas 64×64. Os planos são faixas amplas em orientações complementares e recorte alfa; não são simplesmente quatro apêndices independentes.
- Harpymon já foi estudado para penas em planos. Consultar estudos existentes antes de repetir downloads ou pesquisas.

As bibliotecas e os estudos visuais externos permanecem fora do Git do pipeline. Preservar originais; copiar apenas técnicas e conclusões para construções próprias. Não incorporar geometria, textura, código ou chaves de animação dos mods às criaturas originais.

## Diagnóstico que deve guiar a próxima tentativa

1. A v2 transferiu contagens, mas perdeu a função dos volumes: em Koromon, a parte inferior tem a mesma largura e avança para formar mandíbula/boca; na v2 a base ficou menor e recuada.
2. Profundidade/largura do corpo: cerca de 0,917 na referência e 0,75 na v2. A construção ficou proporcionalmente mais achatada.
3. Os olhos da v2 ficaram menores relativamente, mais próximos e concentrados na frente. O perfil perdeu a leitura do rosto. As posições de Koromon foram estimadas visualmente; ainda precisam virar landmarks anotados.
4. A boca subiu para o volume principal e os dentes ficaram grandes/próximos, dominando o sorriso.
5. A gema usa motivo de **9 pixels de altura numa ilha de 5 pixels**: está cortada por construção. Não confundir aumento do atlas com espaço suficiente para cada motivo.
6. A v2 usa aproximadamente 2 texels/unidade, contra 1 na referência. Densidade e tamanho relativo dos motivos precisam ser decisões explícitas.
7. As raízes das penas ficaram finas como fios, e as lâminas giradas em Y deixam uma pena quase de canto em 3/4. Koromon resolve volume aparente por planos complementares.
8. A v2 teve 0 erros técnicos e 6 avisos geométricos; isso nunca constituiu aprovação visual. O corpo ser cubificado, por si só, não é defeito no estilo escolhido.

## O que já foi implementado e testado

Commit do último trabalho de método: `735943a` — “Acrescenta diagnóstico por partes e método de avaliação com gabaritos”. O registro de retomada pode gerar commits posteriores; confira `git log` para o checkpoint final.

Novo comando `criaturas comparar-referencias`, módulo `ferramenta/criaturas/comparar_referencias.py`. Compara dimensões e centros normalizados por uma parte âncora, volumes/planos, áreas projetadas dos planos e medidas de UV/alfa. Seletores por tipo, osso ou elemento; suporta projetos 4/5. Não compara igualdade literal de JSON e não dá aprovação artística.

Limites: caixas em repouso sem inflate/oclusão/recorte alfa; não detecta olhos, boca, gema, qualidade de pixel art nem silhueta visível automaticamente. Uma textura incorporada e UV explícito; unidades não comparáveis são separadas. Os modelos de entrada não são alterados.

```powershell
uv run pytest ferramenta/testes/test_comparar_referencias.py ferramenta/testes/test_referencias.py ferramenta/testes/test_cli.py -q
uv run criaturas comparar-referencias modelos/criatura-pavao/diagnostico-referencias/caso-koromon-v2.json --saida modelos/criatura-pavao/diagnostico-referencias/comparacao-koromon-v2.json
uv run criaturas referencias buscar koromon
```

Resultado confirmado: **41 testes passaram**. Não significa suíte inteira rodada nesta última mudança. A skill e suas cópias `.agents/skills`/`.claude/skills` foram sincronizadas; o pacote de skill para chat também foi regenerado.

## Próximas ações exatas

1. Ler [[aprendizado-por-gabaritos]], [[0006-comparacao-por-partes-e-gabaritos]], [[0005-estudar-referencias-por-estrutura]] e o estudo externo de Koromon. Não recomeçar pesquisa geral.
2. Anotar landmarks de olhos/boca/gema e relações corpo/mandíbula/ornamentos por vista; registrar correspondências e diferenças necessárias. Planejar capacidade em pixels e continuidade das faces antes de pintar.
3. Criar **uma nova versão** do pavão com a solução estrutural dominante de Koromon, medidas adaptadas ao conceito e arte própria. Usar operações em lote pelo motor; preservar modelos existentes e conferir os clipes aprovados.
4. Comparar render frente/perfil/costas/3/4, com câmera/escala consistentes, contra a v2 e as referências. Corrigir motivos cortados, olhos ausentes, proporções incompatíveis e planos invisíveis antes de pedir aprovação artística.
5. Curar um piloto proposto de 12 casos (escopo de trabalho, não mínimo científico), distribuído entre famílias estruturais. Guardar conceito, render, atlas, decisões e diagnóstico; medir o benefício frente ao método anterior.
6. Separar produção com referências disponíveis de avaliação com gabarito oculto. Congelar a tentativa antes de revelar o alvo; manter duplicatas/recolors/parentes próximos na mesma partição. Testar reconstrução conhecida, adaptação e combinações inéditas separadamente.
7. Só decidir treinamento de componentes após essa linha de base. **Não houve treinamento de rede, busca visual aprendida, ajuste automático de parâmetros nem prova de generalização.** O comparador é uma primeira ferramenta de diagnóstico.

## Texto pronto para enviar ao Claude Code

> Continue no repositório C:\Users\enzoc\dev\pipeline-criaturas. Leia AGENTS.md e docs/sessoes/2026-10-21-retomada-claude.md. Retome o método de modelagem por referências e gabaritos do exato estado registrado: pavão v2 rejeitado, movimentos do ensaio aprovados, comparador por partes implementado com 41 testes. Comece pelas correspondências e landmarks de Koromon/pavão e pela reconstrução em uma nova versão; preserve as versões existentes. Não trate o diagnóstico como um gerador já treinado nem repita pesquisas registradas.
