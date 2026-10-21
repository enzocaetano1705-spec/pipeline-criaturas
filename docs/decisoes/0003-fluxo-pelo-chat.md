---
tipo: decisao
data: 2026-10-21
status: vigente
---

# 0003 — Fluxo pelo chat e edições à mão

**Contexto:** o usuário quer trabalhar só pelo chat: anexar as imagens, receber a folha de vistas e pedir ajustes com um print e uma frase. Ele também vai editar os modelos à mão no Blockbench, e a IA precisa acompanhar essas edições.

**Decisão:**
- O usuário anexa o conceito, a frente e o lado (gerados com o mesmo design). A medição continua cruzando frente e lado; não há modo de "imagem única".
- Novos comandos: `nova` (monta a pasta e a ficha a partir dos anexos), `ver`, `quadro`, `aplicar` (correção por lote de operações, validada, guardada em `eN/correcoes/`) e `adotar`.
- Edição à mão não bloqueia mais as etapas. Ela é **adotada**: a diferença em relação ao último estado do pipeline (`eN/.estado/ultimo.bbmodel`) vai para `eN/historico.jsonl`, e o trabalho segue sobre a versão do usuário. Textura e animações que ele mexeu ficam protegidas (só `--forcar` regera); locators que ele moveu ficam onde estão.
- O `cubificar` continua gravando `.v2` sobre um arquivo editado, porque ele recomeça a geometria do zero. A skill orienta a usar `aplicar` em vez dele.
- Sem `.bat` (o usuário preferiu tudo pelo chat).

**Alternativas descartadas:**
- Uma imagem só (3/4), com profundidade estimada: menos fiel. O usuário prefere mandar frente e lado.
- Recusar o arquivo editado e exigir um `cubificar` novo (comportamento anterior): perdia as edições do usuário.

**Consequências:** a skill ganha `skills/criaturas-3d/chat.md`. Para desfazer uma correção da IA, copie `eN/.estado/antes-de-aplicar.bbmodel` por cima do modelo e rode `adotar`.
