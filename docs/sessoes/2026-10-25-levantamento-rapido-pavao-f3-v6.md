---
tipo: sessao
data: 2026-10-25
fase: 10
ia: codex
status: aguardando-revisao-artistica
---

# F3 — saque, levantamento rápido, floreio e ombro

**Avaliação para o usuário:** conferir o ritmo da `combat_enter` na v6.

**Retorno:** subida contínua da v5 ainda demorada. Usuário pediu saque →
braço rápido para cima → floreio → apoio no ombro. Respiração da guarda mantida.

**Feito:** fonte v5 preservada; nova saída em `f3/animacoes-v6/`. Somente
`combat_enter` alterada. Saque até 0,40 s igual; subida passa de 0,75 para
0,30 s, terminando em 0,70 s. Giro ocorre em 0,70–1,23 s; apoio no ombro em
1,25–1,65 s. Giro e recuperação mantêm poses e velocidade, antecipados 0,45 s.
Total passa de 2,10 para 1,65 s. Outros doze clipes preservados integralmente.

**Continuidade:** curva alvo de remapeamento com velocidade 1 e aceleração
zero nas emendas; acelera o miolo da subida. Geometria, textura, UVs e rig
mantidos. Mesmos lados: esquerdo da criatura floreia/apoia; direito arrasta.

**Problema e correção:** reamostrar a subida acelerada numa grade uniforme
descartava poses intermediárias e prejudicava o contato da outra espada com
o piso. Correção: conservar todos os valores/chaves da fonte e remapear seus
tempos. Interpolação mantém exatamente a trajetória original.

**Verificações:** chaves salvas a 240 amostras/s; doze clipes preservados,
trajetória original, empunhadura, penas, apoios, limites/eixos das juntas,
giro e conexões. Erro de matriz do caminho abaixo de 0,000000000001;
aproximação temporal da curva suave inferior a 0,0001 s. Floreio e final
iguais aos originais com antecipação. Contato da espada com erro inferior a
0,000018 unidade. Motor de animação: zero erros e zero avisos.
Validador comum agora consulta a duração real do saque para conferir a conexão.
V6 aberta no Blockbench, confirmada pelo título da janela. O endpoint MCP
ficou indisponível na conferência final; prévia e verificações feitas localmente.

**Decisões:** ajuste local de tempo, sem mudar arquitetura, formato ou
dependências. Nenhum arquivo manual sobrescrito. Sem Roblox Studio.
Base anterior: commit `5494731`. Fase 10 continua aberta.

**Próximo:** avaliação do ritmo; depois derivar os clipes adiados da base.
