# Correctif de consolidation de l'archive AnyTone du 6 novembre 2026

## Installation sur le depot existant

1. Conserver une copie du depot Git local et du ZIP prive `20261106T102717Z.zip`.
2. Decompresser le *correctif* et copier son dossier `OpenD578/` dans la racine du clone GitHub, en fusionnant les dossiers. Le correctif n'a pas de fichier a supprimer.
3. Verifier les changements avec GitHub Desktop, `Commit to main`, puis `Push origin`.
4. GitHub Actions regenerera le site depuis les nouveaux Markdown. L'archive complete est egalement disponible si l'on reconstruit un depot depuis zero.

## Contenu

- `docs/external/archives_20261106/`: analyses, tableau d'ecarts, renvois vers les originaux **stockes en prive**, manifests, 71 erreurs de collecte, 19 liens F1DMG manquants, registre des images.
- `tools/archive_sources_privees.py`: URL avec espaces encodes, profils de collecte cibles, option explicite pour ZIP/RDT/HPT/MPG et limitation de taille de fichier.
- `tools/test_archive_sources_privees.py`: cinq tests unitaires hors ligne.
- `docs/external/INDEX.md`, `docs/external/F1DMG_RECUPERATION.md`, `README_SITE.md`: navigation et mise a jour de l'etat des sources F1DMG.

**Ne pas placer les pages HTML originales, photographies, dumps, fichiers de contacts, logiciels ou firmwares de tiers dans ce depot public** sans avoir obtenu les droits de republication. Les auteurs restent credites par URL dans les fiches. Le correctif publie uniquement nos analyses, liens et empreintes.

## Verification

Depuis la racine du depot avec Python 3:

```
python -m unittest discover -s tools -p 'test_archive_sources_privees.py' -v
python tools/build_site.py
python tools/test_site.py
python tools/check_publication.py
```

La suite de tests du banc firmware et la compilation complete du simulateur ne sont pas affectees par ce correctif documentaire; elles n'ont pas ete rerun dans cet audit.
