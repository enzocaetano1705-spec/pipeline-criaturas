---
tipo: sessao
data: 2026-11-05
fase: exploração A.2.2a
ia: codex
status: direção/raridade confirmadas; primeiro conceito F3 gerado; arte pendente
---

# Sutruga Mítico — ficha, Ataque Alfa e primeiro conceito final

**Pergunta para o usuário:** a aparência da F3 v2 deve ser a base da Sutruga
final — rosto, casco, paleta e postura — ou o que precisa mudar antes de
desenvolvermos as formas jovem/intermediária? Arte, categoria e vistas não
foram aprovadas; não iniciar modelagem a partir deste estudo.

**Confirmado:** usuário escolheu Sutruga e pediu especial final como Ataque Alfa
do Master Yi, pelo menos na última forma. Em resposta à pergunta de raridade,
confirmou **Mítico**, portanto **três formas** conforme regra do jogo. O briefing
registra a decisão e não presume uma quarta evolução. Aprovação de direção é
distinta de aprovação artística.

**Feito:** A.2.2a. Ficha proposta com história própria, três marcos de evolução,
inventário anatômico, paleta e assinatura de movimento. Passado: aprendiz que
dispara por impulso; transição: domínio da parada; final: encadeamento preciso.
Especial provisoriamente chamado **Voto do Instante**, com desaparecimento breve,
sequência de impactos e reaparição controlada. Nome não foi aprovado pelo usuário.

Referência oficial consultada: página Master Yi da Riot e JSON público Data
Dragon 16.22.1, pt_BR. A descrição confirma deslocamento/teleporte veloz entre
unidades e inalvejabilidade. Não confundir com invulnerabilidade a todo dano.
Dano, alcance, recarga, impactos/alvos, saída e uso contra chefe continuam
questões de balanceamento; não portar automaticamente outros efeitos do LoL.
Sem escrita/implementação em `../jogo-criaturas` ou controle do Studio.

**Geração:** skill `imagegen`, ferramenta nativa (sem CLI/API externa), uma
geração e uma edição direcionada. Primeiro conceito final apresentou casco e
lâminas muito grandes para a leitura rogue; revisão v2 baixou casco, reduziu
arestas, afinou membros e encurtou cauda, preservando rosto/paleta/gesto.
Revisão visual feita pelo próprio harness, sem afirmar revisor independente.

Originais **1536×1024**, prévias inspecionadas **768×512**, quatro PNGs no total,
sem sobrescrever v1. Imagem de referência da edição foi a prévia v1 já vista.
Prompts completos, metadados e hashes em
`docs/direcao-arte/pilotos/tartaruga-monge-rogue/`. Arte em `arte/`.
Custos/tokens/seed/modelo não foram expostos pela ferramenta; não inventar
consumo nem registrar custo zero. Sem treinamento, instalação ou compra.

**Revisão e limites:** v2 conserva quatro membros, face de tartaruga, casco,
plastrão, cauda e mão/pata em gesto de concentração. Atitude e proporções ainda
precisam do usuário. Anatomia oculta, implantação do membro distante, contagem
completa de dígitos, vista posterior e continuidade dos motivos ainda não estão
resolvidas como ficha técnica. Não interpretar uma ilustração 3/4 como prova
de rig, equilíbrio dinâmico ou habilidade funcionando no destino. F1/F2 só texto.

**Validação técnica:** briefing Mítico/três formas/direção escolhida validado;
preparador executado em pasta nova `modelos/_direcao-arte/sutruga-mitico-final-v1/`;
PNGs íntegros, prévias <=768 px e hashes/metadados conferidos. Sem mudança em
módulos 3D, portanto sem repetir pytest de modelagem. Fontes manuais, rascunhos
e exportações preservados/excluídos do commit.

**Próximo passo:** revisão humana da arte F3; refinamento quando necessário;
depois produzir F1/F2, revisar a família e aprovar vistas antes dos backends.
Não marcar a fase A.2.2 inteira concluída ou gerar modelo/rig desta arte ainda.
