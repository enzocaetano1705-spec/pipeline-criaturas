# F3 — guarda parada com a postura da marcha

Arquivo: `criatura-pavao-e3-combate-v4.bbmodel`.
Fonte: `../animacoes-v3/criatura-pavao-e3-combate-v3.bbmodel`, preservada.

O usuário aprovou integralmente `combat_walk` e a qualidade do saque/floreio
da v3. Pediu transformar a pose da marcha na guarda parada e separar os braços
depois de retirar as duas penas. Esta revisão substitui apenas `combat_ready`
e `combat_enter`. Os outros onze clipes, incluindo `combat_walk`, são preservados.

## Lados confirmados

Mantêm-se os mesmos braços da marcha aprovada: **esquerdo da criatura no ombro**,
**direito da criatura no arrasto**. O usuário confirmou essa correspondência,
porque a descrição inicial usava os lados vistos de frente. Só a espada que
termina no ombro faz o floreio.

## Clipes

| Clipe | Duração | Comportamento |
|---|---:|---|
| `combat_ready` | 2,4 s, loop | Mesma postura da marcha, parada; respiração e plumagem discretas |
| `combat_enter` | 2,1 s | Saque em conjunto; espada do chão segue para o arrasto, a do ombro faz uma volta e repousa |
| `combat_walk` | 1,8 s, loop | Aprovada e copiada integralmente da v3 |

A pose inicial da guarda coincide exatamente com o quadro zero da marcha.
Conserva a inclinação, a base escalonada das patas e a posição das duas armas.
Durante a respiração, a ponta da espada do chão continua apoiada. As wings
mantêm a compensação sobre sua base real.

O saque até 0,50 s permanece igual. Depois disso os braços se separam:

- A espada do chão chega à postura de arrasto em 0,90 s e permanece nela.
- A espada do ombro conserva o floreio aprovado de 360° entre 1,15 e 1,68 s,
  com 30° de inclinação para fora, sem salto.
- A partir de 1,70 s, essa espada desce para o ombro enquanto o corpo assenta
  na base da marcha. Termina em 2,10 s na mesma pose da guarda parada.

As patas acomodam a base com dois passos curtos; não deslizam até o novo lugar.
Os clipes adiados de transição, camadas, descanso e saída continuam da revisão
anterior e ainda precisam ser adaptados a esta base.

## Conferência

```powershell
uv run python scripts/animar-combate-pavao-f3-v4.py --animar --validar --previas --folha
```

Modelo e chaves gravados pelo motor externo, em arquivo novo e protegido por
hash. A conferência das chaves salvas verifica preservação dos onze clipes,
geometria/UV/atlas/rig, guarda igual à marcha, contato da espada de descanso,
floreio completo apenas no braço do ombro, preensão, raízes das wings, punhos,
cotovelos, apoio das patas, continuidade e conexões idle → enter → ready.

Detalhes em `validacao.json`; clipes revistos também conferidos pelo validador
de animação do motor. Avaliação artística do novo final e da guarda pendente.
Prévia nos dois GIFs e na folha `poses.png`. Sem alterações no Roblox Studio.
