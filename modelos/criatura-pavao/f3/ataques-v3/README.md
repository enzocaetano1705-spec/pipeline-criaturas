# F3 — alinhamento do Low e arco frontal do Cross

Revisão baseada nas três imagens anotadas pelo usuário em `referencias/`.
Fonte preservada: `../ataques-v2/criatura-pavao-e3-ataques-v2.bbmodel`.

- **Low (1,35 s):** eixo da espada prolonga o antebraço/punho durante a
  varredura. Limite do arco em mundo mantém a recuperação à frente do corpo,
  sem o braço direito entrar no esquerdo. Corpo, pernas e lado esquerdo
  preservam as chaves da v2.
- **Cross (1,95 s):** primeira fatiada parte da linha baixa à direita da
  criatura e cruza em diagonal ascendente para a esquerda. Visto de frente,
  segue o arco vermelho: da esquerda baixa da imagem para a direita alta,
  com começo menos inclinado. Fio orientado pela tangente do arco.
  Descendente esquerdo aprovado preservado integralmente, seguindo a linha azul.

Somente canais de rotação de `arm_right`, `forearm_right` e `hand_right`
foram revistos. UUIDs/clipes, geometria, hierarquia, atlas e UVs iguais.
Os outros 19 clipes permanecem intactos. No Cross, todas as chaves de corpo,
pernas, penas, arma e lado esquerdo são as originais; de 0,725 s em diante
até os três canais direitos são os mesmos da v2. As armas continuam presas
às mãos pela relação de preensão original, sem alterar seus canais.

## Conferência

`validacao-ataques.json`: arquivo salvo, leitor linear e avaliador numérico
nativo, 240 Hz em duas fases; vínculos, articulações, apoios, piso, âncoras,
continuidade e conexões passaram. Critérios específicos:

- desvio angular entre antebraço e espada no Low <0,000002°;
- folga mínima entre cápsulas conservadoras dos braços >5 unidades em
  ambos os golpes, incluindo a janela problemática de 0,55 s;
- deslocamento frontal da ponta no Cross: cerca de 83,5 unidades para o
  lado oposto e 41,5 para cima, com progressão horizontal contínua;
- fio: desvios máximos de 5,12° Low, 5,42° direita/Cross e 1,75° esquerda/Cross;
- sondagem de superfície opaca sem nova penetração nos volumes corporais.

O proxy antigo de punho transformava um eixo da pose mantídea do antebraço
como se fosse o eixo neutro da mão. Ele fica registrado no relatório, mas
para o Low é substituído pelo eixo geométrico solicitado, preensão e punho
constante na fase ativa. Não é uma medição de amplitude de uma articulação
humana. A geometria da mão continua a mesma.

`validacao-motor.json`: zero erros/avisos de estrutura e dos dois clipes
a 120 Hz. Folgas de cápsulas e a sondagem não são hitboxes de jogo.

Prévias `attack_low.gif`, `attack_cross.gif` e `poses-nativas.png` capturadas
no Blockbench via MCP, com câmera fixa por clipe. Cross em vista frontal
para comparar ao desenho. 40/58 quadros. Erro conhecido do listener no
descarte da vista tratado; registro privado removido e timeline restaurada.

## Reprodução

Na raiz: `uv run python scripts/animar-golpes-pavao-f3-v3.py --gerar --validar`.
`--clipes attack_cross` revisa somente o Cross depois da geração completa.
`--nativo` captura com esta versão aberta. Escrita em lotes pelo motor,
protegida por hash contra sobrescrever edições manuais. Decimais explícitos
nas chaves. Os canais preservados mantêm suas chaves/UUIDs originais.

Spin continua adiado na v1. Nenhuma alteração no Roblox ou na lógica de pet.
