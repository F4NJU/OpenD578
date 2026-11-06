# VK578-02 : Erreurs de bande

**Revue approfondie 06/11/2026.** Source principale : [VK7ZJA, D578 mods v7.4, miroir DB1IG](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php). Complément éventuel : [RadioFoundry, matériel AnyTone](https://radiofoundry.org/docs/spec/hardware-anytone).

**Statut de la documentation :** analyse enrichie ; les fonctions validées en exécution sur le D578 OEM conservent ce statut. Les valeurs historiques d'un autre poste restent rattachées à cet appareil.

**Source initialement déjà conservée dans OpenD578 :** [docs/cps/COMPATIBILITE_PRO_PLUS.md](../../../cps/COMPATIBILITE_PRO_PLUS.md). Aucune ancienne donnée n'est supprimée.

**Constat :** les plages RX/TX accessibles dépendent du code MODE, de la branche de firmware et des validations du CPS. Une erreur de bande après import d'un fichier `.rdt` n'est donc ni un problème de synthétiseur QA4818N, ni nécessairement un défaut de mémoire NAND. Le modèle PRO V1.21 et le PLUS V2.x ne doivent pas partager un validateur unique de bande.

**À implémenter :** le diagnostic CPS doit conserver séparément `model`, `cpu_family`, `firmware_version`, `cps_version`, `codeplug_format`, `mode_code`, `rx_frequency`, `tx_frequency` et l'origine du fichier. Signaler un champ hors profil sans corriger silencieusement la fréquence. Utiliser les canaux déjà décodés à 64 octets comme base de comparaison, sans extrapoler le reste du codeplug.

**Cas de tests :** (a) canal VHF/RX valide mais TX interdit par le MODE, (b) bande UHF d'une autre édition, (c) migration PRO vers PLUS, (d) fichier CPS accepté mais canal invalidé. Conserver les octets originaux et produire un diff, jamais une migration destructive.

## Provenance et suite vérifiable

- Ancienne lacune identifiée : Version MODE/RDT et provenance codeplug : garder separer des addresses NAND.
- Source historique : [guide original, édition octobre 2022](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php), rubrique « Erreurs de bande ».
- Application locale : comparer les paramètres en mode non destructif avec l'image OEM de la révision étudiée, conserver trames, adresses et horodatages.
- Niveau de preuve : les observations OEM du dépôt sont indépendantes du texte historique ; une fonctionnalité expérimentale est étiquetée comme telle.
