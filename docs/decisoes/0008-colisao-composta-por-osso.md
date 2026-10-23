---
tipo: decisao
data: 2026-10-23
status: vigente
---

# 0008 — Colisão composta por peça e osso

**Contexto:** o usuário aprovou a colisão simples do F1 e rejeitou a caixa única do F2 por atravessamento
das partes laterais e apoio em espaços vazios. Seu pedido autoriza ampliar o perfil v1 da decisão 0007.

**Decisão:** preservar a escolha por criatura e acrescentar perfil v2 `composta_ossos`. Usar caixas
orientadas para cada sólido, placas finas recortadas pelo alfa para planos e offsets locais a cada Bone.
Manter a Hitbox como referência de frente sem colisão nesse perfil. Gerar o módulo de acompanhamento
da pose junto com o preparo; a prévia local o executa no mesmo cliente que avalia a animação.

**Alternativas descartadas:**
- Unir o corpo num envelope: perde os vazios e a inclinação das peças; rejeitado nos prints do usuário.
- Colisão somente na MeshPart: não acompanha a deformação por Bones.
- Uma caixa por plano inteiro: os cantos transparentes viram superfícies invisíveis.
- Repartir a malha visual/importar novos assets: desnecessário para os volumes físicos gerados.

**Consequências:** preserva os GLBs, textura e animações. F1 continua no perfil aprovado. F2 usa 161
partes físicas (37 sólidas, 124 recortes), com teto explícito de 192. Há custo de atualização/física;
medir muitos NPCs antes de tratar esse detalhe como padrão universal. Planos com rotação de UV ainda
são recusados. Integração multiplayer deve escolher a autoridade de animação/colisão, pois Bone.Transform
não replica. Montaria, transporte de passageiros e dano continuam fora desta etapa.
Para desfazer no Studio, usar Undo ou a revisão anterior salva no histórico; no pipeline, trocar o perfil
no registro e gerar novamente o manifesto/preparo correspondente.
