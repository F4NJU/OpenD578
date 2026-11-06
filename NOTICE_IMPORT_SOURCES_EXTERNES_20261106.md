# OpenD578 : ajout des sources externes sans suppression

Mise a jour additive du 6 novembre 2026. A appliquer **par dessus** le depot OpenD578 deja present sur GitHub : ne pas supprimer de repertoires, ne pas remplacer l'ensemble de l'historique Git. Apres copie, faire Commit to main puis Push origin dans GitHub Desktop.

## Ou lire les nouveaux documents

Dans GitHub Pages, cliquer sur **Sources externes**. Le dossier `docs/external/` centralise l'index F1DMG / VK7ZJA, l'inventaire des sujets (60 rubriques), les donnees de RF/NAND/RTC/GPS recoupees, les documents et photos a conserver, les restrictions de publication et le journal des pieces manquantes.

## Sauvegarde privee sur Windows

Dans PowerShell, depuis la racine du depot clone :

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\archive_sources_windows.ps1
```

Python 3 est necessaire, sous le lanceur Windows `py -3`. L'outil copie les pages des sources accessibles, leurs photographies, PDF et feuilles de style dans `OpenD578_archives_privees`, **en dehors du dossier Git**. Il conserve les octets d'origine, enregistre les URLs et SHA-256, cree une version navigable hors ligne et n'efface jamais les captures precedentes. Il essaie les snapshots Wayback pour les trois anciennes adresses F1DMG en cas d'echec d'acces. Pour les logiciels binaires telecharges, voir la commande optionnelle `--include-tools` ; **ne pas les executer**.

## Ce qui n'est pas fourni comme copie physique

Les pages F1DMG n'etaient pas joignables depuis l'environnement de creation de ce paquet, et la telecopie directe de photos des autres sites etait egalement indisponible. Le ZIP contient l'outil de sauvegarde et les connaissances reformulees, **pas les photos ou textes complets des sites tiers**. Ne pas confondre l'existence du manifeste avec une preuve de telechargement : seuls les resultats marques `200` et dotes de SHA-256 dans `manifest.json` attestent un fichier recupere.

## Verifications

`python tools/build_site.py`, `python tools/test_site.py`, `python tools/check_publication.py` et `python -m unittest discover -s tools/archive_tests -v`. Les nouveaux tests n'ont pas besoin de Unicorn ni de l'image firmware OEM.
