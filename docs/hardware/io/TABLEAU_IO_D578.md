# OpenD578 — liaisons GD32F303VKT6 résolues par firmware

Jean-Philippe (F4EGM) — 9 novembre 2026 — révision 5.

Périmètre : **D578UV PRO GD32 V1.21 et bootloader sauvegardé ; comparaison PLUS GD32 V2.08 et carte BT+APRS V2.00**. 86 signaux : les 80 GPIO, OSC_IN/OUT, NRST, BOOT0 et VREF+/VREF−. Les autres alimentations, masses et NC sont retirés. La colonne de numéro de patte du circuit distant est supprimée.

**Règle de validation retenue : une liaison fonctionnellement établie par les instructions OEM est validée pour le projet et ne demande pas de contrôle de continuité supplémentaire.** La colonne « Précision restante » ne remet pas en cause ces liaisons ; elle indique seulement ce que le code ne nomme pas, comme la référence d’un transistor ou d’un silicium gratté. Une commande localisée sans rôle suffisamment identifié reste partielle.

Les niveaux indiqués sont vus du GD32. La polarité fonctionnelle n’établit pas à elle seule la présence d’un inverseur discret : une entrée active basse du CI produit la même observation. Aucun inverseur physique n’est ajouté sans indice qui permette de le distinguer.

## Résultats de la reprise

- BH2226 : PA5=CSB, PB3=CLK, PB4=DI, identifiés par le format ET la séquence complète d’initialisation. Le code du rétroéclairage est `0x8` sur le fil, mais il désigne **DA1**, pas DA8.
- PB6=SDA et PB7=SCL du tuner : correction confirmée directement dans les instructions OEM, plus seulement par le décodeur du banc.
- PC10/PC11 : UART3 du Bluetooth, partagé avec la carte BT+APRS du PLUS ; les trames APRS arrivent sur PC11 avec +APRS:. Voir APRS_RX_PLUS.md (N14). PE2 : connexion USB.
- PC14/PC15 : quartz RTC LXTAL ; PC0/ADC10 : acquisition audio de réception utilisée par les décodeurs de signalisation.
- Comparaison PLUS V2.08 : mêmes signatures pour les 570 appels directs GPIO indexés ; pilote AM/FM à 0x35 ajouté sur PB6/PB7. Voir COMPARAISON_PRO_PLUS.md (N13).
- Les commandes de marche, TX et SCT auparavant absentes sont désormais documentées avec leurs adresses et séquences.
- PC3 et PE15 conservent une destination/usage non résolu. Certaines commandes SCT sont localisées mais leur nom terminal exact et leur action interne restent partiels. Aucune de ces lignes n’est déclarée libre.

## Tableau des signaux utiles

Le HTML contient le tableau complet filtrable. Le CSV utilise le séparateur point-virgule et l’UTF-8 avec BOM. Les adresses servent à reproduire l’analyse V1.21, pas à définir une API du futur firmware libre.

### Port A

