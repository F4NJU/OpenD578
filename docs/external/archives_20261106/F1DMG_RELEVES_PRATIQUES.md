# F1DMG : observations d'utilisation et modifications de poste

Cette fiche rassemble les elements retrouves dans les originaux `page-20.htm` et `page-22.htm` de la sauvegarde privee du 6 novembre 2026. Ce sont des **releves de F1DMG**, pas des mesures effectuees sur nos exemplaires D578 PRO GD32 V1.21 et PLUS. Les observations figurent ici pour eviter leur disparition et orienter une reproduction sous controle.

## Parametres radio et CPS

| Point dans la source | Description attribuee a F1DMG | Portee pour OpenD578 |
| --- | --- | --- |
| Correction de frequence DMR | Il rapporte un decalage de l'ordre de **+330 a +340 Hz** dans son installation hotspot Raspberry Pi/MMDVM avec un D578UV PRO et mentionne un menu `MENU > SETTING > CHAN SET > OFFSET D578` par pas utilisateur de 10 Hz | Exemple d'installation, ni erreur garantie de nos oscillateurs ni regle de correction Doppler |
| Scan programme | Limites basse/haute a definir et choix `Programme scan` sur D578, distinct du scan normal | Expliquer l'ergonomie OEM, pas de nouvelles trames SPI |
| Arret du scan sur canal actif | Appui long sur `MENU` pendant l'activite; une autre astuce utilise `MENU` puis `#` pour eviter le retour au canal initial apres PTT, selon le mode de scan | Comportements de F1DMG, a caracteriser par version et mode |
| Squelch analogique | Affecter une touche `MONITOR`, puis utiliser une touche du microphone pour maintenir l'ouverture; F1DMG decrit plusieurs sequences pour la desactiver | Cas de test de l'UI, distinct des registres de squelch dans la RF |
| SMS et APRS | F1DMG indique des problemes de SMS lorsque l'option `APRS Receive` est active sur le canal | Observation historique, eviter une regle generale sans mesure |
| Chemin APRS | Consigne de supprimer une virgule entre les deux champs `WIDE` selon sa configuration | Exemple de saisie utilisateur, ne pas appliquer par defaut dans un firmware alternatif |
| 1750 Hz / DTMF | References de declenchement automatique du 1750 Hz et documents de commande DTMF pour l'ATV | Ajouter les cas d'usage audio, pas de preuve de minuterie GPIO |
| Mise a jour du codeplug | Ne pas melanger les versions D878 v1/v2 et D578 PRO/PLUS; exporter/ressaisir les objets lors des changements CPS | Important pour les migrations entre structures NAND |

Les rapports de pannes firmware tres anciennes (redemarrage, heure/date, DTMF C/D, instabilites V1.12/V1.17, etc.) peuvent viser plusieurs radios de generations differentes sur la meme page. **Aucun de ces exemples ne doit etre attribue automatiquement au D578 PRO GD32 V1.21.** Conserver le contexte de la page avant d'ajouter un ticket de regression.

## Modifications physiques illustrees par les photographies d'origine

Les images suivantes sont presentes dans l'archive utilisateur et sont identifiables visuellement. Ne pas les publier sans accord de l'auteur.

- **`578a.jpg`**: photo d'un deflecteur de ventilation ajoute a l'arriere du mobile. **`578b.jpg`**: vue de la grille et du ventilateur du poste. F1DMG indique avoir inverse le sens de son ventilateur et utilise l'option `FAN OPEN = BOTH`; il rapporte un passage de 50 degres C a 30 degres C en quatre minutes dans *sa* configuration. Ce n'est pas une mesure thermique de reference et ne garantit pas la securite d'une inversion de flux sur d'autres installations.
- **`page-20/01Mb.jpg`, `02Mb.jpg`, `03Mb.jpg`**: modification d'un microphone externe avec composant electret, ajout de cablage, interrupteur et connecteur jack. Cette realisation est distincte du protocole USART0 du microphone constructeur et du microphone Bluetooth BT01.
- **`D578-PROTECTION-ROS.png`**: photographie d'une **zone de circuit imprime avec points de soudure/modification**, presentee par F1DMG au titre de la protection ROS. La seule image ne permet pas de valider le schema complet de cette protection, ses seuils ou son action sur l'emetteur.
- **`page-20/boutons3.jpg`**: photographie de modification de la presentation des boutons de facade; utile pour l'ergonomie, sans etablir un nouveau brochage.
- **`RAZ-ANYTONE.png`**: dessin d'un raccordement de reset vers le GD32. L'image comprend une mention **« je n'ai pas essaye »** : il s'agit d'une hypothese de modification, **pas d'une procedure validee**. La liaison SWD/NRST du poste doit rester definie par les observations materielles propres a notre revision.
- **`DEBRID_578.jpg`**: illustration d'options de logiciel, pas une preuve que les filtres et l'etage de puissance couvrent les frequences selectionnees.

Les chemins sont ceux de la collection privee `f1dmg/originals/f1dmg.free.fr/` sous la racine du ZIP. Les valeurs et modifications de F1DMG sont conservees pour analyse historique et comparaison, **sans recommander une intervention sur un appareil sous tension ou en emission**.

## Suites documentaires

1. Ajouter dans les tests UI du simulateur les cas `scan`/`MENU`/PTT/`MONITOR`, **sans affirmer que les cas sont deja rejoues**.
2. Comparer, dans les versions ayant la fonction, le champ d'offset accessible par CPS, l'offset FM/DMR et la correction Doppler du projet satellite. Ces trois termes ne sont pas equivalents.
3. Documenter le capteur thermique, la commande ventilateur et la protection ROS a partir des routines OEM V1.21; les photos F1DMG ne doivent pas etre substituees aux GPIO decodes.
4. Traiter SMS, APRS, roaming et 1750 Hz comme services firmware distincts du protocole USB CPS et du bus SCT3258.

Sources: <http://f1dmg.free.fr/page-20.htm> et <http://f1dmg.free.fr/page-22.htm>, captures originales datées du 6 novembre 2026 dans l'archive privee. Se reporter au [bilan d'integrite](BILAN_ARCHIVE_ET_INTEGRITE.md) et a [l'inventaire des ecarts](ECARTS_AVEC_DEPOT.md).
