# Textura v4 — focinho inteiro, pano só no cachecol, fita contínua (06/11/2026)

Atual: **r03/fera-sombras-e3-textura-v4-r03.bbmodel**.

Entrada: `entrada-blockbench.bbmodel` — o arquivo que o usuário salvou no Blockbench (gola
ampliada para 15×15×3 e as edições anteriores). A geometria, a UV, os ossos e os locators não
mudam em nenhuma revisão desta pasta; só a textura.

Retorno do usuário sobre a v3/r03: "o cachecol ainda não está 100: algumas partes voando e outras
que eram para ser pelo e foram pintadas; o focinho é para ser basicamente todo pintado, afinal ele
é uma preguiça".

- **r01 (Codex, `restaurar.py` com `arte.json`):** `focinho_integral` — a última peça do focinho
  (`head_3`) inteira pigmentada, com luz, sombra e duas narinas; `pano_somente_scarf` — vinho só
  nas peças do cachecol (o resto vira pelo).
- **r02 (Claude, `fita_continua.py`):** o recorte dos 5 planos da fita (`scarf_1..5`) vem de uma
  fita única — o volume de pano vinho da malha que está no ar, fora dos cubos sólidos. Antes cada
  plano tinha contorno escuro também na emenda com o vizinho (pedaços "voando") e o `scarf_1`
  herdava o pano que fica sobre o ombro (uma lâmina atravessando o corpo). Agora o contorno fica só
  na borda real da fita. 0 erros; geometria/UV/ossos conferidos iguais à r01.

- **r03 (Claude, `limpar_ilhas.py`):** retorno "só esses dois bugs na textura": um tufo da base da
  cauda (`tail_1_fur`, 15 texels) boiando no ar entre a fita e as costas e um fragmento de 8 texels
  no `scarf_1`. Tufos que não encostam em nenhum cubo sólido (até 0,75) e poeira de pixels viram
  transparentes; na fita cada plano guarda só o pedaço principal. Conferência automática em 48
  ângulos: nenhuma peça solta na tela (resta só um traço de 2 px da ponta da fita exatamente de
  perfil). Geometria/UV/ossos iguais, 0 erros. `r03/antes-depois.png` mostra r02 × r03 de lado.

Vista de trás e de cima, a fita aparece como uma linha fina: é o plano de perfil, não uma peça solta.

```powershell
uv run python scripts/malha-para-cubos/fita_continua.py modelos/fera-fera-agil-das-sombras/malha-v1/textura-v4/r01/fera-sombras-e3-textura-v4-r01.bbmodel modelos/fera-fera-agil-das-sombras/malha-v1/voxels.npz modelos/fera-fera-agil-das-sombras/malha-v1/textura-v4/arte.json modelos/fera-fera-agil-das-sombras/malha-v1/textura-v4/nova/fera-sombras-e3.bbmodel
```
