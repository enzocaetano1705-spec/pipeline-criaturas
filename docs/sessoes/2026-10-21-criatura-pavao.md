---
tipo: sessao
data: 2026-10-21
fase: 10
ia: codex
---

# Sessão 2026-10-21 — criatura-pavao

**Estado artístico atual:** o usuário rejeitou o modelo e a textura da revisão v2. Solicitou melhorar o método usando exemplos reais como perguntas/gabaritos e soluções por partes. A v2 não está aguardando aprovação nem deve ser exportada como resultado aprovado. Diagnóstico e próximos aceites em [[aprendizado-por-gabaritos]]; sessão em [[2026-10-21-metodo-gabaritos]].

**Revisão v2 executada:** `modelos/criatura-pavao/revisao-arte-v2.py` gerou uma cópia independente em `revisao-v2/criatura-pavao-e1-v2.bbmodel`, com 3 volumes sólidos, 6 planos de penas, atlas original 128×128 com recortes alfa e rosto pintado em maior resolução. Os grupos, pivôs compatíveis e as animações `idle`/`walk` do ensaio foram preservados. Validação do motor: 0 erros de geometria e 6 avisos; animações: 0 erros e 0 avisos. A versão principal e o ensaio anterior ficaram intactos; exportação Roblox/Minecraft ainda pendente de aprovação da folha.

**Revisão atual:** workflow de estudo por referências implementado e ensaio separado em `modelos/criatura-pavao/estudo-referencias/pavao-planos-animado.bbmodel`: 2 volumes, 6 planos e movimentos próprios `idle`/`walk`. O modelo principal `e1` foi preservado. Exportação e teste no Roblox ainda não concluídos.

**Feito:** vistas separadas da prancha original, ficha criada e imagens preparadas. Checklist segue somente a imagem. Usuário confirmou estágio 1 de 3. Nome provisório criatura-pavao. Prompt original não fornecido.

**Decisões:** corpo único, sem pernas, braços, asas ou cauda inventados. As duas penas são ornamentos no topo. O usuário esclareceu a linhagem: primeiro estágio pouco diferenciado, segundo avinídeo, terceiro avinídeo humanoide. Categoria de trabalho registrada como cabeça-corpo › ave; a tabela não dita a anatomia. Altura de trabalho provisória de 1 bloco, mantendo proporções da imagem.

**Modelagem:** leitura com 11 partes, 38 cubos, 12 ossos e 5 locators. Refino reproduzível em `modelos/criatura-pavao/refinar-geometria.py`, sem escrever `.bbmodel` diretamente: 24 volumes contíguos arredondam corpo em X, Y e Z. Penas inclinadas em 45 graus, três segmentos por lado, visíveis de perfil. Todas as edições passam pelo motor em lote. Atlas 128×128.

**Validação:** 0 erros; 12 avisos de interpenetração nas caixas envolventes dos planos inclinados das penas. Bases enterradas cerca de 1 unidade no corpo e segmentos encostados para evitar frestas, conforme convenção. Nenhum aviso entre os volumes do corpo. Diferenças entre vistas de boca (16%) e gema (19%) decorrem da perspectiva do perfil. Vistas recortadas têm resolução inferior à recomendada: usa-se a informação original, sem inventar detalhe.

**Melhorias identificadas no workflow:** o leitor de campos vazios pode consumir a linha seguinte (categoria/altura); contornado preenchendo os campos da ficha criada nesta sessão. Cubificação automática só arredonda por camadas horizontais; corrigido localmente neste modelo, sem mudar arquitetura ou código do pipeline. Planos vistos de frente e de lado precisam orientação explícita para não sumirem de perfil.

**Próximo passo:** aprovação da folha geométrica; depois texturizar, rig, animar e exportar. Não concluir a fase 10 antes disso. Manter o recorte alfa e os detalhes pintados para a etapa de textura, conforme a skill.

