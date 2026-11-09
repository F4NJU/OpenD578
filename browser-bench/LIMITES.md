# État du banc Web 0.14

Le démarrage OEM jusqu'à l'écran des deux mémoires est obtenu dans le moteur Web avec les captures du projet. Cela ne constitue pas une qualification de tout le poste.

Le code JavaScript ne fabrique pas les menus, ne saute pas les boucles d'attente et n'écrit pas les variables OEM pour forcer leur état. Les entrées de façade agissent sur GPIO/ADC ; le DMA accède à la SRAM par les descripteurs écrits par le firmware ; les octets NAND sont lus dans les fichiers sélectionnés.

## Domaine porté

RCU, SysTick temporel, NVIC et exceptions de base, WFI/WFE/SEV, ADC0 et DMA0/ch0, timers1..6, UART0/1/3, RTC/BKP/PMU, DAC numérique, watchdog, cache FMC, GPIO, bus LCD/NAND/RF/FM/HPI et éclairages. USB possède les scénarios déconnecté et connecté : IRQ20, PMA, endpoints simples et hôte CDC.

## Limites conservées

- Pas de précision au cycle. Les durées d'ADC et d'UART sont des modèles numériques, pas des mesures électriques.
- Pas d'exceptions imbriquées, de frames flottantes ni de tous les canaux DMA et modes timer.
- Pas de calcul RF, de modulation/démodulation ou de trajet audio PCM complet. Les valeurs RF de repos et ADC sont un scénario d'entrée déclaré ; elles ne prouvent pas les mesures d'un poste réel.
- DSP/vocodeur DMR non exécuté. Lui seul autorise une réponse de remplacement ; elle est identifiable dans le diagnostic. Les contrôles HPI connus et la configuration codec restent traités séparément.
- GPS : entrées NMEA RMC/GGA/GSV à cadence fixe, trajet/vitesse/cap, pertes de fix et altérations configurables. L’endurance complète OEM et la réception RF GNSS ne sont pas qualifiées. Le test producteur de 10 000 époques reste distinct des essais OEM. Bluetooth non exécuté. Microphone filaire sans chaîne audio complète.
- USB/CPS : énumération, identité et édition du nom du canal 1 par bloc de 128 Kio, END, watchdog et relecture après reset. Le bloc initial a été retrouvé exactement après une seconde édition CPS. Le bouton de restauration partage le même transport et ses transitions sont testées séparément en logiciel. Éditeur CPS général, pont série système et CPS Windows hors qualification. L’inspecteur NAND reste distinct du client CPS.
- NAND : octets main/OOB/statuts ECC capturés, overlay volatil ; absence de modèle électrique, d'usure et de recalcul ECC physique.
- LCD : sous-ensemble des commandes observées ; composant exact, montage et couleurs à qualifier sur le matériel. La projection respecte MY/MX et RGB/BGR du jeu de commandes compatible ; tous les modes graphiques ne sont pas couverts.
- RTC : scénario initial de domaine sauvegardé explicite, distinct d'une capture de la pile RTC réelle.

Les registres ou transactions non couverts provoquent un arrêt du modèle. Un arrêt d'attente WFI est reprenable ; une erreur matérielle reste terminale jusqu'au reset. Les originaux des sauvegardes ne sont jamais écrits.

## Protection SWR / ROS

Mesure, polarité du défaut, seuils, temporisation, affichage et action sur TX restent à identifier et à qualifier dans chaque bande. Une protection matérielle peut agir sans écran d’erreur. Le panneau de capteurs fournit des entrées ADC réelles du modèle et des observations de sorties ; il ne génère aucun défaut SWR ni aucune réaction du firmware. Les comparaisons thermiques 992/868 concernent la commande ventilateur. Elles ne prouvent ni une protection ROS ni une coupure TX de surchauffe.

## Façade et audio

