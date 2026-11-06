# Installer le dépôt complet OpenD578 sur GitHub

Ce paquet est destiné à un dépôt GitHub **vide** nommé `OpenD578` appartenant à `Telectroboy`. Il contient le dossier `OpenD578/` avec sources publiques du banc V11.7, documentation du matériel et Bluetooth, fiches CPS et site GitHub Pages compilé. Les images constructeur et captures privées ne sont **pas** incluses.

## Méthode simple : navigateur GitHub

1. Créer `OpenD578` (ou ouvrir le dépôt déjà créé) et initialiser `main`.
2. Décompresser l'archive et **copier le contenu du dossier `OpenD578/` à la racine du dépôt** (ne pas créer `OpenD578/OpenD578/`).
3. Importer les fichiers via `Add file` / `Upload files` si leur nombre et la taille le permettent. Pour un projet de cette taille, le client Git est généralement plus fiable que l'upload navigateur.
4. Commiter sur `main` ; GitHub Actions doit exécuter `pages.yml`.
5. Dans `Settings` > `Pages` > `Build and deployment`, choisir **GitHub Actions**.
6. Suivre l'exécution `Deploy OpenD578 documentation` dans l'onglet `Actions` et consulter ensuite `https://telectroboy.github.io/OpenD578/`.

## Méthode Git (recommandée)

```sh
unzip OpenD578_COMPLET_CPS_ET_HARDWARE_20261105.zip
cd OpenD578
# Sur un dépôt neuf, sans autre contenu :
git init -b main
git add .
git commit -m "Initial public OpenD578 hardware, CPS and firmware research"
git remote add origin https://github.com/Telectroboy/OpenD578.git
git push -u origin main
```

Si `OpenD578` contient déjà des commits, **cloner le dépôt existant**, puis copier le contenu de l'archive **dans ce clone** avant `git add/commit/push`. Ne pas forcer un `push --force` pour écraser un historique préexistant.

## Maintenance : une seule source Markdown

- **Modifier un document** sous `docs/` ou `firmware/` : le site est régénéré automatiquement à chaque `push` sur `main`. Les fichiers `.md` du dépôt font foi ; pas de doublon HTML à éditer.
- **Ajouter une fiche composant** : `docs/hardware/<nom>.md`.
- **Ajouter une connexion ou un composant cliquable** : modifier `hardware/models/<variante>.json` en indiquant preuve et documents liés.
- **Ajouter des photos** : sous `hardware/photos/<variante>/`, avec annotation des zones si le brochage et la révision sont confirmés. Ne pas redistribuer les photos FCC sans droits.
- **Ajouter un pilote** : code sous `firmware/`, tests sous `firmware/tests/`, sans prétendre à un firmware flashable tant que la validation matérielle n'est pas effectuée.
- **Mettre à jour le dossier CPS** : modifier `docs/cps/`, et compléter les outils du banc et leurs tests si des trames sont mesurées.

## Tester localement

```sh
python3 -m pip install -r site-requirements.txt
python3 tools/validate_hardware_model.py
python3 tools/build_site.py
python3 tools/test_site.py
node bench/web/test_mini_cps.cjs
python3 -m unittest discover -s tools -p test_cps_trace_audit.py -v
python3 -m unittest discover -s tools -p test_bluetooth_tools.py -v
python3 -m http.server --directory site 8000
```

Site local : `http://localhost:8000/`. Le site est statique ; il ne transfère **aucun** paquet de firmware ni ne pilote physiquement la radio. Le banc PC est une application distincte.

## Ce qui n'est pas livré dans une publication publique

- Image OEM GD32 V1.21 / PLUS V2.08 `.CDD`, `.CDI`, `.spi` et programmes CPS Windows.
- Firmware du modem DMR et blobs tiers, dumps NAND complets, codeplug personnel, calibrations RF propres au numéro de série, logs port COM contenant des données privées.
- État d'exécution V11.8 non disponible sous forme de sources complètes : les documents V11.8 sont présents, **le banc disponible est la source publique V11.7**.

Voir [périmètre et niveaux de preuve](cps/README.md), [licence et provenance](../PROVENANCE.md), [état du firmware alternatif](firmware/ARCHITECTURE.md).
