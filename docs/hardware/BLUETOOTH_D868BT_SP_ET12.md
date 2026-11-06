# Carte Bluetooth D868BT-SP, module radio blinde et firmware ET12

**Perimetre :** AnyTone D578UV PRO GD32 V1.21 en priorite ; observations de variantes PLUS et comparaisons D878. **Etat :** interface logicielle partiellement caracterisee, identification physique du module blinde et brochage non verifies. Date : 5 novembre 2026.

## 1. Inventaire de trois niveaux distincts

| Niveau | Ce qui est documente | Niveau de preuve |
| --- | --- | --- |
| Carte support | Une carte fille interne est marquee **`D868BT-SP`** selon le releve sur le poste. Elle porte un deuxieme PCB soude. | **Observation du poste** (designation de variante/position a preciser lors des photos). |
| Module BT blinde | Le deuxieme PCB possede un capot/blindage metallique. Le modele precis du SoC en dessous **n'est pas lu**. | **Observation du poste** ; hypothese BK3260 uniquement par comparaison d'une ancienne generation D878. |
| Micrologiciel / API logique | Identifiant connu : `ET12_AQQX_V10043` ; reference d'image `B707_Audio_AGHF_ET12_QX-V10043.bin`. | **Documentation fabricant** et **modele de banc** (`bench/uart_serial.py`). Ne prouve ni le SoC reel ni l'identite des PCB entre modeles. |

Le marquage **`D868BT-SP` ne demontre pas** que la carte est electroniquement identique a celle des D878, ni que le shield renferme un BK3260. Une publication sur les D878 historiques decrit BK3260 et parfois BK2452 ; le D878UVII ajoute une architecture Bluetooth/APRS avec un autre firmware/circuit. Il faut donc distinguer carte support, carte Bluetooth sous blindage et carte APRS/FM additionnelle. La carte **RF de reception AM** du D578 PLUS est encore un autre sous-ensemble.

## 2. Architecture logique de travail

```text
MCU GD32F303 (D578 PRO / PLUS, selon relevés)
   |
   +-- UART3 logique observee dans le banc  --> [support D868BT-SP ?]
   |                                              |
   |                                              +-- [module radio ET12 ? sous shield]
   |                                                       |
   |                                                       +-- Liaison BT audio + commandes --> BT01
   |                                                       +-- Liaison PTT et etat batterie --> BP-02
   |                                                       +-- Casque / mains libres BT
   +-- Chemin audio analogique (mapping exact au module : INCONNU)
   +-- Controle radio/PTT (aucun GPIO PTT Bluetooth materiel attribue)
```

Les fleches UART3 et module sont fonctionnelles, **pas des pistes PCB identifiees**. Ne pas presenter les pins PC10/PC11 ou d'autres pins comme des connexions confirmees a ce stade. Le manuel Bluetooth constructeur et son guide BT01 prouvent les fonctions, pas le cable interne.

## 3. Dialogue firmware connu sur UART3 : perimetre exact

Le simulateur local `bench/uart_serial.py` emule **UART3** avec un pair facultatif ET12. Il comprend **seulement** le jeu de commandes AT ci-dessous. La qualite de preuve est limitee au modele existant et a la reference binaire dont les reponses ont ete extraites ; aucune capture sur le vrai PCB n'a encore ete comparee.

| Commande envoyee par le GD32 | Reponse dans le modele ET12 | Interpretation prudente |
| --- | --- | --- |
| `AT+VER?\r\n` | `\r\n+VER:ET12_AQQX_V10043\r\n` | Interrogation de version. |
| `AT+AGHF=0\r\n` | `\r\n+AGHF:0\r\n` | Regle un etat AGHF a 0. |
| `AT+AGHF=1\r\n` | `\r\n+AGHF:1\r\n` | Regle un etat AGHF a 1. |
| `AT+AGHF?\r\n` | `\r\n+AGHF:0` ou `:1` suivi de `\r\n` | Lit l'etat AGHF courant. |

- Les octets `\r\n` representent `0D 0A` ; les commandes non reconnues provoquent dans le banc un **arret explicite**, pas un `OK` fabrique.
- `AGHF` est un etat du **modele** ; sa semantique complete (profil audio, activation mains libres, routage, etc.) **n'est pas qualifiee**. Ne pas en deduire un controle audio a partir de son nom.
- `BT_SHA` du banc pour l'image de reference ET12 : `b712048f8e0a3c352b68e8c213894c12d1341756f4ef7d9e435d4a487e3ff40f` (a verifier uniquement contre le binaire que possede l'utilisateur).
- Autres informations presentes dans l'OEM possibles : appairage, nom, batterie, PTT, audio, watchdog, reprogrammation ; **pas encore decodees dans ce modele**.
- **Ni l'adresse du peripherique UART3 en memoire, ni un numero de pin MCU, ni le baudrate reel ne suffisent a definir le cable interne**. On doit extraire et verifier les initialisations RCC/GPIO/AF et comparer a la mesure.

## 4. Versions et mises a jour, sans interchanger les images

