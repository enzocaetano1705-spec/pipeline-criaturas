---
tipo: sessao
data: 2026-10-23
fase: 10
ia: codex
status: aguardando-reimportacao-f1
---

# Validação no cliente do Studio e material do F1

**Pedido ao usuário:** importar apenas o `exportacoes/roblox/pavao/Pavao_F1.glb` atualizado, com Rig Type Custom.
Pode deixar o modelo novo no Workspace; a IA localizará a importação e a colocará na pasta combinada,
preservando o F1 anterior em um subdiretório de histórico. A importação é ação manual combinada com o usuário.
O novo arquivo contém material PBR explícito; a correção visual do F1 ainda não está comprovada.

**Feito:**
- As importações novas estavam no Workspace, entre modelos antigos. Organizadas em
  `Workspace["criaturas modeladas blockbench"]`, com F1 em (24; 1,596; 10), F2 em (35; 4,139; 10), escala 3.
  Os modelos antigos fora da pasta foram preservados. Studio: `Template_95206881_AutoRecovery_0.rbxl`,
  id MCP `b5676c57-2fd5-44e2-92b1-376fb1fc236d`.
- Novos assets: F2 MeshId `120641951142067`, textura `123315715785564`.
  F1 MeshId `97293060483622`, textura `136950763430471` (deduplicados com a importação anterior).
- Correção adicional no preparo: o giro de importação afetava também o pivô do corpo do F2.
  Só desfazer a rotação deixava 3,27 studs de deslocamento. A compensação usa a posição de repouso
  de `InitialPoses.body_Original`, lida sem alteração, e só se aplica ao Bone diretamente sob a MeshPart.
- F1: o importador omitiu a Pose do `root` intermediário. O body estava ligado diretamente à Pose Raiz e não
  animava o Bone real. O preparo agora insere os ancestrais neutros conforme a hierarquia real dos Bones.
- Testes no cliente: walks tocando nas duas criaturas; F2 rotação máxima observada 4,658°,
  deslocamentos X/Z = 0, Y até 0,0834 stud, frente alinhada (dot mínimo 0,99595), hitbox sem movimento.
  F1 salto até 0,4633 stud, sem giro nem deslocamento lateral; hitbox estável.
  Todas as chaves corrigidas: 30 quadros F2 (giro até 4,689°) e 33 F1; X/Z nulos dentro da precisão numérica.
- O Play foi encerrado. Fixtures e alterações temporárias do cliente não persistem no Edit.

**Material branco:**
- F1 com SurfaceAppearance branco; sem SurfaceAppearance a textura apareceu colorida na captura do cliente.
  O asset contém pixels corretos; UVs da malha baixada foram inspecionadas e estão na faixa esperada.
- Trocar URL/reatribuir ColorMap, alternar o filtro e adicionar mapa de roughness nativo não resolveram.
  O mapa de roughness temporário foi removido. Não atribuir o resultado à moderação sem evidência.
- Testes posteriores de material gerado de EditableImage e troca temporária para o asset do F2 não puderam ser
  julgados: o MCP voltou a produzir capturas inteiramente brancas, inclusive com HUD. Não são prova do material.
  Os testes foram encerrados junto com o Play. Não foi acrescentado carregamento dinâmico ao jogo.
- Exportador suporta `material_pbr: true` (habilitado só no F1): acrescenta um PNG 4×4 constante de
  metallic/roughness ao GLB, para o importador montar SurfaceAppearance completo. Albedo 1024, UVs, skin,
  malha e animações são idênticos aos do GLB anterior, inclusive bytes originais do BIN.
  Hipótese a testar com a importação: evitar a conversão posterior de TextureID para ColorMap.
- F2 apareceu texturizado nas capturas do cliente. A inspeção visual final perto/longe de ambas permanece
  pendente; não prometer eliminação de mipmaps, do efeito de iluminação ou equivalência de escala por Bone.
  O Roblox não reproduz os canais de escala existentes no F1; salto e oscilação de walk foram medidos.

**Verificação:**
- `uv run pytest -q ferramenta/testes/test_exportar.py ferramenta/testes/test_roblox_regressoes.py`: 10 passaram.
- GLB F1 com material PBR: 96 triângulos, 18 nós, duas animações, zero erros/avisos Khronos.
- `ferramenta/testes/preparo-roblox.spec.luau`: executado no Studio substituindo o marcador `-- @PREPARO@`
  pelo código real do preparo. Fixtures fora do DataModel validam offset do F2, ancestral do F1, rotação,
  mapas/filtro, contenção da malha na caixa girada, repetição estável e preservação das sequências originais.
- Capturas reduzidas em `modelos/.roblox-trabalho/auditoria-20261022/`, sobretudo `f1-sem-sa-768.png`
  (F1 colorido), `f1-default-768.png` (branco com SA) e `studio-cliente-768.png` (F2 colorido).
- Fonte F2 permanece com SHA256 `57c04dc4274a88c1408fdc2d38c58c5aa8f0ea0bb0c972dc5841a0a2f4a4e736`.
  Alterações manuais da fonte/PNG e `docs/AURA*` ficam fora dos commits da IA.

**Próximo passo:** localizar o novo F1, preservar o anterior, aplicar o preparo vigente e testar no cliente.
Conferir os mapas PBR criados pelo importador e obter evidência visual perto/longe. A fase 10.3 continua aberta.
