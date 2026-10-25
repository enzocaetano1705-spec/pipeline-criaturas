# F3 v5 — pés simples da F2 e UVs reparados

**Aguarda avaliação artística.** Arquivo aberto no Blockbench:
`criatura-pavao-e3-v5.bbmodel`. `pes-detalhe.png` mostra o apoio de perto;
`folha.png` e `apresentacao.png` mostram a criatura completa.

## Origem e alterações

O usuário fez novas correções na v4, retirou os pés e pediu versões menores no
estilo da F2, além de reparar a textura danificada pelos redimensionamentos.
`origem-manual.bbmodel` preserva a aba aberta, inclusive alterações não salvas:
99 blocos e 41 ossos. A geometria manual e os UUIDs desses 99 blocos foram
mantidos, com somente uma translação vertical de −1,471713 para nivelar o apoio.

- Pés compactos: três dedos dianteiros e um posterior, copiados da F2 com escala
  1,15; pontas pintadas na textura e uma base pequena para unir os dedos ao
  tornozelo editado. Cinco peças por pé, sem garras curvas separadas.
- Dimensões por pé: ~4,51 × 1,15 × 7,15 unidades. A antiga proposta tinha
  ~10,71 × 4,02 × 15,22: redução de ~58% da largura e ~53% do comprimento.
- Sete ilhas UV reparadas: coxas, canelas, tarsos/tornozelos e pescoço inferior.
  A imagem do atlas continuava intacta; os UVs passaram a ler regiões vazias ou
  de outras peças. A pintura é amostrada das faces íntegras anteriores à edição,
  no commit `237ceb7`, e reaplicada às novas dimensões.
- Ilhas novas no retângulo livre x=256…512, y=384…512. O restante do atlas 512
  permanece idêntico. Sem redimensionar a imagem nem repintar cabeça/plumagem.
- Pivôs dos quadris, joelhos e jarretes alinhados às juntas da geometria manual;
  locators dos pés e chão adicionados. A aparência estática do corpo foi mantida.

## Conferências e limites

109 peças, 41 ossos, uma textura e nenhum clipe. Zero erros estruturais, peças
soltas, UVs fora ou novas faces sólidas transparentes. Os 99 blocos manuais
conferem com a origem após retirar a translação: erro numérico máximo ~1,8e-15.
Os dois pés apoiam em Y=0. Atlas anterior preservado fora das ilhas novas.

206 avisos: 203 sobreposições AABB de camadas/encaixes e três pares de penas
dorsais não identificados pelos nomes/agrupamentos da edição manual. Esses
elementos foram preservados. As duas transparências herdadas da cabeça da F2
em `beak.south/down` continuam registradas. Não foram criadas animações nem
testadas colisões no Roblox nesta revisão.

## Reproduzir

`uv run python scripts/revisar-pes-uv-pavao-f3.py` lê o snapshot e recupera a pintura
histórica pelo Git. A cópia é escrita exclusivamente por lotes no motor externo.
`--regenerar` exige o hash da própria saída; depois de editar à mão, usar nova
versão. O script recusa restaurar pintura histórica se o PNG também tiver sido
editado, para proteger alterações de textura do usuário.

`ajustes.ops.json`, `auditoria-origem.json`, `revisao.json` e `geracao.json`
registram origem, UVs, geometria, medidas e hashes. Próximo: avaliação artística.
