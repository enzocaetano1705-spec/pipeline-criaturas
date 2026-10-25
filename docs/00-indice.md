---
tags: [indice]
---

# Pipeline de criaturas 3D — índice

Conceito livre (imagens + prompt) → modelo cubificado no estilo Cobblemon/Digimod com textura, ossos, locators e animações → Roblox e Minecraft.

## Trabalho
- [[plano-construcao]]: fases, status e critérios de aceite. Comece por aqui.
- [[convencoes]]: unidades, eixos, nomes de ossos, locators, animações e pastas.
- `decisoes/`: o que foi decidido e por quê ([[0001-decisoes-iniciais]]).
- `sessoes/`: diário curto de cada sessão de IA.
- Skill de modelagem: `skills/criaturas-3d/SKILL.md` (fora do cofre, na raiz do repositório), com os protocolos `classificar.md` e `ler.md`.
- [[0002-exportacao-roblox]]: como o .glb do Roblox é exportado e verificado.

## Criaturas
- [[2026-10-25-reconstrucao-pavao-f3-v2|F3 v2: reconstrução e comparação]]: novas referências, volumes e revisão artística pendente.
- [[2026-10-25-modelagem-pavao-f3|F3: primeira proposta editável]]: modelo, quatro vistas e revisão artística pendente.
- [[2026-10-24-fechamento-f2|F2 finalizada por ora]]: fonte aprovada, animações e próximos passos de integração.
- [[criaturas/LEIA-ME|Como preparar uma criatura]]: requisitos das imagens, números de evolução e checklist.
- `criaturas/_modelo/ficha.md`: modelo da ficha.
- `criaturas/<nome>/`: uma pasta por linhagem.

## Pesquisa (consulta)
- [[00-handoff-pipeline-criaturas]]: resumo da pesquisa e das decisões.
- [[pipeline-assets-3d]]: geradores imagem→3D, custos, licenças, Roblox (importação, animação, combate).
- [[estilo-blocky-referencias]]: técnicas de estilo medidas, regras por estágio, escolha do MCP.
- [[categorias-criaturas]]: taxonomia, regras por categoria e protocolo de classificação.
- [[animacoes-e-mecanismos-reutilizaveis]]: clipes, posers, quirks, movimentos procedurais e o que precisa ser convertido para Roblox.
- [[0005-estudar-referencias-por-estrutura]]: consulta por anatomia e comparação de ilustração, modelo, atlas e código antes de modelar.
- Biblioteca local externa: `~/Downloads/referencias-criaturas/INDICE.md`. O estudo visual de Koromon fica em `estudos/koromon/` dessa biblioteca.

## Fora do cofre (no repositório)
- `referencia/medidas.json`: faixas numéricas por estágio, plano, nicho e assinatura de evolução, lidas pelo código.
- `referencia/exemplo-headless/`: exemplo verificado do motor headless.
- `referencia/prototipo-forja/`: protótipo antigo; partes reaproveitáveis.
