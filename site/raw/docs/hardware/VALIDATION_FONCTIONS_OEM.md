# D578 : statut des fonctions et cartographie issue du firmware OEM

Date : 6 novembre 2026. Ce document remplace la lecture trop prudente des statuts visuels précédents.

## Règle de validation

- **Fonction OEM opérationnelle** : considérée comme **validée**, sur le poste de l’utilisateur. Les fonctions radio, GPS, DMR, LCD, touches et Bluetooth ne doivent pas être qualifiées de non fonctionnelles simplement parce qu'un schéma de piste manque.
- **Broche/routine OEM documentée** : lorsqu’une routine constructeur exécutée utilise explicitement GPIO/ADC/UART, l'affectation du périphérique logiciel est **validée par firmware OEM** ; elle peut être réutilisée comme résultat de reverse engineering avec la provenance indiquée.
- **Modèle uniquement** : une liaison ajoutée par le simulateur, sans vérification de l'écriture GPIO OEM associée, reste « observée dans le modèle » ; pas « identifiée physiquement ».
- **Attribution des pistes/boîtiers** : la relation exacte entre un GPIO connu et une broche d'un CI gratté peut rester à établir sans déclasser la fonction opérationnelle.
- **PLUS** : MCU GD32F303 confirmé, panneau et fonctions opérationnels. Ne pas supposer que toutes les affectations GPIO du firmware PRO V1.21 sont identiques sur la branche PLUS.

## Fonctions de façade PRO V1.21 : correspondances documentées

| Fonction | GPIO / périphérique GD32 | Information utile pour le pilote | Source |
|---|---|---|---|
| LCD D0..D7 | PE7..PE14 | Bus 8080 8 bits, RGB565 128×160 | `docs/LCD_CABLAGE_PILOTAGE_ET_INTEGRATION_V11_8.md` |
| LCD WR, D/C, RESET, CS | PB10, PB11, PB12, PB13 | Initialisation et commandes observées | idem |
| Power | PA0 | Actif à l'état bas; réveil et logique Power | `docs/FACADE_GPIO_BOUTONS_CODEUR_VOLUMES_ET_ECLAIRAGES.md` |
| Appui codeur | PA1 | Actif à l'état bas | idem |
| P1/P2/P3/MENU | PB0 / ADC0 canal 8 | 4 plages de tension de réseau résistif | idem |
| P4/P5/P6/EXIT | PB1 / ADC0 canal 9 | 4 plages de tension de réseau résistif | idem |
| Codeur A/B | PC8, PC9 | EXTI8 descendant, lecture PC9 pour la direction | idem |
| Volume A/B (modèle) | PC2 / ADC12; PC5 / ADC15 | Acquisition ADC0; sens et ordre physiques à constater | idem |
| Voyant rouge/vert poste | PE3 données; PE4 horloge | Mot 8 bits, LSB d'abord | idem |
| Éclairages boutons et LCD | PA5 validation; PB3 horloge; PB4 données | 4 bits adresse + 8 bits valeur, MSB d'abord; canal 8 : luminosité LCD | idem |
| Microphone filaire | USART0, PA9/PA10 selon configuration OEM | Trames 0x41 sur 8 octets, 0x53 sur 16 octets | `docs/NOTICE_CHANGELOG_MICROPHONE_V11_8.md` |
| Sélection haut-parleur | PA7; bus RF banque1/page0/0x25 bit 4 | Speaker Mode Mic/Radio/Both exécuté dans OEM | idem |

## Autres interfaces et protocoles connus

| Élément | Interface connue | Distinction nécessaire |
|---|---|---|
| SWD | PA13 (SWDIO), PA14 (SWCLK) et pads relevés physiquement | Accessible dans MCU UPDATE ; Power est un bouton logique |
| NAND TC58CVG1S3H | GPIO série, modèle PB8 CS, PB15 CLK, PB14 MOSI, PA15 MISO; ID 98 CB | Commandes et dumps cohérents; conserver le statut « modèle » si numéro de broche externe non confirmé |
| QA4818N / RF | Bus 24 bits, PB3 CLK, PB4 SDIO, CS PB5/PB2/PC13/PE1 | Transactions OEM et banque logique connues; attribuer chaque CS au boîtier physique séparément |
| SCT3258 DMR | HPI données PD8..PD15; PD2 CS, PD3 WR, PD4 RD, PD5 handshake | Pilote et paquets HPI observés; DMR opérationnel en OEM |
| RDA5802N | PB6 SDA, PB7 SCL, adresse 0x10 dans modèle FM compatible RDA5807 | Valider la fonction OEM, ne pas transformer l'ACK synthétique du modèle en mesure sur RDA physique |
| GPS ATGM336H | UART GNSS, données NMEA | Fonction OEM validée; instance USART et broches non fixées par le dossier public |
| Bluetooth ET12 | UART3, commandes AT+VER / AGHF modélisées | Télécommande et audio OEM opérationnels; pins carte D868BT-SP à préciser |
| CPS | USB CDC, commandes PROGRAM, R, W, END | Lecture/écriture de canaux et persistance exécutées dans banc OEM |
| Audio | Codec TLV320AIC3204, SCT3258; PA7 et registre RF 0x25 | Séparation des commandes de mute et chemin analogique |

## Attention aux périphériques partageant les broches

PB3/PB4 apparaissent dans le bus de rétroéclairage et dans le décodeur RF série. Ce partage dans nos modèles doit être expliqué par la configuration GPIO, l'alternance temporelle ou une éventuelle confusion de profil avant qu'un firmware indépendant ne l'exécute simultanément. Les fonctions OEM demeurent opérationnelles. **Ne pas activer deux pilotes concurrents sur PB3/PB4.**

## Frontière des conclusions

Une fonction testée sur le poste vaut validation fonctionnelle. Une adresse OEM tirée d'une exécution vaut preuve logicielle. Une photographie et un relevé de continuité valent preuve de câblage. Ces niveaux se complètent ; l'absence du dernier ne doit pas effacer les deux premiers.
