# F3 v4 — braços humanoides, duas espadas e plumagem da F2

**Aguarda avaliação artística.** Arquivo aberto no Blockbench:
`criatura-pavao-e3-v4.bbmodel`. `apresentacao.png` mostra as duas lâminas em vista
oblíqua próxima da frente; `folha.png` reúne frente, perfil, costas e 3/4.

## Alterações pedidas

- Braços humanoides: ombro, cotovelo, antebraço e punho, com mãos em blocos sem
  dedos. Substituem os antebraços recolhidos e as pinças da v3.
- Duas lâminas de 30 unidades, com largura máxima de cinco, em planos recortados;
  bordas quase paralelas, curvatura discreta e ponta. Textura amostrada diretamente
  de `wing_left_feather_1` da F2. Hastes, guardas pequenas e pomos sólidos.
- Seis penas longas da F2 no dorso (`back_wing_feather_*`), em dois grupos presos
  ao tronco. Comprimentos adaptados para 24–26 unidades, com escala uniforme por
  pena e preservação de UV, cores, recorte e proporções da fonte.
- Seis penas menores das asas da F2 nos cotovelos (`elbow_wing_*`), em leques
  com escala de 0,75. `wing_*` acompanha `forearm_*`.
- Inclinação do tronco aumentada em 6° (16° → 22° nesta base); elevação da cauda
  aumentada em 6° (8° → 14°). Cabeça conserva a geometria/UV/textura exatos da F2,
  com translação para acompanhar a nova posição do pescoço.

`origem-aberta.bbmodel` preserva a aba ativa antes desta revisão, incluindo o
estado não salvo. Era a prévia v3 anterior à correção dos pivôs dos joelhos;
esses pivôs foram alinhados às canelas nesta nova saída. Os modelos anteriores
continuam preservados. Atlas 512 incorporado; ilhas novas no quadrante inferior
direito, separado da região que contém o atlas original da F2.

## Rig e conferências

111 peças, 38 ossos, uma textura, nenhum clipe. Hierarquia dos braços:
`arm_* → forearm_* → hand_* → feather_sword_*`; leques sob `forearm_*`, penas
dorsais sob `torso`. Pegada/base/ponta de cada arma têm locators.

Motor: zero erros, peças soltas, assimetrias e UVs fora. Cabeça igual à F2 após
retirar a translação; textura da fonte idêntica. As 12 penas adicionadas conferem
com as dimensões escaladas e UVs dos modelos originais da F2. Armas conservam
o encaixe durante rotações de conferência do punho. Nenhum dedo/pinça remanescente.
Piso mínimo opaco ~0,234. Nenhuma nova face sólida transparente; as duas faces
parcialmente transparentes do bico herdadas da F2 continuam registradas.

279 avisos AABB de sobreposição em camadas/encaixes. A conferência adicional
transforma os centros dos pixels opacos das novas penas para o espaço dos sólidos:
zero penetrações maiores que 0,15 após os 20% iniciais de inserção. As penas
inferiores do dorso foram afastadas um pouco para evitar contato com o leque
caudal. Isso verifica repouso e não garante ausência de cruzamentos em animações.
Sem ações no Roblox Studio nesta revisão.

## Reproduzir

`uv run python scripts/revisar-bracos-plumagem-pavao-f3.py` aplica o lote pelo motor
externo a uma cópia da origem. `--regenerar` só aceita o hash da própria saída.
Depois de edição manual, continuar em outro arquivo. Fontes/hashes, lote,
validação, contatos e prévias ficam nesta pasta.
