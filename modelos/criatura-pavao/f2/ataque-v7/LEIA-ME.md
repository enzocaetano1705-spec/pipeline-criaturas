# F2 v7 — catapulta pela cauda

Proposta para avaliar **somente `attack_tail_kick`** no Blockbench.
Pisão v4 e spin v5 já aprovados; seus clipes permanecem preservados.

## Movimento

1. Recuo e rolagem sobre as pontas dos dedos, com os calcanhares subindo.
2. Patas deixam o piso; quadril, ligação do torso e peito recuam sobre a cauda.
3. Curva carregada se distribui pela cauda, sem uma junta fazendo uma dobra de 90°.
4. Descarga lança o corpo para cima e para a frente, inicialmente recolhido.
5. Patas estendem no início do lançamento; peito, cabeça, braços e plumagem acompanham.
6. Recolhimento, pouso com absorção e passos para a posição inicial.

O efeito elástico é a coreografia fictícia solicitada, não uma simulação de canguru real.
A linha de ataque acompanha o corpo durante o voo: não existe alvo de pata preso ao Y do peito em repouso.

## Arquivos

- `criatura-pavao-e2-ataque-v7.bbmodel`: nova versão, 2,70 s, chaves a 120 Hz.
- `previa-catapulta.gif`: duas vistas a 1×, 50 fps; pausa final de 0,30 s.
- `poses-catapulta.png`: fases no arquivo salvo, com enquadramento comum.
- `catapulta.ops.json`: lote enviado ao motor externo.
- `proveniencia.json`: hashes de entrada/saída; proteção de versões editadas à mão.
- `medidas-catapulta.json`: conferência densa de superfícies, apoio, curva e voo.
- `aprovados-preservados.json`: comparação dos clipes preservados e do recorte de UV.
- `validacao-estrutura.json` e `validacao-ataque.json`: diagnósticos do motor.
- `animacoes.json`: marcadores propostos; ainda não integrados ao gameplay.

## Rig e preservação

Os dois cubos sólidos da cauda foram subdivididos em três trechos cada: **63 cubos/52 grupos**.
Não há apêndice novo nem mudança das proporções em repouso. As UVs das faces externas foram
recortadas proporcionalmente sobre o mesmo atlas, sem repintura. Faces internas fecham os trechos
durante a flexão e ficam ocultas em repouso e nos clipes anteriores. UV por face nesses seis cubos;
o formato continua Bedrock. Pivôs dorsais evitam abrir fendas na borda externa da curva.

As quatro articulações adicionais ficam neutras em idle, walk, pisão e spin. As chaves anteriores
não são reescritas. A conferência compara os mesmos pontos materiais nas matrizes antiga/nova
de cada trecho, além de verificar partição contígua, UV e atlas. Isso cobre também a cauda subdividida,
em vez de exigir a mesma contagem de cubos.

Na carga, o quadril alinha a raiz da cauda e o torso acompanha a transferência. Abertura do leque
permanece constante; as penas giram pelas bases. Penas do tornozelo abrem 18° neste clipe para
liberar os dedos. Não se usam escalas nem alongamento de membros.

## Limites

A trajetória aérea recebe a velocidade da descarga, com continuação balística visual.
Unidades/gravidade são do modelo, não parâmetros físicos do Roblox. O centro dos volumes sólidos
é apenas uma aproximação visual da distribuição do corpo; não mede massa real.
O diagnóstico genérico de chão considera inclusive regiões transparentes de penas: conferir
o relatório por alfa para distinguir esse aviso de uma superfície visível atravessando o piso.

Reutiliza o estudo de movimento documentado na v5 e a IK anatômica existente. Esta revisão não
altera o pipeline geral nem a colisão/runtime. A avaliação artística do usuário continua pendente;
exportar para Roblox depois da aprovação do ataque.

Reproduzir:

```powershell
uv run python scripts/animar-catapulta-pavao-f2-v7.py --medir
uv run python scripts/revisar-catapulta-pavao-f2-v7.py
```

Gerar pela primeira vez sem `--medir`; `--refazer` só substitui uma saída gerada cujo hash não mudou.
A fonte manual do usuário e as versões anteriores não são sobrescritas.
