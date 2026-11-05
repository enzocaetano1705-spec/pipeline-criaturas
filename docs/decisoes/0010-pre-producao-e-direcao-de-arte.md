---
tipo: decisao
data: 2026-11-05
status: vigente para o piloto; guia visual ainda não aprovado
---

# 0010 — Pré-produção de conceitos separada da tradução 3D

**Contexto:** usuário quer gerar criaturas originais e linhagens a partir de
conceitos, com inspiração principal em Miscrits. Confirmou R$ 50 como teto único,
sem mensalidade nova, e acessos existentes ao Gemini e chat.

**Decisão:** preparar um kit opcional anterior à modelagem, com briefing próprio,
referências curadas, criador/revisor, aprovação humana e ficha canônica por estágio.
O script local só compõe prompts; não escolhe/contrata gerador nem inicia treino.
O guia de mundo é hipótese até curadoria e piloto. Nenhum contrato atual foi
substituído e o kit não é adicionado ao comando `criaturas tudo`.

Antes da arte canônica, o criador pode inventar soluções autorizadas pelo briefing.
Depois da aprovação, vistas/modelagem seguem a imagem como fonte de verdade.
Blender/Blockbench recebem o mesmo pacote congelado. Número de estágios é entrada
(três no exemplo do jogo); o catálogo de referência não o impõe.

LoRA fica como experimento posterior para regularidade visual, condicionado a
gargalo demonstrado, curadoria/permissão de dados e orçamento completo. Não fazer
do treino pesado local um pré-requisito numa GPU de 6 GB nem declarar todas as
alternativas locais impossíveis sem ensaio específico.

**Alternativas descartadas:** treinar primeiro em todo o catálogo; tentar resolver
história/evolução com LoRA de imagem; gerar vistas sem arte/anatomia aprovadas;
agentes autônomos em loop ilimitado. Elas confundem problemas e dificultam avaliar
originalidade, custo e preservação do personagem.

**Consequências:** o piloto funciona por arquivos/conversas e cotas existentes;
automatização de provedores, treino e qualidade artística não foram validados.
Manter até duas revisões por etapa e levar impasses ao usuário. Reversão: retirar
o preparador e kit; nenhum backend depende deles. Ver `docs/direcao-arte/`.

**Complemento em 05/11:** usuário confirmou monge + tartaruga com arquétipo
rogue e forneceu sete referências por função. O arquétipo entra como campo
obrigatório no briefing e critério de revisão. A quantidade pode ficar nula na
exploração textual e deve ser definida antes de aprovação de arte/vistas.
Regra já confirmada no jogo, consultada somente para leitura: Comum 1 forma,
Raro 2, Épico em diante 3. Isso corrige a suposição inicial de três por padrão;
não atribui raridade ao piloto nem muda a regra do consumidor.
