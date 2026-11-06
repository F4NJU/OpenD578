# VK578-33 : Réception de la bande aéronautique

**Revue approfondie 06/11/2026.** Source principale : [VK7ZJA, D578 mods v7.4, miroir DB1IG](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php). Complément éventuel : [RadioFoundry, matériel AnyTone](https://radiofoundry.org/docs/spec/hardware-anytone).

**Statut de la documentation :** analyse enrichie ; les fonctions validées en exécution sur le D578 OEM conservent ce statut. Les valeurs historiques d'un autre poste restent rattachées à cet appareil.

**Source initialement déjà conservée dans OpenD578 :** [docs/hardware/CARTE_PLUS_AM_KT_NON_IDENTIFIE.md](../../../hardware/CARTE_PLUS_AM_KT_NON_IDENTIFIE.md). Aucune ancienne donnée n'est supprimée.

**Architecture PRO/PLUS :** la carte RF additionnelle du PLUS porte le circuit marqué `KT0905R / KT09S5R B9129` dans l'observation utilisateur et se raccorde à un connecteur situé près du RDA5802N ; ces connecteurs sont absents du PRO inspecté. Le RDA5802N est le récepteur FM de radiodiffusion, pas le récepteur AM Airband.

**Conséquence pour la carte interactive :** représenter la carte Airband du PLUS comme un module RF distinct : entrée RF propre, quartz, contrôle numérique à identifier, démodulation AM et chemin audio vers la partie principale. La matrice des pilotes doit pouvoir signaler l'absence de ce module sur PRO, même lorsque les deux postes utilisent le même GD32F303.

**Analyse attendue :** à l'activation d'Airband dans OEM PLUS, tracer les écritures GPIO/UART/I²C/SPI, les interruptions et le routage audio ; rechercher les chaînes, tables et éventuelles commandes KT dans le firmware. Ne pas attribuer le protocole d'une référence de CI similaire sans l'avoir relevé. La page RF historique renseigne les plages d'usage, pas les octets de contrôle de cette carte.

## Provenance et suite vérifiable

- Ancienne lacune identifiée : Carte RF PLUS AM distincte du RDA FM broadcast et du front end de base.
- Source historique : [guide original, édition octobre 2022](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php), rubrique « Réception de la bande aéronautique ».
- Application locale : comparer les paramètres en mode non destructif avec l'image OEM de la révision étudiée, conserver trames, adresses et horodatages.
- Niveau de preuve : les observations OEM du dépôt sont indépendantes du texte historique ; une fonctionnalité expérimentale est étiquetée comme telle.
