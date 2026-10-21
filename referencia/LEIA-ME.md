# Referência

| Pasta ou arquivo | Para quê |
|---|---|
| `medidas.json` | Faixas `[p25, mediana, p75]` medidas em 905 modelos do Cobblemon e 270 do The Digimod: por estágio, plano de corpo, nicho (com sub-tabela por estágio), assinatura de evolução (469 + 427 pares) e estatísticas de estilo. Só números agregados. Lido pelo código; para consultar, use `uv run criaturas medidas …` em vez de abrir o arquivo inteiro. |
| `exemplo-headless/` | Teste de fumaça verificado do motor headless do Blockbench (criar → editar em lote → validar → exportar). |
| `prototipo-forja/` | Protótipo antigo em Python. Renderizador, textura, paletas e animações aproveitáveis; os moldes de forma não. |
| `correcoes-classificacao.jsonl` | Criado na Fase 2: cada vez que o usuário escolhe uma categoria diferente da sugestão 1. |

## Como ler `medidas.json`
- `_sobre`: unidades, fontes e cuidados.
- `estagios.cobblemon["1º de 3"]`, `estagios.digimod["Rookie"]`…: faixas por estágio.
- `planos_de_corpo["quadrúpede"]` e `nichos["dragão"]`: faixas gerais e `por_estagio` (inicial, meio, final, único, lendário). Grupos com menos de 3 modelos vêm como `poucos_dados`.
- `assinatura_evolucao`: razões e diferenças entre cada estágio e o seguinte, mais as `regras_validacao_sugeridas`.
- `estilo_cobblemon`: peças planas, cubos rotacionados, locators, texturas, animações mais comuns e nomes de ossos.

Exemplo em Python:
```python
import json
m = json.load(open("referencia/medidas.json", encoding="utf-8"))
m["nichos"]["dragão"]["por_estagio"]["final"]["altura_blocos"]   # [3.4, 3.7, 4.73]
```
