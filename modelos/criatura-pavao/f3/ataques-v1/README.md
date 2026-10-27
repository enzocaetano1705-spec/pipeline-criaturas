# F3 — primeiros três ataques

Versão para avaliação artística. Fonte: `../corrida-v1/criatura-pavao-e3-corrida-v1.bbmodel`.
Os seis clipes de corrida foram aprovados pelo usuário em 27/10/2026.
19 animações anteriores preservadas, com geometria, rig, UVs e textura iguais.
Modelo novo: `criatura-pavao-e3-ataques-v1.bbmodel`, 22 clipes.

| Clipe | Alvos | Duração | Movimento |
| --- | --- | --- | --- |
| `attack_low` | pequenos/baixos | 1,15 s | Talho rasante direito; agacha, avança uma pata, transfere o peso e recupera a guarda. Esquerda permanece no ombro. |
| `attack_cross` | médios/grandes | 1,50 s | Dois cortes diagonais: direito ascendente, depois esquerdo descendente, com duas transferências de peso. |
| `attack_spin` | área | 1,75 s | Preparação, passo para o eixo de apoio, volta de 360° e frenagem. Direita baixa, esquerda em altura intermediária. |

Os três começam e terminam em `combat_ready@0`. Esquerda/direita são da
criatura. Espadas presas às mãos, bases das wings/penas ancoradas,
cotovelos com eixo de flexão e reação do peito, pelve, cabeça, cauda e cristas.
O bico não participa dos golpes. Sem root motion; o pequeno avanço corporal
é local e volta à origem.

`animacoes.json` contém tempos propostos de impacto, recuperação e janela
ativa. São metadados para integração futura, sem lógica de dano, hitboxes,
seleção de alvo ou pet. A passagem de corrida/marcha diretamente para
esses ataques ainda depende da mistura do estado corrente no jogo.

## Conferência

- `validacao-ataques.json`: arquivo salvo, leitura linear e avaliador local
  da semântica numérica nativa em duas fases temporais, a 240 amostras/s.
  Apoios/piso, alcance, juntas, preensão da lâmina inteira, âncoras,
  continuidade e retorno exato à guarda passaram.
- Sondagem de superfície opaca a 36 amostras/s: nenhuma penetração nova
  das espadas nos volumes principais do corpo. Não equivale a colisão de jogo.
- `validacao-motor.json`: motor externo, três clipes a 120 amostras/s,
  zero erros/avisos de estrutura, timing, piso ou separação.
- GIFs `*-local.gif` e `poses-locais.png`: renderizador local, lendo as
  chaves salvas, com câmera fixa por clipe. Não são capturas do aplicativo.

O arquivo foi enviado para abertura no Blockbench, mas a janela ficou vazia
e o endpoint MCP deixou de responder. Captura nativa pendente de reabrir o
aplicativo/reativar o servidor. As prévias locais permitem avaliar os golpes.

## Reprodução

Na raiz: `uv run python scripts/animar-golpes-pavao-f3.py --gerar --validar`.
`--clipes attack_spin` atualiza só esse golpe depois da geração completa.
`--previas` gera a reserva local; `--nativo` captura pelo MCP com esta versão
aberta. O hash de geração impede sobrescrever alterações manuais na saída.
Todas as gravações de animação passam pelo motor externo e usam decimais
explícitos para evitar a interpretação de expoentes como Molang.

Referência de passo/eixo/transferência de peso: [Memorial da Prattica do
Montante, Figueyredo (1651), tradução Myers/Hick](https://www.oakeshott.org/wp-content/uploads/2016/10/Figueiredo_Montante_Translation_Myers_and_Hick_v2.pdf).
Adaptada à anatomia e às duas penas grandes da F3; não é reprodução de uma
técnica histórica de duas espadas. Nenhuma animação de terceiros foi copiada.
