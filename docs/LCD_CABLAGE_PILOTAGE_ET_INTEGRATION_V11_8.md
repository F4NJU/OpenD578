# OpenD578 : câblage, protocole et pilotage du LCD

État des connaissances au 5 novembre 2026, base du banc V11.8.
Cible : AnyTone D578UV PRO, GD32F303VKT6, application OEM GD32 V1.21.

Ce document sert de base à un pilote d’affichage autonome ou à une extension
injectée dans le firmware existant. Il rassemble les broches déduites, les mots
échangés, l’initialisation, les délais et les contraintes de partage du moteur
LCD. Il ne livre pas une image flashable ni un placement RAM/Flash approuvé.

## 1. Ce que nous savons et ce qui reste à mesurer

| Sujet | Résultat | Niveau de preuve |
| --- | --- | --- |
| Module | Marquage HOLITECH FPC-HIB018A011-A1 SLH1920 | Relevé matériel communiqué précédemment |
| Bus de commande et pixels | Parallèle 8 bits, de type 8080, piloté par GPIO | Instructions OEM et transactions exécutées |
| Données | PE7 à PE14, poids faibles vers poids forts | Instructions et décodage des sorties |
| Contrôle | PB10 WR#, PB11 D/C, PB13 CS# | Instructions et transactions exécutées |
| Reset | PB12, impulsion basse dans l’initialisation | Séquence OEM revérifiée |
| Pixels usuels | Fenêtre 128 colonnes × 160 lignes, RGB565 | Transactions et images reconstruites |
| Orientation de présentation | Transposition pour le rendu paysage du banc | Comparaison des images OEM |
| Rétroéclairage | Autre bus, canal 8 | Appels OEM et trames GPIO décodées |
| Contrôleur LCD exact | Non identifié avec certitude | Protocole compatible avec la famille ST7735, sans lecture d’identifiant |
| Numéros des contacts FPC | Non établis dans ce travail | Continuité à relever |
| Tensions et fronts électriques | Non mesurés ici | Mesures sur carte nécessaires |

**Le câblage ci-dessous est une cartographie côté MCU issue du firmware.** Ce
n’est pas un relevé de continuité entre chaque patte du GD32 et chaque contact
de la nappe. Le marquage du module ne suffit pas à identifier le silicium LCD.

## 2. Bus LCD côté GD32

| Signal LCD | GPIO MCU | Masque | Comportement dans le firmware |
| --- | --- | --- | --- |
| D0 | PE7 | 0x0080 | Bit 0 de l’octet |
| D1 | PE8 | 0x0100 | Bit 1 |
| D2 | PE9 | 0x0200 | Bit 2 |
| D3 | PE10 | 0x0400 | Bit 3 |
| D4 | PE11 | 0x0800 | Bit 4 |
| D5 | PE12 | 0x1000 | Bit 5 |
| D6 | PE13 | 0x2000 | Bit 6 |
| D7 | PE14 | 0x4000 | Bit 7 |
| WR# | PB10 | 0x0400 | Impulsion basse ; octet retenu au front montant |
| D/C | PB11 | 0x0800 | 0 : commande ; 1 : paramètre ou pixel |
| RESET# candidat | PB12 | 0x1000 | Haut, bas, puis haut au démarrage |
| CS# | PB13 | 0x2000 | Bas pendant les écritures |
| RD# | Non retrouvé | Non attribué | Pas de lecture LCD démontrée dans le chemin étudié |

Le bus n’est pas traité ici comme une mémoire EXMC/FSMC. Les routines observées
écrivent les registres GPIO. La présence de broches partageant des fonctions
alternatives ne signifie pas que ces fonctions sont utilisées.

### Registres exploités

| Registre | GPIOB | GPIOE | Usage |
| --- | --- | --- | --- |
| CTL0 | 0x40010C00 | 0x40011800 | Configuration broches 0 à 7 |
| CTL1 | 0x40010C04 | 0x40011804 | Configuration broches 8 à 15 |
| OCTL | 0x40010C0C | 0x4001180C | Verrou de sortie |
| BOP | 0x40010C10 | 0x40011810 | Mise à un, et remise à zéro par la moitié haute |
| BC | 0x40010C14 | 0x40011814 | Remise à zéro |

