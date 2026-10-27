---
tipo: sessao
data: 2026-10-27
fase: 10
ia: codex
status: aguardando-revisao-artistica
---

# F3 — Left acelerado, Right sem espera e combo fechado

**Para avaliar:** `f3/ataques-v6/criatura-pavao-e3-ataques-v6.bbmodel`.
`attack_low` v5 aprovado e preservado integralmente. O usuário aprovou
também o movimento do combo, pedindo apenas fechar as duas lâminas no
descendente. Print anotado preservado em `referencias/combo-fechado.png`.

**Feito:** Left de 1,50 para 1,32 s, com preparação mantida e aceleração
concentrada no corte; Right de 1,65 para 1,51 s, atravessando o antigo
intervalo 0,60–0,80 s em aproximadamente 0,06 s. Os primeiros 0,54 s do
Right mantêm o tempo original. Left preserva os valores e sequência das
poses por transformação monotônica do tempo. No Right, além dessa
transformação, a rotação axial do punho é distribuída de 0,60 a 0,91 s,
mantendo a direção da lâmina: comprimir a espera sem essa correção
também acelerava demais o desenrolar do punho. A parte rápida da retomada
mantém o ritmo original, evitando um novo pico de velocidade no ombro.

Combo continua com 2,20 s. Reduzida a abertura lateral do golpe duplo,
com as lâminas quase paralelas. Só rotação dos ombros e rotação/posição
das duas asas de cotovelo entre 0,90 e 1,62 s foram revistas. Cada braço
gira inteiro, preservando flexão do cotovelo, punho e empunhadura; o piso
é corrigido quando necessário. As raízes das penas continuam presas.
Salto, giro, tronco, cauda, pernas, crista e demais canais mantêm as
chaves/UUIDs da v5. Nenhuma fonte manual sobrescrita.

**Preservação:** Low e outros 19 clipes intactos, inclusive chaves/UUIDs.
23 clipes no total, com os mesmos 93 cubos, 41 grupos, rig, UVs e atlas.
Fonte SHA-256:
`ae7cc667173109185994087b62bb70fbf2d47e6b5c880b82cbc9f42444e4c2cd`.
Saída SHA-256:
`9b36df874a85b29edb79dde878bd07be8920c06515973e631ce478287ffb2500`.

**Conferência:** arquivo salvo e semântica numérica nativa, em duas fases
de amostragem; articulações, preensão, fio, continuidade, âncoras, apoio/voo,
piso e sondagem opaca contra o corpo. Critérios novos comparam aceleração
do Left à v5, duração da espera do Right e paralelismo/abertura do combo.
Limiares de contato, continuidade e vínculos mantidos. Proxy de punho
mantídeo continua apenas diagnóstico; os testes não são hitboxes do jogo.
Os leitores linear/nativo a 240 Hz, com duas fases, passaram no arquivo
salvo. Âncoras abaixo de 0,006 unidade; sem nova penetração de lâminas no
corpo nas amostras. Descendente do combo com divergência máxima de 1,05°;
abertura média entre pontas de 39,16 para 12,76 unidades. O teste confirma
20 clipes preservados e os demais canais do combo idênticos à v5.
Motor independente: zero erros/avisos de estrutura e dos três clipes revistos.

**Prévias:** GIFs dos três clipes, frontal e superior do combo e folha de
nove poses capturados no Blockbench. Câmeras/hashes na saída. V6 aberta
para avaliação; a vista privada de captura é removida ao terminar.
Foram 283 quadros capturados; folha nativa conferida. Limpeza da vista
confirmada na lista de vistas. O erro conhecido do listener no descarte
foi tratado pelo helper. Câmera principal em vista superior, combo
pausado em 1,20 s para comparar diretamente ao print anotado.

**Documentação/Git:** scripts, saída, estado atual, ficha, plano e retomada.
Base: `5ab0bc9`. Sem mudança de rig, arquitetura ou dependência. Fase 10
continua aberta, sem tag de conclusão. Sem Studio ou lógica de pet.

**Próximo passo:** feedback do ritmo do Left, recuperação do Right e
fechamento do combo. Low está aprovado. Ataque de área antigo segue adiado.
