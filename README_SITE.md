# Site technique OpenD578 / GitHub Pages

Site statique sans serveur, framework JS, CDN ni animation. Les fichiers `.md` sont
la source unique: le script publie **les Markdown du depot en lecture integree**
a chaque `push` sur `main`. Ajouter ou modifier un fichier sous `docs/` ou
`firmware/` ou `hardware/` met automatiquement a jour l'index et la page correspondante.

## Mise en ligne

1. Pour un depot GitHub **encore vide**, copier le **contenu du dossier `OpenD578/`**
   a la racine de `Telectroboy/OpenD578`. Ne pas copier uniquement le ZIP.
   Pour un depot deja rempli, comparer les fichiers et fusionner les modifications
   sans supprimer les sources existantes.
2. Commit/push sur la branche `main`.
3. Dans GitHub: `Settings` > `Pages` > `Build and deployment` > `Source` =
   **GitHub Actions**.
4. Verifier l'action `Deploy OpenD578 documentation` dans `Actions`.
5. Ouvrir `https://telectroboy.github.io/OpenD578/`.

La compilation du site ne requiert que Python et `mistune` 3.2.x dans l'action.
Le contenu est compile **a partir du fichier courant**, sans mettre a jour
une seconde page HTML a la main. Les fichiers Markdown sources sont egalement
proposes en telechargement.

## Mise a jour

- Modifier n'importe quel `.md` sous `docs/` ou `firmware/`, ou les README.
- Ajouter une liaison ou un composant dans
  `hardware/models/d578uv-pro-gd32-v121.json` avec son niveau de preuve.
- Ajouter une vraie photo dans `hardware/photos/<variante>/` : elle apparait
  automatiquement. Ajouter ses zones cliquables dans `manifest.json` si besoin.
- Ajouter une variante par un nouveau JSON du dossier `hardware/models/`.
- Les nouvelles pages sont listees automatiquement sans modifier un menu.

## Centre de preuves et sauvegardes RTC/GPS

La navigation `Preuves` donne acces aux cinq monographies reconstituees, a la carte CSV des 100 broches GD32, a la feuille KiCad **non cablee**, aux deux sauvegardes RTC/GNSS historiques et aux tests passifs proposes. Le contenu distingue releves utilisateur, OEM statique, banc d emulation et donnees tierces. Les originaux non accessibles ne sont pas inventes. Voir [preuves](docs/evidence/INDEX.md).

## Bluetooth / ajouts materiels recents

La carte **D868BT-SP**, son module Bluetooth blinde (firmware ET12), le microphone
**BT01** et le bouton PTT **BP-02** possedent maintenant des fiches distinctes
reliees aux deux vues PRO/PLUS. Le PLUS utilise egalement un **GD32F303** selon
le releve materiel ; les GPIO et firmware exacts restent propres a la variante.
Le circuit marque **H2226** en boitier **SSOP-B16** est identifie comme
**ROHM BH2226FV-E2** (8 sorties DAC), sans supposer ses affectations physiques.

Les outils `tools/audit_bluetooth_strings.py` et `tools/decode_bt_uart.py`
fonctionnent hors ligne et en **lecture seule** : le premier repere des chaines
dans un binaire fourni, le second annote des trames UART deja capturees.
Ils ne pilotent jamais le poste ni le PTT.

## Generation locale (facultative)

```bash
python3 -m pip install -r site-requirements.txt
python3 tools/validate_hardware_model.py
python3 tools/build_site.py
python3 -m http.server --directory site 8000
```

Le site peut aussi etre ouvert depuis un fichier `site/index.html`; les
scripts et donnees sont embarques/locales et ne consultent pas de service.
Le code met automatiquement des liens vers la documentation GitHub et les
copies Markdown generees pour consultation hors ligne.

## Regles de publication

Aucune image OEM, aucun dump NAND, aucune calibration/codeplug personnel ou
source sous licence incertaine. On ne presente pas un signal de simulation
comme une liaison physique prouvee. Dans les photos tierces, on prefere les
liens de source a une republication sans autorisation.

## Programmation CPS

Un nouvel onglet `CPS / USB` regroupe les trames OEM `PROGRAM`, identification, `R`, `W`, `END`, les descripteurs USB CDC et le format des 128 premiers canaux du PRO V1.21. Les fichiers `bench/cps_bridge.py`, `bench/cps_probe.py`, `bench/web/mini_cps_protocol.js` et leurs tests proviennent de la **source publique V11.7**. Le scanner `tools/cps_trace_audit.py` analyse des journaux JSONL déjà capturés, sans connexion USB.

Le dépôt ne comprend pas le constructeur CPS.exe ni les images constructeur. La compatibilité avec les postes physiques et la totalité des fonctions Windows reste à qualifier.

## Sources externes et archivage prive (novembre 2026)

La navigation **Sources externes** reference les travaux F1DMG et VK7ZJA, les differentes revisions de sa documentation, les photos FCC et leurs recoupements avec les preuves du firmware OpenD578. Lire `docs/external/INDEX.md`. Les originaux et images peuvent etre sauvegardes **localement**, hors du depot GitHub, avec `tools/archive_sources_windows.ps1`. Aucun contenu tiers integral n'est republice dans GitHub sans autorisation.

## Revue croisee DB1IG / VK7ZJA du 6 novembre 2026

La documentation contient une [revue comparative des principales pages AnyTone de DB1IG](docs/external/db1ig/INDEX.md), avec un inventaire de 60 sujets cote a cote avec les fichiers OpenD578 existants. L'ajout est documentaire, et n'a aucun effet sur les pilotes RF ou les actions de programmation. Les originaux et photos conservent leurs references, sans reproduction integrale publique.

## Consolidation RadioFoundry et des 21 sujets DB1IG

- [Audit vérifiable de 129 affirmations, avec liens et statuts](docs/external/radiofoundry/AUDIT_AFFIRMATIONS.md).
- [Approfondissement des 21 sujets DB1IG restés en résumé](docs/external/db1ig/approfondissements/INDEX.md).
- Documentation ajoutée sans suppression des analyses OEM, avec le GPIO D578 prioritaire sur le D868 et le bootloader V1.21 à `0x08006000`.
- `python tools/check_research_coverage.py` contrôle l’intégrité des renvois et de la matrice.
