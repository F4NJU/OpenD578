# 01 - NAND serie TC58CVG1S3HRAIG : bus, lecture, ECC et cartographie

> **RECONSTITUTION du 05/11/2026.** Le document historique portant ce nom n'a pas ete retrouve octet pour octet. Celui-ci a ete recompose a partir de `docs/03_NAND_LECTURES_ECC_CARTE.md`, des sources de banc, des empreintes de captures et des specifications externes. Il ne faut pas le presenter comme l'original ancien.

## 1. Identification du composant et perimetre des preuves

- NAND : **TC58CVG1S3HRAIG** Toshiba/KIOXIA ; identifiant lu sur le poste **98 CB**.
- Geometrie main : **2048 blocs x 64 pages/bloc x 2048 octets/page = 268 435 456 octets (256 Mio)**.
- Nombre de pages : **131 072** ; taille d'un bloc main : **131 072 octets** ; bloc = unite usuelle d'effacement NAND.
- Lecture avec ECC interne active lors de la capture 03/11 : **64 octets auxiliaires** par page, soit 8 Mio auxiliaires et 264 Mio entrelaces. Il ne faut pas assimiler ce fichier au contenu OOB physique brut obtenu avec les options ECC differemment configurees.
- La documentation fabricant annonce un cache par page, une logique ECC et les commandes SPI NAND. La capture utilisateur prouve des reponses de lecture dans un contexte precis ; elle ne prouve ni le comportement en ecriture ni la possibilite de restaurer cette image.

## 2. Bus GPIO reconstruit (PRO GD32 V1.21)

| Fonction serie | GPIO candidat MCU | Broche LQFP100 | Origine | Etat de continute |
| --- | --- | ---: | --- | --- |
| CS# | `PB8` | 95 | Trace OEM / banc SPI | **Non mesuree** |
| SCK | `PB15` | 54 | Trace OEM / banc SPI | Non mesuree |
| SO0 / sortie DQ0 selon mode de lecture | `PB14` | 53 | Trace OEM / banc SPI | Non mesuree |
| SO1 / sortie DQ1 selon mode de lecture | `PA15` | 77 | Trace OEM / banc SPI | Non mesuree |
| VCC, WP#, HOLD# et decouplage | inconnus | - | Composant et PCB non traces | A mesurer |

**Attention :** le firmware GD32 bit-bang les GPIO ; il n'est pas prouve que les memes pins puissent etre utilises via le SPI materiel en AF. PB14/PB15 ne correspondent pas aux roles SPI1 MOSI/MISO habituels dans ce mapping : tenir compte de l'ordre reels des bits sur GPIO. `PA15` peut etre multiplexee JTAG, d'ou la necessite d'initialiser le mode GPIO conforme au schema. La commande `0x3B` represente une lecture **dual output** et demande de reconstruire des bits venant de SO0 et SO1 sur les fronts de l'horloge.

Source de simulation lisible : `bench/verify_spi_wire.py`, `bench/emulate_nand_v121.py`, `bench/nand_state.py`, `bench/nand_overlay.py`. Ces fichiers reproduisent une interface a partir de traces et ne prouvent pas seuls le timing electrique.

## 3. Operations identifiees et nature de la preuve

| Code | Operation serie NAND | Vue dans acquisition | Vue en logiciel OEM / datasheet | Risque |
| --- | --- | --- | --- | --- |
| `0x9F` | Read ID | Oui | Oui | Lecture |
| `0x0F` | Get Feature | Oui | Oui | Lecture et interpretation ECC |
| `0x13` | Page Read -> cache | Oui | Oui | Lecture |
| `0x03` | Read from Cache, sortie simple | Oui | Oui | Lecture |
| `0x3B` | Read from Cache, dual output | Non dans les commandes de la capture utilisateur ; trace/simulation OEM | Oui | Lecture, attention mode de bus |
| `0x06` | Write Enable | **Non** | Identifie en analyse statique OEM | Modifie latch d'ecriture |
| `0x02` | Program Load | **Non** | Oui, datasheet et code OEM | Ecriture tampon |
| `0x10` | Program Execute | **Non** | Oui, datasheet et code OEM | Ecriture irreversible de page |
| `0xD8` | Block Erase | **Non** | Oui, datasheet et code OEM | Destructeur |
| `0x1F` | Set Feature | **Non** | Datasheet | Change comportement du peripherique |

