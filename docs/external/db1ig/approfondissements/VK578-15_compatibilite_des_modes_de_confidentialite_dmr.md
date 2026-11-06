# VK578-15 : Compatibilité des modes de confidentialité DMR

**Revue approfondie 06/11/2026.** Source principale : [VK7ZJA, D578 mods v7.4, miroir DB1IG](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php). Complément éventuel : [RadioFoundry, matériel AnyTone](https://radiofoundry.org/docs/spec/hardware-anytone).

**Statut de la documentation :** analyse enrichie ; les fonctions validées en exécution sur le D578 OEM conservent ce statut. Les valeurs historiques d'un autre poste restent rattachées à cet appareil.

**Source initialement déjà conservée dans OpenD578 :** [docs/peripherals/04_DMR_SCT3258_BOOTSTRAP_HPI_PAQUETS_CODEC_PARAMETRES.md](../../../peripherals/04_DMR_SCT3258_BOOTSTRAP_HPI_PAQUETS_CODEC_PARAMETRES.md). Aucune ancienne donnée n'est supprimée.

**Niveaux DMR :** ne pas confondre *Basic Privacy*, mécanismes propriétaires de chiffrement et contrôle d'accès RAS. RAS peut délibérément modifier un contrôle de validité des transmissions sans être un chiffrement vocal. Les postes AnyTone ne sont pas nécessairement compatibles avec toutes les implémentations de confidentialité d'autres marques.

**Apport RadioFoundry :** le MCU configure le SCT3258 avec des champs `DMR_CALL_*`, `DMR_CC`, `DMR_FLC`. Les commandes `VOCODER_IO_SET` et `CHAN_D` existent dans le firmware OEM pour enregistrer/rejouer des données vocales, donc l'accès aux flux n'est pas théoriquement exclu. Le format, la latence et la synchronisation restent à vérifier pour un pont hotspot ou une transformation volontaire de données AMBE.

**Cas de tests :** appel clair, groupe, privé, flux RAS, erreurs CRC, tentative de Basic Privacy, écran/LED malgré absence audio. Ne pas annoncer un décryptage universel : l'absence de compatibilité est une propriété des profils radio, non une panne HPI. Documenter toute fonction de confidentialité sans publier de clés privées.

## Provenance et suite vérifiable

- Ancienne lacune identifiée : Les modes de privacy ne sont pas tous inter-operables ; distinguer baseband du chiffrement utilisateur.
- Source historique : [guide original, édition octobre 2022](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php), rubrique « Compatibilité des modes de confidentialité DMR ».
- Application locale : comparer les paramètres en mode non destructif avec l'image OEM de la révision étudiée, conserver trames, adresses et horodatages.
- Niveau de preuve : les observations OEM du dépôt sont indépendantes du texte historique ; une fonctionnalité expérimentale est étiquetée comme telle.
