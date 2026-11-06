# État des fonctions : ce que l'analyse seule permet et ce qui exige des mesures

**Révision de travail : D578UV PRO GD32, application V1.21, 5 novembre 2026.**

La colonne « Analyse seule » représente ce que l'on peut étudier avec le code public, les documents, les dumps déjà disponibles et les fiches constructeur, **pas une promesse de certitude**. La colonne « Mesure requise » décrit ce qui ne peut être prouvé sans photographie suffisamment lisible, mesure passive ou continuité sur une carte représentative.

## 19 fonctions du premier modèle

| Fonction | Ce qui manque | Faisable sans poste | Mesure ou photo indispensable |
| --- | --- | --- | --- |
| `lcd` | Contrôleur exact, continuité FPC et interface backlight | Comparer les transactions d’initialisation OEM à ST7735 et aux contrôleurs alternatifs ; reconstituer reset, delays et RGB565 | Photo macro du contrôleur/FPC, contrôles des contacts PE7–PE14, PB10–PB13, rétroéclairage |
| `keys` | Valeurs de résistances et hystérésis, faux déclenchements/antirebond | Analyser le code des seuils ADC, les exceptions et les intervalles de lecture | Valeurs ADC brutes pour chaque touche, résistances et mesures au repos |
| `encoder` | Polarité, temps d’antirebond, montage électrique pull-up | Tracer EXTI et automate de quadrature ; vérifier ordre PC8/PC9 | Capture deux phases en rotation gauche/droite et contact d’appui |
| `volumes` | Affectation A/B et loi de transfert vers atténuateurs/gains | Rapprocher PC2/PC5 des fonctions speaker-volume et U2429, données OEM | Potentiomètres identifiés par mesures ADC simultanées et trames U2429 |
| `lights` | Circuits de commande, table des canaux de LED et PWM rétroéclairage | Indexer writes PE3/PE4, PA5/PB3/PB4, démultiplexeur et canaux 0..15 | Suivi pistes jusqu’aux LEDs, fréquence des lignes et contrôle de chaque éclairage |
| `microphone` | Orientation UART au connecteur, protocole complet, microcontrôleur interne, chemin analogique | Étendre parseur 0x41/0x53 et identifier les champs 8..14 | Capture UART sur prise 8 contacts, tension et lignes micro/haut-parleur |
| `swd` | Schéma de reset, alimentation et stratégie de récupération | Cartographie séquence boot, SWD DP/AP, sections Flash et vecteurs | Confirmer NRST, alimentation et comportement après récupération en conditions sûres |
| `mcu` | Cartographie exhaustive multiplexage GPIO, clocks, DMA, interruptions, RAM réellement occupée | Étendre désassemblage et journaux du banc, charger vecteurs, état horloges et assertions | JTAG/SWD lecture seule et mesures simultanées pour signaux partagés |
| `adc0` | Canaux et taux d’échantillonnage effectifs par scénario, décalage mesures | Décoder SQR/CHSEL, DMA et tables de calibration ; corréler volumes/touches | Injecter aucune tension : observer valeurs mesurées et comparer aux potentiomètres |
| `power` | Arbre 13,8 V / 5 V / 3,3 V, séquencement et état sommeil | Rechercher commandes power/standby et délais de reset, logique d’activation du PA | Tracer L7805CV, protections et rails au repos et en réception |
| `nand` | Table partitions, correction ECC exhaustive, wear/bad-block et écriture sûre | Interpréter dump, OOB, réserves, index et appels pilote ; déduire format sans écrire | Captures lecture seule, comparaison dump stable, mesure bus et politique de récupération |
| `gps` | USART, baud, EN/RESET, NMEA/UBX/CASIC exact, sauvegarde et PPS | Recherche séquences NMEA, initialisation UART, chaînes et interrupteurs dans V1.21 | Capture UART passivement à l’acquisition et repérage TX/RX sur ATGM336H |
| `dmr` | Pinout HPI, reset/clock/IRQ, code DSP, streaming, calibres, DMR TDMA | Analyse des commandes HPI dans firmware et des objets de simulation; localisation blob DSP | Captures bus en RX normal, relevé horloge/reset IRQ, statut boot |
| `codec` | Référence physique, I²C/SPI contrôles, I²S audio, gains et offset par profil | Décoder écritures codec et registres TI, déterminer initialisation audio | Identification du boîtier exact et liaisons numériques/analogiques vers DMR/PA |
| `audio` | Ordre codec → atténuateur → amplificateur, fonctions PA7/reg0x25 | Tracer Speaker Mode et commandes mute selon scénarios connus | Continuité du trajet U2429/MC34119/YD1517 et niveaux volume |
| `bluetooth` | SoC blinde, brochage D868BT-SP, UART/baud, dialogue et audio reel | Modeliser ET12 UART3 (VER/AGHF), analyser les chaines OEM, appairage PTT/BT01 et variants PRO/PLUS | Photographies support + module, continuite UART/EN/RESET, captures de demarrage et d'appairage |
| `rf` | Attribution des 4 QA, PLL, FI, filtres, squelch/CTCSS, biais varicap | Decoder banques SPI, registres 0x29/0x2A/0x44/0x7F et états de réception | Suivi chaque CS, 26 MHz, filtres 38,550/38,850 et RF RX |
| `pa` | Deux chemins VHF/UHF, DAC de polarisation, protection et linéarisation | Repérer appels puissance/mode/bande, tables usine, états de TX contrôlés logiciel | Photos/tracés des AFT05MP075N et rails PA, aucun TX exploratoire |
| `antenna` | Chemin RF complet, commutation TX/RX, filtres passe-bas et protection | Comparer variantes de bande et décisions GPIO pour commutateurs | Continuité depuis les filtres/PA jusqu’au connecteur et mesures RF instrumentées |

