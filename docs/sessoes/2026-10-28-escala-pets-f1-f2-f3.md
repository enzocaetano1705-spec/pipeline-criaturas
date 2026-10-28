---
tipo: sessao
data: 2026-10-28
fase: 11
ia: codex
status: implementado-testado-no-studio
---

# Scale independente para cada forma

**Ação manual restante:** salvar `testesblockbench.rbxl` com Ctrl+S. Alterações
aplicadas e conferidas no DataModel; salvamento em disco não foi executado.

**Feito:** a pedido do usuário, acrescentado `Scale` por forma no início do módulo
`ReplicatedStorage.PipelinePetTest.Config`. `1` usa o tamanho do template,
`0.5` metade, `2` dobro. Valores positivos e finitos; editar com Play parado e
reiniciar. Defaults preservam o tamanho dos templates preparados, incluindo
ajustes manuais existentes nos modelos-base.

`RigScale` aplica escala absoluta a partir da referência guardada, evitando
acumular multiplicadores em reaplicações. Mede novamente chão/body/frente e
recalcula PetAnchorToPivot. Colisores usam a escala efetiva do modelo; alcance,
raio de área, tolerâncias e investida provisória do F1 acompanham o multiplicador.
Ritmo de locomoção já usa GetScale no driver. Dano/cooldown permanecem iguais.
Somente cópias dos rigs são redimensionadas, sem alterações em `.bbmodel`,
texturas ou mapas importados.

O gerador preserva os valores locais de Scale ao atualizar os fontes; o instalador
preserva os valores já editados no Studio. Na reinstalação prevalece o Config do
Studio. Essas cópias são independentes: salvar um `.rbxl` não atualiza o Git.

**Conferência:** `teste-pets/verificar-escala.luau` executado no Studio Edit:
três formas × fatores 0.5/1/1.5. Erros de apoio no chão, tamanho de colisor e
offset de osso: zero nos nove casos. Reaplicação idempotente, valores inválidos
recusados e templates intactos. Config/RigScale/Server passaram na compilação.
Reinstalação manteve Scale 0.75 da F2, depois restaurado.
O gerador também preservou 0.75 após duas execuções idênticas e recusou zero
sem sobrescrever a configuração inválida. Medições em `verificacao-escala.json`.

No Play, com valores temporários declarados no próprio Config:

- F1 em 0.5×: alcance 1.4, cinco impactos de 6 no pequeno.
- F2 em 0.75×: alcance 4.875, raio 12.75, três pisões de 14 no pequeno.
- F3 em 1.5×: alcance 14.25, Low 22, Left 28 e Combo 22+44 no grande.
- Faixas de idle/combate/golpes tocaram; console final sem erros de execução.

Uma tentativa inicial de alterar a tabela Config pelo execute_luau no Server não
modificou o módulo carregado pelo Script do controlador. O ensaio foi corrigido
para usar a edição em Edit e um novo Play, igual ao fluxo documentado ao usuário.
Não é uma validação de edição ao vivo da configuração.

**Encerramento:** valores originais de Scale restaurados em 1 nas três formas,
backup temporário removido, Config selecionada no Explorer e Play encerrado.
Avaliação artística no motor continua com o usuário. Sem nova dependência,
publicação de IDs ou conclusão da fase 11 inteira.
