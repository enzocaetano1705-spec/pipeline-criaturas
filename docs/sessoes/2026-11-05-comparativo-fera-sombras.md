---
tipo: sessao
data: 2026-11-05
fase: B.4 — primeira geometria comparativa
ia: codex
modelo: ID exato e esforço não expostos
status: duas geometrias editáveis; aguardando aprovação da folha
---

# Preguiça gigante rogue — comparação Blockbench e Blender

**Pergunta para o usuário (parada na folha de geometria):** aprova as formas e
proporções de alguma tentativa, ou quais partes devem mudar? Folha atual:
`modelos/fera-fera-agil-das-sombras/comparativo-v1/comparativo-geometria-v3.png`.
As cores são de bloqueio; pintura final e rig dependem da revisão. A skill exige
“Folha de vistas ainda não aprovada numa criatura real (passo 7)”.

**Entradas confirmadas:** conceito declarado satisfatório pelo usuário; forma
**3 de 3**; base **preguiça gigante**, arquétipo **rogue**. Categoria técnica
**bípede com cauda › outros**, pois a tabela não tem nicho de preguiça.
Isso substitui a sugestão inicial canídea; não repetir aquela pergunta.

**Feito:** imagem preservada, SHA-256
`baa929fdfc84418ad325c49e14676acb4b33f7dabbca3b943805330d7fb6231d`.
Briefing, paleta amostrada, grade, leitura semântica da vista real e manifesto em
`modelos/fera-fera-agil-das-sombras/comparativo-v1/entrada/`.
Ficha criada com e3; F1/F2 continuam indefinidas. A vista oblíqua **não** foi
relabelada como frente para satisfazer o medidor. Profundidades e continuidade
oculta são estimativas de autoria para revisão, não medidas de uma vista inexistente.
Os scripts de autoria isolada constroem os lotes/volumes a partir desse briefing.

**Arquivos atuais:** caminhos abaixo relativos a
`modelos/fera-fera-agil-das-sombras/comparativo-v1/`:

- `blockbench-v3/fera-sombras-e3-blockbench-v3.bbmodel`.
- `blender-v3/fera-sombras-e3-blender-v3.blend`.
- `comparativo-geometria-v3.png`: conceito, 3/4, frente, lado e costas de cada autoria.

Ambos possuem **59 elementos: 43 volumes e 16 planos**, em 21 grupos.
Poucos volumes por massa, garras angulares de três dedos, planos largos para
juba/tecidos; rosto e marca do peito pintados diretamente nos volumes.
As v1/v2 internas estão preservadas, sem aprovação humana presumida.

**Referências consultadas:** Weregarurumon real do Digimod, render headless e
inspeção estrutural (27 peças, 18 volumes, 9 planos, atlas 80²), para economia de
membros e rosto pintado; estudo existente de Koromon para planos recortados.
Originais/renders/atlas permanecem na biblioteca externa em Downloads.
Nenhum arquivo de geometria/textura/animação de terceiro foi incorporado.

**Comparação:** autoria A via operações `bbmodel_edit` no motor separado;
autoria B por malhas cubificadas nativas Blender, com plano próprio.
Não foi convertido o modelo A para fabricar B. A geometria B é congelada antes
da leitura do resultado A pelo preparador de render. Funções utilitárias e regras
de cores são compartilhadas. Mesmo agente/contexto e revisões internas conjuntas:
**não é benchmark cego** entre agentes. Não inferir qualidade/custo recorrente.

Ambas as geometrias foram renderizadas no **Blender EEVEE**, com mesma câmera
ortográfica, alvo, escala, luz e densidade visual de 1 pixel/unidade. A folha
identifica autoria e renderizador; não é captura da interface Blockbench.
O `.blend` nativo foi salvo antes de adicionar A à cena temporária de apresentação.
A cena da janela Blender atual não foi alterada.

**Conferência:** Blockbench **0 erros**, **0 peças soltas**, **0 alertas de
espelhamento**, com **57 avisos de interpenetração** preservados no relatório:
articulações e massas da cabeça/juba/colar/roupa se sobrepõem; contatos precisam
de revisão antes da animação. Não declarar rig concluído. Blockbench instalado
5.2.2 é compatível com o formato 5.0 do arquivo entregue.
Blender **5.1.1**, reaberto em processo limpo: 59 malhas, 21 grupos de edição,
atlas empacotado, UVs dentro do atlas, **0 erros** e geometria igual ao plano
congelado. Os grupos ainda não são armature. Ver relatórios JSON junto aos arquivos.
Compilação dos scripts conferida; suíte geral não repetida para esta autoria isolada.

**Revisões:** v1 construção inicial; v2 corrigiu marcas ocultas, ancoragem do tecido
e índices dos dedos; v3 transferiu máscara facial/peito para pintura direta,
eliminando adesivos sobrepostos. Correções comuns aplicadas às duas tentativas.
Uma folha por revisão foi inspecionada. Nenhum original editado à mão foi sobrescrito.
A falha inicial de `zoneinfo` foi contornada sem instalar nada, usando UTC−03:00.
Token/crédito/custo do chat não medido. Sem exportação/integração Roblox nesta etapa.

**Decisões:** mantidos [backend opcional](../decisoes/0009-backend-blender-opcional.md)
e [protocolo comparativo](../comparacao-blender-blockbench.md); nenhuma mudança
de arquitetura ou relaxamento da proteção do backend sintético. Scripts desta
criatura ficam em `scripts/comparativo-fera/`. Documentos pessoais e modelos do
pavão editados pelo usuário permanecem fora do commit.

**Próximo passo:** receber avaliação/aprovação das duas folhas; ajustar as partes
indicadas e contatos; depois completar pintura/rig conforme o escopo escolhido.
B.4 permanece aberta, sem tag de fase. Nenhuma aprovação visual ou de Studio presumida.
