---
tipo: sessao
data: 2026-10-21
fase: 10
ia: codex
---

# Sessão — método de geração com gabaritos

**Pedido:** o usuário rejeitou a aparência do pavão e pediu um método generalizável para aprender soluções de modelos reais, relacionando ilustrações, renders e construção em JSON. O foco desta sessão foi o método e a avaliação, não produzir outra versão visual sem diagnóstico.

**Feito:** auditoria do catálogo (525 entradas: 522 Digimod e 3 Cobblemon); pesquisa em fontes primárias; diagnóstico do pavão v2 contra Koromon; novo comando `criaturas comparar-referencias`; testes e integração à skill. Decisão [[0006-comparacao-por-partes-e-gabaritos]], método completo em [[aprendizado-por-gabaritos]].

**Falha encontrada:** a v2 transferiu a contagem de peças, mas mudou a função dos volumes, distribuição do rosto, densidade e orientação dos planos. A gema de 9 px de altura foi cortada numa ilha de 5 px. Olhos mais centralizados e sem continuação nas laterais perderam a expressão. O estudo anterior já continha evidências que poderiam evitar essas decisões. “0 erros técnicos” não avalia arte.

**Resultado executável:** `modelos/criatura-pavao/diagnostico-referencias/caso-koromon-v2.json` e `comparacao-koromon-v2.json` com 32 comparações agregadas e hashes dos dois inputs. O comando não copia geometria/texturas, não altera os modelos e deixa a arte como não avaliada. As medidas em repouso ignoram inflate, alfa na geometria e oclusão, com limitações explícitas; ausência de textura incorporada não vira comparação entre pixels e unidades UV.

**Validação:** 41 testes passaram, cobrindo novo diagnóstico, referências e CLI. Incluem invariância de escala/translação, hierarquia 4/5, orientação dos planos, pivô implícito, UV espelhado, alpha, diferentes resoluções de imagem/UV, seletor inválido, dados não comparáveis e proteção dos arquivos de entrada.

**Próximo trabalho:** piloto curado com correspondências/landmarks; reconstrução do pavão pela solução estrutural dominante de Koromon; depois exercícios com gabaritos ocultos e casos reservados. Isso permanece pendente. Não houve treinamento de rede, implementação de busca visual, ajuste automático ou comprovação de generalização nesta sessão. A fase 10 segue aberta.
