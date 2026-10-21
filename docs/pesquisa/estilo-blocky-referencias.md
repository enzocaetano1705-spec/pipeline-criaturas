---
tags: [pesquisa, pipeline-criaturas, estilo, evolução, blockbench]
data: 2026-10-21
---

# Estilo blocky de criaturas: análise de Cobblemon e The Digimod + escolha do MCP (21/out/2026)

Objetivo: entender como modeladores traduzem criaturas de desenho/anime para cubos, para o pipeline "imagem livre → modelo cubificado" (Roblox e mods de Minecraft). Uso só para estudo: extraímos números e regras, nada de geometria, textura ou animação copiada.

IMPORTANTE (revisão do mesmo dia): proporções NÃO podem ser tratadas como média geral. Elas dependem do estágio de evolução e do tipo de corpo. Use as tabelas por estágio abaixo (e [[categorias-criaturas]] para tipo de corpo); as medianas gerais da primeira análise ficam só como contexto de estilo (técnicas), não como alvo de proporção.

## Fontes e licenças
- Cobblemon: https://gitlab.com/cable-mc/cobblemon (código MPL 2.0). 530 das 906 pastas de modelo trazem licença Creative Commons Atribuição-NãoComercial 3.0 (texto idêntico em todas). Personagens são IP da Pokémon. Uso comercial (jogo Roblox monetizado) não permitido.
- The Digimod: https://github.com/ginerJ/The-Digimod (GeckoLib, Forge/NeoForge 1.20.1). ModDex lista MIT, mas o LICENSE.txt do repo é o texto padrão do Forge MDK; licença dos assets incerta. Personagens são IP de Digimon.

## Proporções por estágio de evolução
Método: estágio vindo dos dados de espécie (Cobblemon: árvore de evolução + rótulos baby/legendary/mythical; Digimod: campo evo_stage 0–4). Pose de repouso aplicada. "Cabeça % volume" = volume dos cubos sólidos sob o osso head ÷ volume total (métrica mais confiável). "Crânio % altura" = maior cubo da cabeça ÷ altura sólida. Medianas (p25–p75 entre parênteses quando úteis). 905 modelos Cobblemon, 270 Digimod.

### Cobblemon (linhagens de 3 estágios)
| | Básico | Meio | Final | Lendário/mítico |
|---|---|---|---|---|
| n | 102 | 105 | 106 | 23 |
| Cabeça % volume | 46% (32–66) | 29% (17–46) | 14% (7–36) | 10% |
| Crânio % altura | 44% | 29% | 19% | 21% |
| Olho % altura total | 19% | 12,5% | 6% | 6% |
| Perna % altura | 32% | 34% | 40% | 34% |
| Altura no jogo (blocos) | 0,8 | 1,4 | 2,6 | 3,2 |
| Cubos | 41 | 55 | 87 | 107 |
| Bípedes | 50% | 60% | 72% | 74% |
| Ciclo de andar | 1,33 s | 1,5 s | 2,0 s | — (n=2) |
- Linhagens de 2: cabeça 38% → 22% do volume; altura 0,9 → 1,8 bloco; cubos 43 → 68; andar 1,33 → 1,5 s.
- Bebês (19): cabeça 68% do volume; 0,86 bloco; andar 1,0 s.
- Únicos (sem evolução, não lendários, 94): cabeça 27%; 1,5 bloco; 58 cubos.
- Tipo de corpo muda o número: cabeça % altura em bípedes 48% → 36% → 30%; quadrúpedes 60% → 39% → 25%; sem pernas (serpentes, peixes, blobs) 60% → 39% → 37%.
- Idle tem 4 s em todos os estágios; nº de animações por criatura não depende do estágio (8–11).
- % de planos (~43–48%) é constante: estilo, não estágio.

### The Digimod (Baby I → Ultimate)
| | Baby I | Baby II | Rookie | Champion | Ultimate |
|---|---|---|---|---|---|
| n | 20 | 22 | 33 | 111 | 84 |
| Cabeça % volume | 100% (só cabeça) | 100% (p25 56%) | 41% | 21% | 15% |
| Crânio % altura | 100% | 100% | 30% | 23% | 20% |
| Altura (unidades) | 9 | 19 | 27 | 38 | 48 |
| Cubos | 4 | 10 | 22 | 31 | 37 |
| Corpo | 70% cabeça-corpo | 45% cabeça-corpo | 67% bípede | 62% bípede | 70% bípede |
- Baby I e II: um único osso "body" com 3–6 cubos; o bicho inteiro é a cabeça.
- Cada Digimon escolhe 6 animações da biblioteca compartilhada, em qualquer estágio. Voadores/nadadores aumentam a partir de Champion.

