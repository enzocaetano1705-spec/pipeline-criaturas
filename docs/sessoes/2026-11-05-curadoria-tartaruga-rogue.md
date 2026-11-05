---
tipo: sessao
data: 2026-11-05
fase: exploração A.2.1
ia: codex
status: curadoria e propostas textuais prontas; direção/arte não aprovadas
---

# Curadoria pessoal e piloto tartaruga monge rogue

**Decisão para o usuário:** qual direção explorar — Sutruga (impulso armazenado),
Mirágua (engodo por reflexos) ou Vesperuga (liberação espiritual controlada)?
Raridade e quantidade de formas permanecem abertas. Nenhuma arte foi gerada.

**Entradas confirmadas:** sete links com função: 619 conceito/cores/evolução;
721 cores, estágio 0; 594 conceito, estágio 3; 214 conceito/evoluções;
613 evoluções, estágio 0; 642 cores/conceito, estágio 0; 433 conceito. Nos links
sem parâmetro não foi presumido um estágio preferido. O usuário escolheu
**monge + tartaruga** para o piloto e exigiu **rogue** como arquétipo de combate,
destacando o contraste com velocidade. Isso substitui qualquer leitura do
exemplo anterior como criatura puramente lenta/defensiva.

**Feito:** 28 artes e metadados conferidos, em duas folhas de até 768 px,
originais/cache fora do repositório, em
`~/Downloads/referencias-criaturas/estudos/miscrits/curadoria-2026-11-05/`.
Papéis cromáticos de Geneseed/Chico/Nyma amostrados, sem inventar hex por aparência;
quantização serve para estudo, não define paleta oficial. O guia v0.1 distingue
preferência por conceito, cor ou progressão, sem importar anatomia de uma
referência escolhida apenas por cores. Não foi analisado o catálogo inteiro.

**Artefatos:** `docs/direcao-arte/guia-visual-v0.1.md` e
`docs/direcao-arte/pilotos/tartaruga-monge-rogue/{briefing.json,propostas.md}`.
Três direções textuais com tese, mecanismo, progressão, visual, assinatura de
combate, limitação e risco artístico. Nomes provisórios, sem garantia de
originalidade absoluta e sem revisão independente já executada. Recomendação
inicial do autor: Sutruga por expressar diretamente repouso versus arrancada.

**Contrato consultado somente para leitura:**
`../jogo-criaturas/docs/decisoes/0022-raridades-formas-e-arquetipos.md`.
Comum tem 1 forma, Raro 2, Épico em diante 3. Corrigida a suposição anterior de
três por padrão. Quantidade nula é aceita na exploração textual; antes de arte/
vistas aprovadas precisa estar definida. Nenhuma raridade/subclasse/kit numérico
foi decidido. O arquétipo é requisito de entrada/revisão; seu kit continua proposta.

**Mudanças no preparador:** requer `arquetipo_combate`; permite quantidade nula
na fase de texto, recusa aprovação de arte/vistas com formas indefinidas e
quantidade booleana. Prompts e exemplo atualizados. Saídas novas em
`modelos/_direcao-arte/tartaruga-monge-rogue-01/` e `-02/`, sem sobrescrever pilotos
anteriores. Sem IA/API paga, treino ou instalação.

**Validação:** duas preparações byte a byte idênticas e hashes corretos; saída
existente recusada; falta de arquétipo, arte aprovada sem formas e quantidade
booleana recusadas sem criar saída. Compileall/diff-check passam. Não repetir
testes 3D: seus módulos não mudaram. Documentos/modelos/texturas manuais do usuário
preservados, fora do commit; nenhuma escrita no jogo ou controle de Studio/Blender.

**Próximo passo:** escolha humana de direção e refinamento do plano de família;
confirmar raridade/formas antes da arte, gerar dentro das cotas existentes,
revisar e aprovar. Orçamento permanece R$ 50 único como teto futuro; gasto atual
zero adicional, sem autorizar compra ou LoRA. Não modelar nesta etapa.
