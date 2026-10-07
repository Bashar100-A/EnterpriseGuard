#!/usr/bin/env node
// Minimal HTTP server: serves browser-test dir + captures POST /result.
import { createServer } from 'node:http';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join, extname } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PORT = 8765;
const MIME = { '.html':'text/html', '.js':'text/javascript', '.wasm':'application/wasm' };

let gotResult = false;
const server = createServer((req, res) => {
  if (req.method === 'POST' && req.url === '/result') {
    let body = '';
    req.on('data', d => body += d);
    req.on('end', () => {
      process.stdout.write('===BROWSER_RESULT_BEGIN===\n');
      process.stdout.write(body);
      process.stdout.write('\n===BROWSER_RESULT_END===\n');
      res.writeHead(200); res.end('OK');
      gotResult = true;
      setTimeout(() => { server.close(); process.exit(0); }, 200);
    });
    return;
  }
  const rel = req.url === '/' ? '/index.html' : req.url;
  const path = join(__dirname, rel);
  try {
    const data = readFileSync(path);
    res.writeHead(200, { 'Content-Type': MIME[extname(path)] || 'application/octet-stream' });
    res.end(data);
  } catch {
    res.writeHead(404); res.end('not found');
  }
});
server.listen(PORT, '127.0.0.1', () => {
  process.stdout.write(`server up on :${PORT}\n`);
});
setTimeout(() => {
  if (!gotResult) {
    process.stdout.write('TIMEOUT_NO_RESULT\n');
    process.exit(2);
  }
}, 45000);
