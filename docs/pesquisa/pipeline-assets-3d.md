---
tags: [pesquisa, pipeline-criaturas, 3d, roblox, minecraft]
data: 2026-10-21
---

# Pipeline de assets 3D: opções, custos e workflow (pesquisa de 21/out/2026)

Objetivo: transformar imagens de conceito (feitas e corrigidas no gerador de imagens) em assets 3D de qualidade para Roblox e mods/add-ons de Minecraft, sem assinatura cara e sem gastar os limites do Claude Pro. Independente de qualquer jogo específico.

## Diagnóstico
- Cenários via LLM funcionam (composição de peças simples por código). Personagens orgânicos não: o LLM não deve inventar a forma, deve traduzir a imagem do usuário e cuidar do resto.
- Teste do dragão (Forja): textura calculada (oclusão + paleta) agradou; forma por parâmetros de template ficou sem carisma. Carisma vem do conceito em imagem.
- MCP é caro: captura 1920×1080 ≈ 2.691 tokens nos modelos atuais; 40 capturas ≈ 108 mil tokens. Código em vez de chamadas diretas: exemplo da Anthropic caiu de 150 mil para 2 mil tokens.

## Placar imagem→3D por preferência humana (benchmark.ai, out/2026)
Hi3D v3.0 1366 · Meshy 7.1 1299 · Meshy 7 1288 · Tripo H3.1 1261 · Hunyuan3D 3.1 Pro 1145 · Seed3D 2.0 1098 · TRELLIS.2 1005 (melhor aberto) · Rodin Gen-2.5 High 957 · Pixal3D 755 · Hunyuan3D 2.1 751 · TRELLIS 653.
Meshy 7 vence TRELLIS.2 em ~84% das comparações; Hunyuan 3.1 vence TRELLIS.2 em ~69%.

## Custos
| Opção | Detalhe |
|---|---|
| Meshy grátis | 100 créditos/mês; 10 downloads/mês só de Meshy 6 Lite; CC BY 4.0 (comercial com crédito) |
| Meshy Pro | US$20/mês, 1.000 créditos (~100 assets), privado |
| Tripo grátis | 200 créditos (~13), 15 downloads, público, não comercial (CostBench, confiança média) |
| Tripo Pro | US$20/mês, 3.000 créditos (~200), privado, comercial |
| Hunyuan 3D global | 20 gerações grátis/dia; OBJ/GLB; termos comerciais do grátis não confirmados |
| fal.ai | Hunyuan 2 mini turbo US$0,08; 3.1 rapid US$0,225; 3.1 pro US$0,375 por modelo |
| Hitem3D API | v3.0 quality US$1,30 por modelo |
| GPU alugada 24 GB | ~US$0,19 a ~US$0,73/h |
| GPU grátis | Kaggle (~30 h/semana relatadas, T4/P100 16 GB), Colab (T4), HF ZeroGPU (5 min/dia logado) |
Estratégia: iterar barato, assinar 1 mês só quando houver lote de finais (≈US$1/asset em 20 assets).

## Modelos abertos: VRAM e licença
- Hunyuan3D 2.0: 6 GB forma / 16 GB com textura. 2.1: 10 GB forma / 21 GB textura. Omni (controle por pose, caixa, voxel): ~10 GB. Licença: não vale UE/RU/Coreia do Sul; >1M MAU exige outra licença; proíbe treinar outra IA com os resultados. Brasil ok.
- TRELLIS.2 (MIT, 4B): 24 GB mínimo oficial; dependências (DINOv3, nvdiffrast) com licenças próprias; desvio de cor em ilustração chapada.
- Pixal3D (MIT, mai/2026), TripoSG (MIT, 8 GB), Step1X-3D (Apache 2.0), Stable Fast 3D (6–7 GB, licença comunitária Stability). SAM 3D Objects gera gaussian splats.
- Hunyuan 3.0/3.1/2.5: só hospedados.

