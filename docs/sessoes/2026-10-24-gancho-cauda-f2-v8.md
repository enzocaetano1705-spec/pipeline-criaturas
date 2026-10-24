---
tipo: sessao
data: 2026-10-24
fase: 10
ia: codex
status: pisao-spin-aprovados-gancho-aguarda-avaliacao
---

# F2 v8 — cauda em J, leque externo e chute descendente

**Retorno posterior:** usuário considerou a correção da v8 quase perfeita e pediu
retomar o chute cedo da v7, com animação mais curta. A espera pela descida foi revogada.
Proposta atual em [[2026-10-24-ritmo-cauda-f2-v9]], preservando cauda e leque da v8.

**Pedido ao usuário:** avaliar somente `attack_tail_kick` na nova v8:
`modelos/criatura-pavao/f2/ataque-v8/criatura-pavao-e2-ataque-v8.bbmodel`.
Arquivo aberto em Animate. Prévia em `previa-gancho.gif`, duas vistas a 1×.
Pisão e spin já aprovados, sem necessidade de nova avaliação.

## Retorno e referência

Usuário considerou a v7 quase boa e aprovou a sensação elástica. Pediu três correções:
cauda quase em J com ponta para a direita, leque fora da parte sólida e chute depois
do lançamento, quando o corpo já cai para a frente. Referência é a imagem de cauda
de canguru anexada no chat (24/10); direita significa **trás/+Z na vista lateral**,
não dobrar lateralmente no eixo X. Pesquisa anterior da v5 foi reutilizada.

## Feito

- V8 altera somente `attack_tail_kick`, agora 2,85 s: descida da cauda, gancho baixo,
  ponta levantada para trás, carga, descarga, subida recolhida e chute na descida.
- Apoio na barriga do gancho. A ponta fica elevada em vez de ser o contato de chão.
  Na carga, ponta ~5,24 unidades atrás da raiz e ~2,57 acima do apoio.
- Articulação `tail_hook` sob `tail_2`, neutra nos clipes anteriores. Pivôs de flexão
  ajustados para o lado adequado da dobra; conferido o sentido durante todo o clipe.
  Não abre as fendas que surgiram ao simplesmente inverter todas as rotações da v7.
- Retirada a compensação que virava o leque inteiro para dentro do rabo. Penas seguem
  a extremidade pelas inserções reais. A pena central inferior levanta 15° na soltura
  para liberar o piso; largura lateral do leque permanece constante, sem escalas.
- Velocidade de lançamento preservada próxima à v7: ~+43 Y/−27 Z unidades/s.
  Ápice ~1,259 s; patas permanecem recolhidas até ~1,294 s; impacto ~1,424 s,
  já com velocidade vertical ~−16,17 unidades/s. Pouso em 1,70 s.
- Cabeça, peito e braços acompanham o acento do chute tardio. Recolhimento, absorção
  e passos finais respeitam o comprimento das pernas.
- Rotações a 120 Hz; translação do apoio refinada a 240 Hz contra as rotações realmente
  interpoladas. Isso corrige o pequeno descolamento entre amostras durante a troca do
  canto sólido mais baixo. Não é script de runtime.

## Verificação e preservação

- 63 cubos/53 grupos. Elementos, dimensões, UV e atlas idênticos à v7; nenhuma alteração
  na fonte manual ou nas versões anteriores. Arquivo novo e hashes protegidos.
- Chaves/curvas anteriores mantidas. Pisão e spin comparados a 240 Hz nos cantos dos
  63 cubos. Idle/walk protegidos por igualdade das chaves e articulações neutras,
  sem converter suas curvas não lineares para interpolação linear.
- Arquivo salvo conferido por superfícies opacas: leque contra os seis sólidos caudais,
  penas contra pernas, piso, encaixes, orientação do J, largura do leque, apoio, repouso,
  sentido das dobras, continuidade e momento descendente do chute.
- Contatos existentes de inserção das penas em repouso são descontados; tolerância
  de novo contato opaco 0,05 unidade e de piso/interpolação 0,025. Os relatórios não
  representam uma alegação de interseção matematicamente nula.
- Resultados salvos: novo contato leque/cauda máximo ~0,04342 unidade; penas/pernas
  ~0,00902. Apoio da cauda erra no máximo ~0,01680; encaixes <1,3e-14. Nenhuma dobra
  no sentido que abre a junta; largura do leque sem desvio. Piso visível mínimo
  Y=0,08137 para chão Y=0,08741, dentro da tolerância. Pisão e spin: desvio zero.
- Motor: estrutura sem erros/avisos; ataque sem erro de osso, chave ou junta separada.
  Aviso de retângulo transparente de `fan_5` sob o piso, distinguido pelo teste de alfa.
- Folha inclui cauda isolada para mostrar o J sem oclusão pela plumagem. Prévia 50 fps,
  duração real 2,85 s mais pausa de 0,30 s. Carga e impacto conferidos no Blockbench.

Resultados completos em `medidas-gancho.json`, `aprovados-preservados.json` e diagnósticos
do motor na pasta da v8. Scripts `animar-gancho-cauda-pavao-f2-v8.py` e
`revisar-gancho-cauda-pavao-f2-v8.py`; lote em `gancho.ops.json`.

## Limites e próximo passo

Trajetória/coreografia visual com elasticidade fictícia solicitada; não simula massa
ou gravidade reais, nem define dano, hitbox de ataque ou deslocamento físico no Roblox.
Naturalidade final continua sujeita à avaliação do usuário. Sem alteração de arquitetura,
dependências ou da colisão/runtime; não exportada/adotada no Roblox nesta revisão.

**Próximo:** avaliar a v8 e integrar/exportar o ataque após aprovação. Arquivos alheios
à revisão permanecem fora do commit. Fonte manual preservada.

Commit: `Corrige gancho da cauda e atrasa chute do F2 para a descida` (consultar git log).
