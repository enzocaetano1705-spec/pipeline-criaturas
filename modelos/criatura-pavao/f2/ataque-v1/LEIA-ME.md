# F2 — proposta de ataque v1

Arquivo: `criatura-pavao-e2-ataque-v1.bbmodel`. Selecionar **attack_physical** na aba Animate.
Clipe de **1,5 s**, uma execução, assado a **60 Hz**, sem escala animada ou fórmulas Molang.

## Movimento proposto

| Tempo | Ação |
|---|---|
| 0–0,32 s | Passo curto da perna esquerda, transferência de peso e braços recolhidos. |
| 0,32–0,40 s | Antecipação: pequena pausa para ler a intenção do ataque. |
| 0,40–0,52 s | Bote: corpo/pescoço avançam e os antebraços alcançam o alvo. |
| 0,52–0,74 s | Fechamento rápido dos braços para dentro, como uma tenaz. |
| 0,74–1,50 s | Recuo, retorno do pé e dissipação do movimento da crista/leque. |

O apoio digitígrado e o passo seguem a estrutura do walk existente. O corpo faz um avanço curto,
com cabeça orientada para o alvo; a cauda compensa a inclinação e as penas respondem com atraso.
As penas das asas têm compensação do movimento do braço para não varrerem o chão durante o golpe.

É uma **adaptação artística ao híbrido do usuário**, não uma reprodução literal do ataque de um
avestruz. A referência de louva-a-deus é a preparação seguida de alcance/fechamento rápidos dos
membros anteriores: [Rossoni & Niven, 2020](https://pubmed.ncbi.nlm.nih.gov/32396788/),
[dados e descrição das fases pelos autores](https://datadryad.org/dataset/doi%3A10.5061/dryad.59zw3r244).
Para a ave, foi considerado o uso das asas/cauda no equilíbrio descrito pelo
[San Diego Zoo](https://animals.sandiegozoo.org/animals/ostrich). A anatomia continua sendo a do F2.

## Arquivos e verificação

- `previa-ataque.gif`: repetição para revisão; o clipe no modelo permanece sem loop.
- `poses-ataque.png`: seis poses, câmera fixa.
- `ataque.ops.json`: lote original aplicado pelo motor externo do Blockbench.
- `animacoes.json`: proposta dos marcadores de impacto/recuperação; não executa dano.
- `proveniencia.json`: hashes da fonte manual e da proposta gerada.
- `medidas-ataque.json` e `validacao-*.json`: medições e validações, sem depender de aprovação visual.

A fonte é a versão salva pelo usuário **sem as sete garras**, com 59 peças. O arquivo manual não
foi sobrescrito. Geometria, textura e rig permaneceram iguais na cópia; idle/walk mantêm suas chaves
e curvas. O codec apenas normaliza animadores vazios acrescentando listas de chaves vazias.

Na verificação: zero erros/avisos no clipe, sem separação de juntas ou afundamento acima da tolerância
de 0,05 unidade. Medição a 120 Hz: erro máximo do pé no apoio de 0,030 unidade (menos de 1/25 de um
texel da arte), mínimo Y=0,081 frente ao repouso Y=0,087. Início/fim neutros e sem deslocamento acumulado.

## Reproduzir

```powershell
uv run python scripts/animar-ataque-pavao-f2.py
uv run python scripts/revisar-ataque-pavao-f2.py
```

O primeiro comando recusa uma saída existente. `--refazer` permite refazer somente uma proposta cujo
hash ainda coincide com a geração registrada. Uma edição manual nesta proposta passa a ser protegida.

**Estado:** aguardando avaliação do usuário no Blockbench. O registro do Roblox ainda aponta para
`f2/criatura-pavao-e2.bbmodel`, sem o ataque. Os GLBs atuais ainda não incorporam a remoção das garras;
o manifesto será renovado ao exportar a versão aprovada.
