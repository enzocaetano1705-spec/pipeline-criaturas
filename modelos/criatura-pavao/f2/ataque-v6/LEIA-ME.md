# F2 v6 — impulso elástico da cauda

**Pisão e spin aprovados, preservados integralmente. Avaliar apenas `attack_tail_kick`.**
Arquivo: `criatura-pavao-e2-ataque-v6.bbmodel`, Animate, duração **2,10 s**.
`previa-impulso.gif` mostra 3/4 e perfil a **1×/50 fps**, com pausa de 0,30 s no fim.

## Movimento

| Fase | Tempo | Ação |
|---|---:|---|
| Apoio | 0,00–0,43 s | Reposiciona os pés, flexiona o tronco e planta a parte sólida da cauda. |
| Carga | 0,43–0,54 s | Recolhe as patas e concentra o apoio na cauda; quadril, ligação do torso e peito comprimem em sequência. |
| Impulso | 0,54–0,70 s | Cauda estende a curva sob carga e acelera o corpo para cima e para a frente. |
| Golpe aéreo | 0,70–1,12 s | Solta o chão; as duas patas avançam juntas. Contato visual entre 0,82 e 0,88 s à altura do peito em repouso. |
| Pouso | 1,12–1,26 s | Patas recebem o corpo e pernas/tronco absorvem a queda e o avanço. |
| Recuperação | 1,26–2,10 s | Recupera os apoios com passos e volta à pose inicial. |

A trajetória aérea começa com a velocidade da extensão da cauda no último instante de apoio.
Não há pausa antes de iniciar um salto separado. A parábola avança aproximadamente **6,72 unidades
Blockbench**, com uma saída breve do chão. A inclinação do corpo, braços, pescoço e leque acompanham
as mudanças de carga. As penas mantêm sua abertura e continuam rígidas.

É uma coreografia do efeito de mola pedido para a criatura fictícia. Não é simulação física
de tecido muscular ou medição da força real de um canguru. Dano, knockback e deslocamento do
modelo físico no cenário continuam pertencendo à integração futura de gameplay.

## Relação entre `hips`, `TorsoHips` e cauda

- Novo `pelvis`: move `hips` junto à raiz da cauda.
- Novo `waist`: articula `TorsoHips` pela união traseira que fica dentro de `hips`.
  O peito e as pernas seguem essa ligação, conservando as posições dos encaixes.
- As rotações de pelve, ligação do torso e peito distribuem a compressão/extensão pela coluna.
  O torso não gira isoladamente sobre um quadril congelado durante a descarga da cauda.
- A IK usa a matriz real desse encaixe para resolver os pés. O comprimento das pernas e o lado
  de dobra do joelho permanecem os do rig, sem escala animada.
- `tail_1` e `tail_2` articulam os dois volumes sólidos já existentes; leque conserva seus
  ângulos internos. Não se apoia o peso nas penas.

**59 cubos, 48 grupos**, mesma geometria, textura, UV e pose de repouso da v5.
As novas articulações ficam neutras nos clipes aprovados e em idle/walk.

## Conferência do arquivo salvo

- **Pisão e spin:** chaves/curvas originais preservadas e comparação de todos os cantos dos
  59 cubos a 240 Hz com a v5: **desvio zero** em ambos.
- **Juntas:** uniões quadril/ligação do torso, ligação/peito e quadril/cauda permanecem dentro
  dos dois volumes que conectam; maior erro numérico **7,2×10⁻¹⁵ unidade**.
- **Carga na cauda:** patas acima de **Y=4,65** na carga; cauda sólida apoiada até a soltura,
  com desvio máximo de **0,01793 unidade** entre chaves.
- **Fase aérea completa:** aproximadamente **0,704–1,113 s**, incluindo cauda e penas visíveis.
- **Altura do golpe:** peito base em **Y=22,12025**; centros das duas patas alcançam essa altura
  entre 0,82 e 0,88 s com erro máximo **0,01624 unidade**.
- **Continuidade:** a velocidade ao sair do apoio é aproximadamente **+15 Y / −16 Z unidades/s**;
  começo/fim neutros, sem escala e sem salto de orientação entre chaves.
- **Chão:** superfície visível mínima **Y=0,083084**, contra piso **Y=0,087410**.
  Acréscimo máximo de penetração nas amostras opacas das penas contra pernas/pés/quadril
  **0,00242 unidade**, descontado o contato de repouso.
- Motor externo: estrutura sem erros/avisos; ataque sem erros ou juntas separadas.
  Um aviso aponta o retângulo transparente de `fan_5` abaixo do piso na soltura.
  Os cantos dos texels opacos ficam acima do piso, dentro do desvio de interpolação indicado.
- Conferidos no viewport nativo: carga da cauda e golpe aéreo. Geometria e textura preservadas.

Detalhes: `medidas-impulso.json`, `aprovados-preservados.json`, `validacao-*.json` e proveniência.
As verificações técnicas não substituem a avaliação artística da fluidez e do peso do golpe.
Fonte v5 e fonte manual protegidas; não integrado ao Roblox antes da avaliação deste ataque.

## Reprodução

```powershell
uv run python scripts/animar-impulso-cauda-pavao-f2-v6.py --medir
uv run python scripts/revisar-impulso-cauda-pavao-f2-v6.py --poses
uv run python scripts/animar-impulso-cauda-pavao-f2-v6.py
uv run python scripts/revisar-impulso-cauda-pavao-f2-v6.py
```

O gerador recusa saída existente/editada. `--refazer` só regenera a própria saída com hashes
de fonte e saída ainda correspondentes. Edição manual posterior exige nova versão.
No revisor, `--sem-gif` executa as verificações e gera apenas a folha final.
Sem dependência ou mudança de formato do pipeline; reaproveitadas as referências da v5.
