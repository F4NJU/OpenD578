# Changelog et verification de la consolidation des sources (06/11/2026)

## Ajoute au depot OpenD578, sans retrait de documents anterieurs

- Inventaire et datation des versions F1DMG / VK7ZJA / autres sources.
- Index documentaire de **60 sujets** historiquement abordes par VK7ZJA, avec descriptions originales et liens au document source.
- Monographie de recoupement : MCU, RF, QA4818N, premiere FI, NAND et sauvegardes RTC/GPS.
- Fiche protocole CPS / firmware / calibration / flash et differences de revisions.
- Inventaire des photographies internes et fichiers attendus.
- Notice de recuperation F1DMG et copie de son ancien chemin `/578a` signale par VK7ZJA.
- Programme de sauvegarde privee multi-sites, incluant pages, images, documents, manifeste horodate, octets originaux, liens locaux et hashes SHA-256.
- Script PowerShell Windows et tests locaux de la sauvegarde.
- Entree `Sources externes` dans la navigation GitHub Pages.

## Non pretendre realiser

- Aucune copie effective de F1DMG : son serveur ne repond pas depuis l'environnement de consultation.
- Les originaux des photographies ne sont pas telecharges par ce paquet. Ils le seront sur le PC utilisant le script si les sites repondent.
- La mention d'une autorisation de miroir chez DB1IG concerne ce site et ne constitue pas une licence de republication generale.
- Les nouveaux documents ne dedoublonnent ni n'ecrasent les analyses et captures OEM de l'utilisateur.
- La cartographie RF issue du travail ancien ne remplace pas les routines et GPIO obtenus par notre firmware PRO V1.21.

## Controle conseille apres mise a jour GitHub

Ouvrir `docs/external/INDEX.md` via le site GitHub Pages et confirmer la navigation. Sur le PC, lancer le PowerShell d'archivage, ouvrir les `index.html` generes et conserver le `summary.json` avec les archives. Examiner les `ERROR` pour les pages et images non recuperees. Renouveler l'archivage a chaque changement de source pour conserver plusieurs revisions sans effacer les precedentes.
