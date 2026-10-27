---
tipo: sessao
data: 2026-10-27
fase: 10
ia: codex
status: aguardando-revisao-artistica
---

# F3 — espada em linha no Low e fatiada diagonal no Cross

**Para avaliar:** `f3/ataques-v3/criatura-pavao-e3-ataques-v3.bbmodel`,
aberta no Blockbench. GIF frontal do Cross e prévia 3/4 do Low na pasta.

**Pedido:** corrigir o braço direito entrando no esquerdo no Low a partir
de aproximadamente 0,55 s; espada deve seguir a linha do antebraço/punho,
conforme duas setas verdes. Cross: descida esquerda da v2 aprovada; somente
a direita precisava virar uma fatiada diagonal ascendente conforme o arco
vermelho frontal. As três imagens foram copiadas para `referencias/` na saída.

**Feito:** mesma duração, base de corpo e pernas. Low com eixo da espada
colinear ao antebraço durante o corte e arco limitado à frente do corpo.
Cross direito em curva ascendente que atravessa a frente da criatura;
primeira seção mais rasante, depois diagonal mais inclinada. Recupera para
a pose original do braço direito antes da descida esquerda.

Somente rotações de ombro, antebraço e mão direitos foram gravadas.
Demais canais/clipes, geometria, rig, pintura e UVs intactos. Todas as chaves
do lado esquerdo, corpo/pernas e armas do Cross são idênticas à v2; trecho
completo a partir de 0,725 s preservado, inclusive UUIDs das chaves. Total
de 21 clipes, 19 alheios aos ataques intactos. Nenhuma fonte manual sobrescrita.

Fonte SHA-256:
`60944297848eedfd53369202ea7101d2a63181faa045b684dbedc2a3a732251a`.
Saída SHA-256:
`0c9a90a3c7639c7fab0c25afa74927f97ebe23da553de91be72fdd95a3377cf4`.

**Conferência:** leitores linear/nativo em duas fases, 240 Hz, passaram.
Desvio antebraço/espada no Low <0,000002°; punho constante no corte, lâmina
presa à mão e bases das penas ancoradas. Cápsulas dos braços com folga
mínima >5 unidades nos dois clipes. Arco frontal do Cross progride cerca de
83,5 unidades para o lado oposto e 41,5 para cima. Fio dentro do plano
de corte; desvios máximos 5,12°/5,42°/1,75°. Sondagem opaca a 36 Hz sem
nova penetração nos volumes principais. Motor: zero erros/avisos a 120 Hz.
Chaves novas verificadas sem expoentes; ponte numérica não foi alterada.

**Referência do punho:** o proxy legado usava o eixo de repouso mantídeo
do antebraço como eixo da mão. O valor continua no relatório, explicitamente
diagnóstico; no Low o aceite usa o eixo geométrico da empunhadura, vínculo
e constância durante o corte. Não interpretar aquele proxy como amplitude
anatômica humana. Não houve mudança de rig ou dependência.

**Prévias:** dois GIFs reais, 98 quadros ao todo, câmera fixa por clipe,
com Cross frontal para comparar à anotação. Folha nativa conferida.
Limpeza da vista com erro conhecido de listener após remover o registro,
tratado pelo helper. Nova v3 aberta; Low pausado próximo do instante relatado.

**Documentação/Git:** scripts v3, saída, referências anotadas, estado atual,
ficha, plano e retomada atualizados. Base Git: `bed9bc3`.
Sem Studio, hitboxes ou lógica de combate. Spin permanece adiado na v1.

**Próximo passo:** feedback do alinhamento/recuperação do Low e do arco
direito do Cross, preservando a descida esquerda já aprovada.
