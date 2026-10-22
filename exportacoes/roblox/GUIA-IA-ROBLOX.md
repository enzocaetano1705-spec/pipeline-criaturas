# Guia para IAs: criaturas no Roblox Studio

Para qualquer IA ou harness (Claude, Codex, outro) que vá trabalhar com as criaturas deste repositório dentro do
Roblox Studio, normalmente pelo MCP do Studio (`execute_luau`, `search_game_tree`, `inspect_instance`,
`start_stop_play`, `get_console_output`). Leia isto antes de mexer em um modelo.

## 1. O que existe e onde está

| arquivo | o que é |
|---|---|
| `exportacoes/roblox/criaturas.json` | lista das criaturas: nome no Studio, estágio, escala, animações, velocidade do walk |
| `exportacoes/roblox/<especie>/<Nome>.glb` | o modelo pronto para importar (malha, ossos, textura e animações) |
| `exportacoes/roblox/<especie>/<Nome>-textura.png` | a textura que está dentro do .glb (1024 px), só para consulta |
| `exportacoes/roblox/preparar-criatura.luau` | script de preparo, para rodar depois de importar |
| `scripts/exportar-roblox.py` | gera os .glb a partir dos `.bbmodel` aprovados (precisa do Blockbench desktop aberto) |

**Nomes:** `<Especie>_F<estágio>`, por exemplo `Pavao_F1` e `Pavao_F2`. O nome do `.glb` é o nome do Model no Studio.
Nunca renomeie no Studio sem atualizar o `criaturas.json`.

## 2. Importar

1. Faça File › Import 3D (ou Avatar › Import 3D) e escolha o `.glb`. Em **Rig General**, use **Rig Type: Custom**, nunca R15.
2. O Studio sobe a textura para a conta do usuário, então é preciso estar logado. **Importar é ação do usuário.** Uma IA
   não deve tentar contornar isso.
3. Se já existir um Model com o mesmo nome, apague o antigo **e** a pasta dele em `ServerStorage.RBX_ANIMSAVES`.
   Os nomes se repetem e os scripts pegariam o errado.

## 3. Anatomia do modelo importado

```
Workspace.<Nome>              Model
├─ Raiz                       MeshPart (malha única, com skin; TextureID = textura)
│  └─ body, neck_1, head, leg_left, shin_left, foot_left, arm_*, wing_*, tail_1, feather_* …   Bones
├─ AnimationController        (precisa de um Animator dentro; o preparo cria)
├─ AnimSaves                  ObjectValue → ServerStorage.RBX_ANIMSAVES.<Nome>
└─ InitialPoses               CFrameValues da pose de repouso (não mexer)
ServerStorage.RBX_ANIMSAVES.<Nome>
├─ idle                       KeyframeSequence (loop)
└─ walk                       KeyframeSequence (loop)
```

- A `Raiz` é um osso só de exportação: não tem rotação nem animação (só uma chave neutra) e virou a MeshPart.
  **Nunca gire a Raiz na exportação:** com ela girada 180°, o Roblox aplicou as animações dos ossos exageradas e o
  pescoço descolou.
  **Nenhuma animação pode mover a MeshPart.** Se o corpo "descolar", sumir ou a colisão bugar no Play, é porque
  a animação está movendo a peça física: reexporte com a Raiz (`scripts/exportar-roblox.py` já faz isso).
- **Poses das animações:** o Roblox não anima a pose do topo de uma KeyframeSequence, porque ela é a peça raiz.
  O exportador põe uma chave neutra na `Raiz`, para que o topo seja `Raiz > body > …`, e o preparo também conserta isso
  em importações antigas. Sem isso, o balanço do corpo (`body`) não toca.
- **Escala de osso não existe no Roblox:** animações de escala (como a respiração do idle do Pavao_F1) não aparecem lá.
- Ossos sem nenhuma peça (alguns `feather_fan_*`) não chegam. É normal.
- Os locators do Blockbench (`loc_*`) não chegam: o importador descarta nós sem malha. Para prender efeitos, crie
  Attachments no osso mais próximo.
- **Frente:** o Blockbench exporta a frente em +Z, e a malha chega com a cabeça para o lado oposto ao `LookVector`
  dela. Por isso a frente da criatura é a **`Hitbox`**: o preparo a aponta para a cabeça, medindo do osso da cauda
  ao da cabeça. Mova e oriente a criatura sempre pelo `LookVector` da Hitbox, nunca pelo da malha.

## 4. Preparar (sempre, depois de importar)

Abra `preparar-criatura.luau`, ajuste `NOME`, `ESCALA` (do `criaturas.json`) e `PREVIA`, e rode pelo MCP
(`execute_luau`, datamodel `Edit`) ou pela barra de comandos. O script:

- põe um `SurfaceAppearance` com `AlphaMode.Transparency` e **`ResampleMode = Pixelated`**. Com `TextureID`, o alfa
  mostra a cor da peça e penas e orelhas ficam com o fundo escuro. Sem `Pixelated`, a pixel art fica borrada;
- aplica `Model:ScaleTo(ESCALA)` e apoia a base no chão;
- cria a **`Hitbox`**: uma Part invisível do tamanho da criatura, que colide, é o PrimaryPart e fica soldada à malha.
  A malha fica sem colisão (`CanCollide = false`, `Massless`);
