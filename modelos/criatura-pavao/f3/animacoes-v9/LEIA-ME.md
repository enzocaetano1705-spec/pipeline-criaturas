# F3 — correção dos flicks

Modelo: `criatura-pavao-e3-combate-v9.bbmodel`.
Fonte preservada: `../animacoes-v8/criatura-pavao-e3-combate-v8.bbmodel`.

## Correções

- Cristas: os quatro planos tinham espessura zero e faces opostas coincidentes.
  Espessura de 0,01 unidade elimina a disputa entre essas faces no render duplo
  do Blockbench, mantendo os contornos e os UVs.
- Pontas das duas espadas: a parte superior do losango sobrepunha a lâmina
  com faces quase coplanares. As faces largas das pontas recuam 0,01 unidade;
  o desenho da ponta e a pintura permanecem iguais.
- Chaves: todos os canais variáveis de cada clipe usam os mesmos tempos.
  As compensações não ficam fora de fase quando o Blockbench aproxima o
  cursor de uma chave. As espadas têm vínculo fixo na mão quando empunhadas.
- Saque andando: o plano do floreio fica estável no mundo. Inclinar a lâmina
  longa com a oscilação do torso fazia o IK erguê-la e quase travar o cotovelo.
- Camadas `upper`: extraídas dos canais locais do clipe completo correspondente.
  A cintura e a cauda não recebem translações artificiais para compensar outra
  base de caminhada. A raiz da cauda permanece presa à bacia.
- Movimento secundário das cristas suavizado, conservando os endpoints.

Nove clipes corrigidos; nomes, durações e marcadores mantidos. Os canais de
`idle`, `walk`, `combat_ready` e `combat_walk` são idênticos aos aprovados.
93 cubos, 41 grupos, mesma textura e UVs. Apenas seis peças receberam os
ajustes mínimos de profundidade descritos acima. Fontes manuais preservadas.

## Camadas superiores

`combat_enter_upper` corresponde a `combat_enter_walk`; `combat_exit_upper`
corresponde a `combat_exit`. A base usa corpo, bacia e pernas do companheiro,
no mesmo tempo. Os canais da máscara substituem os respectivos canais da
base; não se somam. Sozinha, uma camada não anima corpo/pernas. As prévias
GIF incluem o companheiro para mostrar a composição completa.

## Conferência

```powershell
uv run python scripts/animar-combate-pavao-f3-v9.py --animar
uv run python scripts/animar-combate-pavao-f3-v9.py --validar
uv run python scripts/animar-combate-pavao-f3-v9.py --auditar --previas
```

`validacao.json` confere poses, apoios, juntas, raízes, preensão, soltura,
encaixes e preservação. `validacao-nativa.json` repete a conferência com a
tolerância temporal do Blockbench 5.2.2, fora da grade original. Motor externo:
zero erros e avisos nos três grupos de testes, respeitando a espada enterrada
e a composição das camadas. `comparacao-tecnica.json` mede as superfícies e
a melhora da flexão do cotovelo. `comparacao-nativa.png` reúne seis capturas
reais do aplicativo, antes/depois. Nove GIFs ao lado do arquivo.

Os reparos aguardam avaliação visual. Golpes continuam como próxima etapa.
