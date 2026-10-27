---
tipo: sessao
data: 2026-10-27
fase: 10
ia: codex
status: aguardando-revisao-artistica
---

# F3 — Low amplo e Cross com cotovelos externos

**Para avaliar:** `f3/ataques-v4/criatura-pavao-e3-ataques-v4.bbmodel`.
Low e Cross revistos a partir das três imagens anotadas, preservadas em
`referencias/` na saída. Spin continua adiado na v1.

**Pedido:** espada deve prolongar o antebraço/punho no Cross; cotovelo não
pode girar para dentro do peito. Diminuir a velocidade da primeira fatiada,
ampliá-la se necessário e inclinar a segunda à direita da criatura para
formar X. Low precisa de amplitude próxima ao arco roxo sem atravessar o
outro braço. A nova direção do corte esquerdo substitui a aprovação anterior
da descida vertical; não é uma mudança de arquitetura ou de rig.

**Feito:** Low de 1,65 s com varredura global de 165,74°, rotação adicional
do tronco e pivôs nos apoios. Espada alinhada ao antebraço e guarda esquerda
preservada. Cross de 2,40 s: direita percorre a diagonal ascendente com
cotovelo para fora e fase ativa cerca de três vezes mais longa que a v3.
Esquerda desce em diagonal oposta, inclinada 15° à direita da criatura.
O plano de flexão do cotovelo é controlado separadamente da orientação do
fio, mantendo a empunhadura. Depois do corte o braço recolhe; penas abrem
pela própria raiz. Pescoço recua discretamente para dar passagem à lâmina.

Foi corrigido também um erro na recuperação: um ângulo negativo fazia a
interpolação escolher a volta longa por trás. A recuperação agora segue
o arco curto à frente. Blends de orientação e plano do cotovelo foram
revistos para evitar saltos durante o retorno. As raízes das penas continuam
presas às juntas; não são deslocadas livremente para esconder contatos.

**Preservação:** 93 cubos, 41 grupos, rig, UVs e atlas idênticos à v3.
Outros 19 clipes intactos; 21 no total. Os dois ataques se conectam à guarda
aprovada nas extremidades. Nenhuma fonte manual sobrescrita.

Fonte SHA-256:
`0c9a90a3c7639c7fab0c25afa74927f97ebe23da553de91be72fdd95a3377cf4`.
Saída SHA-256:
`bdde82fff85922f61f35dc77360f2865f2286eab599bd6f601570701c01d7e6f`.

**Conferência:** arquivo salvo, leitores linear e numérico nativo a 240 Hz,
com duas fases de amostragem, passaram. Desvio máximo entre antebraço e
espada <0,004° nas fases ativas; fio até 5,31°. Folga mínima entre cápsulas
conservadoras dos braços: 1,95 unidades Low e 4,82 Cross. Penas opacas
contra peito/pescoço a 60 Hz: nenhuma penetração nova nas amostras, descontada
a guarda original. Cotovelos a mais de 3 unidades dos volumes principais.
Sondagem opaca de espadas/corpo e piso também passou. Motor independente:
zero erros/avisos de estrutura e dos dois clipes a 120 Hz.

`regressao-v3.json` registra a falha esperada da fonte: o teste novo detecta
aproximadamente 2,90 unidades de entrada da pena direita no peito. Na v4
o mesmo critério passa. Limiares não foram relaxados. Sondagens/cápsulas
são instrumentos de revisão, não hitboxes do jogo nem prova de anatomia humana.
O proxy legado de punho continua diagnóstico; o aceite usa o eixo geométrico
pedido, preensão e continuidade das articulações. Decimais sem expoentes.

**Prévias:** três GIFs do Blockbench com câmera fixa: Low em 3/4, Cross
frontal e Cross em 3/4. Folha de nove poses e parâmetros de captura na saída.
Nova v4 aberta para avaliação, Low pausado em 0,86 s. 194 quadros capturados
ao todo. Vista privada removida; erro conhecido do listener no descarte
tratado, e limpeza confirmada na lista de vistas. Relatórios e hashes
acompanham o modelo.

**Documentação/Git:** scripts v4, saída, imagens anotadas, estado, ficha,
plano e retomada atualizados. Base Git: `39669dc`. Sem Studio, hitboxes ou
lógica de combate. Fase 10 segue aberta, sem tag de conclusão.

**Próximo passo:** feedback artístico sobre amplitude do Low, plano dos
cotovelos, ritmo da direita e X do Cross antes de exportar.
