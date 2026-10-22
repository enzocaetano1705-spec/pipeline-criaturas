---
tipo: caso-piloto
caso: 2 de 12
data: 2026-10-22
criatura: criatura-pavao (e2, avinídeo, 2 de 3)
gabaritos: Harpymon (construção das peças); pavão F1 (crista, plumagem, olhos)
modo: adaptação por partes (não é recolor)
nota_final: modelo 3/10 no v1 (refeito à mão pelo usuário); textura 7,5 → 8/10; animação ok
---

# Caso 2 — pavão F2 (avinídeo)

Registro completo em [[2026-10-21-pavao-f2]]. Primeiro caso que não é recolor de um modelo existente.

## O que funcionou
- **Construção das peças pelo gabarito (Harpymon):** perna de ave, asa em planos, cauda em planos, corpo em blocos.
- **Linguagem de textura do caso 1:** plumagem em escama, penas com ocelo, ouro nas pulseiras e tornozeleiras.
- **Walk por cinemática inversa:** a trajetória do pé de avestruz define os ângulos.
- **Conferência:** diagrama de palitos com câmera fixa e o render do próprio motor.

## O que falhou e virou regra
1. **Postura:** sai da vista de lado (ângulo da coluna e da perna). O gabarito dá as peças, não a pose.
2. **Avinídeo:**
   - tronco inclinado de 50° a 75°;
   - cabeça à frente do peito;
   - perna em Z atrás do tronco;
   - mãos à frente do peito.
3. **Ornamentos (leque, crista, asas):** medidos em relação ao corpo nas vistas de lado e de costas.
4. **Olhos de ave:** ficam na lateral da cabeça.
5. **Remodelagem à mão:** depois de uma, achatar o rig, repor os pivôs nas juntas e passar cada peça para o osso da parte em que está encostada (penas da perna na perna).
6. **Pintura e UV:**
   - pintar pela orientação no mundo, não pelo nome da face;
   - refazer peças ancoradas (garras) a partir da âncora atual;
   - conferir `uv_width` ao mudar o atlas.
7. **Andar de ave digitígrada:** não se faz com ângulos chutados; é preciso cinemática inversa com o pé plantado.

## Arquivos
- **Modelo:** `modelos/criatura-pavao/f2/criatura-pavao-e2.bbmodel`. As versões do usuário estão em `f2/historico/`.
- **Scripts:**
  - `gerar-f2.py` (v1);
  - `finalizar-f2.py` (rig, garras, UV, textura);
  - `rodada3.py` (penas das pernas e walk por cinemática inversa);
  - `palitos.py` e `render_motor.py` (conferência).
