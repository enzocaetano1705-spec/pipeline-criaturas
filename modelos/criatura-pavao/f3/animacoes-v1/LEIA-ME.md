# F3 — animações pacíficas e combate com penas da cauda

Proposta para revisão no Blockbench. `origem-manual.bbmodel` guarda a edição do
usuário capturada da aba ativa. A saída animada está indicada em `../estado-atual.json`.

| Clipe | Segundos | Repetição | Movimento |
|---|---:|---|---|
| `idle` | 3,20 | Sim | Respiração e postura aviana |
| `walk` | 1,50 | Sim | Marcha com corpo inteiro e braços dobrados |
| `combat_enter` | 3,40 | Não | Alcançar penas 04/06, sacar, erguer o corpo e cravar a espada direita |
| `combat_idle` | 3,00 | Sim | Espada esquerda no ombro, direita no chão e respiração pesada |
| `combat_walk` | 1,80 | Sim | Marcha mais ereta, carregando as duas lâminas |
| `combat_exit` | 2,80 | Não | Extrair a espada, recolocar as penas e voltar à postura pacífica |
| `combat_walk_start` | 0,80 | Não | Levantar a espada e preparar o primeiro passo |
| `combat_walk_stop` | 0,80 | Não | Recolher os passos e pousar a espada |

O pescoço inferior recebeu pintura nova e ilhas UV próprias; a pintura anterior
fora dessas ilhas continua intacta. A geometria dos 93 blocos manuais foi preservada.
Os pivôs foram alinhados às juntas atuais; o rig contém 41 grupos.

Veja os GIFs com os nomes dos clipes. `validacao.json` verifica o arquivo gravado,
incluindo os intervalos entre chaves, contatos, mão/arma, vínculos com a cauda,
costuras e conexões dos clipes. O motor fornece diagnóstico estrutural separado.
As pontas enterradas da espada são intencionais. A revisão artística ainda é do usuário.

## Reprodução

Na raiz do repositório:

```powershell
uv run python scripts/animar-pavao-f3.py --preparar --animar
uv run python scripts/revisar-animacoes-pavao-f3.py --validar --previas
```

O gerador recusa sobrescrever a saída se seu hash mudou desde a última revisão.
Se houver edições manuais novas, preservar o arquivo e criar outra versão/fonte.
Os lotes passam pelo motor externo; não há escrita direta de JSON `.bbmodel`.

Movimento das armas e ossos está assado em chaves numéricas, sem depender de
scripts ou mudanças de hierarquia em execução. Nenhuma integração no Studio foi feita.
Velocidades de referência e eventos estão em `animacoes.json`; conexões de
começar/parar a caminhada usam a fase zero do ciclo.
