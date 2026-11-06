# OpenD578 : paquet GitHub F1DMG (6 novembre 2026)

## Livrable

Version publiable par génération du site, **à condition d’importer d’abord les photographies depuis le ZIP original de l’utilisateur**. Ce paquet ne contient pas les originaux de Guy ni les captures constructeur, codeplugs ou images d'autres auteurs. Il ne contient aucun fichier de test photographique fictif.

- Rubrique `f1dmg.html` et nouvel onglet.
- Galerie photographique filtrable `f1dmg/galerie.html` avec catégorie, source, pages de référence, SHA-256 et nom de fichier d'origine.
- Pages de consultation historiques `f1dmg/page-20.html`, `f1dmg/page-22.html` avec conversion HTML restrictive.
- Documents et réglages AnyTone pertinents, sans généraliser les observations à toutes les révisions du matériel.
- Vignettes F1DMG sur l'accueil et la page des photographies matérielles existantes.
- Catalogue `publication.json`, inventaire des images absentes et importateur hors ligne.
- Intégration additive au générateur `tools/build_site.py`, au workflow GitHub Actions et à `README_SITE.md`.

## Tests réalisés ici

`python -m unittest discover -s tools -p test_f1dmg_publish.py -v` : **11 tests réussis** sur une archive synthétique créée par les tests, couvrant les références HTML, le filtrage des sources externes, les hashes, les documents, l'import incrémental, l'intégration au site et l'idempotence.

`python -m compileall -q tools` : validé. Maquette sans photographies générée et inspectée via Chromium.

**Non validés dans cette session :** l'import d'un ZIP réel de 118 Mo / 102 Mo de l'utilisateur (octets non accessibles ici), la présence effective de toutes les images de l'archive, l'exécution complète du workflow GitHub Actions en environnement distant, et la publication sur le dépôt GitHub distant.

## Pré-publication

L'utilisateur confirme avoir obtenu l'accord téléphonique de Guy F1DMG pour réutiliser ses propres textes et photographies. Revoir néanmoins chaque fichier issu de contenus éventuellement tiers et confirmer les crédits. L'accord n'implique pas un transfert automatique de licence GPL. Le site DB1IG et les travaux de Jason VK7ZJA ne sont pas importés sous cet accord.

Voir `INSTALLATION_GITHUB_F1DMG.md` pour toutes les commandes.
