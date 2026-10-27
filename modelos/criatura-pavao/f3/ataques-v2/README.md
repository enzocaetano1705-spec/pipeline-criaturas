# F3 — Low e Cross por alavanca do ombro

Revisão para avaliação artística, após o retorno sobre cotovelos contraídos,
punho girando e fio desalinhado da v1. Sem alterar a anatomia/rig do modelo.

| Clipe | Duração | Revisão |
| --- | --- | --- |
| `attack_low` | 1,35 s | Mantém o caminho de peso do corpo da v1, retimado; prepara a espada direita, estende o braço e varre a linha baixa com o fio. Esquerda continua no ombro. |
| `attack_cross` | 1,95 s | Direita sai perto do piso, com extensão e subida conduzida pelo ombro, passando pela frente do corpo. Esquerda sai do ombro e faz a descida vertical até o chão; corpo avança e abaixa junto. |

Os lados são da criatura: direita era a espada em arrasto; esquerda estava
no ombro. Essa convenção continua a guarda e a marcha aprovadas.

O cotovelo fica com aproximadamente 10° de flexão nas fases de corte
(interior próximo de 170°, sem hiperextensão). O punho mantém a mesma
orientação relativa ao antebraço nessa fase. O ombro move o conjunto,
preservando a preensão e o fio no plano do corte. Preparação/recuperação
podem flexionar o cotovelo e reposicionar a empunhadura.

No Cross, a preparação transporta o plano da lâmina sem a meia-volta axial
desnecessária. O braço não é misturado contra um alvo de ombro que muda
continuamente: a cadeia é resolvida em conjunto. As correções de piso
preservam a extensão e a orientação relativa do punho.

19 clipes anteriores e geometria/UVs/atlas/outliner preservados integralmente.
Esta cópia tem 21 clipes. `attack_spin` ficou fora desta revisão; permanece
intacto em `../ataques-v1/`, sem aprovação e adiado pelo usuário.
Os dois golpes partem e retornam a `combat_ready@0`.

## Verificação e prévias

`validacao-ataques.json`: arquivo salvo, leitor linear e avaliador com
semântica numérica nativa a 240 Hz, em duas fases temporais. Apoios, juntas,
preensão, lâmina inteira, âncoras e retorno à guarda passaram. Novos critérios
verificam extensão, punho constante e fio alinhado à velocidade transversal
da lâmina durante o corte. Desvio máximo do fio: 9,53° Low, 6,32° ascendente,
1,75° descendente. A validação técnica não substitui aprovação artística.

Sondagem opaca a 36 Hz sem nova penetração de espada nos volumes corporais.
`validacao-motor.json`: zero erros/avisos de estrutura, timing, piso e
separação nos dois clipes, a 120 Hz. Cristas finas herdadas são intencionais.

`attack_low.gif` (40 quadros), `attack_cross.gif` (58) e `poses-nativas.png`
foram capturados do Blockbench via MCP. Câmera fixa; sem estabilizar a posição
do corpo. O plugin voltou a responder nesta sessão. No descarte da vista
privada, apresentou seu erro conhecido de listener depois de remover o
registro; a timeline foi restaurada e o plugin não foi modificado.

Referência para fio/plano do corte e relação ombros/quadril:
[Hasuji, Calgary Rakushinkan](https://calgaryrakushinkan.com/hasuji/).
Adaptação original à F3, sem afirmar que duas penas gigantes reproduzem
uma técnica histórica ou uma simulação física de combate humano.

## Reprodução

Na raiz: `uv run python scripts/animar-golpes-pavao-f3-v2.py --gerar --validar`.
Depois da geração completa, `--clipes attack_cross` permite rever só o Cross.
`--nativo` captura com esta versão aberta; `--previas` gera reserva em software.
A saída é protegida por hash contra sobrescrever edições manuais.

Marcadores em `animacoes.json` são propostas para futura integração.
Sem lógica de dano, pet, hitboxes, interrupções ou alterações no Roblox Studio.
