# F3 — referências e escolhas de movimento

## Fontes consultadas

- F2 aprovada pelo usuário: `../../f2/corrida-v2/criatura-pavao-e2-corrida-v2.bbmodel` e `docs/pesquisa/piloto-02-pavao-f2.md`. Referência principal para a identidade da marcha, braços dobrados, balanço do corpo e resposta atrasada da plumagem. Não é um retarget automático: as proporções e os pivôs da F3 são diferentes.
- Schaller et al., 2009, [The intertarsal joint of the ostrich](https://onlinelibrary.wiley.com/doi/10.1111/j.1469-7580.2009.01083.x). Apoio digitígrado e função do tarso como base da adaptação aviana. O modelo artístico não é uma simulação musculoesquelética.
- Alfred Hutton, 1892, [Old Sword-Play, capítulo II](https://www.thearma.org/pdf/OldSwordPlay.pdf). Referência de transporte de espada junto ao ombro e relação entre guarda, braços e base de apoio. O uso simultâneo de duas penas gigantes é uma adaptação fantástica solicitada pelo usuário.

## Aplicação

Na marcha pacífica, transferência lateral de peso, compressão/elevação do corpo,
contraposição da bacia e do peito, compensação parcial do pescoço/cabeça e atraso
da cauda/cristas/penas. Os braços permanecem dobrados, como na edição manual.

Em combate, corpo mais erguido, base digitígrada preservada e passos mais curtos.
A plumagem dorsal se recolhe para liberar o caminho da lâmina junto ao ombro.
A mão esquerda leva a pena 04 para o ombro; a direita usa a pena 06. A entrada
termina com um único golpe da espada direita no chão. No idle, o ponto de apoio
fica fixo enquanto o peito e os ombros respiram; a outra lâmina acompanha o ombro.

As duas armas são as seis peças originais desses grupos da cauda, sem duplicação,
ocultação, troca de escala ou criação instantânea. As chaves compensam a transformação
do corpo para fazê-las seguir a cauda ou as mãos. Locators marcam os encaixes,
empunhaduras e pontas. Não é necessário um script para visualizar o saque no Blockbench.

A saída tem movimentos próprios: extrair, guardar, soltar e recolher os braços.
Os clipes auxiliares levantam/pousam a espada para iniciar/parar a caminhada.
As conexões estão na fase zero; a mistura em fases arbitrárias será trabalho de
integração quando o usuário pedir comportamento no jogo.

Nenhum arquivo de geometria, textura, animação ou código de mods foi incorporado.
