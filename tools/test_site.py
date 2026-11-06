#!/usr/bin/env python3
"""Fast sanity tests for generated static pages. Run after build_site.py."""
from pathlib import Path
import json
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'site'

class LocalLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag in ('a','script','link','img'):
            key='href' if tag in ('a','link') else 'src'
            if key in d:
                self.urls.append(d[key])


def main():
    mistakes=[]
    model_files=list((ROOT/'hardware/models').glob('*.json'))
    for mfile in model_files:
        model=json.loads(mfile.read_text(encoding='utf-8'))
        for node in model['nodes']:
            if not (SITE/'component'/model['id']/(node['id']+'.html')).is_file():
                mistakes.append('Missing component page '+node['id'])
        for edge in model['edges']:
            if not (SITE/'connection'/model['id']/(edge['id']+'.html')).is_file():
                mistakes.append('Missing edge page '+edge['id'])
    for htmlfile in SITE.rglob('*.html'):
        links=LocalLinks()
        links.feed(htmlfile.read_text(encoding='utf-8'))
        for uri in links.urls:
            path=urlsplit(uri)
            if path.scheme or path.netloc or uri.startswith('#') or uri.startswith('//'):
                continue
            if not path.path:
                continue
            target=(htmlfile.parent/unquote(path.path)).resolve()
            if not target.is_file():
                mistakes.append(f'{htmlfile.relative_to(SITE)} links to missing {uri}')
    if mistakes:
        print('Site validation FAILED:')
        print('\n'.join(mistakes[:100]));return 1
    files=list(SITE.rglob('*.html'))
    required=['index.html','docs.html','cps.html','doc/docs/cps/PROTOCOLE_OEM_V121.html','firmware.html','photos.html','doc/docs/LCD_CABLAGE_PILOTAGE_ET_INTEGRATION_V11_8.html']
    for path in required:
        if not (SITE/path).is_file():
            mistakes.append('Missing required page '+path)
    if mistakes:
        print('\n'.join(mistakes));return 1
    print('OK: validated',len(files),'HTML pages, local links, model pages, photos and source documentation')
    return 0

if __name__=='__main__':
    sys.exit(main())
