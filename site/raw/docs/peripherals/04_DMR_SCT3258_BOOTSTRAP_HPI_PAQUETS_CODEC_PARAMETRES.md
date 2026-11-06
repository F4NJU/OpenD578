# 04 - Sicomm SCT3258/CT3258 : boot, HPI, paquets, DMR, codec et memoires

> **RECONSTITUTION du 05/11/2026.** Ce fichier n'est pas l'original homonyme. Les donnees sont qualifiees `datasheet`, `analyse OEM`, `simulation` ou `a verifier sur le PCB`, sans faire passer le banc pour le moteur DMR interne.

## 1. Perimetre materiel

Le circuit Sicomm **SCT3258TD** integre le traitement DMR (couches basses) et la fonction vocoder **AMBE+2** exploitee par l'application OEM. C'est un processeur **distinct** du GD32F303. Selon les datasheets Sicomm consultees par RadioFoundry, il utilise une horloge d'environ **12,288 MHz**, son propre firmware et une **Host Port Interface 8 bits** asynchrone avec FIFO et ligne HOBIB de synchronisation. L'audio codec ↔ SCT passe par un flux numerique serie, pas par les conversions lentes de l'ADC0 du GD32.

Il faut distinguer : (1) programme GD32 dans sa Flash interne, (2) petit **boot block** de 2048 octets envoye au SCT apres reset, (3) firmware applicatif et vocoder conserves dans la Flash interne propre au SCT (selon datasheet/portage), (4) parametres utilisateurs et calibrations dans la NAND du poste, (5) configuration volatile/temporisations de session DMR.

## 2. HPI dans le modele GD32 V1.21

`bench/sct_hpi.py` decrit le bus reconstruit depuis des ecritures GPIO OEM :

| Fonction SCT | Ligne GD32 candidate | Broche LQFP100 MCU | Preuve actuelle |
| --- | --- | ---: | --- |
| HCSN (chip select actif bas) | `PD2` | 83 | Decodage GPIO en simulation OEM |
| HWRN (write strobe) | `PD3` | 84 | Decodage GPIO en simulation OEM |
| HRDN (read strobe) | `PD4` | 85 | Decodage GPIO en simulation OEM |
| HOBIB (data ready / handshake) | `PD5` | 86 | Role deduit par le modele, continuite inconnue |
| HPI DATA0..7 | `PD8..PD15` | 55..62 | Mode GPIO 8 bits observe dans le modele |
| Reset, alimentation, 12,288 MHz, PIO | inconnu | - | Non mesures physiquement |

Ne pas confondre les labels **HWRN/HRDN** du SCT avec une fonction EXMC choisie automatiquement par le GD32. Le modele active le bus par GPIO et inspecte les niveaux d'entree; pas de preuve d'utilisation materielle EXMC sur la version PRO.

## 3. Boot : 1024 mots de 16 bits

Documentation de la famille SCT3258 : apres reset, le processeur attend **1024 mots de 16 bits**, soit **2048 octets**, sur HPI, en ordre des octets documente par son protocole. Ce bloc charge un second etage qui demarre le firmware interne SCT. Une reponse de boot est decrite dans la reference Sicomm par le paquet `84 A9 61 00 02 20 17 01`.

RadioFoundry donne le SHA256 d'un bloc identique sur plusieurs firmwares 868/878 et D578 **GD 2.08** :

`743515b9f7cd90737c1fff29b652b7558bc5a56487ec38df4fdea8877e7a619a`

**Attention :** cette empreinte n'est **pas ici une verification sur la CDD PRO GD V1.21 de l'utilisateur**. Les modes 0..3 et les quelques octets de patch mentionnes par RadioFoundry sont specifiques a leur analyse; ne pas imposer un mode sans tracer les conditions du firmware V1.21. Le bloc est un logiciel constructeur/Sicomm, non redistribue dans le depot GitHub.

Un futur pilote doit implementer une machine d'etats :

`POWER_OFF -> GPIO_INPUT -> CLOCK_STABLE -> SCT_RESET -> WAIT_BOOT_READY -> SEND_BOOT_BLOCK -> READ_BOOT_ACK -> CONFIGURE_HPI -> CONFIGURE_MODE -> CONFIGURE_CODEC -> DMR_READY`

Toute erreur de longueur, statut, timeout ou tension doit mener a un **etat non emissif**, plutot qu'a une boucle de commandes RF ou a un TX silencieusement actif.

## 4. Format de paquet HPI et jeu de commandes

La classe `SctHpi` du banc decode des paquets structures avec **en-tete `84 A9 61`**, champ longueur (deux octets, ordre observe dans le code), type et charges utiles. Elle simule le paquet de boot et plusieurs types de requetes selon les champs acceptes. Les registres enumerees dans le code ne sont pas une transcription exhaustive du firmware interne de la puce.

