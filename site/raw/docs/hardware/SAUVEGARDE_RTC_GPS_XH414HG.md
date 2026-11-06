# Deux sauvegardes RTC et GPS sur le PCB CPU : XH414HG et variantes

**Etat au 05/11/2026.** Cible : D578UV PRO GD32 V1.21; architecture D578 historique comme comparaison. L'utilisateur a signale des elements de sauvegarde sur la carte CPU. La photographie precise et les marquages de ses exemplaires PRO/PLUS ne sont pas encore archives. **Ne pas substituer une reference de remplacement sans mesure et identification du boitier reel.**

## 1. Deux composants, deux fonctions

| Element | Localisation dans l'etude VK7ZJA | Charge sauvegardee | Preuve | Reste a verifier sur les postes du projet |
| --- | --- | --- | --- | --- |
| RTC BACKUP | Face arriere du PCB afficheur/MCU, pres du connecteur de nappe | Domaine d'horloge temps reel GD32 | Photo et explication de VK7ZJA / IK8JHL | Continuite vers **GD32 VBAT, broche physique 6**, circuit de charge et diode |
| GPS HOT START | Face avant du meme PCB, entre les deux potentiometres de volume | Maintien du contexte GNSS (RTC/SRAM du GPS) | VK7ZJA / IK8JHL | Continuite vers l'entree **VBAT du module ATGM336H** et orientation des contacts |

La reference **XH414HG IV01E** est indiquee dans l'edition 2023 de l'etude VK7ZJA pour **les deux elements**. Elle n'est **pas** une mesure faite sur nos deux cartes. L'edition ancienne du meme guide proposait **MS412** comme piece de remplacement pour le RTC : c'est une reference DIFFERENTE, et il faut garder l'historique des editions et versions, pas transformer ces deux references en equivalents.

## 2. Nature exacte du XH414HG

Seiko Instruments commercialise le **XH414HG** dans la gamme **XH-HG Capacitor**. Ce n'est pas une pile primaire CR2032 et **pas une cellule lithium standard** : c'est un condensateur de sauvegarde rechargeable, a forte capacite pour son volume.

| Caracteristique fabricant | Valeur |
| --- | --- |
| Famille | XH-HG capacitor, reference XH414HG |
| Capacite nominale | **0,08 F** |
| Tension maximale d'utilisation | **3,3 V** |
| Diametre | **4,8 mm** |
| Hauteur | **1,4 mm** |
| Impedance interne typique de catalogue | **100 ohms** (methode AC specifiee) |
| Usage prevu | Sauvegarde de memoire et d'horloge |

La notice fabricant deconseille une charge avec ondulation excessive et donne des conditions de charge specifiques. **Ne pas charger directement ces composants avec une alimentation de laboratoire** et ne pas les remplacer par une CR2032 sans analyser le circuit de charge. Un MS412 et un XH414HG ne sont pas substituables sur le seul critere de leur taille.

## 3. Liaison au GD32 et au GPS, niveau de preuve

### RTC

- **Fait de datasheet :** GD32F303VKT6 LQFP100, pin **6 = VBAT**. Pins **7 = PC13/TAMPER-RTC**, **8 = PC14/OSC32_IN**, **9 = PC15/OSC32_OUT**. Pin **14 = NRST**. Ce sont les fonctions disponibles du MCU, pas un relevage de pistes du D578.
- **Source externe sur radio D578 :** la sauvegarde situee a l'arriere est assignee a l'horloge RTC.
- **Hypothese de connexion :** batterie/condensateur RTC -> elements de limitation/isolation -> VBAT (pin 6). Circuit et chemins **inconnus** ; aucune GPIO n'est affectee.
- **Indicateurs de panne a comparer :** date/heure perdues, message RTC ERROR / RTC not run, impossibilite de conserver l'heure. Ces symptomes ne prouvent pas a eux seuls une panne du condensateur.

### GPS

