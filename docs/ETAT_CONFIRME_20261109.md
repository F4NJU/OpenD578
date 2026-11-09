# État confirmé du projet — 9 novembre 2026

Jean-Philippe (F4EGM). Cette page rassemble les corrections actuelles ; les archives datées restent des traces historiques.

## Accès

- [Tableau IO, 86 signaux utiles](hardware/io/TABLEAU_IO_D578.md) ; recherche interactive dans la rubrique Tableau IO du site.
- [Analyse des inconnues et preuves N1–N14](hardware/io/ANALYSE_INCONNUES.md).
- [Comparaison PRO V1.21 / PLUS V2.08](hardware/io/COMPARAISON_PRO_PLUS.md).
- [Réception APRS analogique du PLUS](hardware/io/APRS_RX_PLUS.md).
- Le simulateur est accessible dans la navigation, rubrique Simulateur. Ses sources sont dans browser-bench/ ; son guide est intégré.

## Corrections intégrées

| Sujet | État actuel |
|---|---|
| GPS | PA2 TX / PA3 RX, USART1 sans remap ; NMEA et commandes CASIC. Scénarios trajet/vitesse disponibles ; le défaut décimal du formateur OEM n’est pas corrigé à sa place. |
| Microphone filaire | USART0 PA9 TX / PA10 RX ; touches, durées, acquittements et commandes de voyants dans le banc. Ne démontre pas un transport PCM complet. |
| Volumes | U2429 DATA PA13 / CLOCK PA14 après libération SWJ ; D0 canal, D1 individuel/commun. Encodeur C corrigé. |
| BH2226 | PA5 CSB / PB3 CLK / PB4 DI ; nibble série inversé par rapport à l’ordre de présentation ROHM. Code fil 8 = DA1 rétroéclairage LCD. Encodeur C corrigé. |
| Voyants poste | PE3 données / PE4 horloge, 8 bits LSB-first ; rouge et vert issus des commandes OEM, pas des clics de l’interface. |
| Tuner RDA / KT | PB6 SDA / PB7 SCL. Chemins 0x10 RDA et 0x35 compatible KT présents dans les applications. Le modèle Web actuel ne représente pas entièrement le second tuner. |
| APRS RX PLUS | Carte BT+APRS BHT_BOARD : NRZI et retrait du bourrage ; UART3 PC11 RX / PC10 TX, 115200 bit/s, préfixe +APRS: et trame AX.25. Entrée RF/audio de BHT non attribuée. |
| PB9 | PWM TIMER3_CH3 pour tonalités / signalisation, aussi utilisé par APRS TX ; aucune lecture GPIO identifiée. |
| PC0 | ADC0_IN10 acquisition audio RX / signalisation ; pas d’attribution arbitraire au ROS. |
| PC3 / PE15 | Séquences connues ; destination distante non résolue. Non déclarées libres. |
| PLUS | 570 signatures GPIO directes communes aux deux applications ; 36 exécutions isolées comparées. Cela ne certifie pas tout le matériel ni le démarrage PLUS. |

Une liaison fonctionnellement établie dans le firmware est validée pour le projet ; sa continuité n’est pas redemandée. Une référence de silicium ou un trajet analogique non établi reste indiqué comme inconnu. Aucun inverseur matériel n’est inventé à partir d’une polarité logicielle.

## Simulateur intégré

Le banc Web 0.15.1 charge les sauvegardes et exécute l’ARM dans le navigateur avec Flash, SRAM, NAND et périphériques. Il reprend les derniers travaux disponibles : façade, micro, GPS, observation des commandes audio/calibrations, USB/CPS, couleurs LCD corrigées et réduction des surcoûts de journalisation et ADC. Les sources du moteur et licences sont conservées.

Les anciennes références V11.x concernent le banc local Python ; elles ne décrivent pas la version du banc Web. Les validations archivées restent attachées à leur scénario, firmware et version.

La performance reste insuffisante pour promettre le temps réel : sur les mesures bornées conservées, gain global d’environ 1,10×, microbenchmark ADC 3,31×. Le hook JavaScript par instruction demeure. Aucun saut de routine ni écran préfabriqué n’a été ajouté pour donner l’impression d’un démarrage plus rapide.

## Travaux encore nécessaires

- Transport audio PCM complet, filtres et gains physiques de bout en bout, HP poste/micro/externe.
- Protection ROS/SWR : entrée et algorithme avec preuve de coupure OEM sur VHF et UHF ; pas de seuil inventé.
- Entrée RF/audio de BHT et démodulation AFSK complète ; contrôle FCS à établir.
- Modèle complet du tuner KT à 0x35, au-delà de son identification par firmware.
- Requalification longue du banc complet après modifications et amélioration majeure des performances.
- DMR différé, conformément au périmètre retenu.

Le passage général du site vérifie la génération, les modèles, la navigation, les liens locaux et les régressions logicielles. Il ne signifie pas que chaque affirmation historique provenant de sources externes a été démontrée par une nouvelle exécution OEM.

## Complément audio du même jour

Les sources C de commande audio et leur test différentiel sont maintenant intégrés. Une entrée WAV sur PC0/ADC10 traverse le modèle ADC/DMA piloté par l’ARM ; le banc totalise 120 tests réussis. Voir [audio FM, transport et validation](peripherals/08_AUDIO_FM_TRANSPORT_ET_VALIDATION.md). Ce complément ne revendique pas encore une conversation FM micro→RF→HP de bout en bout.

## Vue éclatée, QA et audio raccordé

Les deux vues MCU couvrent les 80 GPIO et les fiches MCU affichent 86 signaux. Les banques QA sont nommées par sélection, avec les fréquences OEM 0x38/0x39. Le transfert U2429 applique les commandes série aux échantillons horodatés ; écoute et export WAV à ses bornes. Le menu Audio RX/TX donne le schéma bloc complet et les raccordements encore ouverts. Voir [schéma et réglages](peripherals/09_SCHEMA_AUDIO_RX_TX_ET_RACCORDEMENTS.md).

## Critère fonctionnel et programme indépendant

Le critère retenu avec Jean-Philippe est désormais la validation fonctionnelle des commandes et réactions ; la fidélité acoustique détaillée est réservée aux essais sur poste. Un premier [programme audio alpha](../firmware/experiments/audio_alpha/README.md) est compilé et exécuté dans le banc : ADC/DMA, deux volumes, coupures et LCD autonome. Il n’initialise pas la RF et n’est pas un paquet de mise à jour constructeur qualifié pour le matériel. 126 tests Web réussis.
