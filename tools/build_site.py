#!/usr/bin/env python3
"""Build a fully static, GitHub-Pages-compatible documentation site.

All rendered pages are derived on each push from the original Markdown files.
No separate web copy of documentation is maintained. No JS framework or CDN.
"""
from __future__ import annotations

import html
import json
import os
import re
import shutil
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, unquote, quote

try:
    import mistune
except ImportError as ex:
    raise SystemExit('Install dependencies: python -m pip install -r site-requirements.txt') from ex

from validate_hardware_model import check

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'site'
GITHUB='https://github.com/Telectroboy/OpenD578'
SOURCES=('docs','firmware','hardware')
BASIC=['README.md','README_FR.md','README_SITE.md','CONTRIBUTING.md','PROVENANCE.md']


def x(s):
    return html.escape(str(s),quote=True)


def relative(from_file:Path,to_file:Path):
    return Path(os.path.relpath(to_file,from_file.parent)).as_posix()


def slug(text):
    text=html.unescape(re.sub('<[^>]*>','',text))
    text=unicodedata.normalize('NFKD',text).encode('ascii','ignore').decode().lower()
    text=re.sub(r'[^a-z0-9 _-]','',text).strip()
    return re.sub(r'[ _]+','-',text) or 'section'


def doc_output(path:Path):
    return SITE/'doc'/path.with_suffix('.html')


def to_repo_relative(src:Path):
    return src.resolve().relative_to(ROOT.resolve())


class PageMarkdown(mistune.HTMLRenderer):
    def __init__(self, source:Path, output:Path):
        super().__init__(escape=True)
        self.source=source
        self.output=output
        self.slugs={}

    def heading(self, text, level, **attrs):
        base=slug(text)
        index=self.slugs.get(base,0)
        self.slugs[base]=index+1
        anchor=base if index==0 else f'{base}-{index}'
        return f'<h{level} id="{x(anchor)}">{text}</h{level}>\n'

    def rewrite(self, url:str, image=False):
        u=urlsplit(url)
        if u.scheme or u.netloc or url.startswith('#') or url.startswith('//'):
            return url
        if not u.path:
            return url
        source=(self.source.parent/unquote(u.path)).resolve()
        try:
            rel=source.relative_to(ROOT.resolve())
        except ValueError:
            return url
        if not source.is_file():
            return url
        if rel.suffix.lower()=='.md' and not image:
            target=doc_output(rel)
            return relative(self.output,target)+(('#'+u.fragment) if u.fragment else '')
        if image and rel.suffix.lower() in ('.png','.jpg','.jpeg','.webp','.svg','.gif'):
            target=SITE/'raw'/rel
            return relative(self.output,target)
        return GITHUB+'/blob/main/'+quote(rel.as_posix())

    def link(self,text,url,title=None):
        return super().link(text,self.rewrite(url),title)

    def image(self,text,url,title=None):
        return super().image(text,self.rewrite(url,True),title)


def title_of(path:Path):
    data=path.read_text(encoding='utf-8')
    for line in data.splitlines()[:25]:
        if line.startswith('# '):
            return line[2:].strip()
    return path.stem.replace('_',' ')


def discover_docs():
    files=[]
    for p in BASIC:
        f=ROOT/p
        if f.is_file():
            files.append(f)
    for folder in SOURCES:
        if not (ROOT/folder).is_dir():
            continue
        files += sorted((ROOT/folder).rglob('*.md'))
    return sorted(set(files))


def category(rel:str):
    if rel.startswith('docs/evidence/'):
        return 'Preuves et tracabilite'
    if rel.startswith('docs/peripherals/'):
        return 'Peripheriques techniques'
    if rel.startswith('docs/archives/'):
        return 'Inventaire des originaux'
    if rel.startswith('docs/cps/'):
        return 'CPS / programmation'
    if rel.startswith('hardware/'):
        return 'Materiel / CAO et brochage'
    if rel.startswith('docs/hardware/'):
        return 'Materiel'
    if rel.startswith('docs/firmware/') or rel.startswith('firmware/'):
        return 'Firmware alternatif'
    if rel.startswith('docs/'):
        return 'Recherche et banc'
    return 'Projet'


