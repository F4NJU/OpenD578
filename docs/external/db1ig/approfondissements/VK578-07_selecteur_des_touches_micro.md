# VK578-07 : Sélecteur des touches micro

**Revue approfondie 06/11/2026.** Source principale : [VK7ZJA, D578 mods v7.4, miroir DB1IG](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php). Complément éventuel : [RadioFoundry, matériel AnyTone](https://radiofoundry.org/docs/spec/hardware-anytone).

**Statut de la documentation :** analyse enrichie ; les fonctions validées en exécution sur le D578 OEM conservent ce statut. Les valeurs historiques d'un autre poste restent rattachées à cet appareil.

**Source initialement déjà conservée dans OpenD578 :** [docs/NOTICE_CHANGELOG_MICROPHONE_V11_8.md](../../../NOTICE_CHANGELOG_MICROPHONE_V11_8.md). Aucune ancienne donnée n'est supprimée.

**Deux couches indépendantes :** le sélecteur mécanique du microphone OEM définit le rôle des touches haut/bas, alors que la liaison série transporte des codes d'événements. Notre banc a déjà reconstruit des trames de 8 octets `41 ... 06` du microphone vers le poste et de 16 octets `53 ... 06` dans l'autre sens.

**Réutilisation :** le pilote microphone doit d'abord décoder un événement physique (code, type d'appui, PTT), puis appliquer le profil de clavier actif (volume, canal, VFO, navigation). Ce profil ne doit pas être codé en dur dans la routine UART. Les variantes Alinco ne sont pas une preuve de codes identiques.

**Tests :** maintenir UP/DOWN tout en changeant la sélection mécanique, appui long/court et événement simultané avec PTT ; enregistrer les octets réellement reçus. Comparer la table des codes à `NOTICE_CHANGELOG_MICROPHONE_V11_8.md` sans attribuer les GPIO PA9/PA10 à une seconde interface non vérifiée.

## Provenance et suite vérifiable

- Ancienne lacune identifiée : Interrupteur lateral Up/Down du microphone OEM distinct de trame USART0.
- Source historique : [guide original, édition octobre 2022](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php), rubrique « Sélecteur des touches micro ».
- Application locale : comparer les paramètres en mode non destructif avec l'image OEM de la révision étudiée, conserver trames, adresses et horodatages.
- Niveau de preuve : les observations OEM du dépôt sont indépendantes du texte historique ; une fonctionnalité expérimentale est étiquetée comme telle.