| Groupe | Exemples de fonctions connues dans la litterature / modele | Statut |
| --- | --- | --- |
| Boot/handshake | 2048 octets, reponse type 0x20 / 0x17 | Datasheet + modele ; timing poste non mesure |
| Configuration radio analogique | `ANALOG_CONFIG`, `CTC_PARAM`, `ANALOG_SUBAUDIO`, `SQ_LEVEL` | Spec externe et traces OEM partielles |
| Gain/calibration | `MOD_GAIN`, `DEMOD_GAIN`, `DIGI_MIC_GAIN`, `DIGI_SPEAKER_GAIN`, `DC_OFFSET`, `IQCOMP_COEF`, `AFC_CONFIG`, `MODOUT_CONFIG` | Noms de familles protocolaires, valeurs usine inconnues |
| Codec TLV320AIC3204 | `SET_I2C_ADDRESS`, `I2C_OPERATION`, `CODEC_SELECT` et bypass type `0x40` | Spec externe + parseur de paquets dans bench/sct_hpi.py |
| DMR voix/donnees | modes DMR, trames et evenements 60 ms TDMA, ID DMR/call setup | Modes a decodage incomplet dans le banc |
| Identite SCT | Requete de version avec reponse conditionnee par image de reference dans banc | Pas preuve d'interrogation physique du poste actuel |

Exemple interne du banc : si la condition de bypass codec est active et la charge utile est une serie de paires `(registre, valeur)`, les transactions sont enregistrees dans `codec_writes`. Les registres AIC sont pagines et le chemin de commande passe par le SCT : **on ne doit pas lancer un pilote I2C autonome directement sur deux GPIO GD32 supposes**.

## 5. Firmware interne SCT et mise a jour distincte

Le **Boot Mode for Sct** affiche par le poste est une fonction de maintenance du baseband et **n'est pas** le mode de mise a jour de l'application GD32. Le logiciel constructeur peut exposer un pont USB/COM vers le port SCT. Une source externe detaille l'outil `SCT_PORT` et un fichier `SCT3258TD_UpdateFlash_V2_01_07BF.hex` ; dans notre banc, l'identite de ce fichier est controlee par SHA256 :

`d5ada473af891b6c707978f0b9dde81324afcc4af27348d3bcdf70615ab19407` (taille **603 102 octets** telle qu'attendue dans `bench/sct_hpi.py`).

Ce fichier est **une reference du modele**, pas un firmware libre ni un blob a programmer. Il peut contenir du code proprietaire et des sections de vocoder. Aucun octet de ce firmware ne doit etre publie comme composant de l'archive source.

## 6. Relation avec RF, codec et parametres usine

Le SCT gere des traitements numeriques qui influencent audio, deviation, CTCSS, DMR, squelch et calibration. Les **quatre QA4818N** et les etages analogiques RF constituent un autre sous-systeme, controle depuis le GD32 par un bus serie distinct (quatre chip selects dans le modele). La liaison exacte entre evenements SCT, frequences des QA et gates PA doit etre mesuree/decodue.

Le rapport NAND situe des zones critiques autour de `0x02F00000..0x02FDFFFF`. On peut chercher les champs de gain/offset dans ces secteurs, mais **aucune correspondance valeur NAND -> commande SCT -> registre DAC physique** n'est certifiee dans la seule lecture de cette documentation. Une valeur de puissance PA incorrecte peut endommager le poste ou causer une emission hors specification : ne pas lancer d'experience TX.

## 7. Etat du modele et tests manquants

La simulation HPI **n'execute pas** le processeur interne, le vocoder AMBE ou les chaines RF/audio physiques. Elle peut valider des formes de paquets, des sequences et l'adressage GPIO observe par l'application OEM, pas le fonctionnement d'un DMR complet. Pour qualifier un driver autonome :

1. Capturer passivement HPI DATA/HCSN/HWRN/HRDN/HOBIB en reception, au boot et lors d'un changement de canal en **mode non emissif**.
2. Mesurer lignes RESET et horloge 12,288 MHz sans charger le quartz ; relever les niveaux logiques pour les domains 1,2 V / 2,5-3,3 V.
3. Comparer les trames a la reference « Packet Interface of CT3258 » et relever toutes les commandes inconnues, sans inventer de reponse.
4. Recuperer le boot block du **firmware OEM appartenant a l'utilisateur**, calculer empreinte et comparer avant tout essai ; ne pas publier le bloc.
5. Tester la lecture des messages, identification et commandes non TX d'abord ; ne jamais valider RF uniquement sur un ACK SCT.
6. Garder un watchdog/timeout independant en cas de reset du SCT, disconnection HPI ou desynchronisation de slot.

## 8. Sources

- Projet : `bench/sct_hpi.py`, `docs/04_RAM_ROUTINES_UI_RF_ET_BROCHAGE.md`, `docs/02_CPU_FLASH_BOOT_USB_SWD.md`, `docs/03_NAND_LECTURES_ECC_CARTE.md`, `docs/hardware/DMR.md`.
- RadioFoundry, architecture AnyTone et caracteristiques SCT : <https://radiofoundry.org/docs/spec/hardware-anytone>.
- Sicomm, datasheet CT3258 : <https://cdn.hackaday.io/files/1642237026116832/CT3258_datasheet.pdf> ; SCT3258 : <https://cdn.hackaday.io/files/1642237026116832/SCT3258_datasheet_v2_0.pdf> ; Packet Interface v1.0 : <https://cdn.hackaday.io/files/1642237026116832/CT3258_Packet_Interface.pdf>. **Licences non etablies : lier, ne pas redistribuer.**
- Mise a jour DMR distincte et pont USB : <https://radiofoundry.org/docs/spec/hardware-anytone>.
