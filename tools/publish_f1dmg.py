#!/usr/bin/env python3
"""Import only public-facing AnyTone material from an existing F1DMG archive.

No network access; no execution of files from the archive; only reads it.
This is a selective publisher, not a replacement for the private research archive.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from dataclasses import dataclass
from html.parser import HTMLParser
import hashlib
import html
import json
from pathlib import Path, PurePosixPath
import re
import shutil
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit
import zipfile

HOST = 'f1dmg.free.fr'
PAGES = ('page-20.htm', 'page-22.htm')
IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
DOC_EXT = {'.pdf', '.doc', '.docx', '.txt', '.odt', '.rtf'}
ROOT_IMAGES = {
    '578a.jpg', '578b.jpg', 'd578-protection-ros.png', 'debrid_578.jpg',
    'raz-anytone.png', 'roaming.png', 'boutons3.jpg',
}
ROOT_DOCUMENTS = {
    'd578-reglages.doc', 'mise_a_jour_d578.doc', 'mises_a_jour_pour_bt01.pdf',
    'cmd-roaming.doc', 'cmd-sms-anytone-2c.pdf', 'sms-d878.pdf', 'touchesd578.pdf',
}
PROVENANCE = 'F1DMG, publication autorisee oralement a Jean-Philippe F4EGM le 6 novembre 2026'
DROP_TAGS = {'script', 'style', 'iframe', 'object', 'embed', 'form', 'svg', 'noscript', 'template'}
SAFE_TAGS = {'p', 'div', 'span', 'b', 'strong', 'i', 'em', 'u', 'small', 'blockquote',
             'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'table', 'tbody',
             'thead', 'tfoot', 'tr', 'td', 'th', 'br', 'hr', 'pre', 'code', 'center',
             'sup', 'sub', 'a', 'img', 'figure', 'figcaption'}
VOID_TAGS = {'br', 'hr', 'img'}
IMAGE_MAGIC = (b'\xff\xd8\xff', b'\x89PNG\r\n\x1a\n', b'GIF87a', b'GIF89a', b'RIFF')


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def norm_url(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), unquote(parts.path), parts.query, ''))


def decode_html(data: bytes) -> str:
    m = re.search(rb'<meta[^>]+charset\s*=\s*["\']?([a-zA-Z0-9_-]+)', data[:10000], re.I)
    encodings = [m.group(1).decode('ascii') if m else 'utf-8', 'utf-8', 'cp1252', 'iso-8859-1']
    for encoding in dict.fromkeys(encodings):
        try:
            return data.decode(encoding)
        except (UnicodeError, LookupError):
            pass
    return data.decode('cp1252', errors='replace')


def simple_name(original: str) -> str:
    stem = re.sub(r'[^a-zA-Z0-9._-]+', '_', original.strip())
    return stem[:120] or 'document'


def category(name: str, context: str) -> str:
    val = (name + ' ' + context).lower()
    for pattern, title in [
        (r'578[ab]\.jpg|ventil|refroid|fan|cool|radiateur', 'Refroidissement'),
        (r'ros|swr|prote[cz]', 'Protection ROS'),
        (r'micro|01mb|02mb|03mb|jack|electret', 'Microphone et audio'),
        (r'button|bouton|clavier|facade|touch', 'Façade et commandes'),
        (r'raz|reset|gd32|cpu|pcb', 'Cartes et électronique'),
        (r'roam|bt01|bluetooth|cps|aprs|sms|debrid|menu', 'CPS et configuration'),
    ]:
        if re.search(pattern, val):
            return title
    return 'Autres illustrations'


def image_ok(data: bytes, suffix: str) -> bool:
    if suffix not in IMAGE_EXT or not any(data.startswith(m) for m in IMAGE_MAGIC):
        return False
    signatures = {'.jpg': b'\xff\xd8\xff', '.jpeg': b'\xff\xd8\xff', '.png': b'\x89PNG\r\n\x1a\n', '.gif': b'GIF', '.webp': b'RIFF'}
    if not data.startswith(signatures[suffix]) or len(data) < 16:
        return False
    return suffix != '.webp' or data[8:12] == b'WEBP'


class PageRefs(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.images = []
        self.docs = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == 'img':
            src = d.get('src') or d.get('data-src')
            if src:
                self.images.append({'url': src, 'alt': d.get('alt') or d.get('title') or '', 'kind': 'embedded'})
        if tag == 'a' and d.get('href'):
            link = d['href']
            suffix = Path(urlsplit(link).path).suffix.lower()
            if suffix in IMAGE_EXT:
                self.images.append({'url': link, 'alt': d.get('title') or '', 'kind': 'linked'})
            elif suffix in DOC_EXT:
                self.docs.append(link)


class SafePage(HTMLParser):
    """Restrictive copy of the author's text; excludes scripts, CSS and event handlers."""
    def __init__(self, base: str, image_map: dict[str, str], document_map: dict[str, str]):
        super().__init__(convert_charrefs=True)
        self.base = base
        self.image_map = image_map
        self.document_map = document_map
        self.skip = []
        self.stack = []
        self.out = []
        self.in_body = False
        self.has_body = False

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == 'body':
            self.in_body = True
            self.has_body = True
            return
        if tag == 'head':
            self.skip.append('head')
            return
        if self.skip:
            if tag in DROP_TAGS:
                self.skip.append(tag)
            return
        if tag in DROP_TAGS:
            self.skip.append(tag)
            return
        if tag not in SAFE_TAGS:
            return
        d = dict(attrs)
        if tag == 'img':
            raw = d.get('src') or d.get('data-src') or ''
            full = norm_url(urljoin(self.base, html.unescape(raw)))
            local = self.image_map.get(full)
            label = d.get('alt') or d.get('title') or Path(urlsplit(raw).path).name or 'Illustration'
            if local:
                # Span is valid inside historical <p> tags. A block-level <figure>
                # inside <p> detached the photo from its explanation.
                self.out.append('<span class="f1dmg-embedded-photo"><img loading="lazy" decoding="async" src="'+html.escape(local, quote=True)+'" alt="'+html.escape(label, quote=True)+'"><span class="f1dmg-inline-caption">'+html.escape(label)+'</span></span>')
            else:
                self.out.append('<span class="f1dmg-missing">Image mentionnée dans l’original mais non disponible : '+html.escape(label)+'</span>')
            return
        att = ''
        if tag == 'a':
            raw = d.get('href', '')
            full = norm_url(urljoin(self.base, html.unescape(raw))) if raw else ''
            if full in self.image_map:
                # A historic image can be linked by text instead of an img tag.
                # Local JS renders these links as inline thumbnails.
                dest = self.image_map[full]
                att = ' class="f1dmg-image-link" href="'+html.escape(dest, quote=True)+'" rel="noopener" target="_blank"'
            elif full in self.document_map:
                dest = self.document_map[full]
                att = ' href="'+html.escape(dest, quote=True)+'" rel="noopener"'
            elif urlsplit(full).scheme in {'http', 'https'}:
                att = ' href="'+html.escape(full, quote=True)+'" rel="noopener noreferrer" target="_blank"'
        if tag in {'td', 'th'}:
            for key in ('colspan', 'rowspan'):
                if d.get(key, '').isdigit() and 0 < int(d[key]) < 50:
                    att += ' '+key+'="'+d[key]+'"'
        self.out.append(f'<{tag}{att}>')
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == 'body':
            self.in_body = False
            return
        if self.skip:
            if tag == self.skip[-1]:
                self.skip.pop()
            return
        if tag in self.stack:
            while self.stack:
                closer = self.stack.pop()
                self.out.append(f'</{closer}>')
                if closer == tag:
                    break

    def handle_data(self, data):
        if not self.skip:
            self.out.append(html.escape(data))

    def handle_entityref(self, name):
        self.handle_data(html.unescape('&'+name+';'))

    def finish(self):
        while self.stack:
            self.out.append('</'+self.stack.pop()+'>')
        return ''.join(self.out)


