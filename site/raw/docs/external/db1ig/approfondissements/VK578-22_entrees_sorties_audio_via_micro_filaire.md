# VK578-22 : Entrées/sorties audio via micro filaire

**Revue approfondie 06/11/2026.** Source principale : [VK7ZJA, D578 mods v7.4, miroir DB1IG](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php). Complément éventuel : [RadioFoundry, matériel AnyTone](https://radiofoundry.org/docs/spec/hardware-anytone).

**Statut de la documentation :** analyse enrichie ; les fonctions validées en exécution sur le D578 OEM conservent ce statut. Les valeurs historiques d'un autre poste restent rattachées à cet appareil.

**Source initialement déjà conservée dans OpenD578 :** [docs/hardware/AUDIO.md](../../../hardware/AUDIO.md). Aucune ancienne donnée n'est supprimée.

**Connecteur microphone 8 contacts :** notre relevé donne URX, +5 V, UTX, SP+, MIC GND, MIC, SP− et GND sur les broches 1 à 8. Les contacts 4/7 correspondent au circuit haut-parleur et `SP−` ne doit pas être raccordé à la masse. L'audio électret et les lignes de communication ne sont pas interchangeables.

**Complément DB1IG :** un microphone de table peut utiliser une détection PTT résistive entre 1 et 8, avec `HandOpMode = Level Detection`. Le guide recommande 1 à 2,2 kΩ et indique une résistance série de 100 Ω et une résistance de polarisation électret ajustable de 22 kΩ à 1 kΩ dans son exemple historique. Les fils du microphone de série restent associés au protocole numérique, pas à ce mode de détection.

**Intégration SignaLink ou interface externe :** isoler les masses de signaux, fixer les niveaux RX/TX par mesures et protéger l'entrée micro. Un appareil externe ne doit pas mettre de tension sur URX/UTX ni court-circuiter SP+/SP−. Produire une fiche de câble par montage et réserver toute émission à un banc RF contrôlé.

## Provenance et suite vérifiable

- Ancienne lacune identifiée : Audio TX/RX externe type SignaLink : niveaux, masses audio et logique differents.
- Source historique : [guide original, édition octobre 2022](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php), rubrique « Entrées/sorties audio via micro filaire ».
- Application locale : comparer les paramètres en mode non destructif avec l'image OEM de la révision étudiée, conserver trames, adresses et horodatages.
- Niveau de preuve : les observations OEM du dépôt sont indépendantes du texte historique ; une fonctionnalité expérimentale est étiquetée comme telle.
