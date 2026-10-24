# F2 v8 — gancho em J e chute na descida

Avaliar **somente `attack_tail_kick`** no arquivo v8. Pisão e spin já aprovados.

## Retorno e correção

O usuário aprovou a sensação elástica da v7 e forneceu referência de cauda em J: ponta
para a direita na vista lateral, isto é, para trás da criatura. Pediu também retirar o
leque de dentro da parte sólida e segurar as patas até depois do lançamento, chutando
quando o corpo já começa a cair para a frente.

- Cauda desce do quadril, curva pela parte baixa e levanta a ponta para trás.
- Apoio na barriga do gancho, com ponta elevada; a ponta não fica presa ao chão.
- Pivôs adequados ao sentido de cada dobra, evitando abrir fendas entre os seis trechos.
- Leque acompanha a extremidade, com suas raízes fixas. Foi retirada a compensação que
  virava todo o leque para dentro. A lâmina central inferior levanta 15° pela própria
  inserção na soltura para liberar o piso. Largura do leque constante, sem escala.
- Patas recolhidas durante a subida e no ápice; chute começa ~0,035 s após o ápice,
  quando a velocidade vertical já é negativa. Impacto ~0,165 s após o ápice.
- Braços, cabeça e peito acompanham o acento tardio. Salto conserva a velocidade de
  descarga próxima da v7 (+43 Y/−27 Z em unidades do modelo por segundo).

## Preservação e arquivos

Nova versão protegida, fonte v7. **63 cubos/53 grupos**: geometria, UV e textura idênticas
à fonte. `tail_hook` é uma articulação neutra inserida sob `tail_2`; quatro pivôs de flexão
foram ajustados onde os clipes aprovados não os animam. Isso não muda o repouso.
As chaves de idle, walk, pisão e spin são mantidas. Os ataques aprovados são comparados
por todos os cantos dos 63 cubos a 240 Hz. Curvas não lineares de idle/walk são protegidas
pela igualdade das chaves e pelas transformações neutras, sem aproximação linear.

- `criatura-pavao-e2-ataque-v8.bbmodel`: 2,85 s, execução única, rotações a 120 Hz;
  translação do apoio refinada a 240 Hz para manter o contato durante a troca do canto mais baixo.
- `previa-gancho.gif`: 1×, duas vistas, 50 fps e pausa final de 0,30 s.
- `poses-gancho.png`: carga, cauda isolada para ver o J, lançamento, espera, chute e pouso.
- `gancho.ops.json`: lote aplicado pelo motor externo.
- `medidas-gancho.json`: piso por alfa, leque contra cauda, juntas, direção da ponta,
  sentido das dobras, largura do leque, voo, tempo do chute e penas contra pernas.
- `aprovados-preservados.json`: igualdade das chaves, geometria, UV e textura.
- `proveniencia.json`: hashes e proteção contra sobrescrever edições à mão.
- `validacao-estrutura.json` / `validacao-ataque.json`: diagnósticos do motor.
- `animacoes.json`: marcadores propostos; não integrados ao gameplay.

Os testes de contato descontam a inserção já existente das penas nos sólidos em repouso.
Há tolerância de 0,05 unidade para novos contatos opacos e 0,025 para piso/interpolação;
não são uma alegação de contato matematicamente nulo. A trajetória é coreografia visual,
com a elasticidade fictícia solicitada, não simulação de massa/gravidade real.

Reproduzir as conferências:

```powershell
uv run python scripts/animar-gancho-cauda-pavao-f2-v8.py --medir
uv run python scripts/revisar-gancho-cauda-pavao-f2-v8.py
```

Gerar pela primeira vez sem `--medir`. `--refazer` só substitui saída própria com hash
íntegro e a mesma fonte. Fonte manual e versões anteriores permanecem protegidas.
Referência desta revisão é a imagem anexada pelo usuário; pesquisa anterior da v5 reutilizada.
Não exportada para Roblox. Naturalidade final depende da avaliação artística do usuário.
