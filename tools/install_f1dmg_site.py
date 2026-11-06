#!/usr/bin/env python3
"""Non-destructive, idempotent integration of F1DMG pages into OpenD578 Pages."""
from __future__ import annotations
import argparse
import ast
from pathlib import Path

MARK_NAV = "('photos.html','Photos'),('sources.html','Code source')"
NEW_NAV = "('photos.html','Photos'),('f1dmg.html','F1DMG'),('sources.html','Code source')"
MARK_BUILD = '    build_assets(models,docs)\n'
NEW_BUILD = MARK_BUILD + '    from f1dmg_site import build_f1dmg_site\n    build_f1dmg_site(ROOT,SITE,shell,x)\n'
SITE_NOTE = '''
## Contribution F1DMG : dossier illustre (6 novembre 2026)

La rubrique F1DMG regroupe sur une meme page les photos, leurs explications
techniques et les deux articles historiques, avec images a leur place :
`https://telectroboy.github.io/OpenD578/f1dmg.html`.
La galerie photographique devient un index secondaire. Les pages historiques
et leur texte complet restent consultables. L'import des archives F1DMG se fait
avec `tools/publish_f1dmg.py` sur la sauvegarde privee, sans envoyer les autres
fichiers du ZIP vers GitHub. Guy conserve les droits sur ses contributions.
Cette rubrique est presentee par Jean-Philippe (F4EGM), projet OpenD578.
VK7ZJA et DB1IG sont des sources separees non couvertes par cette autorisation.
'''
EXTERNAL_NOTE = '\n- [Dossier illustre F1DMG : explications, photos et archives originales](f1dmg/INDEX.md).\n'
WORKFLOW_MARK = '          python tools/test_site.py\n'
WORKFLOW_TEST = '          python -m unittest discover -s tools -p test_f1dmg_publish.py -v\n'


def install(root: Path) -> dict:
    build = root/'tools'/'build_site.py'
    if not build.is_file():
        raise FileNotFoundError('Fichier tools/build_site.py absent : lancer à la racine du dépôt OpenD578')
    current = build.read_text(encoding='utf-8')
    updated = current
    if NEW_NAV not in updated:
        if updated.count(MARK_NAV) != 1:
            raise ValueError('Navigation build_site.py différente : insertion manuelle requise')
        updated = updated.replace(MARK_NAV, NEW_NAV, 1)
    if 'build_f1dmg_site(ROOT,SITE,shell,x)' not in updated:
        if updated.count(MARK_BUILD) != 1:
            raise ValueError('Point de construction build_site.py différent : insertion manuelle requise')
        updated = updated.replace(MARK_BUILD, NEW_BUILD, 1)
    ast.parse(updated, filename=str(build))
    if not (root/'tools'/'f1dmg_site.py').is_file():
        raise FileNotFoundError('Copier au préalable tous les fichiers de l’archive d’intégration')
    changed = (updated != current)
    if changed:
        build.write_text(updated, encoding='utf-8')
    readme = root/'README_SITE.md'
    if readme.is_file():
        content = readme.read_text(encoding='utf-8')
        old_title = '## Contribution F1DMG : galerie autorisée'
        new_title = '## Contribution F1DMG : dossier illustre'
        if old_title in content or new_title in content:
            # Replace both the original gallery note and the previous illustrated
            # version. Do not create a second heading on repeated installation.
            import re
            current_title = old_title if old_title in content else new_title
            first = content.index(current_title)
            later = re.search(r'(?m)^## [^\n]+', content[first + len(current_title):])
            last = first + len(current_title) + later.start() if later else len(content)
            revised = content[:first].rstrip() + '\n' + SITE_NOTE.rstrip() + '\n' + content[last:].lstrip('\n')
            if revised != content:
                readme.write_text(revised, encoding='utf-8')
        else:
            readme.write_text(content.rstrip()+'\n'+SITE_NOTE, encoding='utf-8')
    index = root/'docs'/'external'/'INDEX.md'
    if index.is_file():
        content = index.read_text(encoding='utf-8')
        if '(f1dmg/INDEX.md)' not in content:
            index.write_text(content.rstrip()+'\n'+EXTERNAL_NOTE, encoding='utf-8')
        else:
            updated = content.replace('Travaux F1DMG publiés avec autorisation orale : galerie, sources et crédits',
                                      'Dossier illustré F1DMG : explications, photos et archives originales')
            if updated != content:
                index.write_text(updated, encoding='utf-8')
    workflow = root / '.github' / 'workflows' / 'pages.yml'
    workflow_changed = False
    if workflow.is_file():
        wf = workflow.read_text(encoding='utf-8')
        if 'test_f1dmg_publish.py' not in wf:
            if wf.count(WORKFLOW_MARK) != 1:
                raise ValueError('Workflow GitHub Pages différent : ajout du test automatique manuel requis')
            workflow.write_text(wf.replace(WORKFLOW_MARK, WORKFLOW_MARK + WORKFLOW_TEST, 1), encoding='utf-8')
            workflow_changed = True
    return {'build_site_modified': changed, 'workflow_modified': workflow_changed, 'navigation_present': NEW_NAV in updated,
            'site_hook_present': 'build_f1dmg_site(ROOT,SITE,shell,x)' in updated}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()
    r = install(args.repo)
    print('Intégration F1DMG : '+str(r))
    print('Si les photos ne sont pas déjà importées : python3 tools/publish_f1dmg.py --archive CHEMIN_DU_ZIP')

if __name__=='__main__':
    main()
