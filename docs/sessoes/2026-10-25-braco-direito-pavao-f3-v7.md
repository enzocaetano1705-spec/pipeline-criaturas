---
tipo: sessao
data: 2026-10-25
fase: 10
ia: codex
status: aguardando-revisao-artistica
---

# F3 — suavização do braço direito, esquerdo preservado

**Avaliação para o usuário:** conferir a `combat_enter` da v7 no Blockbench.

**Retorno:** esquerdo da v6 está bom. A aceleração conjunta fez o direito
sacar/baixar a espada bruscamente, quase teletransportando. Usuário pediu
suavizá-lo, podendo ser mais lento e chegar junto da espada esquerda.

**Feito:** nova saída em `f3/animacoes-v7/`. Só os canais de `arm_right`,
`forearm_right`, `hand_right` e `tail_fan_06` em `combat_enter` mudaram.
Esquerdo inteiro e todos os demais animadores mantêm exatamente as chaves
da v6. Saque inicial até 0,40 s igual; depois o direito segue tempo próprio,
chegando ao arrasto em 1,65 s junto do apoio esquerdo no ombro. Duração total
continua 1,65 s. Outros doze clipes, geometria, textura, UVs e rig intactos.

**Método:** trajetória direita anterior à aceleração conjunta (v5), com
desaceleração progressiva, adaptada ao torso atual e ao alvo final de
arrasto. Mantidos eixo do cotovelo, relação mão/arma e piso. Chaves não
uniformes do esquerdo conservadas; direito recebe amostras adicionais.

**Problema e correção:** cruzar a grade adicional com as chaves antigas
criava pares quase simultâneos. Filtradas as amostras adicionais a menos de
0,00012 s de uma chave existente, preservando a precedência das originais.
Validação final do motor: zero erros e zero avisos.

**Verificações:** chaves salvas a 240 amostras/s; empunhadura, raízes de
penas, chão, eixos/limites de juntas, floreio completo e conexões passaram.
Erro de matriz do braço esquerdo: zero; canais dos outros animadores e
doze clipes preservados integralmente. Pico angular da espada direita após
0,40 s reduzido de cerca de 1829 para 974 graus/s, sem alterar o floreio da
esquerda. Prévia GIF e folha de seis poses conferidas. V7 aberta no
Blockbench, nome e caminho confirmados via MCP.

**Decisões:** ajuste de animação, sem mudar arquitetura, formato ou
dependências. Nenhuma fonte manual sobrescrita. Roblox Studio não alterado.
Base anterior: commit `3243b0f`. Fase 10 continua aberta.

**Próximo:** avaliação artística do direito; clipes adiados só depois dessa
base aprovada. Estado atual, metadados, ficha e plano atualizados no vault.
