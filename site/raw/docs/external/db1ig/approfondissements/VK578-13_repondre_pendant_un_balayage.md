# VK578-13 : Répondre pendant un balayage

**Revue approfondie 06/11/2026.** Source principale : [VK7ZJA, D578 mods v7.4, miroir DB1IG](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php). Complément éventuel : [RadioFoundry, matériel AnyTone](https://radiofoundry.org/docs/spec/hardware-anytone).

**Statut de la documentation :** analyse enrichie ; les fonctions validées en exécution sur le D578 OEM conservent ce statut. Les valeurs historiques d'un autre poste restent rattachées à cet appareil.

**Source initialement déjà conservée dans OpenD578 :** [docs/cps/PROTOCOLE_OEM_V121.md](../../../cps/PROTOCOLE_OEM_V121.md). Aucune ancienne donnée n'est supprimée.

**Fonction d'interface :** répondre à un correspondant pendant un balayage demande de distinguer le canal sélectionné initialement du canal où le balayage s'est arrêté. Le guide donne cette fonction comme usage du poste, sans établir une API de synthétiseur spécifique.

**Machine d'état proposée :** `SCANNING -> STOPPED_ON_ACTIVITY -> HOLD_WINDOW -> RESUME`, avec mémorisation de `home_channel`, `detected_channel`, `scan_resume_policy`, `tx_eligible` et `timeout`. Le PTT doit choisir une fréquence TX valide liée au canal détecté uniquement si la politique CPS/firmware l'autorise ; ne jamais modifier implicitement un codeplug.

**Preuve attendue :** comparer les transitions OEM d'écran, la sélection RF et le canal émis en simulation non TX ou sur banc d'atténuation adapté. Les signaux détectés par le squelch et les événements PTT doivent avoir des horodatages. Rien dans la page DB1IG ne fixe un timeout universel : le paramètre reste dépendant de la configuration.

## Provenance et suite vérifiable

- Ancienne lacune identifiée : Comportement PTT sur canal detecte en balayage : politique UI/timer.
- Source historique : [guide original, édition octobre 2022](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php), rubrique « Répondre pendant un balayage ».
- Application locale : comparer les paramètres en mode non destructif avec l'image OEM de la révision étudiée, conserver trames, adresses et horodatages.
- Niveau de preuve : les observations OEM du dépôt sont indépendantes du texte historique ; une fonctionnalité expérimentale est étiquetée comme telle.