## Assinatura de uma evolução (cada criatura comparada com a própria pré-evolução)
Cobblemon, 469 pares:
| Passo | Altura no jogo | Cabeça % volume | Cubos | Pernas % altura | Olho/crânio |
|---|---|---|---|---|---|
| Bebê → básico (21) | ×1,96 (cresce 95%) | −33 pts (92%) | ×1,30 (86%) | +7 pts (92%) | −0,05 (75%) |
| 1º → 2º de 2 (237) | ×2,13 (97%) | −11 pts (78%) | ×1,54 (88%) | +4 pts (64%) | −0,05 (61%) |
| 1º → 2º de 3 (105) | ×1,75 (96%) | −15 pts (87%) | ×1,33 (81%) | +2 pts (65%) | 0 (54%) |
| 2º → 3º de 3 (106) | ×1,86 (92%) | −9 pts (86%) | ×1,60 (92%) | +4 pts (66%) | −0,04 (63%) |
- 71% das evoluções mantêm o tipo de corpo; quando muda, o mais comum é ficar de pé: sem pernas → bípede (52), quadrúpede → bípede (30).
- Cabeça % altura é métrica fraca (chifres, cristas e orelhas crescem junto); usar % volume.

Digimod, 427 pares:
| Passo | Altura | Cabeça % volume | Cubos | Pernas |
|---|---|---|---|---|
| Baby I → Baby II (22) | ×1,96 (100%) | continua 100% | ×2,38 (91%) | — |
| Baby II → Rookie (34) | ×1,49 (94%) | −51 pts (94%) | ×2,08 (85%) | 28 de 29 sem pernas ganham pernas |
| Rookie → Champion (176) | ×1,36 (85%) | −18 pts (89%) | ×1,38 (68%) | +5 pts (68%) |
| Champion → Ultimate (195) | ×1,28 (82%) | −1 pt (54%) | ×1,14 (56%) | 0 (51%) |
- Champion → Ultimate é o passo menos previsível (designs mecânicos/humanoides variados).

Exemplos: Charmander → Charmeleon → Charizard: cabeça 35% → 24% → 4% do volume; 0,8 → 1,3 → 3,4 blocos; 55 → 61 → 123 cubos. Botamon → Koromon → Agumon → Greymon → MetalGreymon: só cabeça → só cabeça → 41% → 35% → 30%; 8 → 16 → 25 → 39 → 51 unidades; 3 → 6 → 12 → 32 → 47 cubos.

Limitações: serpentes ficam esticadas na pose de repouso (Dratini 75 unid.), inflando altura de "sem pernas"; modelos sem osso head (ex.: Gastly/Haunter/Gengar) ficam fora das métricas de cabeça; amostras pequenas em bebês e lendários.

## Técnicas de estilo (não dependem do estágio)
- Cobblemon (1.170 geometrias): planos de espessura zero com recorte alfa = 45% dos cubos (asas, nadadeiras, espinhos, chamas, penas, orelhas); rosto como "adesivo" de planos 0,01–0,02 à frente da cabeça-cubo (82% olhos separados, 80% pálpebras, 42% variações de olhar, 35% ≥2 bocas); Box UV em 100%; 1 px/unidade; tamanhos inteiros 99,9%; inflate em 36% dos cubos; 96% com ossos rotacionados na pose de repouso; simetria quase total; texturas 64×64 a 128×128 na maioria, com camadas emissivas e texturas animadas.
- Ossos padronizados: head, body, torso, neck, tail1..n, leg_front_left/right, leg_back_left/right, arm_left/right, ear_left/right, eye_left/right, eyelid_left/right, pupil_left/right, jaw, mouth. Locators: mediana 18 (root, top, head, face, mouth, target, middle, item, foot, hand, tail_tip, eye, seat).
- Animações Cobblemon: mediana 9 por espécie (blink, ground_idle, cry, ground_walk, sleep, battle_idle, run, recoil, faint, happy/sad/angry, physical/special/status, ar/água). 53% dos canais animados são fórmulas (seno/cosseno do tempo com defasagem entre ossos); marchas procedurais prontas (q.quadruped_walk, q.biped_walk, q.sine_wing_flap); q.look (cabeça segue alvo); blink como quirk aleatório. Durações: blink 0,17 s, cry 1,5 s, faint 3 s.
- Digimod: mais simples (11% planos, 60% dos cubos rotacionados), olhos pintados na textura, biblioteca compartilhada digimons_anims.json com 83 animações escolhidas por criatura via nomes de ossos padronizados.