| Patte GD32 | Signal GD32 | Type de liaison | Sens côté MCU | Circuit / bloc distant | Fonction du signal distant | Polarité / séquence | Validation | Précision restante | Preuves |
|---|---|---|---|---|---|---|---|---|---|
| 23 | PA0 | GPIO + réveil EXTI0 | Entrée | Bouton Power | Contact actif bas — Demande marche/arrêt ; ne coupe pas directement l’alimentation | Voir fonction | Validé par firmware |  | S2; S8 |
| 24 | PA1 | GPIO | Entrée | Appui du codeur | Contact actif bas — Validation / appui du bouton rotatif | Voir fonction | Validé par firmware |  | S2 |
| 25 | PA2 | USART1 TX, AF sans remap observé | Sortie | Module GNSS ATGM336H | RXD du module — Envoi des commandes au GPS | USART1 sans remap ; UART non inversé côté MCU | Validé par firmware |  | S1; S8; S9 |
| 26 | PA3 | USART1 RX, AF sans remap observé | Entrée | Module GNSS ATGM336H | TXD du module — Réception NMEA et événements GPS | USART1 sans remap ; UART non inversé côté MCU | Validé par firmware |  | S1; S8; S9 |
| 29 | PA4 | Analogique DAC0_OUT0 | Sortie analogique | Chaîne de consigne de puissance TX, étage intermédiaire non identifié | Entrée de consigne analogique — Consigne numérique DAC observée en TX VHF/UHF ; destination analogique à tracer | Voir fonction | Validé par firmware | Consigne TX validée ; pas d’affectation directe à une grille de PA ni de conversion watts inventée | S1; S8; S11 |
| 30 | PA5 | Série GPIO 12 bits | Sortie | ROHM BH2226FV (H2226) | CSB : sélection et validation des huit sorties DAC | 0 pendant transfert ; front montant valide | Validé par firmware |  | N1; S7 |
| 31 | PA6 | ADC0_IN6 | Entrée analogique | Chaîne de mesure thermique, capteur non identifié | Sortie du capteur / réseau de conditionnement — Mesure utilisée par la commande du ventilateur | Voir fonction | Validé par firmware |  | S1; S8; S11 |
| 32 | PA7 | GPIO, commande de coupure | Sortie | Chaîne mute HP du poste ; intermédiaire non identifié | Commande mute, haut=coupure — Ouvre/coupe la sortie audio du poste | 1 coupe le HP poste ; 0 ouvre | Validé par firmware | Commande mute validée ; référence de l’étage qui reçoit cette commande non déterminée | S2; S10 |
| 67 | PA8 | GPIO de démarrage SCT | Sortie | Sous-ensemble SCT3258 / interface HPI | Validation du sous-ensemble au démarrage ; désactivation à l’arrêt | 0 arrêt ; 1 avant séquence reset/chargement SCT | Partiel : activation SCT validée | Signal terminal exact (alimentation, buffer, enable) non départagé | N8 |
| 68 | PA9 | USART0 TX | Sortie | Microphone filaire via interface/connexion RJ | Réception série du microphone — Envoi commandes, états et voyants vers le micro | Voir fonction | Validé par firmware |  | S8; S12 |
| 69 | PA10 | USART0 RX | Entrée | Microphone filaire via interface/connexion RJ | Émission série du microphone — Réception clavier, PTT et acquittements du micro | Voir fonction | Validé par firmware |  | S8; S12 |
| 70 | PA11 | USB FS différentiel | Bidirectionnel | Connecteur USB et éventuel réseau de protection | USB D− — Données USB CDC/CPS | Voir fonction | Validé par firmware |  | S1; S12 |
| 71 | PA12 | USB FS différentiel | Bidirectionnel | Connecteur USB et éventuel réseau de protection | USB D+ — Données USB CDC/CPS | Voir fonction | Validé par firmware |  | S1; S12 |
| 72 | PA13 | SWDIO au debug ; série GPIO au fonctionnement | Bidirectionnel SWD / sortie audio | U2429, commande des volumes ; interface SWD au debug | SWDIO ; DATA U2429 — Débogage ou données de volume 11 bits | Voir fonction | Validé par firmware | Partage temporel : SWJ libéré par OEM ; volume ensuite. Liaison retenue validée. | S4; S8; S10; S13 |
| 76 | PA14 | SWCLK au debug ; série GPIO au fonctionnement | Entrée SWD / sortie audio | U2429, commande des volumes ; interface SWD au debug | SWCLK ; CLOCK U2429 — Horloge du debug ou du contrôleur de volume | Voir fonction | Validé par firmware | Partage temporel : SWJ libéré par OEM ; volume ensuite. Liaison retenue validée. | S4; S8; S10; S13 |
| 77 | PA15 | SPI logiciel NAND | Entrée | Toshiba/KIOXIA TC58CVG1S3HRAIG | SO/SO1 — Données sortantes de la NAND, simple/dual output | Voir fonction | Validé par firmware |  | S3; S5 |

### Port B