Les entrées des huit touches analogiques et des deux potentiomètres sont acquises par l’ADC/DMA configuré par le programme ARM. Power, appui codeur et fronts de rotation sont des entrées GPIO. L’observation des sorties de gain/mute est passive ; elle ne remplace ni le codec ni le traitement PCM. Le nombre de fronts par cran, l’ordre et la loi des potentiomètres, ainsi que les adresses des LEDs blanches demandent encore des mesures physiques.

## Microphone filaire 0.10

Le protocole de clavier/PTT, les commandes des voyants RX/TX et MAIN, le verrouillage et la présence 06 du profil public sont portés. Le MCU interne au microphone ne tourne pas dans le banc. La file attend les ACK réels AA ; timeout/retry physique non qualifié. L’audio analogique, le rétroéclairage du clavier et les temporisations exactes restent ouverts. À la capture deux secondes après déconnexion en TX, le poste commande encore rouge ; le banc ne force pas une coupure. Voir `../preuves/VERIFICATION_MICROPHONE.md`.


## Commandes audio 0.11

U2429 : décodage physique logique PA13 DATA / PA14 CLOCK, sorties GPIO et SWJ désactivé requis, lecture au front montant, latch au dernier front descendant avec DATA haut, canaux individuels/communs et codes 0 à −83 dB/coupure. État externe conservé au reset MCU. Le transfert nominal en petit signal est disponible au niveau du composant ; bruit, distorsion et saturation analogique ne sont pas modélisés.

AIC3204 : observateur des demandes HPI paginées, champs de gain signés, PGA micro, coupures et paramètres AGC selon TI SLAA557. L'état interne non transmis du SCT/codec reste inconnu. Cet observateur ne fait pas passer un message HPI pour une mesure I²C, une réponse acoustique, un filtre exécuté ou un flux PCM.

Les deux canaux U2429 ne sont pas attribués automatiquement aux HP ou aux jacks. La sélection A/B du HP micro, les contacts des prises externes, les corrections audio et la chaîne TX micro demandent une qualification distincte.

SCT : six configurations d'égalisation indépendantes RX/TX, coefficients signés Q16.14, calcul nominal de trois sections IIR à 24 kHz avec conservation entre blocs. Ce calcul de référence ne prétend pas exécuter le DSP interne bit pour bit ; arrondis, saturation et commutation des états restent à qualifier. Il n'est pas raccordé à une source ou une sortie PCM supposée.


## Calibrations 0.12

Le traçage compte les octets réellement transmis depuis la NAND, pas le préchargement du cache. Huit champs de service V1.21 sont identifiés ; les noms sont présentés seulement pour la Flash de référence reconnue. Le modèle n'injecte aucun réglage usine. La campagne OEM vérifie MIC, MODV1, MODU et les bits de commande associés à CTCW, avec TX VHF/UHF et changement du niveau utilisateur. Cela ne valide ni la loi physique des codes QA ni la forme d'onde, les contacts de jacks, les amplificateurs ou le flux sonore complet. Les permissions du mode test ne sont pas modifiées.

## Liaisons logiques 0.13

Les fonctions de coupure HP poste/micro et l’application de la préférence MAIN/SUB sont établies par le code OEM. Le bit 2 est une porte contextuelle, le bit 7 peut être réécrit par des routes temporaires. Une réécriture C indépendante correspond à huit routines OEM sur 62 402 cas de tests isolés. Ce résultat ne revendique ni nouveau démarrage intégral ni transport PCM complet. Le relevé intégral du câblage et de la réponse analogique n’est pas un préalable à ces contrats logiciels ; les contacts de prises sans retour MCU restent un cas à modéliser séparément.

## TX et GPS 0.14

Fréquences OEM suivies sur 0x38/0x39 ; calibrations de puissance NAND affichées après lecture ; commandes CASIC02/03/04 reçues par le pair USART1 et appliquées à la source. Le défaut décimal de vitesse est reproduit par le formateur OEM isolé ; le banc ne le corrige pas à la place du programme. Voir la cartographie TX/GPS et le périmètre de première publication à la racine du paquet. Le transport audio continu et le ROS restent ouverts.
