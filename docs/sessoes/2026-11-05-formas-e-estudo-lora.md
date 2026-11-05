---
tipo: sessao
data: 2026-11-05
fase: estudo A.3.1
ia: codex
status: arte ainda sem aprovação; estudo de corpus e experimento LoRA preparado
---

# Gramática de formas e estudo sério de LoRA

**Retorno do usuário:** v3/v4 melhorou informalmente cerca de 70% na percepção
dele, mas continua muito distante do estilo Miscrits. Destacou cauda, desproporção
harmônica entre inferiores/superiores e armas de jade como as do Kai em Kung Fu
Panda. Sugeriu seriamente treinamento LoRA com toda a Miscripedia. Não equivale
a aprovação da arte ou autorização de gasto/treino.

**Diagnóstico:** a nova rodada resolveu parte da leitura de monge armado,
mas resultou num humano musculoso com traços de tartaruga. O próprio prompt
impôs cauda curta, pernas poderosas e lâminas compactas genéricas. A direção
deve tratar desproporções, ritmo entre massas, cauda e morfologia das armas;
LoRA é hipótese para essas regularidades de forma e acabamento, não só pincelada.
Inspiração em Kai é a comparação do usuário, não fato autoral verificado.

**Rodada anterior agora registrada:** v3 recebeu a imagem de Niojade como
referência real na ferramenta nativa; v4 recebeu v3 para completar o enquadramento.
As duas chamadas já haviam ocorrido quando o novo retorno chegou. Quatro PNGs
(originais/prévias), dois prompts e metadados preservados/versionados. Não houve
nova geração nesta avaliação. Nenhuma dessas artes foi aprovada.

**Auditoria:** ferramenta `scripts/auditar-catalogo-miscrits.py`, biblioteca padrão,
GET do JSON público ou repetição offline. 439 linhagens, 1.756 entradas de estágio;
112 variantes com base por nome/prefixo, 327 grupos por essa heurística. Não é
contagem de duplicatas visuais nem atribuição de autoria/licença. Catálogo completo
e inventário permanecem externos em `~/Downloads/referencias-criaturas/estudos/miscrits/`;
no repo só resumo/ferramenta/conclusões. Sem baixar o acervo de imagens inteiro.
No cache seletivo já estudado: 44 artes, todas com maior lado <512 (máximo 507).
Não extrapolar essa resolução a todo o catálogo; upscaling não inventa detalhe.

**Experimento preparado:** `docs/direcao-arte/plano-lora-estilo.md`. Usar todo
catálogo para curadoria, primeiro treino coerente/equilibrado como ensaio;
separar famílias e variantes entre treino/teste, auditar resolução/alfa e legendas,
comparar o mesmo modelo com/sem LoRA e medir preferência/forma/acabamento/novidade.
Quantidade inicial 50–100 é hipótese de projeto, não mínimo ou garantia técnica.
Não tratar a base nova versus gerador nativo como ganho causal de LoRA.

**Custos:** exemplo anterior US$ 1,46 não é cotação para 1.756 imagens. Treinador
Replicate atual lista US$ 0,0122/s. Guia BFL/HF FLUX.2 klein 4B descreve uma
receita em GPU 24 GB; serve como candidato, não receita ensaiada nos nossos dados
nem promessa de rodar no notebook de 6 GB. O teto R$ 50 único e zero mensal novo
permanece. Antes de executar, preparar modelo/configuração, dados/split, local
de inferência, mínimo de recarga/câmbio/taxas e limite de execução. Sem compra,
login, instalação, upload de imagens/pesos ou treino.

**Validação:** auditoria online/offline idêntica, IDs únicos, agrupamento por base
e variante sem base conferidos em amostra pequena; entradas inválidas recusadas,
pasta existente recusada. Compileall/diff-check e hashes das novas artes/prompts
conferidos. Não repetir testes 3D: nenhum módulo desses backends foi alterado.
Fontes manuais/rascunhos/jogo/Studio preservados.

**Próximo passo:** curadoria e configuração/orçamento do experimento, não outra
imagem acabada repetindo anatomia padrão. O estudo de forma também pode produzir
um teste de massas/contorno anterior à pintura. Estado permanece experimental;
nenhum LoRA demonstrou qualidade neste projeto até ser treinado e avaliado.
