---
tipo: decisao
data: 2026-10-21
status: vigente
---

# 0004 — Poucas formas grandes e detalhes na textura

**Contexto:** ao revisar criatura-pavao, o usuário preferiu a primeira versão simples à versão com 38 peças que tentava reproduzir a curvatura da ilustração. Indicou Koromon e a linhagem Goomy como referências visuais de simplificação.

**Decisão:** priorizar pouquíssimos cubos e planos grandes, identidade e proporções gerais. Um corpo simples começa com 1–2 volumes; olhos, dentes, pelo, marcas e relevo aparente ficam principalmente na textura. Referências de orçamento são limites e avisos, não metas de contagem. Não voxelizar uma superfície curva apenas por fidelidade literal. A imagem continua determinando quais partes existem.

**Aplicação nesta criatura:** 8 peças (2 volumes de corpo e 3 segmentos em cada pena), atlas 64×64 e rosto pintado. Os modelos externos foram observados apenas como referência de linguagem visual; nenhuma geometria, textura, animação ou código foi copiado.

**Consequências:** a direção fica registrada em `docs/convencoes.md`. A revisão usa `aplicar` em lote e preserva a versão de 38 peças no histórico. Olhos inteiramente pintados não recebem o blink procedural baseado em geometria sem trabalho adicional; não apresentar esse movimento como concluído.
