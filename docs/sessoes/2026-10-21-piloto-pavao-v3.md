---
tipo: sessao
data: 2026-10-21
fase: 10
ia: claude
---

# Sessão — piloto do pavão v3 com o Koromon como gabarito

**Pedido:** enviar os commits do Codex e começar o piloto do método. O pavão é reconstruído com a construção do Koromon, conforme [[2026-10-21-retomada-claude]] e [[aprendizado-por-gabaritos]].

**Entrada nova:** prancha padrão do usuário, com o conceito à esquerda e frente | lado / costas | 3/4 à direita. `criaturas nova --prancha` corta os quadros e apaga os rótulos (commit `0586b56`). A prancha do pavão está guardada em `modelos/criatura-pavao/revisao-v3/prancha.webp`. Os arquivos `e1-*.png` da ficha não foram trocados.

**Feito:** o gerador `modelos/criatura-pavao/revisao-v3-koromon.py` cria a `revisao-v3/criatura-pavao-e1-v3.bbmodel`. As versões anteriores e o ensaio ficaram intactos.
- O corpo segue o gabarito: 2 volumes de mesma largura, com o de baixo avançando 1 unidade para formar a mandíbula e a boca. Mede 15 × 11 × 12, contra 12 × 11 × 11 no Koromon, porque largura e profundidade vêm da prancha.
- O rosto é só pintado, a 1 texel por unidade, num atlas 64×64 em Box UV:
  - olhos de 5×5 com brilho, que continuam 2 px na lateral;
  - gema em losango de 3×3 entre os olhos;
  - boca com os cantos subindo e 4 dentes de 1 px.
- As penas são a tira dobrada do gabarito (sobe, vai para trás, ponta com ocelo), com recorte alfa.
  - **Diferença 1:** a tira foi dividida em esquerda e direita para manter os ossos e os clipes `idle`/`walk` aprovados no ensaio.
  - **Diferença 2:** um plano complementar virado para o lado, porque a vista de lado da prancha mostra a pena (no Koromon as antenas somem de perfil).
  - **Diferença 3:** inclinação de −8° em vez de −17,5°, para bater com a altura do pico no perfil.

**Validação:** 0 erros e 0 avisos na geometria, 0 erros e 0 avisos nas animações. `comparar-referencias` contra o Koromon:

| medida | Koromon | v2 | v3 |
|---|---|---|---|
| volumes do corpo | 2 | 3 | 2 |
| texels por altura | 11 | 27 | 11 |
| opacidade dos planos das penas | 0,48 | 0,38 | 0,50 |
| área das penas vista de cima | 1,14 | 0,08 | 1,03 |

A largura do corpo, a largura das penas e a área de perfil divergem de propósito, pela prancha. Folha comparada com a prancha em `revisao-v3/comparacao-prancha.png`.

**Limites honestos:**
- O corpo é caixa, como no gabarito; a prancha é uma bola peluda.
- As penas ficam menores e mais esquemáticas que na ilustração.
- Em 3/4, o plano da frente e o plano lateral se cruzam.
- As animações passaram na validação, mas não conferi quadro a quadro com os novos pivôs.

Arte ainda **não aprovada**: aguarda o usuário.

**Próximo:** ajustar pelo retorno do usuário. Depois, registrar a correspondência pavão↔Koromon como o primeiro caso do piloto de 12 (ficha de construção por parte) e passar para um caso com gabarito oculto.
