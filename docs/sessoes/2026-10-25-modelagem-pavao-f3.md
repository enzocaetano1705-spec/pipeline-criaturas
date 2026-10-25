---
tipo: sessao
data: 2026-10-25
fase: 10
ia: codex
status: aguardando-revisao-artistica
---

# Pavão F3 — primeira modelagem editável

**Revisão para o usuário:** avaliar silhueta/proporções e editar a F3 no
Blockbench. A skill `criaturas-3d` pede aprovação da folha antes de seguir para
animações/exportação; esta entrega é a proposta para essa revisão.

**Feito:** quatro imagens separadas preservadas em `docs/criaturas/criatura-pavao/`;
ficha da linhagem ampliada para três estágios e conferida pelo comando `ficha`.
F2 encerrada artisticamente em [[2026-10-24-fechamento-f2]].

F3 em `modelos/criatura-pavao/f3/criatura-pavao-e3.bbmodel`, com atlas embutido,
91 peças, 49 ossos/grupos, nove locators e folha de vistas de até 768 px.
Ave humanoide bípede digitígrada, bico, duas plumas de crista, três lâminas por
antebraço, mãos articuláveis, patas com garras, cauda sólida de três segmentos e
leque de seis penas. Estágio 3 de 3, categoria ave bípede com cauda, conforme
descrição do usuário e continuidade da linhagem; altura inicial ~4 blocos ajustável.

**Leitura das vistas:** frente/costas/3/4 mostram duas plumas de crista; a única
visível no perfil é tratada como sobreposição. Não foram acrescentadas asas
independentes. Jesmon orienta a função de lutador terrestre, sem transferir seu
desenho. Ocelos, creme ventral, turquesa, garras escuras e gema dourada vêm das artes.

**Método:** script próprio de volumes/planos, lotes `bbmodel_edit` no motor separado
e pintura original. Estudo já registrado de Harpymon reaproveitado como estratégia
de poucos sólidos e penas recortadas, sem geometria/textura/animação de terceiros.
Metadados em `referencias-consultadas.json`. A página oficial de Jesmon estava em
manutenção; a referência funcional é a instrução do usuário, não inferência do site.

**Correções durante a revisão:** torção e escalonamento do leque para leitura em
perfil/costas; lâminas deslocadas para a face externa/posterior dos antebraços;
simetria dos dedos/patas corrigida; leque superior separado do sólido caudal;
penas dos tornozelos abertas para fora. Raízes mantidas nos grupos correspondentes.

**Validação:** `revisar-pavao-f3.py`: zero erros estruturais, UVs fora do atlas,
faces sólidas transparentes, planos vazios, vínculos incorretos ou pares assimétricos.
Piso opaco ~0,004 unidade. O motor mantém 122 avisos AABB de sobreposição de
camadas/juntas; o relatório detalha o limite dessa checagem. Amostragem opaca de
lâminas/leque sem penetração distal de mãos/cauda; duas pequenas inserções de
penas nas próprias canelas (~0,37 unidade). Não há validação de poses animadas da F3.
24 testes existentes de ficha/exportação/infraestrutura Roblox passaram.

**Próximo:** retorno artístico do usuário e ajustes em nova versão se ele já
editou o arquivo. Animações, importação da F3 e lógica de pet ficam para outra etapa.
A fonte editada manualmente da F2 e as alterações em AURA foram preservadas.
