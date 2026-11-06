# malha-para-cubos (experimental)

Converte uma malha 3D orgânica (FBX/GLB/OBJ do Tripo, Meshy etc.) num `.bbmodel` cubificado
com ossos (nomes de `docs/convencoes.md`, os mesmos do Pavão), locators e uma textura de bloqueio.
Nenhuma IA roda na conversão: é só código, cerca de 30 s por criatura.
Decisão: [0013](../../docs/decisoes/0013-malha-3d-como-entrada.md).

## Uso
```
# 1. malha -> voxels coloridos + renders de referência (Blender headless, ~10 s)
"C:/Program Files/Blender Foundation/Blender 5.1/blender.exe" -b --factory-startup \
  -P scripts/malha-para-cubos/extrair_malha.py -- <pasta>/entrada/<malha>.fbx <pasta>/voxels.npz --comprimento 64

# 2. voxels -> esqueleto -> partes -> cubos -> .bbmodel pelo motor (~20 s)
uv run python scripts/malha-para-cubos/converter.py <pasta> --nome <nome>-eN-malha [--garras 3] [--estilo equilibrio]
```
Estilos: `equilibrio` (padrão): massa atrás de cada junta volta ao pai, membros com um cubo por
osso girado só em X e Z (sem torção), joelho na dobra real, tronco em 2 cubos numa linha de coluna,
cabeça em degraus suaves, cauda com um cubo por osso e seções suavizadas, garras pelas pontas, pé
deitado, gola em volta do pescoço, fita e juba como planos recortados. `anatomia` (v6): um
cubo por osso real nos membros. Outras opções: `--textura projetada|bloqueio`, `--fator-textura 2`,
`--sem-pelo`.

```
# 3. conferir contra a malha (mesma câmera), juntas e cubos fora da malha
uv run python scripts/malha-para-cubos/diagnosticar.py <pasta>
```
Gera `diagnostico.png` (malha | cubos | sobreposição: azul = falta, laranja = sobra),
`diagnostico.json` e, se houver `entrada/conceito-lado.*`, `referencia.png` (arte × malha × cubos).
`<pasta>` = `modelos/<criatura>/malha-vN/`. `--comprimento` é o comprimento frente-trás em
unidades do Blockbench (16 = 1 bloco).

## Etapas
1. `extrair_malha.py`: eixos do Blockbench (Y cima, frente -Z, direita +X), voxels de 0,5 unidade
   por paridade de raios (voto 2 de 3), cor da textura em cada voxel da superfície.
2. `esqueleto.py`: pontas mais distantes da árvore (ramos curtos descartados), papéis do plano
   bípede com cauda (focinho, cauda, mãos, pés), ombros/quadris onde o membro entra na massa do
   corpo (abertura morfológica), simetria esquerda/direita, cauda com 5 ossos, pescoço com 2,
   corrente de 3–7 ossos para acessórios longos (cachecol pela cor).
3. `cubos.py`: Voronoi geodésico por osso; o que fica atrás de uma junta volta para o osso pai
   (ombro e corcunda vão para o tronco). Tronco (pelvis, waist, torso): perfil adaptativo.
   Membros, cauda (5 ossos), pescoço (2), cabeça e fita: correntes de cubos no eixo do osso,
   começando 1 unidade dentro do pai e terminando na junta seguinte, um cubo a cada ~3 unidades.
   Garras pela cor clara da mão, `--garras` caixas paralelas por mão. Cachecol: gola em anel de
   4 cubos por fora do pescoço; fita achatada numa corrente de 3–7 ossos (esquema do Greninja do
   Cobblemon). Pares esquerda/direita são ajustados juntos e espelhados; no fim, cubos quase
   inteiros dentro de outros são retirados.
4. `textura.py`: textura projetada — cada pixel é projetado ao longo da normal da face até a
   superfície da malha (bake por voxels), paleta curta com destaques, filtro de maioria, cubos do meio
   simétricos; rosto em 3 tons com olhos (pupilas da malha) e nariz (ponta do focinho) desenhados;
   cachecol em vinho chapado com contorno, inclusive o pano caído sobre ombros e costas (detectado pelo
   matiz); planos recebem recorte por transparência.
5. `converter.py`: textura (projetada ou bloqueio), locators, `ops.json` →
   `bbmodel_create`/`bbmodel_edit`, validação, `folha.png` (motor), `comparacao.png`,
   `vistas-claras.png` e uma cópia em `abrir/<nome>.<hash>.bbmodel` (o Blockbench não relê um
   caminho que já está aberto; abra sempre a cópia).

## Ajustes do usuário (reaplicados a cada conversão)
Correções artísticas ficam em `<pasta>/ajustes.json` e são aplicadas depois de pintar a textura:
```json
{"transladar": [{"a_partir_de": "tail_1", "manter_primeiro_cubo": true, "delta": [0, 4, 2]}],
 "girar_membros": [{"osso": "arm", "eixo": [0, 0, 1], "graus": 18}]}
```
`substituir_cubos` guarda a geometria exata de cubos editados à mão (ex.: as pernas da preguiça).
Uma edição feita no Blockbench e ainda não salva pode ser lida pelo plugin MCP do desktop
(`get_undo_stack` e `export_model` com `result_format: "embedded"`), comparada com o arquivo gerado e
anotada aqui. Cópias em `abrir/` salvas à mão não são apagadas pelo conversor.

## Correções manuais
Se uma junta ou ponta sair no lugar errado, crie `<pasta>/juntas-corrigidas.json`:
```json
{"juntas": {"forearm_left": [-15, 18, -16]}, "pontas": {"mao_left": [-16, 7, -29]}}
```
As posições estão em `juntas.json` e na imagem `diagnostico-juntas.png`.

## Retoque da textura já gerada

`retocar.py` trabalha sobre um `.bbmodel` existente sem reconstruir o esqueleto ou
a geometria. É uma revisão **específica da preguiça rogue**, com os nomes de peças
do protótipo; não é um corretor universal de criaturas. Recebe fonte, configuração
e destino novo; recusa sobrescrever um destino. As escritas passam por operações
do motor, e a assinatura estrutural completa deve permanecer igual à entrada.

```powershell
uv run python scripts/malha-para-cubos/retocar.py modelos/fera-fera-agil-das-sombras/malha-v1/textura-v2/entrada-blockbench.bbmodel modelos/fera-fera-agil-das-sombras/malha-v1/textura-v2/retoque.json modelos/fera-fera-agil-das-sombras/malha-v1/textura-v2/nova-revisao/fera-sombras-e3-textura.bbmodel
```

Produz `textura.png`, `ops.json`, modelo, validação, relatório, folha e comparação
antes/depois. Paleta e desenho do olho ficam na configuração; campos 3D de pano
e marca do ombro evitam contornos artificiais independentes nas faces. Limpeza
de componentes pequenos preserva marcas maiores e não usa suavização.

## Limites conhecidos (v1)
- Só o plano "bípede com cauda" tem regras de papéis.
- Garras e cachecol dependem da cor (garra clara, pano vinho); outra paleta pede ajuste em
  `cremoso`/`vermelho`.
- Planos de juba só no meio do corpo (perfil lateral); tufos laterais ficam na textura.
- A textura projetada serve para conferir; a pintura final é do pipeline de textura.
- O lado direito é o espelho do esquerdo (pose de descanso simétrica).
- Cubos se sobrepõem nas juntas (avisos de interpenetração do validador, esperados).
