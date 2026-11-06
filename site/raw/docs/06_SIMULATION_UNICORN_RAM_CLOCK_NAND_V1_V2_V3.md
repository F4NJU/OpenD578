# Simulations réellement récupérées, 4 novembre 2026

**Nature:** exécutions Unicorn Cortex-M4 hors radio, avec firmware officiel GD32 V1.21 dont le SHA attendu est `02b2a3b56bd57c7ada581eb52b9b6f41c5d51aaec1b068d37585efd58dff9c9a`. Les ZIP de simulations contiennent les scripts, README, tests, JSON et sauvegardes SRAM; la CDD officielle et les gros BIN NAND ne sont pas dans ces ZIP. Les instructions exécutées ne sont **pas** des cycles horloge mesurés, une charge CPU ou un temps réel.

## V1 : audit RAM

Archive exacte incluse `D578_RAM_AUDIT_2026-11-04.zip`.

- Reset vrai `0x08006D38` bloque sur `RCU_CTL 0x40021000` en `0x08006344` sans modèle horloge.
- C startup `0x08006130` vers `0x0800620C`, sans `SystemInit`, exécute 64 088 instructions. Initialise 6 872 octets data et 87 560 octets zéro, soit 94 432 octets, réserves 512 heap et 1 024 stack incluses.
- Prolongation jusqu'à main `0x08006654` : 64 549 instructions, puis blocage en `0x08008A82` sur `RCU_CTL`.
- Deux SRAM initiales `0xA5` et `0x5A`: zone init identique au décodeur indépendant des 2 529 octets compressés de source; haut 3 872 octets non écrit pendant le chemin limité.
- Correction de faux positifs pointeurs haut RAM `0x20017801`, `0x20017904`, `0x20017F21`, qui sont en fait des séquences Thumb.
- **Pas** une mesure de consommation maximale RAM.

## V2 : RCU, horloge, GPIO et SysTick

Archive exacte incluse `D578_RAM_CLOCK_SIM_V2_2026-11-04.zip`.