## Composants ajoutés à l'inventaire

| Composant | Ce qui manque | Faisable sans poste | Mesure ou photo indispensable |
| --- | --- | --- | --- |
| `rda5802n` (RDA5802N) | Interface I²C exacte, référence, sortie audio, antenne et mapping PB6/PB7 | Décoder les trames enregistrées par FmI2c et appels OEM | Comparer niveau SDA/SCL sur broches tuner et sortie audio |
| `qa_lo_a` (QA candidat LO A) | Fonction physique et CS du boîtier | Comparer mots 0x29/0x2A aux commandes VFO A | Continuite CS et fréquence oscillateur |
| `qa_lo_b` (QA candidat LO B) | Fonction physique et CS du boîtier | Comparer mots 0x29/0x2A aux commandes VFO B | Continuite CS et fréquence oscillateur |
| `qa_if_a` (QA candidat FI A) | Affectation FI, CS et chaîne analogique | Comparer changements de squelch et registres RF | Relier filtre 38 MHz et contrôle CS |
| `qa_if_b` (QA candidat FI B) | Affectation FI, CS et chaîne analogique | Comparer changements de squelch et registres RF | Relier second filtre 38 MHz et CS |
| `ref26` (Référence 26 MHz) | Répartition aux QA et stabilité | Rechercher calibrations d’horloge OEM | Sonde haute impédance non intrusive |
| `rf_spi` (Bus RF quatre sélections) | Associer banques logiques aux 4 circuits | Simulation déjà disponible dans bench/rf_spi.py | Continuité PB5/PB2/PC13/PE1 |
| `bh2226` (H2226 / BH2226FV-E2 confirme) | Affectation 8 sorties, controle CS/CLK/DI et table de calibration | Emission 12 bits connue de la datasheet ; recherches de boucles et mot-cle init | Continuite DA1..DA8, CS/CLK/DI, tension d'alimentation |
| `u2429` (UTC U2429G) | Deux entrées et sorties et GPIO de contrôle | Rechercher pulses 11 bits liés au volume | Continuité et capture CLOCK/DATA, niveau 5 V |
| `mc34119` (MC34119G) | Affectation HP, CD, audio et alimentation | Chercher commande speaker mode et mute | Continuité CD et OUT1/OUT2 |
| `sgm8272` (SGM8272) | Deux boucles analogiques inconnues | Relier séquences de calibration DAC si identifiées | Mesurer feedback, entrée/sortie et rails |
| `yd1517` (YD1517P) | Lien mute M/SS, alimentation, entrées et sorties | Comparer états PA7 issus du banc | Continuité entre pin 8 et PA7 ; sorties HP |
| `aft_vhf` (AFT05MP075N VHF) | Biais TX, capteurs et filtres | Chercher tables de puissance VHF | Tracer réseau PA sous protection RF |
| `aft_uhf` (AFT05MP075N UHF) | Biais TX, capteurs et filtres | Chercher tables de puissance UHF | Tracer réseau PA sous protection RF |
| `l7805` (L7805CV) | Charges du rail +5 V et activation éventuelle | Reconstituer machine Power du firmware | Mesure des rails et continuité hors tension |
| `bt_support` (support D868BT-SP) | Connector/pads, rails, antenne, identite support entre PRO et PLUS | Comparer les photos FCC et generations D868/D878, localiser les appels UART3 | Photos des 2 faces, continuity connecteur et alimentation |
| `bt_et12` (module blinde) | SoC sous blindage, firmware exact, UART, audio, enable/reset | Documenter VER/AGHF, chercher xrefs AT+ dans la ROM si disponible | Lire version en menu, capter UART passivement au boot, relever padout |
| `bt01` (micro Bluetooth) | Trames commande/ecran/audio, priorites IHM et sortie du mode distant | Exploiter manuel BT01, recenser les menus et construire un automate de reconnexion | Capture d'appairage et messages BT01, controles des commandes filaires |
| `bp02` (PTT Bluetooth) | Trames PTT, mode Hold, watchdog, niveau batterie, separation audio | Definir machine d'etats et tests d'inhibition TX avec manuel BP-02 | Capture d'appairage et appui/relache, perte de connexion |

