---
data: 2026-11-05
status: hipótese de treino em avaliação; nenhum treino ou compra executados
---

# Estudar linguagem de formas e testar LoRA com orçamento limitado

O usuário reconheceu melhora de leitura no novo monge armado, mas rejeitou a
distância em relação ao estilo Miscrits: cauda, desproporções deliberadas e
harmonia entre parte superior e inferior ainda não foram traduzidas. Especificou
lâminas de jade como as do Kai em Kung Fu Panda. Essa comparação é referência
visual dada pelo usuário, não confirmação da inspiração autoral de Niojade.

## Diagnóstico revisado

- A v3/v4 tem anatomia próxima de humano musculoso: pernas longas/definidas,
  tronco e braços proporcionais, cauda curta e adagas convencionais pequenas.
  Isso adicionou sinais de monge/rogue, mas não aprendeu a estilização escolhida.
- Niojade concentra dominância em braços/armas e tronco, com região inferior
  compacta; a cauda curva participa da silhueta. A coerência nasce das relações
  entre essas partes, não da aproximação a proporções humanas normais.
- O prompt v3 ainda impôs **short tail**, pernas poderosas e adagas compactas
  em folha/crescente de pedra clara. Essas foram decisões do autor e devem ser
  corrigidas antes de atribuir tudo à capacidade do gerador.
- A ligação com Kai especifica volume, curvatura, matéria jade e presença das
  armas na composição. Não basta escrever “adagas” e aceitar um par genérico.

Não gerar outra imagem nesta rodada. A questão agora é separar qualidade de
direção de arte e capacidade do modelo de assimilar a linguagem visual.

## O papel possível de um LoRA

LoRA de estilo é hipótese para regularidades de **formas, proporções, contorno,
sombras, cor e composição**, não só acabamento. Não há ensaio ainda demonstrando
que ele resolve este caso. História e lógica de evolução continuam no fluxo de
conceito; um LoRA de imagens não equivale a um sistema narrativo.