@dataclass
class Archive:
    zf: zipfile.ZipFile
    prefix: str
    paths: dict[str, str]
    expected_hashes: dict[str, str]

    @classmethod
    def open(cls, zf):
        paths = {n.lower(): n for n in zf.namelist() if not n.endswith('/')}
        prefix = None
        for page in PAGES:
            suffix = 'originals/f1dmg.free.fr/' + page
            for name in zf.namelist():
                if not name.lower().endswith(suffix):
                    continue
                candidate = name[:-len(suffix)]
                # Support original ZIP with f1dmg/ as root or nested under a dated folder.
                if candidate == '' or candidate.lower().endswith('f1dmg/'):
                    prefix = candidate
                    break
            if prefix is not None:
                break
        if prefix is None:
            raise ValueError('Aucune archive F1DMG reconnue: page-20.htm/page-22.htm absentes')
        expected = {}
        manifest_key = (prefix + 'manifest.json').lower()
        if manifest_key in paths:
            manifest = json.loads(zf.read(paths[manifest_key]))
            for row in manifest.get('entries', []):
                if row.get('sha256') and row.get('original_file'):
                    key = (prefix + row['original_file'].replace('\\', '/')).lower()
                    expected[key] = row['sha256'].lower()
        return cls(zf, prefix, paths, expected)

    def find(self, relative: str) -> str | None:
        return self.paths.get((self.prefix + relative).lower())

    def read(self, name: str) -> bytes:
        data = self.zf.read(name)
        expect = self.expected_hashes.get(name.lower())
        if expect and sha256(data) != expect:
            raise ValueError('SHA-256 incorrect dans le ZIP : '+name)
        return data

    def lookup_url(self, url: str) -> str | None:
        p = urlsplit(url)
        if p.hostname and p.hostname.lower() != HOST:
            return None
        # Original archive crawler replaces unsafe characters in each path segment.
        segments = [simple_name(s) for s in unquote(p.path).split('/') if s and s not in {'.', '..'}]
        if not segments:
            return None
        rel = 'originals/f1dmg.free.fr/' + '/'.join(segments)
        if p.query:
            stem = Path(rel).stem
            ext = Path(rel).suffix
            rel = str(Path(rel).with_name(stem + '__q' + sha256(p.query.encode())[:12] + ext))
        return self.find(rel)