## Pós-processo (onde a qualidade de jogo é decidida)
- Roblox: 20 mil triângulos por malha; 4 ossos por vértice; 1 animação por export; textura até 4096 no upload, orientação de até 1024 para PBR. Malhas com ossos de qualquer forma são animáveis (Bone).
- Redução: Decimate/QuadriFlow (Blender), Meshy Smart Topology (100–15 mil), Tripo P1.0 low-poly, MeshAnything V2 (≤1.600 faces, pesquisa).
- Partes: Hunyuan3D-Part, PartCrafter (MIT).
- Rig humanoide: Mixamo (grátis, só bípede), Roblox Avatar Auto Setup (A/T-pose, ≤10.742 tris), AccuRIG.
- Rig criatura: Tripo/Meshy (dizem suportar quadrúpedes), UniRig (MIT, 8 GB; piora sem ossos de cauda/asa), Puppeteer (pesquisa), Rigify (metarigs de animais).
- Animação: Mixamo/Meshy/Tripo para humanoides; criaturas com ciclos procedurais em script.
- Estilo unificado: rebake de textura com paleta + oclusão; Stable Projectorz para corrigir.

## Minecraft
- Java Block/Item sem rig; Bedrock, Modded Entity e GeckoLib com rig/animação em cubos. GeckoMesh (MIT) põe malha poligonal no GeckoLib.
- Meshy não exporta .bbmodel; sugere refazer em cubos.
- Rotas: código guiado pela imagem (estilo MagmaDev + validação); malha → partes → cubos (PrimitiveAnything, GPL-3.0, ~85% cubos); voxelizar só para blocos/estruturas.

## Blockbench → Roblox (jogo Roblox com arte estilo Minecraft) — adicionado em 21/out/2026
- Viável. Importador 3D do Roblox lê .fbx, .obj e .gltf; rig e animação só em FBX/glTF; Rig Type R15, Custom ou No Rig.
- Export glTF do Blockbench tem "exportar grupos como armadura" + "exportar animações" (conferido no código-fonte): cada grupo vira osso com os cubos 100% presos → uma malha skinned só, Rig Type Custom no Roblox (MeshPart + Bones).
- "Import with Animation" do Studio não traz animação do Blockbench de forma confiável (DevForum, mai/2025). Importar animações pelo Import do Animation Editor (Rig Type Custom) ou converter em lote com anim2rbx (MIT, FBX/glTF → KeyframeSequence).
- Cubo = 12 triângulos; criatura de 60 cubos ≈ 720 triângulos (limite 20 mil).
- Pegadinha: Roblox força filtro bilinear em textura de malha. SurfaceAppearance.ResampleMode existe na API desde v716 (abr/2026), mas ainda não funciona (relatos de ago/2026; release notes 729: "progresso ativo", sem data). Contorno: ampliar textura por vizinho mais próximo (8× = 64× pixels) + padding.
- Pipeline proposto: conceito blocky no gerador de imagens → Claude monta cubos por código guiado pela imagem → checagem por visão computacional (silhueta renderizada vs referência, IoU e proporções em números) → ajuste manual no Blockbench (.bbmodel é a fonte) → animações base procedurais como keyframes no .bbmodel → polimento na timeline do Blockbench → glTF com armadura → Roblox; locators do Blockbench viram Attachments (pontos de hitbox/VFX).
- IP: Cobblemon e Digimod usam IP de terceiros (Cobblemon diz não ser afiliado à Pokémon; código/binários MPL 2.0, nada libera modelos). Usar só como referência de estilo; criaturas originais. Não copiar texturas/mobs do Minecraft.

## Animação e combate no Roblox (2026)
- Onde animar: Animation Editor nativo (rigs com Motor6D e Bones; easing; 7 prioridades; KeyframeSequence; marcadores), Blockbench (mesmo estilo, export glTF), Blender (FBX → Import do Animation Editor, R15 ou Custom; update de ago/2026 quebrou alguns pipelines), Moon Animator 2 (plugin popular), Animation Capture (beta; corpo a partir de vídeo < 15 s; só R15).
- Adaptive Animation (GA 29/abr/2026): uma animação em R15, R6 e rigs custom via HumanoidRigDescription; rig humanoide blocky pode usar animações R15.
- Animation Graphs (GA 15/jul/2026): Blend1D/2D, camadas e máscaras (atacar com tronco enquanto corre), parâmetros via SetParameter, replicados. State machine nodes previstos para meados de 2027.
- Roadmap RDC26: movimento padrão com motion matching e root motion (início de 2027); NPCs por prompt (fim de 2026). Sem texto→animação oficial no Studio.
- Combate (guia de 2026 + ShapecastHitbox): cliente toca animação na hora; servidor valida alcance/cooldown/taxa; marcadores HitFrame/CancelOpen/RecoveryStart via GetMarkerReachedSignal; tabela de combo por arma (animação, dano, tamanho do hitbox); hitbox por cast entre frames a partir de Attachments "DmgPoint" da arma (no cliente, validado no servidor); Trail entre Attachment0/Attachment1 na lâmina; hit-stop 2–4 frames + tremor de câmera. Mesmos Attachments alimentam hitbox e VFX → alinhamento por construção.

