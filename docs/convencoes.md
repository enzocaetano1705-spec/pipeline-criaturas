---
tags: [convencoes, pipeline-criaturas]
status: vigente
---

# Convenções do pipeline

Fonte única para nomes, unidades e formatos. Mudou algo aqui? Registre o motivo em `docs/decisoes/`.

## Direção artística
- Use pouquíssimos cubos e planos grandes para preservar a identidade visual e as proporções gerais da criatura. Não voxelize o arredondamento da imagem com fatias ou camadas só para reproduzir o contorno literalmente.
- Numa criatura simples, comece com 1–2 volumes para o corpo; rosto, pelo e marcas ficam principalmente na textura. Isso é um ponto de partida, não uma contagem universal.
- Membros e apêndices recebem apenas a geometria que ajuda a silhueta ou a animação. Detalhes pequenos não exigem cubos próprios.
- Os orçamentos das tabelas de referência servem como teto ou aviso, nunca como meta de quantidade de peças.

## Unidades e eixos
- 1 bloco do Minecraft = 16 unidades do Blockbench.
- Box UV com 1 pixel de textura por unidade.
- Y para cima. A frente da criatura olha para −Z (as vistas do motor headless são relativas a essa frente).
- Lado direito da criatura = +X (regra da mão direita com Y para cima). Conferido na Fase 0 (21/out/2026): na vista `front` do render headless (câmera em −Z), um braço em −X aparece à direita da imagem, ou seja, é o lado esquerdo da criatura. A exportação Bedrock espelha X (`leg_front_left` sai com X positivo no `.geo.json`); isso é do formato, não muda a convenção.
- Rotações em graus, aplicadas na ordem Z·Y·X em torno do pivô (igual ao `bbmodel_edit`).
- O código do pipeline nunca escreve `.bbmodel` à mão: tudo passa por operações do `bbmodel_edit`, que cuida das convenções do formato 5.0. O exportador do protótipo Forja (formato 4.10) é só referência.

## Formato do modelo
- `.bbmodel` versão 5.0, `model_format: "bedrock"` (Box UV e tamanhos inteiros).
- **Volume:** cubo comum.
- **Plano:** cubo com uma dimensão 0 e recorte por transparência na textura. Use para asas, nadadeiras, orelhas finas, penas, chamas, bigodes e espinhos finos.
- **Adesivo:** plano encostado na superfície (olhos, pupilas, pálpebras, boca, marcas). Permite piscar e trocar expressão.
- `inflate` pequeno (0,1 a 0,5) só para camadas externas (pelo, casco).
- Juntas encostam sem atravessar. A sobreposição de 1 unidade gera aviso de interpenetração no validador; se for usar, documente.

## Hierarquia e nomes de ossos
Nomes em inglês, snake_case. O lado é sempre o da criatura (`_left` e `_right`).

```
root                         no chão, origem 0,0,0; só anima em saltos
└─ body                      pivô na bacia ou centro de massa
   ├─ torso                  peito (bípedes)
   │  ├─ neck_1 … neck_n
   │  │  └─ head
   │  │     ├─ jaw
   │  │     ├─ eye_left / eye_right → pupil_*, eyelid_*   (adesivos)
   │  │     ├─ mouth                                      (adesivo)
   │  │     └─ ear_*, horn_*, crest, antenna_*
   │  ├─ arm_left → forearm_left → hand_left   (o mesmo para right)
   │  └─ wing_left → wing_left_2               (o mesmo para right)
   ├─ leg_left → shin_left → foot_left         bípede
   ├─ leg_front_left, leg_front_right,
   │  leg_back_left, leg_back_right            quadrúpede (shin_ e foot_ com o mesmo sufixo)
   ├─ tail_1 → tail_2 → … → tail_n
   └─ fin_<posição>, tentacle_<i>_<j>, leg_<i>_<lado> (insetos)
```
- Um osso por parte que se move, com o pivô na junta.
- Cada cubo pertence ao osso da sua parte. Só `body` fica direto sob `root`.

## Locators
Viram Attachments no Roblox e locators no Bedrock. A posição é absoluta, em unidades do modelo.

| Nome | Para quê |
|---|---|
| `loc_head_look` | centro da cabeça; alvo do olhar |
| `loc_mouth` | sopro, VFX de ataque, partículas |
| `loc_eye_left`, `loc_eye_right` | brilho e efeitos nos olhos |
| `loc_hand_left`, `loc_hand_right` | arma ou item; a hitbox e o trail da arma partem daqui |
| `loc_foot_*` | poeira dos passos (mesmo sufixo da perna) |
| `loc_tail_tip` | rastro da cauda |
| `loc_center` | centro do corpo; hitbox e alvo dos inimigos |
| `loc_top` | acima da cabeça; nome e barra de vida |
| `loc_ground` | sombra e círculo de seleção |
| `loc_ride` | montaria (opcional) |

