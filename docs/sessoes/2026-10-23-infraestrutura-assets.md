---
tipo: sessao
data: 2026-10-23
fase: 11
ia: codex
status: infraestrutura-v1-validada
---

# Biblioteca, revisões e colisão do corpo

**Pedido ao usuário:** salvar novamente o place para guardar os novos perfis físicos. Conferir a sensação
do bloqueio do F2 no jogo. Carregar o jogador junto com o salto ficou para gameplay, conforme o pedido.
O próximo teste de infraestrutura é Reimport de uma revisão, que depende da operação manual do Studio.

**Correção do diagnóstico anterior:** conter a malha inteira não torna a colisão adequada. O usuário mostrou
o avatar apoiado na caixa vazia da crista/penas. O preparo anterior foi testado por contenção/estabilidade,
mas faltava um perfil físico do corpo. Essa distinção passa a fazer parte do pipeline.

**Feito:**
- Documentação em `exportacoes/roblox/BIBLIOTECA-E-ITERACAO.md`; decisão [[0007-revisoes-e-perfil-fisico-roblox]].
- Manifestos/rastreio por SHA256 de fonte, GLB e configuração; catálogo e receitas geradas pela ferramenta.
  `scripts/preparar-roblox.py` recusa perfis/revisões incompatíveis e pode preservar a escala atual.
- Gerenciador de seleção em lote: auditoria, adoção com histórico, arquivamento local e restauração;
  preflight, proteção de outros Models e participação no Undo. Sem remoções permanentes/online.
- Consulta somente leitura da conta Aerodatiro: 16 Models e 20 Images retornados pelo conector. Relatório
  em `exportacoes/roblox/auditorias/2026-10-23-inventario.json`. É amostra, não análise completa de dependências.
  Neste place não publicado havia só F1/F2 na pasta ativa, Baseplate/Spawn e duas revisões em ServerStorage.

**Colisão aplicada no Studio:**
- Mantidas as escalas editadas pelo usuário: F1 3,5101447; F2 3,3624475. Mantidas as CFrames das MeshParts.
- F1: caixa antiga 5,456 × 3,736 × 3,785; nova 2,852 × 2,413 × 2,852 studs. Usa body_upper/body_lower.
- F2: caixa antiga 6,645 × 9,277 × 12,249; nova 1,681 × 6,164 × 5,022 studs.
  Usa hips, torso, shoulders e TorsoHips, com rotações das peças consideradas.
- Raycast respeitando CanCollide acerta o topo do corpo do F2 em Y=6,164; não acerta mais o vazio lateral
  a 2 studs do eixo do corpo, que antes estava dentro da caixa. É envelope estático para locomoção.
- Walks no cliente após o novo preparo: uma faixa por modelo, X/Z do body=0, hitbox imóvel,
  F2 giro observado até 4,651°, F1 sem giro. Imagens/rig preservados; GLBs permaneceram iguais no Git.
- Play encerrado, Hitboxes selecionadas no Edit. Diagnóstico visual temporário removido.
  Capturas desta rodada vieram brancas: não foram usadas para declarar aprovação visual da nova colisão.

**Verificação:**
- 15 testes de exportação/regressão/infra passaram.
- Fixture `preparo-roblox.spec.luau` executada com o código real e perfil, validando poses, mapa/filtro,
  caixa girada, repetição estável e preservação das sequências.
- Fixture `gerenciar-roblox.spec.luau`: adoção/histórico, arquivo/restauro em lote, rejeição de duplicata,
  preflight sem movimento parcial e isolamento de outro projeto. Nenhum Model real foi arquivado por esses testes.
- Fontes manuais do F2 e alterações em `docs/AURA*` continuam fora do commit da IA.

**Próximo passo:** usuário testar o bloqueio do corpo e, depois, ensaiar Reimport de uma revisão com nomes
estáveis. Para outro modelo, registrar fonte/estágio e a parte física antes de gerar o preparo.
