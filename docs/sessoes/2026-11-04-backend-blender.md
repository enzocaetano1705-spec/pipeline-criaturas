---
tipo: sessao
data: 2026-11-04
fase: extensão Blender B.1–B.3
ia: codex
modelo: família GPT-6 conforme contexto; ID exato/esforço não expostos
status: mínimo validado em arquivo/Blender; Roblox pendente
---

# Backend Blender opcional, criação sintética e ida/volta GLB

**Retomada com o usuário:** aguarda imagens e prompt da primeira criatura
comparativa, estágio e categoria (ou confirmação da sugestão). Categoria e folha
devem ser aprovadas antes da produção completa. **Pedido futuro, não bloqueante:**
importar a fixture num laboratório Roblox autorizado e avaliar aparência/movimento
com câmera/luz/escala equivalentes. Não usar o place do jogo `108241641467799`.

**Feito:** B.1–B.3 da extensão autorizada. Branch isolada `codex/backend-blender`.
Commits `5ed88ba` (decisão/protocolo) e `24cd041` (backend/fixture/testes);
evidência e nota são o commit de conclusão B.3 desta sessão.

`criaturas blender` executa scripts Python em Blender 5.1.1 instalado, background,
factory startup, threads 2. Nada controla mouse/teclado/foco ou o Blender vivo.
Descrição estruturada -> 14 caixas/lâminas originais -> atlas/máscara e duas
variantes -> rig rígido e locators -> idle/walk/run/ataque -> `.blend` e três GLBs
-> validação Khronos -> reimportação num segundo processo e revisão a 240 Hz.
O contrato do jogo foi lido; não houve escrita em `../jogo-criaturas`, controle
do Studio, upload ou publicação de assets.

**Decisões:** [[0009-backend-blender-opcional]]. Compartilha nomes, unidades,
`plano_cubos`/locators/eventos e Khronos; atlas, rig/bake e validação espacial são
do backend. Blockbench e exportador/Minecraft aprovados intactos. O backend v1
recusa criaturas reais até haver pacote de referências e aprovações; não reutilizar
a fixture como molde anatômico automático. Não escolhe vencedor.

**Conferência:** suíte: **235 passaram, 1 pulado, 1 desmarcado** em 414,32 s
(`uv run pytest -q -k 'not test_exporta_roblox_glb_valido'`). Integração Blender
opt-in: **16 passaram** em 119,78 s, incluindo duas reconstruções e detecção de
alteração posterior. Depois da proteção final da máscara, **15 testes host**
passaram; duas execuções finais com a versão final dos scripts também passaram.
O teste desktop foi desmarcado para não acionar interface; integração no motor
permanece separada. Compileall/diff-check sem erro.

Três GLBs de **168 triângulos**, uma malha/material, 16 joints com wrapper,
uma influência rígida/vértice. Khronos zero erros/avisos. Duas execuções finais
em **41,42 s** e **38,60 s**, geometria/atlas/poses e três GLBs idênticos byte a
byte. 1.348 amostras a 240 Hz: superfície reimportada difere no máximo 0,0000098
unidade; pivôs/locators < 0,000007. Loops sem salto de posição; chão mínimo
-0,000393 unidade e deslizamento compensado máximo 0,000389 por amostra.

**Problemas e como contornei:** importador cria Icosphere para exibir ossos
(excluída da contagem de malha com skin); frames começaram em 1 e deslocavam
timestamps (corrigidos para t=0); importação em FPS 24 distorcia tempo (configurar
120 antes de importar); AABB dava falsos contatos (SAT de OBB); bake 60 Hz não
atingia tolerância no ataque (120, revisão 240). Máscara agora protege olhos em
índice 0 e inclui margens das regiões. Histórico de tentativas fica em
`modelos/_blender/ensaio-01` a `ensaio-04`, sem sobrescrever as anteriores.

**Limitações:** dois avisos de projeção do pivô body fora do envelope estático
de apoio no walk/run; avaliar dinâmica visual. Triagem OBB cobre pares da fixture,
não colisão exaustiva. Atlas por face tem 16,9% de área útil / 47,1% com margens;
empacotamento simples, não otimizado. Helper bípede/repouso específico; sem
transições, blink ou outros planos de corpo. Material procedural não foi usado.
Render Blender e reimportação não provam aparência/importação Roblox.

**Auditoria:** documentação oficial informa suporte a 4K e Pixelated, mas a
mesma página de texturas ainda cita 1024 em UV; discrepância registrada. Orçamento
da fixture/consumidor continua 1024. Soluções aprovadas de cabeça, ampliação,
superamostragem e sangramento não foram removidas. UVs dos três GLBs existentes
conferidas dentro da tolerância histórica; F2 chega a 1,000061. Snapshot de
**236 arquivos** do pavão/exportações: zero alterações desde o início. Status
manual original em documentos/modelos preservado e excluído dos commits.

**Arquivos/comandos:** [sistema](../sistema-blender.md),
[comparação](../comparacao-blender-blockbench.md),
[resultados](../validacao/blender-v1/LEIA-ME.md),
[ensaio JSON](../validacao/blender-v1/ensaio.json).

```powershell
uv run criaturas blender conferir modelos/_blender/minimo-v1
uv run criaturas blender comparar modelos/_blender/minimo-v1 modelos/_blender/minimo-v1-reconstrucao
```

Saídas completas em `modelos/_blender/minimo-v1/` e
`modelos/_blender/minimo-v1-reconstrucao/`, com `criatura.blend`, três GLBs, PNGs,
eventos/locators, GIFs, folha e manifesto de hashes. Entradas/scripts/testes e
evidência curta versionados. Tokens/créditos/custo do chat e esforço do modelo
**não medidos**; tempos dos subprocessos não representam custo artístico recorrente.

**Próximo passo:** B.4 somente quando o usuário fornecer as referências. Congelar
pacote comum e iniciar as duas tentativas sem transferir refinamentos exclusivos.
Fases 10/11 existentes continuam no estado anterior; nenhuma tag de conclusão
dessas fases foi criada.
