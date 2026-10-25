# F3 — base de combate v3

Arquivo: `criatura-pavao-e3-combate-v3.bbmodel`. Fonte: snapshot da aba ativa
da v2c em `origem-revisada.bbmodel`. Mesmos 93 blocos, 41 grupos, UVs e textura.
Esta revisão trata apenas dos três clipes abaixo e aguarda avaliação artística.

| Clipe | Duração | Revisão |
|---|---:|---|
| `combat_ready` | 2,4 s, loop | Guarda relaxada, pontas para cima e ligeiramente para fora |
| `combat_walk` | 1,8 s, loop | Uma espada no ombro; a outra arrasta, com cotovelo atrás e mão junto ao quadril |
| `combat_enter` | 2,1 s | Saque aprovado, guarda estável, elevação dos braços, volta completa e retorno à guarda |

## Wings e braços

A rotação dorsal de 45° estava sendo aplicada num pivô à frente da base das
penas e deslocava suas raízes. As chaves agora compensam esse deslocamento:
cada leque gira sobre sua base real, acompanhando o torso ou o cotovelo.
Não foi necessário alterar a geometria nem os pivôs globais do rig.

No arrasto, o ombro fica relaxado, o cotovelo recua e a mão permanece próxima
do quadril. O rolamento da espada permite alinhar a mão ao antebraço; a dobra
longitudinal do punho fica abaixo de 16° durante a marcha. A inclinação da
lâmina acompanha a altura da mão para conservar o contato da ponta com o piso.
Cotovelos mantêm um eixo de flexão/extensão, sem rotação independente para trás.

## Saque e floreio

- 0–0,50 s: trajetória do saque anterior preservada; apenas as wings corrigidas.
- 0,50–0,72 s: acomoda as duas armas na nova guarda.
- 0,72–0,90 s: guarda estabilizada, antes de começar o floreio.
- 0,90–1,15 s: eleva os braços e abre ligeiramente as lâminas.
- 1,15–1,68 s: uma volta completa de 360° por espada.
- 1,68–2,10 s: baixa os braços e retorna à mesma pose da `combat_ready`.

O usuário autorizou inclinar as lâminas para liberar o piso. Cada uma mantém
30° para fora durante a volta; sua projeção lateral descreve um círculo
completo. Não é o oito horizontal da versão anterior. As espadas mantêm o
tamanho; os pés ficam apoiados. A menor folga da lâmina ao chão é de cerca de
0,61 unidade no arquivo salvo. Peito, pescoço, bacia e plumagem acompanham o gesto.

## Escopo adiado

Idle/walk aprovados e os outros oito clipes de combate conservam seus canais
e tempos da fonte. **Start/stop, enter andando, camadas, descanso e saída ainda
são da v2 e não foram adaptados à nova guarda.** Precisam ser derivados desta
base depois da avaliação do usuário; não encadear automaticamente as versões.

## Conferência e reprodução

```powershell
uv run python scripts/animar-combate-pavao-f3-v3.py --animar --validar --previas --folha
uv run pytest -q ferramenta/testes/test_animar.py
```

Somente o motor externo grava o `.bbmodel`. Saída protegida por hash contra
sobrescrita de edições manuais. Análise das chaves salvas a 240 amostras/s:
empunhadura, raízes das penas, sola/ponta no piso, cotovelos, punhos, volta
completa, continuidade de orientação, loops e conexões idle → saque → guarda.
Todos passaram. Dez testes de animação passaram. Validador externo: zero erros
estruturais, 194 avisos de sobreposição/simetria já existentes; zero erros e
zero avisos de animação nos três clipes revistos.

Detalhes em `validacao.json`, `validacao-motor-estrutura.json` e
`validacao-motor-animacoes.json`; prévias nos três GIFs e em `poses.png`.
Sem integração ou alterações no Roblox Studio nesta revisão.
