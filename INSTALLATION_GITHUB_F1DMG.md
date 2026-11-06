# OpenD578 : mise à jour F1DMG pour GitHub Pages

**Date : 6 novembre 2026.** Installation additive : le banc Python V11.7, le modèle PRO/PLUS, le dossier DB1IG et les fichiers déjà présents sont conservés.

## Pourquoi cette archive ne contient pas encore les photographies

Les originaux F1DMG figurent dans ta sauvegarde `20261106T102717Z.zip` ou `OpenD578_archives_privees.zip`. Leur présence est documentée par les inventaires du dépôt. Les octets des fichiers antérieurement fournis n'étaient cependant pas accessibles dans cette session de travail. Ce paquet contient donc **l'outil d'import**, pas une galerie prétendument complète ou des images reconstituées.

Le script d'import n'accède à aucun site Internet ; il lit uniquement le ZIP sur ton PC, vérifie les empreintes disponibles et génère les photos et les pages de consultation. Tu pourras ainsi publier les clichés effectivement présents dans **tes** archives. Le nombre exact de fichiers est affiché après import.

## Installation sous Windows / PowerShell

1. Décompresser ce ZIP à la **racine** du dépôt local `OpenD578`, en conservant l'arborescence `tools/`, `docs/` et `site-assets/`. Ne pas effacer les fichiers déjà présents.
2. Ouvrir PowerShell dans le dépôt, lancer :

```powershell
py -3 tools/install_f1dmg_site.py
py -3 tools/publish_f1dmg.py --archive "C:\CHEMIN\VERS\20261106T102717Z.zip" --dry-run
py -3 tools/publish_f1dmg.py --archive "C:\CHEMIN\VERS\20261106T102717Z.zip"
```

3. Lire le catalogue `site-assets/f1dmg/publication.json`, contrôler que les images publiées appartiennent bien à Guy ou que les auteurs tiers sont identifiés. Les photographies et documents n'ont **pas** été relicenciés sous GPL-3.0.
4. Installer les dépendances de génération du site si nécessaire, puis compiler et vérifier :

```powershell
py -3 -m pip install -r site-requirements.txt
py -3 -m unittest discover -s tools -p "test_f1dmg_publish.py" -v
py -3 tools/build_site.py
py -3 tools/test_site.py
```

5. Vérifier en local `site/f1dmg.html`, `site/f1dmg/galerie.html`, `site/f1dmg/page-20.html` et `site/f1dmg/page-22.html`, puis faire `git add`, commit et push sur `main`.

```powershell
git add tools/publish_f1dmg.py tools/f1dmg_site.py tools/install_f1dmg_site.py tools/test_f1dmg_publish.py docs/external site-assets/f1dmg README_SITE.md tools/build_site.py .github/workflows/pages.yml
git commit -m "Add F1DMG authorized photos and AnyTone documentation"
git push origin main
```

Examine les fichiers avec `git status` avant le commit. Ne publie pas une image dont l'auteur serait distinct de Guy sans vérifier son autorisation.

### Linux / macOS

Les commandes sont identiques en remplaçant `py -3` par `python3` et le chemin `C:\...` par celui de l'archive locale.

## Ce qui sera ajouté au site

- `https://telectroboy.github.io/OpenD578/f1dmg.html` : présentation des contributions et crédits ;
- `https://telectroboy.github.io/OpenD578/f1dmg/galerie.html` : galerie filtrable, avec source et SHA-256 par image ;
- `https://telectroboy.github.io/OpenD578/f1dmg/page-20.html` et `page-22.html` : contenu historique nettoyé des scripts et des ressources tierces ;
- `docs/external/f1dmg/INDEX.md` : documentation technique détaillée et provenance, affichée dans le lecteur Markdown du site ;
- un nouvel onglet **F1DMG** dans la navigation existante, ainsi que des liens et jusqu’à six miniatures sur l’accueil et la page des photos de circuits.

## Précautions sur les fichiers publiés

L'import reconnaît uniquement les images et les PDF/DOC/TXT/ODT/RTF liés par les deux pages AnyTone, ainsi que les images des dossiers `page-20/` et `page-22/` et quelques photos AnyTone connues situées à la racine. **Les firmwares, codeplugs RDT, images NAND, CSV de contacts, fichiers HPT, archives et exécutables sont exclus.**

En option, `--include-all-f1dmg-images` importe aussi les illustrations sans lien direct avec le D578 (sondes météo, projets divers, etc.) ; contrôler leur pertinence et les droits associés avant publication.

Le lien historique `http://f1dmg.free.fr/578a` n'est plus proposé comme lien actif. Il est remplacé par la galerie locale et un libellé d'archive historique.

## Intégrité du site

`tools/build_site.py` efface puis régénère tout `site/`. L'installateur lui ajoute deux points d'intégration idempotents : l'onglet F1DMG et l'appel au constructeur de pages `f1dmg_site.py` **après** `build_assets`. Aucune suppression du code constructeur ou du simulateur n'est requise. Le dépôt Git reste l'unique référence ; les fichiers de `site/` sont reconstruits au prochain push GitHub Actions. Le workflow ajoute également les tests du nouvel importeur à la validation automatique.

Si l'import échoue, le programme n'efface pas tes originaux. Il vérifie les empreintes SHA-256 quand elles sont présentes dans le manifeste de l'archive. Une image manquante est listée sous `missing_images` et ne reçoit pas de photo factice.
