Mise à jour V11.5 : voir [USB_CPS_V11_5.md](USB_CPS_V11_5.md).
Le texte ci-dessous conserve le constat antérieur V11.4.1.

# USB et CPS AnyTone — constat du 5 novembre 2026

## Vérifié dans la Flash capturée

Image complète SHA256 : e2f2483baf60e2bfcab656e25e949670713222591ef4d611d6089054819a750e.
L’inspection est statique : le firmware n’a pas encore répondu à une énumération
USB complète dans le banc. Voir USB_V121_DESCRIPTORS.json et l’outil reproductible
`python tools/inspect_usb_descriptors.py full_flash_pass1.bin`.

| Élément | Application V1.21 | Bootloader |
| --- | --- | --- |
| Descripteur périphérique | 0x080F566E | 0x080044C8 |
| VID:PID | 28E9:018A | 28E9:018A |
| Classe périphérique | 02, communications | 02, communications |
| Configuration CDC | 0x080F60FE | 0x08004508 |
| Interface 0 | CDC ACM, classe 02, sous-classe 02, protocole 01 | idem |
| Interface 1 | données CDC, classe 0A | idem |
| Notification | endpoint 0x82, interruption, 8 octets | idem |
| Données PC → poste | endpoint 0x03, bulk, 64 octets | idem |
| Données poste → PC | endpoint 0x81, bulk, 64 octets | idem |
| Contrôle | EP0, 64 octets | idem |

Les chaînes PROGRAM et QX suivi de 06 sont présentes dans l’application.
Cela concorde avec l’implémentation primaire qdmr, lib/anytone_interface.cc :
https://github.com/hmatuschek/qdmr/blob/master/lib/anytone_interface.cc
Source consultée le 5 novembre 2026 ; une concordance de chaînes ne prouve pas
à elle seule tous les chemins d’exécution du firmware capturé.

| Échange de programmation décrit par qdmr | Réponse attendue |
| --- | --- |
| PROGRAM (7 octets ASCII) | QX puis ACK 06 |
| 02 (identification) | structure avec préfixe I, modèle, bandes, version, fin 06 |
| R + adresse big endian sur 4 octets + longueur 10 hex | W + adresse + longueur + 16 octets + somme + 06 |
| W + adresse + longueur + 16 octets + somme + 06 | ACK 06 |

La somme est l’addition modulo 256 des octets adresse, longueur et données,
sans l’octet commande. qdmr configure son port série à 115200. Ce débit CDC
n’est pas un débit UART matériel démontré. Les adresses du protocole de
programmation ne doivent pas être confondues avec des pointeurs MCU ou des
offsets NAND directs. Le CPS constructeur doit encore être observé : il peut
utiliser d’autres commandes, tailles, contrôles de ligne et délais.

## Architecture retenue pour une liaison fidèle

CPS → port COM virtuel A ↔ port virtuel B → pont local du banc → hôte CDC
simulé → contrôleur USB/PMA/IRQ du GD32 → firmware exécuté → NAND virtuelle.
Le navigateur reste l’interface de commande et d’observation du banc.

Un navigateur peut ouvrir un port existant avec Web Serial ; il ne crée pas
un périphérique COM Windows pour une autre application. Sous Windows, il faut
un pilote de ports virtuels ou un périphérique USB virtuel. Le pont Python
local existant permet d’éviter de faire transiter les octets par l’interface web.
Un PTY peut jouer ce rôle pour un client Linux ; le CPS Windows reste à tester
sur son environnement réel et peut avoir des contraintes de détection de ports.

Il n’est pas nécessaire d’émuler un périphérique USB au niveau du système
Windows si le CPS accepte un port COM virtuel choisi manuellement. Si le CPS
filtre les identifiants USB ou utilise des requêtes de pilote spécifiques, cette
solution devra être complétée. Aucun pilote n’est installé automatiquement.

Références primaires sur les interfaces hôte :
https://developer.chrome.com/docs/capabilities/serial
https://learn.microsoft.com/en-us/windows-hardware/drivers/samples/serial-driver-samples

## Ce qui manque encore

1. Énumération réelle du firmware : GET_DESCRIPTOR, SET_ADDRESS,
   SET_CONFIGURATION et transferts de contrôle à plusieurs paquets.
2. Contrôles CDC : SET/GET_LINE_CODING, SET_CONTROL_LINE_STATE et notifications.
3. Files bulk avec ACK/NAK/STALL, découpage 64 octets et réassemblage du flux.
4. Pont entre ces files et le port virtuel ; journal binaire horodaté des deux sens.
5. Essai du CPS d’origine : identification puis lecture, ensuite écriture dans
   une copie NAND virtuelle et relecture après redémarrage du modèle.
6. Délais réels du CPS : le moteur accéléré ne garantit pas de répondre avant
   son timeout. Ne pas synthétiser une réponse à la place du firmware pour masquer
   un retard ou une fonction manquante.

V11.4.1 ne fournit pas encore une liaison CPS fonctionnelle. Le modèle UsbdHost
existant permet des tokens et interruptions en mode matériel, mais ne réalise
pas encore tout l’hôte CDC. Le mode Analyse OEM conserve son modèle USB absent.
Un faux poste qui répondrait directement PROGRAM/QX et lirait une image mémoire
serait un émulateur de protocole distinct : il ne testerait pas la pile USB et
le gestionnaire de programmation du firmware. Ce n’est pas l’architecture visée.