La routine `0x0808B624` configure le masque `0x7F80` sur GPIOE et `0x3C00`
sur GPIOB. La structure passée au configurateur utilise vitesse `3` et mode
`0x10`, qui produisent le nibble GPIO `0x3` : sortie générale push-pull avec
sélection de vitesse maximale de cette interface GPIO. Cette sélection n’est
pas une fréquence de bus LCD de 50 MHz.

Les bits des autres broches doivent être conservés. En particulier, PE3/PE4
servent à un autre bus de voyants et PB8/PB14/PB15 sont impliqués dans la NAND.
Ne pas remplacer les registres complets de GPIOB/GPIOE par des constantes LCD.

## 3. Écrire un octet

### Commande, routine OEM 0x0808B672

1. D/C bas, puis CS# bas.
2. Présenter l’octet sur PE7..PE14.
3. WR# bas puis haut.
4. CS# haut.

### Paramètre ou donnée, routine OEM 0x0808B6F6

Même principe avec D/C haut. `0x0808B6B0` enchaîne une commande en R0 et
un paramètre en R1. `0x0808B654` place seulement un octet sur le port E.

L’écrivain de données conserve les bits hors masque `0x7F80`. L’OEM effectue
cependant deux écritures OCTL : effacement des huit bits, puis insertion de
l’octet décalé de 7. Aucun front montant WR# n’intervient entre ces écritures.
Un nouveau pilote peut employer les opérations atomiques BOP/BC pour éviter
une lecture-modification-écriture sur tout le port, en conservant le protocole.

Pour les pixels, certaines boucles maintiennent CS# bas sur plusieurs octets.
Il faut garantir l’exclusion sur **toute la transaction**, pas seulement sur
l’impulsion WR# ou sur un appel de fonction.

## 4. Commandes retrouvées

| Commande | Paramètres | Fonction utile pour le pilote |
| --- | --- | --- |
| 0x10 | Aucun | Entrée en sommeil |
| 0x11 | Aucun | Sortie du sommeil |
| 0x28 | Aucun | Affichage désactivé |
| 0x29 | Aucun | Affichage activé |
| 0x2A | Début et fin, chacun sur 16 bits | Fenêtre des colonnes |
| 0x2B | Début et fin, chacun sur 16 bits | Fenêtre des lignes |
| 0x2C | Flux de pixels après la commande | Écriture dans la mémoire graphique |
| 0x36 | 0x48 dans cette image | Contrôle d’accès/orientation |
| 0x3A | 0x55 dans cette image | Format de pixels RGB565 |
| 0xB1..0xB4 | Voir initialisation | Réglages du fonctionnement de la dalle |
| 0xC0..0xC5 | Voir initialisation | Réglages analogiques du contrôleur |
| 0xE0, 0xE1 | 16 octets chacun | Tables de réglage gamma |

Les noms détaillés des commandes de dalle correspondent à une famille de
contrôleurs compatible. Les **valeurs OEM observées** restent la référence
pour cette variante. Ne pas substituer une initialisation générique Arduino
simplement parce qu’elle utilise les mêmes opcodes.

Le simulateur accepte également `0x01` comme reset logiciel. Cela décrit son
modèle ; la séquence OEM ci-dessous utilise le reset GPIO et ne transmet pas
`0x01`. Ne pas confondre une capacité du décodeur avec une commande constatée.

## 5. Initialisation exacte retrouvée dans V1.21

Point d’entrée analysé : `0x080384E8`. Les valeurs ci-dessous ont été relues
dans le binaire et recoupées avec les premières commandes enregistrées dans
la trace d’exécution du banc.

### Reset et attentes

