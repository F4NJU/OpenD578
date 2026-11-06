# Guy F1DMG : photographies, modifications et documentation AnyTone

## Autorisation et crédits

**Jean-Philippe (F4EGM)** a obtenu de Guy **F1DMG**, par téléphone le **6 novembre 2026**, l'autorisation de reprendre ses travaux et ses photographies dans OpenD578.

Merci à Guy pour son accueil chaleureux, sa gentillesse et sa disponibilité. Au téléphone, il a partagé avec plaisir ses expériences et ses idées. Son envie d'échanger, d'expliquer ses montages et d'aider les autres représente bien l'esprit radioamateur. Cette rubrique cherche à respecter son travail, avec ses photos au bon endroit et ses explications conservées. **73 de Jean-Philippe, F4EGM.**

Le contenu réutilisé reste attribué à son auteur. **La licence GPL-3.0 du code source OpenD578 ne s'étend pas automatiquement aux photographies et documents de Guy.** Une image hébergée sur son site peut, dans certains cas, provenir d'un autre auteur : l'archive conserve les URLs et le crédit d'origine pour permettre cette vérification. Les documents de Jason VK7ZJA et les reproductions du site DB1IG restent dans leurs rubriques distinctes, sans réutilisation de leurs images au titre de cette seule autorisation.