Le logiciel de lecture doit **forcer un jeu blanc de commandes autorisees** (`9F/0F/13/03`, et `3B` si decode correct) pour l'acquisition non destructive. La simple presence de la commande `0x10` dans le desassemblage ne valide pas une routine d'ecriture OpenD578.

## 4. Sequencement de lecture, cote driver alternatif

1. Alimenter correctement la NAND et mettre les GPIO dans un mode inoffensif avant d'abaisser CS# ; respecter le niveau d'alimentation exact de la carte.
2. Lire l'identifiant avec `0x9F`, confirmer le manufacturer/device attendu, refuser tout driver si la geometrie ne correspond pas.
3. Lire les registres `GET_FEATURE` et conserver leur valeur brute et le mode ECC avant acquisition.
4. Pour une page logique `p` dans `[0, 131071]`, demander `PAGE_READ 0x13` avec l'adresse de ligne conforme a la datasheet.
5. Attendre fin d'operation par statut, avec timeout calibre par mesures et une condition d'erreur explicite. Ne pas appliquer de boucle temporelle non calibree issue du firmware OEM.
6. Demander `READ_CACHE 0x03` ou `0x3B`, separer adresses de colonnes, dummy bytes et flux de donnees. En dual output, assembler SO0/SO1 sans inverser l'ordre des bits.
7. Acquerir le statut ECC apres la page, l'enregistrer dans une table de **131 072 octets** ; garder le nombre de pages affectees par classe.
8. Sauvegarder main et auxiliaires dans des fichiers distincts avec offsets, horodatage, statut ECC et SHA256 ; ne jamais appeler cette sauvegarde restaurable sans qualification des ECC20.

### Calcul des offsets

Pour un fichier `main` continu, `offset_main = numero_page * 2048`, `block = numero_page // 64`, `page_in_block = numero_page % 64`. Pour l'image de cette capture, `offset_aux = numero_page * 64` et `offset_interleave = numero_page * 2112`. Ce sont des offsets **de fichier** et **pas des adresses ARM** ; ne pas les soustraire de `0x08000000`.

## 5. Resultats de la capture du 03 novembre 2026

| Fichier absent de l'archive publique | Taille exacte | SHA-256 publie dans le rapport |
| --- | ---: | --- |
| `nand_main_256MiB.bin` | 268 435 456 | `329d22165d234bf0df043e62af11397dea96327925b9db18f3c354230ff40945` |
| `nand_oob64_8MiB.bin` | 8 388 608 | `9a999b9fd13a02b45ed4d38e68f9e9c7d1095994c751e36e04f4a62b2e4c5106` |
| `nand_ecc_status_128KiB.bin` | 131 072 | `b40ebd3ebc3923f01d9d98a52a3b019b65785641ba76687127678b788ea793c6` |
| `nand_2112_interleaved_264MiB.bin` | 276 824 064 | `568b6395f88e8ef1b27d16fc9c25aa5d94f8bcf5d47556910466baaeeefde1c9` |

Statuts ECC mesures : **130 610** pages statut `00`, **25** statut `10`, **437** statut `20` non corrige dans la capture, **0** statut `30`. Parmi les 437 : 192 pages entierement 00, 235 marqueurs de fin (225+10), 10 pages non triviales. **Ne pas fusionner les 437 en donnees fiables**. Pages non triviales : 8324, 14848, 14912, 17024, 18817, 18818, 20992, 24256, 24320, 24448.