| Étape | Action | Argument de délai OEM |
| ---: | --- | ---: |
| 1 | WR# haut, CS# haut, PB12 haut | 100 |
| 2 | PB12 bas | 100 |
| 3 | PB12 haut | 500 |
| 4 | Commande 0x11 | 120 |
| 5 | Programmation des registres ci-dessous | Aucun délai explicite entre ces écritures |
| 6 | Après la fenêtre initiale 0x2A/0x2B | 200 |

Les appels de délai visent `0x08009F30`, avec un argument exprimé en
millisecondes selon la chaîne de calibration observée. Cette fonction utilise
le RTOS quand disponible, puis un reliquat temporisé par SysTick. Elle
multiplie le reliquat par 1000 avant d’appeler `0x08009EEA`.

Cette dernière multiplie par l’octet de calibration `0x2000002F`, qui vaut
15 dans la capture étudiée. Cela concorde avec SysTick à HCLK/8 pour HCLK à
120 MHz, soit 15 coups par microseconde. Le quartz de 12 MHz ne donne donc
pas directement la durée de chaque instruction ni celle d’une impulsion LCD.

### Tableau d’initialisation

Chaque ligne indique une commande, puis ses paramètres en hexadécimal.

```text
11
attendre 120 ms
B1  01 01 01
B2  01 01 01
B3  01 01 01 01 01 01
B4  03
C0  28 08 84
C1  C0
C2  0C 00
C3  8C 2A
C4  8A EE
C5  0C
36  48
E0  05 1A 0C 0E 3A 34 2D 2F 2D 2A 2F 3C 00 01 02 10
E1  04 1B 0D 0E 2D 29 24 29 28 26 31 3B 00 00 03 12
3A  55
2C
2A  00 00 00 80
2B  00 00 00 A0
attendre 200 ms
```

Le `2C` avant la première fenêtre est réellement présent. Il n’est suivi
d’aucun pixel à cet endroit ; le décodeur ne lui invente pas de remplissage.

L’initialisation appelle ensuite `0x08022B78`, puis `0x080384DE`, qui envoie
`0x28`. L’allumage `0x29` est assuré dans le déroulement de démarrage par un
chemin distinct ; son enveloppe directe est à `0x08038808`. Un pilote autonome
doit donc décider explicitement quand afficher son premier dessin.

Cette distinction explique qu’un LCD correctement initialisé puisse rester
noir : mémoire graphique, sommeil, Display On et rétroéclairage sont des états
différents.

## 6. Fenêtres, dimensions et orientation

### Adresses inclusives

Les fenêtres prennent deux bornes inclusives, transmises octet fort d’abord :

```text
2A  x0_hi x0_lo x1_hi x1_lo
2B  y0_hi y0_lo y1_hi y1_lo
2C  pixel0_hi pixel0_lo pixel1_hi pixel1_lo ...
```

Pour la surface usuelle, les transactions de dessin utilisent :

```text
2A  00 00 00 7F   # colonnes 0..127
2B  00 00 00 9F   # lignes   0..159
```

Soit 20 480 pixels et 40 960 octets pour un remplissage RGB565 complet.
La fenêtre d’initialisation va à `0x80` et `0xA0`, soit une étendue inclusive
129 × 161. **Elle ne prouve pas une surface visible de 129 × 161 pixels.**
Dans la trace analysée, les dessins couvrent 20 480 positions distinctes.

Le décodeur conserve la plus grande adresse vue. Ses dimensions rapportées
peuvent donc rester à 129 × 161 après cette initialisation. Son tampon interne
512 × 512 est une limite d’implémentation, pas la résolution du module.

### Permutation des coordonnées OEM

La routine `0x08021222` reçoit quatre coordonnées dans R0..R3 et envoie :

```text
2A : 00, R1 bas, 00, R3 bas
2B : 00, R0 bas, 00, R2 bas
```

Dans ce chemin, les coordonnées logiques OEM sont donc transposées par rapport
aux axes colonnes/lignes du bus. Une fonction générique `window(x0,y0,x1,y1)`
ne doit pas appeler cette routine en supposant une correspondance directe.
La routine ne transmet ici que huit bits utiles par coordonnée.

