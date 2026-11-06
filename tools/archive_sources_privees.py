#!/usr/bin/env python3
"""Capture private, immutable HTML/IMG/CSS/PDF with SHA-256 and local navigation.

Runs on the user's computer. Raw publisher bytes remain unchanged, and public
OpenD578 never imports this output. Standard library only.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
import time
from datetime import datetime, timezone
from collections import deque
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, urlunsplit, unquote, urlencode, quote
from urllib.request import Request, urlopen

SOURCES = {
    'f1dmg': {
        'seeds': ['http://f1dmg.free.fr/page-20.htm', 'http://f1dmg.free.fr/578a', 'http://f1dmg.free.fr/'],
        'hosts': {'f1dmg.free.fr'}, 'crawl_pages': True,
    },
    'theweeks': {
        'seeds': ['https://www.theweeks.org/tmp/FILES/Anytone-Mods/578mods.htm'],
        'hosts': {'www.theweeks.org', 'theweeks.org'}, 'crawl_pages': False,
    },
    'vk7zja_v74': {
        'seeds': ['https://radio.carstenbauer.net/578techmods.htm'],
        'hosts': {'radio.carstenbauer.net'}, 'crawl_pages': False,
    },
    'vk7zja_mirror': {
        'seeds': ['https://www.reddicams.co.uk/radio/AnytoneJR/578techmods.htm'],
        'hosts': {'www.reddicams.co.uk', 'reddicams.co.uk'}, 'crawl_pages': False,
    },
    'vk7zja_authorised_mirror': {
        'seeds': ['https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php'],
        'hosts': {'www.db1ig.de', 'db1ig.de'}, 'crawl_pages': False,
    },
    'oz1dgq': {
        'seeds': ['https://qsl.net/oz1dgq/home-filer/anytone-hints.htm'],
        'hosts': {'qsl.net', 'www.qsl.net'}, 'crawl_pages': False,
    },
    'f1dmg_anytone': {
        'seeds': ['http://f1dmg.free.fr/page-20.htm', 'http://f1dmg.free.fr/page-22.htm'],
        'hosts': {'f1dmg.free.fr'}, 'crawl_pages': False,
    },
    'db1ig_anytone_related': {
        'seeds': [
            'https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php',
            'https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_878mods.php',
            'https://db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_dmrbasics.php',
        ],
        'hosts': {'www.db1ig.de','db1ig.de'}, 'crawl_pages': False,
    },
    'radiofoundry': {
        'seeds': ['https://radiofoundry.org/docs/spec/hardware-anytone'],
        'hosts': {'radiofoundry.org','www.radiofoundry.org'}, 'crawl_pages': False,
    },
    'fcc_d578': {
        'seeds': ['https://fccid.io/T4K-D578UV/Internal-Photos/Internal-Photos-4513250',
                  'https://fccid.io/T4K-D578UV2'],
        'hosts': {'fccid.io', 'www.fccid.io'}, 'crawl_pages': False,
    },
}
IMAGE_EXT={'.jpg','.jpeg','.png','.gif','.webp','.svg','.bmp','.tif','.tiff'}
DOC_EXT={'.pdf','.txt','.doc','.docx','.odt','.rtf','.csv'}
STYLE_EXT={'.css','.ico','.woff','.woff2'}
OPTIONAL_EXT={'.zip','.rar','.7z','.exe','.msi','.dll','.bin','.hex','.spi','.cdd','.rdt','.hpt','.mpg','.mp4'}
USER_AGENT='Mozilla/5.0 (compatible; OpenD578PersonalArchiver/1.0; offline historical research)'


def normal(url):
    p=urlsplit(url)
    if p.scheme.lower() not in ('http','https') or not p.hostname:
        return None
    # HTTP clients reject literal spaces in URL paths. Preserve existing %XX escapes.
    path=quote(p.path or '/', safe="/%:@!$&'()*+,;=-._~")
    query=quote(p.query, safe="=&?/%:@!$'()*+,;+-._~")
    return urlunsplit((p.scheme.lower(),p.netloc.lower(),path,query,''))


def relative_filename(url):
    p=urlsplit(url)
    segments=[]
    for part in unquote(p.path).split('/'):
        if part in ('','.','..'): continue
        safe=re.sub(r'[^a-zA-Z0-9._-]','_',part)[:120]
        if safe in ('.','..'): continue
        segments.append(safe or '_')
    if not segments or p.path.endswith('/'):
        segments.append('index.html')
    if not Path(segments[-1]).suffix:
        segments[-1]+='.html'
    if p.query:
        suffix=hashlib.sha256(p.query.encode('utf-8')).hexdigest()[:12]
        stem=Path(segments[-1]).stem
        ext=Path(segments[-1]).suffix
        segments[-1]=stem+'__q'+suffix+ext
    return Path(p.hostname or 'unknown').joinpath(*segments)


class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.images=[]
        self.pages=[]
        self.assets=[]
        self.outgoing=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag in ('img','source','video','audio'):
            for k in ('src','data-src','data-original','poster'):
                if d.get(k):self.images.append(d[k])
            for k in ('srcset','data-srcset'):
                if d.get(k):
                    for chunk in d[k].split(','):
                        self.images.append(chunk.strip().split()[0])
        if tag=='a' and d.get('href'):self.pages.append(d['href'])
        if tag=='link' and d.get('href'):self.assets.append(d['href'])
        if tag=='script' and d.get('src'):self.assets.append(d['src'])
        if tag in ('iframe','embed') and d.get('src'):self.outgoing.append(d['src'])


class PrivateArchive:
    def __init__(self,output,source='f1dmg',max_pages=150,max_assets=1000,
                 timeout=15,delay=0.5,include_tools=False,max_file_mb=40):
        self.output=Path(output)
        self.source=source
        self.config=SOURCES[source]
        self.max_pages=max_pages
        self.max_assets=max_assets
        self.timeout=timeout
        self.delay=delay
        self.include_tools=include_tools
        self.max_file_bytes=int(max_file_mb)*1024*1024
        self.todo=deque()
        self.seen=set()
        self.saved={}
        self.manifest=[]
        self.links=set()
        self.pages=0
        self.assets=0
        self.last_download=0.0
        self.output.mkdir(parents=True,exist_ok=True)
        for seed in self.config['seeds']:
            self.add(seed,'page',None)
    def add(self,url,kind,base):
        full=normal(urljoin(base or '',url))
        if not full or full in self.seen:return
        self.links.add(full)
        # Apache autoindex sorting does not add information and multiplies pages.
        if re.fullmatch(r'C=[NMSD];O=[AD]', urlsplit(full).query, re.I):return
        host=urlsplit(full).hostname
        if host not in self.config['hosts']:
            return
        ext=Path(urlsplit(full).path).suffix.lower()
        if ext in OPTIONAL_EXT and not self.include_tools:return
        if kind=='page' and not self.config['crawl_pages'] and full not in self.config['seeds']:return
        if kind=='page' and self.pages>=self.max_pages:return
        if kind!='page' and self.assets>=self.max_assets:return
        self.seen.add(full)
        self.todo.append((full,kind))
    def get(self,url):
        wait=self.delay-(time.monotonic()-self.last_download)
        if wait>0:time.sleep(wait)
        req=Request(url,headers={'User-Agent':USER_AGENT,'Accept':'text/html,image/*,application/pdf,*/*;q=0.5'})
        with urlopen(req,timeout=self.timeout) as resp:
            end=normal(resp.geturl())
            if not end or urlsplit(end).hostname not in self.config['hosts']:
                raise ValueError('Redirect outside the requested source domain')
            limit=self.max_file_bytes
            data=resp.read(limit+1)
            if len(data)>limit:raise ValueError(f'File exceeds per-file limit: {limit}')
            return data,resp.headers.get('Content-Type',''),end,int(resp.status)
    def run(self):
        while self.todo:
            url,kind=self.todo.popleft()
            if kind=='page':
                if self.pages>=self.max_pages:continue
                self.pages+=1
            else:
                if self.assets>=self.max_assets:continue
                self.assets+=1
            row={'url':url,'kind':kind,'timestamp_utc':datetime.now(timezone.utc).isoformat()}
            try:
                data,ctype,final,status=self.get(url)
                rel=relative_filename(url)
                path=self.output/'originals'/rel
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(data)
                row.update({'status':status,'final_url':final,'content_type':ctype,
                            'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),
                            'original_file':str(path.relative_to(self.output).as_posix())})
                self.saved[url]=str(path.relative_to(self.output).as_posix())
                if 'text/html' in ctype or Path(urlsplit(url).path).suffix.lower() in ('.html','.htm','.php'):
                    decoded=data.decode('utf-8',errors='replace')
                    parser=Links()
                    parser.feed(decoded)
                    for u in parser.images: self.add(u,'asset',url)
                    for u in parser.assets: self.add(u,'asset',url)
                    for u in parser.pages:
                        self.add_link_target(u,url)
                    for u in parser.outgoing:
                        full=normal(urljoin(url,u))
                        if full:self.links.add(full)
                if 'text/css' in ctype or path.suffix.lower()=='.css':
                    for u in re.findall(r'url\(\s*[\'\"]?([^\)\'\"]+)',data.decode('utf-8','replace')):
                        self.add(u,'asset',url)
                print(f'OK   {kind:5} {len(data):8} {url}',flush=True)
            except Exception as exc:
                row.update({'status':'ERROR','error':f'{type(exc).__name__}: {exc}'})
                print(f'FAIL {kind:5} {url} : {row["error"]}',flush=True)
            self.manifest.append(row)
            self.last_download=time.monotonic()
        self.write_index()
        return sum('sha256' in r for r in self.manifest)
    def add_link_target(self,u,base):
        full=normal(urljoin(base,u))
        if not full:return
        self.links.add(full)
        ext=Path(urlsplit(full).path).suffix.lower()
        if ext in IMAGE_EXT|DOC_EXT|STYLE_EXT:
            self.add(full,'asset',None)
        elif ext in OPTIONAL_EXT:
            if self.include_tools:self.add(full,'asset',None)
        elif ext in ('.htm','.html','.php','.shtml','.asp','.aspx',''):
            self.add(full,'page',None)
    def offline_copy(self):
        """Keep immutable originals; produce a second, locally linked HTML copy."""
        pattern=re.compile(r'(?P<attr>\b(?:src|href|poster|data-src)\s*=\s*)(?P<q>[\'\"])(?P<val>.*?)(?P=q)',re.I|re.S)
        count=0
        for row in self.manifest:
            if not ('sha256' in row and row['original_file'].lower().endswith(('.htm','.html','.php','.php.html'))):continue
            src=self.output/row['original_file']
            target=self.output/'offline'/Path(row['original_file']).relative_to('originals')
            target.parent.mkdir(parents=True,exist_ok=True)
            page_url=row['url']
            def change(match):
                full=normal(urljoin(page_url,html.unescape(match.group('val'))))
                local=self.saved.get(full)
                if not local:return match.group(0)
                path=os.path.relpath(self.output/local,target.parent).replace('\\','/')
                return match.group('attr')+match.group('q')+html.escape(path,quote=True)+match.group('q')
            original_bytes=src.read_bytes()
            declared=re.search(br'<meta[^>]+charset\s*=\s*[\"\']?([a-zA-Z0-9_-]+)',original_bytes[:4096],re.I)
            charset=(declared.group(1).decode('ascii') if declared else 'utf-8')
            try:
                raw=original_bytes.decode(charset,errors='strict')
            except (LookupError,UnicodeDecodeError):
                try:raw=original_bytes.decode('utf-8',errors='strict')
                except UnicodeDecodeError:raw=original_bytes.decode('cp1252',errors='replace')
            raw=re.sub(r'(?i)(<meta[^>]+charset\s*=\s*[\"\']?)([a-zA-Z0-9_-]+)',r'\g<1>utf-8',raw)
            target.write_text(pattern.sub(change,raw),encoding='utf-8')
            count+=1
        return count
    def write_index(self):
        self.offline_copy()
        result={'source':self.source,'seeds':self.config['seeds'],
                'captured_utc':datetime.now(timezone.utc).isoformat(),
                'notice':'Copy for private research; external copyright/licences remain with their authors.',
                'entries':self.manifest}
        (self.output/'manifest.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        (self.output/'links.txt').write_text('\n'.join(sorted(self.links))+'\n',encoding='utf-8')
        lines=['# Archive privee : '+self.source,'','Images, pages et documents telecharges ; les originaux sont preserves sans modification.',
               '','| Etat | Taille | Ressource d origine | Fichier |','|---|---:|---|---|']
        for row in self.manifest:
            f=row.get('original_file','')
            link=f'[local]({f})' if f else ('Erreur: '+row.get('error',''))
            lines.append(f"| {row['status']} | {row.get('bytes','')} | {row['url']} | {link} |")
        (self.output/'INDEX.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        with (self.output/'checksum.sha256').open('w',encoding='utf-8') as out:
            for row in self.manifest:
                if 'sha256' in row:out.write(f"{row['sha256']}  {row['original_file']}\n")
        valid=[r for r in self.manifest if r.get('original_file','').lower().endswith(('.html','.htm','.php','.php.html'))]
        items=[]
        for row in valid:
            rel='offline/'+str(Path(row['original_file']).relative_to('originals')).replace('\\','/')
            items.append(f'<li><a href="{html.escape(rel,quote=True)}">{html.escape(row["url"])}</a></li>')
        page='''<!doctype html><html lang="fr"><meta charset="utf-8"><title>Archive AnyTone privee</title>
<style>body{max-width:60rem;margin:3rem auto;font:16px system-ui;line-height:1.5;padding:0 1rem}</style>
<h1>Archives privees</h1><p>Pages originales recuperees a des fins de conservation personnelle.</p><ul>'''+''.join(items)+'</ul><p>Voir manifest.json, checksum.sha256 et links.txt pour les preuves de collecte.</p></html>'
        (self.output/'index.html').write_text(page,encoding='utf-8')


def wayback_latest(url,timeout=10):
    """Optional fallback: resolve an Internet Archive snapshot (not a claimed copy)."""
    endpoint='https://archive.org/wayback/available?'+urlencode({'url':url})
    try:
        req=Request(endpoint,headers={'User-Agent':USER_AGENT})
        with urlopen(req,timeout=timeout) as response:
            data=json.loads(response.read(200000).decode('utf-8'))
        info=data.get('archived_snapshots',{}).get('closest',{})
        result=normal(info.get('url','')) if info.get('available') else None
        if result and urlsplit(result).hostname=='web.archive.org':return result
    except Exception as exc:
        print(f'Wayback query failed for {url}: {exc}',file=sys.stderr)
    return None


def main(argv=None):
    ap=argparse.ArgumentParser(description='Archiver localement des pages AnyTone et leurs photographies.')
    ap.add_argument('--destination',default='archives_privees')
    ap.add_argument('--sites',nargs='+',choices=sorted(SOURCES),default=['f1dmg','theweeks','vk7zja_v74'])
    ap.add_argument('--max-pages',type=int,default=300)
    ap.add_argument('--max-assets',type=int,default=2500)
    ap.add_argument('--timeout',type=float,default=15)
    ap.add_argument('--delay',type=float,default=0.8)
    ap.add_argument('--max-file-mb',type=int,default=40,help='Maximum individual file size; no data is executed.')
    ap.add_argument('--include-tools',action='store_true',help='Also save linked binary executables/firmware and ZIP files; do not execute them.')
    ap.add_argument('--wayback',action='store_true',help='If F1DMG does not respond, attempt to capture known URLs from Wayback snapshots.')
    args=ap.parse_args(argv)
    base=Path(args.destination).expanduser().resolve()
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    run=base/stamp
    run.mkdir(parents=True,exist_ok=False)
    total=0
    for site in args.sites:
        print(f'===== {site} =====',flush=True)
        a=PrivateArchive(run/site,site,max_pages=args.max_pages,max_assets=args.max_assets,
                         timeout=args.timeout,delay=args.delay,include_tools=args.include_tools,max_file_mb=args.max_file_mb)
        saved=a.run()
        total+=saved
        if site=='f1dmg' and args.wayback:
            successful={r['url'] for r in a.manifest if 'sha256' in r}
            missing=[u for u in SOURCES['f1dmg']['seeds'] if u not in successful]
            snapshots=[]
            for original in missing:
                candidate=wayback_latest(original,args.timeout)
                if candidate and candidate not in snapshots:snapshots.append(candidate)
            if snapshots:
                key='f1dmg_wayback'
                SOURCES[key]={'seeds':snapshots,'hosts':{'web.archive.org'},'crawl_pages':False}
                print('===== f1dmg_wayback (historical snapshots) =====',flush=True)
                b=PrivateArchive(run/key,key,max_pages=args.max_pages,max_assets=args.max_assets,
                                 timeout=args.timeout,delay=args.delay,include_tools=args.include_tools,max_file_mb=args.max_file_mb)
                total+=b.run()
            elif missing: print('F1DMG: No accessible Wayback snapshot was discovered for missing seeds.',file=sys.stderr)
    summary={'timestamp_utc':stamp,'sites':args.sites,'saved_entries':total,'destination':str(run)}
    (run/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    if total==0:
        print('No data fetched. Consult each site INDEX.md for the error and try another mirror.',file=sys.stderr)
        return 2
    return 0

if __name__=='__main__':
    raise SystemExit(main())
