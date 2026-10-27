---
tipo: sessao
data: 2026-10-27
fase: 10
ia: codex
status: aguardando-revisao-artistica
---

# F3 — extensão dos braços e fio nos golpes Low/Cross

**Para avaliar:** `f3/ataques-v2/criatura-pavao-e3-ataques-v2.bbmodel`,
aberta no Blockbench, e os dois GIFs nativos na mesma pasta.
Spin adiado e isolado na versão anterior, fora desta cópia.

**Pedido:** usuário aprovou a base de peso do Low, mas rejeitou cotovelos
contraídos, rotação excessiva do punho e fio batendo de lado. Cross precisava
de ascendente realmente baixo, conduzido pelo ombro/corpo, e descida vertical
da espada já apoiada no ombro, até o chão. Braços devem funcionar de forma
próxima à humana em combate. Mantidos os lados previamente confirmados:
direita ascende, esquerda sai do ombro e desce. Essa interpretação foi
explicitada antes de editar, pois a última frase do pedido chamou também
o descendente de direito.

**Feito:** Low de 1,35 s, mantendo a trajetória de peso anterior retimada;
Cross de 1,95 s com ascendente baixo e descendente vertical. Cotovelos com
10° de flexão durante os cortes, punhos constantes relativamente aos
antebraços, orientação do fio ligada ao plano da ação. O ombro orienta a
cadeia inteira; a espada continua rigidamente presa à mão. Corpo da descida
avança/abaixa, patas mantêm apoio e penas/cauda respondem ao movimento.

21 clipes: 19 anteriores preservados integralmente, dois golpes revistos,
spin ausente desta cópia. Geometria, rig, UVs, textura e outliner iguais à
fonte v1; nenhuma edição manual sobrescrita. Origem SHA-256:
`006093385217323fab2df3f4278d5b7b74147b94570d16553f71d32f3f1c2299`.
Saída SHA-256:
`60944297848eedfd53369202ea7101d2a63181faa045b684dbedc2a3a732251a`.

**Problema identificado:** o controle antigo liberava rolamento axial para
reduzir a dobra do punho e não exigia extensão, permitindo um gesto de tapa
com lâmina lateral. Substituído por cadeia direta, flexão prescrita e punho
estável. Durante a revisão, uma mistura de ombro contra alvo variável e
uma meia-volta axial na preparação provocaram passagem ruim entre chaves.
Preparação reconstruída por direção/rolamento transportado, sem inverter
a face da lâmina; piso resolvido com a cadeia completa.

**Verificação:** leitor linear e avaliador de semântica numérica nativa,
duas fases temporais, 240 Hz: passaram piso, alcance, articulações, vínculos,
âncoras, continuidade e conexões à guarda. Novos critérios para cotovelo,
punho e fio: flexão ativa 10°, variação do punho <0,001°; desvios máximos do
fio 9,53° Low, 6,32° direita/Cross e 1,75° esquerda/Cross. Sondagem opaca a
36 Hz sem nova penetração nos volumes principais do corpo. Motor externo
a 120 Hz, zero erros/avisos. Testes do código numérico já existente não
foram repetidos: essa ponte não mudou; chaves novas conferidas sem expoentes.

**Prévias:** MCP voltou a responder; nova cópia aberta e 98 quadros reais
capturados com câmera fixa, dois GIFs e folha 768×768 conferida. Apoios,
extensão e trajetórias compatíveis com a proposta. Limpeza da vista privada
teve o erro conhecido de listener do plugin; registro removido e timeline
restaurada. Sem reiniciar aplicativo nem alterar arquivos de outras abas.

**Referência:** [Hasuji, Calgary Rakushinkan](https://calgaryrakushinkan.com/hasuji/),
para alinhamento do fio ao caminho do corte e relação ombros/quadril.
Animação original adaptada à criatura; sem simulação física ou cópia de clipes.

**Arquivos/Git:** dois scripts v2, modelo/relatórios/metadados/GIFs/README,
estado atual e vault `docs/` atualizados. Base Git: `e91e3ec`.
Fase 10 permanece aberta. Sem mudança de arquitetura/dependências ou Studio.

**Próximo passo:** feedback artístico de Low/Cross; só depois retomar o spin.