Pour les images du banc, la transposition de la GRAM restitue le paysage
160 × 128. Ce n’est pas une simple rotation de 90 degrés, qui introduirait
un miroir. La valeur `MADCTL=0x48` est conservée ; le décodeur ne simule pas
intégralement tous les modes MADCTL et ne valide pas les rotations arbitraires.

## 7. Format des pixels et couleurs

Un pixel RGB565 est composé de 5 bits rouges, 6 verts et 5 bleus :

```c
uint16_t rgb565(uint8_t r, uint8_t g, uint8_t b) {
    return (uint16_t)(((r & 0xF8u) << 8) |
                      ((g & 0xFCu) << 3) | (b >> 3));
}
```

L’octet fort est envoyé en premier sur le bus, même si le Cortex-M4 stocke les
entiers en mémoire dans l’ordre little-endian. Ne pas envoyer directement les
deux octets d’un tableau `uint16_t` sans traiter cet ordre.

| Valeur | Octets à transmettre | Couleur nominale RGB565 |
| --- | --- | --- |
| 0x0000 | 00 00 | Noir |
| 0xFFFF | FF FF | Blanc |
| 0xF800 | F8 00 | Rouge |
| 0x07E0 | 07 E0 | Vert |
| 0x001F | 00 1F | Bleu |

La permutation RGB/BGR physique est à contrôler avec ces aplats sur le poste.
Le décodeur reconstruit du RGB565 et offre une option BGR ; il ne transforme
pas cette option en preuve de l’ordre des sous-pixels du module.

En coordonnées GRAM du modèle, la progression est colonne d’abord, puis ligne,
avec retour au début de la fenêtre. Ce comportement reconstruit les dessins
OEM observés. D’autres valeurs de MADCTL restent hors de cette qualification.

## 8. Timings : distinguer trois choses

### Attentes longues du firmware

Pour un premier pilote autonome, reprendre les attentes OEM : 100 ms avant
l’impulsion de reset, 100 ms reset bas, 500 ms après sa libération, 120 ms après
Sleep Out et 200 ms à la fin de la programmation initiale. Leur observation
n’en fait pas des minima électriques universels.

### Impulsions de bus

Le code OEM n’insère pas une attente longue pour chaque octet. Les appels GPIO,
les accès périphériques et les instructions constituent l’intervalle de bus.
Les compteurs d’instructions du banc ne sont pas des mesures à l’oscilloscope :
Unicorn et le temps virtuel ne constituent pas un modèle exact des cycles ARM,
des attentes Flash, du pont APB et des fronts de sortie.

Pour une première version indépendante, utiliser une primitive d’attente
calibrée et, par exemple, **1 µs** pour chaque phase de setup, WR# bas et hold.
C’est un choix de mise au point volontairement lent, pas un timing mesuré ni
une garantie sur un contrôleur non identifié. Optimiser après capture logique.

### Référence conditionnelle de famille

La fiche Sitronix ST7735S V1.3, section 8.1, donne notamment les valeurs
suivantes pour son interface 8080. Elles servent de comparaison et ne sont
pas déclarées spécifications garanties du module D578 :

| Paramètre ST7735S | Minimum documentaire |
| --- | ---: |
| Cycle d’écriture TWC | 66 ns |
| WR# haut TWRH | 15 ns |
| WR# bas TWRL | 15 ns |
| Setup CS# TCS | 15 ns |
| Hold CS# TCSH | 10 ns |

Source : fiche constructeur Sitronix hébergée chez TI,
<https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/908/ST7735S_5F00_v1.3.pdf>.
Cette référence ne remplace pas l’identification du contrôleur et une capture
sur notre carte. Les timings de lecture ne sont pas utilisables sans RD#,
sans direction du bus qualifiée et sans protocole de lecture vérifié.

## 9. Rétroéclairage : bus distinct

