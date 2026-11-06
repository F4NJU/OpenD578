# UTC U2429G : atténuateur audio stéréo à commande série

Le `U2429G` fabriqué par UTC (Unisonic Technologies) est un **contrôleur de volume analogique à deux canaux**. Il conserve des entrées/sorties analogiques ; le GD32 règle leur atténuation par deux signaux **CLOCK et DATA**. Il ne s'agit **pas d'un périphérique I²C** (pas de SDA/SCL ni d'adresse 7 bits).

## 1. Pinout constructeur (SOIC8 / DIP8, vue dessus)

| Pin | Nom | Rôle |
| ---: | --- | --- |
| 1 | VIN1 | Entrée signal voie 1 |
| 2 | VOUT1 | Sortie signal voie 1 |
| 3 | GND | Masse |
| 4 | DATA | Entrée série |
| 5 | CLOCK | Horloge série |
| 6 | VCC | Alimentation, 4,5–5,5 V |
| 7 | VOUT2 | Sortie signal voie 2 |
| 8 | VIN2 | Entrée signal voie 2 |

Atténuation programmable de **0 à −83 dB par incréments de 1 dB**, plus une condition de coupure. Les deux canaux peuvent être réglés ensemble ou séparément.

## 2. Contraintes électriques et timings

Selon la datasheet UTC (rév. D) : tension recommandée 4,5–5,5 V, `VIH ≥ 0,8×VCC` pour CLOCK/DATA, `VIL ≤ 0,2×VCC`. À **VCC=5 V**, `VIH ≥ 4 V` : **une sortie 3,3 V du GD32 ne garantit pas une entrée haute**. Chercher un étage d'adaptation, un transistor, une alimentation différente ou une autre révision avant toute connexion.

Horloge série, fiche constructeur : `tCR ≥ 4 µs` (soit une fréquence maximale théorique de 250 kHz), état haut et bas de `1,6 µs` minimum chacun. Conserver des marges après capture des séquences OEM. Les changements de DATA doivent respecter les délais de setup/hold du tableau original.

La trame native contient **11 bits** : sélection d'un ou des deux canaux, atténuation et bits de contrôle. Le sens de transmission, la fonction de chaque champ et l'événement de validation doivent être **repris du diagramme de timing UTC et confirmés sur la radio** ; ils ne sont pas interchangeables avec une commande I²C.

## 3. Reconstitution de la commande GD32

Il reste à trouver les **deux GPIO** ou le circuit de translation qui aboutissent aux broches 4/5, et les **deux sources audio** raccordées aux broches 1/8. La relation avec les potentiomètres `PC2/PC5` est seulement conceptuelle : ces potentiomètres sont mesurés par ADC du GD32, qui pourrait recalculer l'atténuation, mais la correspondance n'a pas été tracée.

À rechercher dans V1.21 : fonction d'écriture à 11 cycles d'horloge, appels au mouvement des boutons de volume, code de mute, reprise de veille, ordre d'envoi des deux canaux. Les routines natives d'origine ne doivent pas être prises pour des adresses universelles d'un firmware autonome.

## 4. Qualification matérielle

1. Poste hors tension : relever la continuité entre broches 4/5 et réseau de transistors/MCU ; entre 1/2/7/8 et amplificateurs.
2. Poste allumé sans TX : mesurer VCC, niveaux logiques CLOCK/DATA et trames pendant variation du volume A et B.
3. Rejouer ces trames **uniquement dans le banc** pour valider l'encodage, sans injection sur le poste réel.
4. Déterminer si U2429 reçoit les deux voies indépendantes ou un mix stéréo, et si la coupure intervient ailleurs.

**Référence constructeur :** <https://www.unisonic.com.tw/uploadfiles/836/part_no_pdf/U2429.pdf>

## 5. Format de la trame documenté par UTC

Les **onze bits D0 à D10 sont transmis dans cet ordre** et lus sur le **front montant CLOCK**. Le constructeur indique un mécanisme de latch sur front descendant à la fin du paquet, avec D9 et D10 tenus à 1. L’ordre de tension DATA doit être vérifié au scope sur le D578 avant tout usage matériel.

| Bits | Signification de la fiche UTC |
| --- | --- |
| D0 | `0` = deux canaux réglés en même temps ; `1` = un seul canal |
| D1 | `0` = canal 1 ; `1` = canal 2 (utile si D0=1) |
| D2..D6 | Atténuation grossière, pas de **4 dB** ; ordre LSB-first, code 21 pour 0 dB, 1 pour −80 dB |
| D7..D8 | Atténuation fine, pas de **1 dB** ; code 3 pour 0 dB, 2 pour −1 dB, 1 pour −2 dB, 0 pour −3 dB |
| D9..D10 | Deux bits à **1** pour terminer/valider la trame |

Pour une atténuation entière `A` de 0 à 83 dB, le codage extrait de la table constructeur est `coarse = 21 - floor(A/4)` et `fine = 3 - (A % 4)`. Exemple : A=0 donne `D2..D6=10101`, `D7..D8=11` ; A=83 donne `10000` et `00`. Les bits sont affichés dans l'ordre **D2 vers D6 / D7 vers D8**, pas dans l'ordre traditionnel d'un nombre écrit sur 5 bits.

Un encodeur C **sans GPIO**, compilable sur ordinateur, est livré dans `firmware/hal/serial_command_encoders.c` avec tests dans `firmware/tests/test_serial_command_encoders.c`. **Il ne prouve pas l’accès au U2429 du D578** et ne permet pas de forcer ses lignes.
