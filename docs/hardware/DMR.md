# DMR / SCT3258 : documentation de travail

Le projet vise l'acces complet au circuit baseband DMR et la possibilite de remplacer le firmware d'application. La famille **SCT3258** est identifiee dans la recherche sur le D578. Le banc possede un sous-ensemble `SCT3258_HPI`; cela ne prouve pas l'exhaustivite du pilote ni le pinout reel.

Sujets a reconstruire : alimentation et sequence reset/clock, host-port interface (HPI), bus de donnees et lignes IRQ, image et format du firmware interne/DSP, adresses et protocole de chargement, configuration TDMA, codec AMBE, commandes d'audio, streaming TX/RX, interface codec, zone NAND/Flash de stockage des binaires et de la calibration, observabilite des evenements et procedures de recuperation.

**Important :** il n'y a pas encore de firmware DMR alternatif operationnel ni de jeu de commandes garantit sur le poste. Les binaires proprietaires ne sont pas inclus dans le depot public. Les enregistrements de test doivent etre horodates et attaches a la version exacte de la carte.

**Points de depart :** [roadmap](../ROADMAP.md), [routines UI/RF](../04_RAM_ROUTINES_UI_RF_ET_BROCHAGE.md), [simulateur](../EMULATOR.md), [retour d'experience](../07_ERREURS_CORRECTIONS_HYPOTHESES_ET_NO_GO.md).