Le modèle `bench/lighting.py` décode les sorties suivantes :

| Signal | GPIO |
| --- | --- |
| Latch/validation de trame | PA5 |
| Horloge | PB3 |
| Données | PB4 |

Une trame comprend 12 bits, MSB d’abord : **4 bits d’adresse**, puis **8 bits
de valeur**. PA5 passe bas pour commencer ; le récepteur prend les données
aux fronts montants PB3 ; PA5 repasse haut pour valider. L’entrée OEM analysée
est `0x0808A7C0`, adresse en R0, donnée en R1.

Le canal 8 correspond à la luminosité LCD dans les chemins de réglage et de
veille/réveil étudiés. Des écritures `8,0` et `8,255` figurent dans les traces.
La loi photométrique, les niveaux intermédiaires et le circuit récepteur exact
restent à qualifier. Ne pas présenter la valeur brute comme un pourcentage
mesuré, ni confondre ce bus avec une broche PWM LCD directement identifiée.

PB3/PB4 peuvent aussi concerner le débogage JTAG selon la configuration MCU.
Pour un nouveau programme autonome, examiner la configuration AFIO/debug avant
de reprendre ces broches. Ne pas désactiver SWD par une configuration globale
copiée sans analyse.

## 10. Deux façons d’intégrer un nouveau programme

### Programme autonome ou diagnostic prenant la main

Il doit posséder sa propre initialisation CPU, sa pile, ses horloges et ses
délais. Il configure seulement les broches nécessaires, reprend le reset et
l’initialisation ci-dessus, dessine un motif, puis active l’affichage et le
rétroéclairage. Le trajet radio n’est pas nécessaire au dessin du motif.

Un essai qui utilise une dalle déjà initialisée par l’OEM valide seulement une
reprise à chaud. Il ne qualifie pas le démarrage à froid du nouveau pilote.
L’adresse d’injection, la méthode de lancement et la récupération du poste
restent des sujets séparés de ce protocole LCD.

### Extension conservant l’application OEM

Elle doit s’intégrer au gestionnaire d’interface et obtenir la propriété du
bus pendant une transaction complète. Les appels bas niveau seuls ne protègent
pas de la tâche UI, des fenêtres déjà ouvertes et des autres chemins de dessin.

| Élément V1.21 | Adresse | Portée connue |
| --- | --- | --- |
| Handle du sémaphore LCD | 0x20000128 | Objet RTOS retrouvé |
| Création du sémaphore | 0x0803848C → 0x080AEC5A | Chemin d’initialisation |
| Acquisition / restitution | 0x080AED66 / 0x080AEEC4 | API et retours à qualifier avant réutilisation |
| Garde de phase RTOS | 0x20001542 | État observé, pas un verrou à forcer |
| Worker UI | 0x08038466 | Tâche OEM identifiée |
| Dispatch/rendu | 0x08037BE8 | Gestionnaire de vues |
| Sleep In / Sleep Out | 0x080387AC / 0x080387DA | Enveloppes de 0x10 / 0x11 |

L’audit antérieur compte 37 sites d’acquisition et 38 de restitution, avec
37 paires adjacentes et un saut particulier. Ces nombres ne prouvent ni un
bug du constructeur ni une API de réservation LCD prête pour notre extension.
`0x080393C6` traite des notifications/temporisations et ne doit pas être appelé
comme un mutex LCD.

Une injection doit prévoir un point d’entrée dans l’UI, un état de retour et
un redessin OEM propre. Masquer durablement les interruptions pour dessiner
serait susceptible de perturber l’audio, l’USB et les temporisations.
Un reset de la dalle au milieu du fonctionnement OEM invalide également ses
hypothèses d’état. Il ne remplace pas un accord de propriété du moteur LCD.

## 11. Squelette C pour un pilote indépendant

Cet exemple exprime le protocole, pas un binaire prêt à injecter. Il suppose
les GPIO déjà configurés en sorties, les horloges actives, le LCD initialisé,
le bus exclusif, et `lcd_wait_us()` correctement calibrée. Les coordonnées
sont celles de la GRAM, sans transposition implicite. Il n’appelle pas l’OEM.