## Répartition des tâches

### Réalisable hors ligne dès maintenant

- Indexer les données constructeur accessibles, les routines déjà trouvées, les registres et séquences de simulation avec leur **niveau de preuve**.
- Retrouver des initialisations, tables de fréquences, traitements de registres et boucles de sérialisation dans un **binaire V1.21 intégral disponible localement**. Dans le dépôt public préparé ici, le binaire OEM intégral **n'est pas présent**, donc les nouvelles adresses de routines ne sont pas revendiquées.
- Proposer des pilotes HAL sans dépendance à la RAM OEM et des tests d'encodage côté PC, en gardant les valeurs de registres non qualifiées comme inconnues.
- Documenter séparément PRO et PLUS, sans transférer un brochage ou un firmware par supposition.

### Impossible à confirmer hors ligne sans nouvelles données matérielles

- Identifier **physiquement** chaque broche de chacun des quatre LQFP32 grattés et sa sélection SPI.
- Attribuer les sorties BH2226 et SGM8272 à des varicaps, amplificateurs ou régulateurs sans suivre les pistes.
- Déterminer la référence précise `KT09?5R` à partir d'un marquage incertain, le connecteur PLUS et son bus.
- Vérifier la continuité entre GPIO du GD32 et circuit RDA/U2429/MC34119/YD1517/L7805.
- Etablir le brochage et l'identite du SoC du module Bluetooth sous blindage, ainsi que les trames BT01 et BP-02 en utilisant des mesures et captures passives. Le marquage D868BT-SP ne demontre pas a lui seul une equivalence D878.
- Certifier la chaîne TX, les calibrations PA, les profils RF ou la sûreté d'un firmware flashable sans essais de protection et de récupération.

Le [plan de mesures](PLAN_INVESTIGATION_BROCHAGES.md) fournit un ordre de travail et un format de fiche réutilisable pour chaque liaison.

### QA4818N : mise à jour documentaire du 6 novembre 2026

Le nouvel [analyseur QA4818N](QA4818N_RECONSTRUCTION_REGISTRES_PLL_CHAINES_RX_TX.md) rapproche automatiquement les paires de registres `0x29/0x2A` des fréquences VFO et des FI 38,550/38,850 MHz ; un calculateur C reproduit le format supposé AT1846S. Il **ne clôt pas** l'inconnue sur les quatre CI : la corrélation sur captures OEM et la mesure de fréquence LO restent nécessaires.
