# F3 — levantamento rápido antes do floreio

Arquivo: `criatura-pavao-e3-combate-v6.bbmodel`.
Fonte preservada: `../animacoes-v5/criatura-pavao-e3-combate-v5.bbmodel`.
Somente `combat_enter` revisto. Os outros doze clipes, incluindo respiração
da `combat_ready` e marcha aprovada, conservam integralmente canais e tempos.

| Trecho | v5 | v6 |
|---|---:|---:|
| Saque inicial | 0–0,40 s | 0–0,40 s |
| Subida do braço | 0,40–1,15 s | 0,40–0,70 s |
| Floreio | 1,15–1,68 s | 0,70–1,23 s |
| Apoiar no ombro | 1,70–2,10 s | 1,25–1,65 s |

A subida dura 0,30 s, antes 0,75 s: 2,5 vezes mais rápida em média.
Aceleração concentrada no meio do gesto, com velocidade compatível nas
emendas do saque e do floreio. Giro e recuperação conservam ritmo e poses;
apenas começam 0,45 s antes. Duração total: 1,65 s.

Todas as chaves originais foram mantidas com novos tempos. Isso preserva
também a interpolação entre as poses, incluindo preensão, penas e apoio da
espada no chão. As chaves ficam mais próximas durante a subida; não descartar
essas chaves para forçar uma grade uniforme de tempo.

## Reprodução e conferência

```powershell
uv run python scripts/animar-combate-pavao-f3-v6.py --animar --validar --previas
```

Escrita pelo motor externo, em versão nova e protegida por hash. Verificadas
as chaves salvas: preservação dos doze clipes, geometria/UVs/rig, trajetórias,
apoios, empunhadura, wings, limites/eixos das juntas, giro completo e conexões.
Relatórios: `validacao.json` e `validacao-motor.json`; sem erros ou avisos de
animação no motor. Prévia em `combat_enter.gif`.

Avaliação do novo ritmo pendente. Demais variantes/transições/descanso/saída
continuam adiados. Sem ações no Roblox Studio.
