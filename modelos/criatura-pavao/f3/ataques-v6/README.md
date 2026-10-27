# F3 — ajustes finais de ritmo e fechamento

Cópia nova da v5. `attack_low` aprovado e outros 19 clipes permanecem
integralmente iguais, incluindo suas chaves. Total: 23 clipes.

- `attack_left` — 1,32 s: carga mantida e aceleração concentrada no corte.
  A transformação do tempo preserva os valores e a sequência das poses.
- `attack_right` — 1,51 s: corte inicial até 0,54 s intacto; a passagem pelo
  antigo intervalo 0,60–0,80 s leva cerca de 0,06 s. Recuperação começa antes,
  com o giro axial do punho distribuído suavemente entre 0,60 e 0,91 s.
- `attack_combo` — 2,20 s: golpe duplo mais fechado e quase paralelo,
  conforme `referencias/combo-fechado.png`. Salto, giro, tronco, cauda,
  pernas e crista mantêm as chaves aprovadas da v5.

No combo, só seis canais são revistos entre 0,90 e 1,62 s: rotação dos
dois ombros e rotação/posição das duas asas de cotovelo. Cada braço gira
como uma alavanca para retirar a abertura lateral. Cotovelos, punhos e
preensão mantêm suas relações; as asas conservam as raízes presas e a
orientação da v5. Correção de piso mantém o contato das duas lâminas.

`validacao-ataques.json` verifica preservação, articulações, preensão,
fio, continuidade, âncoras, apoio/voo, piso e superfícies opacas. Inclui
comparação da aceleração do Left, intervalo de recuperação do Right e
abertura/ângulo entre as lâminas do combo. `validacao-motor.json` contém
a conferência independente do motor externo. Aprovação artística com o usuário.

GIFs das três animações e vistas frontal/superior do combo capturados no
Blockbench. `poses-nativas.png` reúne nove poses; câmeras e hash ficam em
`previas-nativas.json`. Sem alteração no Studio ou na lógica de combate.

```powershell
uv run python scripts/ajustar-golpes-pavao-f3-v6.py --gerar --validar
```

`--clipes attack_combo` atualiza apenas esse ajuste. `--nativo` exige a v6
aberta. Escritas pelo motor externo, em lotes de até 500 operações, com
proteção por hash contra alterações manuais e valores sem expoentes.
