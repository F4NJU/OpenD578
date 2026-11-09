# OpenD578 — reprise des inconnues IO par les instructions OEM

Jean-Philippe (F4EGM) — 9 novembre 2026 — révision 4.

## Contrat et résultat

Une liaison établie par analyse du firmware est retenue valide dans le projet. Aucune mesure de continuité n’est demandée pour la requalifier. Cela permet de figer le contrat logiciel : GPIO, sens, transaction, sélection et polarité. Une référence de composant, une destination analogique ou une action interne absente du code restent indiquées comme telles ; elles ne sont pas inventées.

Le tableau révisé comprend **86 lignes** : 80 GPIO, 2 signaux quartz principal, NRST, BOOT0 et les deux références ADC. Il retire les alimentations, masses, NC et numéros de pattes distantes. Sur ces 86 lignes, 70 sont classées « Validé par firmware », 8 ont une commande ou séquence partiellement attribuée, 2 conservent une fonction distante non résolue, 4 relèvent du brochage/connaissances projet et 2 des références ADC. Une liaison validée peut conserver une précision ouverte sur la référence du CI terminal.

Les 18 GPIO entièrement non attribuées de la version précédente ont toutes été réexaminées, ainsi que PC0, les bus DAC/tuner et le Bluetooth. Les commandes du SCT sont ici étudiées comme IO ; ce travail ne réintroduit pas le développement fonctionnel du DMR.

## Image et méthode

- Flash sauvegardée, 3 Mio, SHA-256 `e2f2483baf60e2bfcab656e25e949670713222591ef4d611d6089054819a750e`.
- Application PRO GD32 V1.21 : 1 020 300 octets à `0x08006000`, SHA-256 `02b2a3b56bd57c7ada581eb52b9b6f41c5d51aaec1b068d37585efd58dff9c9a`. Identité octet à octet vérifiée avec cette portion de la Flash.
- Instructions Thumb décodées et littéraux résolus. Appels directs aux primitives GPIO recherchés dans le premier Mio, bootloader inclus. Les références candidates sont fournies séparément ; ce balayage n’est pas une preuve de couverture complète des appels indirects ou accès directs MMIO.
- Les rapprochements sémantiques ci-dessous reposent sur la lecture des séquences et de leurs appelants, pas sur le seul nom d’une fonction du banc.
- Essais isolés des instructions OEM : 10 cas de wrappers booléens, une séquence DAC et sa correspondance des canaux ; 12 vérifications réussies. Ce sont des exécutions de routines isolées, pas un nouveau démarrage complet ni des mesures de délais électriques. Aucun accès au poste ni écriture de sauvegarde NAND.

## N1 — BH2226 : bus et numérotation corrigés

`0x0808A7C0` transmet quatre bits de commande puis huit bits de donnée, MSB-first. PA5 descend avant le mot et remonte pour le valider ; PB3 est l’horloge et PB4 les données. `0x0808A8A0` émet exactement les mots suivants, vérifiés par exécution :

`900 3FF FFF 800 C00 200 A00 600 E00 100` (hexadécimal).

Le début correspond à la sortie de veille du BH2226, au choix DAC pour les huit canaux puis au réglage des huit sorties. Cette concordance de protocole ET d’initialisation permet de retenir la liaison vers le H2226/BH2226 présent dans le projet.

**Correction de notre documentation précédente :** la table constructeur présente le sélecteur dans l’ordre D8,D9,D10,D11 ; le premier nibble transmis est observé dans l’ordre D11,D10,D9,D8. Pour retrouver la désignation du canal, renverser les quatre bits du nibble fil. La donnée de huit bits conserve son ordre normal.

| Nibble sur le fil | Sortie du BH2226 | Wrapper OEM |
| --- | --- | --- |
| 8 | DA1 — rétroéclairage LCD | `0x0808A8F4` |
| 4 | DA2 | `0x0808A956` |
| C | DA3 | `0x0808A902` |
| 2 | DA4 | `0x0808A910` |
| A | DA5 | `0x0808A91E` |
| 6 | DA6 | `0x0808A92C` |
| E | DA7 | `0x0808A948` |
| 1 | DA8 | `0x0808A93A` |

Le menu de luminosité appelle DA1 à `0x0808A9B6`. Les autres sorties sont programmées par les routines de calibration/routage, notamment `0x080649BC`, `0x08064B12`, `0x080655DC` et `0x08065626`. Leurs destinations analogiques exactes ne sont pas toutes déduites. Le registre historique `lighting[8]` du banc reste un code de commande, et ne signifie pas « DA8 ». Aucun code du banc n’a été modifié dans ce livrable.

