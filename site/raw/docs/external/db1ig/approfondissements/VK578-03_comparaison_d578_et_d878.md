# VK578-03 : Comparaison D578 et D878

**Revue approfondie 06/11/2026.** Source principale : [VK7ZJA, D578 mods v7.4, miroir DB1IG](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php). Complément éventuel : [RadioFoundry, matériel AnyTone](https://radiofoundry.org/docs/spec/hardware-anytone).

**Statut de la documentation :** analyse enrichie ; les fonctions validées en exécution sur le D578 OEM conservent ce statut. Les valeurs historiques d'un autre poste restent rattachées à cet appareil.

**Source initialement déjà conservée dans OpenD578 :** [docs/hardware/BLUETOOTH_PRO_PLUS_D878_COMPARAISON.md](../../../hardware/BLUETOOTH_PRO_PLUS_D878_COMPARAISON.md). Aucune ancienne donnée n'est supprimée.

**Architecture :** le D578 réalise une double réception analogique réelle avec deux chaînes RF indépendantes, contrairement au balayage de deux VFO de certains portables. La disponibilité d'une seule chaîne de traitement DMR simultané est une contrainte distincte du nombre de récepteurs analogiques. Le guide VK7ZJA documente cette distinction et notre banc connaît quatre banques QA4818N.

**Modèle logiciel :** `receiver[2]` doit avoir fréquence RX, état squelch, niveau RSSI, audio et largeur de bande propres. Le routage DMR se représente comme une ressource partagée (`dmr_owner=A|B|none`), sans fabriquer deux vocoders SCT3258. Il faut distinguer deux voies FM ouvertes à la fois, une voie DMR, et la gestion de priorité sonore.

**À vérifier par traces OEM :** la sélection de banque lors de deux réceptions FM simultanées, la propriété de la chaîne DMR, le changement de priorité A/B, le comportement du squelch et l'audio quand les deux signaux sont présents. Les banques présentes dans le modèle ne donnent pas à elles seules l'attribution physique de chaque CI.

## Provenance et suite vérifiable

- Ancienne lacune identifiée : Dual RX D578 contre dual watch D878 ; une seule chaine DMR simultanee.
- Source historique : [guide original, édition octobre 2022](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php), rubrique « Comparaison D578 et D878 ».
- Application locale : comparer les paramètres en mode non destructif avec l'image OEM de la révision étudiée, conserver trames, adresses et horodatages.
- Niveau de preuve : les observations OEM du dépôt sont indépendantes du texte historique ; une fonctionnalité expérimentale est étiquetée comme telle.
