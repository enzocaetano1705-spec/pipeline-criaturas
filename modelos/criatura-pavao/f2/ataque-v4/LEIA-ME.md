# F2 — três ataques v4, para avaliação

Abrir **criatura-pavao-e2-ataque-v4.bbmodel** no Blockbench, aba **Animate**.
As três animações são propostas artísticas; ainda precisam da avaliação do usuário.

| Clipe | Duração | Movimento |
|---|---:|---|
| `attack_stomp` | 1,25 s | Passo de apoio para trás; uma pata avança recolhida e desce com peso. Tronco, cabeça, mãos e cauda acompanham a transferência. |
| `attack_spin` | 1,35 s | Agacha, põe penas longas dos cotovelos e leque da cauda na horizontal, gira 360° rapidamente e recupera a pose. |
| `attack_tail_kick` | 1,55 s | Recua, planta a parte sólida da cauda, recolhe e projeta as duas patas juntas à frente, depois recupera os apoios. |

Os GIFs individuais e `previa-combate.gif` usam as **chaves do arquivo salvo**, a **1×/50 fps**,
em 3/4 e perfil com câmera fixa por golpe. Há pausa de 0,30 s na pose final entre repetições.
O GIF conjunto corta de um clipe para outro; não representa uma sequência de combate encadeada.
`poses-combate.png` é uma folha de 768×690 para comparação rápida.

## Correções de fixação

- **Cauda:** pivô da peça sólida na união real com o quadril, na face frontal de `tail_mid`.
  O pivô antigo estava no meio do segmento e fazia a base sair do corpo ao girar.
- **Cotovelos:** penas longas `_1`, `_8` e `_9` seguem o antebraço por `elbow_blades_*`.
  As penas curtas `_2`, `_3` e `_7` continuam seguindo o braço, na fixação original.
- **Tornozelos:** seis penas seguem a canela, com pivô próprio na raiz real de cada lâmina.
  Correção máxima de 12° pela raiz libera o tornozelo; a pena inteira permanece rígida.
  O grupo único no joelho usado na v3 foi abandonado nesta proposta.
- **Leque:** sete pivôs na aresta de fixação de cada pena. No giro, as lâminas ficam horizontais;
  durante o apoio da cauda elas se erguem para liberar o chão. Não se usa a plumagem como pé.
- **Giro:** `combat_pivot` guarda a volta completa com Y contínuo até 360°.
  O começo e o fim têm a mesma transformação espacial, sem giro inverso no último quadro.

São **59 cubos, 43 grupos**, mesma geometria/UV/textura e pose de repouso da fonte manual.
Os novos grupos são articulações, sem peças visuais adicionais. Chaves e curvas originais de
idle/walk foram preservadas; as correções de pivô e parentesco também afetam como esses clipes
movem a cauda e a plumagem. Não significa reprodução visual idêntica ao rig defeituoso.

## Verificação do arquivo final

Medição das chaves salvas a **240 Hz**, em unidades Blockbench:

| Medida | Pisão | Giro | Apoio na cauda |
|---|---:|---:|---:|
| Mínimo Y da superfície visível; piso = 0,087410 | 0,084836 | 0,086188 | 0,082180 |
| Maior desvio do pé em relação à trajetória calculada | 0,023119 | 0,026321 | 0,037274 |
| Acréscimo máximo de penetração pena/perna nos texels opacos amostrados | 0,006365 | 0,001574 | 0,024381 |
| Maior variação de Euler por chave | 5,081° | 14,387° | 8,295° |

- Raízes das penas e união da cauda: erro de fixação menor que **2×10⁻¹⁴**.
- Pisão: erro máximo de piso nas patas de apoio **0,001374**; uma pata golpeia e a outra sustenta.
- Giro ativo: cerca de **360° em 0,30 s**; normais dos 13 planos cortantes alinhadas ao eixo Y
  durante a fase ativa, ou seja, superfícies paralelas ao solo.
- Ataque duplo: ponto da cauda sólida plantado em Y=0,087410/Z=25 entre **0,34 e 0,98 s**;
  desvio máximo **0,000949**. Solas acima de Y=13,10 na fase de impacto.
- Todos os clipes começam/terminam na transformação de repouso; sem escala animada,
  fórmulas Molang ou controladores de IK necessários na reprodução.
- Motor externo: estrutura sem erros/avisos; animações sem erros, **um aviso de chão no pisão**.
  Esse validador usa o retângulo inteiro das penas: o canto transparente da pena esquerda 3
  chega a Y=−0,420446. A conferência dos cantos dos texels opacos confirma que a superfície
  visível fica acima do piso, dentro dos pequenos desvios de interpolação listados na tabela.
- Idle/walk: nenhuma junta solta ou erro novo no motor. Mantém o aviso preexistente do dedo
  traseiro esquerdo do walk (0,34 unidade abaixo do piso a 0,267 s); também conferido no viewport.
- Penetração foi comparada com o contato já presente em repouso, por amostras dos texels opacos
  das penas contra volumes orientados das pernas, pés e quadril. Não é um solver de tecido
  ou garantia de ausência de contato entre quaisquer duas superfícies do modelo.
- Conferidos também no viewport nativo: impacto do pisão, lâminas horizontais no giro e
  extensão das patas com apoio da cauda. O arquivo aberto é a v4, não a aba antiga da v3.

Os marcadores em `animacoes.json` são propostas para futura integração, não eventos de dano
já publicados. Dano, varredura de área, escolha de alvos e deslocamento pelo cenário são gameplay.
Fonte manual e exportações Roblox atuais continuam protegidas; a v4 ainda não foi adotada.

## Reprodução

```powershell
uv run python scripts/animar-combate-pavao-f2-v4.py --medir
uv run python scripts/revisar-combate-pavao-f2-v4.py --poses
uv run python scripts/animar-combate-pavao-f2-v4.py
uv run python scripts/revisar-combate-pavao-f2-v4.py
```

O gerador recusa sobrescrever a proposta existente. `--refazer` só permite regenerar a própria
saída se fonte e saída ainda corresponderem aos hashes de `proveniencia.json`. Qualquer edição
manual posterior exige nova versão. `--so-previas` no revisor refaz somente os GIFs.

Fonte SHA256: `4ee150999774ac5f9b8036487040904ee95243d58e9efc002534654a398d3bad`.
Sem mudança de formato, dependência ou arquitetura do pipeline. Histórico v1/v2/v3 preservado.
