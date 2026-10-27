# F3 — corridas pacífica e de combate

Modelo: `criatura-pavao-e3-corrida-v1.bbmodel`.
Fonte: `../animacoes-v10/criatura-pavao-e3-combate-v10.bbmodel`.

| Clipe | Duração | Função |
|---|---:|---|
| `run` | 0,84 s | Corrida aviana baixa, em loop |
| `run_start` | 0,60 s | Marcha pacífica → corrida |
| `run_stop` | 0,66 s | Corrida → marcha pacífica |
| `combat_run` | 0,96 s | Corrida armada pesada, em loop |
| `combat_run_start` | 0,66 s | Marcha armada → corrida armada |
| `combat_run_stop` | 0,72 s | Corrida armada → marcha armada |

## Movimento

A corrida aprovada da F2 e as marchas da F3 orientam a construção. `run`
inclina o tronco, recolhe os braços e usa a cauda como contrapeso. `combat_run`
conserva a assinatura aprovada: braço esquerdo da criatura com a espada no
ombro, braço direito com a outra lâmina em arrasto. O peso muda a postura e
a cadência; não se trata de acelerar a marcha.

Há compressão/impulso do corpo, fase aérea breve, contraposição de bacia/peito,
compensação parcial da cabeça e resposta atrasada das cristas/penas/cauda.
As pernas usam IK; o pé rola sobre a ponta no impulso. As bases das penas
acompanham as articulações. As mesmas penas 04/06 continuam na cauda ou nas
mãos, conforme a postura, sem duplicação.

19 clipes no arquivo: os treze anteriores, geometria, textura, UVs e rig são
preservados. `root` permanece neutro; o balanço acontece em `body`.

## Transições

Entradas e saídas usam uma curva de aceleração suave e integram a frequência
da passada. Não reiniciam a fase quando a velocidade muda. `animacoes.json`
registra, para cada transição, clipe/tempo de origem e clipe/fase/tempo de
destino. Respeitar esses tempos ao reproduzir a sequência.

Para comandos interrompidos, a futura lógica de animação precisará conservar
a fase e misturar a pose atual com o novo destino. Esta entrega prepara os
clipes e seus canais; não implementa esse controle no Roblox. A parada leva à
marcha correspondente; as transições já existentes cuidam dos demais estados.

## Conferência e prévias

```powershell
uv run python scripts/animar-corrida-pavao-f3.py --gerar --validar
uv run python scripts/animar-corrida-pavao-f3.py --nativo
```

`validacao-corrida.json` confere o arquivo salvo com interpolação linear e
tolerância temporal nativa em duas fases fora da grade: apoios, piso, preensão, vínculos,
juntas, oscilação do corpo, fase aérea, fechamento dos loops e encaixes.
`continuidade-bordas.json` compara as poses a 1/60 s de cada borda com a
continuação do ciclo correspondente. O maior desvio dos pivôs é inferior a
0,004 unidade; orientação inferior a 0,022°. Os pontos exatos de chegada das
partidas também estão gravados nos loops. A cadeia do arrasto mantém um
relógio comum para não mergulhar a espada devido à tolerância temporal nativa.

Motor: zero erros/avisos de estrutura e animações. O critério de espessura
aceita as cristas finas de 0,01 unidade herdadas da v9; elas não foram alteradas.

Seis GIFs individuais e duas sequências `sequencia-pacifica.gif` /
`sequencia-combate.gif` mostram as transições completas. As prévias nativas
usam câmera fixa e o Blockbench real; não equivalem a uma integração no jogo.
`poses-nativas.png` reúne seis instantes. Fontes manuais permanecem intactas.

As corridas aguardam avaliação artística. Golpes ficam para a etapa seguinte.
