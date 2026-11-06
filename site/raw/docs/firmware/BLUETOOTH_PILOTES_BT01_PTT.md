# Firmware alternatif : couches Bluetooth D868BT-SP / ET12, BT01 et PTT BP-02

**Objectif :** reimplementer proprement le controle Bluetooth sans depender des adresses RAM de l'OEM. **Etat actuel :** specification de developpement, *pas* de pilote radio valide sur PCB et *pas* d'image flashable.

## 1. Separation minimale des responsabilités

| Module propose | Responsabilite | Dependance a qualifier |
| --- | --- | --- |
| `hal/uart_bt.c` | USART3 logique, interruption RX, tampon circulaire, compteur erreurs, timeout, pinmux verifie | UART physiquement connectee, frequence et baud exacts |
| `drivers/et12.c` | Format commandes/reponses AT, interrogation version, activation, etat de liaison | Toutes commandes necessaires a appairage et audio, exactitude de la V10043 |
| `app/bt01_remote.c` | Etat distant, touches, rendu, synchronisation zones/VFO, sortie mode distant | Trames de synchronisation BT01 non decodees |
| `app/bt_ptt.c` | Arbitrage PTT filaire/BT01/BP-02, timeout et interlock TX | Format evenements BT PTT et traitement de la deconnexion |
| `drivers/bt_audio.c` | Commutations micro/HP, gain, mute, coexistence codec/FM/DMR | Brochage et routine audio analogique non traces |
| `storage/bt_settings.c` | Parametres accessibles dans l'IHM et persistants | Format et emplacement des parametres du codeplug |

Ne pas multiplier les couches : HAL UART + protocole ET12 + gestionnaire d'etat distant/PTT suffisent initialement, tant que l'audio n'est pas qualifie. Le projet doit rester leger et deterministe.

## 2. Jeu de commandes teste en simulation existante

```text
TX AT+VER?\r\n      RX \r\n+VER:ET12_AQQX_V10043\r\n
TX AT+AGHF=0\r\n    RX \r\n+AGHF:0\r\n
TX AT+AGHF=1\r\n    RX \r\n+AGHF:1\r\n
TX AT+AGHF?\r\n     RX \r\n+AGHF:0|1\r\n
```

La notation `0|1` represente les deux reponses possibles ; **elle n'est pas une reponse literale**. Ces valeurs viennent du *pair* simule `bench/uart_serial.py` et des tests `bench/test_uart_serial.py`, pas d'un log d'UART de la radio physique. Les commandes inconnues sont interdites dans le modele, pas remplacees par `OK`.

## 3. Contrats obligatoires avant PTT BT

- Bloquer TX par defaut au boot, au reset Bluetooth, en absence de liaison ou en cas d'erreur UART/protocole.
- Accepter une demande PTT uniquement apres validation mode/canal/frequence, et lever le TX a la relache ou a un timeout independant du module ET12.
- Coordonner BT01, BP-02, PTT filaire, VOX, DMR (TDMA) et affichage A/B : aucune priorite n'est supposee OEM sans trace.
- Verifier l'arbitrage des sources audio par les signaux reels, jamais par ecriture opportuniste dans la RAM OEM.
- Ne pas envoyer de sequences d'update/module ni reprogrammer le firmware ET12 pendant la caracterisation.

## 4. Etapes du portage

1. Capturer l'echange V1.21 au demarrage en lecture seule (`BT off`, `BT on`, interrogation version) et le relire par `tools/decode_bt_uart.py`.
2. Retrouver la routine UART/GPIO en Ghidra avec les chaines de la ROM via `tools/audit_bluetooth_strings.py`; sauvegarder la plage, les references et les valeurs de baud.
3. Reproduire uniquement l'interrogation de version et le timeout, sur banc avant poste physique.
4. Ajouter appairage PTT et BT01, synchrone / asynchrone en separant leurs etats, en utilisant une trace reellement observee.
5. Tracer la chaine audio et les signaux `mute`, `gain` et HP. Programmer les niveaux uniquement apres qualification du routage.
6. Ajouter tests de non-regression (reception duale, GPS/APRS, satellite, boot, NAND, USB, DFU, TX inhibit).

## 5. References

- [Carte D868BT-SP et ET12](../hardware/BLUETOOTH_D868BT_SP_ET12.md)
- [Microphone BT01](../hardware/BT01_MICROPHONE_BLUETOOTH.md)
- [PTT BP-02](../hardware/BP02_PTT_BLUETOOTH.md)
- Sources `bench/uart_serial.py`, `bench/test_uart_serial.py` ; documents fabricant dans les fiches ci-dessus.
