# N13 — comparaison des IO PRO V1.21 / PLUS V2.08

Jean-Philippe (F4EGM) — 9 novembre 2026 — complément de la révision 4 du tableau IO.

## Résultat

Le firmware PLUS confirme les commandes GPIO déjà retrouvées, dont PB9 PWM audio. Il ne donne pas une nouvelle destination à PC3 ou PE15 : leurs séquences restent communes. Le manque principal retrouvé dans la cartographie est **un deuxième correspondant radio sur le bus PB6/PB7 : un tuner AM/FM à l’adresse I²C 7 bits 0x35, avec pilote compatible KT0937-D8**. Il est distinct du chemin RDA à 0x10. Les deux pilotes existent dans les deux applications ; cela ne signifie pas que les deux composants sont montés sur chaque radio.

Le tableau conserve la règle du projet : une liaison établie par instructions OEM est validée sans nouvelle exigence de continuité. Une commande connue mais dont le circuit destinataire n’est pas identifié ne reçoit pas un nom arbitraire.

## Images comparées et portée

| Image | Taille | SHA-256 |
| --- | ---: | --- |
| PRO GD32 V1.21, application | 1 020 300 octets | `02b2a3b56bd57c7ada581eb52b9b6f41c5d51aaec1b068d37585efd58dff9c9a` |
| PLUS GD32 V2.08, `D578UV2_GD_V2.08_20240619.CDD` | 1 020 408 octets | `8efad950169f332c8c60d340722a2ceee84ce41d7d8fabb0ebf19482973ceca2` |

L’image PLUS correspond au fichier référencé dans `firmwares/PROVENANCE.json` du projet, archive Powerwerx V2.08 collectée le 4 novembre 2026. Son texte de version contient `GD_Ver 2.08` et son libellé de menu inclut `FM/AM Radio`. Les deux images sont des applications chargées à `0x08006000` ; leurs octets ne sont pas identiques. **Le CDD PLUS ne contient pas son bootloader.** Les observations antérieures sur le bootloader PRO ne deviennent donc pas des observations du bootloader PLUS.

Il s’agit d’une comparaison statique ciblée complétée par des routines isolées exécutées, pas d’un démarrage complet PLUS avec une NAND PLUS. Aucun firmware interne SCT/Bluetooth n’est exécuté ici. Les fichiers firmware/NAND ne sont pas ajoutés à cette archive documentaire.

## Index GPIO : ce qui est réellement comparé

Les primitives GPIO de bibliothèque sont retrouvées aux mêmes adresses dans les deux applications : initialisation `0x08008670`, lecture d’entrée `0x08008796`, lecture de port `0x080087A8`, mise à 1 `0x080087CA`, mise à 0 `0x080087CE`, écriture conditionnelle `0x080087D2` et écriture de port `0x080087DC`.

**570 sites d’appels directs** vers les primitives considérées sont indexés dans chaque application. Leur ordre présente **zéro différence de signature** pour : type de primitive, port, masque et mode de configuration quand applicable. Les structures passées sur la pile sont résolues ; c’est ce qui permet de voir l’usage PWM de PB9, manqué par le tout premier index.

Ce ne sont pas 570 transactions observées au démarrage : l’index est statique et ne prouve pas que tous les chemins ont été exécutés. Les configurations génériques de ports entiers ne prouvent pas l’usage de chaque patte. Les lectures/écritures directes MMIO, appels indirects, accès DMA et fonctions alternatives doivent aussi être considérés. Le CSV comparatif signale ces limites.

## Correspondances importantes

| Fonction | PRO V1.21 | PLUS V2.08 | Conclusion |
| --- | --- | --- | --- |
| PC3 : configuration puis niveau haut | `0x0808A1A8` | `0x0808A1FC` | Séquence commune ; destination non résolue |
| PE15 : niveau bas après délai de démarrage | `0x080066D2` | `0x080066D2` | Même instruction d’appel et même masque |
| PE15 : niveau haut dans init | `0x0808A2B8` | `0x0808A30C` | Séquence commune |
| PE15 : niveau bas dans chemin de veille | `0x08089F6A` | `0x08089FBE` | Même condition et même commande |
| PB9 : mode analogique / neutralisation | `0x0808C796` | `0x0808C7EA` | Même mode |
| PB9 : fonction alternative PWM | `0x0808C7B6` | `0x0808C80A` | Même mode AF push-pull |
| Échantillon PWM TIMER3_CH3CV | `0x0808C834` | `0x0808C888` | Écriture 16 bits à `0x40000840` dans les deux |
| Initialisation série BH2226 | `0x0808A8A0` | `0x0808A8F4` | Même séquence complète de dix mots |
| PE2 : connexion USB | `0x0809B396` | `0x0809B3F2` | Même commande booléenne |
| PC4 : commande RF auxiliaire | `0x0808A2C4` | `0x0808A318` | Même commande, même limite d’interprétation |
| PD1 : requête SCT | `0x0809364C` | `0x080936A6` | Même commande booléenne |
| PC7 : commande SCT | `0x08093666` | `0x080936C4` | Même commande booléenne |
| PD7 : requête SCT | `0x08093A5E` | `0x08093ABC` | Même commande booléenne |
| Démarrage / reset SCT | `0x0809306C` | `0x080930C4` | Même suite PA8/PC6/PC7/PC12/PD1/PD6/PD7 |

Les décalages d’adresses ne sont pas constants dans toute l’image : plusieurs valent +0x54, d’autres +0x58/+0x5A/+0x5C/+0x5E. La correspondance a été recherchée dans les instructions ; il ne faut pas convertir une adresse PRO en PLUS avec un offset unique.

