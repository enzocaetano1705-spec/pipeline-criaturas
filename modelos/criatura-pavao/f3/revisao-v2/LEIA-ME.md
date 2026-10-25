# Pavão F3 — reconstrução v2

**Proposta para revisão artística.** A v1 foi rejeitada pelo usuário com 3/10.
O arquivo anterior, que recebeu tentativas de edição manual e remoção de textura,
foi preservado. Abra `criatura-pavao-e3-v2b.bbmodel` para esta reconstrução.
`criatura-pavao-e3-v2.bbmodel` é o estudo intermediário aberto durante a revisão;
a v2b corrige a orientação da pena caudal central nas costas e é a proposta atual.

## Referências e leitura

As quatro referências novas estão preservadas em `docs/criaturas/criatura-pavao/revisao-f3/`.
Frente e perfil orientam as proporções; as artes originais mantêm a identidade da
criatura. Garras adicionais e o microvoxelamento dos redesenhos não foram adotados.
Os arquivos de origem/hashes estão em `imagens-fonte.json`.

Refeitos corpo, cabeça/bico, cintura/quadril, membros, pés, crista, lâminas e leque.
As lâminas começam acima dos cotovelos e descem para fora/para trás; o leque combina
três penas mais verticais e três posteriores, para leitura frontal e lateral.
As penas principais são volumes de espessura 0,7–0,9 unidade, com haste, lâmina
grande e ponta em diagonal. Não são contornos voxelizados pixel por pixel.
Garras apenas nos pés; mãos escuras com três dedos e polegar, sem garras extras.

## Arquivos de revisão

- `comparacao.png`: referência/modelo de frente e de perfil aproximado.
- `massas.png`: vista 3/4 cinza, para avaliar volumes sem as cores.
- `cameras.json`: posições, alvos e FOV para repetir os enquadramentos.
- `textura.png`: cópia externa da textura embutida no `.bbmodel`.
- `revisao.json` e `validacao-estrutura.json`: conferências e limites.

As referências foram geradas separadamente e não são vistas calibradas de uma
mesma malha. Os enquadramentos são aproximações em perspectiva. O render por
software serve para comparação; o arquivo também foi aberto e conferido no
Blockbench desktop.

## Integridade e escopo

130 peças (118 sólidos e 12 planos finos), 36 ossos, dez locators e atlas 256×256.
As lâminas seguem o antebraço; o leque segue sua inserção na base da cauda.
O motor reporta zero erros, peças soltas, assimetrias e UVs fora do atlas; faces
sólidas sem transparência e detalhes planos com pixels opacos. Piso mínimo opaco
~0,19 unidade. Há 193 avisos AABB de interpenetração de camadas e encaixes; o
relatório não comprova ausência de problemas visuais durante futuras poses.

A comparação da máscara frontal, com a mesma câmera, passa de IoU 0,5404 na v1
original do Git para 0,7650 nesta v2b. Esse número mede silhueta projetada, **não**
qualidade artística, semântica ou fidelidade anatômica. A aprovação é do usuário.

O perfil composto calculado localmente tem 153 peças, dentro do limite atual de
192. Não foi aplicado no Studio. Não há animações nesta versão: a forma precisa
de avaliação antes de desenvolver movimentos ou publicar outra exportação.

## Preservar suas alterações

Os scripts são `scripts/modelar-pavao-f3-v2.py` e `scripts/revisar-pavao-f3-v2.py`.
A geração escreve por lotes do motor externo. `--refazer` exige que o hash ainda
seja o da saída gerada. Depois de você editar o modelo, qualquer nova geração
deve usar outra versão; a edição manual fica protegida.
