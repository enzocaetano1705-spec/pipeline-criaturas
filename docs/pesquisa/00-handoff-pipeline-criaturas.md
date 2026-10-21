---
tags: [handoff, pipeline-criaturas, roblox, minecraft, blockbench]
data: 2026-10-21
status: pesquisa concluída — construção em andamento (ver plano-construcao)
origem: conversa no app Claude (projeto "Roblox")
---

# Handoff: pipeline de criaturas 3D (imagem livre → modelo cubificado → Roblox/Minecraft)

Resumo de uma conversa de pesquisa para qualquer IA ou ferramenta continuar o trabalho. Detalhes e números completos nas notas de `pesquisa/`:
- [[pipeline-assets-3d]] — geradores imagem→3D, custos, licenças, limites do Roblox, Blockbench → Roblox, animação e combate no Roblox.
- [[estilo-blocky-referencias]] — técnicas de estilo medidas no Cobblemon e no Digimod, regras por estágio de evolução, escolha do MCP do Blockbench.
- [[categorias-criaturas]] — taxonomia de criaturas, regras de modelagem por categoria e protocolo de classificação de imagens.

## Objetivo
- Transformar conceitos de criaturas (imagens geradas livremente, em qualquer estilo, + o prompt usado) em modelos 3D cubificados no estilo Cobblemon/Digimod, com rig, textura e animações.
- Destino principal: jogos no Roblox com arte estilo Minecraft. Secundário: mods de Minecraft.
- Restrições: dev indie no plano Pro do Claude; evitar assinaturas caras (Meshy/Tripo); gastar poucos tokens; trabalha com vários harnesses e modelos (Claude Code, Codex, Antigravity…), então tudo precisa ser portátil.
- O usuário gosta muito de evoluções: todo jogo deve suportar linhagens de evolução.

## Decisões tomadas
1. **Código em vez de MCP passo a passo.** O MCP que põe cubo a cubo gasta muitos tokens (ex.: captura de 1920×1080 ≈ 2.700 tokens). A IA escreve/roda scripts e lê relatórios curtos; imagem só para conferência final (folha de 4 vistas ≈ 800 tokens).
2. **A IA não inventa a forma.** O carisma vem do conceito em imagem do usuário. O LLM faz leitura semântica (partes, proporções, paleta) e o código faz a parte espacial. (Teste inicial "Forja": textura calculada agradou, forma inventada por template ficou sem carisma.)
3. **Blockbench é o centro.** `.bbmodel` (JSON) é a fonte do modelo; grupos = ossos; locators = pontos de ancoragem.
4. **MCP escolhido:** https://github.com/jasonjgardner/blockbench-mcp-plugin (GPL-3.0). Servidor *headless* (edita `.bbmodel` sem o app, edição em lote, validação, render, export Bedrock/Java) como motor; servidor *desktop* para ver ao vivo, polir e exportar glTF com armadura. Regra: sempre lote/script, nunca cubo a cubo.
   - Claude Code: já configurado no `.mcp.json` do repositório `pipeline-criaturas`, com o motor rodando de um clone local fixado no commit `141ef78` (o `npx github:…#commit` falhou no teste; ver [[0001-decisoes-iniciais]]). Servidor desktop: `http://localhost:3000/bb-mcp`.
   - Plugin no Blockbench: File › Plugins › Load Plugin from URL › `https://jasonjgardner.github.io/blockbench-mcp-plugin/mcp.js`.
5. **Blockbench → Roblox:** export glTF com "grupos como armadura" + animações → importador 3D do Roblox (rig Custom: MeshPart + Bones). Animações pelo Import do Animation Editor ou em lote com anim2rbx (MIT). Cubo = 12 triângulos (limite 20 mil por malha).
6. **Pegadinha da textura pixelada:** o Roblox borra textura de malha (filtro bilinear). `SurfaceAppearance.ResampleMode` (modo pixelado) aparece na API desde a v716, mas ainda não funcionava em ago/2026. Contorno: ampliar a textura por vizinho mais próximo (ex.: 64→512) com margem.
7. **Separar design de tradução:** o gerador de imagens cria livremente (não forçar estilo cubo); o pipeline traduz para cubos.
8. **Estágio e categoria são entradas obrigatórias** do tradutor. Médias gerais não servem (bebê Digimon = 100% cabeça; Charizard = 4% de cabeça no volume).
9. **Classificação de imagem:** primeiro só a imagem (prompt escondido), depois o prompt preenche só itens incertos/ocultos; imagem sempre vence conflitos; até 3 sugestões de categoria com motivo e estágio provável; o usuário escolhe ou cria categoria nova.
10. **Uso dos mods como referência:** Cobblemon (modelos CC BY-NC 3.0, IP Pokémon) e Digimod (IP Digimon) só para estudo. Extrair números e regras; nunca copiar geometria, textura ou animação. Criaturas próprias.