- Part du vrai Reset_Handler et traverse SystemInit, scatter, main, puis initialisation application, sans patch ni fonction sautée.
- `RCU_CTL 0x40021000` : stabilité IRC8M/HXTAL/PLL après activation; bits stable 1/17/25 reflétant disponibilité réelle modélisée, `RCU_CFG0 0x40021004` statut système, alias bitband PLL `0x42420060`. `FMC_WS 0x40022000` enregistre wait-state (pas d'effacement), `SCB_VTOR 0xE000ED08` reçoit `0x08006000`.
- Horloge seule -> arrêt à configuration GPIOC `0x40011000`, 64 828 instructions immédiat, 64 954 avec attente 7 lectures RCU_CTL.
- GPIO/AFIO/SysTick -> entrée pilote mémoire via `0x0808AE62`, arrêt à `0x0800879A` sur `GPIOA_ISTAT 0x40010808` bit PA15, 70 692 ou 70 818 instructions.
- Pilote demande `9F` et compare `C8`, puis `98`; une donnée de mémoire externe doit être fournie, non inventée.
- Tests négatifs HXTAL/PLL indisponibles restent dans les boucles (`0x08006276`, `0x08006308`) après quota 100 000. La simulation ne force donc pas une réussite factice.
- SysTick config initiale `CTRL 0x3`, recharge `0x124F8` = 75 000; unité virtuelle et aucune mesure du quartz réel.

## V3 : NAND bit-série, sommeil profond, Power, ADC DMA

Archive exacte incluse `D578_RAM_NAND_SIM_V3_2026-11-04.zip`. Le simulateur fait communiquer le code OEM avec une NAND **virtuelle** alimentée par la capture physique. Il ne fait pas un `memcpy` de convenance directement dans les buffers SRAM : il simule les fronts SCK, CS et les bits MISO/SO0/SO1. Il compare après coup les données attendues et celles effectivement lues.

Bus : PB8=CS actif bas, PB15=SCK, PB14=MOSI ou SO0, PA15=MISO ou SO1. Commandes modélisées `9F`, `0F`, `1F`, `13`, `03`, `0B`, `3B`, `06`, `04`, `FF`, `FE`. L'application utilise effectivement `3B` (deux fils) en démarrage. ID `98 CB`, NAND virtualisée avec A0=38 et B0=16 à la remise à zéro selon les docs, ensuite état modifié par l'OEM. ECC `20` conservé dans les états, pas magiquement corrigé.

**Résultat V3:**

| Mesure | Résultat |
|---|---|
| Buffers lus par le pilote OEM et comparés au dump | **58/58** |
| Données transférées | **2 673 octets** |
| Pages chargées | **16 chargements**, **9 pages distinctes** |
| Buffers SRAM de départ distincts | **46** |
| Adresses SRAM distinctes couvertes | **2 610** |
| Transactions NAND durant scénarios avant/après Power | **105 par scénario** |
| Vérifications indépendantes `verify_spi_wire.py` | **16 groupes réussis** |
| Texte station constaté en lecture | `F4EGM JN29HN`, NAND page 19008 colonne 1536 vers `0x20003FEC` |
| Mise sous tension sans Power | `WFI 0x080089AA`, mode SLEEPDEEP |
| Réveil via Power virtuel | PA0/EXTI0 front descendant, IRQ6 vecteur `0x0808CAE5`, relâchement après 20 SysTick |
| SysTick | Vecteur Thumb `0x08009D79`, trame d'exception alignée, contrôle pile/registres |
| Stop suivant | `0x08007A9E`, activation DMA0 ch0 à `0x40020008` sur ADC0 |

Scénarios exécutés :

| Scénario | SRAM init | Instructions observées | Dernier état |
|---|---|---:|---|
| avant Power, NAND initialement busy puis ready, compteur normal | A5 / 5A | 7 242 575 chacun | WFI profond |
| avant Power, ready immédiat, entrée MISO inerte=0 | A5 | 634 527 | WFI profond |
| après appui + relâchement Power, attente idle accélérée x64 | A5 / 5A | 6 957 025 chacun | DMA ADC |

Les scénarios après Power exécutent **347 SysTick** et **1 IRQ6** par scénario, soit 348 retours d'exception contrôlés. 11 SysTick dans les scénarios avant Power busy. La simulation « idle-clock-scale=64 » est un raccourci **du modèle du compteur virtuel dans une attente**, pas une accélération du CPU réel ou un saut de fonction.

**ADC DMA, blocage volontaire :**

- PC `0x08007A9E`, écriture `DMA0 CH0 CTL 0x40020008 = 0x25A1`.
- Périphérique source `ADC0_RDATA` à `0x4001244C`.
- Destination SRAM `0x2000DA76`.
- Nombre: 7 valeurs 16 bits = 14 octets, plage `0x2000DA76..0x2000DA83`, déjà à l'intérieur de ZI constructeur.
- Aucune voie analogique, conversion, déclencheur ou transfert DMA réellement simulés à ce stade. **Le circuit TLV320AIC3204 est un codec audio distinct du périphérique ADC0 du GD32**; l'ADC rencontré est d'abord celui du microcontrôleur.

RAM: 94 432 octets init/reservés; haut 3 872 octets sans écriture observée sur ces chemins; pile main minimum avant Power `0x2001702C`, après Power `0x2001700C` soit descente maximale observée 212 octets depuis SP initial pour ce scénario. Cela ne borne pas les piles des tâches DMR/FM/APRS ou des IRQ RF en fonctionnement.

## Reproduire sur PC

Les scripts Python sous `07_CODE_SIMULATEURS_ET_SOURCES_RECUPEREES/D578_RAM_*` attendent Unicorn et la CDD constructeur exacte; `emulate_nand_v121.py` attend le répertoire des BIN NAND d'origine. Ils ne sont pas reliés au SWD, ne modifient aucun fichier constructeur, et leurs outputs JSON/SRAM sont des données de simulation. Voir les README et `requirements.txt` originaux inclus dans chaque ZIP. Exemple **lecture seule** :

```bash
python3 -m pip install -r 07_CODE_SIMULATEURS_ET_SOURCES_RECUPEREES/D578_RAM_NAND_SIM_V3_2026-11-04/requirements.txt
cd 07_CODE_SIMULATEURS_ET_SOURCES_RECUPEREES/D578_RAM_NAND_SIM_V3_2026-11-04
python3 verify_spi_wire.py /CHEMIN/NAND_ORIGINAUX --out verification_spi.json
python3 emulate_nand_v121.py /CHEMIN/D578UV_GD_V1.21_OFFICIEL.CDD /CHEMIN/NAND_ORIGINAUX --instructions 15000000 --wake-once --idle-clock-scale 64 --out power.json
```

Ce modèle prouve des transferts cohérents dans la simulation, **pas** l'activité radio, l'affichage LCD correct, l'occupation mémoire en charge, ni la robustesse d'un firmware modifié.
