# Protocolo de classificação (a parte da IA)

Entrada: as imagens com grade de `modelos/<nome>/eN/preparo/` e o prompt da ficha.
Saída: `modelos/<nome>/eN/checklist.json` (contrato `ferramenta/criaturas/contratos/checklist.schema.json`).
Quem pontua as categorias é o código (`criaturas classificar`), não a IA.

Custo: uma imagem de 768 px. Abra `frente-grade.png`. Se não houver frente, abra `conceito-grade.png`. Só abra `lado-grade.png` se precisar de profundidade (cauda, corpo, focinho) e a frente deixar o item incerto.

## Passo 1 — só a imagem (prompt escondido)
Não leia o prompt ainda. Olhe a imagem com grade e preencha os 13 itens. Cada item recebe:
- `valor`: no vocabulário do contrato. Prefira números medidos na grade a palavras (ex.: `{"frac_alt": 0.42}` para a cabeça).
- `certeza`: `visível` (dá para ver), `incerto` (dá para ver em parte ou é ambíguo) ou `oculto` (não aparece).
- `fonte`: `imagem`.

| Item | O que medir na grade (1 célula = 1/32 da altura) |
|---|---|
| postura | bípede, quadrúpede, rastejante, flutuante, nadando ou sem membros |
| pernas | número; se der, `frac_alt` = comprimento da perna ÷ 32 células |
| bracos | número (as pernas da frente de um quadrúpede não contam) |
| asas | `{pares, envergadura_alt, tipo}`; envergadura_alt = largura das asas abertas ÷ altura |
| cauda | `{comprimento_alt, grossura, segmentos, leque}`; comprimento_alt = comprimento ÷ altura |
| nadadeiras | número |
| pescoco | nenhum, curto, médio ou longo; `{segmentos}` se der para contar |
| cabeca | `{frac_alt}` = altura da cabeça (sem orelhas e chifres) ÷ altura total |
| focinho | `{razao_cranio}` = comprimento do focinho ÷ altura do crânio; ou nenhum, curto, médio, longo, bico |
| orelhas | `{razao_cranio}` = altura da orelha ÷ altura do crânio; ou nenhuma, pequenas, médias, grandes, enormes |
| olhos | `{frac_alt}` = altura do olho ÷ altura total |
| cobertura | pelo, escama, pena, pele, pedra, planta, gosma, metal ou carapaça |
| extras | lista: chifres, juba, carapaça, chamas, antenas, tentáculos, cascos, bigodes, bico, folhas, múltiplas cabeças, flutua… |

Itens de profundidade (comprimento do corpo e da cauda, grossura dos membros, patas escondidas) costumam ficar `incerto` numa imagem de frente. Não chute: marque `incerto` ou `oculto`.

## Passo 2 — o prompt só completa
Agora leia o prompt da ficha.
- Só mexa em itens `incerto` ou `oculto`. Troque o valor pelo que o prompt diz e mude `fonte` para `prompt` (a certeza continua `incerto` ou `oculto`).
- Item `visível` não muda, nunca. O contrato rejeita item visível com fonte diferente de imagem.
- O prompt não cria partes que a imagem não apoia.

## Passo 3 — conflitos
Se o prompt contradiz algo visível, a imagem vence. Registre o caso em `conflitos`:
```json
{"item": "cauda", "imagem": "curta", "prompt": "long flowing tail", "nota": "a cauda aparece inteira na frente"}
```

## Depois
1. Grave `modelos/<nome>/eN/checklist.json`.
2. Rode `uv run criaturas classificar <pasta> --estagio eN`. Ele valida o checklist e grava `classificacao.json` com até 3 sugestões (plano › nicho, %), os traços que justificam cada uma e o estágio aparente. Se a ficha estiver `pronta-para-modelagem`, ele também acrescenta a seção "Classificação sugerida" no fim dela.
3. **PARE numa criatura real.** O pipeline só segue com a `Categoria confirmada` preenchida na ficha pelo usuário. Escreva a pergunta no topo da nota da sessão: as 3 sugestões e "escolha 1, 2, 3 ou outra categoria".
4. Nas sintéticas e nas imagens de `docs/criaturas/_testes/`, siga com a categoria verdadeira ou com a sugestão 1.
5. Se o usuário escolher algo diferente da sugestão 1, rode `uv run criaturas classificar <pasta> --estagio eN --registrar-escolha "plano › nicho"`. Isso anexa a correção em `referencia/correcoes-classificacao.jsonl`.

## Exemplo de checklist
```json
{
  "estagio": "e1",
  "vista": "preparo/frente-grade.png",
  "itens": {
    "postura": {"valor": "quadrúpede", "certeza": "visível", "fonte": "imagem"},
    "pernas": {"valor": {"n": 4, "frac_alt": 0.27}, "certeza": "visível", "fonte": "imagem"},
    "bracos": {"valor": 0, "certeza": "visível", "fonte": "imagem"},
    "asas": {"valor": 0, "certeza": "visível", "fonte": "imagem"},
    "cauda": {"valor": {"comprimento": "longa", "grossura": "grossa"}, "certeza": "incerto", "fonte": "prompt"},
    "nadadeiras": {"valor": 0, "certeza": "visível", "fonte": "imagem"},
    "pescoco": {"valor": "curto", "certeza": "visível", "fonte": "imagem"},
    "cabeca": {"valor": {"frac_alt": 0.4}, "certeza": "visível", "fonte": "imagem"},
    "focinho": {"valor": {"razao_cranio": 0.45}, "certeza": "incerto", "fonte": "imagem"},
    "orelhas": {"valor": {"razao_cranio": 0.9}, "certeza": "visível", "fonte": "imagem"},
    "olhos": {"valor": {"frac_alt": 0.1}, "certeza": "visível", "fonte": "imagem"},
    "cobertura": {"valor": "pelo", "certeza": "visível", "fonte": "imagem"},
    "extras": {"valor": [], "certeza": "visível", "fonte": "imagem"}
  },
  "conflitos": []
}
```
