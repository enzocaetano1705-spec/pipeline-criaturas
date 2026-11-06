---
tipo: sessao
data: 2026-11-05
fase: ensaio malha 3D -> cubos
ia: claude-code
modelo: claude-opus-5-5
status: protótipo entregue; aguardando avaliação do usuário
---

# Preguiça rogue — conversão do FBX do Tripo para Blockbench

**Pergunta para o usuário:** o protótipo `modelos/fera-fera-agil-das-sombras/malha-v1/fera-sombras-e3-malha.bbmodel`
vai na direção certa? Abra no Blockbench e veja `comparacao.png` (malha × cubos) e `folha.png`.
Em caso positivo, os próximos passos são garras separadas, tufos/espinhos como planos e
ligação com o `texturizar`.

**Entrada:** FBX baixado pelo usuário do Tripo (plano grátis), 10.304 triângulos, textura JPG
4096 embutida, sem esqueleto/animação. SHA-256 `e27f2c3d…bf2`. Conceito e3 copiado da ficha.

**Feito:** `scripts/malha-para-cubos/` (extrair_malha, esqueleto, cubos, converter, comparar,
vistas) e [decisão 0013](../decisoes/0013-malha-3d-como-entrada.md). Conversão sem IA:
~10 s no Blender + ~20 s em Python.

**Resultado malha-v1 (v11, estilo equilíbrio):** 31 cubos + 14 planos recortados, 31 ossos,
10 locators, textura projetada 512² (UV 256²). Geometria idêntica à aba que o usuário
deixou no Blockbench (0 diferenças): cauda, braços, pernas e ligação da cauda vêm de `malha-v1/ajustes.json`.
Motor: 0 erros. Pronto para textura final/animação a critério do usuário. Abrir a cópia em `malha-v1/abrir/`.

**Iterações:** v1 só caixas de massa (39 cubos, IoU 61%, cauda inclinada pelo caminho mediano);
v2 eixo por PCA + componentes soltos (cobertura 96%, mas IoU 53%: caixas sobrando);
v3 ramos com ponta e caixa justa por ramo (56 cubos, IoU 64%).
Retorno do usuário sobre a v3: silhueta muito superior à das tentativas por imagem, mas caixas
cruzadas/embutidas, frestas, cauda com problema, cachecol bagunçado, garras e cabeça fracas.
Pediu cachecol como no Greninja do Cobblemon (gola grossa + fita em blocos menores ou planos).
Greninja estudado direto do jar local (gola 11×3×11; fita = 7 ossos com um bloco cada); nada
copiado. v4 (atual): perfil por trechos no eixo de cada parte (sem sobras cruzadas), cabeça em
degraus crânio → focinho pelo eixo do osso, 3 garras finas pela cor, gola + fita em 5 ossos,
limpeza de cubos embutidos.
Retorno sobre a v4: garra fora de posição, junção da cauda estranha (um trecho detalhado e outro
liso), pés e braços mal conectados, braço grosso demais, peça da gola estranha, pernas grosseiras;
pediu mais cubos (animação mais fluida). v5 (atual): membros/cauda/pescoço/cabeça como correntes
presas na junta, cauda com 5 ossos e pescoço com 2, seções mais finas nos membros, garras
paralelas, gola em anel de 4 cubos, fita achatada pela PCA, massa atrás de cada junta devolvida
ao pai (corcunda no tronco).

**Problemas e como contornei:** papéis dos pés pegavam tufos da cauda → mãos/pés exigem ramos
longos; ombros perto do centro → raiz do membro onde ele entra na massa do corpo (abertura
morfológica); cotovelo por curvatura instável → frações + simetria; caminho relativo do motor
gravava em `modelos/modelos/` → caminho absoluto.

**Limites:** sem planos para juba/tufos; garras e cachecol dependem da cor; papéis só para bípede
com cauda; textura de bloqueio, não final. Nenhum arquivo do Pavão ou documento pessoal foi tocado.

Retorno sobre a v5: garras com a mesma orientação errada desde a v1; cauda boa; braços e pernas
com juntas demais (mamífero tem poucos ossos nos membros); peça do meio do corpo, gola, sequência
das costas, cintura e pé estranhos. v6 (atual): um cubo por osso real nos membros (dois só se o
volume muda muito), pé deitado no chão, garras pelas pontas (k-médias das pontas + caixa da base
até cada ponta; antes a PCA da massa clara separava pela curvatura e gerava placas empilhadas),
tronco inteiro numa linha de coluna (base da cauda → base do pescoço), waist e neck_2 sem cubo,
gola numa peça só centrada em x = 0.

Escolha do usuário depois da v6: "a v4 com o rabo da v6 e as garras alinhadas" → estilo
equilíbrio (v7), padrão do conversor.

