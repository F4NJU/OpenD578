import { stripTypeScriptTypes } from 'node:module';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { root, output } from './build.mjs';

// Dependency order is explicit: this small bundle has no external imports.
const modules = ['model', 'frequency', 'validation', 'json', 'editor', 'csv'];
const paths = [...modules.map(name => `src/core/${name}.ts`), 'src/device/oem-readonly.ts', 'src/device/bench-http.ts', 'src/ui/bench-panel.ts', 'src/ui/scan-panel.ts', 'src/ui/app.ts'];
const example = JSON.parse(await readFile(path.join(root, 'examples/analog.opend578.json'), 'utf8'));
const parts = [];
for (const sourcePath of paths) {
  let source = stripTypeScriptTypes(await readFile(path.join(root, sourcePath), 'utf8'));
  source = source.replace(/^import .*?;\r?$/gm, '').replace(/^export (?=(?:function|class|const|let)\b)/gm, '');
  if (sourcePath === 'src/ui/app.ts') {
    const fetchExample = "fetch('./examples/analog.opend578.json')";
    if (!source.includes(fetchExample)) throw new Error('Standalone example loader must be updated.');
    source = source.replace(fetchExample, `Promise.resolve(new Response(${JSON.stringify(JSON.stringify(example))}))`);
  }
  if (/^import\s/m.test(source)) throw new Error(`Unresolved import in ${sourcePath}`);
  parts.push(source);
}
const javascript = parts.join('\n').replace(/<\/script/gi, '<\\/script');
const css = await readFile(path.join(root, 'styles.css'), 'utf8');
let html = await readFile(path.join(root, 'index.html'), 'utf8');
html = html.replace('<link rel="stylesheet" href="./styles.css">', () => `<style>${css}</style>`)
  .replace('<script type="module" src="./src/ui/app.js"></script>', () => `<script type="module">${javascript}</script>`);
await mkdir(output, { recursive: true });
await writeFile(path.join(output, 'OpenD578-CPS.html'), html);
console.log('Version autonome : cps/dist/OpenD578-CPS.html');
