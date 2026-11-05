---
tipo: sessao
data: 2026-11-05
fase: exploração A.1
ia: codex
status: estudo e kit preparados; piloto artístico pendente
---

# Criação de conceitos/linhagens antes da modelagem

**Próxima decisão do usuário:** selecionar referências exemplares e aprovar uma
direção de estilo/conceito antes do piloto artístico. Nenhuma compra, instalação
ou aprovação de linhagem foi solicitada/realizada nesta sessão.

**Feito:** A.1 do plano, branch `codex/direcao-arte-criaturas` baseada no backend
Blender. Kit em `docs/direcao-arte/`, com método, estudo Miscrits, critérios,
briefing e quatro prompts: criador, revisor, arte e vistas. Exemplo textual de
raciocínio “monge + tartaruga” é exploratório e não está aprovado.

Usuário confirmou: **até R$ 50 uma única vez, sem gasto mensal novo**, Gemini e
este chat já disponíveis; ainda sem exemplos específicos de Digimon/Pokémon.
GPU consultada por `nvidia-smi`: RTX 4050 Laptop, 6141 MiB. Nenhum driver,
treinador ou pacote instalado. Não assumir que todo treinamento local é impossível
nem fazer o fluxo depender de treino pesado nessa GPU.

**Estudo:** páginas públicas Miscripedia/769 e catálogo; a página SPA consulta
`miscrits.json`. Metadados públicos lidos seletivamente, quatro linhagens com
quatro artes cada conferidas: 769, 1, 3, 13. Histórias da 769 consultadas. Originais,
cache público e duas folhas <=768 px permanecem na biblioteca externa em
`~/Downloads/referencias-criaturas/estudos/miscrits/`. Nenhuma arte de terceiros
foi adicionada ao repositório. Não se estudou todo o catálogo nem se atribuiu
autoria não presente no endpoint.

**Recomendação:** iniciar com guia visual e referências curadas, três propostas
textuais, criador/revisor em contextos separados e aprovação humana; planejar a
família antes da arte, congelar arte por estágio e só então gerar/revisar vistas.
Gastar R$ 0 adicional no piloto dentro das cotas existentes. LoRA é hipótese para
consistência de acabamento após demonstrar necessidade, não solução automática
para história, originalidade, parentesco ou concordância entre ângulos.

**Custos consultados:** guia Replicate dá exemplo de ~US$ 1,46 por treino pequeno;
FLUX-dev-lora é anunciado a US$ 0,032 por saída. Soma de exemplo para treino +
20 imagens: US$ 2,10, antes de câmbio/taxas/mínimo de recarga/retrabalho. Sem
promessa de que compra real cabe em R$ 50, sem assinatura ou recarga automática.
Ver fontes e limites no LEIA-ME do kit. Permissão de dados e licença do ambiente
precisam ser conferidas antes de qualquer treino para o jogo.

**Validação:** `scripts/preparar-direcao-arte.py` só usa biblioteca padrão e prepara
arquivos; nenhuma IA/API/rede/cobrança. Executado com briefing de exemplo em
`modelos/_direcao-arte/piloto-01` e `piloto-01-reconstrucao`: os seis arquivos são
idênticos, hashes conferidos e marcadores preenchidos. Pasta existente recusada
sem sobrescrever; briefing sem conceitos recusado sem criar saída. Compileall e
diff-check passaram. Testes 3D não repetidos: seus módulos não foram alterados.

**Preservação:** alterações preexistentes em AURA e modelos/texturas manuais
continuam fora do commit. Nenhuma escrita em fichas rascunho, backend, exportador,
fontes aprovadas ou `../jogo-criaturas`. Nenhum controle de Studio/Blender vivo.

**Próximo passo:** A.2, piloto com referências escolhidas e dois papéis, usando
os acessos atuais. A.3 (LoRA) apenas se o piloto identificar gargalo de estilo e
houver dados permitidos/orçamento confirmado. Nenhum vencedor, imagem nova,
originalidade ou qualidade artística foi validado nesta exploração.
