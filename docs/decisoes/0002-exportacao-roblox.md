---
tipo: decisao
data: 2026-10-21
status: vigente
---

# 0002 — Exportação para o Roblox e dependências JS

**Contexto:** o .glb para o Roblox sai do Blockbench desktop (`export_model`, codec gltf). Era preciso um cliente MCP HTTP, um validador glTF e um jeito de não depender de cliques.

**Decisão:**
- O cliente MCP (`ferramenta/js/mcp-desktop.ts`) roda no Bun do clone fixado e importa o SDK oficial do MCP (MIT) de `externos/blockbench-mcp-plugin/node_modules`. Nada do plugin (GPL-3.0) é copiado.
- O validador é o pacote npm `gltf-validator` 2.0.0-dev.3.10 da Khronos (Apache-2.0), fixado em `ferramenta/js/package.json`. O `node_modules` não vai para o Git; `npm install --omit=dev` em `ferramenta/js` refaz.
- O `.glb` vem embutido na resposta do `export_model` (`result_format: "embedded"`) e o pipeline o grava. Gravar direto pelo `path` faria o Blockbench pedir permissão de arquivo (um clique do usuário).
- Os locators entram no `.glb` como nós filhos do osso, porque o exportador glTF do Blockbench não leva locators. No Roblox, `Bone` herda de `Attachment`.
- A cópia para o Roblox leva no nome um pedaço do hash do conteúdo, porque o Blockbench reaproveita a aba de um arquivo já aberto sem reler o disco.

**Alternativas descartadas:**
- Cliente MCP em Python puro: funcionaria, mas o plano pedia o SDK, que já está instalado.
- Exportador glTF próprio (plano B): não foi preciso. O export do Blockbench passou no validador da Khronos.

**Consequências:** a Fase 8 só fecha o Roblox com o Blockbench aberto e o plugin MCP carregado (`blockbench_launch` abre o app se estiver fechado). O resultado no Studio depende do teste do usuário (item 8.4). Para desfazer, troque `exportar_glb` por outro exportador e mantenha `verificar_glb`.

## Atualização 2026-10-21 — primeiro teste real no Studio (pavão)

O usuário importou o `.glb` do pavão (File › Import 3D, Rig Type Custom). O resultado foi uma malha com textura, os 7 ossos e o `idle`/`walk` em `ServerStorage.RBX_ANIMSAVES` (2,40 s com 59 quadros-chave e 1,33 s com 33, ambos em loop).

O que precisou de preparo no Studio, agora em `modelos/criatura-pavao/export/roblox/preparar-no-studio.luau`:
- **Alfa:** com `TextureID`, o alfa mostra a cor da peça, e os planos das penas ficaram com fundo escuro. A solução é um `SurfaceAppearance` com `ColorMap` igual ao `TextureID` e `AlphaMode.Transparency`.
- **Escala:** o modelo chega com 1 bloco = 1 stud, e o pavão media ~1,5 stud. `Model:ScaleTo(3)` levou para 4,7 × 3,2 studs.
- **UV fora de [0, 1]:** agora o `exportar` recusa antes de exportar (`uv_fora_do_atlas`) e o `verificar_glb` confere a faixa do `.glb` (`uv_do_glb`, tolerância 0,002).
- **Animação:** sem um `Animator` nada toca. Para a prévia, `KeyframeSequenceProvider:RegisterKeyframeSequence` gera um id temporário que só vale no Studio. O jogo publicado precisa da animação publicada.
- **Locators:** não chegam (o importador descarta nós sem malha). Ficam para quando o jogo precisar prender efeitos.

O teste no Run passou: o `idle` toca e o console não mostrou erro do modelo.
