# VK578-05 : Conseils d'utilisation du CPS

**Revue approfondie 06/11/2026.** Source principale : [VK7ZJA, D578 mods v7.4, miroir DB1IG](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php). Complément éventuel : [RadioFoundry, matériel AnyTone](https://radiofoundry.org/docs/spec/hardware-anytone).

**Statut de la documentation :** analyse enrichie ; les fonctions validées en exécution sur le D578 OEM conservent ce statut. Les valeurs historiques d'un autre poste restent rattachées à cet appareil.

**Source initialement déjà conservée dans OpenD578 :** [docs/cps/COMPATIBILITE_PRO_PLUS.md](../../../cps/COMPATIBILITE_PRO_PLUS.md). Aucune ancienne donnée n'est supprimée.

**Point documentaire précis :** `Tool > Export > Export All` n'englobe pas toutes les *Optional Settings* et, d'après le guide historique, ne sauvegarde pas certaines données privées de configuration. Les captures des réglages, notamment les options de microphone et de signalisation, sont une sauvegarde logique différente des canaux exportés.

**Architecture d'un sauvegardeur :** sauvegarder quatre ressources indépendantes : (1) dump brut du codeplug si disponible, (2) export CPS structuré, (3) version et profil matériel, (4) description des options non exportées, avec marqueurs « non disponible » plutôt que des valeurs par défaut inventées. Si des secrets sont présents, les conserver uniquement hors dépôt public et chiffrés côté utilisateur.

**Tests :** export/import sans changement de version ; mise à niveau CPS avec conservation des zones/contacts ; comparaison des options non exportées ; rollback sur copie de travail. Notre protocole USB `PROGRAM/R/W/END` reste la preuve primaire de la lecture/écriture, distincte de ces règles de migration.

## Provenance et suite vérifiable

- Ancienne lacune identifiée : Exporter les options non couvertes par Export All ; profil CPS/firmware/codeplug.
- Source historique : [guide original, édition octobre 2022](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php), rubrique « Conseils d'utilisation du CPS ».
- Application locale : comparer les paramètres en mode non destructif avec l'image OEM de la révision étudiée, conserver trames, adresses et horodatages.
- Niveau de preuve : les observations OEM du dépôt sont indépendantes du texte historique ; une fonctionnalité expérimentale est étiquetée comme telle.
