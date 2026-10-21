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
