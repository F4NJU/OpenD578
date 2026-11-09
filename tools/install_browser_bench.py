#!/usr/bin/env python3
"""Additive installer for OpenD578 Browser Bench, compatible with existing
F1DMG / other site changes. Fails without touching existing files if an
expected anchor is missing or ambiguous.

Copyright (C) 2026 OpenD578 contributors. GPL-3.0-or-later.
"""
from __future__ import annotations
import argparse
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / 'tools' / 'build_site.py'
PAGES = ROOT / '.github' / 'workflows' / 'pages.yml'


def insert_unique(text: str, anchor: str, insert: str, what: str) -> str:
    if text.count(anchor) != 1:
        raise RuntimeError(f'{what}: ancre absente ou non unique (aucune modification)')
    return text.replace(anchor, insert + anchor, 1)


def edit_build(source: str) -> str:
    nav_link = "('simulator/index.html','Simulateur')"
    if nav_link not in source:
        # Insert immediately before Docs, which survives the F1DMG overlay.
        source = insert_unique(source, "('docs.html','Documents')", nav_link + ',', 'navigation')

    # Source index should include .mjs / browser-bench for site source listing.
    for field, member in [('groups', 'browser-bench'), ('exts', '.mjs')]:
        pattern = re.compile(r'(?P<prefix>\b' + field + r'\s*=\s*)(?P<value>\[[^\]\n]*\]|\{[^}\n]*\})')
        matches = list(pattern.finditer(source))
        if len(matches) != 1:
            raise RuntimeError(f'{field}: definition absente ou ambigue (aucune modification)')
        m = matches[0]
        original = m.group('value')
        items = ast.literal_eval(original)
        if not isinstance(items, (list, set)):
            raise RuntimeError(f'{field}: type inattendu')
        if member not in items:
            suffix = original[-1]
            inner = original[1:-1].rstrip()
            sep = ',' if inner and not inner.endswith(',') else ''
            new_value = original[0] + inner + sep + repr(member) + suffix
            source = source[:m.start('value')] + new_value + source[m.end('value'):]

    if "browser_source = ROOT/'browser-bench'" not in source:
        copy_block = """    # Browser bench lives in source; site/ is regenerated on each build.
    browser_source = ROOT/'browser-bench'
    if browser_source.is_dir():
        shutil.copytree(browser_source, SITE/'simulator',
                        ignore=shutil.ignore_patterns('tests', '__pycache__'),
                        dirs_exist_ok=True)
"""
        source = insert_unique(source, "    (SITE/'.nojekyll').touch()", copy_block, 'copie browser-bench')

    ast.parse(source, filename='tools/build_site.py')
    return source


def edit_workflow(source: str) -> str:
    test_cmd = 'node --test browser-bench/tests/*.test.mjs'
    if test_cmd not in source:
        source = insert_unique(source, '      - name: Configure Pages\n',
            '      - name: Validate browser bench (offline, no npm dependencies)\n'
            f'        run: {test_cmd}\n', 'GitHub Actions')
    return source


def plan() -> tuple[str, str, bool, bool]:
    if not (ROOT/'browser-bench'/'index.html').exists():
        raise RuntimeError('Dossier browser-bench absent de la racine du depot')
    if not BUILD.exists() or not PAGES.exists():
        raise RuntimeError('tools/build_site.py ou .github/workflows/pages.yml absent')
    old_build = BUILD.read_text(encoding='utf-8')
    old_pages = PAGES.read_text(encoding='utf-8')
    new_build = edit_build(old_build)
    new_pages = edit_workflow(old_pages)
    return new_build, new_pages, new_build != old_build, new_pages != old_pages


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    try:
        build, pages, changed_build, changed_pages = plan()
    except Exception as error:
        print(f'ERREUR : {error}')
        return 1
    if args.check:
        print(f'OK : installation possible; build_site.py={changed_build}, pages.yml={changed_pages}')
        return 0
    if changed_build:
        BUILD.write_text(build, encoding='utf-8')
    if changed_pages:
        PAGES.write_text(pages, encoding='utf-8')
    print(f'OK : site modifie={changed_build}; workflow modifie={changed_pages}')
    print('Etapes : node --test browser-bench/tests/*.test.mjs ; python3 tools/build_site.py')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
