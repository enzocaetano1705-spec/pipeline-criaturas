---
name: criaturas-3d-chat
description: Ajuda a preparar a ficha de uma criatura para o pipeline 3D cubificado (Cobblemon/Digimod -> Roblox/Minecraft) no chat — confere as imagens, faz o checklist morfológico, sugere 3 categorias (plano de corpo › nicho) e o estágio, e checa se a ficha está pronta para modelagem. Não modela. Use quando o usuário trouxer imagens ou o prompt de uma criatura e quiser deixar a ficha pronta.
---

# Criaturas 3D — ficha e classificação (chat)

No chat não há o repositório nem o código: aqui só se prepara a **ficha**. A modelagem acontece depois, no Claude Code, a partir dela.

Arquivos de apoio nesta skill:
- `referencias/requisitos-imagens.md`: como devem ser as imagens, os números da evolução, as dicas e o checklist "pronta para modelagem".
- `referencias/ficha-modelo.md`: o modelo da ficha a preencher.
- `referencias/categorias.md`: planos de corpo, nichos, tabelas por plano e nicho, pares que se confundem e o protocolo de classificação.

## Fluxo
1. **Imagens.** Para cada imagem enviada, confira os requisitos (corpo inteiro, fundo liso, luz chapada, pose neutra, mesmo design nas vistas, 1024–1536 px). Diga o que falta, sem refazer a imagem por conta própria.
2. **Checklist morfológico, só pela imagem.** Antes de ler o prompt, preencha os 13 itens (postura, pernas, braços, asas, cauda, nadadeiras, pescoço, cabeça, focinho, orelhas, olhos, cobertura, extras). Cada item recebe valor, certeza (visível, incerto ou oculto) e fonte (imagem). Prefira medidas (cabeça como fração da altura, focinho ÷ crânio) a palavras.
3. **O prompt só completa.** Leia o prompt e troque apenas itens incertos ou ocultos (fonte: prompt). Item visível não muda. Se o prompt contradiz a imagem, vale a imagem: liste o conflito.
4. **Três sugestões.** Compare o checklist com `referencias/categorias.md` e dê até 3 opções `plano › nicho` com %, os 2 ou 3 traços que justificam cada uma e o estágio aparente (pela cabeça e pelo olho). Use os "pares que se confundem" para separar vizinhos (canídeo × felino, dragão × dinossauroide, ave × morcego, peixe × serpente, canídeo × ungulado).
   ```
   1. Quadrúpede › canídeo — 70%: 4 patas, focinho médio, cauda cheia
   2. Quadrúpede › felino — 20%: cabeça grande, cauda fina
   3. Bípede com cauda › roedor — 10%: postura ambígua
   Estágio aparente: inicial (cabeça ~45% da altura)
   ```
   O usuário escolhe 1, 2, 3 ou outra categoria. Não escolha por ele.
5. **Ficha.** Monte a ficha no formato de `referencias/ficha-modelo.md`, com o que o usuário confirmou:
   - nome (minúsculas, sem acento, com hífen), destino, estilo e número de estágios;
   - por estágio: estágio (1 de 3…), categoria (palpite e confirmada), altura no jogo, imagens, o que a imagem não mostra bem, partes finas (viram planos), rosto, jeito de se mover e o prompt exato.
6. **Pronta para modelagem?** Passe o checklist do fim de `referencias/requisitos-imagens.md` item por item e diga o que falta. Compare as alturas e as cabeças entre estágios com a tabela (cada evolução cresce de 1,75× a 2,1× e a cabeça perde de 9 a 15 pontos). Só quando tudo estiver ok, sugira mudar para `status: pronta-para-modelagem`.

## Regras
- A forma vem da imagem do usuário. Não invente partes, cores nem proporções.
- Estágio e categoria são entradas obrigatórias da ficha. A categoria final é do usuário.
- Nada de copiar modelos, texturas ou animações de Cobblemon e Digimod: os números das tabelas são só referência.
- Respostas curtas: uma tabela ou uma lista por passo, e a ficha completa no fim.
