# Ensaio orgânico — Fera das Sombras F3

Arquivo atual: [fera-sombras-organica.blend](r05/fera-sombras-organica.blend).
Folha: [folha-geometria.png](r05/folha-geometria.png).

Preguiça gigante, rogue, forma 3 de 3. Quatro referências originais e hashes em
`entrada/`. Autoria inteiramente por código em `scripts/fera-organica/`, sem importar
geometria dos modelos anteriores e sem gerador 3D externo.

## Resultado verificável

- 19.516 triângulos visíveis; corpo reduzido com 8.500 triângulos.
- Mestre preservado e oculto: 140.512 triângulos.
- Corpo/cabeça/pescoço/membros/dedos/cauda: uma superfície conectada.
- Zero bordas abertas ou arestas não manifold no corpo; volume positivo.
- Arquivo reaberto em processo limpo, zero erros.
- Garras: três por mão e três por pé; vestuário e olhos separados conforme referência.

A folha e os renders são Blender EEVEE. Cores por vértice e materiais procedurais
são estudo, não pintura UV final. A decimação preserva a apresentação, mas ainda
exige retopologia/ajuste de pesos antes de prometer animação orgânica correta.
Não houve exportação/importação Roblox nem aprovação artística.

## Conferência MCP

`get_addon_status` e `look(image=render)` falharam por falta de conexão com o
Blender. Nenhum comando de autoria foi enviado por MCP. Há duas janelas Blender
abertas com modificações não salvas; elas foram preservadas. A conferência ao vivo
requer ativar a conexão do addon. Não instalar/atualizar automaticamente.

## Consumo

Até o checkpoint `06-fechamento`: entrada sem cache **29.324**,
entrada cacheada **5.672.832**, saída **47.721**,
total processado **5.749.877**. Cache e raciocínio já estão incluídos
nos respectivos totais. O registro inclui preparação, tentativas e revisões.
Tokens finais de documentação/resposta posteriores ao checkpoint não estão incluídos.
Não converter esses números em preço ou percentual do plano.

Os snapshots globais da conta mudaram de 46% para 70% na janela de 5 h e de 54%
para 58% na semanal. São dados globais compartilhados; a variação não é uma
medição isolada deste trabalho. Nenhuma compra ou geração 3D externa foi acionada.
Tempos de subprocesso em cada `execucao.json`, separados do consumo do chat.

## Reproduzir em uma pasta nova

Na raiz, usando o Blender instalado:

```powershell
& 'C:/Program Files/Blender Foundation/Blender 5.1/blender.exe' --background --factory-startup --disable-autoexec --threads 2 --python-exit-code 1 --python scripts/fera-organica/modelar.py -- r06
uv run python scripts/fera-organica/montar_folha.py r06
& 'C:/Program Files/Blender Foundation/Blender 5.1/blender.exe' --background modelos/fera-fera-agil-das-sombras/organico-v1/r06/fera-sombras-organica.blend --disable-autoexec --threads 2 --python-exit-code 1 --python scripts/fera-organica/conferir.py
```

Uma revisão existente é recusada. O `.blend` nativo contém o mestre oculto e a
cópia de apresentação; o script/manifesto registra quais superfícies são estudo.