```c
#include <stdint.h>
#include <stdbool.h>

#define REG32(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define PB_BOP REG32(0x40010C10u)
#define PB_BC  REG32(0x40010C14u)
#define PE_BOP REG32(0x40011810u)
#define PE_BC  REG32(0x40011814u)
#define LCD_WR (1u << 10)
#define LCD_DC (1u << 11)
#define LCD_CS (1u << 13)
#define LCD_DATA_MASK 0x7F80u

extern void lcd_wait_us(uint32_t us);

static void lcd_byte(uint8_t value, bool data) {
    /* WR haut avant de modifier D/C ou les donnees. */
    PB_BOP = LCD_WR;
    if (data) PB_BOP = LCD_DC; else PB_BC = LCD_DC;
    PB_BC = LCD_CS;
    PE_BC = LCD_DATA_MASK;
    PE_BOP = ((uint32_t)value << 7);
    lcd_wait_us(1);             /* setup de mise au point */
    PB_BC = LCD_WR;
    lcd_wait_us(1);             /* WR bas */
    PB_BOP = LCD_WR;
    lcd_wait_us(1);             /* hold apres front montant */
    PB_BOP = LCD_CS;
    lcd_wait_us(1);             /* intervalle entre transactions */
}

static void lcd_cmd(uint8_t value) { lcd_byte(value, false); }
static void lcd_data(uint8_t value) { lcd_byte(value, true); }

static void lcd_u16(uint16_t value) {
    lcd_data((uint8_t)(value >> 8));
    lcd_data((uint8_t)value);
}

static bool lcd_window(uint16_t x0, uint16_t y0,
                       uint16_t x1, uint16_t y1) {
    if (x0 > x1 || y0 > y1 || x1 >= 128u || y1 >= 160u)
        return false;
    lcd_cmd(0x2A); lcd_u16(x0); lcd_u16(x1);
    lcd_cmd(0x2B); lcd_u16(y0); lcd_u16(y1);
    lcd_cmd(0x2C);
    return true;
}

static void lcd_fill(uint16_t colour) {
    if (!lcd_window(0, 0, 127, 159)) return;
    for (uint32_t i = 0; i < 128u * 160u; ++i)
        lcd_u16(colour);
}
```

La durée minimale introduite par cet exemple est de 4 µs par octet, soit au
moins 163,84 ms pour les seuls 40 960 octets de pixels d’un écran complet.
C’est une base de diagnostic, pas une proposition d’interface finale fluide.
Une fois le matériel vérifié, grouper les pixels sous CS# et redessiner les
zones modifiées diminuera le coût. Un framebuffer complet de 40 960 octets
n’est pas requis pour des aplats, glyphes ou petits rectangles.

L’exemple emploie des accès atomiques de bits mais ne fournit pas de verrou
logiciel. Cela préserve les autres broches, sans résoudre les conflits entre
deux utilisateurs simultanés du LCD.

## 12. Qualification avant une injection utilisable

1. Vérifier la continuité des signaux et relever l’orientation de la nappe.
2. Capturer un démarrage OEM : reset, première commande 0x11, bus et lumière.
3. Contrôler les tensions, la largeur WR#, le setup et le hold des données.
4. Tester à froid le pilote autonome avec les paramètres OEM et délais longs.
5. Dessiner noir, blanc, rouge, vert, bleu, puis quatre coins distincts et un
   rectangle non carré pour confirmer orientation et limites.
6. Tester plusieurs petites fenêtres et le retour au début d’une fenêtre.
7. Vérifier séparément 0x28/0x29, 0x10/0x11 et le canal de rétroéclairage.
8. Pour une extension OEM, qualifier la prise/restitution de l’UI et son redessin
   pendant RX, PTT, USB, changement de menu et veille.