| Patte GD32 | Signal GD32 | Type de liaison | Sens côté MCU | Circuit / bloc distant | Fonction du signal distant | Polarité / séquence | Validation | Précision restante | Preuves |
|---|---|---|---|---|---|---|---|---|---|
| 35 | PB0 | ADC0_IN8, réseau résistif | Entrée analogique | Réseau résistif des boutons de façade | Nœud commun du réseau P1/P2/P3/MENU — Identification analogique des quatre touches | Voir fonction | Validé par firmware |  | S1; S2 |
| 36 | PB1 | ADC0_IN9, réseau résistif | Entrée analogique | Réseau résistif des boutons de façade | Nœud commun du réseau P4/P5/P6/EXIT — Identification analogique des quatre touches | Voir fonction | Validé par firmware |  | S1; S2 |
| 37 | PB2 | GPIO, sélection série RF | Sortie | Circuit RF de la banque 1 (famille QA4818N) | CS# / sélection active basse — Sélection de la banque logique 1 | CS actif bas | Validé par firmware | Banque identifiée fonctionnellement ; la référence exacte du silicium gratté n’est pas encodée par le logiciel | S6 |
| 47 | PB10 | GPIO, parallèle 8080 8 bits | Sortie | LCD HOLITECH FPC-HIB018A011-A1 | WR# — Strobe d’écriture, octet pris au front montant | Voir fonction | Validé par firmware |  | S15 |
| 48 | PB11 | GPIO, parallèle 8080 8 bits | Sortie | LCD HOLITECH FPC-HIB018A011-A1 | D/C ou A0 — 0=commande, 1=donnée | Voir fonction | Validé par firmware |  | S15 |
| 51 | PB12 | GPIO, parallèle 8080 8 bits | Sortie | LCD HOLITECH FPC-HIB018A011-A1 | RESET# — Réinitialisation matérielle active basse | Voir fonction | Validé par firmware |  | S15 |
| 52 | PB13 | GPIO, parallèle 8080 8 bits | Sortie | LCD HOLITECH FPC-HIB018A011-A1 | CS# — Sélection active basse de l’écran | Voir fonction | Validé par firmware |  | S15 |
| 53 | PB14 | SPI logiciel NAND | Sortie puis entrée en lecture dual | Toshiba/KIOXIA TC58CVG1S3HRAIG | SI/SO0 — Commandes/adresses vers NAND et donnée de poids 0 en lecture dual | Voir fonction | Validé par firmware |  | S3; S5 |
| 54 | PB15 | SPI logiciel NAND | Sortie | Toshiba/KIOXIA TC58CVG1S3HRAIG | SCK — Horloge du bus NAND | Voir fonction | Validé par firmware |  | S3; S5 |
| 89 | PB3 | Série GPIO partagée | Sortie | BH2226FV + quatre banques RF | CLK du BH2226 et SCLK RF | Échantillonnage sur front montant ; sélections distinctes | Validé par firmware |  | N1; S6; S7 |
| 90 | PB4 | Série GPIO partagée | Bidirectionnel RF / sortie DAC | BH2226FV + quatre banques RF | DI du BH2226 ; SDIO RF | 12 bits pour DAC ; 8+16 bits pour RF | Validé par firmware |  | N1; S6; S7 |
| 91 | PB5 | GPIO, sélection série RF | Sortie | Circuit RF de la banque 0 (famille QA4818N) | CS# / sélection active basse — Sélection de la banque logique 0 | CS actif bas | Validé par firmware | Banque identifiée fonctionnellement ; la référence exacte du silicium gratté n’est pas encodée par le logiciel | S6 |
| 92 | PB6 | I²C logiciel partagé | Bidirectionnel | Tuner RDA à 0x10 ; tuner AM/FM compatible KT0937-D8 à 0x35 selon équipement | SDA : données et acquittement des deux chemins de pilote | Donnée stabilisée pendant SCL haut ; émission/lecture MSB-first | Validé par firmware | Les deux pilotes sont compilés dans PRO et PLUS ; présence des esclaves dépend de l’équipement, pas du seul nom du firmware | N2; N13; S6 |
| 93 | PB7 | I²C logiciel partagé | Sortie | Tuner RDA à 0x10 ; tuner AM/FM compatible KT0937-D8 à 0x35 selon équipement | SCL : horloge des deux chemins de pilote | Impulsions sur masque PB7=0x0080 | Validé par firmware | Référence exacte du CI observé KT0905R/KT09S5R à réconcilier avec le pilote compatible KT0937-D8 | N2; N13; S6 |
| 95 | PB8 | SPI logiciel NAND | Sortie | Toshiba/KIOXIA TC58CVG1S3HRAIG | CS# — Sélection active basse de la NAND | Voir fonction | Validé par firmware |  | S3; S5 |
| 96 | PB9 | TIMER3_CH3, sortie PWM audio | Sortie | Chaîne audio de génération de tonalités et signalisation | Sortie PWM : rapport cyclique alimenté par les échantillons audio ; utilisée aussi dans le chemin APRS OEM | Mode AF push-pull pendant génération ; mode analogique quand neutralisée | Validé par firmware | Étage filtre/mixeur analogique terminal non identifié ; aucune lecture du niveau GPIO PB9 identifiée | N12; S1 |

### Port C

