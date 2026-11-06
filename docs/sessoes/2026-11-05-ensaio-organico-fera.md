---
tipo: sessao
data: 2026-11-05
fase: ensaio orgânico autorizado
ia: codex
status: rejeitado artisticamente; reconstrução com gabarito em novo ensaio
---

# Ensaio orgânico da preguiça gigante rogue

**Pendência histórica no momento da entrega:** ativar a conexão MCP no Blender
para concluir a conferência solicitada e avaliar a folha de geometria. O modelo
editável e a folha já estão em `modelos/fera-fera-agil-das-sombras/organico-v1/r05/`.
A skill exige “Folha de vistas ainda não aprovada numa criatura real (passo 7)”.
A conexão é necessária para a conferência MCP; cenas abertas com modificações
não salvas não foram substituídas ou alteradas.

**Autorização:** pedido explícito de 05/11: quatro referências, Blender orgânico
com detalhamento, código como autoria, MCP só conferência e monitoramento de uso.
Categoria/estágio/base/rogue já confirmados na sessão anterior. Decisão
[0011](../decisoes/0011-ensaio-organico-blender.md) isola o experimento sem mudar
os backends cubificados, contrato Minecraft ou arquivos anteriores.

**Feito:** entradas/auditoria no commit `3cfff38`. Imagens e hashes, precedência entre vistas e divergências em
`organico-v1/entrada/briefing.json`. Corpo autoral por volumes/lofts fundidos,
relaxamento e redução de apresentação; garras curvas contínuas, olhos, máscara
facial, tufos, manto/cauda, broches, faixas, cinturão, tecido rasgado e bolsa.
Nenhuma geometria do comparativo anterior foi usada. Scripts em
`scripts/fera-organica/` e leitura da entrega em `organico-v1/LEIA-ME.md`.

**Resultado conferido:** 19.516 triângulos visíveis,
corpo de 8.500; mestre preservado com 140.512.
Corpo, cabeça, pescoço, membros, dedos e cauda pertencem a uma superfície conectada,
sem bordas abertas/não manifold e com volume positivo. Reabertura em processo
limpo sem erros. Scripts compilados. Materiais/cores de estudo; não há pintura UV,
retopologia para animação, rig funcional ou importação Roblox aprovados.
A conferência prova integridade em repouso, não equivalência artística ao alvo.

**Revisões:** r01 corrigiu mudança da API de triangulação (índices em vez de vetores);
r02 primeira prévia; r03 corrigiu faixas encobertas/olhos salientes e reduziu o
orçamento; r04 detectou dois fragmentos de voxel de 8 vértices; r05 removeu somente
fragmentos de até 16 vértices e extensão <0,08 unidade, registrou as dimensões,
e refinou juba lateral, nariz e drapeado do manto. Não descartar partes anatômicas
para passar nos gates. r02/r03 preservados; r01/r04 não produziram asset aprovado.
Uma folha por revisão foi inspecionada; imagem avulsa inicial somente para diagnóstico.

**MCP:** `get_addon_status` e `look` do PNG falharam por conexão indisponível.
Zero chamadas de autoria MCP. Validação disponível foi CLI/arquivo e render local;
não alegar leitura da cena viva nem instalar/atualizar addon sem intervenção.

**Auditoria:** baseline é o contador anterior à mensagem deste pedido, não o
início tardio da execução do script. Checkpoints em `organico-v1/auditoria/`.
Até `06-fechamento`: 29.324 entrada sem cache,
5.672.832 cache, 47.721 saída,
5.749.877 total processado. Cache faz parte da entrada;
raciocínio da saída. Inclui preparação e falhas/revisões; não inclui os tokens
posteriores ao checkpoint. Preço e consumo percentual atribuível: indisponíveis.
Limites globais: 46→70% (5 h), 54→58% (semanal); não atribuir exclusivamente ao
ensaio. Sem compras ou geradores 3D pagos. Tempos CLI separados nos `execucao.json`.

**Próximo passo:** conferir por MCP assim que conectado, receber avaliação da
forma e então corrigir a anatomia indicada. Pintura UV/bake, retopologia/rig e
exportação são etapas posteriores; não presumir aprovação por existir `.blend`.
Modelos do pavão/documentos pessoais e cenas abertas permanecem preservados.

## Retorno posterior do usuário

O usuário rejeitou silhueta e textura/cores, embora tenha reconhecido a continuidade
das partes. R05 não está aprovada. Forneceu seis capturas de um modelo consistente
em giro e pediu construção sobre o perfil. Nova direção em
[[2026-11-05-gabarito-silhueta-fera]], decisão 0012 e pasta `gabarito-v1/`.
O arquivo orgânico permanece preservado como tentativa rejeitada.
