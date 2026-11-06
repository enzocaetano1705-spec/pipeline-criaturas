---
tipo: sessao
data: 2026-11-06
fase: animação da preguiça rogue (locomoção)
ia: claude-code
modelo: claude-opus-5-5
status: locomoção r03 entregue para avaliação
---

# Preguiça rogue — locomoção (idle, walk, run e transições)

**Pergunta para o usuário:** a locomoção da `animacoes-v1/r03` passa a sensação de preguiça-gigante
pesada e veloz? Ver os GIFs e abrir o modelo no Blockbench.

**Conceito do usuário:** anda e corre como preguiça-gigante muito veloz, quadrúpede nos nós das mãos
com as garras dobradas para dentro, corpo todo balançando como se fosse pesado e com gordura.
Arquétipo rogue, matador de chefes que lida bem com ondas. Habilidade 1 decidida: uma garra
arremessada ricocheteia marcando os inimigos, volta para a mão e a preguiça teleporta dando um golpe
curto em cada marcado. Habilidade 2: sequência focada no chefe. Sem vídeos de referência.

**Feito:** ossos das garras (`scripts/fera-animacao/garras.py`), pivôs de joelho/tornozelo alinhados
aos cubos editados pelo usuário (`pivos_pernas.py`), motor de pose com IK de dois ossos, garras
dobrando e molas para a gordura (`pose.py`, `clips.py`) e gerador com prévias (`gerar.py`). Clipes
idle 4,0 s, walk 1,6 s, run 0,62 s, run_start 0,5 s, run_stop 0,7 s; 8.276 chaves a 30/s.

**Conferência:** validação de animação 0 erros e 0 avisos (r01 tinha cauda afundando — sinal da
rotação trocado — e pé soltando da canela por pivô fora do cubo; r02/r03 corrigiram). Juntas
iguais às do motor (`bbmodel_sample_pose`, diferença ≤ 0,1). Roblox não anima escala de osso: o peso
vem de molas no tronco/pescoço, quique e ondas na cauda e no cachecol.

**Próximo passo:** avaliação do usuário; depois postura de combate, ataque básico e habilidades.