| Patte GD32 | Signal GD32 | Type de liaison | Sens côté MCU | Circuit / bloc distant | Fonction du signal distant | Polarité / séquence | Validation | Précision restante | Preuves |
|---|---|---|---|---|---|---|---|---|---|
| 7 | PC13 | GPIO, sélection série RF | Sortie | Circuit RF de la banque 2 (famille QA4818N) | CS# / sélection active basse — Sélection de la banque logique 2 | CS actif bas | Validé par firmware | Banque identifiée fonctionnellement ; la référence exacte du silicium gratté n’est pas encodée par le logiciel | S6 |
| 8 | PC14 | Oscillateur LXTAL RTC | Entrée oscillateur | Quartz RTC 32,768 kHz | OSC32_IN : entrée de l’oscillateur de sauvegarde | LXTAL activé sans bypass ; source RTC LXTAL ; prédiviseur 0x7FFF | Validé par firmware |  | N9; S1 |
| 9 | PC15 | Oscillateur LXTAL RTC | Sortie oscillateur | Quartz RTC 32,768 kHz | OSC32_OUT : sortie de l’oscillateur de sauvegarde | Même oscillateur que PC14 | Validé par firmware |  | N9; S1 |
| 15 | PC0 | ADC0_IN10 / DMA | Entrée analogique | Chaîne audio de réception vers décodeurs de signalisation | Acquisition audio pour échantillonnage 8 bits et détection de passages de seuils | Échantillon DMA index 3 ; seuils 0x760 / 0x8A0 ; traitement quand TX=0 | Validé par firmware | Le CI ou l’AOP qui fournit le signal n’est pas nommé par ces lectures | N10 |
| 16 | PC1 | ADC0_IN11 | Entrée analogique | Réseau de mesure de l’alimentation | Point milieu du réseau de conditionnement — Mesure d’alimentation et détection de tension basse | Voir fonction | Validé par firmware |  | S1; S8; S11 |
| 17 | PC2 | ADC0_IN12 | Entrée analogique | Potentiomètre de volume A (nom logique du banc) | Curseur — Acquisition du réglage de volume | Voir fonction | Validé par firmware |  | S1; S2 |
| 18 | PC3 | GPIO de sortie fixe | Sortie | Bloc distant non identifié | Sortie établie à 1 très tôt par bootloader et application | 1 dans 0x080040D6 et 0x0808A1C8 ; aucune commutation fonctionnelle identifiée | Non résolu : fonction distante | Impossible de choisir entre enable, maintien ou autre entrée fixe à partir de ces seules écritures | N7 |
| 33 | PC4 | GPIO de commande RF auxiliaire | Sortie | Chaîne RF, commutation complémentaire au TX | Porte auxiliaire, synchronisée avec les états TX/SCT et la condition de bande | 0 à init ; wrapper écrit 0/1 sans inversion logicielle | Partiel : commande TX/RF validée | Fonction terminale PA/commutateur/voie exacte non départagée | N6 |
| 34 | PC5 | ADC0_IN15 | Entrée analogique | Potentiomètre de volume B (nom logique du banc) | Curseur — Acquisition du réglage de volume | Voir fonction | Validé par firmware |  | S1; S2 |
| 63 | PC6 | GPIO de démarrage SCT | Sortie | Sous-ensemble SCT3258 | Commande d’activation maintenue pendant chargement et exécution | 0 arrêt ; 1 avant séquence PD6 et bootstrap | Partiel : activation SCT validée | Signal terminal exact non départagé | N8 |
| 64 | PC7 | GPIO de commande SCT | Sortie | SCT3258, commande auxiliaire | Ligne de mode/validation du protocole SCT | 0 au boot ; wrapper booléen ; 0 avant échange de démarrage, 1 dans séquence ultérieure | Partiel : commande SCT validée | Nom matériel et rôle exact de cette commande non distingués | N8 |
| 65 | PC8 | GPIO + EXTI8 | Entrée | Codeur rotatif | Phase/contact A, déclenchement — Front d’interruption de rotation | Voir fonction | Validé par firmware |  | S2 |
| 66 | PC9 | GPIO | Entrée | Codeur rotatif | Phase/contact B, direction — Direction lue au changement de phase | Voir fonction | Validé par firmware |  | S2 |
| 78 | PC10 | UART3 partagé Bluetooth / APRS RX | Sortie | PRO : module Bluetooth ; PLUS : carte BT+APRS / BHT_BOARD vers module Bluetooth | RX de la carte : commandes AT / échanges Bluetooth et BT+APRS | UART non inversé côté GD32 ; 115200 bit/s ; RX par interruption UART3 | Validé par firmware | Liaison série validée. Prélèvement RF/audio en amont de BHT et référence de son MCU non encore attribués ; lire APRS_RX_PLUS.md | N3; N14; S6 |
| 79 | PC11 | UART3 partagé Bluetooth / APRS RX | Entrée | PRO : module Bluetooth ; PLUS : carte BT+APRS / BHT_BOARD vers module Bluetooth | TX de la carte : réponses Bluetooth et trames APRS RX préfixées +APRS: | UART non inversé côté GD32 ; 115200 bit/s ; RX par interruption UART3 | Validé par firmware | Liaison série validée. Prélèvement RF/audio en amont de BHT et référence de son MCU non encore attribués ; lire APRS_RX_PLUS.md | N3; N14; S6 |
| 80 | PC12 | GPIO de strap au démarrage | Sortie puis entrée avec rappel bas | SCT3258, configuration de démarrage | Strap imposé bas pendant reset/chargement, puis libéré | Mode sortie 0 avant bootstrap ; entrée pull-down au passage en exécution | Partiel : strap SCT validé | Choix exact du mode SCT associé au strap non nommé | N8 |