La capture physique a ete conduite **sans WRITE/ERASE NAND** mais avec etat volatile SRAM/GPIO modifie durant la lecture via debug ; elle ne represente pas une capture passive sans aucune intervention.

## 6. Cartographie : observations propres au poste et comparatif externe

| Plage NAND (octets main) | Attribution | Statut |
| --- | --- | --- |
| `0x00020000`, `0x03000000` (blocs 1,384) | Glyphes monochromes chinois 16 x 16, 32 octets par glyphe | Trouves dans dump |
| `0x00800000` | 128 premiers canaux et suite du codeplug, record de 64 octets dans le CPS V11.6 | Simulation + signatures dump |
| `0x02F00000..0x02F80679` | Calibration RF et copies selon VK7ZJA | Source externe, ne pas l'egaler a une carte totale de la revision |
| `0x02FA0000..0x02FDFFFF` | Configuration radio/copies ; `D578UV` a 0x02FA0010 et 0x02FC0010 | Dump + source externe, zone critique |
| `0x02FE0000` | `CHECKING DATA FOR D578UV` | Signature dump |
| `0x05500000...` | Annuaire DMR probable | Noms/IDs du dump et cartographie historique |
| `0x0C8E0000...` | Audio enregistre selon etude VK7ZJA | Source externe ancienne, non revu sur dump projet |

Le guide externe detaille encore les fonts `0x00000000..0x0014FFFF`, bitmaps `0x00150000..0x001FFFFF`, codeplug `0x00800000..0x02A9FFFF`, images personnalisees `0x02AC0000`, `0x02B00000`, `0x02B80000`. Ces plages sont une **reference historique** a confronter a la branche GD32 V1.21 ; elles ne sont ni une table de partition formelle ni une preuve d'espace libre ailleurs.

## 7. Ecriture, ECC et transactions : travail non qualifie

- Reconstituer le contrat de synchronisation entre `PROGRAM LOAD`, `PROGRAM EXECUTE`, statut busy et invalidation des caches.
- Observer les pages programmee par le firmware au format CPS, les copies locales, la correction ECC et les secteurs de secours.
- Identifier le mapping des **bad blocks** ; une lecture logique ne suffit pas a reconstruire la remap physique.
- La valeur ACK du CPS n'atteste pas une persistance immediate ; la mise a jour peut se terminer apres `END` et apres l'ACK visible.
- Les plages `0x02F0....` de calibrage RF peuvent rendre l'emission dangereuse en cas de corruption. **Aucune routine write/erase n'est fournie comme operation approuvee**.
- Ne jamais utiliser les blocs FF observes comme allocation TLE, code ou journal avant d'avoir etabli les allocations OEM et une sauvegarde recuperable.

## 8. Sources et tests de reference

- Projet : `docs/03_NAND_LECTURES_ECC_CARTE.md`, `docs/cps/PROTOCOLE_OEM_V121.md`, `bench/emulate_nand_v121.py`, `bench/nand_state.py`, `bench/verify_spi_wire.py`, `docs/07_ERREURS_CORRECTIONS_HYPOTHESES_ET_NO_GO.md`.
- KIOXIA, datasheet TC58CVG1S3HRAIG : <https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/305/KIOXIA_TC58CVG1S3HRAIG_Rev2.0_E191001.pdf>.
- Implementation Linux pour TC58CVG1S3HRAIG ID `0xCB`, ECC 8 bits par 512 octets : <https://cos.googlesource.com/third_party/kernel/+/5aa092beb12119ed7e0b9fc696e597ca0fba9721/drivers/mtd/nand/spi/toshiba.c>.
- Specifications de commandes (source tiers) : <https://spiflash.readthedocs.io/en/latest/chips/98cb-nand.html>.
- Carte NAND et precautions historiques : <https://www.theweeks.org/tmp/FILES/Anytone-Mods/578mods.htm>.
