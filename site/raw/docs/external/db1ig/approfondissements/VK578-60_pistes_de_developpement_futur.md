# VK578-60 : Pistes de développement futur

**Revue approfondie 06/11/2026.** Source principale : [VK7ZJA, D578 mods v7.4, miroir DB1IG](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php). Complément éventuel : [RadioFoundry, matériel AnyTone](https://radiofoundry.org/docs/spec/hardware-anytone).

**Statut de la documentation :** analyse enrichie ; les fonctions validées en exécution sur le D578 OEM conservent ce statut. Les valeurs historiques d'un autre poste restent rattachées à cet appareil.

**Source initialement déjà conservée dans OpenD578 :** [docs/firmware/ARCHITECTURE.md](../../../firmware/ARCHITECTURE.md). Aucune ancienne donnée n'est supprimée.

**Idées étudiées dans l'article historique :** exploiter les capacités du TLV320AIC3204 (égaliseur, gain numérique, filtrage), déporter physiquement la façade par nappe 40 voies, modifier les ressources graphiques et examiner le firmware interne du SCT3258. L'auteur comparait aussi l'organisation de certaines mises à jour SCT avec des équipements Hytera, sans démontrer la possibilité d'installer Codec2.

**Priorités pragmatiques OpenD578 :** (1) garder les pilotes FM/DMR, écran, NAND et CPS simples ; (2) valider le chemin des commandes du codec via `CODEC_SELECT`/`I2C_OPERATION`, puis seulement programmer EQ ou AGC ; (3) traiter le lien façade comme un problème de signal électrique ; (4) évaluer `CHAN_D` et `VOCODER_IO_SET` pour des fonctions de transfert vocal, sans modifier le firmware propriétaire du SCT.

**Règles de preuve :** un périphérique dont la commande est connue du firmware OEM est acquis pour la révision testée. Une idée mentionnée comme possibilité historique ne devient pas une fonction implémentée tant qu'il n'existe ni routine OEM ni validation. L'architecture doit limiter les fonctions optionnelles pour préserver la stabilité du mode satellite futur.

## Provenance et suite vérifiable

- Ancienne lacune identifiée : Etudier codec DSP, nappe facade et vocoder comme pistes futures, pas fonctions OEM implementees.
- Source historique : [guide original, édition octobre 2022](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php), rubrique « Pistes de développement futur ».
- Application locale : comparer les paramètres en mode non destructif avec l'image OEM de la révision étudiée, conserver trames, adresses et horodatages.
- Niveau de preuve : les observations OEM du dépôt sont indépendantes du texte historique ; une fonctionnalité expérimentale est étiquetée comme telle.
