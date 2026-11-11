import http from 'node:http';
import path from 'node:path';
import { readFile } from 'node:fs/promises';
import { build, output } from './build.mjs';

await build();
const types = { '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.json': 'application/json' };
const server = http.createServer(async (request, response) => {
  try {
    const pathname = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
    const target = path.resolve(output, '.' + (pathname === '/' ? '/index.html' : pathname));
    if (!target.startsWith(output + path.sep)) { response.writeHead(403).end(); return; }
    const bytes = await readFile(target);
    response.writeHead(200, { 'Content-Type': types[path.extname(target)] ?? 'application/octet-stream',
      'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
      'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'" });
    response.end(bytes);
  } catch { response.writeHead(404).end('Introuvable'); }
});
server.on('error', error => { console.error(error.message); process.exitCode = 1; });
server.listen(Number(process.env.CPS_PORT ?? 8095), '127.0.0.1', () => console.log(`OpenD578 CPS : http://127.0.0.1:${server.address().port} — Ctrl+C pour arrêter`));
