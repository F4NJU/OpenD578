# N14 — Réception APRS analogique du D578UV PLUS

Jean-Philippe (F4EGM) — 9 novembre 2026 — révision 5.

La réception APRS analogique utilise la **carte auxiliaire BT+APRS, firmware BHT_BOARD**. Le GD32 reçoit ses trames sur **PC11 / UART3_RX**, et communique dans l’autre sens sur **PC10 / UART3_TX**, à **115200 bit/s**. Cette liaison transporte aussi les échanges Bluetooth. Le tuner AM/FM compatible KT sur PB6/PB7 n’est pas le correspondant série identifié ici.

## Chaîne et niveau de résolution

| Liaison ou traitement | Fonction établie | État |
|---|---|---|
| Récepteur RF → entrée du sous-ensemble BT+APRS | Fournit le signal nécessaire à la réception analogique | Prélèvement, conditionnement et entrée exacte non encore attribués |
| BHT_BOARD, traitement des bits | Reconstruction, décodage NRZI, retrait du zéro inséré après cinq 1, reconstruction des octets et reconnaissance de délimiteurs | Instructions H analysées ; ne prouve pas à elle seule tout le démodulateur AFSK ni la vérification FCS |
| BHT → PC11, UART3_RX GD32 | Préfixe ASCII `+APRS:` puis octets binaires AX.25, délimités par `0x7E` | Validé par les deux firmwares, émission H exécutée isolément |
| PC10, UART3_TX GD32 → BHT | Commandes / échanges du lien partagé avec le Bluetooth | Configuration et routines UART validées ; pas d’affirmation que chaque commande AT appartient à APRS |
| GD32 → traitement APRS | Adresse AX.25 destination/source, SSID, puis contenu APRS | Parseur et consommateurs retrouvés ; début de décodage des adresses visible directement |
| GD32 → affichage | Gestion du message reçu dans le traitement APRS OEM | Chemin retrouvé ; démarrage complet et pixels LCD non validés dans ces essais |

**Aucune nouvelle entrée GPIO GD32 propre à APRS RX n’est nécessaire pour cette arrivée de données** : l’interface déjà présente pour le Bluetooth est partagée. Le tableau principal conserve 86 signaux ; les lignes PC10 et PC11 sont complétées, sans ajouter une broche imaginaire.

## Preuves dans PLUS GD32 V2.08

- `0x08077824` : initialisation UART3 et PC10/PC11 ; base UART `0x40004C00`. Les appelants passent 115200.
- `0x08077DEC` : interruption UART3 RX ; réception des octets, buffer `0x2000B0F0`, longueur `0x20000ED2`, appel du dispatch `0x0807C200`.
- `0x0807C18E` : assemblage du flux ; le contrôle du préfixe est déclenché à six octets.
- `0x0807C634` : comparaison exacte de six caractères avec `+APRS:` stocké à `0x080F50F0` ; indicateur `0x20000F79`.
- `0x0807C664` : états de réception recherchant `0x03`, puis `0xF0`, puis `0x7E`. À la fin, copie vers `0x2000CC4B`. Ces valeurs correspondent au contrôle UI, PID sans couche 3 et délimiteur AX.25 ; ce n’est pas une ligne APRS texte TNC2.
- Même routine : au moins une configuration VFO (pointeurs `0x2000070C` et `0x20000710`) doit avoir le bit 5 de l’octet `+0x21` activé ; les deux modes `+8 & 3` ne doivent pas être simultanément non nuls ; la temporisation `0x20000F7C` doit être nulle. L’indicateur de travail devient `0x20000F7A=1`.
- `0x0807F566` : consommateur de cet indicateur ; recherche du premier `0x7E`, contrôle par `0x0807D942`, décodage des deux adresses à six caractères décalés d’un bit et des SSID ; poursuite du traitement du contenu. La plage se prolonge jusqu’à la gestion de fin `0x080802EE`.

Le parseur de préfixe et la réception binaire existent **aussi dans PRO V1.21**, à `0x0807C5E0` et `0x0807C610`. Les 12 essais appariés ci-dessous passent dans les deux applications. La présence de code commun ne démontre donc ni présence de la carte BT+APRS dans le PRO, ni activation de toutes ses fonctions. Charger simplement le firmware PLUS dans un PRO n’est pas une solution démontrée.

## Preuves dans la carte BT+APRS

