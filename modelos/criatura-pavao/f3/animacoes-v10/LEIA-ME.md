# F3 — flicks numéricos e descanso mais leve

Modelo: `criatura-pavao-e3-combate-v10.bbmodel`.
Fonte preservada: `../animacoes-v9/criatura-pavao-e3-combate-v9.bbmodel`.

## Causa confirmada

O parser Molang instalado no Blockbench 5.2.2 interpreta `1e-8` como `-8`
e `-6.5e-7` como `-7`. Essas strings apareciam exatamente nas pequenas
rotações/compensações das penas no início do saque e nas bordas de start/stop.
O leitor numérico anterior convertia expoentes corretamente e escondia essa
diferença do aplicativo. Apenas sincronizar mais chaves não resolvia a causa.

Todos os valores agora usam texto decimal explícito. 2.831 chaves foram
regravadas nos outros clipes sem alterar seus valores, tempos, interpolação
ou metadados de animação. O pipeline também faz essa conversão em toda nova
operação `set_keyframe`; expressões Molang são preservadas.

## Descanso

`combat_idle`: **34.644 → 5.866 chaves**, redução de **83,1%**. Duração de
7,15 s, pausa de três segundos, cravar/soltar/recuperar/guardar e marcadores
preservados. Redução por canal, com eventos protegidos; a conferência inclui
a tolerância temporal nativa fora da grade. Limites locais: 0,01° e 0,001
unidade por eixo. Maior desvio visual medido: **0,02561 unidade**.

O arquivo passa de 44,95 para 36,12 MB. A medição real de FPS ficou
indisponível porque a janela estava oculta e o render suspenso; zero frames
nessa condição não representa o desempenho da animação.

Geometria, textura, UVs, hierarquia e os outros doze movimentos são os da v9.
Não houve alterações no Roblox Studio. Golpes continuam como próxima etapa.

## Conferência

```powershell
uv run pytest -q ferramenta/testes/test_chaves_decimais.py
uv run python scripts/corrigir-flicks-pavao-f3-v10.py --gerar
uv run python scripts/corrigir-flicks-pavao-f3-v10.py --validar --auditar
```

- `validacao.json` e `validacao-nativa.json`: nove clipes de combate,
  incluindo encaixes, espada solta, piso, juntas, raízes e conexões.
- `validacao-motor.json`: quatro clipes dos instantes relatados, sem erros,
  avisos ou canais ignorados. Descanso/camadas são conferidos no contexto
  próprio para respeitar espada enterrada e máscara de ossos.
- `comparacao-tecnica.json`: precisão da compactação e diagnóstico numérico.
- `comparacao-nativa.png`: capturas reais dos instantes indicados, v9/v10.
- `compactacao.json` e `geracao.json`: contagens, tolerâncias e hashes.

As camadas superiores mantêm as regras da v9: substituir os canais da
máscara sobre o companheiro completo no mesmo tempo; não são aditivas.

A v10 aguarda a conferência visual dos cinco pontos relatados e a avaliação
do desempenho do descanso com a janela visível.