| Bloc | Reference / contrainte constructeur |
| --- | --- |
| Programme principal du poste | V1.x pour les modeles D578UV PRO GD32 ; le PLUS suit son propre jeu d'images. Le MCU similaire n'autorise PAS le croisement des images. |
| DSP / DMR | SCT3258, micrologiciel distinct. |
| Bluetooth interne ET12 | `ET12_AQQX_V10043` ou version prise en charge par le modele ; mise a jour officiellement proposee via Android et l'utilitaire Bluetooth constructeur. |
| BT01 | Firmware **propre au microphone**, mis a jour separement via USB depuis l'outil constructeur. |
| PLUS APRS / BT | Carte ou firmware supplementaire pour le RX APRS ; ne pas l'assimiler a `D868BT-SP` sans photo et continuite. |

Pour les versions de compatibilite et leurs limites, consulter le guide BT01 officiel. Un paquet de mise a jour Bluetooth ET12 n'est **pas** une image GD32 ni une preuve du silicium contenu sous le blindage.

## 5. Comment retrouver la liaison dans le firmware constructeur V1.21

1. **Analyse statique, sans poste :** retrouver les chaines `AT+VER?`, `AT+AGHF`, `ET12`, `Bluetooth`, `PTT`, `RfBT`, les appels de transfert de caracteres `\r\n`, puis etablir les *xrefs* en Ghidra.
2. Remonter jusqu'aux routines d'initialisation UART3 (horloge RCC, nombre de bits, parite, stop, diviseur de baud, IRQ, DMA si applicable). Aucune valeur de baud n'est revendiquee ici.
3. Retrouver le pinmux GPIO applique **a l'initialisation OEM** ; les broches doivent etre etablies par les ecritures de registres et validees contre le MCU, pas par un nom peripherique ou une datasheet generique.
4. Etablir le dispatch des commandes AT/reponses et les transitions d'etat (BT off/ready/pairing/connected/BT01 mode). Differencier donnees de controle et audio.
5. Localiser les options OEM et tables *codeplug* : `BT On`, `BT PTT Pair`, `PTT Hold`, `PTT Sleep`, gains de RX/TX et reglage de commande BT01. **Les adresses OEM et les offsets de NAND ne sont pas encore attribues**.
6. En hardware : controler `GND`, rails 3,3/5 V, `TX`, `RX`, `EN`, `RST`, `STATE`, lignes audio et sortie antenne du connecteur entre **carte support** et GD32. Relever le nombre de pads ; photographier les deux faces, sans dessouder pour le moment.
7. Capturer au niveau logique **passivement** en ecoute, au demarrage, pendant `BT On`, appairage du PTT, connexion BT01, changement de canal, reception puis transmission sur charge adaptee en environnement de test reglementaire. Chaque trace doit enregistrer horodatage, direction, baud, bytes hex et contexte.

**Limite de ce travail** : le binaire OEM V1.21 complet n'est pas dans les sources publiques presentes ici ; une nouvelle adresse de routine ou de GPIO Bluetooth non deja verifiee serait donc inventee. Les utilitaires `tools/audit_bluetooth_strings.py` et `tools/decode_bt_uart.py` permettent une premiere qualification **lecture seule**, si l'image ou la trace originale est fournie.

## 6. Matrice d'observations a completer

| Fonction | Logiciel disponible | Physique manquant |
| --- | --- | --- |
| Presence/version | ET12 V10043, `AT+VER?` du modele | Reponse reelle, sortie UART3 sur connecteur |
| Mise sous tension et reset | Menus OEM ; modele AT limite | Broche enable/reset, polarite, rail alimente |
| Audio RX | Support audio dans le produit | Entrée/sortie et niveau, mute, branchements codec/amplis |
| Audio TX | Support microphone BT01/casque | Injection vers FM/DMR, ajustement gain, protection PTT |
| PTT BP-02 | Mode momentane/verrouille dans le manuel | Trame radio/AT reelle, timeout et deconnexion |
| BT01 / gestion ecran | Etats et menus dans la notice | Transport des donnees d'affichage, protocole de synchro et priorite UI |
| Parametres memorises | Champs exposes dans le CPS et qdmr | Adresse NAND, format exact, CRC/migration |
| Firmware interne | Nom ET12 et outils de MAJ | Bootrom/module SoC, dump/hashes, format image et secu de MAJ |

## 7. References externes verifiables

- Manuel Bluetooth AnyTone D578 : <https://www.csi-radios.com/content/support/AnyTone/AT-D578UV/BT%20manual.pdf>
- Guide officiel BT01 : <https://support.bridgecomsystems.com/hubfs/Tech%20%28AnyTone%29/BT01_user_manual_221121.pdf>
- Conditions de mise a jour / BT01 : <https://www.bridgecomsystems.com/pages/bluetooth-speaker-mic-quick-start-guide>
- Methode de mise a jour Bluetooth ET12 pour D578/D878 : <https://pnwdigital.net/wp-content/files/documents/Anytone/BT_FW_Upgrade_578_878.pdf>
- Sources techniques familiales D868/D878 : <https://radio.carstenbauer.net/878techmods.htm>
- Photographies internes D578 : <https://radio.carstenbauer.net/578techmods.htm>
- QDMR, structures de parametres Bluetooth (definitions semantiques, pas offsets OEM prouvés) : <https://static.dm3mat.de/qdmr/manual/ch04s04.html>
- Logiciel du banc : `bench/uart_serial.py`, `bench/test_uart_serial.py`, `bench/emulate_lcd_v121.py`.
