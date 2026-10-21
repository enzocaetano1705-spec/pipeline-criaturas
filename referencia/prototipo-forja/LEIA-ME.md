# Protótipo Forja (só referência)

Primeira tentativa, feita antes da pesquisa: ela inventava a forma a partir de moldes por plano de corpo. A textura agradou; a forma saiu sem carisma (o "dragão gordo"). Por isso o pipeline novo lê a forma da imagem do usuário. Não use os moldes (`templates.py`) para criar criaturas.

Funciona com Python 3.12, numpy e Pillow. Teste rápido (gera `.bbmodel` 4.10, textura, prévia e relatório):
```bash
cd referencia/prototipo-forja
python -m forja exemplo_spec.py --out saida --sem-gif --raios 12
```

## O que vale reaproveitar
| Arquivo | Ideia útil |
|---|---|
| `render.py` | renderizador por software (numpy + Pillow): folha de 4 vistas sem GPU, nas mesmas convenções de face e UV do Blockbench. Base do item 1.7. |
| `texture.py` | layout de UV, AO por raios, dilatação de ilhas, decalques de rosto (olhos, pupilas, blush). |
| `style.py` | paletas por papel ("primary", "belly", "eye"…) com rampas OKLCH: sombras puxam para tons frios, luzes para quentes. |
| `anim.py` | marchas procedurais: bípede, quadrúpede, hexápode, tentáculos, blob, balanço de corrente com defasagem. Base da Fase 6, adaptada aos nomes de `docs/convencoes.md`. |
| `check.py` | correção de z-fighting, peças soltas, juntas, simetria, equilíbrio do centro de massa. |
| `core.py` | encaixe relativo de peças (`Box.on(pai, at=…, anchor=…, sink=…)`), pivôs nas juntas, espelhamento. |
| `export_bb.py` | escreve `.bbmodel` 4.10 direto. **Não usar no pipeline novo**: lá tudo passa pelo `bbmodel_edit` (formato 5.0). |

## Defeitos conhecidos (o validador headless encontrou)
- As pernas entram 1 unidade no corpo (`sink=1`), o que gera 8 avisos de interpenetração.
- No `walk`, o pé traseiro afunda 0,6 unidade abaixo do chão aos 0,1 s.