### Port D

| Patte GD32 | Signal GD32 | Type de liaison | Sens côté MCU | Circuit / bloc distant | Fonction du signal distant | Polarité / séquence | Validation | Précision restante | Preuves |
|---|---|---|---|---|---|---|---|---|---|
| 55 | PD8 | GPIO, bus HPI parallèle 8 bits | Bidirectionnel | Sicomm SCT3258 | HPI DATA0 — Bit 0 des octets échangés avec le SCT | Voir fonction | Validé par firmware |  | S16 |
| 56 | PD9 | GPIO, bus HPI parallèle 8 bits | Bidirectionnel | Sicomm SCT3258 | HPI DATA1 — Bit 1 des octets échangés avec le SCT | Voir fonction | Validé par firmware |  | S16 |
| 57 | PD10 | GPIO, bus HPI parallèle 8 bits | Bidirectionnel | Sicomm SCT3258 | HPI DATA2 — Bit 2 des octets échangés avec le SCT | Voir fonction | Validé par firmware |  | S16 |
| 58 | PD11 | GPIO, bus HPI parallèle 8 bits | Bidirectionnel | Sicomm SCT3258 | HPI DATA3 — Bit 3 des octets échangés avec le SCT | Voir fonction | Validé par firmware |  | S16 |
| 59 | PD12 | GPIO, bus HPI parallèle 8 bits | Bidirectionnel | Sicomm SCT3258 | HPI DATA4 — Bit 4 des octets échangés avec le SCT | Voir fonction | Validé par firmware |  | S16 |
| 60 | PD13 | GPIO, bus HPI parallèle 8 bits | Bidirectionnel | Sicomm SCT3258 | HPI DATA5 — Bit 5 des octets échangés avec le SCT | Voir fonction | Validé par firmware |  | S16 |
| 61 | PD14 | GPIO, bus HPI parallèle 8 bits | Bidirectionnel | Sicomm SCT3258 | HPI DATA6 — Bit 6 des octets échangés avec le SCT | Voir fonction | Validé par firmware |  | S16 |
| 62 | PD15 | GPIO, bus HPI parallèle 8 bits | Bidirectionnel | Sicomm SCT3258 | HPI DATA7 — Bit 7 des octets échangés avec le SCT | Voir fonction | Validé par firmware |  | S16 |
| 81 | PD0 | GPIO de synchronisation SCT | Entrée | SCT3258, synchronisation des fenêtres TX | État de synchronisation lu pour autoriser/couper PE6, PC4 et DAC0 | Niveau 0 entraîne coupure dans chemin temporisé ; niveau 1 autorise la fenêtre | Validé par firmware | Association nominale à PIO3/TDMA non nécessaire au contrat GPIO ; pas de numéro PIO attribué | N6; N8 |
| 82 | PD1 | GPIO de requête SCT | Sortie | SCT3258, requête hôte auxiliaire | Impulsion de sollicitation avant attente de réponse du protocole SCT | 1 puis 0 ; requête suivie d’une attente de message 0x15 | Partiel : requête SCT validée | Nom terminal IRQ/PIO exact non donné | N8 |
| 83 | PD2 | GPIO, HPI parallèle asynchrone | Sortie | Sicomm SCT3258 | HCSN — Sélection / écriture / lecture / handshake HPI | Voir fonction | Validé par firmware |  | S16 |
| 84 | PD3 | GPIO, HPI parallèle asynchrone | Sortie | Sicomm SCT3258 | HWRN — Sélection / écriture / lecture / handshake HPI | Voir fonction | Validé par firmware |  | S16 |
| 85 | PD4 | GPIO, HPI parallèle asynchrone | Sortie | Sicomm SCT3258 | HRDN — Sélection / écriture / lecture / handshake HPI | Voir fonction | Validé par firmware |  | S16 |
| 86 | PD5 | GPIO HPI | Entrée | SCT3258 | HOBIB / indication de disponibilité HPI | Le getter renvoie 1 lorsque PD5 est bas | Validé par firmware |  | N8; S16 |
| 87 | PD6 | GPIO reset / exécution SCT | Sortie | SCT3258 | Commande de reset/maintien du cœur et libération après bootstrap | 1 puis 0 avant chargement ; maintenu 0 pendant bootstrap ; 1 ensuite | Validé par firmware | Reset/maintien déduit de la séquence ; ne démontre pas un inverseur discret | N8 |
| 88 | PD7 | GPIO de requête SCT | Sortie | SCT3258, commande auxiliaire de séquence | Impulsion dans une séquence de réinitialisation logique du protocole | 1 ; attente OEM 200 ; 0 | Partiel : requête SCT validée | Action interne exacte côté SCT non établie | N8 |