def nav(dest:Path,active:str=''):
    links=[('index.html','Vue eclatee'),('docs.html','Documents'),('cps.html','CPS / USB'),('doc/docs/evidence/INDEX.html','Preuves'),('firmware.html','Firmware'),('photos.html','Photos'),('sources.html','Code source')]
    out=['<nav class="nav" aria-label="Navigation">']
    for name,label in links:
        clazz=' class="active"' if name==active else ''
        out.append(f'<a{clazz} href="{x(relative(dest,SITE/name))}">{x(label)}</a>')
    out.append(f'<a href="{GITHUB}" rel="noopener" target="_blank">Depot GitHub</a></nav>')
    return '\n'.join(out)


def shell(title:str,output:Path,body:str,active:str=''):
    css=relative(output,SITE/'assets/site.css')
    js=relative(output,SITE/'assets/site.js')
    models=relative(output,SITE/'assets/models.js')
    search=relative(output,SITE/'assets/search-data.js')
    return f'''<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="OpenD578: cartographie materielle, reverse engineering et firmware alternatif D578UV PRO GD32">
<title>{x(title)} - OpenD578</title>
<link rel="stylesheet" href="{x(css)}"></head>
<body><header class="site-header"><div class="brand"><a href="{x(relative(output,SITE/'index.html'))}">OpenD578</a><span> | Documentation materielle et firmware</span></div>{nav(output,active)}</header>
<main class="container">{body}</main>
<footer class="site-footer">Documentation evolutive - faits materiels, observations OEM et hypotheses distingues. Pas de firmware installable.</footer>
<script src="{x(models)}" defer></script><script src="{x(search)}" defer></script><script src="{x(js)}" defer></script>
</body></html>'''


def write(path:Path,s:str):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(s,encoding='utf-8')


def doc_link(output:Path,rel:str):
    return relative(output,doc_output(Path(rel)))


def source_link(rel:str):
    return GITHUB+'/blob/main/'+quote(rel)


def evidence(output:Path,docs):
    return ''.join(f'<li><a href="{x(doc_link(output,d))}">{x(title_of(ROOT/d))}</a> <small><a href="{x(source_link(d))}">source</a></small></li>' for d in docs)


def build_docs(files):
    catalog=[]
    for src in files:
        rel=to_repo_relative(src)
        rel_text=rel.as_posix()
        target=doc_output(rel)
        data=src.read_text(encoding='utf-8')
        renderer=PageMarkdown(src,target)
        md=mistune.create_markdown(renderer=renderer,plugins=['table','strikethrough','task_lists','url'])
        rendered=md(data)
        raw=SITE/'raw'/rel
        raw.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,raw)
        page=f'''<div class="breadcrumb"><a href="{x(relative(target,SITE/'docs.html'))}">Documents</a> / {x(category(rel_text))}</div>
<div class="doc-heading"><h1>{x(title_of(src))}</h1><div class="doc-actions"><a href="{x(source_link(rel_text))}">Modifier sur GitHub</a><a download href="{x(relative(target,raw))}">Telecharger .md</a></div></div>
<p class="muted small">Source unique : <code>{x(rel_text)}</code></p>
<article class="markdown-body">{rendered}</article>'''
        write(target,shell(title_of(src),target,page,'docs.html'))
        clean=re.sub(r'[`*_>#\[\]()]',' ',data)
        clean=re.sub(r'\s+',' ',clean).strip()
        catalog.append(dict(path=rel_text,title=title_of(src),category=category(rel_text),body=clean[:25000],url=relative(SITE/'docs.html',target)))
    return catalog


