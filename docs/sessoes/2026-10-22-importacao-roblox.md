---
tipo: sessao
data: 2026-10-22
fase: 10
ia: codex
status: aguardando-importacao
---

# Correções da exportação e do preparo no Roblox

**Pedido ao usuário:** importar `exportacoes/roblox/pavao/Pavao_F1.glb` e `Pavao_F2.glb` com Rig Type Custom
e colocar ambos em `Workspace["criaturas modeladas blockbench"]`. Avisar quando terminar; então rodar o
preparo atualizado por MCP em cada modelo e testar no cliente do Play (textura perto/longe, walk, frente e hitbox).
O usuário pediu explicitamente essa etapa manual. A fase 10.3 continua pendente.

**Feito:**
- Usuário confirmou que salvou as alterações do F2. Backup por hash em
  `modelos/criatura-pavao/f2/historico/20261022-57c04dc4274a-usuario.bbmodel` e `.png`.
  SHA256 da fonte: `57c04dc4274a88c1408fdc2d38c58c5aa8f0ea0bb0c972dc5841a0a2f4a4e736`.
- Comparação por UUID com Git: retirou um `beak`, adicionou `claw_left_`, ajustou o outro bico, dedos,
  cristas, uma pena da asa e grupo `feather_left_2`, além de dados de idle/walk. Pintura embutida igual ao PNG salvo.
  As alterações manuais são a referência; não reconstruir a criatura a partir do gerador antigo.
- Exportador: hash inclui a textura; cópias antigas são preservadas; atlas em cache vem da cópia com as UVs
  remapeadas; borda repetida nas ilhas superamostradas da cabeça.
- Preparo: preserva ColorMapContent existente, recusa entrada sem textura, exige Pixelated, remove tintura cinza,
  limita a busca à pasta combinada; hitbox medida no eixo da frente; corrige cópias das animações e guarda originais.
- GLBs regenerados: F1 96 triângulos, F2 760; ambos com duas animações, uma textura de 1024 e zero erros/avisos Khronos.
  O F1 é idêntico ao GLB anterior: os ajustes dele estão no preparo do Studio.

**Verificações:**
- `uv run pytest -q ferramenta/testes/test_exportar.py ferramenta/testes/test_roblox_regressoes.py`: 9 passaram.
- Teste isolado no Studio, objetos temporários fora do Workspace e destruídos ao final: mapa existente com TextureID
  vazio preservado, Pixelated, hitbox contendo malha girada 37°, frente correta, compensação 180° → 4,7°,
  sequências originais preservadas e duas execuções sem deslocamento ou crescimento da hitbox.
- F2: 66 cubos com mesmos volumes, pivôs e rotações, grupos preservados, todos os keyframes originais iguais;
  só foi acrescentada Raiz neutra. Comparação de 42 canais glTF com exportação direta da fonte: nenhuma diferença.
- Reexportação repetida manteve hash do PNG; fonte original manteve SHA256.
- Folha de comparação de 768 px e relatório em `modelos/.roblox-trabalho/auditoria-20261022/` (temporários).
  O render headless mostrou diferença nos antebraços entre fonte e cópia ao normalizar animadores vazios;
  pivôs amostrados e todos os canais glTF são iguais. Conferir a aparência no cliente real após importação.

**Diagnóstico e limites:**
- Consulta somente de leitura aos modelos existentes em `Template_95206881_AutoRecovery_0.rbxl`:
  F1 asset `136950763430471`, F2 `73223217303259`: ambos retornaram AssetFetchStatus.Success e imagens coloridas
  de 1024 px via EditableImage. F2 estava sem SurfaceAppearance; F1 já tinha ColorMap e Pixelated.
  Isso não sustenta a afirmação anterior de que tudo era moderação. A causa visual exata do branco ainda precisa
  ser conferida no cliente; os ajustes encontrados no código não provam, sozinhos, a causa desse sintoma.
- Filtro Pixelated é suportado oficialmente; mipmaps, qualidade gráfica e iluminação ainda precisam de inspeção
  perto/longe. Não prometer eliminação de todo mipmap nem equivalência visual de 100% sem o teste importado.
- Não foram alterados os modelos existentes no Studio. F1/F2 novos precisam do preparo atualizado após importar.
- Originais editados pelo usuário e mudanças em `docs/AURA*` continuam fora do commit desta correção.

**Decisões:** nenhuma mudança de arquitetura. Continua uma malha/atlas e rig Bedrock com Raiz neutra.

**Próximo passo:** após o aviso de importação, listar Studios, localizar a pasta combinada, preparar F1 e F2,
testar no cliente e registrar evidências de textura, movimento dos Bones e frente/colisão. Guardar os resultados aqui.