### Port E

| Patte GD32 | Signal GD32 | Type de liaison | Sens côté MCU | Circuit / bloc distant | Fonction du signal distant | Polarité / séquence | Validation | Précision restante | Preuves |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PE2 | GPIO USB | Sortie | Circuit de connexion USB, activation du pull-up | Connexion / déconnexion logique du périphérique USB | 1 dans callback connexion ; 0 dans callback déconnexion | Validé par firmware | Le code ne distingue pas un pull-up commuté directement d’un étage de commande | N4 |
| 2 | PE3 | Série GPIO 8 bits | Sortie pendant transfert | Registre / driver série des voyants | DATA : état des sorties, dont rouge et vert du voyant poste | LSB-first ; 0x46 repos, 0x4E vert, 0x56 rouge | Validé par firmware | Référence du driver non déterminée | N5; S2 |
| 3 | PE4 | Série GPIO 8 bits | Sortie pendant transfert | Registre / driver série des voyants | CLOCK : décalage des huit bits | Front montant, horloge ramenée basse en fin de mot | Validé par firmware | Référence du driver non déterminée | N5; S2 |
| 4 | PE5 | GPIO de commande du registre série | Sortie | Registre / driver série des voyants | Libération de la commande commune de reset/activation du driver | 0 dans initialisation bootloader ; 1 avant usage du driver série | Partiel : séquence validée | RESET# ou ENABLE : équivalents pour la séquence retrouvée ; référence du driver non déterminée | N5 |
| 5 | PE6 | GPIO de commande TX | Sortie | Chaîne de commutation émission RF | Porte TX matérielle commandée par PTT et temporisation SCT | 0 à l’arrêt TX ; 1 dans les fenêtres d’émission autorisées | Validé par firmware | L’étage de commande exact n’est pas nommé dans le firmware | N6 |
| 38 | PE7 | GPIO, parallèle 8080 8 bits | Sortie | LCD HOLITECH FPC-HIB018A011-A1 | D0 — Bit 0 de l’octet commande/paramètre/pixel | Voir fonction | Validé par firmware |  | S15 |
| 39 | PE8 | GPIO, parallèle 8080 8 bits | Sortie | LCD HOLITECH FPC-HIB018A011-A1 | D1 — Bit 1 de l’octet commande/paramètre/pixel | Voir fonction | Validé par firmware |  | S15 |
| 40 | PE9 | GPIO, parallèle 8080 8 bits | Sortie | LCD HOLITECH FPC-HIB018A011-A1 | D2 — Bit 2 de l’octet commande/paramètre/pixel | Voir fonction | Validé par firmware |  | S15 |
| 41 | PE10 | GPIO, parallèle 8080 8 bits | Sortie | LCD HOLITECH FPC-HIB018A011-A1 | D3 — Bit 3 de l’octet commande/paramètre/pixel | Voir fonction | Validé par firmware |  | S15 |
| 42 | PE11 | GPIO, parallèle 8080 8 bits | Sortie | LCD HOLITECH FPC-HIB018A011-A1 | D4 — Bit 4 de l’octet commande/paramètre/pixel | Voir fonction | Validé par firmware |  | S15 |
| 43 | PE12 | GPIO, parallèle 8080 8 bits | Sortie | LCD HOLITECH FPC-HIB018A011-A1 | D5 — Bit 5 de l’octet commande/paramètre/pixel | Voir fonction | Validé par firmware |  | S15 |
| 44 | PE13 | GPIO, parallèle 8080 8 bits | Sortie | LCD HOLITECH FPC-HIB018A011-A1 | D6 — Bit 6 de l’octet commande/paramètre/pixel | Voir fonction | Validé par firmware |  | S15 |
| 45 | PE14 | GPIO, parallèle 8080 8 bits | Sortie | LCD HOLITECH FPC-HIB018A011-A1 | D7 — Bit 7 de l’octet commande/paramètre/pixel | Voir fonction | Validé par firmware |  | S15 |
| 46 | PE15 | GPIO de séquence marche / veille | Sortie | Bloc distant non identifié | Ligne auxiliaire positionnée dans la séquence d’initialisation et de veille | 1 dans init générale ; 0 après attente au démarrage et dans un chemin de veille | Non résolu : fonction distante | La séquence est retrouvée ; destination et signification électrique non résolues | N7 |
| 97 | PE0 | GPIO de marche / veille | Sortie | Circuit de commande marche / maintien du poste | Commande de maintien logique du poste en marche | 1 après démarrage ; 0 dans les chemins d’extinction, après coupure RF/audio | Validé par firmware | Type de transistor ou de latch non déductible ; n’implique pas coupure du MCU alimenté par SWD | N7 |
| 98 | PE1 | GPIO, sélection série RF | Sortie | Circuit RF de la banque 3 (famille QA4818N) | CS# / sélection active basse — Sélection de la banque logique 3 | CS actif bas | Validé par firmware | Banque identifiée fonctionnellement ; la référence exacte du silicium gratté n’est pas encodée par le logiciel | S6 |

