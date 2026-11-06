# F1DMG : dossier illustré, version 3

**Cette version garde les photographies à côté des explications et ajoute le remerciement signé Jean-Philippe (F4EGM).**

La page publique `f1dmg.html` contient désormais :

- des fiches par modification (refroidissement, microphone, protection ROS, commandes, reset, CPS, scan/DMR/APRS), avec **photographies placées dans la même section que les explications** ;
- les deux pages originales F1DMG intégrées **en entier, dans leur ordre de lecture**, avec leurs images à l'endroit où elles apparaissaient dans l'HTML d'origine ;
- les photos désignées dans l'original par un lien texte affichées comme **vignettes dans le texte**, et non plus seulement comme liens ;
- les documents liés, les crédits, un vrai mot de remerciement à Guy F1DMG, et une galerie secondaire conservée comme index de recherche.

Les notes « Pour OpenD578 » sont les remarques de Jean-Philippe (F4EGM) sur ce qui sera utile au projet ou non. Elles ne sont pas attribuées à Guy. Les contenus de VK7ZJA et DB1IG ne sont pas republies par cette autorisation.

## Installer sur Debian dans le dépôt déjà cloné

Depuis `~/Projets/OpenD578` (ou le dossier dans lequel tu as cloné OpenD578) :

```bash
cd ~/Projets/OpenD578
unzip -o ~/Téléchargements/OpenD578_F1DMG_DOSSIER_ILLUSTRE_v3_Debian_GitHub.zip -d .
python3 tools/install_f1dmg_site.py
```

Si tu as déjà importé la sauvegarde et que `site-assets/f1dmg/publication.json` existe, **les photos et documents sont réutilisés sans réimportation**. Sinon :

```bash
python3 tools/publish_f1dmg.py --archive ~/Téléchargements/20261106T102717Z.zip --dry-run
python3 tools/publish_f1dmg.py --archive ~/Téléchargements/20261106T102717Z.zip
```

Puis reconstruire et tester. Si les dépendances de génération ne sont pas déjà installées, utilise un environnement virtuel Debian :

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r site-requirements.txt
```

Tests et construction :

```bash
python3 -m unittest discover -s tools -p test_f1dmg_publish.py -v
python3 tools/build_site.py
python3 tools/test_site.py
python3 -m http.server --directory site 8000
```

Ouvrir `http://localhost:8000/f1dmg.html`. Confirmer visuellement que chaque photo est au bon emplacement, puis arrêter le serveur avec `Ctrl+C`.

Pour publier :

```bash
git status --short
git diff --stat
git add tools/f1dmg_site.py tools/publish_f1dmg.py tools/install_f1dmg_site.py tools/test_f1dmg_publish.py site-assets/f1dmg docs/external/f1dmg tools/build_site.py README_SITE.md .github/workflows/pages.yml
git diff --cached --stat
git commit -m "Integrate F1DMG photos into illustrated technical notes"
git push origin main
```

Examine les fichiers ajoutés avant le commit : les archives privées, firmware OEM, codeplugs et NAND ne doivent pas être envoyés dans le dépôt. **Ne pas mettre tout le contenu de l'archive privée dans `site-assets`.** Utiliser l'importeur.

Si `tools/test_site.py` vérifie une page qui n'existe pas encore, relancer d'abord `python3 tools/install_f1dmg_site.py` : l'installateur connecte les pages au générateur.

## Ce qui a changé dans les textes

- Un vrai remerciement signé **73, Jean-Philippe (F4EGM)** ouvre la rubrique.
- Les fiches parlent de ce qu’apporte le travail de Guy au projet, sans employer « preuve » à chaque observation.
- Les descriptions d’origine de Guy et l’ordre de ses photos restent conservés dans les deux pages historiques.
- Les mentions sur les droits des images restent présentes ; la republication autorisée ne signifie pas mise sous GPL.

## Ce qui est conservé

L'URL publique reste `https://telectroboy.github.io/OpenD578/f1dmg.html`. Les anciennes URLs `f1dmg/page-20.html`, `f1dmg/page-22.html` et `f1dmg/galerie.html` restent utilisables. La navigation du site et la documentation firmware ne sont pas supprimées.

## Contrôle de publication

Le moteur du site regénère `site/` à chaque build. Il copie uniquement les photos présentes dans `site-assets/f1dmg/photos/`. Une photographie manquante n'est pas substituée par une image artificielle.

La génération locale a été testée sur une **archive de test synthétique** (et non sur les octets originaux de Guy, indisponibles dans cette session). Les images source seront vérifiées sur le poste Debian au moment de l'import. Le site public reste entièrement statique et consultable sans serveur applicatif.
