---
tags: [criaturas, entrada, pipeline-criaturas]
---

# Como preparar uma criatura para o pipeline

## Passo a passo
1. Copie a pasta `_modelo/` para `docs/criaturas/<nome>/` (minúsculas, sem acento, com hífen: `raposa-de-fogo`).
2. Salve as imagens nessa pasta com estes nomes:
   - `linhagem.png`: todos os estágios lado a lado, na mesma escala. Recomendada.
   - `e1-conceito.png`: imagem principal do estágio 1. **Obrigatória.**
   - `e1-frente.png` e `e1-lado.png`: fortemente recomendadas. Sem a vista lateral, a profundidade é estimada pela tabela da categoria.
   - `e1-costas.png`: só se as costas tiverem detalhe.
   - o mesmo para `e2-…` e `e3-…`.
3. Preencha a `ficha.md` e cole o prompt exato de cada imagem principal.
4. Quando estiver tudo pronto, mude `status: rascunho` para `status: pronta-para-modelagem`. Enquanto estiver em rascunho, nenhuma IA mexe nem faz commit dessa pasta.

Imagens antigas para teste (por exemplo, o dragão das tentativas anteriores) podem ir em `docs/criaturas/_testes/`. Elas servem para testar a classificação e a medição antes da criatura oficial.

## Requisitos das imagens
1. Corpo inteiro visível, sem cortes, uma criatura por imagem.
2. Fundo liso (branco ou cinza claro) ou PNG transparente. Sem cenário e sem sombra grande no chão.
3. Luz chapada e uniforme, sem sombras fortes nem brilhos. A cor da imagem vira a cor da textura.
4. Pose neutra:
   - de pé, com os membros afastados do corpo;
   - boca fechada;
   - asas abertas (se tiver asas);
   - cauda inteira visível.
5. Mesmo design em todas as vistas: cores, marcas, número de dedos, chifres. Gere o conceito primeiro e use-o como imagem de referência para gerar as vistas.
6. Vistas de frente e de lado o mais "retas" possível (pouca perspectiva).
7. PNG com o lado maior entre 1024 e 1536 px.

## Números que ajudam a evolução a funcionar em cubos
Medidos em criaturas cubificadas de mods (as tabelas completas estão em `docs/pesquisa/`).

| Estágio | Altura no jogo | Cabeça (% do volume) | Olho (% da altura) | Peças |
|---|---|---|---|---|
| 1 de 3 | ~0,8 bloco | ~46% | ~19% | ~41 |
| 2 de 3 | ~1,4 bloco | ~29% | ~12,5% | ~55 |
| 3 de 3 | ~2,6 blocos | ~14% | ~6% | ~87 |

- Cada evolução cresce de 1,75× a 2,1× em altura e a cabeça perde de 9 a 15 pontos de volume.
- O estágio final tende a ficar mais ereto e imponente e a andar mais devagar.
- Dragões finais chegam a ~3,7 blocos.
- Peixes quase não encolhem a cabeça; plantas e fantasmas mantêm a cabeça grande até o meio.

## Dicas de design para o estilo cubificado
- A silhueta precisa ser legível de longe: poucas formas grandes valem mais que muitos detalhes pequenos.
- Detalhes finos (orelhas, nadadeiras, chamas, penas, bigodes) viram planos. Anote-os na ficha.
- Paleta de 3 a 5 cores principais, mais 1 ou 2 de destaque.
- Mantenha 2 ou 3 motivos que atravessam a linhagem (uma cor, uma marca, o formato da orelha ou da cauda).

## Pronta para modelagem? (checklist)
- [ ] Todos os estágios têm `eN-conceito.png` de corpo inteiro com fundo liso.
- [ ] Pelo menos frente e lado do estágio 1 existem.
- [ ] O design é o mesmo em todas as vistas.
- [ ] O prompt de cada imagem principal está na ficha.
- [ ] O campo "O que a imagem não mostra bem" está preenchido onde houver dúvida (cauda escondida, asas fechadas, profundidade).
- [ ] As alturas e as cabeças seguem a tendência da tabela, ou a ficha explica por que não.