Cette inversion d’ordre des bits n’est pas un inverseur électrique.

Source fabricant : [ROHM BH2226FV/BH2226F, Rev.001, figure 15 et Channel Settings](https://www.mouser.com/datasheet/2/348/bh2226fv-e-1807393.pdf), pages 8–9 imprimées. La référence exacte des variantes de boîtier s’appuie aussi sur l’identification H2226/SSOP du projet.

## N2 — PB6/PB7 : l’écart SDA/SCL est tranché

Dans `0x08088876`, le bit à émettre commande le masque `0x0040` de GPIOB. Le masque `0x0080` est ensuite monté et descendu pour l’horloge. Dans `0x080888EE`, les bits reçus sont lus sur `0x0040` pendant ces impulsions.

**PB6=SDA ; PB7=SCL.** L’ancien CSV donnant l’inverse est corrigé. Cette attribution ne dépend plus du décodeur FmI2c du banc. Le firmware contient aussi des routines de bus logiciel à `0x0808D244` et suivantes utilisant la même paire ; une routine générique ne signifie pas la présence d’un nouvel esclave.

## N3 — Bluetooth sur PC10/PC11

`0x080777D0` configure PC10 en fonction alternative de sortie, PC11 en entrée et le périphérique UART3 `0x40004C00`. Le débit est passé dans R0 ; les appelants utilisent notamment `0x1C200`, soit 115200 bit/s. Les séquences de dialogue Bluetooth et commandes AT déjà documentées passent par ce pilote.

La destination Bluetooth est retenue valide : PC10 vers RX du module et PC11 depuis TX. Le nom ET12 désigne le protocole/module de cette analyse ; il n’identifie pas le SoC sous le blindage.

## N4 — PE2 : connexion USB

`0x0809B370` configure PE2 en sortie. `0x0809B396` l’établit à 1 pour argument 1, à 0 autrement. Les callbacks à `0x080B06F8` et `0x080B0708` appellent respectivement ces états lors de la connexion et de la déconnexion USB. Le bootloader possède la commande équivalente à `0x080021B6/0x080021C0`.

La fonction de connexion logique USB est validée. Le firmware ne distingue pas le montage exact du pull-up et un transistor éventuel. Deux essais OEM isolés confirment le sens de la commande ; aucun inverseur discret n’est affirmé.

## N5 — PE5 et driver série des voyants

Le bootloader abaisse PE5 à `0x080040CE`, puis la remonte dans `0x080042AE` avant l’usage du driver de huit bits `0x080042BA`. L’application configure PE3/PE4/PE5 et place PE5 à 1 à `0x0808A4CE`, avant l’émission via `0x0808A3D6`.

PE3=DATA et PE4=CLOCK sont validées ; PE5 est la commande commune de libération du driver. Un reset actif bas est compatible avec la séquence, mais le code ne sépare pas RESET# et ENABLE, ni n’identifie de façon unique un 74HC164 ou un autre composant. PE5 reste donc partiellement attribuée plutôt que rattachée arbitrairement à une référence.

## N6 — PE6, PC4, PD0 et DAC0 : commutation TX

PE6 est abaissée dans les chemins d’arrêt TX et de veille, et montée dans les fenêtres d’émission (`0x080718BA…0x08071922`, `0x0808CB18…0x0808CBBA`). PD0 est lu pour autoriser/couper la fenêtre ; le traitement de temporisation à `0x08006A2C` coupe PE6 et PC4 lorsque la condition PD0 disparaît. Le DAC0 reçoit aussi les valeurs de consigne TX à travers `0x0808B73C`.

`0x0808A2C4` commande PC4 sans inversion logicielle. Cette sortie participe à la commutation RF auxiliaire selon des états SCT et une comparaison de fréquences à la frontière 300 MHz (unité OEM). Cela ne suffit pas à choisir « commutateur d’antenne », « polarisation PA » ou un étage spécifique. La commande PC4 est validée mais sa fonction terminale reste partielle.

PD0 est retenue comme synchronisation du sous-ensemble SCT ; l’attribution nominale à une PIO précise n’est pas nécessaire au contrat GPIO et n’est pas inventée. L’étude des IO n’implique pas validation des échanges DMR.

## N7 — PE0, PC3 et PE15 : séquences de marche / veille

PE0 est mise à 1 après démarrage (`0x080066C2`) et dans les chemins de maintien ; elle est abaissée dans les chemins d’extinction (`0x08089B82`, `0x0808A11A`) après arrêt RF/audio. La commande logique marche/maintien est donc retenue. Cela ne signifie pas que le MCU alimenté par USB/SWD perd son alimentation.

PC3 est configurée et mise à 1 dans le bootloader (`0x080040D6`) et l’application (`0x0808A1A8`). Ces écritures fixes ne permettent pas d’en désigner la destination.

PE15 est montée pendant l’initialisation (`0x0808A2B8`), puis abaissée au démarrage (`0x080066D2`) et dans un chemin de veille (`0x08089F6A`). La proximité d’un dialogue Bluetooth dans un appelant ne constitue pas une preuve que PE15 est l’alimentation ou le reset du Bluetooth. Destination laissée non résolue.

## N8 — lignes de démarrage et commandes SCT3258

Les initialisations `0x08092E98`, `0x08092F06`, `0x0809306C` et `0x080930EA` appartiennent au chemin de démarrage HPI/SCT. La routine `0x080930FA` lit PD5 et inverse le résultat booléen : bas devient « disponible ».

| Ligne | Observation OEM | Attribution retenue |
| --- | --- | --- |
| PA8 | 0 à l’arrêt, 1 avant reset/bootstrap | Activation du sous-ensemble HPI/SCT ; entrée terminale exacte partielle |
| PC6 | 0 à l’arrêt, 1 avant séquence PD6 | Activation du sous-ensemble SCT ; signal terminal exact partiel |
| PC12 | Sortie basse au boot ; `0x0809304C` la passe en entrée pull-down après bootstrap | Strap de démarrage imposé bas puis libéré ; choix de mode interne partiel |
| PD6 | 1, attente, 0 ; bootstrap `0x080935B0` ; 1 via `0x080930EA` | Reset/maintien du cœur pendant chargement puis libération ; aucun inverseur physique affirmé |
| PD1 | Wrapper `0x0809364C`, impulsion 1→0 avant réponse 0x15 | Requête hôte auxiliaire SCT ; nom terminal IRQ/PIO exact partiel |
| PC7 | Wrapper `0x08093666`, transitions dans `0x080A65BC` et `0x080A8424` | Commande auxiliaire de mode/validation SCT ; action interne partielle |
| PD7 | Wrapper `0x08093A5E`, impulsion 1→0 dans `0x080A58F6` | Requête auxiliaire dans une séquence de réinitialisation logique ; action interne partielle |

Les trois wrappers booléens PD1/PC7/PD7 ont été exécutés avec arguments 0 et 1 ; sorties conformes dans les six cas. Les noms PA8/PC6/PC12 ne sont plus de simples copies d’une carte D868 : les instructions D578 sont fournies. Le rôle électronique plus précis reste distinct de cette preuve de séquence.

## N9 — quartz RTC PC14/PC15

Dans `0x0808CF64`, le chemin d’initialisation appelle `0x08008BF8` avec argument 1 : cette primitive écrit l’activation LXTAL sans bypass dans RCU_BDCTL. Le programme attend le drapeau de stabilisation, appelle `0x08008C30` avec `0x100` pour la source RTC, active RTC puis règle le prédiviseur à `0x7FFF`.

Il s’agit bien de l’oscillateur externe RTC à 32,768 kHz, donc PC14/OSC32_IN et PC15/OSC32_OUT. La conclusion vient de l’initialisation OEM ; la valeur retenue par le modèle de sauvegarde n’est pas utilisée comme seule preuve. L’initialisation semblable à `0x08074760` recoupe ce choix.

## N10 — PC0/ADC10 : audio de réception, pas attribution ROS

La séquence ADC/DMA connue est `[6,8,9,10,11,12,15]` vers `0x2000DA76`. Le quatrième demi-mot, à +6, correspond donc à ADC10/PC0.

`0x0800A31A` et `0x0800C704` prélèvent les bits 11:4 de cet échantillon et les déposent dans un tampon de signalisation. `0x0800AD54` détecte les franchissements alternés des seuils `0x760` et `0x8A0`, mémorise les intervalles et alimente le traitement temporel. L’interruption de timer à `0x08006AD8` ne distribue ces traitements que lorsque l’état TX est nul et selon le mode de décodeur 1/2/3.

Le rôle d’acquisition audio pour décodeurs de réception est retenu. Le CI ou AOP qui fournit cette tension reste sans identité déduite. Cette observation corrige la piste qui consistait à attribuer cette entrée au ROS sur la seule présence de seuils ; elle ne conclut pas à l’absence d’une protection ROS ailleurs dans le poste.

## N11 — limite du premier index de recherche

Le premier index listait les appels de lecture/écriture GPIO et les valeurs immédiates de masques. Il ne résolvait pas le contenu des structures d’initialisation passées sur la pile. Il n’avait donc pas identifié la configuration PB9 en fonction alternative. La mention précédente « aucun usage identifié » était un résultat incomplet de cette recherche, pas une preuve d’inutilisation.

## N12 — PB9 résolue : sortie PWM audio TIMER3_CH3

La vérification complémentaire identifie :

- `0x0808C7B6` : masque GPIO `0x0200` sur GPIOB, configuration fonction alternative push-pull ; le nibble de PB9 devient `0xB`.
- `0x0808C796` : même masque, configuration analogique ; le nibble revient à `0x0`.
- `0x0808C7D6` : initialisation du timer à `0x40000800` et du canal de sortie dont la valeur de comparaison est à `+0x40`.
- `0x0808C834` : écrit son argument en demi-mot à `0x40000840`, valeur de comparaison TIMER3_CH3CV.
- `0x0800C016…0x0800C056` : combine deux tables périodiques et envoie l’échantillon résultant à cette primitive, ce qui établit l’usage de génération audio/tonalités par PWM.
- `0x080925E0` : activation PB9 dans le générateur de séquences sonores ; `0x080921BE` et `0x080924C6` la neutralisent.
- `0x08067240` : activation PB9 dans le chemin de signalisation APRS, avant l’appel du modulateur natif `0x08066306`.

La fiche GD32F303xx Rev3.3, table LQFP100 page 35, confirme PB9 = TIMER3_CH3 ; la carte mémoire page 18 confirme TIMER3 à `0x40000800`. La conclusion est fondée sur la configuration effectivement programmée par l’OEM, pas sur une simple fonction disponible dans la datasheet.

**PB9 est utilisée en sortie.** Aucune lecture électrique de son niveau GPIO n’a été identifiée dans le bootloader ni dans l’application. Une sortie de timer n’a pas besoin d’être lue par le CPU pour fonctionner. Dans le bootloader étudié, aucun usage propre de PB9 n’a été identifié. Les lectures des registres de configuration lors des initialisations ne sont pas une acquisition de son niveau.

Six essais isolés exécutant les instructions OEM confirment les deux modes PB9 et les écritures de comparaison pour 0, 1, 127 et 255. Détails : `preuves/PB9_VALIDATION_OEM.json`. L’étage analogique situé après cette sortie (filtrage/mixage) reste sans référence de CI déduite.

PC3 et PE15 restent sans destination unique. Des commandes d’activation de rail, de maintien ou de veille sont compatibles avec leurs séquences. Le firmware ne permet pas encore de choisir cette explication plutôt qu’une autre entrée de contrôle de périphérique. Aucun inverseur discret n’est identifié.

## Liaisons indirectes conservées

Les HP microphone, ventilateur et routages MAIN/SUB sont commandés par des bits des banques RF ; ils ne consomment pas nécessairement un GPIO GD32 chacun. Les LED/clavier du micro passent par son contrôleur sur USART0. Le contrôle codec TLV320AIC3204 passe par SCT/HPI. Les flux analogiques MIC et SP+/SP− ne deviennent pas des signaux UART. Ces connaissances restent valides ; les GPIO non attribuées ne sont pas remplies avec des liaisons I²S/I²C inventées.

## Fichiers de preuve

`preuves/` contient le désassemblage ciblé, les références candidates, la validation isolée JSON et deux scripts reproductibles. Les scripts attendent les sauvegardes du projet aux chemins indiqués dans leur en-tête ; les binaires et la NAND de l’utilisateur ne sont pas ajoutés à cette archive. Dépendances de l’analyse : Capstone 5 et Unicorn 2. Les sources historiques S1–S16 restent dans le Markdown du tableau. Les scripts de recherche produisent des candidats ; ils ne remplacent pas la lecture des séquences ci-dessus.

## N13 — comparaison PLUS V2.08

Voir COMPARAISON_PRO_PLUS.md et COMPARAISON_IO_PRO_PLUS.csv. Les deux pilotes I²C radio (0x10 et 0x35) sur PB6/PB7 y sont désormais distingués. PC3 et PE15 restent sans destination résolue après comparaison.


## N14 — APRS RX du PLUS

Carte BT+APRS BHT_BOARD identifiée, PC10/PC11 UART3 partagé à 115200 bit/s ; réception +APRS: suivie d’AX.25. 13 essais OEM isolés réussis. Voir APRS_RX_PLUS.md pour les adresses, preuves et la liaison RF/audio vers BHT restant non attribuée.
