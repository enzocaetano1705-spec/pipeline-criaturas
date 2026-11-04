---
tipo: decisao
data: 2026-11-04
status: vigente
---

# 0009 — Backend Blender opcional e isolado

**Contexto:** pedido explícito do usuário em 04/11 autoriza uma alternativa de autoria
com a mesma disciplina de entradas, scripts, revisões e exportação do Blockbench.
Os testes antigos por prompts MCP não permitem concluir qual ferramenta produz arte melhor.

**Decisão:** acrescentar `criaturas blender`, separado das etapas existentes e de
`criaturas tudo`. Fonte de autoria: JSON estruturado + scripts Python persistidos;
`.blend` reconstruível em pasta nova. Blender instalado é executado como programa
separado, em background, factory startup, sem MCP vivo, mouse, teclado ou foco.
Não há dependência Python adicional nem instalação de addon.

Compartilhados: briefing/leitura orientados pela imagem, estágio/categoria, protocolo
de aprovação, `plano_cubos.schema.json`, nomes/unidades/eixos, gerador de locators
de `rig.py`, eventos e validador Khronos já fixado. Próprios do Blender: extensão
de entrada sintética, atlas por face, malha, armature, bake IK, render, ida/volta
GLB e manifesto. A validação `bbmodel_validate` não valida uma cena Blender.

O protótipo v1 habilita fixtures sintéticas e um helper bípede explícito. Entradas
reais são recusadas enquanto não existirem referências, classificação e folha
aprovadas e o adaptador de produção for conferido. Não gerar uma criatura real
pela simples troca do nome/tipo da fixture.

Escala interna de autoria: unidades do pipeline; no Blender `(X,-Z,Y)/16`, no GLB
Y-up e frente -Z. Uma malha, um material PBR, uma influência rígida por vértice.
Wrapper de exportação `Raiz` estático acima de `root -> body`; correção de base
Blender/glTF não é uma rotação artística animada. Locators também são entregues
em JSON, pois o importador Studio pode descartar empties.

Planos de dimensão zero recebem espessura **só no backend Blender** (0,08 unidade
na fixture), resultando em lâmina fechada. UV por face com densidade/margens
declaradas, alfa recortado e duas variantes por máscaras sem mudar detalhes.
Não se usa subdivisão, bevel automático, voxelização ou material procedural.

**Alternativas descartadas:**

- Substituir o motor, a fonte `.bbmodel` ou o exportador atual: risco e escopo
  desnecessários. O padrão funcional continua Blockbench.
- Construir cubos/keyframes em chamadas MCP individuais: não é reconstruível
  nem permite medir custo de autoria de forma justa.
- Chamar importação do pavão de autoria independente: não testa criação.
- Prometer importação Roblox com base só no render: arquivo, reimportação,
  aprovação artística e ensaio no motor são evidências diferentes.

**Consequências:** contrato Minecraft e GPL do motor externo permanecem intactos.
Novas saídas nunca sobrescrevem pastas existentes, inclusive `.blend` editado.
A primeira criatura comparativa permanece pendente das referências do usuário.
Protocolo e limitações em [sistema Blender](../sistema-blender.md) e
[comparação](../comparacao-blender-blockbench.md). Desfazer é remover o subcomando
adicional e seu pacote; as etapas antigas não dependem dele.