## Workflow para virar skill
1. Conceito no gerador de imagens. 2. Referência pronta para 3D (A-pose, quase ortográfica, frente/lado/costas, luz uniforme, fundo liso). 3. 3–4 candidatos na rota mais barata; usuário escolhe. 4. Pós-processo automático no Blender headless. 5. Rig e animação por tipo de corpo. 6. Relatório de texto + 1 imagem de 4 vistas (~784 tokens) → export Roblox ou conversão Blockbench.
Pendente: saber GPU/VRAM do usuário para escolher local vs nuvem (menos crítico na rota Blockbench, que não precisa de GPU).

## Fontes
- https://www.benchmark.ai/image-to-3d
- https://app.cinevva.com/guides/ai-3d-model-generation-timeline-2026
- https://triposr.org/blog/hunyuan3d-versions
- https://nexgpu.net/en/models/trellis/
- https://github.com/Bingeljell/image-to-3dlab
- https://huggingface.co/TencentARC/Pixal3D
- https://help.meshy.ai/en/articles/15696428-what-is-included-on-the-free-plan
- https://www.meshy.ai/pricing
- https://www.costbench.com/software/ai-3d-generation/tripo-ai/
- https://costgoat.com/pricing/hunyuan-3d
- https://docs.hi3d.ai/en/api/getting-started/pricing
- https://huggingface.co/docs/hub/spaces-zerogpu
- https://gpuperhour.com/blog/free-cloud-gpus-and-credits
- https://create.roblox.com/docs/en-us/art/modeling/specifications.md
- https://create.roblox.com/docs/en-us/art/modeling/texture-specifications.md
- https://create.roblox.com/docs/avatar-setup/auto-setup-requirements
- https://create.roblox.com/docs/en-us/art/modeling/rigging.md
- https://devforum.roblox.com/t/beta-4d-generation-unlock-new-types-of-gameplay/4331818
- https://github.com/VAST-AI-Research/UniRig
- https://arxiv.org/html/2508.10898v1
- https://app.cinevva.com/guides/free-character-animations-rigging
- https://github.com/buaacyw/MeshAnythingV2
- https://www.blockbench.net/wiki/blockbench/formats
- https://www.curseforge.com/minecraft/mc-mods/geckomesh
- https://www.meshy.ai/use-cases/free-game-assets/minecraft
- https://github.com/primitiveanything/primitiveanything
- https://www.anthropic.com/engineering/code-execution-with-mcp
- https://platform.claude.com/docs/en/build-with-claude/vision
- https://huggingface.co/papers/2504.01786
- https://arxiv.org/abs/2508.08228v1
- https://create.roblox.com/docs/en-us/studio/importer.md
- https://devforum.roblox.com/t/how-to-import-model-with-animations-that-are-made-in-blockbench-into-studio/3639381
- https://forum.defold.com/t/blockbench-animation-guide/82193
- https://github.com/jiwonz/anim2rbx
- https://devforum.roblox.com/t/pixelated-resamplemode-for-surfaceappearances-pixel-art-meshes/4028314?page=4
- https://devforum.roblox.com/t/mesh-texture-pixel-art/2303754?page=4
- https://robloxapi.github.io/ref/class/SurfaceAppearance.html
- https://create.roblox.com/docs/animation/editor
- https://create.roblox.com/docs/en-us/animation/capture.md
- https://nilo.io/articles/export-blender-animation-roblox-studio
- https://devforum.roblox.com/t/full-release-adaptive-animation-use-one-animation-across-any-rig/4605672
- https://devforum.roblox.com/t/full-release-animation-graphs-create-complex-character-motion-visually/4739840
- https://devforum.roblox.com/t/full-release-the-future-of-character-movement-character-controller-library/4565267
- https://devforum.roblox.com/t/rdc26-what-we-announced/4865880
- https://www.npcmotion.com/blog/roblox-ai-tools
- https://create.roblox.com/docs/reference/engine/classes/KeyframeMarker
- https://create.roblox.com/docs/en-us/reference/engine/classes/Trail.md
- https://devforum.roblox.com/t/shapecasthitbox-for-all-your-melee-needs-v025/3624241
- https://kitsblox.com/blog/how-to-make-combat-system-roblox
- https://curseforge.com/minecraft/mc-mods/cobblemon
