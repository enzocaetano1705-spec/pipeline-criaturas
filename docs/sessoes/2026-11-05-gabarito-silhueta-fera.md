---
tipo: sessao
data: 2026-11-05
fase: ensaio de gabarito multivista
ia: codex
status: protocolo e estudo de ajuste entregues; geometria ainda em revisão
---

# Gabarito da preguiça — perfil, volume e sobreposição

**Ponto de revisão:** avaliar o estudo cinza e as diferenças de volume, antes de
pintura. Arquivo atual em `modelos/fera-fera-agil-das-sombras/gabarito-v1/r05/`,
`fera-gabarito-360.blend` e `folha-auditoria.png`. A skill mantém a parada na
“Folha de vistas ainda não aprovada numa criatura real”. O estudo não é modelo
final: rosto, tufos, dedos e volumes transversais ainda precisam refinamento.

**Retorno:** usuário rejeitou silhueta e textura do orgânico r05, reconhecendo
que as partes ficaram conectadas. Sugeriu modelar diretamente sobre a imagem
lateral e enviou seis capturas do mesmo modelo em giro. Isso passa a ser a
referência dominante de forma/pose; artes anteriores continuam fonte de cor.
Não pedir novamente espécie/estágio/arquétipo: preguiça gigante, F3, rogue.

**Implementado:** decisão 0012; capturas/hashes e máscaras; fundo quadrático
ajustado às bordas para lidar com vinheta; grade e landmarks; traçado de regiões
de antebraço/perna/tronco/juba; seções da cabeça/cauda extraídas do perfil;
larguras estimadas pela frente; volumes facetados, cinza; fundo lateral
empacotado no `.blend`, excluído dos renders e das máscaras medidas.

Protocolo geral acrescentado a `skills/criaturas-3d/referencias.md`, sincronizado
para `.agents` e `.claude`, pacote de chat regenerado. Scripts desta anatomia em
`scripts/gabarito-fera/` permanecem experimentais, sem substituir o CLI/gerador
padrão. O uso por futuros modelos cubificados reaproveita contornos/medidas,
respeitando as restrições do formato; não é converter cada pixel em um cubo.

**Ciclo medido:** primeiro bloco r01: perfil IoU 65,2%, com quadril/pés deslocados.
A sobreposição revelou o erro das marcações estimadas. Após traçar as regiões
diretamente na máscara: r03 82,5%, r04 85,2%, r05 **89,4%** no perfil principal.
A câmera do perfil permaneceu fixa. Métrica conjunta de geometria/enquadramento
nas outras vistas: frente **75,6%**, costas **73,1%**, perfil oposto **86,2%**,
superior **76,3%**, inferior **76,6%**. Os renders finais são Blender, não máscaras
de referência reapresentadas como geometria. Azul=falta, laranja=excesso,
cinza=interseção. Recortes de cabeça/mão/pé/cauda estão em JSON diagnóstico.

**Limites importantes:** IoU é interseção/união das máscaras, não nota artística.
Uma cauda grande pode dominar a métrica; recortes regionais complementam a leitura.
Capturas não fornecem FOV/elevação/zoom; as câmeras são estimadas. Calibração nas
vistas secundárias usa apenas escala uniforme e translação de câmera, gravadas e
aplicadas ao arquivo nativo. Não há deformação por vista para maquiar números.
Vistas superior/inferior têm rótulos provisórios. Todos os originais permanecem
preservados. Nenhuma malha/dado oculto foi extraído do serviço pago.

**Conferência:** reabertura em processo limpo, 33 volumes fechados, 4.162 triângulos,
8 câmeras; zero erros técnicos. Verificação compara os vértices do `.blend` com a
malha anterior à calibração: geometria preservada. Gabarito é empty de imagem
empacotada, `hide_render=True`. Scripts compilados. Textura/rig/Roblox pendentes.
MCP consultado somente por `get_addon_status`, ainda sem conexão; nenhuma autoria
MCP e nenhuma cena aberta foi substituída. Arquivos do pavão/documentos pessoais
fora das alterações. R02 falhou por mudança da API NumPy de produto vetorial 2D,
corrigida por determinante explícito; nenhuma instalação foi necessária.

**Auditoria:** contador do novo pedido, separado do ensaio orgânico:
`gabarito-v1/auditoria/`. Captura final e manifesto consolidados junto à entrega.
Tokens/cache/saída não são convertidos em preço nem percentual da assinatura.

**Próximo passo:** usar as diferenças expostas pelas seis vistas para ajustar
larguras/posições e volumes internos, especialmente mãos, ombros e torso, e depois
o rosto/tufos/roupas. Aprovar a forma antes da pintura. O ensaio é reconstrução
de referência conhecida; não comprova generalização para outras criaturas.
