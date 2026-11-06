# Inventaire des travaux encore ouverts et pistes d'analyse locale

Ce fichier donne un point de reprise transversal sans remplacer les fiches détaillées. Un composant « identifié » au sens de sa référence fabricant n'est **pas** nécessairement prêt pour un pilote lorsque ses GPIO, rails et périphériques voisins sont inconnus.

| Sous-système | Déjà exploitable dans le dépôt | Ce que l'analyse logicielle peut encore fournir | Ce qui exige une mesure ou un nouvel échantillon |
| --- | --- | --- | --- |
| GD32F303, démarrage et SWD | Cartes CPU, bootloader, observations SWJ, adresses des routines OEM | Tables vecteurs, appels SWD/USB, registres, sources d'horloge | Reset / BOOT0 sur la carte, séquence de récupération contrôlée |
| USB CDC et CPS | Protocole `PROGRAM/R/W/END`, descripteurs, source banc V11.7 | Décodage de captures, cartographie de nouveaux champs et transactions | Capture du CPS Windows complet, test sur PRO et PLUS |
| NAND 256 Mio | Dump de référence, géométrie, zones et ECC | Diff/entropie/structures/index, signatures d'écritures différées | Vérifier l'usure et l'interruption sans endommager les calibrations |
| GPS ATGM336H | Pilote et UART partiels | Analyse init, NMEA, traitements d'heure et GPS/APRS | Oscillateur, niveau logique et continuité UART |
| LCD, touches, codeur, LED | Timing, commandes, routage GPIO des fonctions connues | Couverture des commandes restantes et timings sur traces OEM | Brochages et alignement des photos PCB, mesure des courants |
| RF QA4818N x4 candidats | GPIO RF, mots série, référence 26 MHz et hypothèse 2 LO / 2 IF | Décoder tables de registres et distinguer instances/banques | Identifier les quatre boîtiers par pistes, quartz et signaux 26 MHz |
| FM RDA5802N | Modèle I2C PB6/PB7, adresse logicielle, commandes partielles | Extraire séquences init et configuration | Continuité de PB6/PB7 et réseau RF/audio |
| DAC ROHM BH2226FV (H2226, SSOP-B16) | Référence et protocole fabricant | Repérer séquences et ordres de commande du firmware | Affectation des huit sorties à chaque réglage analogique |
| ADC/AIC3204, U2429G, MC34119G, SGM8272 | Fiches fonctionnelles et chemins audio candidats | Registres d'initialisation et routage logiciel | Nœuds analogiques, niveaux, mute, gain et chaîne audio jusqu'aux HP |
| PA AFT05MP075N x2 et amplificateur PA1517G/YD1517P | Identification fabricant / variante | Tables de puissance, watchdog thermique, contrôle mute | Mesures RF et alimentation sous charge avec procédures sûres |
| Carte airband PLUS KT0905R/KT09S5R | Topologie carte fille / quartz / connecteur | Chercher appels de pilote et variantes dans image PLUS | Identifier puce, connecteur et bus, vérifier référence sur photo |
| Bluetooth D868BT-SP, ET12, BT01, PTT BP-02 | UART3 dans modèle, AT+VER?, fonctions UI | Désassembler chaînes et tables commandes, traces UART | Photo module sous shield, brochage BT, appairage et trames physiques |
| Modem SCT3258 / DMR | Flux HPI et fichiers de mise à jour distincts | Décrire protocole de transfert, audio AMBE, commandes de baseband | Mesures sur bus HPI et qualification d'une émission/réception DMR |
| Firmware alternatif | HAL source, modèle de simulation, stratégie satellite | Compilation/test hors ligne, budget mémoire, règles RF | Boot matériel indépendant, préservation calibration, comparaison RF |

Les essais restent **lecture seule** sur le poste physique tant qu'un moyen de récupération indépendant et les mécanismes de sauvegarde/restauration ne sont pas qualifiés.

À consulter : [audit des fonctions partielles](hardware/AUDIT_FONCTIONS_PARTIELLES.md), [priorités et blocages](09_REPRISE_PRIORITES_TESTS_ET_INFOS_MANQUANTES.md), [CPS et codeplug](cps/README.md), [sources externes](SOURCES_EXTERNES_ET_RECOUPEMENTS_20261105.md).

### Avancement RF du 6 novembre 2026

Un encodeur 30 bits (pas calculé 62,5 Hz selon AT1846S), un décodeur de journaux quatre banques/page et une matrice de corrélation `F_RX ± 38,550/38,850 MHz` ont été ajoutés. **N'ayant pas de trace OEM native complète pour plusieurs fréquences dans le dépôt, le mapping LO/IF et les séquences RX/TX ne sont pas encore qualifiés.** [Voir l'étude QA4818N](hardware/QA4818N_RECONSTRUCTION_REGISTRES_PLL_CHAINES_RX_TX.md).
