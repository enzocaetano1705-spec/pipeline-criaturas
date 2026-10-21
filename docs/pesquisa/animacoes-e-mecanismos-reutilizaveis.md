---
tags: [pesquisa, animacao, referencias, pipeline-criaturas]
data: 2026-10-21
status: consulta
---

# Animações e mecanismos reutilizáveis

Estudo do tutorial indicado pelo usuário, das páginas oficiais relacionadas e dos arquivos locais do The Digimod no commit `744e72e970ae33a77acd241221e917f6f3d5258a`. Esta nota registra mecanismos e observações, sem incorporar geometria, textura ou chaves das referências.

## O que o tutorial oferece

O [tutorial de modelagem](https://wiki.cobblemon.com/index.php/Tutorials/Creating_A_Model) orienta Bedrock Entity, Box UV, grupos como ossos, pivô da raiz na origem e uma parte associada ao olhar. Modelos de estrutura semelhante são referências para organizar ossos. Ele lista estados e nomes de clipes; a documentação de **Poser** é que apresenta os mecanismos procedurais prontos.

## Clipes, posers e animações prontas são coisas diferentes

- **Clipe:** curvas de rotação, posição e escala aplicadas aos ossos; pode conter chaves numéricas ou expressões.
- **Pose:** estado como parado, andando, voando ou dormindo. **Poser:** seleciona clipes e comportamentos conforme esse estado. `q.bedrock` chama um clipe; `q.bedrock_stateful` sobrepõe movimento parcial e `q.bedrock_primary` toma controle da animação principal.
- **Quirk:** programa ocorrências ocasionais, como piscar ou mexer uma parte; pode escolher entre clipes com `q.array`. O agendamento e a prioridade pertencem ao jogo.
- **Placeholders procedurais:** `q.quadruped_walk`, `q.biped_walk`, `q.bimanual_swing` e `q.sine_wing_flap` geram movimentos simples a partir dos ossos e parâmetros. `q.look` acompanha um alvo. Não são coleções universais de keyframes para importar.

Os nomes dos ossos e a raiz precisam corresponder ao modelo. Fonte: [Poser — poses, quirks, olhar e placeholders](https://wiki.cobblemon.com/index.php/Poser).

## Olhos pintados também podem mudar de expressão

Cobblemon oferece camadas de textura com uma sequência de PNGs, FPS e loop, seguindo o UV do modelo. É um caminho para detalhes animados sem um cubo por detalhe. Aplicar isso a piscadas é uma **possibilidade de implementação**, não uma piscada já pronta no pavão. Fonte: [Animated Textures](https://wiki.cobblemon.com/index.php/Tutorials/Animated_Textures).

O [tutorial de substituição de animações](https://wiki.cobblemon.com/index.php/Tutorials/Animation_Replacement) também mostra que geometria, textura, clipes, resolver e poser são componentes distintos. Encontrar o arquivo de animação não garante reproduzir o comportamento completo.

## Observação real: Koromon

Fontes: [dados de Koromon](https://github.com/themodderg/The-Digimod/blob/744e72e970ae33a77acd241221e917f6f3d5258a/src/main/resources/data/thedigimod/digimon/koromon.json) e [biblioteca de animações](https://github.com/themodderg/The-Digimod/blob/744e72e970ae33a77acd241221e917f6f3d5258a/src/main/resources/assets/thedigimod/animations/digimons_anims.json), conferidas nos arquivos baixados em `Downloads/referencias-criaturas/the-digimod/`.

- Koromon é `evo_stage: 1`, com movimento de solo, e escolhe seis nomes: `idle6`, `sit7`, `walk4`, `fly`, `attack2`, `shoot4`.
- A biblioteca tem **83 clipes**. O `.bbmodel` incorpora muitos clipes compartilhados; essa lista no editor não significa que todos sejam usados por Koromon.
- A geometria exportada de Koromon contém somente `entity` e `body`. Algumas trilhas da biblioteca citam outras partes; não se deve presumir que todos os canais tenham alvos nessa criatura. O nome `fly` na configuração tampouco autoriza inventar asas.

| Referência escolhida | O que existe no arquivo | Aplicação candidata ao pavão |
|---|---|---|
| `idle6` | Loop; escala de `entity`, mais rotações de partes; expressões com `query.anim_time` | Respiração do volume completo; mapear raiz e ajustar contato com o chão |
| `walk4` | Loop; posição, rotação e escala de `body`, com trilhas de `ear`/`ear2`; usa `query.anim_time` | Locomoção do corpo sem pernas; desenhar balanço próprio para as penas |
| `attack2` | Ação de duração 1,6875 s; canais em `entity`, `body` e `top` | Base de estudo para antecipação e impulso corporal; avaliar alvos existentes |

As correspondências da última coluna são **inferências para adaptação**, ainda não animações implementadas. O mapeamento semântico inicial é `entity` → `root`, `body` → `body`. O pavão tem três ossos por pena; esses segmentos não equivalem automaticamente a orelhas do modelo de referência.

## O que realmente pode ir para Blockbench e Roblox

1. **Validar o rig antes do movimento:** hierarquia, pose de repouso, pivôs, eixo de frente e escala. Igualar nomes sem igualar a função do osso produz resultados diferentes.
2. **Separar referência e execução:** aprender a estrutura e o ritmo; recriar ou adaptar os movimentos permitidos sobre o rig de destino. Neste projeto, não incorporar arquivos de animação de terceiros no repositório.
3. **Assar quando necessário:** fórmulas de tempo podem ser amostradas em chaves numéricas. Expressões que dependem de velocidade, alvo ou estado precisam de parâmetros de exemplo definidos, ou de um comportamento próprio no jogo. `q.look`, quirks e seleção de poses não são resolvidos apenas exportando glTF.
4. **Conferir a saída:** primeiro/último quadro do loop, contato com o chão, conexão dos apêndices e amplitude. Verificar escala e interpolação no importador de destino; um preview correto no Blockbench não comprova a reprodução no Roblox.

O pipeline já segue a ideia procedural em `ferramenta/criaturas/animar.py`: funções por plano de corpo são amostradas em chaves; `walk` sem pernas gera pulos; correção de chão é calculada por quadro. Duas lacunas encontradas neste estudo foram corrigidas: `feather_*` com geometria recebe balanço secundário em idle/walk, sem habilitar voo; olhos/pálpebras vazios ou ocultos não produzem um `blink` sem efeito. Olhos pintados continuam exigindo um mecanismo próprio de expressão.

**Próximo uso recomendado:** estudar Koromon com uma folha de vistas e um ciclo de movimento; escolher somente os canais compatíveis; produzir idle e locomoção próprios para o pavão, com balanço das penas e verificação de chão. Resolver a expressão dos olhos como textura animada ou mecanismo explícito do destino.
