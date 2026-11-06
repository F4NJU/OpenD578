# VK578-53 : Utilitaire de sauvegarde NAND

**Revue approfondie 06/11/2026.** Source principale : [VK7ZJA, D578 mods v7.4, miroir DB1IG](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php). Complément éventuel : [RadioFoundry, matériel AnyTone](https://radiofoundry.org/docs/spec/hardware-anytone).

**Statut de la documentation :** analyse enrichie ; les fonctions validées en exécution sur le D578 OEM conservent ce statut. Les valeurs historiques d'un autre poste restent rattachées à cet appareil.

**Source initialement déjà conservée dans OpenD578 :** [docs/03_NAND_LECTURES_ECC_CARTE.md](../../../03_NAND_LECTURES_ECC_CARTE.md). Aucune ancienne donnée n'est supprimée.

**Outils et données :** le guide VK7ZJA attribue à Colin G4EML un utilitaire de lecture/écriture de la NAND externe. Il concerne les paramètres RF, codeplug, images, contacts et enregistrements, à distinguer du programme GD32 en Flash interne et du firmware propre au SCT3258.

**Notre preuve actuelle :** OpenD578 possède une capture de NAND `main + OOB + ECC` avec rapports de checksum et partitions ; le banc reproduit les commandes `0x9F`, `0x0F`, `0x13`, `0x03` et le protocole CPS `R/W` dans les limites documentées. Les adresses CPS, les adresses NAND et les adresses ARM ne sont pas le même espace.

**Mise en sûreté :** préserver un dump brut en lecture seule, OOB compris, deux copies hashées et un rapport de bad blocks, puis travailler sur une copie. Les zones d'alignement et la zone de configuration ne doivent jamais être réécrites sur la base de la carte d'un autre poste. Documenter la version de NAND, le sens des offsets et les erreurs ECC avant de promettre une restauration.

## Provenance et suite vérifiable

- Ancienne lacune identifiée : Outils de lecture historiques et sauvegardes sans operation destructrice.
- Source historique : [guide original, édition octobre 2022](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php), rubrique « Utilitaire de sauvegarde NAND ».
- Application locale : comparer les paramètres en mode non destructif avec l'image OEM de la révision étudiée, conserver trames, adresses et horodatages.
- Niveau de preuve : les observations OEM du dépôt sont indépendantes du texte historique ; une fonctionnalité expérimentale est étiquetée comme telle.
