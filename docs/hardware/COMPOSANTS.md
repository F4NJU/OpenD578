# Inventaire materiel et nomenclature de travail

**Variante de reference :** AnyTone D578UV PRO, MCU GD32F303VKT6, firmware constructeur GD32 V1.21.

Ce document accompagne la [vue eclatee interactive](../../README_SITE.md). Pour chaque composant, le modele source versionne est dans `hardware/models/d578uv-pro-gd32-v121.json`. Le site genere automatiquement une fiche par composant et une fiche pour chacune de ses liaisons. La fiche donne les informations, les connexions, les affectations de broches et les renvois vers les documents complets.

| Element | Identification | Niveau de detail actuel | Documentation principale |
| --- | --- | --- | --- |
| CPU | GD32F303VKT6 | Flash, SRAM, SWD, boot et GPIO analyses | [CPU et boot](../02_CPU_FLASH_BOOT_USB_SWD.md) |
| NAND serie | TC58CVG1S3HRAIG | Lecture, ECC, captures, zones critiques et bus GPIO candidates | [NAND](../03_NAND_LECTURES_ECC_CARTE.md) |
| Afficheur | HOLITECH FPC-HIB018A011-A1 SLH1920 | Bus 8080, initialisation, timings et commandes; controleur exact a confirmer | [LCD](../LCD_CABLAGE_PILOTAGE_ET_INTEGRATION_V11_8.md) |
| Façade | 10 touches, codeur, deux potentiometres | Entrees ADC/GPIO et pilotes autonomes proposes | [Facade](../FACADE_GPIO_BOUTONS_CODEUR_VOLUMES_ET_ECLAIRAGES.md) |
| Microphone | Prise 8 contacts, LED A/B | UART 8/16 octets, audio, commandes, routines | [Microphone](../NOTICE_CHANGELOG_MICROPHONE_V11_8.md) |
| GPS | ATGM336H | Identification module, controles UART a poursuivre | [GPS](GPS.md) |
| DMR | SCT3258 (famille a confirmer sur la carte cible) | Peripherique HPI modele, firmware et protocoles incomplets | [Baseband DMR](DMR.md) |
| Audio externe | TLV320AIC3204 (identification a confirmer) | Hypothese codec, aucun brochage de carte qualifie | [Audio](AUDIO.md) |
| RF | Etages RX/TX VHF/UHF | Routines RF candidates, implantation et liaisons incompletes | [RF](RF.md) |
| Alimentation | Rails et protections a relever | Power est une entree vers MCU; ne pas confondre avec coupure MCU | [CPU](../02_CPU_FLASH_BOOT_USB_SWD.md) |
| Bluetooth interne | Support D868BT-SP, module RF soude sous blindage, firmware de famille ET12 | UART3 et quatre commandes AT du banc ; SoC, GPIO, audio et connecteur non etablis | [Carte et ET12](BLUETOOTH_D868BT_SP_ET12.md) |

Une liaison affichee dans l'explorateur ne signifie **pas** toujours qu'elle a ete mesuree sur PCB. Les preuves sont etiquetees individuellement : mesure materielle, code OEM, execution du simulateur, hypothese, ou inconnue.

La liste deviendra exhaustive au rythme des identifications reelles : ne pas ajouter un circuit sans photo lisible, mesure, identification de composant ou preuve logicielle attribuable a cette revision.

## Inventaire complémentaire PRO GD32 (novembre 2026)

| Élément nouveau | État de preuve | Fiche détaillée |
| --- | --- | --- |
| RDA5802N | Référence observée; bus PB6/PB7 connu du **banc** uniquement | [FM radiodiffusion](RDA5802N_RECEPTION_FM.md) |
| QA4818N ×4, grattés | Identification de famille par VK7ZJA, chacun à attribuer sur la carte | [Quatre circuits et horloge 26 MHz](QA4818N_QUATRE_CIRCUITS_26MHZ.md) |
| H2226 / ROHM BH2226FV-E2 | Identification type confirme par marquage H2226 et boitier SSOP-B16 ; sorties et broches GD32 inconnues | [DAC huit sorties](BH2226_H2226_DAC_RF.md) |
| UTC U2429G | Atténuateur 2 voies identifié; GPIO non identifiés | [Volume analogique série](VOLUME_U2429G.md) |
| MC34119G + SGM8272 | Amplificateur local et double AOP, fonctions sur la carte non prouvées | [Étages analogiques](AUDIO_MC34119_SGM8272.md) |
| YD1517P PRO / UTC PA1517G PLUS | Ampli audio 2×6W, mute et chemins audio à mesurer | [Comparaison des amplificateurs](AUDIO_PA1517_YD1517_VARIANTES.md) |
| 2× AFT05MP075N | Transistors LDMOS RF, VHF et UHF dans la famille D578 | [Étages de puissance RF](PA_RF_AFT05MP075N.md) |
| L7805CV TO-220 | Régulateur 5 V; aucune cartographie des charges | [Distribution de puissance](ALIMENTATION_L7805CV.md) |
| PLUS KT09?5R / carte fille | Récepteur AM plausible ; référence inconnue, connecteur absent PRO | [Module supplémentaire PLUS](CARTE_PLUS_AM_KT_NON_IDENTIFIE.md) |

| BT01 | Microphone sans fil avec afficheur et firmware propre ; mode radio distant | [Microphone BT01](BT01_MICROPHONE_BLUETOOTH.md) |
| BP-02 | Bouton PTT Bluetooth independant du BT01 ; protocole radio non releve | [PTT BP-02](BP02_PTT_BLUETOOTH.md) |
| Variantes Bluetooth | PRO et PLUS avec GD32F303 ; comparaison D878 sans identite de carte prouvee | [PRO / PLUS / D878](BLUETOOTH_PRO_PLUS_D878_COMPARAISON.md) |

Pour le détail **fonction par fonction** de ce qui manque et de ce que l'on peut établir seul : [audit des fonctions incomplètes](AUDIT_FONCTIONS_PARTIELLES.md). Les étapes de mesure et d'attribution sont dans le [plan d'investigation](PLAN_INVESTIGATION_BROCHAGES.md).

- [Analyse RF QA4818N détaillée](QA4818N_RECONSTRUCTION_REGISTRES_PLL_CHAINES_RX_TX.md) : formule théorique, quatre banques, test C et comparaison aux données OEM.