- cria o `Animator` e, se pedido, o Script `TocarAnimacao`, que toca uma animação em loop no Run/Play;
- aponta a Hitbox para a cabeça (ossos `head` e `tail_1`; sem eles, assume +Z da malha) e imprime como decidiu;
- embrulha as poses das animações numa pose da Raiz, para importações antigas sem a chave neutra.

Tudo fica numa gravação do `ChangeHistoryService`: um Ctrl+Z desfaz.

## 5. Animações

- As animações vêm como **KeyframeSequence local**. Um id criado com
  `KeyframeSequenceProvider:RegisterKeyframeSequence(seq)` **só vale nos testes do Studio**.
- **No jogo publicado:** publique cada KeyframeSequence pelo Animation Editor (o usuário publica). Guarde o `AnimationId`
  e use `Animator:LoadAnimation(anim)`. Registre os ids publicados no `criaturas.json` (`ids_publicados`).
- Para tocar:
  ```lua
  local faixa = modelo.AnimationController.Animator:LoadAnimation(anim)
  faixa.Looped = true
  faixa:Play()
  ```
  - Para trocar `idle`↔`walk`, use `faixa:Stop(0.2)` e toque a outra com fade.
- **Velocidade:** o walk anda no lugar, com o pé deslizando para trás como numa esteira.
  - Para o pé não patinar, mova o PrimaryPart na velocidade do `criaturas.json` (`walk_studs_por_s`, na escala indicada).
  - Em outra escala ou velocidade, ajuste com `faixa:AdjustSpeed(velocidade_real / walk_studs_por_s * escala_studio / escala_atual)`.
- **Mover um NPC:** mova o PrimaryPart (`Hitbox`) com `PivotTo` e `CFrame.lookAt` para a direção do passo. Pode ser via
  TweenService, `RunService.Heartbeat` ou `AlignPosition`/`AlignOrientation` com a Hitbox desancorada. A criatura não usa
  Humanoid.

## 6. Texturas: por que borram e o que já foi feito

- **A correção é `SurfaceAppearance.ResampleMode = Enum.ResamplerMode.Pixelated`.** Existe no Studio desde
  2025–26 e o preparo já liga. Sem ela, o Roblox usa filtro bilinear e a pixel art borra até de perto. De longe, o
  mipmap ainda suaviza um pouco.
- **O que já foi feito na exportação:**
  - a textura é ampliada sem suavizar até **1024** (o máximo que o Roblox guarda sem reduzir);
  - o **alfa é sangrado**: os pixels transparentes levam a cor do vizinho opaco, o que tira o contorno escuro
    em volta de penas e orelhas.
- **No Studio:** para julgar a textura, use a qualidade gráfica no máximo (File › Studio Settings › Rendering ›
  Editor Quality Level) e olhe de perto. De longe, o mipmap sempre suaviza.
- **Nunca reamostre a textura no Studio nem a substitua por outra imagem:** para mudar a textura, reexporte.

## 7. Reexportar

```bash
uv run python scripts/exportar-roblox.py            # todas as criaturas do criaturas.json
uv run python scripts/exportar-roblox.py Pavao_F2   # só uma
```

O exportador:
- recusa UV fora da textura;
- valida o `.glb` com o validador da Khronos;
- põe a `Raiz` (com chave neutra), sangra o alfa, amplia para 1024 e dá o nome à cena.

Depois disso, importe de novo no Studio e rode o preparo.

## 8. Checklist quando algo parecer errado

| sintoma | causa | o que fazer |
|---|---|---|
| fundo escuro nas penas/orelhas | falta o `SurfaceAppearance` | rode o preparo |
| contorno escuro fino nas bordas recortadas | `.glb` antigo, sem alfa sangrado | reexporte |
| linha transparente numa borda | UV fora da textura no `.bbmodel` | corrija no Blockbench (o exportador já recusa) |
| corpo descola, some ou flutua no Play | animação movendo a MeshPart (sem `Raiz`) | reexporte |
| anda de costas ou vira para o lado errado | está sendo movida pelo LookVector da malha | mova pela `Hitbox` (o preparo a aponta para a cabeça) |
| animação exagerada, partes descolando | `Raiz` girada na exportação | reexporte (a Raiz não pode ter rotação) |
| textura borrada | `ResampleMode` não está `Pixelated` | rode o preparo |
| animação não toca | sem `Animator`, ou id temporário fora do Studio | rode o preparo ou publique a animação |
| pernas animam, mas o corpo não balança | a pose `body` está no topo da KeyframeSequence | rode o preparo (passo 4b) ou reexporte |
| colisão estranha | malha colidindo | rode o preparo (Hitbox) |

## 9. Boas maneiras pelo MCP

- Antes de alterar, liste os Studios (`list_roblox_studios`) e confirme o lugar. O usuário tem outros jogos abertos.
- Ache o modelo pelo nome do `criaturas.json`. Se houver dois com o mesmo nome, compare o `TextureID`.
- Faça cada alteração dentro de uma gravação do `ChangeHistoryService`.
- Não apague nem altere modelos que não foram pedidos.
- Para testar, use `start_stop_play` (true), leia o `get_console_output` e **pare o teste** (false) no fim.
- A captura de tela do MCP às vezes volta em branco. Confira por código, por exemplo `Bone.Transform` mudando entre dois
  instantes, ou peça um print ao usuário.
