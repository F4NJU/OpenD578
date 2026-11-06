# 05 - Bootloader GD32 24 Kio : Flash, vecteurs, USB et politique de recuperation

> **RECONSTITUTION du 05/11/2026.** L'original historique homonyme et le dump binaire `boot_A.bin/boot_B.bin` ne sont pas redistribues ; toutes les adresses et empreintes de cette fiche proviennent des rapports d'acquisition existants. Ce fichier n'est pas une image executable.

## 1. Les trois demarrages a ne pas melanger

| Domaine | Cible | Action | Ce qu'on peut en conclure |
| --- | --- | --- | --- |
| Bootloader OEM dans Flash interne | GD32F303VKT6 | Demarrage et installation de l'application OEM | Domaine occupe et protege de 24 Kio sur le poste analyse |
| « MCU Update » | Mise a jour du GD32 | Etat avec LED rouge clignotante vu via SWD/USB | Descripteurs USB ne suffisent pas a reconnaitre le mode |
| « Boot Mode for Sct » | Sicomm SCT3258 | Mise a jour/pont de communication DMR | **Ce n'est pas** un recovery garanti du GD32 |

Le GD32 comporte egalement des mecanismes de boot ROM definis par le silicium, mais l'acces physique a `BOOT0`, les niveaux au reset et la politique de protection de la carte AnyTone ne sont pas qualifies. **Ne pas supposer qu'un boot ROM USB/USART est exploitable parce qu'il existe dans la datasheet.**

## 2. Flash physique relevee en lecture via SWD

Cible : **GD32F303VKT6**, 3 145 728 octets de Flash et 98 304 octets de SRAM. Connexion debug reussie avec un FTDI FT232H / OpenOCD a 25 kHz en SWD, pads identifies par l'utilisateur, **sans NRST cable**. Lecture double passe des trois Mio et du boot :

| Plage ARM, inclusive | Taille | Constat |
| --- | ---: | --- |
| `0x08000000..0x08005FFF` | 24 576 octets | Boot OEM propre a cette revision |
| `0x08006000..0x080FF18B` | 1 020 300 octets | Image application **GD V1.21 CDD** identique au dump |
| `0x080FF18C..0x080FF19F` | 20 octets | Zeros hors fichier CDD |
| `0x080FF1A0..0x082F57FF` | 2 057 824 octets | `FF` lors de deux captures, **pas libre garanti** |
| `0x082F5800..0x082FF81F` | 40 992 octets | Donnees constructeur non-FF |
| `0x082FF820..0x082FFFFF` | 2 016 octets | Derniere portion FF, zone OEM dependante |

**Des editions AnyTone anterieures** etudiees par RadioFoundry emploient un bootloader de 16 Kio et une application a `0x08004000`. Ces adresses sont **incompatibles** avec le releve de notre boot 24 Kio / app `0x08006000`. Ne pas les recopier pour cette image.

## 3. Vecteurs et routines retrouvees (GD V1.21)

| Adresse | Role analyse | Force de preuve |
| --- | --- | --- |
| `0x08000000` | Base Flash et table vecteur boot | Dump SWD, code statique |
| boot MSP `0x20001E50` | Valeur de pile initiale du boot | Vecteur lu |
| boot Reset pointeur `0x080004D9` | Reset_Handler Thumb du boot, code a `0x080004D8` | Vecteur lu |
| `0x08006000` | Table vecteur de l'application V1.21 | Dump et CDD |
| app Reset_Handler `0x08006D38` | Initialisation application | Analyse statique |
| `0x08006384/0x08006388` | Changement de VTOR dans l'application | Analyse statique |
| `0x0800436E` | Routine boot FMC candidate | Analyse statique, **pas une API qualifiee** |
| `0x0808CE72` | Routine d'alimentation Flash haute depuis des donnees NAND | Analyse statique, risque de reecriture |
| `0x0800400E` | Ancrage de transfert mentionne dans rapports historiques | **A revalider avec dump**, ne pas executer |

La borne de securite reperee dans le boot teste un **debut d'adresse** `0x08000000 <= r8 < 0x08100000` ; elle **ne prouve pas** qu'une longueur de transfert est bornee ni que le boot protege des secteurs par construction. Le jeu d'instructions et les littéraux du boot doivent etre examines dans un environnement isolement, jamais rejoues directement sur une carte client.

## 4. Empreintes attestant les sources proprietaires (non incluses)

| Source originale | Taille | SHA-256 |
| --- | ---: | --- |
| Boot GD32 physique | 24 576 | `c098c74d2a979e162d6dd901c9d59d7ed3f0a4c9d526a168a1db78fba316fdeb` |
| Flash GD32 physique double passe | 3 145 728 | `e2f2483baf60e2bfcab656e25e949670713222591ef4d611d6089054819a750e` |
| Application OEM GD V1.21 `.CDD` | 1 020 300 | `02b2a3b56bd57c7ada581eb52b9b6f41c5d51aaec1b068d37585efd58dff9c9a` |
| Application OEM GD V1.20 | 1 020 096 | `1cdf1817f8abbbee72901357316953aea28763e192fe35b913c82520db31453b` |

