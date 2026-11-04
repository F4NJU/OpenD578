# CPU, Flash interne, boot, USB et SWD

## Identification, environnements et provenance

[MATERIEL] GD32F303VKT6 (Cortex-M4, LQFP100), Flash 3 145 728 octets, SRAM 98 304 octets (96 Kio). [EXTERNE] Le fabricant GigaDevice donne 3072 K Flash et 96 K SRAM : https://www.gigadevice.com/product/mcu/mcus-product-selector/gd32f303vkt6 . Horloge maxi nominale 120 MHz, pas une fréquence mesurée du poste pendant les simulations.

[UTILISATEUR/MATERIEL] FTDI C232HD-DDHSP-0 / FT232H, OpenOCD 0.12.0 Debian, MPSSE SWD, liaisons déclarées: SWCLK orange -> pad2 PA14; SWDIO jaune via 470 ohms et vert -> pad4 PA13; GND noir -> pad3; 3,3 V -> pad1; NRST non câblé. En mode MCU Update à LED rouge clignotante, lecture DPIDR 0x2BA01477, AHB-AP 0x24770011, Cortex-M4 r0p1. **La description de câblage n'est pas une procédure d'alimentation recommandée sans contrôle du schéma réel.** L'utilisateur précise que le bouton Power est une entrée vers le MCU, pas une coupure directe de son alimentation (notamment lorsqu'alimenté via l'USB/SWD).

[OBSERVATION USB] La branche GD32 expose `28e9:018a`, CDC ACM `GD32 Virtual ComPort`, numéro série `000000010000` rapporté; modes normal et MCU Update peuvent partager ces descripteurs, donc ne pas détecter le mode sur le seul VID:PID. Des observations de « Boot Mode for Sct » n'ont pas prouvé un bootloader de récupération indépendant. Aucune commande USB write n'a été validée.

## Images et SHA de référence (non incluses si la colonne statut le signale)

| Fichier | Longueur | SHA-256 |
|---|---:|---|
| App OEM GD V1.20, base 0x08006000 | 1 020 096 | `1cdf1817f8abbbee72901357316953aea28763e192fe35b913c82520db31453b` |
| App OEM GD V1.21 .CDD, base 0x08006000 | 1 020 300 | `02b2a3b56bd57c7ada581eb52b9b6f41c5d51aaec1b068d37585efd58dff9c9a` |
| Boot physique 24 Kio | 24 576 | `c098c74d2a979e162d6dd901c9d59d7ed3f0a4c9d526a168a1db78fba316fdeb` |
| Dump Flash physique 3 Mio, double passe | 3 145 728 | `e2f2483baf60e2bfcab656e25e949670713222591ef4d611d6089054819a750e` |
| `D578UV_Setup_1.21.exe` | 5 961 204 | `7602fe26c4733e86f4b12d1e34ab55f32dbbd58fd3b381b55ae1f5a38a82949e` |
| `QX_Firmware_Update.exe` du CPS | non reporté ici | `3303e9c7be4163f07b516a91b14e66dcd701d8101296f1a564d521cfb09fbee7` |

## Occupation Flash selon les deux dumps physiques

Les bornes sont inclusives, sur espace ARM. Une valeur `FF` est un état de lecture, pas un titre de propriété de secteur.

| Plage | Octets | Interprétation |
|---|---:|---|
| `0x08000000..0x08005FFF` | 24 576 | Boot OEM, protéger. |
| `0x08006000..0x080FF18B` | 1 020 300 | Application OEM V1.21, identique octet pour octet à CDD. |
| `0x080FF18C..0x080FF19F` | 20 | Zéros hors CDD, page occupée. |
| `0x080FF1A0..0x082F57FF` | 2 057 824 | FF sur deux captures, **non alloués au satellite**. |
| `0x082F5800..0x082FF81F` | 40 992 | Données constructeur, cache/ressources, non FF. |
| `0x082FF820..0x082FFFFF` | 2 016 | FF, dernière page affectée OEM. |

896 pages observées: 256 pages de 2 Kio et 640 pages de 4 Kio; 504 totalement FF, 392 non FF; 0 réservée au satellite. Flash haute gérée par l'OEM, possible rechargement depuis NAND; ne pas implanter une extension sur une zone candidate sans preuve de non-utilisation/consistance.

## Exécution du boot, fonctions statiques

- Boot MSP `0x20001E50`; vecteur Reset boot `0x080004D9` (bit Thumb), code `0x080004D8`; littéraux `0x08000500` et `0x08000504` vers `0x080002F9` et `0x08000131`.
- App vecteur base `0x08006000`, Reset_Handler code `0x08006D38`; VTOR positionné par la séquence `0x08006384` / STR `0x08006388`.
- Routine boot de programmation FMC candidate `0x0800436E`, filtre seulement sur adresse **initiale** `0x08000000 <= r8 < 0x08100000`; cela ne prouve pas une borne de longueur ni un droit d'écraser l'application.
- Routine constructeur haute `0x0808CE72`, transferts depuis NAND vers Flash en `0x082F5800`; sources NAND candidates `0x00200000`, `0x02B00000`, `0x02B20000`, `0x02B80000`, `0x02BA0000`.
- Chaîne `UPDATE -> buffer 32 octets -> FMC` en audit statique, sans test de restauration.

## Risque majeur

Le SWD a permis **la lecture** de deux copies de la Flash et du boot; cela ne démontre ni déverrouillage option bytes, ni possibilité de rétablir l'application en cas de panne, ni sûreté de l'outil MCU Update. Le patch Thumb expérimental de phase60 est encore pass-through. Le blob ROM `satellite_rom_ONLY_STAGE60.bin`, lorsqu'il sera retrouvé, **ne doit jamais être utilisé comme fichier update**.

## Sources directes récupérées

- `05_TEXTES_EXTRAITS_DES_ARCHIVES/RAPPORT_PHASE35_D578.txt`
- `05_TEXTES_EXTRAITS_DES_ARCHIVES/PHASE35_FLASH3M_PASS1_AUDIT.txt`
- `05_TEXTES_EXTRAITS_DES_ARCHIVES/RAPPORT_PHASE32_D578.txt`
- `05_TEXTES_EXTRAITS_DES_ARCHIVES/D578_PHASE35_FLASH_PAGE_MAP_896.txt` (extraction textuelle du CSV)
- `07_CODE_SIMULATEURS_ET_SOURCES_RECUPEREES/D578_PHASE53_OFFLINE_2026-11-03/tools/audit_v121.py`
