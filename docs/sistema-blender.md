---
tipo: sistema
data: 2026-11-04
status: backend opcional; fixture sintética
---

# Autoria cubificada com Blender

O backend adicional é chamado explicitamente por `criaturas blender`. Os comandos
Blockbench e `criaturas tudo` continuam com seu funcionamento anterior. A decisão
[0009](decisoes/0009-backend-blender-opcional.md) delimita o experimento. Esta versão
não gera a próxima criatura real: ela valida a construção independente com uma
fixture original, sem importar geometria/animações do pavão.

## Reconstruir

Na raiz do repositório, com dependências do projeto e Blender já instalados:

```powershell
uv run criaturas blender construir ferramenta/testes/sinteticos/blender-bipede.json --saida modelos/_blender/minimo-v1
uv run criaturas blender conferir modelos/_blender/minimo-v1
uv run criaturas blender construir ferramenta/testes/sinteticos/blender-bipede.json --saida modelos/_blender/minimo-v1-reconstrucao
uv run criaturas blender comparar modelos/_blender/minimo-v1 modelos/_blender/minimo-v1-reconstrucao
```

Toda pasta de saída deve ser **nova**. Não existe `--force`; nunca sobrescrever
um `.blend` ou artefato editado. As saídas de fixture sob `modelos/_blender/` são
ignoradas pelo Git; a entrada, scripts, testes e evidência curta são versionados.

Descoberta do executável: `--executavel`, depois `CRIATURAS_BLENDER`, PATH, pasta
`Program Files/Blender Foundation`. O ensaio foi desenvolvido no Blender 5.1.1;
outra versão precisa passar a integração. Falta de Blender ou validador é erro
antes de criar artefatos; instalar requer intervenção conforme AGENTS.md.

O processo efetivo é `blender --background --factory-startup --disable-autoexec
--threads 2 --python-exit-code 1 --python <worker.py> -- construir <pasta>`.
Um segundo processo limpo faz `reimportar`. Não há acesso à cena do Blender aberto,
mouse, foco, MCP do Studio ou escrita no repositório do jogo. Os logs ficam no
disco e a CLI imprime um resumo curto. Erros deixam `falha.json` para diagnóstico.

## Entradas e etapas

| Etapa | Entrada/saída | Responsabilidade |
|---|---|---|
| Briefing | `briefing`, estágio e categoria -> `briefing.json` | intenção, restrições e destino |
| Interpretação | `interpretacao` -> `interpretacao.json` | partes, proporções, incertezas; imagem em produção |
| Plano | `plano` -> `plano-cubos.json` | contrato compartilhado, pivôs absolutos, hierarquia e poucas formas |
| Atlas/malha | `textura`/`limites` -> `atlas.json`, `malha.json`, PNGs/máscara | densidade por face, empacotamento, margens e volumes |
| Autoria | scripts Python -> `criatura.blend` | uma malha rígida, armature, locators e clipes assados |
| Revisão | `validacao-autoria.json`, `amostras-autoria.json`, folha/GIFs | medidas e render identificado como Blender |
| Exportação | três GLBs, `animacoes.json`, `locators.json`, `entrega-roblox.json` | contrato de entrega e variantes |
| Ida/volta | `validacao-glb.json`, `validacao-reimportacao.json` | validar o arquivo e reimportar em processo limpo |
| Proveniência | `manifesto.json`, `relatorio.json`, `reconstrucao.json` | hashes, parâmetros, ambiente, tempo e limitações |

A fixture é o exemplo executável do formato v1. `entrada.py` valida o plano com
`plano_cubos.schema.json` existente e acrescenta invariantes específicos, sem
afrouxar os contratos atuais. Os locators são gerados por `rig.locators` quando
ausentes; `loc_ground` acompanha root, sem respiração do body. Campos de cubo
não implementados são recusados (rotação óssea de repouso, inflate, UV prévio ou
mirror não são silenciosamente descartados). A v1 aceita pernas verticais no
repouso; outro esqueleto precisa de helper e ensaio próprio.

## Geometria, UV, textura e material

Uma caixa por volume descrito, sem arredondamento, subdivisão ou microcubos.
Cada cubo possui oito vértices de autoria e seis faces externas com normais planas.
Costuras UV/normais separam vértices na exportação, sem alterar a forma. Planos
recebem espessura explícita para formar volumes fechados; isso pertence ao adapter
Blender, não altera Minecraft. Uma influência com peso 1 em cada vértice; root e
Raiz não influenciam a geometria.

Atlas determinístico por face, densidade explícita, dimensões arredondadas para
texels inteiros e margem duplicada. Falta de espaço falha; não reduzir densidade
automaticamente. Na fixture: 128², 2 px/unidade, margem 2 px e exportação ×8 para
1024². `atlas.json` lista retângulos, ocupação útil e densidade. O strip mínimo de
faces laterais da lâmina é um texel. Aumentar PNG por nearest só repete pixels.

`mascara-regioes.png` usa índices documentados no atlas. As variantes âmbar/violeta
mudam só regiões mutáveis; bico, pés e olhos permanecem idênticos. Pintura de olhos
e recorte losango são **operações explícitas da fixture**, não anatomia inferida.
Recorte tem RGB de borda sob alfa zero; margem não invade outras ilhas. Os testes
conferem alfa, bordas, recoloração e ampliação sem interpolação.

Material único Principled PBR com metallic 0, roughness 1, base color PNG e alfa.
Não usa shader exclusivo no arquivo de destino nem exige bake de procedural.
GLB carrega PNG idêntico à entrega, sampler nearest e nearest-mipmap-nearest.
O comportamento real do filtro no Roblox requer o ensaio do motor. Pesquisa e
pressupostos históricos estão na [auditoria](pesquisa/auditoria-textura-roblox-blender.md).

