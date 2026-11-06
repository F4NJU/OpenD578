# OpenD578 : import additionnel RadioFoundry + 21 approfondissements DB1IG

**Édition : 6 novembre 2026.** Base : archive `OpenD578_COMPLET_REVUE_DB1IG_20261106.zip`, sans accès direct au dépôt GitHub utilisateur. La mise à jour est prévue pour un dépôt déjà publié.

## Livrables

- 21 fiches indépendantes dans `docs/external/db1ig/approfondissements/`, une pour chacun des `RESUME_A_DEVELOPPER` de la matrice précédente. L'ancienne matrice CSV/Markdown reste intacte.
- Inventaire factuel RadioFoundry de 129 entrées dans `docs/external/radiofoundry/AUDIT_AFFIRMATIONS.csv` + JSON et Markdown, avec le modèle d'origine, le niveau de preuve et la fiche existante liée.
- Quatre synthèses originales pour SCT3258/CHAN_D, GPIO 868 vs 578, NAND/calibrations et bootloader/UPDATE/CPS.
- Deux modèles de cartes mis à jour **uniquement dans les liens vers les fiches**, sans changer les composants ni les connexions déjà validés.
- Tests `tools/check_research_coverage.py`, appelés aussi dans les workflows GitHub Actions.

## Invariants

1. Ne supprimer aucune observation physique, trace OEM, document antérieur ou code source.
2. Notre V1.21 a un bootloader de 24 Kio et l'application à `0x08006000`, malgré les variantes 868 dont le boot débute sur 16 Kio.
3. Les GPIO du D868 rapportés par RadioFoundry ne changent pas les GPIO déjà identifiés sur le D578 par l'exécution du firmware constructeur.
4. Les données publiées sur le SCT3258 sont une source exploitable, y compris `CHAN_D` 36 octets, la configuration via `I2C_OPERATION` et le bootstrap de 2 048 octets. Les détails propres à la V1.21 ne sont validés que si observés dans ses routines/traces.
5. Les calibrations et codeplugs du D868 n'ont pas les mêmes adresses garanties que ceux du D578.
6. L'article RadioFoundry indique lui-même qu'il n'a pas une carte AnyTone à disposition. L'audit ne doit pas changer une affirmation d'un autre modèle en mesure physique de notre poste.
7. Les documents tiers sont liés, jamais recopiés intégralement ni présentés comme appartenant à OpenD578.

## Installation Windows / GitHub Desktop

Décompresser le ZIP **correctif** et copier le contenu du dossier `OpenD578` sur le dépôt local. Accepter le remplacement des fichiers d'accueil/index, des deux modèles JSON et des deux workflows de tests. **Ne pas effacer les autres dossiers.** Commit, puis Push origin dans GitHub Desktop. GitHub Pages régénère le site lors du push et vérifie les liens locaux.

Pour tester localement :

```powershell
python tools/check_research_coverage.py
python tools/validate_hardware_model.py
python tools/build_site.py
python tools/test_site.py
```

Ne pas flasher de firmware, écrire de calibration, ni lancer de transmission dans le cadre de cette revue documentaire.
