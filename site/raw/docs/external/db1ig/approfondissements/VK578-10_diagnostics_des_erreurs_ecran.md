# VK578-10 : Diagnostics des erreurs écran

**Revue approfondie 06/11/2026.** Source principale : [VK7ZJA, D578 mods v7.4, miroir DB1IG](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php). Complément éventuel : [RadioFoundry, matériel AnyTone](https://radiofoundry.org/docs/spec/hardware-anytone).

**Statut de la documentation :** analyse enrichie ; les fonctions validées en exécution sur le D578 OEM conservent ce statut. Les valeurs historiques d'un autre poste restent rattachées à cet appareil.

**Source initialement déjà conservée dans OpenD578 :** [docs/LED_STATUS_BUS.md](../../../LED_STATUS_BUS.md). Aucune ancienne donnée n'est supprimée.

**Séparer symptômes et causes :** les carrés blancs après une mise à jour peuvent traduire une banque d'icônes incompatible ou manquante, pas un LCD défectueux. Un démarrage incohérent peut venir de données CPS corrompues, d'un problème RTC/backup ou d'une erreur d'alimentation, qui exigent des tests distincts. Le guide historique décrit des procédures de réparation, dont certaines effacent les paramètres.

**Table de diagnostic à conserver :** `message_exact`, `contexte`, `branche_firmware`, `ressource_concernee`, `risque_perte_codeplug`, `preuve`, `action_sure`. Ne jamais grouper sous « problème écran » un défaut de bitmap et une panne du contrôleur LCD.

**Test minimal sans écriture :** photographier le message, relever les versions MCU/SCT/icons et confronter à la présence des ressources NAND. La vérification du bus LCD `PE7..PE14` reste indépendante. Toute opération de recovery, réinitialisation ou flash doit être documentée comme potentiellement destructrice, pas exécutée par le simulateur de contrôle.

## Provenance et suite vérifiable

- Ancienne lacune identifiée : Cataloguer les messages erreurs et leurs conditions, sans confondre panne flash et mauvais codeplug.
- Source historique : [guide original, édition octobre 2022](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php), rubrique « Diagnostics des erreurs écran ».
- Application locale : comparer les paramètres en mode non destructif avec l'image OEM de la révision étudiée, conserver trames, adresses et horodatages.
- Niveau de preuve : les observations OEM du dépôt sont indépendantes du texte historique ; une fonctionnalité expérimentale est étiquetée comme telle.
