# Protocolo de leitura semântica (a parte da IA)

Entrada: `modelos/<nome>/eN/preparo/<vista>-grade.png` (frente e lado), a ficha e a categoria confirmada.
Saída: `modelos/<nome>/eN/leitura.json`. O contrato `ferramenta/criaturas/contratos/leitura.schema.json` pode ser lido: ele diz quais campos são obrigatórios (`id`, `pai`, `tipo`, `simetria`, `caixas`) e quais são opcionais (`espelho`, `rotacao_repouso`, `papel_cor`, `segmentos`; no topo, `papeis_cor` e `incertezas`).
A IA diz **o que** é cada parte e **onde** ela está na grade. O código (`criaturas medir`) encosta as caixas na silhueta real e calcula as medidas em 3D.

Antes da primeira geometria, use `referencias.md` para decidir a simplificação. O campo opcional `modelagem` guarda abordagem (`poucas_formas` ou `silhueta_fatiada`), justificativa e referências por papel. Em `poucas_formas`, cada volume descrito gera um cubo; a curvatura do desenho não é convertida automaticamente em fatias. Detalhes pintados não pedem uma parte geométrica só para existir no checklist.

## Regras
1. **Olhe só as versões com grade.** No máximo `frente-grade.png` e `lado-grade.png` (2 imagens de 768 px). As costas só se tiverem detalhe que muda a forma.
2. **Nunca invente parte.** Toda parte listada aparece em pelo menos uma vista. Nada de "deve ter garras", "provavelmente tem língua".
3. **Incerteza segue uma ordem:** imagem → prompt → faixa da categoria. Se a imagem não resolve, use o prompt. Se o prompt também não, deixe o código usar a tabela. Registre cada caso em `incertezas` com `resolucao` (`imagem`, `prompt` ou `tabela`). Quando for a tabela, escreva "da tabela" na nota.
4. **Caixas na grade.** `[x0, y0, x1, y1]` em células, com uma casa decimal se precisar. Origem no canto superior esquerdo do desenho; y = 32 é o chão. Desenhe a caixa justa do que **aparece** da parte nessa vista. Se ela está toda escondida numa vista (perna de trás atrás da da frente, olho de perfil), não ponha caixa nessa vista.
5. **Vistas:**
   - frente: o lado **esquerdo** da criatura aparece à **direita** da imagem;
   - lado: é o lado esquerdo da criatura, com a frente à esquerda da imagem (se o conceito estava virado, o `preparar --espelhar-lado` já virou);
   - costas: o lado esquerdo aparece à esquerda.
6. **Ids padrão** de `docs/convencoes.md`: `body`, `torso`, `neck_1…`, `head`, `jaw`, `eye_left`, `mouth`, `ear_left`, `horn_left`, `arm_left`, `forearm_left`, `hand_left`, `wing_left`, `leg_left` (bípede) ou `leg_front_left`/`leg_back_left` (quadrúpede), `shin_*`, `foot_*`, `tail_1…`, `fin_<posição>`, `tentacle_<i>_<j>`. Peças sem nome padrão: snake_case em inglês (`snout`, `beak`, `crest`).
7. **Pai** é a parte em que a peça se apoia e com que se move: `head` → `body`, `ear_left` → `head`, `tail_2` → `tail_1`. O `body` tem `pai: null`.
8. **Tipo:**
   - `volume` para quase tudo;
   - `plano` para partes finas: asas, nadadeiras, orelhas finas, penas, chamas, bigodes, espinhos finos;
   - `adesivo` para o que é pintado na superfície e mexe: olhos, pupilas, pálpebras, boca, marcas.
9. **Simetria:** liste o lado esquerdo (`_left`, `simetria: esquerda`, `espelho: <id>_right`). O direito pode ficar de fora: o código espelha. Liste o direito só se ele for diferente.
10. **Correntes** (cauda, pescoço, tentáculo): uma parte por segmento visível (`tail_1`, `tail_2`…), cada uma com sua caixa. Se a cauda é uma peça só, use `tail_1` com `segmentos: N` (o cubificador divide).
11. **Rotação de repouso** (`rotacao_repouso`, graus X, Y, Z): só para partes visivelmente inclinadas (cauda erguida, orelhas abertas). Aproximada, de 15 em 15 graus.
12. **Papéis de cor:** dê nome às 3 a 5 cores base (`primaria`, `barriga`, `escura`…) e às 1 ou 2 de destaque. Para o hex, não chute a olho: amostre pixels de `preparo/<vista>-recorte.png` com um trecho de Python (Pillow) e use a cor mais comum da região. Cada parte recebe `papel_cor`.
13. **Peças que aparecem em uma vista só** (focinho, ponta da cauda, crista vistos só de perfil) entram como parte própria com caixa só nessa vista. O código completa a largura.

## Depois
1. Grave `modelos/<nome>/eN/leitura.json`.
2. Rode `uv run criaturas medir <pasta> --estagio eN`. Ele imprime as partes medidas e os avisos (diferença maior que 10% entre vistas, profundidade estimada).
3. Se um aviso apontar uma caixa errada, corrija só essa caixa e rode de novo. Não reabra as imagens sem necessidade.

## Exemplo (trecho, de uma raposa; os números são ilustrativos)
```json
{
  "vistas": {"frente": {"imagem": "preparo/frente-grade.png"}, "lado": {"imagem": "preparo/lado-grade.png"}},
  "partes": [
    {"id": "body", "pai": null, "tipo": "volume", "simetria": "central", "caixas": {"frente": [2, 18.5, 11.5, 23.6], "lado": [21, 8.5, 44.5, 21.4]}, "papel_cor": "primaria"},
    {"id": "head", "pai": "body", "tipo": "volume", "simetria": "central", "caixas": {"frente": [0, 6.7, 13.5, 18.5], "lado": [6.5, 0, 21, 15]}, "papel_cor": "primaria"},
    {"id": "ear_left", "pai": "head", "tipo": "plano", "simetria": "esquerda", "espelho": "ear_right", "caixas": {"frente": [8.5, 0, 13.5, 6.7]}, "papel_cor": "escura"},
    {"id": "tail_1", "pai": "body", "tipo": "volume", "simetria": "central", "caixas": {"lado": [44.5, 10.7, 53, 15]}, "papel_cor": "primaria"}
  ],
  "papeis_cor": {"primaria": "#d9772b", "escura": "#5a3520"},
  "incertezas": [{"parte": "tail_1", "item": "largura", "resolucao": "tabela", "nota": "escondida na frente; largura da tabela"}]
}
```
