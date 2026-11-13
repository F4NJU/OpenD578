# Première liaison CPS sur l'alpha OpenD578 — variante de banc

Cette variante ajoute à l'alpha RX FM de F4EGM une liaison USB CDC en lecture
seule. Elle n'utilise ni firmware constructeur, ni capture NAND, ni adresse de
structure OEM. Les deux VFO sont lus depuis les variables propres à l'alpha.
Le code optionnel est activé uniquement avec `OPEND578_CPS_READONLY`.
Les binaires `rx_fm_alpha.bin/.elf` existants ne sont pas remplacés.

**Binaire : `browser-bench/samples/rx_fm_cps.bin`, réservé au banc matériel.**
Il ne s'agit pas d'un paquet constructeur à installer sur un poste. Le pull-up
USB de la carte, le branchement USB physique et les pilotes Windows ne sont pas
qualifiés. Les identifiants USB `FFFF:0578` sont des identifiants expérimentaux
de laboratoire, sans allocation officielle pour un produit.

## Architecture et périmètre

- `hal/usb_cdc_poll.[ch]` : registres USBD/PMA, EP0 de contrôle, EP1 bulk IN/OUT,
  interface CDC et EP2 de notification réservé. Traitement polling, sans IRQ USB.
- `cps/readonly_protocol.[ch]` : parseur borné, sans MMIO, allocation ni stockage.
- `rx_fm_alpha/main.c` : copie l'état courant de A/B et alimente ce service dans
  la boucle principale. Une action sur le codeur reste traitée par l'alpha.
- `hal/freestanding_memory.c` : petits auxiliaires ABI requis par le compilateur.

La configuration de l'horloge choisit nominalement PLL120 / 2,5 pour USB avant
d'activer l'horloge du contrôleur. Ce calcul et les transactions de registres sont
vérifiés par le banc, pas mesurés sur une carte. Référence matérielle :
[GD32F30x User Manual Rev2.9](https://www.gd32mcu.com/data/documents/userManual/GD32F30x_User_Manual_Rev2.9.pdf),
chapitres RCU et USBD. Les écritures EP respectent les champs STAT/DTOG à bascule
et CTR à effacement sur zéro ; les demi-mots PMA ont un espacement CPU double.

L'énumération testée utilise GET_DESCRIPTOR device/configuration, SET_ADDRESS,
SET_CONFIGURATION, SET_LINE_CODING et SET_CONTROL_LINE_STATE ; GET_LINE_CODING
est implémenté aussi. Les autres requêtes de contrôle non reconnues sont STALL.
Ce sous-ensemble n'est pas présenté comme une pile USB matérielle complète.

## Protocole de recherche `opend578-cps`, version 1

Requêtes ASCII, au plus 63 caractères hors LF :

```text
OD578/1 1 HELLO\n
OD578/1 2 VFOS\n
```

`\n` représente un seul octet LF. L'identifiant est un entier 1–65535, renvoyé
dans la réponse. Une réponse est un objet JSON terminé par LF, au plus 384 octets.
Les fragments de paquets USB ne sont pas des frontières de message.

HELLO renvoie `protocol`, `version`, `id`, `firmware` et `capabilities`. Cette
alpha annonce uniquement `vfoRead: true`. Les capacités `vfoWrite`, `memories`,
`ctcss`, `dcs`, `tx` et `persistent` sont explicitement fausses.

VFOS renvoie `selected` (A ou B), puis deux objets avec `id`, `rxHz` en Hz entiers,
`bandwidth` (`wide`/`narrow`) et `txInhibit: true`. Une tonalité absente de ce
protocole signifie non prise en charge, pas CTCSS désactivé. Aucun faux nom de
canal, fréquence TX ou contenu de mémoire n'est fabriqué.

Une commande inconnue donne `unsupported_command`, une trame mal formée
`bad_request` avec id 0. Une ligne trop longue est écartée jusqu'au prochain LF.
Aucune commande d'écriture, adresse brute, PROGRAM, R/W constructeur ou END
n'existe dans ce service. Les lectures peuvent se succéder sans reset.

## Construction et vérification

Depuis une copie complète du dépôt, avec Python et les dépendances épinglées du
banc, puis Zig 0.15.2 (vérifié sur Windows x64) :

Le compteur natif du banc doit déjà être compilé, selon sa procédure habituelle
(`python bench/build_native.py --cc COMPILATEUR_C`, avec GCC/Clang). La copie
locale préparée pour Maxime possède déjà ce compteur. Le vérificateur de parseur
hôte fourni ci-dessous est spécifique à Windows x64 ; le fichier de tests C
est indépendant et peut aussi être compilé avec un compilateur hôte adapté.

```powershell
python tools/build_rx_fm_cps.py --zig CHEMIN_ZIG --out-dir bench/work/rx-fm-cps
python tools/verify_readonly_protocol_host.py --zig CHEMIN_ZIG
python tools/verify_rx_fm_cps.py bench/work/rx-fm-cps/rx_fm_cps.bin --output bench/work/rx-fm-cps/arm.json
```

Le build utilise directement Clang/LLD pour éviter la dépendance au cache CRT
Windows de `zig cc`. L'image brute est extraite des segments PT_LOAD ELF ARM
par leur adresse physique Flash, en conservant le LMA de `.data`. Aucun binaire
constructeur n'est une entrée de compilation. Empreinte du binaire qualifié :
`d18ec821d63b82bce2b0d7ab18696093dd9376a738e580ca7116fefca6bd1acd` (12 007 octets).
Le manifeste sous `docs/evidence/rx_fm_cps/build.json` indique les empreintes sources.

Résultats reproductibles : 8 contrôles du parseur C hôte ; exécution ARM sur le
modèle matériel, énumération CDC, lecture des VFO 145,500/435,000 MHz puis
145,5125 MHz après une action sur le codeur, refus de WRITE, zéro commande observée
levant PE6/PC4. Le rapport ARM est `docs/evidence/rx_fm_cps/arm.json`.
Ces observations ne constituent pas une mesure RF, une preuve de sensibilité
ou de fonctionnement USB sur poste physique.

Le runner matériel avait un quota d'avancement sans CPU consommé sur toute la
durée d'un appel. Après des WFI/SysTick pourtant actifs, un long appel finissait
par ne plus avancer. Le quota est maintenant renouvelé après une progression
CPU réelle. Un test Thumb synthétique couvre ce cas et le test ARM exécute un
appel continu de 10 millions d'instructions. Aucun saut de code ou réponse USB
n'est ajouté au modèle pour faire passer ce programme.

Le client web est préparé séparément dans la branche CPS du fork F4NJU/OpenD578.
La suite reste à concevoir avec F4EGM : format de mémoires, commandes d'écriture,
persistance et portage réel des fonctions CTCSS/DCS. Les anciennes observations
réussies avec le constructeur ne rendent pas ces fonctions disponibles ici.
