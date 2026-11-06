# Correctif additif de documentation DB1IG (6 novembre 2026)

Ce paquet ajoute des fichiers Markdown, JSON et CSV sous `docs/external/db1ig/`, et complete `docs/external/INDEX.md`, `README_SITE.md`, `README_FR.md`. Il ne retire aucune fiche, trace, image ou code du depot existant et ne touche ni au firmware ni aux workflows de tests.

Pour l'utiliser avec GitHub Desktop : copier **le contenu** du dossier `OpenD578/` du correctif a la racine du depot clone, autoriser le remplacement des trois fichiers d'index/README qui ont seulement recu une rubrique supplementaire, verifier l'onglet Changes, puis Commit et Push.

Les fichiers source demeurent la source unique du site statique ; GitHub Actions reconstruira les pages automatiquement. Les traductions/mirroirs d'un document VK7ZJA ne sont pas des preuves independantes. Les informations issues des executions OEM du poste conservent leur niveau de confiance.

La base comparee a ete l'archive du 06/11/2026 `OpenD578_COMPLET_SOURCES_F1DMG_VK7ZJA_20261106.zip` (empreinte dans `docs/external/db1ig/SOURCES_ET_DECOUVERTES.json`). Les commits GitHub plus recents, non accessibles a l'analyse, devront etre fusionnes plutot qu'ecrases. Si README a change entre-temps, ne coller que la nouvelle rubrique.
