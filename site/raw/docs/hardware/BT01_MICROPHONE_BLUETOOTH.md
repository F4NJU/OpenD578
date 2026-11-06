# Microphone sans fil AnyTone BT01 : fonctions, protocole a retrouver et integration

**Cibles :** AnyTone D578UV PRO/PLUS. Le BT01 est un terminal externe **avec son propre firmware, afficheur, clavier, batterie, microphone et haut-parleur**, pas seulement une capsule audio BT. La liaison vers le poste peut etre **Bluetooth** ou **filaire par cable 4 m** ; ces deux modes ne se confondent pas avec le protocole du microphone d'origine.

## 1. Architecture des flux

```text
                     Liaison Bluetooth 2,4 GHz
D578 [GD32] -- UART? -- [module ET12]  <-----------------> [BT01]
   |                |                                         |
   |                +--- voies audio a tracer                +-- Afficheur, clavier
   |                                                          +-- Micro et haut-parleur
   |                                                          +-- PTT, P1/P2/P3, charge USB
   |                                                          +-- MCU et firmware propres
   +------------------ port microphone / cable 4 m ----------+
```

Le manuel qualifie une synchronisation d'etat/menus entre BT01 et radio. **Aucune trame binaire du protocole de prise de controle d'ecran n'est documentee ici.** Les paquets `41 ... 06` et `53 ... 06` concernent le microphone filaire standard et **ne sont pas automatiquement ceux du BT01**, meme si une prise ressemble a un RJ45.

## 2. Etats fonctionnels constructeur

| Etat BT01 | Etat radio attendu | Donnees a observer |
| --- | --- | --- |
| Alimentation BT01, choix `BT MODE`/`CABLE MODE` | Aucun lien ou recherche | Niveau et version des deux terminaux. |
| `BT MODE`, « NO DEVICE CONNECTED » | Recherche BT / appairage | Noms d'appairage, ouverture de session ET12. |
| `ALL DATA CHECKING` | Synchronisation des menus et parametres | Quantite de donnees, ordre/CRC, timeout, reprise, source exacte. |
| `EXTERNAL BT MODE` | Mode de controle distant | Verrouillage des touches/ecran du poste, gestion PTT, RX/TX, canaux. |
| `EXTERNAL CABLE MODE` | BT01 connecte en filaire | Flux du connecteur microphone : niveaux et trames differents possibles. |
| Deconnexion / extinction BT01 | Reprise de controle local du poste | Relachement PTT, retour HP/micro, UI et etat BT. |

**Point fonctionnel verifie par le guide** : en mode BT01 connecte, plusieurs commandes facade du D578 deviennent indisponibles et son affichage est limite ; la voie audio et certains modes (notamment cross-band) subissent des contraintes de coexistence. Un firmware alternatif doit prevoir un *mode distant exclusif* et une sortie de secours.

## 3. Organes et reglages a traiter

- **PTT** local BT01, touche d'emission ; securite si perte radio ou batterie faible.
- **Microphone et HP** BT01 ; gains RX/TX independants selon firmware et codeplug (`RfBT Mic Gain`, `RfBT SPK Gain`, `H-BT Mic Gain`).
- **P1/P2/P3** programmables ; appuis bref, long et tres long, gestion au niveau programme radio.
- **CH+/-**, zones, numerotation de canal, saisie VFO, menus; coherence de l'ecran pendant dual-watch, DMR et satellite.
- **POWER** et synchronisation arret du poste selon option CPS (`BT Synchronization Shutdown Host`). Ne jamais couper l'alimentation du GD32 sans une sequence validee pour cette revision.
- **USB-C** de charge et de mise a jour BT01 : ne pas confondre avec le port USB du D578.
- **RJ45/cable 4 m** : connexion alternative, a qualifier electriquement avant tout echange de paquets hors manuel.

## 4. Gestion des firmwares

Le guide constructeur indique des versions distinctes de **firmware principal D578**, **firmware ET12 du poste**, **firmware BT01**, **CPS** et parfois **carte APRS PLUS**. Ne pas charger un firmware ET12 dans le BT01 ni un firmware BT01 dans le GD32. Le BT01 dispose de son propre mode de mise a jour par USB et de son jeu de fichiers constructeur.

## 5. Travail a faire dans le firmware V1.21 et le banc

1. Extraire les points d'entree « External BT Mode », « ALL DATA CHECKING », transitions vers la gestion distante, desactivation de touches P1..P6, synchronisation A/B.
2. Trouver les routines de serialisation des changements d'etat et de commandes BT01, en partant des chaines disponibles et des xrefs et en distinguant le filaire du Bluetooth.
3. Capturer passivement UART du module ET12 et l'interface filaire BT01 pour comparaison des flux avec les meme actions.
4. Decoupler les pilotes : `bt_transport.c`, `bt01_remote_ui.c`, `bt_audio.c`, `bt_ptt.c` et configuration stockee de maniere propre au firmware alternatif.
5. Ajouter des cas de test : reconnexion, perte de signal, boutons maintenus, commande PTT pendant 2 VFO, sat/Doppler, codeplug non pret, audio en cours, retour UI local, arret radio.

Pour un firmware alternatif **tout PTT distant doit tomber a OFF en cas de perte de liaison, reset, timeout ou changement de source non qualifie**. Un etat de touche presse ne doit jamais etre conserve silencieusement apres la deconnexion.

## 6. Sources

- Guide officiel BT01 2022 : <https://support.bridgecomsystems.com/hubfs/Tech%20%28AnyTone%29/BT01_user_manual_221121.pdf>
- Notice d'utilisation BT01 : <https://support.bridgecomsystems.com/hubfs/Tech%20%28AnyTone%29/BT01_BT_Display_Mic_Instructions.pdf>
- FCC ID BT01 et photographies internes : <https://fccid.io/T4K-BT01>
- Parametres BT01 du codeplug : <https://static.dm3mat.de/qdmr/manual/ch04s04.html>
- Comparaison avec le microphone filaire d'origine : [Notice microphone V11.8](../NOTICE_CHANGELOG_MICROPHONE_V11_8.md).