def hardware_pages(models):
    for model in models:
        vid=model['id']
        id_to_node={n['id']:n for n in model['nodes']}
        for n in model['nodes']:
            target=SITE/'component'/vid/f"{n['id']}.html"
            refs=evidence(target,n['docs'])
            edges=[]
            for e in model['edges']:
                if n['id'] in (e['source'],e['target']):
                    other=id_to_node[e['target'] if e['source']==n['id'] else e['source']]
                    link=relative(target,SITE/'connection'/vid/f"{e['id']}.html")
                    edges.append(f'<li><a href="{x(link)}">{x(e["label"])}</a> - {x(other["label"])} <span class="tag">{x(e["status"])}</span></li>')
            body=f'''<div class="breadcrumb"><a href="{x(relative(target,SITE/'index.html'))}">Vue eclatee</a> / {x(model['title'])}</div>
<h1>{x(n['label'])}</h1><p>{x(n['description'])}</p><dl class="facts"><dt>Groupe</dt><dd>{x(n['group'])}</dd><dt>Statut</dt><dd>{x(n['confidence'])}</dd><dt>Variante</dt><dd>{x(model['title'])}</dd></dl>
<h2>Connexions</h2><ul class="link-list">{''.join(edges) or '<li>Pas de liaison documentee</li>'}</ul><h2>Notices et preuves</h2><ul>{refs}</ul>'''
            write(target,shell(n['label'],target,body))
        for e in model['edges']:
            target=SITE/'connection'/vid/f"{e['id']}.html"
            src=id_to_node[e['source']]
            dst=id_to_node[e['target']]
            rows=''.join('<tr><td><code>'+x(p['from_pin'])+'</code></td><td>'+x(p['to_pin'])+'</td><td>'+x(p.get('status',''))+'</td></tr>' for p in e['pins'])
            if not rows:
                rows='<tr><td colspan="3">Broches non qualifiees : ne pas attribuer de GPIO par deduction.</td></tr>'
            body=f'''<div class="breadcrumb"><a href="{x(relative(target,SITE/'index.html'))}">Vue eclatee</a> / Liaison {x(e['id'])}</div>
<h1>{x(e['label'])}</h1>
<p><a href="{x(relative(target,SITE/'component'/vid/(src['id']+'.html')))}">{x(src['label'])}</a> &rarr; <a href="{x(relative(target,SITE/'component'/vid/(dst['id']+'.html')))}">{x(dst['label'])}</a></p>
<dl class="facts"><dt>Bus</dt><dd>{x(e['bus'])}</dd><dt>Niveau de preuve</dt><dd>{x(e['status'])}</dd><dt>Variante</dt><dd>{x(model['title'])}</dd></dl>
<p>{x(e['details'])}</p><h2>Signaux</h2><div class="table-scroll"><table><thead><tr><th>MCU / source</th><th>Signal destination</th><th>Preuve</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Notices et traces</h2><ul>{evidence(target,e['docs'])}</ul>'''
            write(target,shell(e['label'],target,body))


