---
tipo: sessao
data: 2026-10-25
fase: 10
ia: codex
status: aguardando-revisao-artistica
---

# F3 — peso da respiração e continuidade do saque

**Avaliação para o usuário:** conferir respiração da `combat_ready` e fluidez
do saque até estender o braço. Floreio, recuperação e final aprovados preservados.

**Retorno:** usuário considerou a v4 excelente. Pediu respiração mais pesada
com mais movimento corporal e eliminar a estabilização percebida por volta de
0,35–0,80 s: deve sacar e continuar até a extensão do braço, perto de 1,17 s.
Restante da animação aprovado. Mesmos lados da marcha: esquerdo no ombro e
direito no arrasto, conforme confirmação da sessão anterior.

**Feito:** fonte v4 preservada; saída nova em `f3/animacoes-v5/`. Só a guarda
e o trecho 0,40–1,15 s do braço do ombro no saque foram revistos. Demais onze
clipes, geometria, UVs, textura e hierarquia mantidos. Conferência da aba ativa:
mesma geometria e valores; diferenças do codec apenas no arredondamento de
tempos de chaves, até 0,00000333 s. Usada a fonte v4 já salva/versionada.

**Respiração:** mesmo ciclo de 2,4 s. Oscilação vertical do corpo passa de
0,36 para 1 unidade; inclinação do peito, de 1,8 para 5,6°. Cintura/pescoço
acompanham, cabeça parcialmente estabilizada e cauda/penas com leve atraso.
Patas, preensão e ponta da espada conservam apoio. Não altera escala de blocos.

**Fluidez:** removidos o retorno à guarda baixa e a espera antes da elevação.
Arco da mão com guia em 0,56 s e velocidade não nula; posição em Hermite e
orientações em Bézier esférica, com derivadas compatíveis nas junções.
O ombro orienta o gesto, cotovelo mantém a dobradiça e as penas seguem suas raízes.
O outro braço conserva o gesto de arrasto. Até 0,40 s e depois de 1,15 s,
as poses do saque são preservadas. Floreio/final e duração de 2,1 s mantidos.

**Verificações:** chaves salvas a 240 amostras/s: preservação dos onze clipes,
apoios, empunhadura, raízes das wings, juntas, loop/conexões, velocidade positiva
no novo arco e igualdade das poses após a extensão. Relatórios e prévias na v5.
Solucionador local do contato da espada usa busca salvaguardada/cache em vez
de repetir 22 bisseções de IK por quadro; conserva a precisão do apoio.
Validador comum aceita o limite do trecho inicial preservado, padrão ainda 0,50 s.
Todas as conferências passaram; motor com zero erros e zero avisos nos dois
clipes. Nova mão mantém velocidade acima de 5,24 unidades/s no trecho conferido;
nenhum retorno vertical. Poses após 1,15 s com erro de matriz abaixo de 0,000004.
Respiração medida no arquivo salvo: 1 unidade vertical e 5,6° de peito.
V5 aberta e conferida no Blockbench via MCP; `combat_ready` deixada em reprodução.

**Decisões:** ajuste local de animações, sem mudar arquitetura, dependências,
formato ou geometria. Fonte/edições manuais preservadas. Sem Roblox Studio.
Base anterior: commit `fdf3aa6`. Fase 10 continua aberta.

**Próximo:** avaliação dos dois ajustes; depois derivar os clipes adiados
da base de combate aprovada. Não considerar variantes, camadas, descanso e
saída automaticamente adaptados.