def derive_page_assets(arc: Archive, include_all_images: bool):
    page_html = {}
    image_references = defaultdict(list)
    doc_references = defaultdict(list)
    for page in PAGES:
        name = arc.find('originals/f1dmg.free.fr/' + page)
        if not name:
            continue
        base = 'http://f1dmg.free.fr/' + page
        source = decode_html(arc.read(name))
        page_html[page] = source
        refs = PageRefs()
        refs.feed(source)
        for entry in refs.images:
            full = norm_url(urljoin(base, html.unescape(entry['url'])))
            if urlsplit(full).hostname == HOST:
                image_references[full].append({'page': page, **entry})
        for entry in refs.docs:
            full = norm_url(urljoin(base, html.unescape(entry)))
            if urlsplit(full).hostname == HOST:
                doc_references[full].append(page)
    # Include known photographs and unlinked variants in the relevant AnyTone directories.
    for name in arc.zf.namelist():
        low = name.lower()
        token = '/originals/f1dmg.free.fr/'
        if token not in low or Path(name).suffix.lower() not in IMAGE_EXT:
            continue
        tail = name[len(name[:low.index(token)])+len(token):]
        if tail.lower().startswith(('page-20/', 'page-22/')) or Path(tail).name.lower() in ROOT_IMAGES or include_all_images:
            full = norm_url('http://' + HOST + '/' + tail)
            image_references[full].append({'page': 'Archive F1DMG', 'url': tail, 'alt': '', 'kind': 'archive'})
    for name in arc.zf.namelist():
        low = name.lower()
        token = '/originals/f1dmg.free.fr/'
        if token not in low or Path(name).suffix.lower() not in DOC_EXT:
            continue
        tail = name[low.index(token)+len(token):]
        if Path(tail).name.lower() in ROOT_DOCUMENTS:
            full = norm_url('http://' + HOST + '/' + tail)
            doc_references[full].append('Archive F1DMG')
    return page_html, image_references, doc_references