## Rig e movimento

`Raiz` é um wrapper estático de exportação; abaixo dele, `root -> body`. A anatomia
da fixture tem head/bico/crista, braços, pernas `leg -> shin -> foot` e dois ossos
de cauda. Pivôs estão nas juntas, em coordenadas absolutas do plano. No Blender,
todos os eixos ósseos de repouso são identidade; a conversão de base do glTF pode
ficar no wrapper. Não girar esse wrapper artisticamente no preparo do Studio.

`movimento.py` é independente de bpy e gera matrizes canônicas. A IK de dois
segmentos resolve joelho/tornozelo a partir do alvo; comprimentos rígidos não
mudam. O bake grava localização/quaternion locais, hemisfério contínuo e curvas
lineares. Nenhuma constraint ou expressão precisa existir no destino.

- `idle`: respiração, cabeça e cauda secundárias, pés fixos.
- `walk`: trajetória de apoio com avanço compensável, retorno Hermite e lift suave,
  transferência lateral, oscilação/pitch do corpo e braços alternados.
- `run`: passada mais longa, corpo mais baixo/inclinado, maior lift e ritmo próprio.
- `attack_physical`: antecipação, investida/cabeçada, impacto e recuperação, pés
  firmes. Eventos em segundos e mapa `attack_basic -> attack_physical` no sidecar.

Os clipes de locomoção são in-place. Velocidade de avanço coerente é
`passo/(fracao_apoio*duracao)/16` studs/s na escala 1. O teste de apoio compensa
esse avanço; pé que se move para trás num clipe in-place não é escorregamento por si.
O v1 não implementa transições start/stop, combate complexo, blink, mutações do
jogo ou todos os planos de corpo. O conjunto mínimo aqui é o solicitado para a fixture.

## O que é validado e o que depende de arte/motor

Testes host: entradas inválidas, hierarquia/ciclos, limites, normais/volumes,
orçamento/margens de UV, máscaras, cores protegidas, alfa, ampliação, IK e derivada
analítica dos loops. Geração Blender: amostras a 240 Hz, incluindo meios de frame
entre chaves a 120 Hz, conferem geometria avaliada, alvo do pé, chão, saltos entre
amostras, loop e apoio compensado. Relatórios registram também diferença de
velocidade finita na borda; ela inclui aceleração, não prova um flick sozinha.

A triagem de colisão usa SAT de caixas orientadas em pares de risco da fixture:
braços/corpo, pés entre si, cabeça/cauda. Não é colisão exaustiva ou simulação física.
Equilíbrio usa projeção do pivô body sobre o envelope dos pés em apoio; não é
centro de massa nem estabilidade dinâmica. Avisos dessa heurística ficam visíveis
para revisão e não aprovam peso/personalidade automaticamente.

Khronos valida estrutura glTF. Verificações próprias conferem uma malha/material,
skin rígida, hierarquia, nomes, clipes/durações, quaternions, eixos de entrega,
UV dentro do atlas e PNG embutido. A reimportação usa FPS correto **antes** de
importar (o Blender transforma segundos em frames nesse momento) e exclui somente
a malha auxiliar de exibição dos ossos. Compara superfícies e pivôs ao longo dos
quatro clipes. Nós locators e sidecar permitem reconstruir Attachments; existência
de empty em glTF não garante que Studio o manterá.

```powershell
uv run pytest ferramenta/testes/test_blender_backend.py -q
$env:CRIATURAS_TESTAR_BLENDER = '1'
uv run pytest ferramenta/testes/test_blender_backend.py -q
Remove-Item Env:CRIATURAS_TESTAR_BLENDER
uv run pytest -q -k 'not test_exporta_roblox_glb_valido'
```

A integração opt-in reconstrói duas vezes, valida ambos e compara semântica e
GLBs, além de detectar alteração posterior num artefato. A exclusão do último
comando evita acionar o Blockbench desktop enquanto o usuário usa o computador;
não exclui os testes headless do fluxo existente. Não há teste Studio nesta sessão.

`manifesto.json` registra hash de entrada, scripts, executável Blender, artefatos,
versão/build, comandos, seed nula (algoritmo determinístico), revisão base e tempos.
`conferir` detecta edição de artefatos; script alterado é relatado como versão
diferente. Comparação semântica ignora bytes internos do `.blend` e tempos, mas
inclui plano, atlas, geometria e poses completas; GLBs são comparados à parte.

## Entregar para Roblox posteriormente

Importar o GLB de fixture num laboratório autorizado, Rig Type Custom. Conferir
MeshPart única com Bones, raiz física imóvel, body animando, escala e frente pelo
bico. Aplicar SurfaceAppearance com o atlas de entrega, AlphaMode Transparency,
ResampleMode Pixelated e mapas foscos quando necessários no destino. Criar
AnimationController/Animator, Hitbox orientada para a frente e Attachments dos
locators. Os eventos permanecem no JSON, não são eventos glTF padronizados.

`entrega-roblox.json` registra a escala de entrega (1/16 stud por unidade), altura
de repouso e mapas de nomes. Não acrescenta fixture ao catálogo de produção nem
altera receitas aprovadas do pavão. Arquivo/Blender validado não equivale a
aprovação artística ou importação testada no Roblox. O
[protocolo comparativo](comparacao-blender-blockbench.md) define o ensaio futuro.

**Retomada:** aguardar imagens, prompt, estágio/categoria da primeira criatura
comparativa. Confirmar categoria e folha conforme skill. Preparar o adapter dessa
anatomia a partir das entradas congeladas, sem copiar a solução final da outra tentativa.
