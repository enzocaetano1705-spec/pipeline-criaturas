---
tipo: sessao
data: 2026-10-27
fase: 10
ia: codex
status: golpes-aprovados-consolidados
---

# F3 — Low, Left e Combo aprovados; Right retirado

**Feito:** usuário aprovou o combo e decidiu manter Low, Left e Combo.
Low e Left passam a atender alvos de qualquer altura na direção de
combate; a antiga divisão baixo/médio/grande não restringe esses clipes.
`attack_right` foi retirado do modelo atual e das listas ativas de golpes,
aprovações e sequência sugerida. Decisão artística do usuário, sem nova
arquitetura ou lógica de jogo.

Saída: `f3/ataques-v7/criatura-pavao-e3-ataques-v7.bbmodel`.
22 animações: os três golpes e as 19 anteriores. Verificação integral
confirma que todas as chaves/UUIDs, eventos e dados dos clipes mantidos
são idênticos à v6. Geometria, rig, locators, UVs e atlas também intactos.
As únicas diferenças no modelo são o nome do projeto e a remoção do clipe.

Fonte SHA-256:
`9b36df874a85b29edb79dde878bd07be8920c06515973e631ce478287ffb2500`.
Saída SHA-256:
`aa1d03d8bd586bb1efc8e9de121aca1e804b57ea64f03b95be960347c5bf45d1`.

**Conferência:** `validacao-catalogo.json` registra ausência do Right,
igualdade completa dos 22 clipes e preservação dos eventos de Low/Left/Combo.
As medições e capturas da v6 continuam documentadas como origem: não houve
mudança no movimento que exija nova amostragem ou novas prévias. A v7 foi
aberta no Blockbench para seguir o trabalho com o catálogo atualizado.
Fonte v6 preservada; nenhuma revisão manual sobrescrita.

**Documentação/Git:** catálogo, aprovações, estado atual, ficha, plano e
retomada atualizados. Base: `8b52830`. Sem Studio ou lógica de pet.
O ataque de área antigo continua adiado. A aprovação do conjunto de golpes
não declara concluída a fase 10 inteira; sem tag de conclusão de fase.

**Próximo passo:** próxima etapa de produção a definir. A exportação e a
integração da F3 no jogo permanecem futuras; usar esta versão como fonte atual.
