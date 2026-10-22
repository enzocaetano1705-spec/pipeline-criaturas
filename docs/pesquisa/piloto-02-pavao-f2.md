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

## Exportação
- **Roblox:** `export/roblox-f2/criatura-pavao-e2.glb`, com 792 triângulos e textura de 1024. O validador da Khronos não acusou erros e o UV ficou dentro de [0, 1].
- **No Studio, em 22/10:** o modelo chegou com 23 dos 27 ossos (os sem malha, como alguns `feather_fan_*`, não vêm) e com idle e walk.
- **Preparo aplicado pelo MCP:**
  - `SurfaceAppearance` com alfa recortado;
  - escala 3×, o que dá 5,9 × 8,3 × 10,9 studs, ao lado do F1;
  - `Animator`;
  - script `TocarAnimacao` (walk).
- **Teste:** no Run, o walk tocou e as pernas se moveram, sem erro no console.

## Roblox, segunda rodada (22/10)

**Relato do usuário:** a textura estava borrada; a animação estava exagerada, com o pescoço descolando; e a criatura andava de lado invertido, com o corpo sumindo.

**Causas encontradas e correções:**
- **Corpo sumindo:** o osso de cima virava a MeshPart. Agora há uma `Raiz` sem animação, só com uma chave neutra.
- **Animação exagerada:** a `Raiz` estava girada 180°. Agora ela é neutra, e a frente é dada pela `Hitbox`, que o preparo aponta para a cabeça.
- **Textura borrada:** a correção é `SurfaceAppearance.ResampleMode = Pixelated`, que agora existe no Studio. Junto com isso, a textura vai em 1024 e com alfa sangrado.

**Teste no Play, medido no `Transform` dos ossos:** os giros máximos batem com os do Blockbench:

| osso | giro máximo |
|---|---|
| body | 4,7° |
| pescoço | 7,0° |
| cabeça | 9,3° |
| quadril | 31,9° |
| joelho | 18,4° |
| tornozelo | 32,5° |

O corpo sobe e desce 0,08 stud (0,45 unidade × 0,1875), e a malha fica parada.

## Roblox, terceira rodada (22/10): animação parada no Play

**Causas:**
- A prévia rodava no servidor. Um id criado por `RegisterKeyframeSequence` no servidor não toca no cliente, e no Play quem desenha a tela é o cliente.
- O lugar tinha cópias duplicadas de `Pavao_F1` e `Pavao_F2` sem preparo, porque a recuperação automática do Studio voltou com as duas importações.

**Correção:**
- prévia em `Script` com `RunContext = Client`, lendo as animações de `<Model>.Animacoes`;
- `ModelStreamingMode = Persistent`;
- preparo aplicado às 4 cópias.

**Teste no cliente (Play):** as 4 criaturas com a faixa tocando e os ossos se movendo, sem erros no console.

## Roblox, quarta rodada (22/10): "walk invertendo de lado" e olho borrado

**Lado invertido:** a recuperação automática do Studio trouxe de volta cópias importadas do `.glb` antigo, com a `Raiz` girada: em (14,7; 1,6; 7,4) [F1] e (1; 4,1; 7,5) [F2]. Nelas a pose `Raiz` tem 180° e, no F2, o `body` também, então o corpo vira de lado no walk. As cópias do `.glb` atual estão certas: o quadril segue os mesmos ângulos do Blockbench (+15° → −32°) e o `body` fica perto de 0°. **Solução:** apagar as cópias antigas e usar só as do `.glb` atual.

**Olho do F2 borrado:**
- O atlas tem 256 (as ilhas somam 30.886 px², não cabem em 128), e a ampliação para 1024 é só 4×.
- O olho tem 3×3 pixels: o bilinear do Roblox, em pixels de 4 texels, deixa o traço visivelmente borrado.
- O resto do corpo passa porque é textura de ruído.

**Proposta:** exportar a cabeça (crânio, bico e crista) com uma textura própria e pequena (64 → 1024, 16×, igual ao F1, que fica nítido). O `.glb` sai com duas malhas, e o Roblox cria duas MeshParts sobre o mesmo esqueleto.
