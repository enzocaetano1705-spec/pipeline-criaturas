---
tipo: decisao
data: 2026-10-21
status: vigente
---

# 0005 — Referências por estrutura antes da modelagem

**Contexto:** o usuário propôs estudar a relação entre ilustração, aparência no Blockbench, número de elementos, volumes, pintura, rig e representação JSON. Bibliotecas reais de Cobblemon e The Digimod já estão disponíveis localmente. Escolher um orçamento por categoria, sem examinar como modelos refinados resolvem formas parecidas, não basta.

**Decisão:** introduzir consulta e inspeção estrutural no workflow, antes da primeira geometria e para problemas concretos de revisão. Escolher poucos casos por anatomia e função (corpo, penas, locomoção), conferir vistas e atlas reais e registrar a estratégia de tradução. Estudos completos e originais ficam na biblioteca externa; o pipeline conserva mecanismos, conclusões e dados agregados.

**Aplicação inicial:** estudo de Koromon com ilustração fornecida, cinco vistas renderizadas no motor Blockbench, atlas e inspeção de grupos/UV. O arquivo tem 2 volumes e 4 planos, e a espécie seleciona seis animações de uma biblioteca maior. A solução de simplificação serve de referência para o pavão; não é necessário incorporar o asset de Koromon ao modelo próprio.

**Mecanismos:** `criaturas referencias` encontra e resume casos reais. `leitura.modelagem.abordagem: poucas_formas` desativa a expansão automática de volumes em fatias; leituras antigas preservam o comportamento anterior. `silhueta_fatiada` continua disponível quando necessária. A geometria permanece produzida por lotes do motor.

**Animação:** conferir papéis, pivôs, ossos com geometria e dependências antes de adaptar movimentos. Clipes incorporados, clipes usados pela espécie, posers/quirks e texturas animadas são componentes diferentes. Fórmulas de tempo compatíveis podem ser assadas; estado do jogo e olhar para um alvo não surgem apenas exportando glTF. Piscar em um osso vazio não conta como uma piscada implementada.

**Consequências:** a skill ganha `referencias.md`; Obsidian e CLI apontam para os estudos e o catálogo. A decisão complementa a direção artística 0004 e esclarece o estudo previsto em 0001; não altera a separação entre assets de terceiros e criaturas originais. Não exige consultar centenas de arquivos nem pedir aprovação a cada referência.
