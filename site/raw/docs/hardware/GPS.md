# GPS ATGM336H

Le module ATGM336H a ete identifie dans le projet D578. Ce fichier est un **point d'entree** pour la documentation detaillee; il ne constitue pas encore un pinout confirme.

**A documenter avant un driver alternatif :** marquage exact et revision, alimentations et backup, niveaux logiques, ligne UART TX/RX jusqu'aux GPIO du GD32, baudrate reel, requetes et messages NMEA/commandes proprietaires effectivement observes, gestion fix/PPS, modes veille et hot start, EEPROM/Flash internes si le module en possede dans la configuration montee, chemins EEPROM/NAND/Flash des parametres GPS du poste et interactions APRS.

Les captures doivent distinguer l'UART du module, l'etat synthetique du simulateur et les variables du firmware constructeur. Ne pas attribuer une broche au GD32 uniquement parce que le module standard fournit une fonction correspondante.

**Sources internes :** [recherche](../RESEARCH_INDEX.md), [emulateur](../EMULATOR.md), [routines OEM](../04_RAM_ROUTINES_UI_RF_ET_BROCHAGE.md), [priorites de reprise](../09_REPRISE_PRIORITES_TESTS_ET_INFOS_MANQUANTES.md).

**Source photographique tierce :** [vue du module et de la carte de facade](https://radio.carstenbauer.net/578techmods.htm) pour orientation, **sans preuve que la revision photographiée est identique** a la notre.
