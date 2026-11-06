from __future__ import annotations
import base64
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).parent))
from publish_f1dmg import publish, SafePage, Archive, image_ok
from install_f1dmg_site import install
from f1dmg_site import build_f1dmg_site

PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+cB9kAAAAASUVORK5CYII=')

class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root/'repo'
        self.repo.mkdir()
        self.archive = self.root/'archive.zip'
        prefix = '20261106T102717Z/f1dmg/'
        self.page20 = b'''<html><head><script>BAD</script><style>badcss</style></head><body>
        <h1>Guy F1DMG AT-D578UV</h1><p>Refroidissement <b>ventilateur</b>.</p>
        <img src="578a.jpg" alt="D&eacute;flecteur ventilateur" onerror="alert(1)">
        <a href="page-20/01Mb.jpg">Photo micro</a>
        <a href="CMD-Roaming.doc">Guide roaming</a>
        <img src="https://db1ig.de/photos/other.jpg" alt="Externe">
        <a href="javascript:alert(1)">injection</a>
        </body></html>'''
        self.page22 = b'''<html><body><h1>PRO et PLUS</h1><p>BT01 et CPS</p>
        <img src="page-20/01Mb.jpg" alt="Microphone"><img src="not_found.jpg" alt="Absente">
        </body></html>'''
        objects = {
            'originals/f1dmg.free.fr/page-20.htm': self.page20,
            'originals/f1dmg.free.fr/page-22.htm': self.page22,
            'originals/f1dmg.free.fr/578a.jpg': b'\xff\xd8\xff' + b'jpeg-example-image'*3,
            'originals/f1dmg.free.fr/page-20/01Mb.jpg': b'\xff\xd8\xff' + b'jpeg-example-photo'*3,
            'originals/f1dmg.free.fr/other_unrelated.jpg': b'\xff\xd8\xff' + b'jpeg-example-other'*3,
            'originals/f1dmg.free.fr/CMD-Roaming.doc': b'DOC placeholder',
            'originals/f1dmg.free.fr/Mises_a_jour_pour_BT01.pdf': b'%PDF-1.4 synthetic fixture',
            'originals/f1dmg.free.fr/Contacts.csv': b'CALLSIGN,12345',
        }
        rows=[]
        for rel, data in objects.items():
            rows.append({'url':'http://f1dmg.free.fr/'+rel.removeprefix('originals/f1dmg.free.fr/'),
                         'original_file':rel,'sha256':hashlib.sha256(data).hexdigest(),'status':200})
        with ZipFile(self.archive,'w') as z:
            for rel, data in objects.items():
                z.writestr(prefix+rel,data)
            z.writestr(prefix+'manifest.json',json.dumps({'entries':rows}))

    def test_archive_prefix_at_root(self):
        alternate = self.root/'root_archive.zip'
        with ZipFile(self.archive) as src, ZipFile(alternate,'w') as dst:
            for item in src.infolist():
                name = item.filename.removeprefix('20261106T102717Z/')
                dst.writestr(name, src.read(item.filename))
        report=publish(alternate,self.repo,dry_run=True)
        self.assertEqual(len(report['pages']),2)
        self.assertEqual(len(report['photos']),2)

    def test_dry_run_is_read_only(self):
        report = publish(self.archive,self.repo, dry_run=True)
        self.assertEqual(len(report['pages']),2)
        self.assertEqual(len(report['photos']),2)
        self.assertEqual(len(report['documents']),2)
        self.assertFalse((self.repo/'site-assets').exists())

    def test_publish_filters_unrelated_and_externals(self):
        r=publish(self.archive,self.repo)
        self.assertEqual(len(r['photos']),2)
        self.assertEqual(len(r['documents']),2)
        self.assertTrue(all('db1ig.de' not in x['source'] for x in r['photos']))
        self.assertEqual(len(list((self.repo/'site-assets'/'f1dmg'/'photos').iterdir())),2)
        self.assertFalse(any(x.suffix=='.csv' for x in (self.repo/'site-assets'/'f1dmg').rglob('*')))

    def test_sanitized_html_and_images(self):
        publish(self.archive,self.repo)
        content=(self.repo/'site-assets'/'f1dmg'/'pages'/'page-20.fragment.html').read_text()
        self.assertNotIn('<script',content)
        self.assertNotIn('alert(',content)
        self.assertNotIn('onerror=',content)
        self.assertNotIn('<style',content)
        self.assertIn('f1dmg-embedded-photo',content)
        self.assertIn('photos/',content)
        self.assertNotIn('db1ig.de/photos',content)
        self.assertIn('f1dmg-image-link',content)
        self.assertIn('href="photos/',content)
        self.assertNotIn('href="http://f1dmg.free.fr/page-20/01Mb.jpg',content)

    def test_missing_images_inventory(self):
        report=publish(self.archive,self.repo)
        self.assertEqual(len(report['missing_images']),1)
        self.assertIn('not_found.jpg',report['missing_images'][0]['source'])

    def test_idempotent_import(self):
        a=publish(self.archive,self.repo)
        b=publish(self.archive,self.repo)
        self.assertEqual(a['photos'], b['photos'])

    def test_tampered_hash_fails(self):
        import zipfile
        other=self.root/'tampered.zip'
        with zipfile.ZipFile(self.archive) as z, zipfile.ZipFile(other,'w') as out:
            for name in z.namelist():
                data=z.read(name)
                if name.endswith('/578a.jpg'):
                    data+=b'altered'
                out.writestr(name,data)
        with self.assertRaisesRegex(ValueError,'SHA-256 incorrect'):
            publish(other,self.repo)

    def test_include_all_option(self):
        report=publish(self.archive,self.repo,True,True)
        self.assertEqual(len(report['photos']),3)

    def test_installer_idempotent(self):
        tools=self.repo/'tools'
        tools.mkdir()
        (tools/'f1dmg_site.py').write_text('pass')
        original="def nav():\n    links=[('photos.html','Photos'),('sources.html','Code source')]\n\ndef main():\n    build_assets(models,docs)\n"
        path=tools/'build_site.py'
        path.write_text(original)
        (self.repo/'README_SITE.md').write_text('# Site\n')
        workflow=self.repo/'.github'/'workflows'/'pages.yml'
        workflow.parent.mkdir(parents=True)
        workflow.write_text('name: Pages\njobs:\n  build:\n    steps:\n      - run: |\n          python tools/test_site.py\n')
        (self.repo/'docs'/'external').mkdir(parents=True)
        (self.repo/'docs'/'external'/'INDEX.md').write_text('# Sources\n')
        first=install(self.repo)
        second=install(self.repo)
        self.assertTrue(first['build_site_modified'])
        self.assertFalse(second['build_site_modified'])
        self.assertEqual(path.read_text().count('build_f1dmg_site(ROOT,SITE,shell,x)'),1)
        self.assertEqual(path.read_text().count("('f1dmg.html','F1DMG')"),1)
        self.assertEqual(workflow.read_text().count('test_f1dmg_publish.py'), 1)

    def test_existing_site_readme_migrates_gallery_note(self):
        from install_f1dmg_site import install
        tools = self.repo / 'tools'
        tools.mkdir()
        (tools / 'f1dmg_site.py').write_text('pass')
        (tools / 'build_site.py').write_text(
            "def nav():\n    links=[('photos.html','Photos'),('sources.html','Code source')]\n"
            "def main():\n    build_assets(models,docs)\n")
        (self.repo/'README_SITE.md').write_text('# Site\n## Contribution F1DMG : galerie autorisée (6 novembre 2026)\nAncien contenu\n## Section suivante\nNe pas effacer.\n')
        install(self.repo)
        install(self.repo)
        result=(self.repo/'README_SITE.md').read_text()
        self.assertIn('## Contribution F1DMG : dossier illustre', result)
        self.assertNotIn('Ancien contenu',result)
        self.assertIn('## Section suivante\nNe pas effacer.',result)
        self.assertEqual(result.count('## Contribution F1DMG'),1)

    def test_existing_site_readme_updates_v2_note(self):
        from install_f1dmg_site import install
        tools = self.repo / 'tools'
        tools.mkdir()
        (tools / 'f1dmg_site.py').write_text('pass')
        (tools / 'build_site.py').write_text(
            "def nav():\n    links=[('photos.html','Photos'),('sources.html','Code source')]\n"
            "def main():\n    build_assets(models,docs)\n")
        old = ('# Site\n## Contribution F1DMG : dossier illustre (6 novembre 2026)\n'
               'Texte de la v2 sans signature.\n## Section suivante\nNe pas effacer.\n')
        (self.repo / 'README_SITE.md').write_text(old)
        install(self.repo)
        install(self.repo)
        updated = (self.repo / 'README_SITE.md').read_text()
        self.assertIn('Jean-Philippe (F4EGM)', updated)
        self.assertNotIn('Texte de la v2', updated)
        self.assertIn('## Section suivante\nNe pas effacer.', updated)
        self.assertEqual(updated.count('## Contribution F1DMG'), 1)

    def test_site_generator_builds_gallery(self):
        publish(self.archive,self.repo)
        (self.repo/'site-assets'/'f1dmg'/'f1dmg.css').write_text('body {}')
        (self.repo/'site-assets'/'f1dmg'/'f1dmg.js').write_text('(function(){})();')
        site=self.repo/'site'
        site.mkdir()
        for filename in ('index.html', 'photos.html'):
            (site / filename).write_text('<html><head></head><body><main>OpenD578</main></body></html>')
        def shell(title,path,body,active=''):
            return '<html><head></head><body>'+body+'</body></html>'
        result=build_f1dmg_site(self.repo,site,shell)
        self.assertEqual(result['photos'],2)
        self.assertTrue((site/'f1dmg.html').is_file())
        self.assertTrue((site/'f1dmg'/'galerie.html').is_file())
        gallery=(site/'f1dmg'/'galerie.html').read_text()
        self.assertIn('f1dmg-photo',gallery)
        self.assertEqual(gallery.count('class="f1dmg-photo"'),2)
        self.assertIn('Refroidissement',gallery)
        self.assertIn('photos/',(site/'f1dmg'/'page-20.html').read_text())
        # Landing page includes the complete historic article and its images
        # in reading order, not in a separate photographic gallery.
        landing=(site/'f1dmg.html').read_text(encoding='utf-8')
        self.assertIn('Les travaux de Guy F1DMG',landing)
        self.assertIn('Merci Guy !',landing)
        self.assertIn('Jean-Philippe (F4EGM)',landing)
        self.assertIn('esprit radioamateur',landing)
        self.assertIn('Pour OpenD578 :',landing)
        self.assertNotIn('Le mainteneur',landing)
        self.assertNotIn('une preuve',landing)
        self.assertIn('Refroidissement du D578',landing)
        self.assertIn('f1dmg/photos/',landing)
        self.assertLess(landing.index('Refroidissement du D578'),landing.index('id="f1dmg-page-20"'))
        source_section=landing[landing.index('<article class="f1dmg-original"'):]
        self.assertLess(source_section.index('Refroidissement'),source_section.index('f1dmg-embedded-photo'))
        self.assertIn('class="f1dmg-image-link" href="f1dmg/photos/',source_section)
        self.assertIn('id="f1dmg-page-22"',landing)
        self.assertIn('f1dmg-page-20',landing)
        self.assertIn('f1dmg/documents/',landing)
        self.assertIn('f1dmg/photos/',landing)
        assert 'http://f1dmg.free.fr/page-20/01Mb.jpg' not in source_section
        story=landing[landing.index('id="refroidissement"'):landing.index('id="microphone"')]
        self.assertIn('578a.jpg',story)
        self.assertIn('f1dmg-story-photo',story)

        for filename in ('index.html','photos.html'):
            home=(site/filename).read_text()
            self.assertIn('id="f1dmg-feature-title"', home)
            self.assertIn('f1dmg.html', home)
            self.assertIn('Lire le dossier technique avec ses photographies', home)

    def test_no_archive_fallback(self):
        site=self.repo/'site'
        def shell(title,path,body,active=''):
            return '<html><head></head><body>'+body+'</body></html>'
        result=build_f1dmg_site(self.repo,site,shell)
        self.assertEqual(result['photos'],0)
        self.assertIn('Archive locale non importée',(site/'f1dmg.html').read_text())

if __name__=='__main__':unittest.main()