def index_page(models,docs):
    dest=SITE/'index.html'
    modopts=''.join(f'<option value="{x(m["id"])}">{x(m["title"])}</option>' for m in models)
    first=models[0]
    featured=[i for i in docs if any(s in i['path'] for s in ['LCD_CABLAGE','FACADE_GPIO','NOTICE_CHANGELOG_MICRO','03_NAND','02_CPU','ROADMAP'])]
    featured=featured[:7]
    links=''.join(f'<li><a href="{x(doc_link(dest,d["path"]))}">{x(d["title"])}</a></li>' for d in featured)
    body=f'''<h1>Explorateur materiel du D578</h1>
<p class="lead"><span id="model-intro">Vue eclatee documentaire du D578UV PRO GD32 V1.21.</span> Cliquez sur un <strong>composant</strong> ou une <strong>liaison</strong> pour voir les signaux, les preuves et les notices d'origine.</p>
<p class="muted small">Important : vue logique, <strong>pas</strong> implantation physique ni releve de pistes. Les liaisons non confirmees sont distinguees et ne constituent pas un brochage utilisable.</p>
<section class="explorer" id="hardware-explorer">
<div class="toolbar">
<label>Variante <select id="variant-select">{modopts}</select></label>
<label>Zone <select id="group-filter"><option value="all">Toutes les zones</option><option value="facade">Façade</option><option value="logique">Carte logique</option><option value="peripheriques">Peripheriques</option><option value="radio">RF / antenne</option></select></label>
<label>Preuve <select id="status-filter"><option value="all">Toutes</option><option value="physical">Materiel</option><option value="oem_trace">Trace OEM</option><option value="emulator">Emulation</option><option value="hypothesis">Hypothese</option><option value="unknown">Inconnue</option></select></label>
<label class="filter-input">Rechercher <input id="part-filter" type="search" placeholder="LCD, PB10, NAND, GPS..."></label>
</div>
<div class="explorer-content"><div class="diagram-col">
<div id="diagram-wrap" tabindex="0" aria-label="Carte des composants; defilement horizontal possible"><svg id="hardware-svg" viewBox="0 0 1280 824" role="img" aria-label="Diagramme materiel cliquable"></svg></div>
<div class="diagram-key"><span>Ligne continue : observation</span><span>Ligne en tirets : modele/hypothese</span><span>Ligne pointillee : broches inconnues</span></div>
</div><aside class="inspector" id="inspector" aria-live="polite"><h2>Selection</h2><p>Selectionner un bloc ou un trajet dans le dessin.</p></aside></div></section>
<section class="home-bottom"><div><h2>Documentation technique</h2><ul class="link-list">{links}</ul><p><a href="docs.html">Voir tous les documents, avec recherche</a></p></div>
<div><h2>Firmware alternatif</h2><p>Architecture, pilotes et tests independants, sans image flashable. La NAND et les zones de calibration sont conservees.</p>
<p><a href="firmware.html">Ouvrir l'espace firmware</a></p><h2>Communication CPS</h2><p>USB CDC, commandes de programmation, codeplug et tests.</p><p><a href="cps.html">Ouvrir le dossier CPS</a></p><h2>Photographies</h2><p>References FCC et images de cartes propres a la revision des qu'elles sont annotees.</p><p><a href="photos.html">Acceder aux photos</a></p></div></section>'''
    write(dest,shell('Explorateur materiel',dest,body,'index.html'))


def docs_page(docs):
    dest=SITE/'docs.html'
    body='''<h1>Documents Markdown</h1><p>Une seule source : les fichiers <code>.md</code> du depot. La lecture integree, les liens GitHub et les telechargements sont regeneres a chaque commit.</p>
<label class="search-field">Recherche dans les titres et le contenu <input id="docs-search" type="search" placeholder="ADC, EEPROM, SWD, 0x08006000..."></label>
<p class="muted small" id="search-count"></p><div id="search-results" class="docs-grid" aria-live="polite"></div>'''
    write(dest,shell('Documents',dest,body,'docs.html'))