Le depot n'expedie pas les fichiers OEM, les dumps ou les patches binaires pouvant contenir du code proprietaire. Les hashes ne remplacent pas les octets : une revue independante exige la copie authentique sous controle du proprietaire du poste.

## 5. USB normal, CPS et UPDATE

Le firmware OEM expose USB **VID `28E9`, PID `018A`**, interface CDC ACM **GD32 Virtual ComPort in FS Mode**, numero de serie rapporte `000000010000`. Cet identifiant peut se retrouver dans plusieurs modes ; **ne pas faire de choix de recovery selon VID/PID**.

Le protocole CPS `PROGRAM`/`R`/`W`/`END` a ete decodue dans le banc, mais il s'agit des **commandes de codeplug** et non des ordres de reprogrammation MCU. RadioFoundry documente dans la famille OEM un protocole `UPDATE` suivi de paquets de 32 octets et checksum ; nous n'avons pas qualifie une session complete d'installation sur le poste physique. Ne pas envoyer `UPDATE` en utilisant le banc CPS comme s'il s'agissait d'une commande de lecture.

Le terme **Boot Mode for Sct** correspond a un pont vers la Flash interne du baseband DMR. Le MCU peut dans ce mode servir de transport USB <-> HPI, et les options de mise a jour SCT n'effacent pas necessairement le bootloader GD32. Les details restent distincts dans `04_DMR_SCT3258_BOOTSTRAP_HPI_PAQUETS_CODEC_PARAMETRES.md`.

## 6. Modele de developpement OpenD578 : principes bloquants

Un firmware alternatif autonome doit posseder une table de vecteurs, ses propres horloges, GPIO, USB, interruptions, watchdog, pilotes NAND, LCD, clavier, GPS, codec et SCT. Les **adresses de routines 0x080... et variables RAM 0x200... OEM n'ont aucun sens apres remplacement**. Pour un patch additif dans l'application OEM, il faut au contraire documenter et verifier toute ABI particuliere, ce qui n'est pas fait.

Conditions de publication d'une premiere image chargeable :

1. **Carte exacte** (PRO/PLUS, suffixe et MCU, version OEM) identifiee.
2. Source OEM authentifiee, sauvegarde Flash/NAND, checksums et lecture de verification ; une NAND avec pages ECC20 ne constitue pas a elle seule une sauvegarde restaurable.
3. Secteur Flash destine a OpenD578 **officiellement reserve ou prouve non utilise**, avec effacement sans collisions de pages ni ressources CJK OEM.
4. Vecteurs, position RAM/pile/heap et consommation en pleine charge qualifies ; les 3 872 derniers octets de RAM non initialises ne sont **pas** une preuve d'espace libre.
5. Recovery **independant** teste sur echec, coupure et image invalide. La lecture SWD ne prouve pas qu'un restore marche.
6. Tests de zero TX involontaire, watchdog, GPIO tri-state a boot, pas de PA enable ni DAC RF en etat inconnu.
7. Tests de retour arriere, provenance et identification strictes de la version avant toute operation d'ecriture.

Pour l'instant : **NO_GO** pour une image OEM modifiee, un blob phase60 ou une nouvelle application flashable. Le mode satellite Phase60 est **pass-through inactif**, avec `.bss` placee volontairement a `0x30000000` comme garde-fou.

## 7. Liste des preuves a recuperer si disponibles

- `boot_A.bin`, `boot_B.bin`, `full_flash_pass1.bin`, `full_flash_pass2.bin` avec hashes et journal OpenOCD.
- `D578_GD32_Brochage_KiCad_V0_3.zip`, original V0.3, plutot que le nouveau symbol KiCad reconstruit sous `hardware/kicad/`.
- `D578_SAT_V121_EXP06_PHASE60_SAT_CHANNEL_NONFLASHABLE_2026-11-03.zip` et CDD d'origine, sans redistribution publique OEM.
- Traces USB du processus Update **en lecture seule et anonymisees**, puis confirmation d'un recovery physique avant toute ecriture.

## 8. Sources

- Projet : `../02_CPU_FLASH_BOOT_USB_SWD.md`, `../04_RAM_ROUTINES_UI_RF_ET_BROCHAGE.md`, `../05_SATELLITE_CODE_INTEGRATION_EXP06.md`, `../cps/PROTOCOLE_OEM_V121.md`.
- GigaDevice GD32F303 : <https://www.gigadevice.com/product/mcu/mcus-product-selector/gd32f303vkt6> ; datasheet LQFP100 : <https://www.gd32mcu.com/data/documents/datasheet/GD32F303xx_Datasheet_Rev3.0.pdf>.
- RadioFoundry comparaison bootloader AnyTone et SCT : <https://radiofoundry.org/docs/spec/hardware-anytone> (autres variantes non transposables telles quelles).
- Comparatif OEM D578 et recovery : <https://www.theweeks.org/tmp/FILES/Anytone-Mods/578mods.htm>.
