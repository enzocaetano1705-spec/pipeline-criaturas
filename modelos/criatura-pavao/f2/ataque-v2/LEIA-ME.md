# F2 — ataques v2: pernas e bico

**Retorno artístico posterior:** chutes rejeitados por leitura humanizada e pouco anatômica;
bicotada aproveitável, conjunto ainda sem vida. A alta frequência deixou de ser requisito.
Ver `docs/sessoes/2026-10-23-direcao-combate-f2.md` para a proposta de repertório em discussão.
Esta versão permanece como estudo e não está aprovada para adoção/exportação.

**Avaliação no Blockbench:** abrir `criatura-pavao-e2-ataque-v2.bbmodel`, aba Animate,
e tocar **attack_chain_preview**. O GIF tem a mesma sequência em velocidade normal (1×),
sem pausa adicional entre repetições. Os ataques individuais executam uma vez.

| Clipe | Duração | Movimento |
|---|---:|---|
| `attack_physical` | 0,40 s | Chute esquerdo à frente, convergindo para o centro e descendo sobre o alvo. |
| `attack_physical_right` | 0,40 s | Chute direito com o mesmo percurso, respeitando a assimetria original dos pés. |
| `attack_peck` | 0,30 s | Bicotada com avanço do corpo/pescoço e retirada curta. |
| `attack_chain_preview` | 1,10 s | Esquerda → bico → direita; loop para avaliação, três contatos propostos. |

## Escolha do movimento

O usuário rejeitou a tenaz dos braços da v1: alcance curto, altura inadequada para alvos pequenos,
preparação/recuperação longas e penas compridas ficando para trás. Nesta proposta os braços ficam
na guarda, as pernas são as armas principais e o bico oferece uma alternativa mais alta.

O chute sai com pequena transferência de peso, estende o pé pelo centro e faz uma descida antes
de recolher a perna. A retirada tem altura suficiente para as penas das pernas não cruzarem o chão.
O pé de apoio fica plantado e o calcanhar ergue durante a extensão. A cauda compensa a inclinação.
Não há escala animada nem alongamento de membros; a IK é assada nas rotações dos ossos.

Cada chute tem apenas 72 ms até o fim do primeiro recolhimento e chega à extensão em 144 ms.
A bicotada chega à extensão em 114 ms. Todos começam e terminam na **mesma guarda de combate**,
sem retornar à pose ereta do idle a cada golpe. A sequência demonstra cerca de 2,73 golpes/s;
essa cadência é uma escolha artística para o jogo, não uma medida biológica nem um DPS implementado.
Os clipes foram criados para essas durações, sem acelerar a v1.

Referências consultadas: uso defensivo das pernas e equilíbrio de uma ave corredora no
[San Diego Zoo](https://animals.sandiegozoo.org/animals/ostrich); distinção entre fases da bicotada
em [pombos, estudo de controle do movimento](https://pubmed.ncbi.nlm.nih.gov/27885041/).
São referências de mecanismo; a coreografia e as proporções são próprias do F2. A anatomia
especializada de outras aves não foi adicionada ao modelo.

## Penas do cotovelo

Na **cópia v2**, `wing_left/right` são filhos de `forearm_left/right`, com o pivô no cotovelo.
Assim herdam ombro e cotovelo diretamente. Foi removida a compensação inversa da v1 que
neutralizava o braço e deixava as penas para trás. Só há pequena flexão secundária local.
A posição das peças em repouso permanece igual, inclusive UVs, textura e recorte de alfa.

## Alcance e limites

O ensaio usa interseção real entre cubos orientados dos dedos/bico e caixas de alvo, a 240 Hz.
Coordenadas em unidades Blockbench, frente em −Z, piso em Y=0,08741:

| Alvo de ensaio | Caixa (X; Y; Z) | Resultado |
|---|---|---|
| Pequeno no chão | ±1,5; piso…piso+3; −16…−10 | Ambos os chutes encontram o alvo no arco baixo, a partir de 0,200 s. |
| Médio | ±3; piso…piso+14; −22…−16 | Ambos os chutes encontram o alvo na extensão, a partir de ~0,12 s. |
| Grande | ±4; piso…piso+48; −24…−20 | Bicotada encontra a superfície frontal na faixa da cabeça. |

Isso verifica cobertura de alturas diferentes **dentro do alcance**. Tamanho, distância, altura
do terreno e aproximação ainda precisam orientar a escolha do golpe no gameplay. Uma única pose
fixa não garante contato com qualquer caixa em qualquer posição. Não há seleção automática de
variante, movimentação do personagem, dano ou transição do walk implementados nesta proposta.
Os marcadores em `animacoes.json` são sugestões; o chute também acerta depois do instante de
extensão máxima. A integração deverá usar a janela/varredura do golpe e evitar dano repetido no alvo.

## Preservação e verificação

- Fonte manual sem as sete garras: 59 cubos, 27 grupos e uma textura 256×256. SHA256 registrado
  em `proveniencia.json`; a fonte não foi sobrescrita. V1 guardada como histórico da avaliação.
- Cubos, textura, UVs e geometria em repouso conferidos contra a fonte. Nenhum membro novo.
- Chaves/curvas originais de idle/walk preservadas; só listas vazias normalizadas pelo codec.
  As penas passam a herdar o antebraço também nesses clipes; corpo, cabeça e pernas mantêm o rig.
- Motor externo: estrutura e quatro ataques com **zero erros e zero avisos** (amostragem 120 Hz,
  afundamento tolerado 0,05 e separação de junta 0,75 unidade).
- Chaves salvas medidas a 240 Hz: apoio com desvio máximo **0,008143 unidade**; mínimo global
  **Y=0,080098**, diferença de 0,007312 para o piso devido à interpolação entre chaves.
- Pé livre: desvio máximo de 0,261202 unidade da trajetória analítica entre chaves a 120 Hz;
  menor que um texel/unidade do modelo. É medido separadamente do pé de apoio.
- Pivô das penas coincide com o cotovelo durante todos os clipes; início/fim iguais e guarda comum.
- Idle/walk: zero erros e um aviso no dedo traseiro do pé esquerdo do walk (0,34 unidade sob o piso).
  O mesmo aviso foi reproduzido na fonte sem ataque: não foi introduzido pela nova hierarquia.
  Não foi alterado o walk já aprovado para corrigir esse aviso preexistente.

## Arquivos e reprodução

`ataque.ops.json` contém as edições em lote; `proveniencia.json` protege propostas editadas à mão.
`medidas-ataque.json` contém alcance, apoios, chão e contatos com os alvos; `validacao-*.json`
contém os resultados do motor. `poses-ataque.png` tem seis poses e `previa-ataque.gif` duas vistas.

```powershell
uv run python scripts/animar-ataque-pavao-f2-v2.py
uv run python scripts/revisar-ataque-pavao-f2-v2.py
```

O gerador recusa uma saída existente; `--refazer` só funciona se fonte e saída ainda coincidirem
com os hashes registrados. Uma proposta editada manualmente deve gerar outra versão.

**Estado após avaliação:** chutes rejeitados, bicotada aproveitável; repertório novo em discussão
na nota de direção do combate. A fonte canônica e as exportações do Roblox ainda não adotaram estes
ataques; a remoção das garras será propagada junto da versão que vier a ser aprovada.