def cps_page(docs):
    dest=SITE/'cps.html'
    ordered=['docs/cps/README.md','docs/cps/USB_CDC_GD32_V121.md',
             'docs/cps/PROTOCOLE_OEM_V121.md','docs/cps/CODEPLUG_CANAL_OEM_V121.md',
             'docs/cps/CPS_ARCHITECTURE_SIMULATION.md','docs/cps/COMPATIBILITE_PRO_PLUS.md',
             'docs/cps/CPS_QUALIFICATION.md',
             'docs/USB_CPS_V11_5.md','docs/CPS_INTEGRE_V11_6.md',
             'docs/SOURCES_EXTERNES_ET_RECOUPEMENTS_20261105.md']
    links=''.join('<li><a href="'+x(doc_link(dest,rel))+'">'+x(title_of(ROOT/rel))+'</a></li>'
                  for rel in ordered if (ROOT/rel).is_file())
    body=f'''<h1>Programmation PC : CPS, USB et codeplug</h1>
<p class="lead">Protocole AnyTone OEM D578UV PRO GD32 V1.21, simulation de la communication serie USB et structure de la NAND.</p>
<p class="muted small">Les lectures et ecritures de noms ont ete testees avec le firmware OEM dans le banc V11.7. La compatibilite totale du CPS Windows et celle d'un firmware alternatif ne sont pas validees.</p>
<div class="stack"><section class="panel"><h2>Chemin de programmation</h2><pre>PC / CPS -&gt; USB CDC 28E9:018A -&gt; GD32F303 -&gt; gestionnaire NAND -&gt; codeplug</pre>
<p>PROGRAM / identite / R / W / END. Les commandes d'ecriture sont tamponnees et l'ACK de END precede la finalisation de certaines metadonnees NAND.</p></section>
<section class="panel"><h2>Outils et sources du banc</h2><p><code>bench/cps_bridge.py</code>, <code>bench/cps_probe.py</code>, <code>bench/usb_cdc.py</code>, <code>bench/usbd_host.py</code>, <code>bench/web/mini_cps_protocol.js</code>.</p>
<p><a href="{x(source_link('tools/cps_trace_audit.py'))}">Audit hors ligne des journaux CPS</a></p></section></div>
<h2>Fiches detaillees</h2><ul class="link-list">{links}</ul>'''
    write(dest,shell('CPS et USB',dest,body,'cps.html'))


def firmware_page(docs):
    dest=SITE/'firmware.html'
    f=[d for d in docs if d['category']=='Firmware alternatif' or 'docs/ROADMAP.md'==d['path'] or d['path']=='docs/EMULATOR.md' or d['path']=='docs/05_SATELLITE_CODE_INTEGRATION_EXP06.md']
    links=''.join(f'<li><a href="{x(doc_link(dest,d["path"]))}">{x(d["title"])}</a></li>' for d in f)
    body=f'''<h1>Developpement firmware alternatif</h1><p class="lead">Zone de travail reservee aux pilotes autonomes, a l'application radio et aux tests. Le depot contient aujourd'hui un simulateur et des notes de recherche, <strong>pas</strong> de firmware radio installable.</p>
<div class="stack"><section class="panel"><h2>HAL et drivers</h2><p>GPIO, ADC, LCD, NAND en lecture, UART, audio et RF, bases sur les registres et verifications materiels.</p><a href="{x(GITHUB+'/tree/main/firmware/hal')}">Voir les sources HAL sur GitHub</a></section>
<section class="panel"><h2>Application</h2><p>Demarrage, VFO, FM, CTCSS, memoires, GPS/APRS. DMR et APRS RX apres validation. Mode satellite additif.</p><a href="{x(GITHUB+'/tree/main/firmware/app')}">Voir les sources application</a></section>
<section class="panel"><h2>Tests et banc</h2><p>Simulation CPU et peripheriques, tests de non-regression, qualification avant tout essai sur poste.</p><a href="{x(GITHUB+'/tree/main/bench')}">Voir le banc</a></section></div>
<h2>Notices de developpement</h2><ul class="link-list">{links}</ul>'''
    write(dest,shell('Firmware alternatif',dest,body,'firmware.html'))