## Revisão solicitada: simplificação

- A versão arredondada de 38 peças foi substituída por 8 peças: 2 volumes de corpo e 3 segmentos por pena. A anterior está preservada em `modelos/criatura-pavao/e1/historico-versoes/antes-simplificacao-38.bbmodel`.
- Removidos os planos de rosto. Olhos âmbar, sorriso, dentes e gema foram pintados no próprio corpo, com atlas 64×64. Os ocelos das penas usam pintura original. UVs independentes corrigem a pena que desaparecia com a projeção automática espelhada.
- Correções realizadas pelo comando `aplicar` e guardadas em `e1/correcoes/`. Plano sincronizado com a geometria atual. Scripts reprodutíveis: `simplificar-geometria.py` e `pintar-estilo-simples.py`.
- Validação final: 0 erros e 4 avisos de encaixe de 1 unidade nas raízes e segmentos das penas, mantidos para evitar frestas. Textura sem transparência em faces de volume; transparência apenas nas pontas das penas.
- A pintura automática apagava o sorriso e uma pena; substituída por pixel art original para esta revisão. Não é uma textura extraída das referências externas.
- Direção artística registrada em [[0004-direcao-artistica-simples]] e `docs/convencoes.md`. O arredondamento detalhado anterior não representa mais a preferência vigente.
- Ainda sem animações. O blink baseado em planos dos olhos não funciona com olhos inteiramente pintados; requer solução própria se solicitado.

## Estudo por referências e ensaio separado

- Biblioteca consultável em `~/Downloads/referencias-criaturas/`, com 525 entradas indexadas. O comando `criaturas referencias` busca por estrutura e inspeciona contagens, proporções, UV, hierarquia e clipes sem modificar os modelos. Tags são pistas pelos nomes e precisam de confirmação visual.
- Estudo de Koromon em `estudos/koromon/` na biblioteca: ilustração, vistas reais e atlas comparados. São 2 volumes e 4 planos; as antenas são faixas largas com recorte alfa. Há 77 clipes incorporados, mas os dados da espécie selecionam apenas seis da biblioteca compartilhada.
- Harpymon confirmado visualmente como referência de penas ornamentais em planos; não interpretar a presença de penas como asas ou voo. Referências por função, registradas em `skills/criaturas-3d/referencias.md` e na decisão [[0005-estudar-referencias-por-estrutura]].
- `modelagem.abordagem: poucas_formas` agora evita o fatiamento automático na cubificação. A opção é declarada na leitura e mantém o comportamento anterior como padrão para os arquivos existentes.
- Ensaio do pavão mantém as 8 peças, mas troca os 4 segmentos sólidos das penas por planos: 2 volumes + 6 planos. Atlas original adaptado e recortado; nenhuma textura ou chave de animação de terceiros incorporada. Prévia em `estudo-referencias/previa-movimento.gif`.
- `idle` e `walk` são funções próprias assadas em chaves numéricas, com movimento secundário nas penas. Validação das animações: 0 erros e 0 avisos. `blink` omitido porque os olhos estão pintados e seus ossos não têm geometria visível.
- Geometria do ensaio: 0 erros e 4 avisos de caixas envolventes das penas inclinadas sobrepostas ao corpo (0,78–1 unidade), mantendo as raízes encaixadas. Arquivo aberto e movimento `idle` iniciado no Blockbench 5.2.2. É um ensaio técnico, ainda sujeito à revisão visual da criatura.
- Mecanismos procedurais de Cobblemon, estados e quirks documentados em [[animacoes-e-mecanismos-reutilizaveis]]. Seleção de estado e olhar dependente de alvo precisam de comportamento no jogo de destino; não são clipes universais.
- Testes relacionados: 56 passaram. Avaliação independente confirmou a seleção de Koromon para corpo e Harpymon para penas, conferindo render e atlas. A fase 10 continua aberta até a revisão artística, exportação e teste de importação.
