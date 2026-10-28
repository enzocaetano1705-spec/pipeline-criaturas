# F3 — conjunto de golpes aprovado

Modelo atual: `criatura-pavao-e3-ataques-v7.bbmodel`.

- `attack_low` — 1,42 s, mantido para alvos de qualquer altura.
- `attack_left` — 1,32 s, mantido para alvos de qualquer altura.
- `attack_combo` — 2,20 s, aprovado com o golpe duplo fechado.

`attack_right` retirado por decisão do usuário. Os 22 clipes restantes,
incluindo estes três golpes, conservam integralmente chaves, UUIDs,
tempos e eventos da v6. Geometria, rig, locators, UVs e atlas também iguais.

`validacao-catalogo.json` comprova que o nome do projeto e a remoção desse
clipe são as únicas alterações do modelo. As medições de movimento e
prévias da [v6](../ataques-v6/README.md) continuam válidas para os clipes
preservados. `animacoes.json` registra catálogo, sequência sugerida e aprovação.

Reprodução pela raiz do repositório:

```powershell
uv run python scripts/consolidar-golpes-pavao-f3.py
```

`--validar` verifica a saída existente. A gravação usa o motor externo,
em uma cópia nova, com proteção por hash contra edições manuais.
Exportação e integração da F3 no jogo continuam como etapas futuras.