def photos_page(models):
    dest=SITE/'photos.html'
    refs=[('Photos FCC T4K-D578UV','https://fccid.io/T4K-D578UV/Internal-Photos/Internal-Photos-4513250'),('Dossier FCC T4K-D578UVIII','https://fccid.io/T4K-D578UVIII/'),('Photos et modifications D578','https://radio.carstenbauer.net/578techmods.htm')]
    lis=''.join(f'<li><a target="_blank" rel="noopener" href="{x(u)}">{x(t)}</a></li>' for t,u in refs)
    body=f'''<h1>Photos des PCB</h1><p>Les photos et positions de composants doivent correspondre a la revision de carte indiquee. Une photographie FCC d'une autre version reste une <strong>reference</strong>, pas une preuve de connexion.</p>
<section id="photo-gallery" class="docs-grid" aria-label="Photos locales annotees"></section>
<h2>Sources photographiques externes</h2><ul>{lis}</ul>
<p>Pour ajouter des images du poste demonte et leurs zones cliquables, consulter <a href="{x(doc_link(dest,'docs/hardware/PHOTOS.md'))}">la procedure de contribution</a>. L'archive ne republie pas les photos tierces sans droits verifies.</p>'''
    write(dest,shell('Photos des PCB',dest,body,'photos.html'))


def build_source_index():
    dest=SITE/'sources.html'
    groups=['bench','tools','firmware']
    exts={'.py','.c','.h','.js','.css','.json','.yml','.yaml','.sh','.cmd'}
    items=[]
    for group in groups:
        for f in sorted((ROOT/group).rglob('*')):
            if f.is_file() and f.suffix.lower() in exts and f.name!='build_site.py':
                rel=f.relative_to(ROOT).as_posix()
                items.append(f'<li><a href="{x(source_link(rel))}">{x(rel)}</a></li>')
    body='<h1>Index des sources</h1><p>Le code source reside uniquement dans GitHub. Cet index est regenere a chaque modification du depot.</p><ul class="source-index">'+''.join(items)+'</ul>'
    write(dest,shell('Sources',dest,body))


def build_assets(models,docs):
    assets=SITE/'assets'
    assets.mkdir(exist_ok=True)
    shutil.copy2(ROOT/'site-assets/site.css',assets/'site.css')
    shutil.copy2(ROOT/'site-assets/site.js',assets/'site.js')
    safe=lambda o:json.dumps(o,ensure_ascii=True,separators=(',',':')).replace('</','<\\/')
    photo_models={}
    for m in models:
        vid=m['id']
        folder=ROOT/'hardware/photos'/vid
        manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
        known={p['file'] for p in manifest.get('photos',[])}
        for item in sorted(folder.iterdir()):
            if item.suffix.lower() in ('.png','.jpg','.jpeg','.webp') and item.name not in known:
                manifest.setdefault('photos',[]).append(dict(file=item.name,title=item.stem.replace('_',' '),side='Non precisee',note='Photographie non annotee. Attribution et identification de la carte a ajouter.'))
        photo_models[vid]=manifest
    write(assets/'models.js','window.OpenD578Models = '+safe({m['id']:m for m in models})+';\n'+
        'window.OpenD578Photos = '+safe(photo_models)+';\n')
    write(assets/'search-data.js','window.OpenD578Docs = '+safe(docs)+';\n')
    for m in models:
        p=ROOT/'hardware/photos'/m['id']
        out=SITE/'photos'/m['id']
        out.mkdir(parents=True,exist_ok=True)
        for f in p.iterdir():
            if f.is_file() and f.name!='manifest.json':
                shutil.copy2(f,out/f.name)


def main():
    if not check():
        return 1
    import mistune
    if tuple(int(x) for x in mistune.__version__.split('.')[:2]) < (3,2):
        raise SystemExit('mistune 3.2+ required')
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    docs=build_docs(discover_docs())
    models=[json.loads(f.read_text(encoding='utf-8')) for f in sorted((ROOT/'hardware/models').glob('*.json'))]
    hardware_pages(models)
    index_page(models,docs)
    docs_page(docs)
    cps_page(docs)
    firmware_page(docs)
    photos_page(models)
    build_source_index()
    build_assets(models,docs)
    (SITE/'.nojekyll').touch()
    print(f'Built {len(docs)} Markdown pages, {sum(len(m["nodes"]) for m in models)} components, {sum(len(m["edges"]) for m in models)} connections at {SITE}')
    return 0

if __name__=='__main__':
    sys.exit(main())
