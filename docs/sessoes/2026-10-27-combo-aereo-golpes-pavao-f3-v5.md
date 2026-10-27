---
tipo: sessao
data: 2026-10-27
fase: 10
ia: codex
status: aguardando-revisao-artistica
---

# F3 — aceleração, ataques independentes e combo aéreo

**Para avaliar:** `f3/ataques-v5/criatura-pavao-e3-ataques-v5.bbmodel`.
O Low mantém o arco aprovado, com aceleração revista. Três ataques para
alvos grandes substituem o Cross nesta cópia: `attack_right`, `attack_left`
e `attack_combo`. A v4 permanece intacta.

**Pedido:** sentir o peso na partida e na parada da espada, com ganho
rápido de velocidade no meio. Separar as duas fatiadas existentes. Criar
uma terceira animação em que a direita impulsiona um salto e um giro
completo, seguida de um golpe descendente com ambas as lâminas na queda.
Prioridade a fluidez, energia e cuidado com braços, penas, crista e coluna.

**Feito:** Low 1,42 s; direita 1,65 s; esquerda 1,50 s; combo 2,20 s.
Low recebe uma transformação monotônica do tempo sem mudar a trajetória.
Direita mantém o arco ascendente e ganha continuação/frenagem: tronco e
cintura acompanham, pernas recebem carga e cauda contrabalança. Esquerda
sai do ombro em um clipe independente, preservando a fatiada inclinada.
Todos começam e terminam na guarda aprovada, permitindo uso independente
ou sequência futura. Marcadores ficam em `animacoes.json`; sem lógica de jogo.

No combo, a preparação comprime pernas e tronco; o impulso coincide com
o começo do corte ascendente de 45°. A fatiada continua durante a entrada
no giro. Corpo gira 360° no ar, com pelve, peito e cauda em fases diferentes.
As pernas recolhem no voo e abrem para aterrissar. Esquerda arma lateralmente
antes de subir; direita acompanha a rotação antes de armar. As duas descem
juntas na queda e terminam no piso em 1,20 s; coluna e pernas comprimem e
recuperam. `root` move apenas em Y, de 0,40 a 1,20 s, com ápice de 20 unidades
e deslocamento líquido zero. Nenhuma peça foi escalada ou acrescentada.

**Preservação:** 93 cubos, 41 grupos, rig, UVs, atlas e outros 19 clipes
iguais à v4. Total: 23 clipes. Fontes manuais preservadas.

Fonte SHA-256:
`bdde82fff85922f61f35dc77360f2865f2286eab599bd6f601570701c01d7e6f`.
Saída SHA-256:
`ae7cc667173109185994087b62bb70fbf2d47e6b5c880b82cbc9f42444e4c2cd`.

**Problemas e correções:** normal invertida entre as etapas de elevação
da espada esquerda gerava giro axial brusco; normal agora é contínua.
Passagem da preparação para o primeiro corte recebe uma transição curta
antes da janela ativa. A direção do fio usa a velocidade global da lâmina,
incluindo ombro e salto, com correção encerrada antes do contato no solo.
As penas abrem em suas raízes durante a ação. O bake acrescenta amostras
onde a interpolação deslocaria essas raízes ou faria a lâmina entrar no piso.

**Referência:** [IWUF Taolu, seção 3.1.2.1](https://iwuf.org/wp-content/uploads/2021/09/EN-IWUF-Wushu-Taolu-Competition-Rules-Judging-Methods-Excerpt-2019.pdf),
páginas impressas 56–57, para separar impulso, rotação aérea e aterrissagem.
A coreografia com espadas gigantes é original e fantástica, conforme o
pedido; não é um movimento demonstrado por essa fonte. Sem nova dependência,
formato de modelo, rig ou decisão de arquitetura.

**Conferência:** ver `validacao-ataques.json`, `validacao-motor.json` e
`previas-nativas.json` na saída. Incluem hashes, preensão, articulações,
fio, raízes, continuidade, apoio/voo, piso e superfícies opacas contra corpo.
Clipes de voo têm janela própria; o salto não libera flutuação nos demais.
Proxy antigo de punho mantídeo é apenas diagnóstico; o aceite usa o eixo
geométrico do antebraço/espada, a preensão e o movimento das articulações.
Sondagens são auxiliares de revisão e não hitboxes de jogo ou prova clínica.
Arquivo salvo passou nos leitores linear/nativo a 240 Hz, com duas fases.
Âncoras até 0,006 unidade no avaliador nativo; desvio máximo braço/espada
durante os cortes <0,12° e fio <10°. Lâminas a aproximadamente 0,015 unidade
do piso no impacto. Sem nova penetração das lâminas nos volumes corporais
amostrados. Aceleração da ponta: pico/início médio 2,14× Low e 5,40× direita.
Motor: zero erros e avisos de estrutura e dos quatro clipes a 120 Hz.
Limiares de continuidade, vínculos e piso mantidos; voo permitido só na
janela explícita, com `root` restrito a Y.

**Prévias:** GIF de cada clipe, uma vista frontal adicional do combo e
folha de nove poses capturados no Blockbench. Vista privada removida; erro
conhecido do listener no descarte tratado. V5 aberta para avaliação.
Foram 270 quadros capturados, com câmera fixa por clipe. Folha nativa
conferida; combo selecionado no início e câmera principal enquadrada.

**Documentação/Git:** scripts, saída, estado atual, ficha, plano e retomada
atualizados. Base: `729aca2`. Fase 10 continua aberta, sem tag de conclusão.
Sem alterações no Studio, publicação de animações ou lógica de pet.

**Próximo passo:** retorno artístico sobre aceleração/frenagem e leitura do
combo aéreo. Spin antigo continua adiado; a nova animação é um combo aéreo
para alvos grandes, não uma retomada do ataque de área rejeitado.
