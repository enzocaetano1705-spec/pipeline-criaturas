/**
 * Valida um .glb/.gltf com o validador oficial da Khronos (gltf-validator) e imprime um resumo JSON:
 *   node ferramenta/js/validar-gltf.mjs <arquivo.glb>
 */
import { readFile } from "node:fs/promises";
import validator from "gltf-validator";

const arquivo = process.argv[2];
const dados = new Uint8Array(await readFile(arquivo));
const relatorio = await validator.validateBytes(dados, { maxIssues: 50 });
const { numErrors, numWarnings, numInfos, messages } = relatorio.issues;
process.stdout.write(JSON.stringify({
  erros: numErrors, avisos: numWarnings, infos: numInfos,
  mensagens: messages.slice(0, 20).map((m) => ({ codigo: m.code, texto: m.message, gravidade: m.severity, ponteiro: m.pointer })),
  info: relatorio.info,
}) + "\n");
