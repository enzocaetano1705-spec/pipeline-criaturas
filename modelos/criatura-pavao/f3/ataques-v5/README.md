# F3 — Low acelerado e combo aéreo

`criatura-pavao-e3-ataques-v5.bbmodel` é uma cópia nova da v4, com quatro
clipes em avaliação. A trajetória aprovada do Low é preservada e recebe
uma nova distribuição do tempo. O Cross foi desdobrado nos três ataques
pedidos; a versão anterior continua disponível na pasta `ataques-v4/`.

| Clipe | Duração | Movimento |
|---|---:|---|
| `attack_low` | 1,42 s | Mesmo arco amplo; carga lenta, aceleração curta e frenagem |
| `attack_right` | 1,65 s | Ascendente direito, continuação da lâmina e frenagem pelo corpo |
| `attack_left` | 1,50 s | Descendente esquerdo saindo do ombro, agora independente |
| `attack_combo` | 2,20 s | Impulso, corte diagonal, volta no ar e impacto duplo na queda |

Cada clipe começa e termina na `combat_ready` aprovada. Os três últimos
podem formar uma sequência futura. Não há implementação de lógica de jogo.

## Movimento

O Low mantém a amplitude da v4. O ritmo muda por uma transformação suave
do tempo: a aceleração fica concentrada na passagem da espada pela frente.
No direito isolado, a lâmina continua antes de parar; tronco, cintura,
cauda e pernas absorvem a desaceleração antes de voltar à guarda.

No combo, as pernas carregam e impulsionam o salto junto com o corte
ascendente de 45°. A primeira fatiada continua no começo da rotação,
sem uma pose de parada separando golpe e giro. Pelve, tronco e cauda têm
fases diferentes. As pernas recolhem no ar e abrem para a aterrissagem.
As duas espadas armam acima da cabeça e descem enquanto a criatura cai;
pernas e coluna comprimem no impacto, seguidas pela recuperação.

O deslocamento de `root` é somente vertical, sem avanço líquido: ápice
de 20 unidades e voo de 0,40 a 1,20 s. O corpo faz uma volta completa e
termina olhando na direção inicial. As penas mantêm as raízes ancoradas.
As lâminas prolongam os antebraços durante os cortes; a orientação do fio
considera a velocidade do ombro, do salto e da queda.

Referência de estrutura do salto/giro: [IWUF, Taolu, seção 3.1.2.1](https://iwuf.org/wp-content/uploads/2021/09/EN-IWUF-Wushu-Taolu-Competition-Rules-Judging-Methods-Excerpt-2019.pdf),
páginas impressas 56–57: rotação medida entre saída e aterrissagem e
execução aérea. A combinação de duas lâminas gigantes é a coreografia
fantástica pedida pelo usuário; a fonte não descreve este ataque.

## Verificação e reprodução

Geometria, rig, UVs, pintura e outros 19 clipes preservados. Total: 23
clipes. `animacoes.json` registra os eventos de dano, voo e impacto e
a sequência sugerida. Nenhuma fonte manual é sobrescrita.

`validacao-ataques.json`: arquivo salvo em interpolação linear e numérica
nativa, articulações, preensão, fio, apoios/voo, raízes das penas,
continuidade, piso e sondagem das superfícies opacas contra o corpo.
O voo só é permitido na janela declarada do combo. Sondagens são auxiliares
de revisão; a aprovação artística continua com o usuário.

`validacao-motor.json`: estrutura e animações no motor externo.
GIFs e `poses-nativas.png`: captura no Blockbench, com parâmetros e hash em
`previas-nativas.json`. O helper trata o erro conhecido do listener no
descarte da vista privada e confirma a remoção dessa vista.

```powershell
uv run python scripts/animar-golpes-pavao-f3-v5.py --gerar --validar
```

`--clipes attack_combo` atualiza apenas esse clipe depois da geração
completa. `--nativo` exige a v5 aberta. Todas as escritas passam pelo
motor externo em lotes e verificam o hash contra edições manuais.
Chaves usam decimais explícitos, sem fórmulas Molang ou expoentes.
O bake parte de 120 Hz e adiciona amostras nos intervalos em que a
interpolação deslocaria uma âncora ou colocaria uma lâmina sob o piso.
