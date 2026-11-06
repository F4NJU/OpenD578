# VK578-46 : Modification du haut-parleur interne

**Revue approfondie 06/11/2026.** Source principale : [VK7ZJA, D578 mods v7.4, miroir DB1IG](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php). Complément éventuel : [RadioFoundry, matériel AnyTone](https://radiofoundry.org/docs/spec/hardware-anytone).

**Statut de la documentation :** analyse enrichie ; les fonctions validées en exécution sur le D578 OEM conservent ce statut. Les valeurs historiques d'un autre poste restent rattachées à cet appareil.

**Source initialement déjà conservée dans OpenD578 :** [docs/hardware/AUDIO.md](../../../hardware/AUDIO.md). Aucune ancienne donnée n'est supprimée.

**Modification mécanique documentée :** VK7ZJA décrit la perforation de la plaque de fond du haut-parleur interne pour diminuer la résistance acoustique. Il rapporte un gain d'environ 2 dB dans ses conditions. Ce chiffre est un résultat de sa modification et n'est pas une augmentation du gain électrique du YD1517P.

**Séparer les modèles :** la puissance de l'amplificateur, l'atténuation du U2429G, le mute GPIO et la réponse du haut-parleur sont des fonctions différentes. Une réponse acoustique plus forte ne démontre pas un changement des registres audio.

**Protocole comparatif :** niveau, distance, fréquence, orientation et pièce constants ; mesure SPL ou enregistrement calibré avant/après. Ajouter à la documentation photos et dimensions du HP seulement avec provenance. Ne pas proposer de modification irréversible du châssis comme prérequis pour tester le firmware.

## Provenance et suite vérifiable

- Ancienne lacune identifiée : Modification mecanique HP et difference mesuree en historique, pas driver audio.
- Source historique : [guide original, édition octobre 2022](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php), rubrique « Modification du haut-parleur interne ».
- Application locale : comparer les paramètres en mode non destructif avec l'image OEM de la révision étudiée, conserver trames, adresses et horodatages.
- Niveau de preuve : les observations OEM du dépôt sont indépendantes du texte historique ; une fonctionnalité expérimentale est étiquetée comme telle.
