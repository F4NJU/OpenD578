# VK578-42 : Mot de passe de programmation CPS

**Revue approfondie 06/11/2026.** Source principale : [VK7ZJA, D578 mods v7.4, miroir DB1IG](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php). Complément éventuel : [RadioFoundry, matériel AnyTone](https://radiofoundry.org/docs/spec/hardware-anytone).

**Statut de la documentation :** analyse enrichie ; les fonctions validées en exécution sur le D578 OEM conservent ce statut. Les valeurs historiques d'un autre poste restent rattachées à cet appareil.

**Source initialement déjà conservée dans OpenD578 :** [docs/cps/PROTOCOLE_OEM_V121.md](../../../cps/PROTOCOLE_OEM_V121.md). Aucune ancienne donnée n'est supprimée.

**Séparation CPS :** l'authentification ou mot de passe de programmation se situe au niveau de l'accès au codeplug, distinct du transport USB CDC et du protocole de trames `PROGRAM/R/W/END` reconstruit. Une réussite du handshake n'implique pas que l'ensemble des zones NAND soit lisible ou éditable.

**Pour l'analyseur :** tracer `USB_session`, `CPS_handshake`, `model_identity`, `lock_state`, `read_write_permission`, `codeplug_region` et `reply`. Si la réponse indique une protection, elle ne doit pas être assimilée à un timeout ou à un checksum invalide. Les secrets ne doivent pas entrer dans les journaux publics.

**Validation :** capturer des sessions autorisées sur le poste propriétaire (avec et sans option de mot de passe si l'utilisateur en a la maîtrise), puis déduire séparément la machine d'état d'accès et le format des canaux. Le dossier de compatibilité PRO/PLUS conserve ces cas par version.

## Provenance et suite vérifiable

- Ancienne lacune identifiée : Mot de passe CPS : ne pas le confondre avec cle crypto ou deverrouillage TEST.
- Source historique : [guide original, édition octobre 2022](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php), rubrique « Mot de passe de programmation CPS ».
- Application locale : comparer les paramètres en mode non destructif avec l'image OEM de la révision étudiée, conserver trames, adresses et horodatages.
- Niveau de preuve : les observations OEM du dépôt sont indépendantes du texte historique ; une fonctionnalité expérimentale est étiquetée comme telle.