## Pilote AM/FM manquant sur PB6/PB7

### Deux chemins I²C distincts

| Chemin | Adresse esclave 7 bits | Octets adresse sur le fil | PRO | PLUS |
| --- | --- | --- | --- | --- |
| Registres AM/FM compatibles KT | `0x35` | `0x6A` écriture, `0x6B` lecture | Lecture registre `0x0808895A`, écriture registre `0x080889E4` | Lecture `0x080889AE`, écriture `0x08088A38` |
| Tuner RDA, transferts séquentiels | `0x10` | `0x20` écriture, `0x21` lecture | Transfert TX `0x0808D55A`, RX `0x0808D4E2` | TX `0x0808D5AE`, RX `0x0808D536` |

Les deux chemins commandent SDA sur PB6 et SCL sur PB7. Le premier transfère une adresse de registre 8 bits et une valeur 8 bits ; la lecture utilise un redémarrage répété. Le second transfère un tampon séquentiel. L’ancien tableau réduisant PB6/PB7 au seul RDA est donc incomplet et a été corrigé.

### Identification fonctionnelle par le code

L’OEM lit les registres `0x02` et `0x03`, les assemble en un mot, puis compare à **`0x4B54`** :

- PRO : lectures à `0x08088DC4…0x08088DD6`, comparaison à `0x08088DDC`.
- PLUS : lectures à `0x08088E18…0x08088E2A`, comparaison à `0x08088E30`.

En cas de reconnaissance, le code appelle les lectures de configuration et l’initialisation du correspondant. Les routines du chemin RDA consultent aussi l’état de sélection de ce pilote ; les chemins ne sont pas tous exécutés indifféremment.

Le rapprochement avec KT0937-D8 repose sur plusieurs éléments concordants : protocole à adresse 0x35, registres 8 bits, configuration d’horloge par `0x04…0x0A`, activation de configuration par `0x04` bit 7, attente de `0x1B` bit 2, volume par `0x0F` et séquences de réglage AM/FM. Le firmware contient aussi des lectures de qualité de réception et des réglages de fréquence pour ce chemin. Il ne s’agit donc plus d’une supposition fondée sur la proximité du RDA.

**Attribution retenue :** liaison de commande PB6/PB7 vers le tuner AM/FM compatible KT0937-D8. La lecture de marquage antérieure `KT0905R/KT09S5R` reste distincte de cette identification fonctionnelle ; la référence commerciale exacte n’est pas changée arbitrairement. Le pilote compilé dans le PRO ne prouve pas la présence du composant sur la carte PRO sauvegardée. Il ne prouve pas non plus, à lui seul, tous les étages analogiques de la réception airband du PLUS.

Source primaire recoupée : [KT Micro, KT0937-D8 Programming Guide V2.1, 22 juin 2017](https://maximradio.altervista.org/datasheets/KT0937-D8_Programming%20Guide_V2.1.pdf), sections initialisation, horloge, interface I²C et volume. Les fonctions disponibles du GD32 ne sont pas utilisées seules pour attribuer une liaison.

## Ce qui manque encore au banc Web pour cette partie PLUS

Le décodeur `FmI2c` actuellement conservé dans les sources n’acquitte que l’adresse 0x10. Les autres adresses sont enregistrées comme absentes. Il ne représente donc pas le correspondant 0x35 ni ses registres, son initialisation, son volume, ses états ou sa sélection de mode.

La suite concrète pour représenter cette partie est un modèle du tuner à 0x35, fondé sur ses registres et transitions, raccordé au même bus PB6/PB7. Le choix des composants montés doit appartenir au profil matériel PRO/PLUS. Le firmware conserve ses propres sondages et décisions. Cette étape documentaire n’a pas modifié le banc ni publié un nouveau site ; elle ne revendique pas une réception AM ou APRS RX entièrement émulée.

## Inconnues qui restent après comparaison

- **PC3** : mise à 1 commune aux deux applications ; commande d’alimentation/enable/maintien possible, destination unique non déduite.
- **PE15** : mêmes changements dans init et veille ; commande d’alimentation/veille possible, destination unique non déduite.
- **PC4 et commandes auxiliaires SCT** : séquences communes et confirmées ; la version PLUS n’apporte pas de nom terminal ou d’action interne supplémentaire qui fermerait les interprétations partielles.
- **Sorties analogiques du BH2226, filtres/mixeurs audio et référence exacte du tuner KT** : la comparaison GPIO ne donne pas tous les raccordements internes.
- **APRS RX, complément N14** : la carte BT+APRS BHT_BOARD transmet les trames +APRS: sur PC11/UART3_RX ; PC10 est le TX partagé. Les routines réceptrices existent aussi dans PRO. Le raccordement RF/audio en amont de BHT reste non attribué. Lire APRS_RX_PLUS.md.
- **Bootloader PLUS** : absent du fichier application examiné.

## Vérifications et fichiers

**18 cas appariés, soit 36 exécutions de routines OEM isolées**, donnent les mêmes écritures MMIO PRO/PLUS : cinq wrappers booléens avec 0/1, init PC3, modes analogique/AF de PB9, quatre valeurs de comparaison PWM et séquence complète du BH2226. Zéro écart. Les tests ne fabriquent pas une réponse d’identité du tuner KT et ne prétendent pas démarrer le PLUS.

`comparaison_plus/` contient le désassemblage annoté des deux versions, l’index des 570 appels, le résultat des essais et les scripts. `COMPARAISON_IO_PRO_PLUS.csv` reprend les 86 signaux du tableau avec les références PLUS, en distinguant les configurations de ports entiers des commandes propres à une broche. L’absence d’appel GPIO direct n’y est pas interprétée comme absence d’utilisation.
