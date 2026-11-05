---
data: 2026-11-05
status: amostra seletiva; hipóteses para curadoria do usuário
---

# Estudo inicial de linguagem e evolução

Foram conferidas artes dos quatro estágios de quatro linhagens: o exemplo do
usuário e três casos estruturalmente diferentes. Os originais, folhas de até
768 px e cache de consulta estão na biblioteca externa:
`~/Downloads/referencias-criaturas/estudos/miscrits/`. Não entram no repositório.

A página é uma aplicação JavaScript; sua interface consulta o JSON público
`https://worldofmiscrits.com/miscrits.json`. Na consulta havia 439 registros,
cada um representando uma família com nomes/descrições por estágio. Isso não é
439 imagens nem declaração de que a amostra representa todo o acervo. O endpoint
consultado não trazia um campo separado de artista ou inspiração. A leitura de
inspiração feita abaixo é análise visual, sem inventar atribuições autorais.

| Caso | Observação de construção visual | Hipótese aproveitável no método |
|---|---|---|
| [Turtudi → Meiolan → Niojade → Tide Gong](https://worldofmiscrits.com/miscripedia/769?evo=0) | família de tartaruga, ornamentação mineral/verde e água, crescente organização/complexidade | combinar arco narrativo com transformação de motivos e postura |
| [Flue → Chimnay → Firebrawl → Afterburn](https://worldofmiscrits.com/miscripedia/1) | fogo e estruturas cinzas persistem enquanto massa e postura mudam | conservar uma ideia estrutural, não repetir o mesmo corpo só maior |
| [Prawnja → Hermetalcrab → Shellgun → Clawmurai](https://worldofmiscrits.com/miscripedia/3) | crustáceo, laranja/azul e linguagem de equipamento crescem em complexidade | unificar anatomia e tema com hierarquia e contraste |
| [Elefauna → Floraphaunt → Stammoth → Grastodon](https://worldofmiscrits.com/miscripedia/13) | anatomia de elefante e vegetação se transformam até uma presença arbórea | evoluir a relação entre conceitos, não apenas acrescentar acessórios |

A história do exemplo 769 acompanha acolhimento/treinamento, viagem em busca de
conhecimento e transmissão do aprendizado. O desenho e o texto oferecem uma
progressão legível. **Interpretação:** a evolução expressa papel e experiência,
além de tamanho/poder. Não assumir que toda família do catálogo segue esse arco.

Para “monge + tartaruga”, esse caso já ocupa uma solução conhecida. Criar um
original exige outra história, outro comportamento e outro motivo dominante,
evitando reproduzir a combinação específica de bastão de jade, dragões e jornada
de mestre/discípulo. Trocar nomes ou cores não basta para diferenciá-la.

## Hipóteses de guia visual v0

Observações desta amostra, a validar com o usuário:

- Silhueta legível e pose expressiva; detalhes de personalidade distribuídos
  de forma hierárquica, com cabeça/gesto/motivo dominante atraindo atenção.
- Contornos definidos e variação de peso, superfícies com regiões de cor
  organizadas e sombras desenhadas. Não confundir isso com exigir pixel art na
  concept art; o pixel art pertence à tradução/textura 3D posterior.
- Contraste entre áreas simples e focos de detalhe. A família 769 é mais
  ornamentada que vários exemplos antigos; não misturar ambos cegamente num
  único “estilo médio” ou dataset sem curadoria.
- Paleta e motivos relacionados entre estágios; diferenças de escala/atitude
  e especialização dão progressão. As regras comuns de acabamento permitem
  variar animal, tema e cores entre famílias.
- Densidade de detalhe pode aumentar, mas uma forma final não precisa ganhar
  asas, ficar humanoide ou usar armadura. Escolher conforme o conceito.

Essas hipóteses ainda não constituem uma bíblia visual aprovada. A próxima
curadoria deve perguntar **quais casos são exemplares, quais são exceções e
quais soluções o usuário não quer no seu universo**. Começar com Miscrits;
Digimon/Pokémon entram só quando houver seleção concreta, evitando misturar
referências que o usuário não considera representativas.

## Usar referências sem esconder cópia

Registrar uma função por referência: acabamento, anatomia, transformação,
gesto ou economia de formas. Registrar também elementos proibidos para aquela
nova criação. Depois do piloto, os originais próprios aprovados passam a formar
o núcleo do guia de mundo. Um conjunto curado é útil tanto sem treinamento
(referências e fichas consultadas no prompt) quanto numa decisão futura de LoRA.