## Pipeline planejado (ainda não construído)
1. Conceito livre no gerador de imagens (todos os estágios da linhagem juntos, para manter coerência) + folha frente/lado/costas.
2. Classificação (categoria + estágio) com confirmação do usuário.
3. Leitura semântica pelo Claude: tipo de corpo, partes, proporções, paleta, rosto, o que é volume e o que é plano.
4. Cubificador determinístico com as faixas da categoria e do estágio + medidas da silhueta da imagem. Opcional para formas difíceis: malha intermediária (Hunyuan 3.1 grátis 20/dia, TRELLIS.2) + segmentação de partes.
5. Textura projetada da imagem, quantizada em paleta, sombreado pintado; rosto como "adesivo" de planos (olhos, pupilas, pálpebras, bocas) para piscar e expressões.
6. Ossos e locators com nomes padrão + biblioteca de animação procedural por tipo de corpo (seno com defasagem entre ossos, marchas prontas, piscar aleatório, cabeça seguindo alvo).
7. Validação automática + validação da linhagem (assinatura de evolução) + 1 folha de 4 vistas.
8. Polimento manual no Blockbench → glTF com armadura (Roblox) ou Bedrock/GeckoLib (Minecraft).

## Números-chave
**Técnicas de estilo (Cobblemon, 1.170 modelos):** 45% das peças são planos de espessura zero com recorte (asas, nadadeiras, espinhos, chamas, penas, orelhas); rosto em planos (80% com pálpebras); Box UV, 1 pixel por unidade, texturas 64–128 px; 96% com ossos já rotacionados na pose de repouso; ~18 locators por modelo; 53% dos canais de animação são fórmulas (seno/cosseno do tempo); mediana de 9 animações por criatura (blink, ground_idle, cry, ground_walk, sleep, battle_idle, run, recoil, faint, happy/sad/angry, ataques, voo, nado).
**Digimod (270):** modelos mais simples (25 cubos), olhos pintados, 60% dos cubos rotacionados, uma biblioteca de animação compartilhada por muitas criaturas via nomes de ossos padronizados.

**Por estágio (Cobblemon, linhagens de 3):** cabeça 46% → 29% → 14% do volume; altura 0,8 → 1,4 → 2,6 blocos; cubos 41 → 55 → 87; olho 19% → 12,5% → 6% da altura; bípedes 50% → 60% → 72%; andar 1,33 → 1,5 → 2,0 s.
**Digimod:** Baby I/II são só cabeça (3–6 cubos); Rookie 41% → Champion 21% → Ultimate 15% de cabeça.
**Assinatura de cada evolução (469 pares):** altura ×1,75–2,1 (92–97% dos casos); cabeça −9 a −15 pontos de volume (78–87%); cubos ×1,3–1,6; tende a ficar de pé; andar mais lento. Usar para validar linhagens (evolução invertida = erro).

**Categorias (exemplos):** canídeo × felino = focinho 0,52 vs 0,27 do crânio, cabeça 30% vs 50%, cauda cheia (4 segmentos) vs fina (6). Dragão: pescoço de 3 segmentos, cauda grossa 0,8× a altura, finais de 3,7 blocos. Dinossauroide: focinho mais longo, andar mais lento (3,5 s). Ave: envergadura 2,5× a altura. Peixe: cabeça quase não encolhe na evolução. Tabelas completas em [[categorias-criaturas]].
**Precisão esperada da classificação:** mesmo com o esqueleto, a morfologia visível só bate com a categoria oficial em 65% dos casos → por isso as 3 sugestões.

## Roblox: animação e combate (referência para depois)
- Animar: Animation Editor (rigs Motor6D e Bones, marcadores), Blockbench, Blender (FBX), Moon Animator 2, Animation Capture (vídeo → R15, beta).
- Adaptive Animation (abr/2026): uma animação em R15, R6 e rigs custom. Animation Graphs (jul/2026): mistura, camadas e máscaras.
- Combate: cliente toca a animação, servidor valida; marcadores HitFrame/CancelOpen/RecoveryStart; hitbox por cast entre frames a partir de Attachments na arma (ex.: ShapecastHitbox); Trail entre os mesmos Attachments → VFX e hitbox alinhados por construção.
- Código em arquivos: Studio Script Sync (lançado em 17/jun/2026) grava scripts como `.luau` numa pasta → versionável com Git; Rojo se quiser o projeto inteiro em arquivos.

## Pendências
- GPU/VRAM do usuário (decide se a rota de malha intermediária roda local ou na nuvem; a rota Blockbench pura não precisa de GPU).
- Padrão de prompt para gerar criaturas (o usuário vai desenvolver).
- Primeiro teste ponta a ponta com UMA criatura: conceito → classificação → cubos → textura → 2 animações → Roblox (textura ampliada, locators como Attachments).
- ~~Montar repositório + cofre de notas + AGENTS.md~~ → kit montado em 21/out/2026; o andamento está em [[plano-construcao]].

## Fontes principais
- https://gitlab.com/cable-mc/cobblemon
- https://github.com/ginerJ/The-Digimod
- https://github.com/PokeAPI/pokeapi
- https://github.com/jasonjgardner/blockbench-mcp-plugin
- https://create.roblox.com/docs/en-us/studio/importer.md
- https://create.roblox.com/docs/scripting/sync
- https://www.benchmark.ai/image-to-3d