Não treinar diretamente um lote bruto só porque ele é grande. O [treinador da
Replicate](https://replicate.com/replicate/fast-flux-trainer/readme) recomenda
diversidade de assuntos com consistência de estilo e evitar conteúdo dominante.
Escolher o modelo base compatível e avaliar sua geração sem LoRA primeiro.
Comparar o **mesmo modelo** com/sem adaptador; trocar do gerador nativo para outro
modelo e atribuir toda diferença ao LoRA não é um teste causal.

## Auditoria do catálogo inteiro: metadados, não treino

Consulta ao endpoint público `https://worldofmiscrits.com/miscrits.json`:

- 439 registros de linhagens, todos com quatro nomes: **1.756 entradas de estágio**.
- **112 variantes** cujos nomes Dark/Light/Foil/Blighted têm uma base correspondente
  por remoção de prefixo; **327 grupos** por essa heurística.
- Isso não prova que arquivos são duplicados, que pertencem ao mesmo artista
  ou que o catálogo tem um único acabamento. Exige revisão visual posterior.
- No cache seletivo de 44 artes já inspecionadas, todas têm maior lado abaixo de
  512 px (máximo 507). Não extrapolar ao catálogo inteiro. Procurar fonte melhor
  quando possível; ampliar PNG não cria desenho/detail novo.

Usar **todo o catálogo para inventário e curadoria**. Um primeiro conjunto de
treino deve ser selecionado de modo consciente, não conter obrigatoriamente tudo.
As variantes favoritas, como Blighted Flue, não são proibidas; agrupá-las para
não supercontar o mesmo corpo e não vazar variantes entre treino e teste.

Originais/cache e inventário completo permanecem na biblioteca externa:
`~/Downloads/referencias-criaturas/estudos/miscrits/`. No repositório ficam ferramenta,
resumo, conclusões e metadados de experimento. O inventário não é um dataset
validado, licenciado ou pronto para upload.

```powershell
uv run python scripts/auditar-catalogo-miscrits.py --saida "$env:USERPROFILE/Downloads/referencias-criaturas/estudos/miscrits/auditoria-nova"
```

Para repetir sem rede, informar `--arquivo <catalogo-publico.json>` e outra saída.

## Experimento proposto antes de gastar

1. **Definir o alvo visual.** Ficha de proporções por exemplo: dominância
   cabeça/tronco/braços/pernas, papel da cauda, exageros intencionais, tipos de
   armas, espaços negativos e relação entre grandes/médias/pequenas formas.
   Essas medidas não viram uma receita anatômica universal para todas as espécies.
2. **Curar candidatos do catálogo.** Cobrir animais/objetos e planos de corpo,
   estágios, graus de exagero, paletas e densidades de detalhe, mantendo acabamento
   coerente. Auditar recorte, alfa/fundo, tamanho, compressão e repetições visuais.
3. **Primeiro treino pequeno e controlado.** Como hipótese de projeto, selecionar
   50–100 imagens curadas, ajustável após escolher modelo/orçamento. Não é mínimo
   técnico nem tamanho ideal comprovado. Guardar o restante como expansão posterior.
4. **Separar por família/grupo antes do treino.** Toda a família e suas variantes
   ficam no mesmo conjunto; reservar linhagens inteiras, inclusive a família
   Turtudi/Niojade num teste de generalização, para detectar memorização. Uma
   avaliação que fornece a imagem-alvo como condicionamento tem de ser identificada.
5. **Legendar conteúdo e estrutura observável.** Espécie, postura, partes e
   proporções, armamento, material, cor e estágio quando pertinentes; revisar
   autocaptions para não apagar caudas/membros ocultos ou chamar tudo de humano.
   A associação de estilo deve seguir a receita do treinador escolhido.
6. **Controle e avaliação.** Mesmos briefs inéditos, resolução, número de tentativas
   e configurações comparáveis no modelo base e com LoRA. Julgar linguagem de formas,
   acabamento, legibilidade, variedade e semelhança excessiva com treino. Seeds não
   garantem determinismo entre provedores. Não escolher checkpoint apenas pela loss.
7. **Só depois expandir.** Treino maior/catálogo inteiro precisa mostrar ganho
   medido sobre o piloto; não aumentar corpus ou passos para encobrir um briefing
   que continua impondo proporções erradas.

## Viabilidade e orçamento

O teto continua **R$ 50 uma única vez**, sem mensalidade nova. Não houve
autorização de compra ou execução de treino. Custo depende de configuração,
passos, resolução, pré-processamento, tempo/armazenamento e quantidade de testes;
número de imagens sozinho não determina a conta.

A estimativa anterior de **US$ 1,46** era um exemplo pequeno do guia Replicate,
não uma cotação para 1.756 imagens. A [página do treinador](https://replicate.com/replicate/fast-flux-trainer/train)
consultada lista US$ 0,0122/s. Dez minutos nessa taxa seriam US$ 7,32 antes de
outros custos; isso ilustra por que não prometer o catálogo inteiro por R$ 50.

Há opções a estudar: o [guia FLUX.2 klein publicado pela Black Forest Labs no
Hugging Face](https://huggingface.co/blog/black-forest-labs/flux-2-klein-lora)
descreve treino LoRA do base 4B em GPU de 24 GB. Sua indicação de cerca de uma
hora/~US$ 0,50 refere-se à receita/provedor do exemplo, com conjunto pequeno;
não é cotação para nossos dados. Esse requisito de GPU é superior aos 6 GB
do notebook atual; a nuvem é uma opção, sem prometer treino local nessa receita.

Antes de executar, preparar modelo/configuração, dataset/split, orçamento final
em reais com recarga mínima/câmbio/taxas e limite de execução, além de onde rodar
a inferência depois. Adapter pequeno não remove a necessidade do modelo base
nem torna gerações posteriores gratuitas. Não criar assinatura/reload automático.

O acesso público às artes não informa por si só as condições para treinamento,
upload de dados/pesos ou uso no jogo. Registrar termos/permissão/origem e licença
do modelo/ambiente antes de escolher o conjunto executável. Não presumir
permissão ou proibição universal apenas a partir do URL.

**Resultado desta etapa:** diagnóstico e inventário de metadados, não um treino
realizado nem promessa de qualidade. V3/v4 não têm aprovação artística; próximas
gerações devem aguardar estudo de forma e decisão do experimento.