Pedido depois da v7: "bate com o modelo da Tripo e a imagem referência e arruma o quanto der".
Diagnóstico novo (`diagnosticar.py`): silhuetas na mesma câmera (malha × cubos, falta em azul e sobra
em laranja), fração de cada cubo fora da malha e lacunas nas juntas. Achados: braço, coxa e 1º bloco
da fita com 17–20 unidades (engoliam ombro, quadril e corcunda), cintura como placa de 3, lâmina no
antebraço, gola mais estreita que o pescoço, fresta entre pelve e cauda. v8: massa atrás de cada
junta volta ao pai, fita só com pano vinho, cintura e neck_2 sem cubo, membros presos nas juntas
(seção 8–92/12–88), tronco numa linha de coluna, pé deitado, gola em volta do cubo do pescoço,
base da cauda entrando na pelve; fita e juba como planos recortados (textura com transparência);
textura projetada da malha (cor do voxel de superfície mais próximo, paleta de 16 + destaques como o
dourado do broche, filtro de maioria 3×3). Comparação `referencia.png`: arte × malha × cubos de lado.

**Limites:** lado direito espelhado do esquerdo (a malha não é simétrica: garras da direita ficam
um pouco fora); garras retas (a arte tem garras curvas); textura projetada é para conferir, não pintura
final; a exportação Roblox amplia a textura ×8 — conferir o limite de 1024 px antes de exportar.

Retorno sobre a v8: cauda reposicionada pelo usuário no Blockbench (aba não salva; lida pelo MCP do
desktop com `get_undo_stack` e `export_model` embutido, sem gravar nada), vinho do cachecol manchando
ombros e coxa, braços abertos demais, joelho invertido, ombros com orientação estranha, cabeça
desproporcional; pediu menos cubos e transição mais suave. Causas: o classificador de vinho também
pegava o marrom do pelo (agora exige azul ≈ verde); o joelho ia pela metade do caminho até a ponta do
pé (caía no tornozelo); o braço girava nos 3 eixos (torção); a nuca virava uma tábua 10×4×4 por cima do
crânio. v9: joelho na dobra real (centro do volume) e tornozelo onde o pé sai do chão; membros com um
cubo por osso girado só em X e Z (sem torção); nuca devolvida ao pescoço e degraus da cabeça suavizados
(10 → 8 → 6); cauda com um cubo por osso e seções suavizadas; tronco em 2 cubos; textura dos cubos de
pelo sem vinho e sem dourado; fita orientada pela largura de cada trecho; gola mais discreta;
`ajustes.json` com a correção da cauda e os braços fechados, reaplicado a cada conversão; cópias
salvas à mão em `abrir/` não são mais apagadas.

Retorno sobre a v9: "ficou bem melhor"; o usuário arrumou as pernas no Blockbench (canela recuada,
alongada até o pé e inclinada 12,5°; pé recuado e chato; ligação da cauda 2 mais alta) e apontou
texturas ruins no rosto e no cachecol. Para a beta, modelos menos polidos são aceitos. v10: edições
das pernas lidas da aba (sem salvar) e guardadas em `ajustes.json` (`substituir_cubos`); ajustes
passam a entrar antes da UV (tamanhos podem mudar) e a pintura busca a cor de cada cubo movido na pose
da malha; textura por projeção ao longo da normal da face (bake por voxels) em vez do voxel mais
próximo; rosto em 3 tons (creme, pelo, escuro) com olhos desenhados na posição das pupilas da malha
(íris âmbar, pupila, sobrancelha escura); cubos do meio do corpo simétricos; fita do cachecol em
vinho chapado com contorno escuro, gola com moldura escura; planos de pelo sem vinho e sem dourado;
pé gerado chato (até 3) e canela descendo até ele.

Retorno sobre a v10: rosto bem melhor, mas a ponta do focinho "bugou" (a frente pegava o queixo escuro
da malha e virava um retângulo marrom, como uma boca aberta) e manchas rosadas no tronco/ombros onde o
pano do cachecol cai sobre as costas ("parece que era para ter algo ali"). v11: frente da ponta do
focinho creme com o nariz escuro desenhado na posição da ponta da malha; pano sobre ombros e costas
detectado pelo matiz (vermelho-magenta, inclusive o desbotado; o marrom fica de fora) e pintado como
o cachecol — vinho chapado com contorno — só em tronco, pescoço e braços (nas pernas continua sem vinho).

**Próximo passo:** com rosto e cachecol aprovados, animar (Codex) e exportar para o Studio. Depois: juba/tufos como planos, texturizar pelo
pipeline e exportar para o Studio.
