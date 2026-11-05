---
data: 2026-11-05
status: interpretação das referências escolhidas; aguarda validação artística do usuário
---

# Guia visual v0.1 — preferências selecionadas

Base: sete links enviados pelo usuário com funções explícitas, além da referência
769 já discutida. Conferidas as 28 artes e os nomes/descrições por estágio. As
imagens e dados completos ficam na biblioteca externa em
`~/Downloads/referencias-criaturas/estudos/miscrits/curadoria-2026-11-05/`.
As observações são leitura de direção de arte, não atribuição oficial de inspiração.

Respeitar a função escolhida: gostar da **cor** de Chico não autoriza importar
sua anatomia/ornamentos; gostar do **conceito** de Tenebros não significa pedir
que todas as criaturas tenham sua paleta. `evo=0` aponta o primeiro estágio e
`evo=3` o quarto. As famílias inteiras dão contexto; o estágio do link continua
identificado como foco. Sem parâmetro, não presumir um estágio preferido específico.

| Referência | Escolha do usuário | Leitura e uso autorizado na direção |
|---|---|---|
| [619: Geneseed → Netherreap](https://worldofmiscrits.com/miscripedia/619) | conceito, cores e evolução | crescimento/revelação com perda de uma aparência protetora; grandes formas orgânicas, escuros, vinho/carmesim, marfim e acentos verdes. Estudar a transformação, sem copiar semente/pétalas/esqueleto |
| [721: Chico](https://worldofmiscrits.com/miscripedia/721?evo=0) | cores | base verde-azulada relativamente contida e acentos quentes vermelhos/laranja/dourados. Contraste quente/frio e hierarquia, sem adotar automaticamente sua iconografia |
| [594: Tenebros](https://worldofmiscrits.com/miscripedia/594?evo=3) | conceito | sombra/material fluido parece constituir o corpo; rosto e lâminas dão foco e intenção. Fantasia incorporada à anatomia/gesto, sem fazer uma réplica de ninja de sombra |
| [214: Shurikoon → Ninjat](https://worldofmiscrits.com/miscripedia/214) | conceito e evoluções | especialização crescente; a silhueta e os membros passam a comunicar deslocamento/ataque. Estudar transformação de função e linguagem de movimento, não copiar morcego, armas ou figurino |
| [613: Hekatom → Unbound](https://worldofmiscrits.com/miscripedia/613?evo=0) | evoluções | algo contido passa a manifestar corpo e autonomia; material/motivo herdado muda de função. O interesse é a progressão causal, não prescrever livro/pergaminhos |
| [642: Nyma](https://worldofmiscrits.com/miscripedia/642?evo=0) | cores e conceito | base clara/fria com magenta e ciano; volumes arredondados, curvas e elementos líquidos dão identidade. O acento intenso ocupa regiões focais, sem colorir tudo igualmente |
| [433: Blighted Flue](https://worldofmiscrits.com/miscripedia/433) | conceito | um processo de corrupção modifica aparência/temperamento e mantém reconhecimento do organismo-base. Não é autorização para implementar mutações nem copiar a variante existente |

## Síntese a testar

1. **A ideia organiza o personagem.** Matéria, anatomia, rosto, comportamento,
   gesto, figurino e armamento podem carregar a fantasia. Não converter integração
   em veto a acessórios: Niojade usa esses recursos de maneira importante.
2. **Evoluir pode revelar, libertar ou especializar.** Manter sinais de parentesco,
   mas mudar o significado de partes/motivos. Acrescentar espinhos e ornamentos
   por estágio não basta.
3. **Carisma e ameaça podem conviver.** Rosto legível/expressivo, corpo com
   personalidade e uma silhueta final marcante. Isso não impõe agressividade ou
   escuridão a todo o catálogo.
4. **Cor organizada, não saturação uniforme.** Há lugar para escuros ricos e para
   claros luminosos. Escolher base, contraste e acento por função e área visível.
5. **O extremo é localizado.** Olhar, borda, órgão ou energia podem concentrar
   detalhe/contraste; preservar massas maiores que sustentem a leitura pequena.
6. **Acabamento comum, conteúdo diverso.** Contorno desenhado, sombras organizadas
   e hierarquia de formas sustentam coesão. Animal, tema, paleta e movimento variam.

Estas são hipóteses sobre as escolhas enviadas, ainda não um cânone aprovado.
Não concluir que o usuário deseja somente monstros sombrios, humanoides ou
ornamentados. A amostra Nyma/Chico impede reduzir rogue a preto/roxo por padrão.

## Amostragem de cor

Amostrados pixels com alfa >=220 das artes iniciais; quantização de 10 cores
com Pillow median-cut. Exemplos representativos: Geneseed `#a02a47`, `#7b1e34`,
`#b5b499`; Chico `#50706d`, `#dd812e`, `#b81e22`, `#f3c87e`; Nyma `#edf2f8`,
`#b92875`, `#99f1f7`. São resumos do render com sombras, não cores oficiais nem
paletas canônicas para copiar. O agrupamento perde acentos pequenos; os papéis
precisam de revisão visual. Resultados completos permanecem na biblioteca externa.

## Aplicação ao piloto monge + tartaruga + rogue

Rogue/Ladino é requisito de combate confirmado pelo usuário. Explorar contraste
entre serenidade/defesa da tartaruga e arrancadas, reposicionamento e precisão.
Monge precisa aparecer na postura, rosto e demais marcadores escolhidos;
tartaruga, na cabeça/casco e no conjunto corporal. Adagas são requisito posterior
explicitado pelo usuário; mãos livres e postura marcial precisam sustentá-las.
Barba, figurino ou armas não são proibidos por princípio. Movimento rápido não exige invisibilidade/teleporte
em todo rogue. **Atualização do piloto:** o usuário escolheu Sutruga e autorizou
o especial final inspirado no Ataque Alfa do Master Yi, com desaparecimento breve.

O corpo pode sugerir robustez sem virar automaticamente um tanque. Qualquer
combinação de proteção, velocidade e dano precisa de janelas/limitações a discutir;
nenhum número de balanceamento ou kit foi implementado. O jogo ainda não tem uma
definição fechada de especializações de Ladino.

Quantidade de formas: no jogo, Comum tem 1, Raro 2 e Épico em diante 3. Não
importar quatro estágios das referências nem impor três a toda linhagem.
**Atualização:** usuário confirmou Sutruga **Mítico**, portanto **três formas**.
Fonte consultada somente para leitura:
`../jogo-criaturas/docs/decisoes/0022-raridades-formas-e-arquetipos.md`.

**Atualização após rejeição:** o usuário rejeitou a Sutruga v1/v2 e apontou
**Niojade, terceira forma da Turtudi (`evo=2`)**, como referência dominante.
O [diagnóstico](pilotos/tartaruga-monge-rogue/diagnostico-rejeicao-niojade.md)
substitui a leitura de que a tentativa estava próxima da meta. Não tratar as
outras referências como média que dilui essa solução prioritária.
