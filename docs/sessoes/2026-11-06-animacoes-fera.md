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

## r04 — pernas recuadas

Retorno: o usuário recuou as pernas no Blockbench porque nas animações elas entravam nos braços, e
apareceu um pedaço de textura solto. Lido da aba aberta (sem salvar): cubos da coxa +10 em Z, canela e
pé +9; os pivôs tinham ficado para trás. `pernas_recuadas.py` aplicou a edição e moveu os pivôs junto;
`limpar_ilhas.py` tirou o tufo do `pelvis_fur` que ficou boiando; a passada usa as patas de trás
relativas ao tornozelo. Antes: pernas encostando nos braços em 25/25 quadros do walk e 7/10 do run;
agora a menor distância é 3,2 e nenhum encosta. 0 erros e 0 avisos. `loc_ground` (+11, atrás dos pés,
provavelmente arrastado na seleção) ficou no lugar original — confirmar com o usuário.

## r05 — run refeito como galope

Retorno: walk aprovado; run com frente em ritmo de 2 ciclos contra 1 da traseira, balanço demais,
cauda estranha e partes se soltando. Causa medida: quique, tronco e cachecol em 2× a passada, mola
da gordura na própria frequência, tronco transladando 2,8. Novo `pose_galope`: galope rotativo de
0,66 s, tudo travado na fase da passada, só o `body` translada, cauda com elevação fixa. `medir.py`
confere ritmo (1 ciclo/passada), translações e frestas. 0 erros, 0 avisos.
