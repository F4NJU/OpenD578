# VK578-16 : Écran et façade déportés

**Revue approfondie 06/11/2026.** Source principale : [VK7ZJA, D578 mods v7.4, miroir DB1IG](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php). Complément éventuel : [RadioFoundry, matériel AnyTone](https://radiofoundry.org/docs/spec/hardware-anytone).

**Statut de la documentation :** analyse enrichie ; les fonctions validées en exécution sur le D578 OEM conservent ce statut. Les valeurs historiques d'un autre poste restent rattachées à cet appareil.

**Source initialement déjà conservée dans OpenD578 :** [docs/LCD_CABLAGE_PILOTAGE_ET_INTEGRATION_V11_8.md](../../../LCD_CABLAGE_PILOTAGE_ET_INTEGRATION_V11_8.md). Aucune ancienne donnée n'est supprimée.

**Observation historique :** le guide VK7ZJA mentionne l'idée d'une façade séparée par rallongement de la nappe plate d'environ 40 voies. Ce n'est pas une fonction logicielle de déport native ni la garantie qu'un câble long fonctionne sans retouche.

**Pourquoi le détail compte :** notre pilote LCD exploite les écritures parallèles `PE7..PE14` et les strobes `PB10..PB13`. Une nappe longue pourrait accroître la capacité et les réflexions ; alimentation, masse, touches, éclairage, ADC des volumes et microphone font aussi partie de la connectique de façade.

**Dossier électrique requis :** attribuer une fonction à chaque broche de la nappe par continuité et documentation OEM ; rechercher les rails GND/3,3 V/5 V et les retours ; mesurer l'intégrité des signaux et la marge des temporisations LCD. Les GPIO MCU ne sont pas les numéros physiques de la nappe. Le site doit montrer séparément leur topologie et l'hypothèse de déport.

## Provenance et suite vérifiable

- Ancienne lacune identifiée : Nappe facade de 40 voies citee comme option de deport non OEM ; integrite signal.
- Source historique : [guide original, édition octobre 2022](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php), rubrique « Écran et façade déportés ».
- Application locale : comparer les paramètres en mode non destructif avec l'image OEM de la révision étudiée, conserver trames, adresses et horodatages.
- Niveau de preuve : les observations OEM du dépôt sont indépendantes du texte historique ; une fonctionnalité expérimentale est étiquetée comme telle.
