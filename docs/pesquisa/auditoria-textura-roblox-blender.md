---
data: 2026-11-04
tipo: auditoria
status: consulta oficial e inspeção local; ensaio no motor pendente
---

# Textura, UV e filtragem antes de experimentar Blender

Consulta oficial em 04/11/2026: [Texture specifications](https://create.roblox.com/docs/art/modeling/texture-specifications)
anuncia suporte a imagens de até 4096×4096 e qualidade adaptativa por dispositivo.
A própria seção UV dessa página ainda cita 1024×1024; há inconsistência documental.
Não tratar o comentário local de “máximo universal 1024” como limite comprovado
do motor nem usar 4K como obrigação. Confirmar caminho concreto de importação e
dispositivo. O orçamento de entrega da fixture permanece **1024**, configurável,
e não altera o contrato do consumidor que atualmente pede atlas até 1024.

[SurfaceAppearance](https://create.roblox.com/docs/reference/engine/classes/SurfaceAppearance)
expõe `ResampleMode`. O [fonte oficial da documentação](https://github.com/Roblox/creator-docs/blob/main/content/en-us/reference/engine/classes/SurfaceAppearance.yaml)
descreve `Enum.ResamplerMode.Pixelated` com nearest-neighbor. A constatação de
outubro de “não mudou nada visível” é evidência daquele ensaio, não ausência atual
da API. No Blender/glTF, sampler Closest/NEAREST e NEAREST_MIPMAP_NEAREST é
metadado de arquivo; não prova que o importador Studio aplicou Pixelated.

[General specifications](https://create.roblox.com/docs/art/modeling/specifications)
mantém teto de 20 mil triângulos por mesh, até quatro influências por vértice,
root sem influência e recomenda volumes fechados. A fixture usa uma influência,
uma malha/material, lâmina com espessura e orçamento menor para validar o caminho.

## Auditoria do fluxo atual (somente leitura)

- `exportar.py:TEXTURA_ROBLOX`, `textura_para_roblox`, `separar_textura` e comentários
  da decisão 0001/convencões contêm pressupostos históricos sobre limite/filtro.
  Nenhuma dessas rotinas foi removida ou alterada neste experimento.
- `superamostrar` realoca faces de ossos selecionados no **mesmo atlas**, repetindo
  pixels. É redistribuição do orçamento para detalhes pequenos, sem criação de
  detalhe artístico. No catálogo F2 usa `ossos: [head]`, incluindo descendentes,
  com fator 4; F3 não usa `superamostrar` no catálogo atual. Precisa ser comparado
  por densidade efetiva e motivo visível, não pelo tamanho do PNG.
- `separar_textura` cria material/malha extra e muda cópia para formato genérico;
  guia registra problema de giro e o considera experimental. Backend novo mantém
  uma malha/material; não adota esse caminho como solução.
- Alfa sangrado mantém RGB sob transparência; margens isolam as ilhas. Ambos
  continuam relevantes para mipmaps e filtros do destino, mesmo com nearest.
- UVs fora de [0,1] já têm recusa pelo exportador. Auditoria numérica dos três
  GLBs aprovados e hashes ficam no relatório do ensaio; fontes manuais não foram
  reexportadas.

## Fixture Blender

Atlas de trabalho 128², 2 pixels/unidade nas faces principais, margem 2 pixels
de trabalho, ampliação inteira ×8 para 1024². Cabeça tem densidade explícita igual
ao corpo; olhos têm ilha suficiente e são repintados após recoloração para serem
protegidos. Aumentar escala PNG repete pixels; aumentar densidade planejada muda
o espaço de autoria, não inventa arte. Recorte da crista tem RGB colorido também
sob alfa zero, e faces laterais fecham a lâmina.

Antes de remover ampliação/superamostragem do fluxo aprovado, ensaiar atlas nativo
e ampliado, Pixelated/Default, densidade de cabeça igual/especial, perto/longe e
qualidade baixa/alta no Studio autorizado. Comparar ocupação/margens, olho e
contorno alfa com as mesmas câmeras/luz. Não foi realizado neste chat.
