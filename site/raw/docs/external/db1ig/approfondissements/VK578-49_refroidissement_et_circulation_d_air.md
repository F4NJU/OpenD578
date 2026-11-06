# VK578-49 : Refroidissement et circulation d'air

**Revue approfondie 06/11/2026.** Source principale : [VK7ZJA, D578 mods v7.4, miroir DB1IG](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php). Complément éventuel : [RadioFoundry, matériel AnyTone](https://radiofoundry.org/docs/spec/hardware-anytone).

**Statut de la documentation :** analyse enrichie ; les fonctions validées en exécution sur le D578 OEM conservent ce statut. Les valeurs historiques d'un autre poste restent rattachées à cet appareil.

**Source initialement déjà conservée dans OpenD578 :** [docs/hardware/ETAGES_RF_PROTECTION_FI.md](../../../hardware/ETAGES_RF_PROTECTION_FI.md). Aucune ancienne donnée n'est supprimée.

**Gestion thermique :** sur les D578 décrits historiquement, le refroidissement repose sur le dissipateur du boîtier et un ventilateur arrière. VK7ZJA rapporte qu'inverser son sens de circulation et guider le flux avec une petite gaine peut améliorer la dissipation, mais sans fournir de courbe thermométrique exhaustive. Il recommande une ventilation additionnelle si le service à forte puissance est prolongé.

**Dans OpenD578 :** différencier `fan_request`, `fan_gpio_or_bus_write`, `measured_heatsink_temp`, `PA_temp_if_available`, `TX_duty_cycle` et `thermal_derating`. Le modèle de banc a relevé une commande de ventilateur dans la banque RF, mais cette trace ne démontre pas encore quelle broche commute physiquement le moteur.

**Essai à préparer :** capteur sur le dissipateur, consommation ventilation, température ambiante, puissance et durée d'émission contrôlées. Ne pas promettre un gain thermique quantifié sans la mesure. Conserver le lien historique F1DMG `/578a`, sans supposer que ses anciennes photos soient encore accessibles.

## Provenance et suite vérifiable

- Ancienne lacune identifiée : Ventilateur, sens de flux et F1DMG ancien : mesure thermique avant modification.
- Source historique : [guide original, édition octobre 2022](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php), rubrique « Refroidissement et circulation d'air ».
- Application locale : comparer les paramètres en mode non destructif avec l'image OEM de la révision étudiée, conserver trames, adresses et horodatages.
- Niveau de preuve : les observations OEM du dépôt sont indépendantes du texte historique ; une fonctionnalité expérimentale est étiquetée comme telle.
