# Correctif CI OpenD578 - 6 novembre 2026

## Cause
Le workflow `tests.yml` lance les tests du banc sans compiler la bibliotheque native `bench/native_gate_host.so`. La classe `NativeGate` leve alors `RuntimeError: Native counter missing`.

## Changement
- `tests.yml`: compile `python bench/build_native.py` apres installation de `bench/requirements.txt` et avant les tests.
- `tests.yml` et `pages.yml`: utilisent `actions/checkout@v5`, `actions/setup-python@v6` et une image `ubuntu-24.04` fixe.

Les fichiers `.so` ne sont pas ajoutes au depot : ils doivent etre compiles sur chaque runner.

## Installation
Copier le contenu du dossier `OpenD578/` de ce correctif dans la racine du depot, puis faire Commit et Push avec GitHub Desktop.

Cette verification est structurelle et locale. La suite de tests complete n'a pas ete executee ici, car Unicorn n'est pas installe dans le conteneur. Consulter GitHub Actions apres le push pour le resultat reel.
