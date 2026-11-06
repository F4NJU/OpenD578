# Liaisons inter-composants et niveaux de preuve

La carte interactive utilise le fichier unique `hardware/models/d578uv-pro-gd32-v121.json`. Chaque liaison possede un identifiant, un type de bus, un niveau de preuve, une liste de signaux **si elle est connue**, des reservations et les documents qui etayent les informations.

## Comment interpreter le dessin

- **Materiel observe :** releve effectif sur le poste ou liaison debug testee. Cela ne valide pas necessairement toutes les caracteristiques electriques.
- **Trace constructeur :** GPIO, routine ou commande obtenus par analyse et/ou execution OEM. La continuite physique vers une patte externe peut rester inconnue.
- **Emulation :** niveaux de bus ou transfert reproduits par le banc a partir du pilote OEM, sans mesure de piste.
- **Hypothese :** attribution candidate; ne pas en faire une constante dans un firmware alternatif.
- **Inconnu :** interaction fonctionnelle citee sans correspondance de broches certifiee.

**Rappel de securite :** une broche identifiee en lecture seule ne doit jamais etre pilotee par essai au hasard. En particulier, les zones NAND de calibration et les secteurs Flash de boot doivent rester intacts.

## Liaisons bien documentees cote logiciel

| Source | Destination | Interface | Preuve / limites | Notice |
| --- | --- | --- | --- | --- |
| GD32 | LCD | PE7..PE14, PB10..PB13 | GPIO OEM; continuites FPC non toutes mesurees | [LCD](../LCD_CABLAGE_PILOTAGE_ET_INTEGRATION_V11_8.md) |
| GD32 | NAND | PB8/PB15/PB14/PA15 (candidats) | Pilote OEM et niveaux de bus simules; continuite a confirmer | [NAND](../03_NAND_LECTURES_ECC_CARTE.md) |
| GD32 | Touches, codeur et volumes | PA0, PA1, PB0/1, PC2/5/8/9 | Chemins OEM, essais du banc; placement physique a confirmer | [Facade](../FACADE_GPIO_BOUTONS_CODEUR_VOLUMES_ET_ECLAIRAGES.md) |
| GD32 | Microphone | USART0 PA9/PA10 candidats | Protocole observe et pinout prise publie; sens et continuite a verifier | [Microphone](../NOTICE_CHANGELOG_MICROPHONE_V11_8.md) |
| GD32 | LED et eclairages | PE3/4, PA5, PB3/4 | Commandes OEM observees; chaines LED a cartographier | [Facade](../FACADE_GPIO_BOUTONS_CODEUR_VOLUMES_ET_ECLAIRAGES.md) |
| GD32 | Amplification HP | PA7 et registre RF bank 1/page 0/0x25 bit4 | Selection Speaker Mode observee, amplis non traces | [Microphone](../NOTICE_CHANGELOG_MICROPHONE_V11_8.md) |

| GD32 | Support Bluetooth D868BT-SP / ET12 | UART3 **dans le simulateur** ; aucune pin, frequence/baud ou ligne audio physique assignee | [Bluetooth ET12](BLUETOOTH_D868BT_SP_ET12.md) |
| Module BT | Microphone BT01 | Liaison sans fil, commandes d'ecran, touches et audio ; details de trames non captures | [BT01](BT01_MICROPHONE_BLUETOOTH.md) |
| Module BT | BP-02 | Commandes PTT sans fil ; pas de bus MCU direct etablit | [PTT BP-02](BP02_PTT_BLUETOOTH.md) |

Les interfaces GPS, DMR, Bluetooth, codec audio et RF n'ont pas de table exhaustive de broches propre a la carte GD32. Elles apparaissent comme liaisons **a qualifier**, et non comme cablage certifie.

## Ajouter ou corriger une connexion

Modifier directement `hardware/models/d578uv-pro-gd32-v121.json` avec une liste `pins` et une note `details` indiquant la source; conserver un niveau de preuve explicite. Si une correction resulte d'un nouveau relevé, joindre une photo ou trace non sensible dans `hardware/photos/` et une explication dans un `.md` source. Le site est regenere au prochain commit sur `main`.

### Complément matériel

Consulter [PLAN INVESTIGATION BROCHAGES](PLAN_INVESTIGATION_BROCHAGES.md) et [audit des fonctions partielles](AUDIT_FONCTIONS_PARTIELLES.md).
