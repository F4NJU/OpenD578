# Décisions et chronologie technique du portage satellite D578

## Contrat logiciel imposé par l'utilisateur

Le poste cible est l'**AnyTone D578UV PRO branche GD32**, avec **GD_Ver 1.21**. La branche AT32, le D578UVII PLUS V2.x et les firmwares D878 ne doivent pas être confondus avec cette cible. Deux postes D578UV PRO ont été signalés, dont un autre en V1.15c. La cible a été ouverte et identifiée comme GD32F303VKT6.

**[UTILISATEUR]** Le firmware doit rester léger, simple, fluide et stable, conserver la FM, le DMR, le GPS/APRS, les mémoires, le CPS, les fréquences/offsets, le CTCSS/DCS, les données et la calibration. Aucun module satellite ne doit détourner une émission, introduire une deuxième tâche, monopoliser l'interface, réécrire la NAND ou imposer un ordonnanceur supplémentaire.

**[UTILISATEUR]** Le code satellite doit être intégré **de façon additive** si possible. Les retraits de fonctions sont autorisés en dernier recours seulement, avec analyse des dépendances : enregistrement vocal (Record), 2Tone/5Tone, Work Alone, Weather Alarm, réception FM commerciale, roaming DMR, CH Ranging, Scrambler, Digital Encryption. Ne pas supprimer ces fonctions par simple suppression de chaînes. Ne pas toucher aux fonctions critiques même indirectement. La conception tient compte des instabilités signalées sur l'ancien mode satellite de l'AnyTone D878.

**[UTILISATEUR]** L'écran satellite doit appartenir au rendu OEM, avec exclusivité sur l'afficheur, sans collision de commandes LCD. Reproduire exactement les pixels OpenGD77 n'est pas un objectif. Réutiliser les polices et dimensions natives de l'AnyTone.

**[UTILISATEUR]** Fonction déclenchée idéalement par une **mémoire analogique FM normale dont le nom commence par `SAT:`**, par exemple `SAT:SO50`, les champs RX/TX et CTCSS étant définis par le CPS. Activer le Doppler au changement de canal et présenter une interface courte de type fenêtre APRS, si l'API OEM le permet. Aucun suivi ne doit s'activer sur un canal DMR ou une éphéméride absente. Le projet ne doit pas écrire le Doppler dans la NAND/codeplug.

La variation de fréquence en émission a été discutée, mais la règle conservatrice du développement est : **aucun changement TX pendant PTT ou TX actif**, ni lorsque l'état est inconnu; la vitesse réelle de reprogrammation et le pas minimal du synthétiseur n'ont pas été qualifiés. Une émission ne doit pas basculer de fréquence sans contrôle RF OEM.

## Chronologie et jalons, sans requalification indue

