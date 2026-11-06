# Inventaire des originaux manquants et documents reconstruits

**Date : 05/11/2026.** Les noms ci-dessous renvoient aux travaux des discussions anterieures. On ne fabrique jamais un faux binaire pour faire croire a une archive complete.

| Original historique annonce | Statut dans ce depot | Alternative actuellement presente |
| --- | --- | --- |
| `D578_DOSSIER_PERIPHERIQUES_2026-11-05.zip` et ses 5 monographies | Archive originale absente | Cinq fichiers `docs/peripherals/` **reconstruits** |
| `D578_GD32_Brochage_KiCad_V0_3.zip` | ZIP original absent | CSV datasheet 100 pins et KiCad **recrees 05/11 V0.4** |
| `D578_SAT_V121_EXP06_PHASE60_SAT_CHANNEL_NONFLASHABLE_2026-11-03.zip` | Code exact Phase60 non exporte | `docs/05_SATELLITE_CODE_INTEGRATION_EXP06.md`, phase60 non flashable decrite |
| `OpenD578_MAJ_V11_8.zip` complet | Distribution executable originale absente | Notices V11.8, code banc public V11.7 |
| `boot_A.bin`, `boot_B.bin` | Binaire de boot physique absent | Vecteurs, allocations et SHA256 dans docs/02 et docs/peripherals/05 |
| `full_flash_pass1.bin`, `full_flash_pass2.bin` | Dumps Flash 3 Mio absents | Cartographie et empreintes sans bytes |
| `nand_main_256MiB.bin`, `nand_oob64_8MiB.bin`, `nand_ecc_status_128KiB.bin`, `nand_2112_interleaved_264MiB.bin` | Dumps NAND absents ; 437 ECC20 | Carte statistique, hashes, scripts d'observation |
| Photographies carte CPU/RF de nos PRO/PLUS avec blindages retires | Non publiees | Liens FCC, guide photographique tiers, manifestes vides |
| Captures passives UART/GPIO/HPI des composants reels | Non archivees | Traces et decodeurs du banc public, et plans de mesures |

La non-publication de certains fichiers OEM et dumps est souhaitable : droits de tiers, informations individuelles et memoires de calibration. Une archive **publique** ne peut donc pas etre un clone inconditionnel de toutes les donnees de recherche. Le projet doit publier la preuve de provenance (SHA256, chemin et rapport) et conserver les sources proprietaires/secrets dans l'archive privee du proprietaire.

## Empreintes attestant les binaires proprietaires historiques

- Boot physique 24576 octets : `c098c74d2a979e162d6dd901c9d59d7ed3f0a4c9d526a168a1db78fba316fdeb`.
- Flash physique 3145728 octets : `e2f2483baf60e2bfcab656e25e949670713222591ef4d611d6089054819a750e`.
- App OEM V1.21 CDD 1020300 octets : `02b2a3b56bd57c7ada581eb52b9b6f41c5d51aaec1b068d37585efd58dff9c9a`.
- NAND main 268435456 octets : `329d22165d234bf0df043e62af11397dea96327925b9db18f3c354230ff40945`.
- NAND OOB64 8388608 octets : `9a999b9fd13a02b45ed4d38e68f9e9c7d1095994c751e36e04f4a62b2e4c5106`.
- NAND 2112 interleave 276824064 octets : `568b6395f88e8ef1b27d16fc9c25aa5d94f8bcf5d47556910466baaeeefde1c9`.
- Phase60 originale : consulter la passation `docs/05_SATELLITE_CODE_INTEGRATION_EXP06.md` ; un rapport de code compile NE FOURNIT PAS les octets originaux.

**Ne pas attribuer au depot les tests exacts de Phase60 ou les observations hardware d'une archive qu'on ne peut pas re-executer.**
