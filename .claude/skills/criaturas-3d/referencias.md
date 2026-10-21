# Modelar com referências reais

Use antes da primeira geometria de uma criatura, ou quando uma revisão mostrar que falta uma solução de forma, textura ou movimento. O objetivo é decidir **como traduzir a imagem com poucas peças**, comparando ilustração, modelo renderizado, atlas e estrutura do arquivo. Não repetir a pesquisa em cada ajuste: reutilize o estudo já conferido.

## Encontrar um caso próximo

A biblioteca local fica, por padrão, em `~/Downloads/referencias-criaturas/`. Use `--biblioteca` para outra pasta. Os originais e os estudos visuais permanecem nela; não entram no repositório do pipeline.

```
uv run criaturas referencias listar --limite 8
uv run criaturas referencias buscar koromon
uv run criaturas referencias buscar --tag penas --limite 5
uv run criaturas referencias inspecionar "<caminho do .bbmodel>" --saida "<biblioteca>/estudos/<nome>/estrutura.json"
```

Escolha poucos casos e dê uma função a cada um: por exemplo, **Koromon para o corpo baby**, uma ave para as penas e um clipe de locomoção para o movimento. Anatomia e pose importam mais que o nome ou o parentesco. Tags automáticas são pistas justificadas por nomes de partes; a imagem e a inspeção confirmam se servem.

As buscas preservam os modelos e mantêm um cache agregado na biblioteca. Em uma inspeção de arquivo isolado, use `--dados <json da espécie>` e `--animacoes <biblioteca de clipes>` para conferir a seleção efetivamente usada; a ausência desses dados não significa que a espécie não use animações.

Se a biblioteca não tiver o caso necessário, procure uma ilustração oficial e uma fonte pública do modelo. Registre origem e versão; mantenha a licença junto ao arquivo. Não baixe outro catálogo inteiro para resolver uma parte.

## Estudar o que de fato está no modelo

1. **Ilustração → volumes:** quais características dão identidade? Onde a tradução abandona a curvatura literal? Conte separadamente volumes e planos, sem confundir os dois com ossos ou locators.
2. **Vistas → silhueta:** consulte ou gere uma folha de até 768 px com frente, lado, costas e 3/4; acrescente cima quando resolver uma dúvida. Use render real do Blockbench/headless e mantenha o original intacto. Não confunda screenshot enviado pelo usuário com o arquivo efetivamente baixado.
3. **Atlas → detalhe:** observe o que é rosto pintado, recorte alfa, face interna transparente, ilha compartilhada e sombreamento pintado. Uma faixa larga transparente pode desenhar dois apêndices sem dois conjuntos de cubos. Face interna transparente não é, por si, buraco externo.
4. **Código → organização:** leia o resumo estrutural e só os trechos necessários do JSON. Verifique hierarquia, função dos pivôs, rotação de repouso, UV, densidade e quais elementos realmente têm geometria. As versões 4.x e 5.x do `.bbmodel` guardam grupos de formas diferentes; não concluir que um modelo tem zero ossos só por faltar `groups`.
5. **Animação → mecanismo:** diferencie clipes que o arquivo incorpora dos que a espécie usa. Confira alvos existentes, pivôs, fórmulas e dependências do jogo. Ver [animações e mecanismos reutilizáveis](../../docs/pesquisa/animacoes-e-mecanismos-reutilizaveis.md).

O estudo de Koromon desta máquina está em `~/Downloads/referencias-criaturas/estudos/koromon/`: ilustração fornecida pelo usuário, vistas do arquivo real e atlas lado a lado. Ele usa **2 volumes e 4 planos**; a configuração da espécie seleciona seis nomes da biblioteca compartilhada. Isso é um caso estudado, não uma receita obrigatória para todo baby.

Se um render de `.bbmodel` 4.x acusar `MISSING_GROUP` ou perder a pose dos apêndices, converta **uma cópia na biblioteca externa** para 5.x com `bbmodel_convert_legacy` antes de renderizar. Confira a hierarquia e o resultado; não normalize o original no lugar nem aceite uma vista que ignorou grupos antigos.

## Transformar estudo em um plano próprio

Registre a estratégia em `leitura.json`, sem coordenadas ou chaves copiadas de terceiros:

```json
"modelagem": {
  "abordagem": "poucas_formas",
  "justificativa": "Corpo baby resolvido por grandes volumes; rosto e pequenos detalhes pintados; penas por planos recortados.",
  "referencias": [
    {"nome": "Koromon", "papel": "economia de volumes e rosto pintado", "caminho": "<biblioteca>/estudos/koromon/estudo-koromon.md"}
  ]
}
```

`poucas_formas` mantém um cubo por volume descrito e não transforma o contorno redondo em várias fatias automáticas. Se duas formas grandes forem necessárias, descreva duas partes próprias. `silhueta_fatiada` preserva a alternativa detalhada; use quando a revisão justificar esse custo. A imagem do usuário continua decidindo quais partes e proporções existem.

Adapte **a solução**: família estrutural, número e função dos volumes, uso de planos, estratégia de pintura, organização dos ossos e ritmo do movimento. Crie operações e textura próprias para a criatura. Para modelos já corrigidos ou pintados, use `aplicar`; não rode `cubificar` para reconstruir tudo apenas para adicionar a estratégia.

## Conferir movimentos reaproveitáveis

- Faça um mapa de papéis, por exemplo raiz→raiz e corpo→corpo; confira também pivôs, eixos, escala e pose de repouso.
- Um osso vazio não produz uma piscada visível. Olhos pintados precisam de uma solução explícita de textura/expressão; não declarar um `blink` só porque o nome existe.
- Penas ornamentais não viram asas. Movimento secundário discreto pode ser próprio, sem incorporar uma biblioteca inteira.
- Fórmulas e mecanismos do Cobblemon/Digimod não são automaticamente portáveis para Roblox. Assar as funções compatíveis em chaves numéricas, testar loop e contato com o chão; seleção de estado e olhar para alvos continuam comportamentos do jogo.
- Compare um ciclo com a referência e valide o modelo de destino. Quantidade de clipes não é critério de qualidade.

## Critério para a revisão

Mostre a criatura original e a tradução, com uma frase justificando as peças: volumes que sustentam a silhueta, planos que recortam os apêndices e detalhes que a textura resolve. Confira identidade, proporções, frente/lado e leitura do rosto antes de aumentar a contagem. Use as aprovações já fornecidas pelo usuário e os pontos de revisão da skill; não transforme cada consulta à biblioteca em nova pergunta.
