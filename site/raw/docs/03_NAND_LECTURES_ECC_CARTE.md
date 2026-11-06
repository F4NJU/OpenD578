# NAND Toshiba/KIOXIA, géométrie, captures, ECC et zones critiques

## Fichiers physiques et hashes attestés

Le composant est `TC58CVG1S3HRAIG`, ID en lecture `98 CB`. Capacité **2 048 blocs x 64 pages x 2 048 octets = 268 435 456 octets main (256 Mio)**. Acquisition avec ECC interne actif: **64 octets auxiliaires par page**, soit 8 388 608 octets, non équivalents au véritable OOB raw 128 octets avec ECC désactivé. Interleave: 2 112 octets par page, total 276 824 064 octets (264 Mio), sur 131 072 pages. Un bloc main mesure 131 072 octets (128 Kio). Ne pas confondre **offset NAND de fichier** et adresse ARM Flash interne `0x080...`.

| Source originale non incluse | Taille | SHA-256 de l'acquisition 03/11 |
|---|---:|---|
| `nand_main_256MiB.bin` | 268 435 456 | `329d22165d234bf0df043e62af11397dea96327925b9db18f3c354230ff40945` |
| `nand_oob64_8MiB.bin` | 8 388 608 | `9a999b9fd13a02b45ed4d38e68f9e9c7d1095994c751e36e04f4a62b2e4c5106` |
| `nand_ecc_status_128KiB.bin` | 131 072 | `b40ebd3ebc3923f01d9d98a52a3b019b65785641ba76687127678b788ea793c6` |
| `nand_2112_interleaved_264MiB.bin` | 276 824 064 | `568b6395f88e8ef1b27d16fc9c25aa5d94f8bcf5d47556910466baaeeefde1c9` |
| `nand_critical_896KiB_main.bin` | 917 504 | `f10703d96c006543d05c5715e293c095dff486f16162c7273f896e28852b81fe` |

`capture_report.json` (~9 592 o) déclare acquisition COMPLETE, 276 824 064 octets validés, pas de commande NAND d'écriture, pas de modification Flash cible, double passage critique correspondant et récupération non prouvée. `openocd_nand.log` (~439 131 o) mentionne `D578_NAND_RUN_FINISHED`. Les captures brutes anciennes existent au catalogue mais leurs octets n'ont pas été exportés ici. **Les données de la NAND peuvent contenir indicatifs et paramètres privés.**

## Statuts ECC

| Statut | Pages | Interprétation de la capture |
|---|---:|---|
| `00` | 130 610 | Pas d'erreur signalée. |
| `10` | 25 | Bits corrigés par ECC interne. |
| `20` | **437** | Erreurs non corrigées selon le statut capturé. Ne pas restaurer aveuglément. |
| `30` | 0 | Aucune page dans cette classe. |

Sur les 437 pages avec ECC 20 : 192 pages toutes à `00` dans blocs 3, 1536, 1537; 225 pages de fin de bloc motif `22334455 ... 5555AAAA`; 10 pages de fin motif `AAAA5555 5555AAAA`; 10 pages avec contenu non trivial. **Correction d'erreur antérieure : il y a 235 pages marqueurs de fin de bloc, non 238.** Pages non triviales à traiter en priorité: `8324`, `14848`, `14912`, `17024`, `18817`, `18818`, `20992`, `24256`, `24320`, `24448`.

La présence d'octets `00` sur tout un bloc et ECC `20` ne démontre pas l'état réel de la cellule; il peut s'agir de données non retournées. Aucune image de restauration physique totalement fiable n'est certifiée.

## Carte logique candidate, offset main

| Offset/bloc | Observations | Force |
|---|---|---|
| Bloc 1 / `0x00020000`, bloc 384 / `0x03000000` | Glyphes monochromes chinois 16x16, 32 octets par glyphe, lignes big-endian. Prévisualisations PNG créées précédemment mais originaux non exportés. | Format observé, chemin LCD non prouvé. |
| Bloc 64 / `0x00800000` | Indicatifs, noms, fréquence et structures de relais. | Signatures, sans décodage complet. |
| Blocs 379-382 / `0x02F60000..0x02FDFFFF` | Paires de copies proches, signatures `D578UV`, probables paramètres/copies de calibration. | **Critique à protéger**, rôle exact à confirmer. |
| Bloc 383 / `0x02FE0000` | `CHECKING DATA FOR D578UV`. | Chaîne certaine, sens exact non connu. |
| Blocs pairs 512-550 / depuis `0x04000000` | Valeurs numériques en enregistrements fixes. | Hypothèse index/tables. |
| Blocs pairs 680-1032 / `0x05500000..0x0811FFFF` | Noms, indicatifs, villes/pays. | Annuaire radio/DMR probable. |
| Blocs 3,1536,1537 | Main et auxiliaires tout zéro, ECC20 sur l'ensemble. | Non garantis utilisables. |

Occupation statistique de 2 048 blocs : 741 blocs tous FF, 576 à marqueur de dix octets 55 initiaux, 463 à sentinelle terminale 55 55 AA AA, et autres familles. **Les 741 blocs FF ne sont PAS des blocs attribuables aux TLE.**

## Copies critiques

- Page 24256 bloc 379 vs page 24320 bloc 380 : 1 octet différent à indice 21.
- Page 24384 bloc 381 vs page 24448 bloc 382 : 5 octets différents aux indices 3, 10, 11, 12, 13.
- Signatures `D578UV` aux offsets `0x02FA0010`, `0x02FC0010`; `CHECKING DATA FOR D578UV` à `0x02FE0000`.
- Plusieurs pages de ces couples portent ECC20 : la ressemblance entre copies ne garantit pas leur intégrité.
- Extraction courte `nand_critical_896KiB_main.bin` : 7 fragments de 128 Kio, dont les quatre derniers blocs 379,380,381,382. Les trois premiers portent des marqueurs ordinaires et ne se repèrent pas de manière unique sans la carte de capture.

## Commandes et séparation lecture/écriture

Les écritures **présentes en code statique OEM** sont `06` write-enable, `02` program load, `10` program execute, `D8` erase, mais **elles n'ont pas été exécutées dans l'acquisition fournie**. L'acquisition matérielle utilisait `9F`, `0F`, `13`, `03`. La simulation V3 ajoute `3B` sur deux lignes pour reproduire l'interface réellement utilisée par l'application; elle n'écrit pas les données NAND d'origine.

Les tables de la copie Flash haute lisent la NAND aux offsets `0x00200000`, `0x02B00000`, `0x02B20000`, `0x02B80000`, `0x02BA0000`. Un appel OEM ciblant 32 octets à `0x02F60000` a été repéré en Phase47 : protection prioritaire.

## Reprise de l'analyse

Retrouver les 5 fichiers de capture bruts, vérifier SHA; reproduire `map_nand.py`, `preview_glyphs.py` si l'archive `D578_GD32_Satellite_PHASE46_NAND_RE_2026-11-03.zip` est récupérée. Exécuter les scripts originaux en lecture seule. Pour le simulateur disponible, utiliser `D578_RAM_NAND_SIM_V3_2026-11-04/verify_spi_wire.py` avec les trois fichiers de capture attendus. **Ne jamais écrire dans la NAND pour tester une hypothèse de mapping.**
