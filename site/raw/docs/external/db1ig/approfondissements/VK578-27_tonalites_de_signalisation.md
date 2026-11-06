# VK578-27 : Tonalités de signalisation

**Revue approfondie 06/11/2026.** Source principale : [VK7ZJA, D578 mods v7.4, miroir DB1IG](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php). Complément éventuel : [RadioFoundry, matériel AnyTone](https://radiofoundry.org/docs/spec/hardware-anytone).

**Statut de la documentation :** analyse enrichie ; les fonctions validées en exécution sur le D578 OEM conservent ce statut. Les valeurs historiques d'un autre poste restent rattachées à cet appareil.

**Source initialement déjà conservée dans OpenD578 :** [docs/hardware/AUDIO.md](../../../hardware/AUDIO.md). Aucune ancienne donnée n'est supprimée.

**Trois chemins différents :** les bips d'interface et signalisations utilisateur passent par la chaîne audio, les tonalités CTCSS/DCS influencent la modulation RF et les messages vocaux DMR sont gérés via le SCT3258. Les regrouper dans une routine audio unique conduit à de mauvaises conclusions sur les registres.

**Recette de référence non musicale :** le guide VK7ZJA donne pour le bip d'autorisation TX une séquence de cinq entrées dont quatre actives : 1570 Hz/50 ms, 1050 Hz/40 ms, 1570 Hz/40 ms et 1320 Hz/40 ms, puis silence. La première durée est présentée comme un ajustement historique de firmware et n'est pas un timing mesuré sur V1.21.

**Analyse OEM à produire :** enregistrer l'appel UI, le générateur de ton, l'activation amplificateur PA7, le chemin U2429G/codec et les éventuels accès SCT. Pour la comparaison, injecter des événements d'interface sans transmettre et analyser la sortie haut-parleur sur oscilloscope ou capture audio. Ne pas assimiler ces tons au DMR `TONEU/TONEV2` du mode TEST.

## Provenance et suite vérifiable

- Ancienne lacune identifiée : Tonalites constructeur a analyser comme stimuli audio, distinctes CTCSS/DCS.
- Source historique : [guide original, édition octobre 2022](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php), rubrique « Tonalités de signalisation ».
- Application locale : comparer les paramètres en mode non destructif avec l'image OEM de la révision étudiée, conserver trames, adresses et horodatages.
- Niveau de preuve : les observations OEM du dépôt sont indépendantes du texte historique ; une fonctionnalité expérimentale est étiquetée comme telle.