Le paquet constructeur distribué avec PLUS V2.08 contient deux variantes :

| Image auxiliaire | Taille | SHA-256 |
|---|---:|---|
| BHT_BOARD_H_V2.00_20230417.CDD | 12364 | a61ef5f36b2f32e0d6b564321ce962533168c2ca9135535c1c0623b4959d1c8d |
| BHT_BOARD_V2.00_M_20230923.CDD | 11316 | 038ed4128ee9b118847f3eb1f99a3083c7db0560bce5b1acfc766f4e32edc1d4 |

Les instructions constructeur distinguent ancien et nouveau silicium de carte BT+APRS : M correspond à l’ancien, H au nouveau. Elles attribuent explicitement à BHT_BOARD l’amélioration du décodage APRS analogique. La référence exacte du MCU n’est pas déduite du seul nom H/M.

Dans H, image ARM Thumb chargée à `0x2000` :

- `0x000041D0` : compare les niveaux successifs (NRZI : transition → 0, niveau inchangé → 1), compte les 1 consécutifs et élimine le zéro de bourrage ; assemble les bits dans `0x200003D2`.
- `0x000026F0…0x0000282E` : traitement des octets reconstruits et fin de trame ; appel de l’émetteur à `0x00002820`.
- `0x00003EF0` : émission des six octets de `+APRS:` (chaîne à `0x00004F4C`), puis du bloc binaire.
- `0x00004844` : émission du préfixe ; `0x00004818` : émission du bloc avec dernier octet établi à `0x7E` ; les deux appellent le pilote série `0x00004A7E` avec index UART 1.
- `0x00003B80` : débit UART 1 construit par `0xE1 << 9`, soit 115200.
- M contient également `+APRS:` à `0x00004B50`. Son traitement complet n’a pas fait l’objet des essais d’exécution H.

La capture temporisée des transitions est visible dans `0x00003C90` et la reconstruction des bits en amont. **Le code analysé ne permet pas encore de nommer avec assurance la sortie RF/audio, le comparateur ou démodulateur éventuel et l’entrée physique correspondante de BHT.** On ne substitue donc pas PC0/ADC10, le tuner KT, PE15 ou PC3 à cette inconnue. La détection de fin de trame ne constitue pas une preuve d’un contrôle CRC/FCS complet.

## Vérifications reproductibles

`aprs_rx_plus/test_oem_aprs.py`, avec Unicorn 2 et Capstone 5 :

- 5 cas par application : autorisation VFO A, autorisation VFO B, réception désactivée, deux modes non analogiques, temporisation active ; les octets sont introduits dans le buffer d’entrée du parseur natif et son état de longueur. Le firmware décide seul de la copie et de l’indicateur final.
- 1 préfixe erroné par application, rejeté par la routine OEM.
- 1 exécution de l’émetteur BHT H : les deux boucles OEM produisent `+APRS:` et le contenu binaire, avec terminaison `0x7E`. Seule la primitive d’écriture UART est interceptée pour relever les octets.

**13/13 essais réussis.** Ce sont des essais de routines isolées avec stimuli synthétiques, pas une réception RF réelle, pas un démodulateur AFSK validé, pas un démarrage intégral ni une validation des écrans. Aucun résultat LCD ou indicateur final n’est forcé.

Pour le banc fidèle, il faut raccorder la sortie du véritable modèle BHT à UART3. Injecter une trame déjà décodée sur ce port reste utile pour tester le parseur et l’IHM, mais ne valide pas la chaîne complète de réception analogique.

## Sources primaires et provenance

- [Paquet constructeur PLUS V2.08, distribué par Powerwerx](https://powerwerx.com/help/firmware-anytone-d578uvplus). Archive `Anytone-578Plus-DMR-Firmware-v2.08.zip`, SHA-256 `1351734dcedef6cb575944fa9c51239f24c9fd5232cb3ea79651d3241bcb7477`.
- [Instructions constructeur BT+APRS V2.00, copie consultable](https://device.report/m/6bee54bf562d735096cafc8e78e4faf4895d6bd8f20f6f8271337518f0da5198).
- Firmware MCU PRO/PLUS : mêmes images et empreintes que N13 / COMPARAISON_PRO_PLUS.md.
- Désassemblages annotés, script et résultats JSON joints dans `aprs_rx_plus/`. Les adresses sont des preuves pour les versions indiquées, pas une API du futur firmware libre.