Le [dossier F1DMG illustré](https://telectroboy.github.io/OpenD578/f1dmg.html) présente chaque modification **avec ses photographies dans la même section** et les deux pages sources intégrales avec les images replacées au fil du texte. L'[index photographique](https://telectroboy.github.io/OpenD578/f1dmg/galerie.html) est une aide secondaire pour retrouver les noms, sources et empreintes.

Les encadrés « Pour OpenD578 » indiquent ce que nous pouvons reprendre pour notre projet, ou ce qui ne s’y applique pas. Les textes originaux de Guy restent séparés visuellement sous l'en-tête « Archives F1DMG », avec photos dans l'ordre de sa publication.

## Pages historiques conservées

- `http://f1dmg.free.fr/page-20.htm` : textes et images D578/D878, réglages, maintenance, microphone, refroidissement, configurations et aides CPS.
- `http://f1dmg.free.fr/page-22.htm` : évolution PRO/PLUS, BT01, mises à jour et textes d'accompagnement.
- `D578a` (et l’ancienne référence `/578a` dans certains documents) : **ancienne adresse non fonctionnelle** du site de Guy, mentionnée dans le contexte du déflecteur de ventilation. Elle reste dans l'historique, pas comme un lien actif à consulter.

Ces pages ont été sauvegardées le 6 novembre 2026 dans l'archive originale `20261106T102717Z.zip`. La republication du contenu est produite par un script local, sans nouveau téléchargement ni dépendance à la disponibilité du site d'origine. Les anciennes URLs restent visibles à titre de provenance.

## Photographies identifiées

| Fichier original | Sujet | Portée technique |
| --- | --- | --- |
| `578a.jpg`, `578b.jpg` | Déflecteur ajouté, ventilateur et grille de ventilation | Modification sur un exemplaire ; ne détermine pas un régime thermique normalisé |
| `page-20/01Mb.jpg`, `02Mb.jpg`, `03Mb.jpg` | Microphone modifié, câblage et prise | Montage individuel, distinct du microphone constructeur UART et du BT01 |
| `D578-PROTECTION-ROS.png` | Partie de la carte et points de soudure | Repérage visuel de la carte ; seuils à mesurer sur notre poste |
| `page-20/boutons3.jpg` | Modification de boutons de façade | Ergonomie et pièces mécaniques ; le GPIO est relevé séparément |
| `RAZ-ANYTONE.png` | Proposition de raccordement RESET | Dessin explicitement marqué non essayé, ne pas présenter comme modification validée |
| `DEBRID_578.jpg` | Options logicielles de bande | Capture d'écran, non une démonstration des performances RF hors bande |
| `ROAMING.png` | Réglages d'interface CPS | Exemple daté et dépendant de la version |

La galerie générée ajoute **tous les autres noms effectivement présents** dans les deux pages, avec catégories, provenance, empreintes SHA-256 et liens vers l'image. Elle ne se limite pas à la sélection du tableau.

## Observations pratiques à conserver dans les tests

### Ventilateur et contrôle thermique

F1DMG rapporte une inversion du sens de circulation d'air et l'utilisation du réglage `FAN OPEN = BOTH`. Il décrit, pour sa configuration, une diminution de **50 °C à 30 °C en quatre minutes**. Il s'agit d'une observation de son poste, sans protocole de mesure reproductible décrit. Ce résultat ne doit pas être attribué au D578 PRO GD32 V1.21 du projet sans essais complémentaires.

### Correction de fréquence DMR

Dans une installation D578UV PRO avec hotspot Raspberry Pi/MMDVM, Guy a observé un décalage d'environ **+330 à +340 Hz**. Le menu cité est `MENU > SETTING > CHAN SET > OFFSET D578` avec un pas de 10 Hz. Cette correction utilisateur et le calcul de Doppler du futur mode satellite sont deux fonctions différentes : ne pas les confondre dans le modèle RF.

### Scan, surveillance et touches

Les notes traitent du scan programmé, d'un maintien de l'activité par un appui sur `MENU`, de certains effets de `MENU` puis `#`, et de l'usage de la fonction `MONITOR`. Ces comportements dépendent du mode de scan et de la version du logiciel. Ils constituent des scénarios à ajouter au banc de test, **pas** des tests déjà validés dans le simulateur.

### GPS Roaming, SMS et APRS

Le document `CMD-Roaming.doc` fournit une configuration d'exemple avec `GPS ON`, `GPS Roaming ON`, `Auto Roaming ON`, `Fixed Time Set 2`, `Repeater Check ON`, `Intervals Set 50`, `Reconnections 2`, `Outrange KIND`, `Effect Wait 2`. Guy décrit aussi un effet possible sur le double affichage VFO A/B. Les unités et les offsets NAND internes ne sont pas établis par cette notice.

Ses pages évoquent également des interactions entre `APRS Receive` et certains SMS, ainsi que la saisie des champs `WIDE`. Il faut conserver le contexte de version et de réseau, et ne pas en faire des règles universelles pour le PRO/PLUS.

### Documents techniques de Guy

Les ressources citées dans l'archive du 6 novembre incluent : `D578-REGLAGES.doc` (combinaisons de démarrage), `MISE_A_JOUR_D578.doc` (ordre des étapes CPS/firmware/réimport), `Mises_a_jour_pour_BT01.pdf`, `CMD-Roaming.doc`, `Cmd-SMS-Anytone-2c.pdf`, `SMS-d878.pdf` et `TouchesD578.pdf`. La mise à jour des ressources (SCT3258, ET12, icônes, CPS, codeplug) dépend des versions exactes de poste et de logiciel.

Seuls les fichiers documentaires réellement présents dans le ZIP et **liés par les deux pages AnyTone** sont publiés automatiquement. Les exécutables, firmwares constructeur, codeplugs `.rdt`, fichiers de calibration, CSV de contacts, archives RAR/ZIP et clés éventuelles restent exclus.

## Méthode de reproduction et contrôle d'intégrité

Le script `tools/publish_f1dmg.py` :

1. ouvre le ZIP utilisateur **sans l'extraire aveuglément**, sélectionne uniquement les pages AnyTone et leurs illustrations hébergées sur le domaine F1DMG ;
2. vérifie le SHA-256 de tout objet qui possède une empreinte dans le manifeste de collecte ;
3. filtre les HTML pour supprimer scripts, formulaires, iframes, attributs d'événement et chargements tiers ;
4. écrit les images à noms fondés sur SHA-256 dans `site-assets/f1dmg/photos/`, et le catalogue dans `publication.json` ;
5. laisse `tools/build_site.py` copier ces fichiers vers `site/f1dmg/` à chaque publication GitHub Pages.

Un rapport conserve la liste des images mentionnées mais absentes de la sauvegarde. L'option `--include-all-f1dmg-images` permet une extension volontaire à **toutes les images F1DMG présentes dans le ZIP**, même hors des rubriques AnyTone ; ce mode nécessite une revue de périmètre et de droits avant publication.

## Documentation déjà présente dans OpenD578

- [Analyse initiale des pages F1DMG](../archives_20261106/F1DMG_APPORTS_REELS.md).
- [Observations pratiques et photos](../archives_20261106/F1DMG_RELEVES_PRATIQUES.md).
- [Table des écarts avec nos analyses firmware](../archives_20261106/ECARTS_AVEC_DEPOT.md).
- [Modes TEST et architecture de démarrage](../../02_CPU_FLASH_BOOT_USB_SWD.md).
- [Documentation microphone](../../NOTICE_CHANGELOG_MICROPHONE_V11_8.md).
- [Pilotage de la façade](../../FACADE_GPIO_BOUTONS_CODEUR_VOLUMES_ET_ECLAIRAGES.md).

Les pages historiques restent attribuées à Guy. Pour les correspondances GPIO, nous utilisons les relevés matériels et l’analyse du firmware de notre poste.