def publish(archive_path: Path, repo: Path, dry_run=False, include_all_images=False, include_documents=True):
    destination = repo / 'site-assets' / 'f1dmg'
    with zipfile.ZipFile(archive_path) as zf:
        arc = Archive.open(zf)
        pages, images, docs = derive_page_assets(arc, include_all_images)
        if not pages:
            raise ValueError('Le ZIP ne contient aucune page F1DMG exploitable')
        photo_rows = []
        document_rows = []
        missing = []
        save_images = {}
        save_docs = {}
        map_images = {}
        map_docs = {}
        for url, refs in sorted(images.items()):
            name = arc.lookup_url(url)
            if not name:
                missing.append({'source': url, 'pages': sorted({x['page'] for x in refs})})
                continue
            data = arc.read(name)
            ext = Path(name).suffix.lower()
            if not image_ok(data, ext):
                missing.append({'source': url, 'reason': 'Image invalide ou non prise en charge'})
                continue
            digest = sha256(data)
            filename = digest[:12] + '_' + simple_name(Path(name).name)
            relative = 'photos/' + filename
            save_images[relative] = data
            label = next((x['alt'].strip() for x in refs if x.get('alt', '').strip()), Path(name).stem.replace('_', ' '))
            photo_rows.append({
                'file': relative, 'title': label[:180], 'category': category(Path(name).name, label),
                'source': url, 'sha256': digest, 'bytes': len(data),
                'pages': sorted({x['page'] for x in refs}),
                'archived_as': name, 'credit': 'F1DMG (site source, auteur de chaque image à vérifier si reprise tierce)',
            })
            map_images[url] = relative
        if include_documents:
            for url, page_refs in sorted(docs.items()):
                name = arc.lookup_url(url)
                if not name or Path(name).suffix.lower() not in DOC_EXT:
                    continue
                data = arc.read(name)
                digest = sha256(data)
                filename = digest[:12] + '_' + simple_name(Path(name).name)
                relative = 'documents/' + filename
                save_docs[relative] = data
                map_docs[url] = relative
                document_rows.append({'file': relative, 'source': url, 'sha256': digest,
                                      'bytes': len(data), 'pages': sorted(set(page_refs))})
        reports = {'version': 1, 'source_archive': archive_path.name,
                   'authorization': PROVENANCE,
                   'scope': 'Pages AnyTone page-20.htm et page-22.htm, images de ces pages et images AnyTone archivées',
                   'photos': photo_rows, 'documents': document_rows,
                   'missing_images': missing, 'pages': sorted(pages)}
        if dry_run:
            return reports
        destination.mkdir(parents=True, exist_ok=True)
        # Avoid deleting any source files. Remove only stale photo/document files previously generated by this importer.
        previous = destination / 'publication.json'
        if previous.is_file():
            try:
                old = json.loads(previous.read_text(encoding='utf-8'))
                new_names = set(save_images) | set(save_docs)
                for obj in old.get('photos', []) + old.get('documents', []):
                    old_file = obj.get('file')
                    if old_file and old_file not in new_names and re.fullmatch(r'(photos|documents)/[a-f0-9]{12}_[\w.\-]+', old_file):
                        (destination / old_file).unlink(missing_ok=True)
            except (ValueError, OSError):
                pass
        for rel, data in {**save_images, **save_docs}.items():
            path = destination / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists() or sha256(path.read_bytes()) != sha256(data):
                path.write_bytes(data)
        source_pages = destination / 'pages'
        source_pages.mkdir(exist_ok=True)
        for page, raw in pages.items():
            safe = SafePage('http://f1dmg.free.fr/' + page,
                            {u: p for u, p in map_images.items()},
                            {u: p for u, p in map_docs.items()})
            safe.feed(raw)
            fragment = safe.finish()
            (source_pages / page.replace('.htm', '.fragment.html')).write_text(fragment, encoding='utf-8')
        (destination / 'publication.json').write_text(json.dumps(reports, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        return reports


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--archive', type=Path, required=True, help='ZIP source 20261106T102717Z.zip')
    ap.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1], help='Racine du dépôt OpenD578')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--include-all-f1dmg-images', action='store_true', help='Inclure aussi les images des rubriques F1DMG sans lien AnyTone')
    ap.add_argument('--no-documents', action='store_true', help='Ne pas publier les PDF/DOC liés dans les deux pages')
    args = ap.parse_args()
    if not args.archive.is_file():
        ap.error('Archive introuvable : '+str(args.archive))
    report = publish(args.archive, args.repo, args.dry_run, args.include_all_f1dmg_images, not args.no_documents)
    print(f"Pages: {len(report['pages'])}, images présentes: {len(report['photos'])}, images absentes: {len(report['missing_images'])}, documents: {len(report['documents'])}")
    if args.dry_run:
        print('Mode prévisualisation : aucun fichier modifié')
    else:
        print('Publication préparée sous site-assets/f1dmg. Contrôler les droits des œuvres tierces intégrées avant push.')

if __name__ == '__main__':
    main()
