---
tipo: decisao
data: 2026-10-23
status: vigente
---

# 0007 — Revisões de importação e perfil físico do Roblox

**Contexto:** o usuário priorizou infraestrutura para um projeto maior. Repetir importações gerava
cópias indistinguíveis, e a caixa de toda a criatura fazia penas/crista/cauda bloquearem espaços vazios.
O usuário deixou transporte do jogador e colisão acompanhando a animação para gameplay posterior.

**Decisão:** ampliar o registro e o preparo existentes, mantendo GLB, motor externo e fontes atuais.
Usar Asset Manager/Reimport nativos; acrescentar manifestos com hashes de fonte/exportação/configuração,
receitas geradas, atributos de identidade no Model e operações em lote com histórico reversível.
O perfil físico v1 usa o envelope do corpo sólido em um osso escolhido, até o chão; planos e outros
ossos ficam fora desse envelope. O perfil fica em coordenadas locais do Bone, escalado pelo Model no Studio.

**Alternativas:** uma caixa com a malha inteira foi rejeitada pelo teste do usuário; collision fidelity
da malha não resolve deformação por Bones. Interface própria, servidor de assets, credenciais de nuvem e
montagem de inventário como drive do Windows não são necessários para esta entrega.

**Consequências:** novos arquivos `*-importacao.json`, `*-preparar.luau` e `catalogo.json`; novos atributos
`Pipeline*` nos Models. O envelope é estático e aproximado; não inclui montaria, dano nem superfícies
animadas. O histórico local preserva uploads. A limpeza de assets online exige levantamento de uso.
Compatibilidade inicial limitada às criaturas terrestres registradas no pipeline; novos casos passam por teste.
