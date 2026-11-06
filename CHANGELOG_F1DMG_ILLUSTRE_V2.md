# OpenD578 : correctif F1DMG, présentation illustrée v2

**Motif :** la première intégration plaçait les résumés techniques sur la page principale et les photos dans un index distinct. Il fallait ouvrir des pages séparées pour lire les textes d'origine avec leurs illustrations.

## Modification livrée

- `f1dmg.html` devient le **dossier technique illustré principal** : chaque fiche comprend le contexte de la modification, ses photos et une rubrique distincte « Application OpenD578 ».
- Les pages historiques `page-20.htm` et `page-22.htm` sont **également intégrées à la page principale**, avec leurs images à leur place d'origine. Les anciennes pages de consultation individuelles restent accessibles.
- Les liens vers des fichiers image dans le texte original se transforment en vignettes lors de l'affichage. Une image insérée par `<img>` reste au même endroit dans le texte. Les éléments externes absents sont signalés, pas remplacés par une image inventée.
- Les photos non associées avec certitude à une étape de modification ne sont pas attribuées arbitrairement. Elles sont conservées dans leur contexte historique lorsqu'il existe et recensées dans l'index photographique.
- Navigation locale et liens d'origine, crédits de Guy, liens de téléchargement des documents, index photographique et SHA-256 conservés.
- La galerie devient une aide à la recherche et n'est plus la voie de lecture principale.
- L'installateur convertit la notice F1DMG v1 en notice v2 sans créer de doublons.

## Fichiers modifiés

`tools/f1dmg_site.py`, `tools/publish_f1dmg.py`, `tools/install_f1dmg_site.py`, `tools/test_f1dmg_publish.py`, `site-assets/f1dmg/f1dmg.css`, `site-assets/f1dmg/f1dmg.js`, `docs/external/f1dmg/INDEX.md`.

Les changements existants de `tools/build_site.py` et de `.github/workflows/pages.yml` sont préservés. Sur une installation neuve, le script `tools/install_f1dmg_site.py` les adapte automatiquement comme dans la version précédente.

## Contrôle

- 12 tests unitaires d'import, de restitution et d'installation validés sur des données **synthétiques**.
- Vérification visuelle de l'interface en navigateur Chromium sur grand écran et mobile.
- Aucune image F1DMG véritable n'est incluse dans le ZIP de correction. Les photos déjà importées dans `site-assets/f1dmg/photos/` sont réutilisées automatiquement, sans perte. Sinon, relancer l'import à partir du ZIP original sur le poste Debian.
- Les scripts et photographies de VK7ZJA et DB1IG ne sont pas republies avec cette autorisation.

## URL inchangée

`https://telectroboy.github.io/OpenD578/f1dmg.html`
