---
tipo: sessao
data: 2026-10-24
fase: 10
ia: codex
status: pisao-spin-aprovados-catapulta-aguarda-avaliacao
---

# F2 v7 — transferência sobre a cauda e catapulta

**Pedido ao usuário:** avaliar somente `attack_tail_kick` na v7, aberta em Animate:
`modelos/criatura-pavao/f2/ataque-v7/criatura-pavao-e2-ataque-v7.bbmodel`.
Prévia em `previa-catapulta.gif`, duas vistas a 1×. Pisão e spin continuam aprovados.

## Retorno incorporado

V6 foi melhor, mas a cauda ainda dobrava em L, com raiz contrária ao quadril, e o corpo
não transferia seu peso para ela. O salto era baixo e a cauda parecia somente um apoio.
Usuário descreveu: recuar sobre os dedos, tirar os pés do chão e carregar o corpo sobre
a cauda, esticá-la com força, catapultar para cima/frente com patas recolhidas e estendê-las
aproveitando a aceleração. A altura do peito é uma linha de força/ataque, não um alvo em Y fixo.

## Feito

- Nova v7 altera somente o ataque de cauda: 2,70 s, execução única, chaves a 120 Hz.
- Dois sólidos caudais divididos em três trechos cada; quatro articulações adicionais:
  63 cubos/52 grupos. Pivôs dorsais distribuem a curvatura sem abrir fendas externas.
  Forma e dimensões em repouso mantidas, mesma textura, faces externas com UV recortado
  proporcionalmente. Esses seis cubos usam UV por face dentro do mesmo formato Bedrock.
- Quadril gira para alinhar a saída da cauda; ligação do torso e peito levam o corpo
  sobre o apoio. Recuo com calcanhares altos, retirada dos pés e carga exclusiva na cauda.
- Carga termina em 0,62 s; descarga até 0,82 s, seguida pela trajetória aérea que herda
  sua velocidade. Subida da bacia após a soltura ~8,16 unidades; avanço no ar ~20,96.
  Fase completamente aérea ~0,83–1,58 s. V6 tinha subida ~1,67 e voo ~0,41 s.
- Patas recolhidas no início do lançamento; extensão começa em 0,79 s, próxima ao pico
  da aceleração da descarga (~0,81 s), e conclui em 0,94 s. Alvo acompanha o quadril/peito
  em movimento, sem limitar o salto à altura original do peito.
- Peito, cabeça, braços e plumagem acompanham a carga/descarga. Leque mantém sua abertura.
  Penas dos tornozelos abrem 18° pela raiz neste clipe para liberar os dedos no recolhimento.
- Pouso com absorção e passos de recuperação. Sem escala dos ossos ou alongamento das pernas.

## Verificação

- Preservação dos aprovados: chaves/curvas originais iguais; comparação dos mesmos pontos
  materiais nos cubos e nas fatias da cauda a 240 Hz. Partição longitudinal e UV verificadas.
- Idle/walk: chaves/curvas iguais e prova da neutralidade das quatro articulações inseridas;
  cadeia reduzida e transformações originais coincidem. Não aproxima curvas não lineares
  pelo leitor linear dos ataques.
- Arquivo salvo conferido a 240 Hz: piso por alfa, penas contra sólidos das pernas, encaixes,
  apoio sólido da cauda, patas livres na carga, abertura do leque, repouso e continuidade.
  Números completos em `medidas-catapulta.json` e `aprovados-preservados.json`.
- Desvio dos aprovados: zero. Dobra máxima entre trechos durante a carga ~23,995°;
  erro de apoio da cauda <0,008 unidade, encaixes <7,2e-15. Piso visível mínimo Y=0,08087
  para chão Y=0,08741 (diferença ~0,00655, tolerância 0,025). Acréscimo de penetração
  pena/perna ~0,01032 unidade; variação máxima de Euler entre chaves ~13,07°.
- Motor: estrutura sem erros/avisos; ataque sem erros ou separação de juntas. Um aviso de
  caixa transparente de `fan_1` abaixo do piso; conferência dos texels opacos passa.
- Conferência nativa do Blockbench nas poses de carga/impacto; GIF com chão e câmera fixa,
  50 fps, duração real da animação e pausa final de 0,30 s.

O centro dos volumes sólidos sem cauda fica próximo ao apoio na carga (distância sagital
~1,4 unidade). É uma aproximação visual com densidade uniforme, não uma massa física medida
nem uma prova de equilíbrio. Parâmetros balísticos são de animação, não do runtime Roblox.
O efeito de mola é a coreografia fictícia solicitada. Naturalidade depende da avaliação do usuário.

## Histórico e reprodução

Scripts `animar-catapulta-pavao-f2-v7.py` e `revisar-catapulta-pavao-f2-v7.py`; lote, hashes,
marcadores, relatórios e prévias na pasta da v7. Fonte é v6, que permanece intacta.
Referências da v5 reutilizadas; não repetida pesquisa. Sem alteração de arquitetura/dependências.

Problemas corrigidos durante a revisão: leque tocava o chão ao fechar a curva; orientação pela
raiz corrigida sem mudar abertura. Pena 3 do tornozelo cruzava dedos ao recolher; correção de
yaw de 12° para 18° libera o contato sem atravessar o quadril. Recuperação foi ajustada para
respeitar o comprimento das pernas durante o avanço. Saídas geradas só foram refeitas com
hash íntegro, e o projeto foi reaberto após cada alteração em disco.

**Próximo:** retorno artístico sobre a v7; integrar/exportar após aprovação. Não adotada no Roblox.
Fonte manual, textura do usuário e alterações não relacionadas permanecem fora do commit.

Commit: `Refaz ataque do F2 com curva distribuída e catapulta pela cauda` (consultar git log).
