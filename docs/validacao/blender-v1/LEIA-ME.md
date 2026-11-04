# Ensaio Blender mínimo — 04/11/2026

Backend opcional funcionando da descrição sintética à cena `.blend`, GLB, render
e reimportação. Não é uma produção artística comparativa nem um teste no Roblox.

| Evidência | Resultado |
|---|---|
| Fixture original | 14 caixas/lâminas, 168 triângulos, uma malha/material |
| Rig | 15 ossos anatômicos + wrapper Raiz; uma influência por vértice |
| Animação | idle, walk, run, attack_physical; bake 120 Hz |
| Revisão temporal | 1.348 amostras a 240 Hz, incluindo subframes |
| GLBs base/âmbar/violeta | Khronos: zero erros, zero avisos em cada |
| Reconstrução | mesma geometria, atlas, poses e três GLBs byte a byte |
| Ida/volta | erro máximo de superfície 0,0000098 unidade |
| Pivôs/locators | erro máximo na ida/volta < 0,000007 unidade |
| Piso | mínimo -0,000393 unidade, abaixo da tolerância de 0,02 |
| Apoio compensado | desvio máximo por amostra 0,000389 unidade |
| Loops | posição inicial/final idêntica na tolerância numérica |
| Colisões | zero penetração na triagem OBB dos pares explicitados |
| Variantes | duas recolorações; olhos, bico, pés e alfa preservados |
| Preservação | 236 fontes/exportações existentes conferidas sem alteração |

`ensaio.json` guarda hashes das duas execuções, tempos, falhas/retrabalho,
auditoria dos GLBs do pavão e uso indisponível explicitamente não medido.
Os JSONs restantes são evidência resumida da primeira execução; o manifesto é
um **snapshot da pasta de origem**, não a lista de arquivos desta pasta reduzida.
As amostras completas, `.blend` e GLBs estão nas pastas geradas indicadas abaixo.

**Limitações observadas:** a projeção do pivô body sai do envelope estático dos
pés em até 0,973 unidade no walk e 0,962 no run durante transferência de apoio.
É uma heurística de equilíbrio, não medição de centro de massa/estabilidade
dinâmica; ambos os avisos permanecem no relatório. Apreciação de peso,
personalidade, antecipação/impacto e recuperação exige avaliação artística.
A colisão cobre pares de risco da fixture, não toda interseção possível.

O atlas tem 84 ilhas por face, 16,9% de área útil e 47,1% incluindo margens.
Empacotamento shelf é deliberadamente simples; não é prova de aproveitamento
ótimo. Resolução 64 não comporta densidade e margens escolhidas. Redes de faces
contíguas/compartilhamento podem melhorar esse custo numa revisão autorizada.

As duas execuções finais levam dezenas de segundos nesta máquina; os tempos
exatos medidos estão no JSON. Eles medem geração/validação/render em subprocessos,
não o custo total de engenharia do chat nem o custo recorrente da próxima criatura.
Tokens, créditos, ID exato do modelo e esforço não foram expostos ao script e
permanecem `null`. Não houve inferência de consumo a partir de chamadas MCP.

**Testes executados:**

- `uv run pytest -q -k 'not test_exporta_roblox_glb_valido'`: **235 passaram,
  1 pulado, 1 desmarcado**, 414,32 s. Pulado: integração Blender opt-in; desmarcado:
  teste que acionaria Blockbench desktop.
- `CRIATURAS_TESTAR_BLENDER=1 uv run pytest ferramenta/testes/test_blender_backend.py -q`
  (variável configurada via PowerShell): **16 passaram**, 119,78 s, duas
  reconstruções e detecção de alteração posterior num PNG. Após refinar proteção
  da máscara, os 15 testes host passaram de novo; as duas execuções finais abaixo
  verificaram a versão final dos scripts.
- `compileall` e `git diff --check`: sem erros nos arquivos novos/alterados pelo backend.

**Saídas completas locais:**

- `modelos/_blender/minimo-v1/`
- `modelos/_blender/minimo-v1-reconstrucao/`

**Reproduzir:** seguir [sistema Blender](../../sistema-blender.md). Para congelar
uma nova evidência em pasta nova:

```powershell
uv run python scripts/registrar-ensaio-blender.py modelos/_blender/minimo-v1 modelos/_blender/minimo-v1-reconstrucao --saida docs/validacao/blender-nova-revisao
```

**Retomada:** aguardar referências, prompt, estágio e categoria da primeira
criatura comparativa; confirmar categoria/folha. Importação/render no Roblox
continua pendente em laboratório autorizado, com câmera/luz/escala equivalentes.
O place do jogo `108241641467799` não foi controlado, e `../jogo-criaturas` só
foi consultado para leitura do contrato. Nenhum vencedor foi escolhido.