## Animações
| Nome | Loop | Duração típica |
|---|---|---|
| `idle` | sim | 2–4 s |
| `walk` | sim | ciclo por estágio: 1,33 s (inicial), 1,5 s (meio), 2,0 s (final) |
| `run` | sim | ~0,75 s |
| `blink` | não | 0,17 s; o jogo dispara a cada 2–6 s |
| `cry` | não | ~1,5 s |
| `attack_physical`, `attack_special` | não | 0,8–3 s |
| `hurt`, `faint` | não | 0,5 s / 2 s |
| `sleep` | sim | 4 s |
| `fly_idle`, `fly` | sim | alados |
| `swim` | sim | aquáticos |
| `happy`, `sad`, `angry` | não | expressões |

- Mínimo por criatura: `idle`, `walk` e `blink`.
- Olhar para um alvo é feito em código no jogo, não como animação.
- As chaves são "assadas" (sem fórmulas Molang) para funcionarem no Roblox. A exportação Bedrock usa as mesmas chaves.
- Marcadores de combate (Roblox) ficam em `animacoes.json`, ao lado do modelo: `HitFrame`, `CancelOpen` e `RecoveryStart`, com o tempo em segundos.

## Pastas e arquivos
```
docs/criaturas/<nome>/            entrada do usuário (ver docs/criaturas/LEIA-ME.md)
modelos/<nome>/
  entrada.json                    ficha normalizada
  linhagem.json                   relatório da linhagem
  e1/
    preparo/                      imagens recortadas, versões de 768 px e com grade
    classificacao.json
    leitura.json                  leitura semântica feita pela IA
    medidas.json                  medidas tiradas da silhueta
    plano-cubos.json
    ops.json                      lote enviado ao bbmodel_edit
    <nome>-e1.bbmodel             gerado; se você editou à mão, a próxima versão sai como <nome>-e1.v2.bbmodel
    textura.png
    textura-roblox.png            ampliada por vizinho mais próximo
    folha.png                     4 vistas ao lado do conceito
    animacoes.json                marcadores e eventos
    relatorio.json
  export/roblox/<nome>-e1.glb
  export/minecraft/…
```
- `<nome>`: minúsculas, sem acento, palavras separadas por hífen (ex.: `raposa-de-fogo`).
- Estágios: `e1`, `e2`, `e3`…

## Categorias e estágios
- As chaves de plano de corpo (10) e de nicho (19, mais "outros") são as de `referencia/medidas.json`, em minúsculas e com acento (ex.: `bípede com cauda`, `dragão`, `roedor/pequeno mamífero`). As tabelas de `docs/pesquisa/categorias-criaturas.md` usam os mesmos nomes com inicial maiúscula.
- Estágio da ficha → estágio das tabelas:

| Ficha | `por_estagio` de planos e nichos | `estagios.cobblemon` |
|---|---|---|
| 1 de 3 | inicial | `1º de 3` |
| 2 de 3 | meio | `2º de 3` |
| 3 de 3 | final | `3º de 3` |
| 1 de 2 | inicial | `1º de 2` |
| 2 de 2 | final | `2º de 2` |
| 1 de 1 | único | `único` |
| bebê (pré-estágio) | inicial | `bebê` |
| lendário | lendário | `lendário/mítico` |

Linhagens com 4 ou mais estágios usam as tabelas do Digimod (`Baby I`, `Baby II`, `Rookie`, `Champion`, `Ultimate`).

## Paleta e textura
- Até 5 cores base e 2 de destaque por criatura, cada uma expandida numa rampa de tons (como em `referencia/prototipo-forja/forja/style.py`).
- Textura de 64×64 quando couber, senão 128×128.
- Versão Roblox: ampliação ×8 por vizinho mais próximo, com 2 px de margem em volta de cada ilha de UV.

## Limites dos destinos
- **Roblox:** até 20 mil triângulos por MeshPart (um cubo tem 12), até 4 ossos por vértice (aqui sempre 1, rígido), textura de até 1024 px recomendada.
- **Minecraft Bedrock:** só cubos (malhas não exportam). GeckoLib segue as regras de validação próprias do `bbmodel_validate`.
