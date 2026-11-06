# VK578-31 : Extension historique de la réception

**Revue approfondie 06/11/2026.** Source principale : [VK7ZJA, D578 mods v7.4, miroir DB1IG](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php). Complément éventuel : [RadioFoundry, matériel AnyTone](https://radiofoundry.org/docs/spec/hardware-anytone).

**Statut de la documentation :** analyse enrichie ; les fonctions validées en exécution sur le D578 OEM conservent ce statut. Les valeurs historiques d'un autre poste restent rattachées à cet appareil.

**Source initialement déjà conservée dans OpenD578 :** [docs/hardware/RF.md](../../../hardware/RF.md). Aucune ancienne donnée n'est supprimée.

**Historique sans confusion des images :** les packages modifiés cités par VK7ZJA sont notamment issus des branches non-PLUS v1.16n et PLUS v2.03n. Ils prétendent étendre certaines plages de réception, mais ces binaires ne représentent pas la cible OpenD578 PRO GD32 V1.21 ni notre PLUS actuel.

**Limite physique :** une PLL peut se verrouiller hors bande alors que les filtres accordables en entrée atténuent le signal, d'où une sensibilité très variable. Même un affichage de fréquence accepté par le CPS n'est pas une preuve de démodulation satisfaisante. Aucune plage de TX supplémentaire ne doit être considérée sûre.

**Pour le projet :** inventorier les tables de plage dans chaque binaire séparément, identifier le code de décision RX/TX, comparer sans flasher des images modifiées, puis réunir les mesures de RSSI/sensibilité de référence. Le développement satellite doit rester borné aux bandes autorisées et calibrées de chaque appareil.

## Provenance et suite vérifiable

- Ancienne lacune identifiée : Ne pas confondre FW RX modifie de 2022 avec PRO GD32 V1.21.
- Source historique : [guide original, édition octobre 2022](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php), rubrique « Extension historique de la réception ».
- Application locale : comparer les paramètres en mode non destructif avec l'image OEM de la révision étudiée, conserver trames, adresses et horodatages.
- Niveau de preuve : les observations OEM du dépôt sont indépendantes du texte historique ; une fonctionnalité expérimentale est étiquetée comme telle.
