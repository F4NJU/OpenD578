# VK578-41 : Mot de passe au démarrage

**Revue approfondie 06/11/2026.** Source principale : [VK7ZJA, D578 mods v7.4, miroir DB1IG](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php). Complément éventuel : [RadioFoundry, matériel AnyTone](https://radiofoundry.org/docs/spec/hardware-anytone).

**Statut de la documentation :** analyse enrichie ; les fonctions validées en exécution sur le D578 OEM conservent ce statut. Les valeurs historiques d'un autre poste restent rattachées à cet appareil.

**Source initialement déjà conservée dans OpenD578 :** [docs/cps/COMPATIBILITE_PRO_PLUS.md](../../../cps/COMPATIBILITE_PRO_PLUS.md). Aucune ancienne donnée n'est supprimée.

**Fonction de protection :** le mot de passe demandé au démarrage protège l'usage du poste, mais il n'est pas équivalent au mot de passe de programmation CPS, aux permissions d'alignement TEST ou au contrôle du bootloader. Réinitialiser l'appareil peut effacer un codeplug sans lever les autres protections.

**Modélisation :** distinguer `user_lock_boot`, `cps_programming_lock`, `service_mode_permission`, `update_mode` et `sct_boot_mode`. Chaque état a son propre flux d'interface et sa propre politique de sauvegarde. Aucun de ces éléments ne peut être déduit du champ `mode_code` seul.

**Cas de diagnostic non destructif :** relever la chaîne exacte affichée, confirmer les versions et le profil des paramètres, comparer au manuel avant action. Toute procédure de récupération historique doit indiquer la perte possible de configuration. Ne pas construire de contournement automatique de mot de passe dans le pilote alternatif.

## Provenance et suite vérifiable

- Ancienne lacune identifiée : Mot de passe de demarrage : mode recovery distinct de verrou CPS.
- Source historique : [guide original, édition octobre 2022](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php), rubrique « Mot de passe au démarrage ».
- Application locale : comparer les paramètres en mode non destructif avec l'image OEM de la révision étudiée, conserver trames, adresses et horodatages.
- Niveau de preuve : les observations OEM du dépôt sont indépendantes du texte historique ; une fonctionnalité expérimentale est étiquetée comme telle.
