# OpenD578 : réorganisation matérielle et façade (6 novembre 2026)

## Changements

1. GD32F303VKT6 central dans les deux variantes du schéma.
2. Façade détaillée ajoutée avec LCD, huit touches analogiques, Power, appui codeur, deux volumes, LED et bus d'éclairage.
3. Airband déplacé de la façade à la carte RF de la variante PLUS.
4. Niveaux de preuve corrigés : une routine OEM observée est considérée comme une preuve logicielle ; une fonction opérationnelle ne devient pas « inconnue » pour défaut de continuité électrique.
5. HPI SCT3258 ajouté explicitement aux liaisons : PD2, PD3, PD4, PD5, PD8..PD15, avec leur rôle déclaré.
6. Fiches GPIO/NAND/RF/USB/microphone reliées aux composants et aux traces existantes.
7. PLUS : six blocs de façade ajoutés. Le MCU GD32F303 était déjà confirmé sur la carte de l'utilisateur. Le GPIO exact de la variante PLUS n'est pas copié automatiquement du firmware PRO.
8. Documentation des partages PB3/PB4 pour bus RF et rétroéclairage. Ne pas initialiser deux pilotes concurrents sans qualifier la commutation.

## Provenance et limites

- Sources principales : notices LCD V11.8, façade GPIO, microphone V11.8, HPI SCT3258, modèles GPIO RF et tests du banc.
- Fonctionnement OEM confirmé par l'utilisateur sur poste physique.
- Cette mise à jour ne crée pas de firmware flashable ; elle modifie la documentation et la présentation.
- Les noms des circuits grattés et les pistes non mesurées restent présentés comme des attributions physiques à confirmer.

## Tests

- `python tools/validate_hardware_model.py`
- `python tools/build_site.py`
- `python tools/test_site.py`
- `node --check site-assets/site.js`

Le site est généré à partir des Markdown et JSON source unique, sans édition manuelle des pages HTML.
