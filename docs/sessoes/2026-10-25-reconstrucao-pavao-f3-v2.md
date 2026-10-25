---
tipo: sessao
data: 2026-10-25
fase: 10
ia: codex
status: aguardando-revisao-artistica
---

# F3 — reconstrução após rejeição da v1

**Revisão para o usuário:** avaliar a reconstrução no Blockbench e a comparação
com frente/perfil. A skill `criaturas-3d` mantém a parada de aprovação da forma
antes de animações e exportação.

**Retorno recebido:** v1 considerada inutilizável, 3/10; textura era o único ponto
aceitável. Usuário tentou alterar blocos e removeu a textura, sem conseguir
recuperar o modelo. Enviou quatro redesenhos com aparência de modelo como alvo
mais claro, priorizando frente e lateral. Avisou que há garras indevidas e excesso
de voxels nas referências. Fonte manual anterior preservada, sem sobrescrita.

**Feito:** quatro imagens novas preservadas em `criaturas/criatura-pavao/revisao-f3/`.
Reconstrução em `modelos/criatura-pavao/f3/revisao-v2/criatura-pavao-e3-v2b.bbmodel`.
Novos script/lotes, volumes corporais, cintura/quadril, cabeça/bico, membros,
pés com garras, crista dupla, lâminas grandes dos antebraços e leque em camadas.
Sem garras adicionais nas mãos, canelas ou tronco.

**Correção do método:** comparar referência e modelo com enquadramentos semelhantes
durante a construção. As câmeras estão registradas; as imagens não são vistas
calibradas da mesma malha. Os planos iniciais continuavam com aspecto de papel;
as penas principais passaram a três volumes grandes (haste, lâmina e ponta em
diagonal), com espessura real, evitando cubos para cada pixel. Detalhes finos ainda
usam alfa. A prévia `massas.png` permite rever a forma sem as cores.

**Conferências:** 130 peças (118 sólidos/12 planos), 36 ossos e dez locators.
Atlas 256×256 incorporado. Zero erros estruturais, peças soltas, pares assimétricos,
UVs fora do atlas, faces sólidas transparentes, planos vazios e vínculos incorretos
das lâminas. Ajustadas duas pontas caudais que entravam no piso; mínimo opaco ~0,19.
193 avisos AABB restantes de interpenetração de camadas/juntas: não equivalem a
aprovação artística nem verificam interseções durante futuras animações.

Silhueta frontal, mesma câmera aproximada: IoU 0,5404 na v1 original do commit
`fe94ca4` e 0,7650 na v2b. Métrica de máscara, sem afirmar nota artística ou match
integral. Perfil físico composto calculado localmente: 153 peças, limite 192.
MCP do Blockbench confirmou a nova aba, com 130 cubos/36 grupos/textura incorporada;
conferida vista 3/4. A vista traseira revelou a pena central quase de perfil;
a correção foi gerada na v2b, preservando o arquivo v2 já aberto no aplicativo.
Conferida também a vista das costas. Nenhuma alteração no Roblox Studio.

**Próximo:** avaliação artística da v2. A primeira tentativa não está aprovada.
Se o usuário editar a v2, continuar em versão nova. Sem clipes, publicação de
animações ou lógica de pet nesta etapa. F2 encerrada por ora permanece preservada.
