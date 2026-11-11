import { stripTypeScriptTypes } from 'node:module';
import { readdir, readFile, mkdir, writeFile, copyFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

export const root = fileURLToPath(new URL('../', import.meta.url));
export const output = path.join(root, 'dist');

async function compile(directory) {
  for (const entry of await readdir(path.join(root, directory), { withFileTypes: true })) {
    const relative = path.join(directory, entry.name);
    if (entry.isDirectory()) { await compile(relative); continue; }
    if (!entry.name.endsWith('.ts')) continue;
    const source = await readFile(path.join(root, relative), 'utf8');
    const js = stripTypeScriptTypes(source).replace(/(from\s+['"][^'"]+)\.ts(['"])/g, '$1.js$2');
    const target = path.join(output, relative.replace(/\.ts$/, '.js'));
    await mkdir(path.dirname(target), { recursive: true });
    await writeFile(target, js);
  }
}

export async function build() {
  await mkdir(output, { recursive: true });
  await compile('src');
  for (const name of ['index.html', 'styles.css']) await copyFile(path.join(root, name), path.join(output, name));
  await mkdir(path.join(output, 'examples'), { recursive: true });
  await copyFile(path.join(root, 'examples/analog.opend578.json'), path.join(output, 'examples/analog.opend578.json'));
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await build(); console.log('CPS prêt dans cps/dist');
}
