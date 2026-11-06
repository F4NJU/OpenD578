# VK578-28 : Numérotation et carnets EchoLink

**Revue approfondie 06/11/2026.** Source principale : [VK7ZJA, D578 mods v7.4, miroir DB1IG](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php). Complément éventuel : [RadioFoundry, matériel AnyTone](https://radiofoundry.org/docs/spec/hardware-anytone).

**Statut de la documentation :** analyse enrichie ; les fonctions validées en exécution sur le D578 OEM conservent ce statut. Les valeurs historiques d'un autre poste restent rattachées à cet appareil.

**Source initialement déjà conservée dans OpenD578 :** [docs/cps/CODEPLUG_CANAL_OEM_V121.md](../../../cps/CODEPLUG_CANAL_OEM_V121.md). Aucune ancienne donnée n'est supprimée.

**Distinction protocolaire :** la numérotation EchoLink est une configuration d'usage, généralement associée à des séquences de touches ou tonalités de contrôle, et non à une commande du SCT3258. Le carnet CPS peut inclure des numéros et règles d'appel, sans correspondre aux enregistrements de contacts DMR.

**Modèle documentaire :** séparer `dtmf_sequence`, `echolink_command`, `user_contact`, `dmr_id` et `dmr_contact_record`. Le traitement par le poste doit pouvoir sélectionner le bon mode de signalisation selon le canal et la configuration des touches. Un identifiant EchoLink numérique ne doit jamais être importé comme DMR ID.

**Validation :** caractériser les sorties DTMF en FM sur un récepteur de mesure, la réaction des touches microphone et le format CPS correspondant. La source historique ne décrit pas les adresses NAND de ces éléments : les champs restent marqués « localisation mémoire non relevée », sans remettre en cause la fonction utilisateur du poste.

## Provenance et suite vérifiable

- Ancienne lacune identifiée : EchoLink et numerotation : comportement de carnet CPS non couche SCT HPI.
- Source historique : [guide original, édition octobre 2022](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php), rubrique « Numérotation et carnets EchoLink ».
- Application locale : comparer les paramètres en mode non destructif avec l'image OEM de la révision étudiée, conserver trames, adresses et horodatages.
- Niveau de preuve : les observations OEM du dépôt sont indépendantes du texte historique ; une fonctionnalité expérimentale est étiquetée comme telle.