| Phases / dates | Contenu vérifiable ou rapporté | Limite |
|---|---|---|
| 1-8, 01/11-02/11 | Comparaison V1.20, repérage menus/handlers, premiers composants passages à la demande OpenGD77. Phase3: 106 libellés et 231 xrefs. | Archives initiales fragmentaires. |
| 9-14 | PLAN13 comparé à OpenGD77 (30/30 AOS/LOS sur vecteurs), UI simulee et cache NAND RO (50 000 consultations pour une lecture en simulation). | Aucun lien matériel. |
| 15-26 | UI/RTOS, NAND/Flash, tables TBB/TBH, dépendances des menus et options. Phase26: 43 dispatchs TBB/TBH résolus dans chacune de deux images, 78 tables statiques, ~186 500 candidats, 2 372 points d'entrée candidats, 133 tests Python, 18 modules ARM 16 503 o non liés. | Les candidats statiques ne sont pas une couverture dynamique. |
| 27-32, 02/11 | UI et garde RF simulés, API hôte, analyse CPS et enveloppes update, observation USB de deux radios; correction live du callback busy/PTT phase32. | Aucune API OEM RX/TX certifiée. |
| 33-35, 02-03/11 | Liaison SWD réelle, deux captures boot 24 Kio, deux captures Flash 3 Mio identiques, égalité de l'application OEM V1.21 avec CDD officielle, carte des 896 pages Flash. | Lecture n'établit pas récupération/flashage sûr. |
| 36-40, 03/11 | BOOT/FMC, copie Flash haute, lease LCD en simulation, budget PLAN13 8 itérations/100 ms, plafond UI 8 commandes, pile statique individuelle réduite; 21 modules 19 129 o et 288 o BSS non liés. | FPU/libm externes et piles RTOS non qualifiés. |
| 41-44, 03/11 | Worker UI et sémaphore OEM RAM 0x20000128 avec guards RTOS; 37 acquisitions et 38 releases au niveau statique, paires et règles contrôlées. | Pas de droit de hook ni d'ABI exclusive certifiée. |
| 45-47 logiciel, 03/11 | Chaînes RF/BCD, écritures VFO RAM, exclusions de faux setters, pilote série, appels NAND, 21 tests phase47. | Setter RX/TX et état PTT toujours non prouvés. |
| 46 NAND forensique, 03/11 | Dump NAND 264 Mio entrelacé + 256 Mio main + 8 Mio auxiliaires + 128 Kio statuts ECC. Cartographie et erreurs ECC. | Image non garantie restaurable à cause des ECC 0x20. |
| 48-52, 03/11 | RF/NAND, encodeur/PTT/VFO, simulation de RX/TX Doppler et restauration. Phase52: 22 modules, 20 039 o non liés, 288 BSS, 28 externes. | Aucune connexion OEM. |
| 53, 03/11 | Audit autonome des adresses et hashes V1.21, 12 tests unitaires contenus dans l'archive récupérée, exécutés avec succès; pas de firmware. | Reste un outil de recherche statique. |
| 54-59, 03/11 | Pré-intégrations ARM non flashables, softfloat, prévisualisation ROM, sans preuve de lien OEM. Archives listées mais non exportées. | Les noms ZIP ne démontrent pas le comportement du code non lu. |
| 60 EXP06, 03/11 | Détection `SAT:ID`, sélection TLE (25 slots), modèle popup, 30 sources ARM liées, softfloat, 14 680 octets texte/constantes, BSS 288 o, aperçu à 0x080F0000. | Aucune image installable, aucun raccord RAM/LCD/RF/TLE. |
| SIM V1, 04/11 | Audit démarrage C et 94 432 octets SRAM initialisés, deux motifs A5/5A, indépendance du décodeur. | Ce n'est pas une mesure RAM en charge. |
| SIM V2, 04/11 | Reset/horloge RCU/PLL, GPIO/AFIO, SysTick; arrêt sur PA15 demandé par lecture NAND 9F. | NAND non encore simulée. |
| SIM V3, 04/11 | Modèle NAND bit-série, lecture de vrais buffers, WFI/Power/EXTI/SysTick; arrêt ADC DMA. | ADC/LCD visuel/GPS/DMR non simulés. |

Le détail des phases anciennes figure dans les rapports textuels récupérés, en particulier `PASSATION_D578_SATELLITE_PHASE47_NAND_2026-11-03.txt` et les `RAPPORT_PHASE*.txt`. Plusieurs archives cumulatives contiennent le code réel, mais n'ont pas été matériellement exportées dans ce ZIP.

## Ne pas altérer les timings et protections déjà décidés

- PLAN13: budget 8 itérations/tranche, 100 ms entre tranches de calcul de passages, sans thread en plus.
- UI: budget 8 opérations de dessin/tranche pour la page sélectionnée, protection de génération et d'écran, acquittement propriétaire OEM.
- PTT/busy: vérifier un état **frais** juste avant toute proposition de modification RF; état inconnu = aucune commande.
- Canal `SAT:`: codeplug 64 octets, champ nom à +0x23 selon qdmr, mais **position du champ dans la représentation RAM OEM non prouvée**.
- L'utilisation de la fonction d'affichage APRS OEM à réception d'une trame est une piste de recherche; le slot précis et son ABI sont encore inconnus.
