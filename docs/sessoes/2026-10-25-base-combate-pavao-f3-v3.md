---
tipo: sessao
data: 2026-10-25
fase: 10
ia: codex
status: aguardando-revisao-artistica
---

# F3 — guarda, marcha e saque como base de combate

**Avaliação para o usuário:** conferir somente `combat_ready`, `combat_walk`
e `combat_enter` na v3 aberta no Blockbench. Demais clipes ficam para depois.

**Retorno:** na v2c, espadas horizontais na guarda, braço de arrasto com anatomia
ruim e wings flutuando. Saque aprovado, floreio rejeitado: deve acontecer depois
de estabilizar a guarda e fazer uma volta completa vertical, pelos punhos.
Usuário confirmou pontas para cima/fora na guarda e braços elevados no floreio.
Ao conferir que a lâmina tem cerca de 56 unidades, foi consultado sobre a folga
no piso; preferiu inclinar as espadas em vez de usar salto ou encurtá-las.

**Feito:** snapshot da aba ativa em `f3/animacoes-v3/origem-revisada.bbmodel`;
saída nova `criatura-pavao-e3-combate-v3.bbmodel`. Mesmos 93 blocos, 41 grupos,
geometria, UVs, atlas e hierarquia. Só três clipes substituídos. Guarda de 2,4 s,
marchas de 1,8 s e saque/floreio de 2,1 s. Prévia individual em GIF e folha 768 px.

**Wings:** base dorsal real fica perto de Z=-6,08; pivô herdado em Z=-1,41.
A rotação de combate levantava a raiz das penas para fora das costas. Corrigido
com posição compensada nas chaves, girando sobre a base real. Mesma compensação
nas penas dos cotovelos; sem mudar o rig global dos clipes adiados.

**Arrasto:** ombro relaxado, cotovelo atrás, mão próxima ao quadril. Rolamento
da lâmina ajusta a preensão à direção do antebraço. Maior dobra longitudinal
do punho na marcha: 15,24°. Ponta acompanha o piso com desvio inferior a 0,00014
unidade. A outra espada continua apoiada no ombro.

**Saque:** ombros/cotovelos e trajetória aprovada preservados até 0,50 s.
Chega à nova guarda em 0,72 s e estabiliza até 0,90 s. Eleva braços até 1,15 s;
gira ambas as lâminas 360° entre 1,15 e 1,68 s, com 30° para fora; baixa até 2,10 s.
Sem salto, encurtamento, escala ou soltura da empunhadura. Menor folga da lâmina
ao solo: 0,606 unidade. Os pés mantêm apoio. Maior dobra de punho no saque: 72,08°.

**Verificações:** 240 amostras/s do arquivo salvo; mãos/armas, raízes das wings,
solas, ponta no chão, limites/eixo dos cotovelos, punhos, saltos de orientação,
volta completa, loops e conexões idle → enter → ready. Zero erros. Demais dez
clipes preservados integralmente em tempos/canais; o codec apenas normaliza
animadores vazios. Motor: zero erros estruturais e 194 avisos herdados de
sobreposição/simetria; animações revistas com zero erros/avisos. Dez testes de
`test_animar.py` passaram. Conferido também no Blockbench via MCP.

**Decisões:** ajustes específicos das chaves desta criatura; nenhuma mudança
de arquitetura, formato, dependência ou geometria. Fonte e edições do usuário
preservadas. Sem ações no Roblox Studio. Base anterior: commit `f66dada`.

**Próximo:** avaliação artística destes três clipes. Depois, adaptar os clipes
adiados a esta base. Start/stop, enter andando, camadas, descanso e saída ainda
são da v2; não considerá-los conectados à nova guarda. Fase 10 continua aberta.
