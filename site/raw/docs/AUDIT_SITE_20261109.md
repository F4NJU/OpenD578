# Revue générale du site — 9 novembre 2026

Base : dépôt Telectroboy/OpenD578, HEAD cdef47dcba37f1e886bc301e330e65d7f3a3e79f ; l’archive fournie correspond à ce commit, avec différences de fins de lignes normalisées. Le SHA exact de base est conservé dans le patch fourni.

## Changements

- Intégration additive du banc Web 0.15.1, de ses sources WebAssembly et licences, du guide et de 120 tests ; copie automatique vers simulator/ lors de la construction GitHub Pages.
- Tableau IO courant, HTML filtrable et export CSV/JSON, preuves N1–N14, comparaison PLUS et rapport APRS RX ; copie vers io/ et navigation sur les pages régénérées.
- Modèles PRO/PLUS corrigés : GPS, U2429, BH2226, UART3 et BHT_BOARD ; fiches et liaisons régénérées.
- Générateur de brochage alimenté par la table résolue : un rebuild ne réintroduit plus PB6/PB7 inversés ou les anciens états inconnus.
- Encodeurs C corrigés : nibble de sélection BH2226, D0/D1 U2429. Tests de référence et étape CI ajoutés.
- Les documents historiques restent datés ; chaque page documentaire renvoie vers le bilan confirmé. Les sources externes n’ont pas été réécrites en preuves OEM.

## Validation

- 120 tests du banc Web réussis, dont les couleurs LCD et la journalisation MMIO.
- 36 tests Python des outils réussis ; couverture documentaire 129 affirmations RadioFoundry et 21 approfondissements sur 60 thèmes historiques.
- Deux modèles : 74 composants, 86 connexions, documents et photos référencés vérifiés.
- Site reconstruit et liens locaux de toutes les pages HTML vérifiés ; inventaire détaillé généré dans audit_pages_20261109.csv.
- Encodeurs C et routines RF QA4818N compilés avec avertissements traités en erreurs et exécutés ; mini CPS Node réussi.

Ce contrôle porte sur la cohérence technique du site et les régressions logicielles. Il n’inclut pas une nouvelle campagne RF sur poste, un démarrage OEM long complet dans le navigateur, ni une vérification visuelle manuelle de chaque écran. Les limites audio PCM, ROS, modèle KT et amont RF/audio BHT sont conservées dans ETAT_CONFIRME_20261109.md.

## Publication

La lecture du dépôt distant a réussi. GitHub n’a pas pu être modifié depuis la session : le connecteur GitHub renvoie Unknown tool et git push ne trouve pas d’authentification HTTPS. Aucun déploiement distant n’est revendiqué. Le paquet inclut le dépôt complet et un patch à appliquer à la base contrôlée, sans effacer le travail local du mainteneur.

## Complément audio

334 pages après ajout du dossier audio ; source WAV externe sur PC0/ADC10 et export des acquisitions. Commandes C audio intégrées, comparaison OEM de 62 402 cas sans différence. Le flux voix FM complet reste ouvert ; voir le nouveau dossier 08_AUDIO_FM_TRANSPORT_ET_VALIDATION.md.
