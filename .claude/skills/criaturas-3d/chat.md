# Fluxo pelo chat (o usuário só anexa imagens e escreve)

O usuário não cria pastas nem renomeia arquivos: isso é seu. Ele anexa imagens e pede em texto. Nunca peça que ele mova arquivos.

## 1. Nova criatura
- **Formato padrão (desde 21/10):** o usuário anexa **uma prancha** com o conceito à esquerda e, à direita, frente | lado em cima e costas | 3/4 embaixo, cada quadro rotulado. Use `--prancha <caminho>`: o `nova` corta os 5 quadros e apaga os rótulos. Confira os recortes antes de seguir (`docs/criaturas/<nome>/e1-*.png`).
- Formato antigo: imagens soltas de **conceito**, **frente** e **lado** (costas opcional), com `--conceito/--frente/--lado/--costas`. Uma vista avulsa substitui o quadro da prancha.
- Cada imagem anexada aparece na conversa com `source: <caminho>`. Olhe as imagens para saber qual é qual (conceito 3/4, frente reta, lado reto). Se não der para saber, pergunte.
- Pergunte só o que faltar: nome, estágio (`1 de 3`…) e o prompt. Categoria e altura são opcionais (o pipeline pergunta a categoria depois).
- Crie a criatura:
  ```
  uv run criaturas nova <nome> --prancha <caminho>
  uv run criaturas nova <nome> --conceito <caminho> --frente <caminho> --lado <caminho> [--costas <caminho>] --estagio-texto "1 de 3" --prompt "<prompt>" [--categoria "plano › nicho"] [--altura 0.8] [--destino roblox,minecraft]
  ```
  Para um novo estágio da mesma criatura, use `--estagio e2` (o e1 continua na ficha).
- Rode `uv run criaturas tudo docs/criaturas/<nome>` e siga os passos de `SKILL.md` (checklist, leitura, categoria).
- **Devolva a folha:** depois do `folha`, mostre `modelos/<nome>/e1/folha.png` ao usuário (conceito + frente, lado, costas, 3/4). Ele aprova ou pede ajuste. Aprovado: `tudo … --folha-aprovada`.

## 2. Ajustes pedidos com print e uma frase
Ciclo, sempre:
1. `uv run criaturas ver <pasta>`: adota edições à mão, se houver, e grava `eN/ver.png` com a lista de peças (ossos, pais, tamanhos). Compare com o print do usuário. Abra `ver.png` só se o print não bastar.
2. Escreva o lote de correção (lista de operações do `bbmodel_edit`) num JSON no scratchpad.
3. `uv run criaturas aplicar <pasta> <lote.json> --motivo "<o que o usuário pediu>"`. Ele valida e registra no histórico. Se o motor recusar, nada muda.
4. `ver` de novo e mostre `ver.png` ao usuário.

Receitas (coordenadas em unidades do modelo; Y para cima, frente em −Z, lado esquerdo em −X):
| O usuário diz | Correção |
|---|---|
| "está sem um braço" | `add_group` (`arm_right`, pivô no ombro, pai `body`) + `add_cube` espelhando o `arm_left` em X, com `mirror_uv: true`. Depois `texturizar` (se a textura não foi pintada à mão) e `rig`. |
| "a arma está flutuando" | `update_node` no cubo da arma: `parent` = `hand_*` ou `forearm_*`, e `from`/`to` encostando na mão (confira as caixas no `ver --tudo`). |
| "esse pedaço ficou sem textura" | Se a textura não foi pintada à mão: `uv run criaturas texturizar <pasta>`. Se foi: diga ao usuário qual face está vazia; repintar com `--forcar` apaga a pintura dele. |
| "a parte X está grande, pequena ou torta" | `update_node` com `from`/`to` (tamanho inteiro) ou `rotation` no grupo. |
| "a animação buga nesse frame" | `uv run criaturas quadro <pasta> --anim <nome> --tempo <s>`: mostra as 4 vistas e as rotações dos ossos nesse instante. Corrija com `set_keyframe` (mesmo tempo substitui) ou `remove_keyframe`. |
| "refaz as animações" | `uv run criaturas animar <pasta>` (não toca nas que o usuário editou; `--forcar` regera essas também). |

Operações do `bbmodel_edit`: `add_group {name, origin, rotation, parent}`, `add_cube {name, from, to, parent, box_uv, uv_offset?, mirror_uv?}`, `update_node {target, name?, origin?, rotation?, from?, to?, parent?, mirror_uv?}`, `remove_node {target}`, `add_locator {name, parent, position}`, `set_keyframe {animation, bone, channel, time, value, interpolation}`, `remove_keyframe {animation, bone, channel, time}`, `add_animation`, `remove_animation`. Os alvos são o nome exato. Prefira sempre código (`aplicar`); MCP do desktop só se nenhuma operação resolver.

## 3. O usuário também edita à mão no Blockbench
- Qualquer comando (`ver`, `aplicar`, `texturizar`, `rig`, `animar`, `exportar`, `quadro`) primeiro **adota** a versão dele: compara com o último estado do pipeline, registra o que mudou em `eN/historico.jsonl` e segue a partir dela. Para só registrar: `uv run criaturas adotar <pasta>`.
- O que ele mexeu fica protegido: textura pintada à mão não é repintada e animação editada à mão não é regerada (só com `--forcar`, e só se ele pedir). Locators que ele moveu ficam onde ele pôs (`rig --forcar` recoloca).
- Não rode `cubificar` de novo depois que ele editou: isso recomeça a geometria do zero (ela sai como `.v2`, sem as edições dele). Use `aplicar`.
- Leia `historico.jsonl` (as últimas linhas) quando ele perguntar "o que mudou?" ou antes de um ajuste grande.
