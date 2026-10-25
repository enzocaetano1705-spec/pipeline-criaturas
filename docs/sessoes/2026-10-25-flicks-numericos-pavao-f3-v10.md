---
tipo: sessao
data: 2026-10-25
fase: 10
ia: codex
status: aguardando-revisao-artistica
---

# F3 — flicks numéricos e compactação do descanso

**Para avaliar:** v10 aberta no Blockbench. Rever penas 04/06 no início de
`combat_enter`/`combat_enter_walk`, asas/costas no início de `combat_walk_start`
e final de `combat_walk_stop`, e desempenho de `combat_idle` com janela visível.

**Retorno:** demais movimentos parecem corretos. Pontos remanescentes:
0–0,18 s no saque parado, cerca de 0,15 s no saque andando, 0,01 s no start,
0,58 s no stop e queda de FPS durante o descanso.

**Causa confirmada:** o motor serializava floats pequenos com `String(number)`.
O parser Molang do aplicativo instalado interpreta `1e-8` como **-8**,
`-8.2e-7` e `-6.5e-7` como **-7**. Esses números aparecem nos instantes
relatados e explicam os saltos de peças aparentemente contínuas no validador.
A validação anterior lia floats com expoente corretamente, ignorando essa
diferença. Relógio comum, isoladamente, não eliminava o defeito.

**Feito:** nova v10, sem sobrescrever fontes manuais/v9. Valores de chaves
gravados como decimais explícitos. 2.831 chaves reparadas nos outros doze
clipes; mesmos valores, tempos, interpolações e metadados. Conversão preventiva
na ponte Python do motor, sem copiar código externo ou alterar dependências.
Dez testes de regressão cobrem precisão, expressões, imutabilidade e não finitos.

`combat_idle` compactada de **34.644 para 5.866 chaves (-83,1%)**. Mesma
duração, pausa de três segundos, ações e marcadores. Redução por canal com
eventos protegidos, conferida também com a tolerância temporal nativa.
Erro local ≤0,01°/0,001 unidade por eixo; maior desvio nos vértices foi
**0,02561 unidade**. Arquivo de 44,95 para 36,12 MB.

**Verificações:** dez testes passaram. Nove clipes passaram nos verificadores
normal e nativo a 240 amostras/s, incluindo fora da grade, contatos/juntas,
encaixes e máscaras. Motor: zero erros/avisos nos quatro clipes relatados,
sem canais ignorados. Os outros doze clipes têm equivalência numérica exata;
geometria, UVs, textura e rig iguais à v9. Comparação de seis capturas reais
em `animacoes-v10/comparacao-nativa.png`. Modelo ativo/caminho confirmados pelo MCP.

**Limitação da medição:** contador de FPS retorna `document_hidden=true` e
`rendering_paused=true`; não se obteve medida válida de FPS. A redução de
carga foi medida por chaves; o ganho real ainda requer janela visível.

**Documentação:** metadados/estado da F3, ficha, plano e retomada atualizados
no vault `docs/`. Fase 10 aberta, sem tag de conclusão. Sem alterações no Studio.
Base anterior: commit `36cb18f`.

**Próximo passo:** avaliar os cinco reparos; depois trabalhar os golpes da F3.
