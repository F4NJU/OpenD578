# VK578-35 : Découpages de réception FM

**Revue approfondie 06/11/2026.** Source principale : [VK7ZJA, D578 mods v7.4, miroir DB1IG](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php). Complément éventuel : [RadioFoundry, matériel AnyTone](https://radiofoundry.org/docs/spec/hardware-anytone).

**Statut de la documentation :** analyse enrichie ; les fonctions validées en exécution sur le D578 OEM conservent ce statut. Les valeurs historiques d'un autre poste restent rattachées à cet appareil.

**Source initialement déjà conservée dans OpenD578 :** [docs/hardware/RF.md](../../../hardware/RF.md). Aucune ancienne donnée n'est supprimée.

**Front-end et sensibilité :** les mesures VK7ZJA montrent une réception médiocre à certaines fréquences hors bandes nominales, bien que le poste puisse y afficher une fréquence. Cela cadre avec les quatre étages de filtrage de suivi à varactors décrits pour les entrées VHF/UHF, ainsi qu'avec les commandes `BPFL*`, `BPFM*`, `BPFH*` du mode TEST.

**Repères historiques :** les mesures de synthèse sont données dans l'ancien guide pour un critère de 10 dBQ en NFM, environ 0,18 µV en VHF et 0,20 µV en UHF. Des essais très hors bande sont plusieurs dizaines de dB plus défavorables. Les résultats ne sont pas la calibration de notre PCB.

**Démarche firmware :** distinguer `PLL_locked`, `RF_gain`, `RF_tracking_voltage`, `IF_gain` et `squelch`; chercher la relation fréquence→valeurs de réglage dans la NAND et les écritures DAC/BH2226. Une fréquence programmée correcte ne suffit pas à déclarer un profil RF validé. Conserver fréquence, niveau injecté, critère et mode dans chaque capture.

## Provenance et suite vérifiable

- Ancienne lacune identifiée : Cas hors bande : filtres front-end expliquent variation sensibilite.
- Source historique : [guide original, édition octobre 2022](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php), rubrique « Découpages de réception FM ».
- Application locale : comparer les paramètres en mode non destructif avec l'image OEM de la révision étudiée, conserver trames, adresses et horodatages.
- Niveau de preuve : les observations OEM du dépôt sont indépendantes du texte historique ; une fonctionnalité expérimentale est étiquetée comme telle.