### Autres signaux

| Patte GD32 | Signal GD32 | Type de liaison | Sens côté MCU | Circuit / bloc distant | Fonction du signal distant | Polarité / séquence | Validation | Précision restante | Preuves |
|---|---|---|---|---|---|---|---|---|---|
| 12 | OSC_IN | Oscillateur HXTAL | Entrée | Quartz 12,000 MHz et réseau de charge | Borne du quartz — Oscillateur principal | Voir fonction | Fonction MCU / connaissance projet |  | S1; S13 |
| 13 | OSC_OUT | Oscillateur HXTAL | Sortie | Quartz 12,000 MHz et réseau de charge | Borne du quartz — Oscillateur principal | Voir fonction | Fonction MCU / connaissance projet |  | S1; S13 |
| 14 | NRST | Reset matériel | Entrée / reset MCU | Réseau NRST, point de récupération SWD | NRST — Réinitialisation / connect under reset | Voir fonction | Fonction MCU / connaissance projet |  | S1; S13 |
| 20 | VREF- | Alimentation / référence | Alimentation | Réseau d’alimentation ou de référence de la carte | Définit la borne basse de conversion ADC/DAC | Référence basse | Référence ADC/DAC du MCU | Le firmware ne permet pas d’identifier la source analogique externe de référence | S1 |
| 21 | VREF+ | Alimentation / référence | Alimentation | Réseau d’alimentation ou de référence de la carte | Définit la borne haute de conversion ADC/DAC | Référence haute | Référence ADC/DAC du MCU | Le firmware ne permet pas d’identifier la source analogique externe de référence | S1 |
| 94 | BOOT0 | Strap de démarrage | Entrée | Réseau de polarisation non relevé | Niveau BOOT0 — Sélection du mode de démarrage | Voir fonction | Fonction MCU / connaissance projet | Le binaire n’identifie pas le réseau de polarisation | S1 |

## Sources historiques


Révision étudiée : **D578UV PRO, GD32F303VKT6, OEM GD32 V1.21**. État du tableau : **9 novembre 2026**. Les variantes PLUS/V2.08 ne sont pas réputées identiques sans contrôle.