- **Fait de datasheet (module ATGM336H-5N, a confronter a la sous-version montee) :** entree VBAT dediee a la sauvegarde RTC/SRAM, avec domaine mentionne 1,5 a 3,6 V. **La numerotation de broche 6 du module -5N ne doit pas etre transposee a toutes les sous-versions ATGM336H sans verifier le footprint**.
- **Source D578 :** second element en facade entre les volumes, affecte au demarrage GNSS a chaud.
- **Hypothese de connexion :** sauvegarde GPS -> reseau de charge -> VBAT du module ; mesurer la continute sans injection.
- Une acquisition GPS lente peut aussi provenir de l'antenne, du firmware, du temps depuis le dernier fix, de la position ou du bruit RF : ne pas la diagnostiquer par defaut comme une panne de sauvegarde.

## 4. Observation et qualification sans depannage destructif

1. Photographier les deux faces du PCB CPU, identifier exactement les inscriptions et la polarite eventuelle des composants, preciser PRO/PLUS et revision.
2. Mesurer **hors tension, alimentation debranchee** la tension aux bornes avec un instrument a entree haute impedance ; relever la duree depuis la derniere mise sous tension.
3. Etablir la continuite du composant RTC vers VBAT pin 6 du GD32 et du composant GPS vers la piste de sauvegarde du GNSS. Ne pas utiliser de test de continuite si une tension residuelle est presente.
4. Si autorise, mesurer passivement les tensions avant/apres alimentation du poste, y compris poste logiquement eteint mais alimente ; **aucun pontage ni injection**.
5. Tester la conservation de l'heure et la difference entre premier fix GPS a froid / redemarrage rapide, puis consigner mesures et temperatures. Ces essais ne remplacent pas l'identification electrique.
6. Ajouter photo et captures au manifeste `hardware/photos/` avec la variante et la date.

## 5. Consequences pour un firmware alternatif

- Le RTC doit avoir un driver independant du GPS, avec detection de donnees invalides et politique explicite d'initialisation UTC.
- Le GNSS peut perdre son contexte de hot start alors que le RTC systeme garde l'heure, et inversement.
- Aucun code du firmware ne doit traiter l'alimentation VBAT comme une GPIO commutable sans schema.
- L'absence de validation du RTC/heure rend une propagation TLE/Doppler non fiable ; le mode satellite doit refuser de calculer des corrections sur une date inconnue.
- Des tests de veille/power doivent verifier la continute d'alimentation des sauvegardes, sans conclure a l'autonomie exacte depuis une simple capacite nominale de 0,08 F.

## 6. Sources et differences de revision

1. VK7ZJA / IK8JHL, documentation 2023, deux elements XH414HG IV01E et localisations : <https://www.radiomanual.info/schemi/Vari/Alinco_DR-MD500_DR-MD520_AnyTone_AT-D578UV_mods_and_information_VK7ZJA_2023.pdf> ; miroir HTML : <https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php>.
2. Edition ancienne, remplacement RTC MS412 : <https://www.theweeks.org/tmp/FILES/Anytone-Mods/578mods.htm>. **La proposition MS412 date d'une autre edition, ne pas la fusionner avec XH414HG.**
3. Seiko Instruments, Micro Battery Product Catalogue 2007-2008, pages XH-HG Capacitor / XH414HG : <https://www.infinite-electronics.kr/datasheet/3c-XH414HG-IV01E.pdf>.
4. GigaDevice, GD32F303xx Datasheet, section LQFP100 pin definitions : <https://www.gd32mcu.com/data/documents/datasheet/GD32F303xx_Datasheet_Rev3.0.pdf>.
5. ATGM336H-5N reference de famille : consulter la fiche fabricant correspondant au marquage reel avant d'attribuer VBAT.
6. Vue photographique commerciale annotee des deux emplacements : <https://moonrakeronline.com/eu/anytone-replacement-battery-for-at-d578uv-sm3r3703t01u>. Photographies externes liees, non recopiees dans le depot public.

**Regle de preuve :** confirmation utilisateur de composants de sauvegarde sur la carte CPU ; nature exacte XH414HG, nombre et fonctions etayes par la documentation externe sur le D578 historique ; pas de preuve de continuite sur les cartes PRO/PLUS inspectees actuellement.
