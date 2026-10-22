# Exportações para o Roblox

| criatura | arquivo | escala no Studio |
|---|---|---|
| Pavão F1 (bebê) | `pavao/Pavao_F1.glb` | 3 |
| Pavão F2 (avinídeo) | `pavao/Pavao_F2.glb` | 3 |

1. Importe o `.glb` no Studio: File › Import 3D, com Rig Type **Custom**.
2. Rode `preparar-criatura.luau`, ajustando `NOME` e `ESCALA`.
3. Para trabalhar com os modelos no jogo, especialmente por IA ou MCP, leia o [GUIA-IA-ROBLOX.md](GUIA-IA-ROBLOX.md).

Os dados de cada criatura (estágio, animações, velocidade do walk) estão em `criaturas.json`.

Para gerar de novo: `uv run python scripts/exportar-roblox.py`.
