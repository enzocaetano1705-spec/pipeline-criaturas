# F2 v5 — impulso do giro e ataque apoiado na cauda

**Pisão aprovado. Giro e ataque com cauda aguardam avaliação artística.**
Abrir `criatura-pavao-e2-ataque-v5.bbmodel`, aba Animate. Avaliar primeiro `attack_spin`.

| Clipe | Duração | Estado |
|---|---:|---|
| `attack_stomp` | 1,25 s | Coreografia aprovada da v4 preservada. |
| `attack_spin` | 1,65 s | Revisão com apoio, impulso, torção do tronco e frenagem. |
| `attack_tail_kick` | 1,85 s | Revisão com cauda articulada, leque aberto e reação do tronco ao golpe. |

## Movimento

### Giro

- Desce o centro do corpo e transfere o peso para a pata esquerda; o peito antecipa a torção.
- A pata direita empurra pelos dedos, libera o chão e recolhe. A esquerda faz o pivô pela ponta.
- Quadril inicia a volta; peito, cabeça, braços e cauda têm trajetórias e tempos diferentes.
  Há variação de inclinação, altura e orientação ao longo da passagem, em lugar de congelar a pose.
- As seis penas longas dos cotovelos e as sete da cauda ficam horizontais durante o corte.
  As penas curtas junto aos ombros mantêm sua função e acompanham os braços.
- Na saída, a pata livre retoma o apoio, o corpo absorve a frenagem e o peito acomoda depois.

**Pena perdida localizada:** os nomes não são simétricos. `wing_right_feather_7` é longa
e corresponde à esquerda `_8`; a seleção da v4 a deixava no grupo do braço.
A v5 identifica a família pelo comprimento da peça e corrige a ligação ao antebraço.

### Ataque com cauda

- Recua os pés, carrega o tronco e planta a parte sólida da cauda antes de levantar as patas.
- `tail_mid` e `tail_base` agora articulam na união real entre os dois segmentos.
  A porção proximal desce; a distal faz a curva de apoio e continua apontando para trás.
- O leque inclina como conjunto, conservando os ângulos entre suas penas. Não se comprimem
  as sete lâminas numa orientação única. A plumagem não é usada como pé.
- Pernas recolhem sob o ventre; tronco e braços preparam, as patas avançam juntas e há reação
  da bacia, peito e pescoço na extensão. As patas recolhem e voltam ao chão antes de liberar a cauda.
- O cálculo de avanço acompanha uma junta material fixa. Usar o vértice momentaneamente mais
  baixo para determinar também o avanço trocava de ponto e causava um salto da bacia na preparação.

## Rig e proteção do aprovado

59 cubos, uma textura 256×256, **46 grupos**. Sem alteração de geometria, UV ou proporções.
Foram acrescentados `chest`, `tail_2` e `elbow_blade_right_7`; demais articulações vêm da v4.
Peito e cauda distal ficam neutros no pisão, idle e walk. Chaves/curvas originais conservadas.

A pena direita 7 passou ao antebraço. Somente no pisão, chaves auxiliares de compensação
conservam o movimento que o usuário aprovou. Comparação de todos os cantos dos 59 cubos
contra a v4 a 240 Hz: desvio máximo **0,000173 unidade**, apenas nessa pena; demais peças iguais.
Idle/walk mantêm as chaves, agora com o vínculo corrigido da pena direita.
Essa preservação não significa conservar a falha do vínculo nos dois ataques revisados.

Fonte v4 e modelo manual preservados. Não adotado nas exportações Roblox nesta avaliação.

## Conferência

- Chaves assadas a 120 Hz, leitura independente a 240 Hz. Início/fim neutros por matriz,
  sem escala animada, fórmulas ou IK necessária no jogo.
- Continuidade de Euler e do deslocamento da bacia; nenhum salto de 180° ou troca de ponto de apoio.
- Pisão comparado geometricamente com o clipe aprovado, além de conferir suas chaves originais.
- Superfície opaca conferida contra o chão, incluindo os cantos dos texels; penas dos tornozelos
  amostradas contra pernas/pés/quadril e comparadas com o contato já existente em repouso.
- Raízes sem separação numérica; apoio da pata esquerda durante o giro e apoio sólido da cauda
  entre 0,40 e 1,10 s. Leque conserva a abertura; 13 planos cortantes horizontais na fase ativa.
- Motor externo: estrutura sem erros/avisos; ataques novos sem erro ou separação de juntas.
  Resta um aviso de chão para o retângulo transparente de `fan_5` no ataque com cauda.
  O recorte opaco passa pela conferência de chão. Pisão e walk conservam seus avisos anteriores.
- `medidas-superficies.json`, `continuidade.json`, `pisao-preservado.json` e `validacao-*.json`
  registram a medição do arquivo final. São verificações técnicas; a naturalidade é avaliação artística.

GIFs individuais e conjunto a **1×/50 fps**, vistas 3/4 e perfil, com pausa de 0,30 s entre golpes.
O GIF conjunto corta entre dois clipes independentes. `poses-combate.png` tem 768×720.
Marcadores em `animacoes.json` são sugestões para integração posterior de gameplay.

## Referências consultadas

- [ONEIROMACHIA — spin attack, frames](https://oneiromachia.artstation.com/projects/PX8q0L):
  quadros do autor vistos no navegador; orientação do olhar, giro do peito e continuidade dos braços.
  É um ataque humano aéreo estilizado; usado como referência de encadeamento, sem copiar poses
  ou supor equivalência anatômica com a ave. Nenhum asset da referência foi copiado ao projeto.
- [Wayne Gilbert / Animation Mentor — Body Mechanics](https://www.animationmentor.com/blog/animation-tips-tricks-what-makes-or-breaks-a-good-body-mechanics-shot/):
  causa do movimento, transferência de peso e relação entre partes que lideram e seguem.
- [Warburton et al., 2013 — musculatura e combate em cangurus](https://onlinelibrary.wiley.com/doi/10.1111/bij.12090):
  apoio na cauda e ação conjunta de membros anteriores/posteriores. A anatomia da criatura
  continua sendo a do modelo do usuário. Reutilizado também o estudo de apoio já registrado
  em `docs/sessoes/2026-10-23-direcao-combate-f2.md`.

## Reproduzir

```powershell
uv run python scripts/animar-combate-pavao-f2-v5.py --medir
uv run python scripts/revisar-combate-pavao-f2-v5.py --poses
uv run python scripts/animar-combate-pavao-f2-v5.py
uv run python scripts/revisar-combate-pavao-f2-v5.py
```

`--refazer` no gerador só sobrescreve a própria proposta se os hashes de fonte e saída ainda
coincidirem. Edição manual posterior exige uma versão nova. `--sem-gifs` no revisor omite os GIFs.
