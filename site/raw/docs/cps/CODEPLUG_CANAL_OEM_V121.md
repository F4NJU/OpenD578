# Codeplug OEM V1.21 : champs de canal et organisation NAND

## 1. Vue de la zone étudiée

Le mini-CPS du banc V11.6 lit les 128 premières entrées analogiques/digitales de l'image constructeur à l'adresse logique `0x00800000`, structurées en enregistrements de **64 octets**. Il ne prétend pas représenter le codeplug complet : le constructeur possède d'autres tables de canaux, zones, contacts, réglages, étalonnages et copies de secours.

```text
0x00800000  Page logique 0 : 32 x 64 octets = 2048 octets
0x00800800  Page logique 1 : 32 x 64 octets
0x00801000  Page logique 2 : 32 x 64 octets
0x00801800  Page logique 3 : 32 x 64 octets
0x00802000  Au-delà des 128 premiers canaux : non édité par ce module
```

Les pages de 2048 octets correspondent aux 128 transferts de 16 octets lors de la réécriture d'un groupe, et à la géométrie NAND principale relevée ; le rapport de V11.5 mentionne notamment une page physique `4160` après traduction de la première adresse logique. **Ne pas transformer l'adresse logique CPS en numéro de page physique par une formule constante non vérifiée** : le firmware peut utiliser des métadonnées, blocs alternatifs, copies ou une couche de translation.

## 2. Champs identifiés dans l'enregistrement de 64 octets

| Offset (hex) | Taille | Fonction observée dans le décodeur V11.6 | Niveau de preuve |
| --- | ---: | --- | --- |
| `0x00..0x03` | 4 octets | Fréquence RX, codage BCD | Implémentation testée dans le mini-CPS |
| `0x04..0x07` | 4 octets | Décalage RX->TX en BCD | Implémentation testée |
| `0x08` bits `7:6` | 2 bits | sens : 0 simplex, 1 positif, 2 négatif, 3 refusé | Implémentation testée |
| `0x08` bits `1:0` | 2 bits | indicateur de mode brut | Champ décodé, interprétation exacte à corroborer |
| `0x08` bits `3:2` | 2 bits | indicateur de puissance brut | Champ décodé, pas une mesure RF |
| `0x23..0x32` | 16 octets | Nom affiché du canal, ASCII 1-16 caractères, terminé par NUL si plus court | Écriture de nom et persistance testées |
| Tous les autres | Variable | Paramètres de canal non décodés dans le mini-CPS | Inconnus **dans cet outil** ; ne pas les remplacer |

L'éditeur ne change que les seize positions du champ nom. Il conserve tous les octets voisins, même lorsqu'ils paraissent vides.

## 3. Fréquences : exemple du test source

Le test du mini-CPS encode la fréquence RX à l'aide des octets `14 55 00 00`. La conversion BCD du code retourne `145500000` Hz, soit 145,500 MHz. Le décalage `00 00 06 00` correspond à 600000 Hz, et le sens positif produit `146100000` Hz. Ces valeurs vérifient le code du décodeur, pas l'intégralité de la plage de fréquences du D578.

Fonction présente dans le code source : `bcd(bytes)` multiplie l'entier BCD reconstitué par 10 pour obtenir les hertz. Des nibbles supérieurs à `9` sont rejetés.

**Ne pas attribuer une signification aux bits réservés** sur la seule base d'un exemple. Pour connaître les CTCSS/DCS RX/TX, l'inversion, la bande, les flags, le scan et la puissance nominale, comparer un vrai export CPS à une modification contrôlée champ par champ, puis mesurer le comportement matériel.

## 4. Relation avec la cartographie externe publiée

VK7ZJA décrit une mémoire NAND Toshiba/KIOXIA de **2 Gbit / 256 Mio** dans le D578 et une cartographie indicative :

| Plage publiée (adresses NAND logiques) | Rôle rapporté | Utilisation dans OpenD578 |
| --- | --- | --- |
| `0x00800000..0x02A9FFFF` | Données de codeplug hors DMR IDs | **Zone à sauvegarder**, écriture limitée aux records compris |
| `0x02F00000..0x02F80679` | Alignement RF actif et sauvegardes | **Zone protégée**, ne jamais effacer pendant l'édition de canaux |
| `0x02FA0000..0x02FDFFFF` | Informations locales du poste et copie | Lecture de 16 octets testée dans le banc |
| `0x05500000..` | Base de DMR IDs | Non validée pour l'écriture dans OpenD578 |
| `0x0C8E0000..` | Enregistrements audio DMR | Non validés |

Cette cartographie est issue d'un travail externe sur la famille 578. Les zones ont été étudiées à d'autres révisions. **Elle ne constitue pas un décodage exhaustif des adresses de ton dump PRO GD32 V1.21.** Voir [NAND et ECC](../03_NAND_LECTURES_ECC_CARTE.md) et [source VK7ZJA](https://www.theweeks.org/tmp/FILES/Anytone-Mods/578mods.htm).

## 5. Conséquences pour le firmware alternatif

Le chemin le plus sûr consiste à : sauvegarder des images de référence et leurs empreintes ; identifier les records et leur numérotation ; séparer le codeplug des étalonnages ; conserver les octets inconnus ; traiter les écritures par page avec vérification et politique d'interruption ; reconstruire seulement les index compris ; tester lecture/écriture/relecture après redémarrage sur **banc** avant toute mise en service.

Pour le mode satellite, le nom `SAT:` peut être utilisé comme convention dans le codeplug, mais l'adresse `+0x23` **ne démontre pas** que le nom réside à la même position dans l'objet RAM utilisé par le firmware OEM. Cette séparation est déjà consignée dans [le portage satellite](../05_SATELLITE_CODE_INTEGRATION_EXP06.md).

## 6. Ce qui manque

- Bitmap des canaux actifs et relation des index de zones et groupes de balayage.
- Encodage complet du CTCSS/DCS analogique, fréquence TX, options PTT, bandwidth, compander, scrambler, etc.
- Formes exactes des canaux de banque 2 et offsets au-delà du premier groupe.
- Transactions de mise à jour des copies, ECC et état en cas d'extinction durant `END`.
- Différences PRO V1.20/V1.21 et PLUS V2.07/V2.08.

**Sources** : `bench/web/mini_cps_protocol.js`, `bench/web/test_mini_cps.cjs`, `docs/CPS_INTEGRE_V11_6.md`, `docs/validation_v11_6.json`, [qdmr anytone_codeplug](https://github.com/hmatuschek/qdmr/blob/master/lib/anytone_codeplug.cc), [dmr-tools/codeplugs](https://github.com/dmr-tools/codeplugs/tree/master/d578uv).
