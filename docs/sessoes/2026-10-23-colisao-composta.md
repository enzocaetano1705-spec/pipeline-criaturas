---
tipo: sessao
data: 2026-10-23
fase: 11
ia: codex
status: colisao-composta-testada
---

# Colisão composta do F2

**Retorno posterior:** usuário aprovou o F2 (melhor que esperava) e pediu o mesmo perfil no F1.
Aplicação e teste registrados em [[2026-10-23-colisao-f1]]. O acompanhamento usa um módulo embutido,
não é colisão por Bones nativa sem script.

**Pedido ao usuário:** testar contorno, costas e cabeça do F2 no Play e salvar novamente o place.
As alterações já estão aplicadas; o GLB e os IDs de malha/textura não mudaram nesta revisão.

**Retorno:** F1 aprovado; F2 ainda atravessável nas laterais e com apoio no vazio. O perfil v1 era
aproximação insuficiente para a anatomia do F2. Ver [[0008-colisao-composta-por-osso]].

**Feito (11.7):**
- Perfil v2 por peça com rotação própria e referencial do Bone. Planos recortados pelo alfa, inclusive
  UV invertida e união das duas faces. Nenhum alongamento até o chão.
- F2: 37 caixas sólidas + 124 placas = 161 partes; teto configurável até 192, sem truncamento silencioso.
- Hitbox de referência sem colisão; módulo ColisaoOssos e chamada na prévia do cliente em PreSimulation.
- Mantidos MeshPart.CFrame e escala 3,3624475 do F2, IDs e sequências. F1 não foi preparado de novo:
  continua escala 3,5101447 e Hitbox 2,852 × 2,413 × 2,852, conforme aprovado.
- Revisão anterior do F2 preservada em ServerStorage.HistoricoCriaturasBlockbench.Pavao_F2_antes_colisao_composta.

**Verificação:**
- 12 testes Python (infra + regressões); fixtures Luau reais de preparo v1 e colisão composta passaram.
  Cobrem rotações/cantos, filhos, máscara de alfa/UV espelhada, vazios, orçamento, escala, repetição,
  acompanhamento de Bone.Transform e falha antecipada sem destruir colisores válidos.
- No Edit: 161 contatos por raycast confirmados; posição de cada caixa coincide com seu offset/Bone.
  Raios verticais ao longo do eixo central retornam superfícies em Y=3,721 / 4,074 / 4,571 / 5,167 /
  6,077 / 7,454 studs para Z=7…12. A caixa única anterior tinha topo plano em Y=6,164.
- No cliente, 45 frames: desvio máximo de posição zero; colisores moveram até 2,002 studs; uma faixa
  walk ativa, body até 4,655° sem inversão. Atualização Lua: média 0,077 ms, máximo 0,248 ms.
  Esses tempos não medem o custo total da física nem validam uma população de NPCs.
- Avatar colocado sobre o antigo vazio em X=46,5406/Z=9: caiu 1,673 stud e ficou apoiado, estado Running,
  FloorMaterial Plastic, base estimada Y=4,491. Não ficou na superfície fantasma anterior.
- Play encerrado. Nenhum driver de montaria ou transporte de jogador foi criado.
- Folha técnica 768×600: exportacoes/roblox/auditorias/2026-10-23-f2-colisao-composta.png.

**Limites:** aproximação em peças acompanha a geometria cubificada; placas têm espessura finita de
0,25 unidade Blockbench. A prévia é local; jogo multiplayer exige decidir autoridade do animador e
dos colisores. Planos com UV rotacionada param com erro, em vez de gerar um perfil errado.

**Próximo passo:** retorno do usuário sobre a sensação da colisão. O ensaio de Reimport (11.5) e
retenção/uso de uploads (11.6) continuam pendentes. Fontes manuais do usuário permanecem fora do commit.