Un test dans le banc peut confirmer les octets, l’ordre et l’image reconstruite.
Il ne mesure pas les fronts électriques et ne certifie pas les modes du
contrôleur que le modèle n’implémente pas.

## 13. Preuves de simulation et limites du modèle

Dans la trace de travail `speaker_probe_v118`, qui inclut démarrage et menus :

| Mesure | Résultat |
| --- | ---: |
| Pixels écrits, répétitions comprises | 737 926 |
| Positions distinctes écrites | 20 480 |
| Appels de commande recoupés | 8 509 |
| Divergences commande OEM / bus décodé | 0 |
| Format reçu | 0x55 |
| MADCTL reçu | 0x48 |

Ces résultats prouvent une reconstruction cohérente des chemins exécutés.
Ils ne constituent pas une couverture exhaustive du moteur graphique.

Le modèle interprète les fenêtres et le sous-ensemble RGB565, observe les
commandes d’affichage et conserve les autres paramètres. Il ne reproduit pas
la physique de la dalle, ses alimentations analogiques, tous les effets des
gammas, tous les modes MADCTL, ni les minima temporels du circuit réel.

Des lignes vides OEM peuvent produire une borne de fin égale au début moins un,
sans pixels ensuite. Le banc les journalise et rejette un flux de pixels dans
une telle fenêtre. Un nouveau pilote doit les éviter plutôt que copier ce cas.

Le mécanisme historique d’armement du décodeur au premier appel connu
`0x0808B672` est spécifique au profil OEM : pour un programme entièrement
expérimental, il faut aussi armer l’observation par une configuration explicite
ou les conditions matérielles. Sans cette adaptation, un autre point d’entrée
LCD peut ne produire aucune image dans le banc malgré des GPIO corrects.
C’est une limite du banc à lever, pas une contrainte imposée au futur firmware.

## 14. Références et historique de cette note

Analyse binaire : `D578UV_GD_V1.21_20240619.CDD`, chargé à `0x08006000`.
SHA-256 : `02b2a3b56bd57c7ada581eb52b9b6f41c5d51aaec1b068d37585efd58dff9c9a`.
Les adresses changent entre versions et ne sont pas des symboles d’API stables.
Pour appeler une routine Thumb depuis C, son adresse de fonction doit respecter
le bit Thumb et son ABI complète doit être vérifiée ; une adresse seule ne suffit pas.

Sources publiques du projet :

- `bench/lcd_bus.py` : décodeur des fronts et mémoire de pixels.
- `bench/emulate_lcd_v121.py` : observation GPIO, armement et recoupement OEM.
- `bench/lcd_bridge.py` : accélération de la capture des fronts, sans remplacer
  le dessin ni les instructions ARM.
- `bench/lighting.py` : décodage du bus de rétroéclairage.
- `bench/test_lcd_bus.py` et `bench/test_lcd_bridge.py` : tests du modèle.
- `docs/04_RAM_ROUTINES_UI_RF_ET_BROCHAGE.md` : anciennes analyses UI/RTOS.
- Dépôt : <https://github.com/Telectroboy/OpenD578>.

Référence documentaire externe : fiche Sitronix ST7735S V1.3 citée en section 8,
utilisée comme comparaison conditionnelle, pas comme identification du module.

Cette note ajoute la relecture détaillée de l’initialisation, la distinction
entre surface dessinée et fenêtre initiale, la permutation des coordonnées,
le chemin de reset, le protocole du rétroéclairage et un squelette C de bus.
Elle ne modifie pas le banc V11.8 et n’annonce aucun essai sur le poste physique.

Contrôles effectués pour ce document : les 18 commandes de la table
d’initialisation et tous leurs paramètres correspondent au début de la trace
exécutée ; les 20 tests de `test_lcd_bus.py` et `test_lcd_bridge.py` réussissent.
Les deux exemples C passent `gcc -std=c11 -Wall -Wextra -Werror -fsyntax-only`.
Ce contrôle de syntaxe ne constitue pas une compilation ARM liée ni un essai
du squelette sur la radio.