- **S1** — GigaDevice, GD32F303xx Datasheet Rev.3.3, figure 2-3 et table 2-5 (LQFP100), pages imprimées 30–36 : https://www.gd32mcu.com/data/documents/datasheet/GD32F303xx%20Datasheet_Rev3.3.pdf . La numérotation du boîtier et les fonctions internes viennent du constructeur ; cela ne fournit pas le schéma D578.
- **S2** — Projet, `docs/FACADE_GPIO_BOUTONS_CODEUR_VOLUMES_ET_ECLAIRAGES.md`, décodeur `browser-bench/assets/board-io.mjs` : touches, codeur, ADC, bus de voyants et d’éclairage.
- **S3** — Projet, `docs/peripherals/01_NAND_SPI_CABLAGE_PILOTE_FORMATS_MEMOIRE.md` et décodeur NAND GPIO : attribution des quatre lignes du bus.
- **S4** — UTC, U2429 QW-R502-031.D, page 2 : https://www.unisonic.com.tw/uploadfiles/836/part_no_pdf/U2429.pdf . Les pattes DATA=4 et CLOCK=5 sont les fonctions constructeur du composant ; la continuité sur le PCB reste à qualifier.
- **S5** — KIOXIA, TC58CVG1S3HRAIG Rev.2.0, page 7, WSON8 : https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/305/KIOXIA_TC58CVG1S3HRAIG_Rev2.0_E191001.pdf . CS#=1, SO/SO1=2, SI/SO0=5, SCK=6. Le brochage du composant et la liaison MCU sont deux preuves distinctes.
- **S6** — Projet, `browser-bench/assets/radio-buses.mjs`, classes `RfSpi` et `FmI2c` : sélections des banques, SDIO/CLK et décodage I²C logiciel. Ce sont des correspondances du modèle, pas un schéma de continuité.
- **S7** — Projet, `docs/hardware/BH2226_H2226_DAC_RF.md` : brochage fabricant BH2226 et protocole 12 bits. L’identification du BH2226 sur carte ne prouve pas que le bus d’éclairage décodé aboutit à ses entrées.
- **S8** — Capture OEM existante `oem_audio_v012/TX_A_level4.json`, section GPIO/config, UART et DAC. Lecture passive d’un état du banc après TX VHF. Les nibbles affichés sont un instantané, pas la configuration permanente des broches ni une mesure électrique du poste. Un extrait est fourni dans `PREUVE_CONFIGURATION_OEM.json`.
- **S9** — Projet, documentation GPS ATGM336H et essais USART1/GPS. S8 donne PA2=0xB, PA3=0x4, AFIO_PCF0=0x04000000 ; le remap USART1 n’est pas activé. Le rattachement logique PA2/PA3 est ainsi mieux établi qu’une simple possibilité de la fiche constructeur. Le suffixe et les numéros de broches du module sur cette carte restent non relevés.
- **S10** — Projet, `docs/peripherals/AUDIO_LIAISONS_LOGIQUES_OEM_V013.md` : pilote U2429 PA13/PA14, mute poste PA7, commandes de chemin/mute via PIO RF. Les opérations du pilote OEM ont été confrontées à une réécriture indépendante.
- **S11** — Étude SWR/ROS et travaux TX/mesures du projet : ADC6 thermique, ADC10 non attribué, ADC11 alimentation, consigne DAC0 en TX. L’étage analogique entre DAC et PA reste non identifié.
- **S12** — Documentation et essais microphone/USB du projet. Le brochage RJ historique est distinct du sens de la liaison côté MCU.
- **S13** — Relevés communiqués par Jean-Philippe (F4EGM) : quartz 12 MHz, accès SWD réussi (SWCLK pad 2, SWDIO pad 4, GND pad 3 du montage), repérage NRST de F1DMG. Ces numéros de pads ne constituent pas une norme de connecteur.
- **S14** — Projet, ancien `hardware/pinmaps/GD32F303VKT6_LQFP100_REFERENCE.csv`, documents tuner FM et Bluetooth. Le nouveau désassemblage N2 tranche SDA/SCL.
- **S15** — Projet, `docs/LCD_CABLAGE_PILOTAGE_ET_INTEGRATION_V11_8.md` : bus LCD 8080 GPIO, PE7..PE14, PB10..PB13. Les numéros de contacts FPC et le silicium du contrôleur ne sont pas établis.
- **S16** — Projet, `docs/peripherals/04_DMR_SCT3258_BOOTSTRAP_HPI_PAQUETS_CODEC_PARAMETRES.md` et décodeur HPI : PD2..PD5 et PD8..PD15. Aucun numéro de patte SCT n’est inventé. Le DMR reste hors développement fonctionnel de cette étape.


Les anciennes formulations de réserve physique de ces documents sont remplacées, pour les liaisons résolues, par la règle de validation de cette révision. Voir ANALYSE_INCONNUES.md pour les preuves nouvelles N1…N14.