## Regras para o tradutor (revisadas)
1. Estágio é entrada obrigatória (bebê/básico/meio/final/único/lendário, ou Baby I…Ultimate) junto com o tipo de corpo.
2. A imagem do usuário manda no design; a faixa do estágio decide quanto exagerar ao cubificar (bebês/básicos puxam para cabeça grande; finais para cabeça pequena, pernas longas, mais detalhe).
3. Modo linhagem: traduzir todos os estágios juntos e validar a assinatura de evolução entre estágios vizinhos (altura ×1,3–2,1; cabeça −9 a −18 pts de volume; cubos ×1,3–1,6; olho menor em relação ao corpo; tendência a ficar de pé; andar mais lento). Inversões (como a do lich do vídeo do MagmaDev) viram erro.
4. Orçamento por estágio: cubos e tamanho de textura crescem com o estágio (Cobblemon ~40 → 55 → 90; Digimod 4 → 10 → 22 → 31 → 37).
5. Técnicas de estilo acima (planos, rosto adesivo, Box UV 1 px/unid., ossos padronizados, fórmulas seno, pose de repouso viva).

## Pipeline proposto (imagem livre → cubo)
Conceito livre no gerador de imagens (todos os estágios da linhagem) → folha frente/lado/costas → leitura semântica pelo Claude (tipo de corpo, partes, proporções, paleta, rosto, volume vs plano, estágio) → cubificador com faixas do estágio + medidas da silhueta (opcional: malha intermediária Hunyuan/TRELLIS + segmentação P3-SAM) → textura projetada e quantizada + rosto adesivo → ossos/locators padrão + biblioteca procedural por tipo de corpo e estágio → validação individual + validação da linhagem + 1 contact sheet → polimento no Blockbench → glTF com armadura (Roblox) ou Bedrock/GeckoLib (Minecraft).

## MCP do Blockbench escolhido
- https://github.com/jasonjgardner/blockbench-mcp-plugin (GPL-3.0; v1.10.1 em 16/out/2026; tags até v1.9.3).
  - Headless (stdio, desde v1.9): edita .bbmodel sem o app; bbmodel_edit aplica lote atômico; valida peças soltas, interseções, simetria, GeckoLib; valida animações (afundar no chão, membro descolando); exporta Bedrock/Java Block/Modded Entity; render e contact sheet (WebGPU: GPU + Node 23.6+); headless/call.ts chama ferramentas por script.
  - Desktop (HTTP, localhost:3000/bb-mcp): ~135 ferramentas; risky_eval (script JS inteiro no Blockbench; desligável); export_model glTF com armature + animations (o que o Roblox precisa).
  - Claude Code: `claude mcp add bbmodel --transport stdio -- npx -y github:jasonjgardner/blockbench-mcp-plugin --root <pasta>` e `claude mcp add blockbench --transport http http://localhost:3000/bb-mcp`; plugin no Blockbench via File > Plugins > Load Plugin from URL: https://jasonjgardner.github.io/blockbench-mcp-plugin/mcp.js
- Skills do mesmo autor (Apache-2.0): https://github.com/jasonjgardner/blockbench-mcp-project
- Alternativas (MIT, menores): sosadly/blockbench-mcp (set/2026), sigee-min/bbmcp (set/2026), enfp-dev-studio/blockbench-mcp (jul/2025, parado).
- Regra de tokens: Claude Code adia definições de MCP quando passam de 10% do contexto (Tool Search); o custo real é chamar ferramenta a ferramenta → sempre lote/script, nunca cubo a cubo. Skills como hairyf/minecraft-model fazem o oposto (design já em estilo Minecraft + cubo a cubo).

## Fontes
- https://gitlab.com/cable-mc/cobblemon
- https://wiki.cobblemon.com/index.php/Tutorials/Creating_A_Model
- https://wiki.cobblemon.com/index.php/Tutorials/Creating_A_Custom_Pokemon
- https://curseforge.com/minecraft/mc-mods/cobblemon
- https://github.com/ginerJ/The-Digimod
- https://moddex.gg/mod/the-digimod-beta
- https://github.com/jasonjgardner/blockbench-mcp-plugin
- https://github.com/jasonjgardner/blockbench-mcp-project
- https://github.com/sosadly/blockbench-mcp
- https://github.com/sigee-min/bbmcp
- https://github.com/enfp-dev-studio/blockbench-mcp
- https://www.skills.sh/hairyf/skills/minecraft-model
- https://claudelog.com/faqs/what-is-tool-search-in-claude-code/
- https://huggingface.co/tencent/Hunyuan3D-Part/blob/main/README.md?code=true
