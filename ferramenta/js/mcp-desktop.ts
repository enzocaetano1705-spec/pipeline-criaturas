/**
 * Cliente MCP HTTP mínimo para o servidor do Blockbench desktop (plugin MCP, http://localhost:3000/bb-mcp).
 *
 * Usa o SDK oficial do MCP (MIT) que o clone fixado do motor já instalou em
 * externos/blockbench-mcp-plugin/node_modules; nada do plugin (GPL-3.0) é copiado.
 *
 *   bun run ferramenta/js/mcp-desktop.ts <url> <ferramenta> [@args.json | '{json}']
 *   bun run ferramenta/js/mcp-desktop.ts <url> --list
 *
 * Imprime o resultado da ferramenta em JSON ({content, isError}). Código 1 se a ferramenta deu erro.
 */

import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const raiz = resolve(import.meta.dir, "..", "..");
const sdk = join(raiz, "externos", "blockbench-mcp-plugin", "node_modules", "@modelcontextprotocol", "sdk", "dist", "esm");
const { Client } = await import(pathToFileURL(join(sdk, "client", "index.js")).href);
const { StreamableHTTPClientTransport } = await import(pathToFileURL(join(sdk, "client", "streamableHttp.js")).href);

const [url, ferramenta, bruto] = process.argv.slice(2);
if (!url || !ferramenta) {
  console.error("uso: mcp-desktop.ts <url> <ferramenta> [@args.json | '{json}'] | --list");
  process.exit(2);
}

async function argumentos(texto: string | undefined): Promise<Record<string, unknown>> {
  if (!texto) return {};
  const conteudo = texto.startsWith("@") ? await Bun.file(texto.slice(1)).text() : texto;
  return JSON.parse(conteudo);
}

const cliente = new Client({ name: "criaturas-pipeline", version: "1.0.0" });
await cliente.connect(new StreamableHTTPClientTransport(new URL(url)));
try {
  if (ferramenta === "--list") {
    const { tools } = await cliente.listTools();
    process.stdout.write(JSON.stringify(tools.map((t: { name: string }) => t.name)) + "\n");
  } else {
    const resultado = await cliente.callTool({ name: ferramenta, arguments: await argumentos(bruto) }, undefined, { timeout: 600_000 });
    process.stdout.write(JSON.stringify(resultado) + "\n");
    if (resultado.isError) process.exitCode = 1;
  }
} finally {
  await cliente.close();
}
