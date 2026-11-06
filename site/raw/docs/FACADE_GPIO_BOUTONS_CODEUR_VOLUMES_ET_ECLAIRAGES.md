# OpenD578 : façade, boutons, codeur, volumes et éclairages

État des connaissances : 5 novembre 2026. Base étudiée : D578UV PRO GD32,
application constructeur V1.21 et banc V11.8.

Objectif : développer les entrées et sorties d’un firmware alternatif à partir
des **périphériques matériels**. Les exemples ne lisent aucune variable RAM du
firmware constructeur et n’appellent aucune de ses routines. Ils utilisent les
registres du GD32 et leur propre état logiciel. Les adresses de périphériques
ne changent pas lorsqu’on remplace le firmware sur la même carte.

Ce document distingue les constats du firmware, les observations utilisateur,
les stimuli synthétiques du banc et les choix proposés pour un nouveau pilote.
Il ne remplace pas un schéma de continuité de la carte.

## 1. Périmètre et comptage

Les dix boutons de façade pris en compte sont : P1, P2, P3, P4, P5, P6, MENU,
EXIT, Power et l’appui du codeur. La rotation du codeur utilise deux autres
contacts. Les touches du microphone sont traitées dans la note microphone.

Concernant « 2 LED R/V », le relevé physique retenu dans le projet est :

| Emplacement | Éléments | Traitement |
| --- | --- | --- |
| Poste | Un voyant bicolore, composantes rouge et verte | Bus GPIO PE3/PE4 décrit ici |
| Microphone | Deux voyants bicolores A et B | Commandes UART, rappel en section 10 |
| Microphone | Deux voyants blancs MAIN A/B | Sélection du VFO, rappel en section 10 |

Cette distinction évite d’inventer deux voyants bicolores sur le poste. Le
nombre de dies et leur montage électrique exact restent à relever sur carte.

## 2. Cartographie matérielle de travail

| Fonction | GPIO / périphérique | Polarité ou format | Qualification |
| --- | --- | --- | --- |
| Power | PA0 | Bas pendant l’appui | Code OEM et simulation d’entrée |
| Appui codeur | PA1 | Bas pendant l’appui | Lecteur OEM exécuté avec ce stimulus |
| P1/P2/P3/MENU | PB0, ADC0 canal 8 | Quatre plages analogiques | Décodeur OEM et acquisition ADC |
| P4/P5/P6/EXIT | PB1, ADC0 canal 9 | Quatre plages analogiques | Décodeur OEM et acquisition ADC |
| Codeur, contact de déclenchement | PC8 | Front descendant dans le chemin OEM | Configuration EXTI et gestionnaire exécuté |
| Codeur, phase de direction | PC9 | Niveau lu lors du front PC8 | Gestionnaire exécuté |
| Volume A, nom utilisé par le banc | PC2, ADC0 canal 12 | Valeur 12 bits | Affectation du modèle ; position physique A/B à confirmer |
| Volume B, nom utilisé par le banc | PC5, ADC0 canal 15 | Valeur 12 bits | Même réserve sur l’ordre des boutons |
| Voyant rouge/vert du poste, données | PE3 | Mot de 8 bits, LSB d’abord | Bus OEM décodé |
| Voyant rouge/vert du poste, horloge | PE4 | Donnée prise au front montant | Bus OEM décodé |
| Éclairages, validation de mot | PA5 | Bas pendant le mot, haut à la fin | Bus OEM décodé |
| Éclairages, horloge | PB3 | Front montant | Bus OEM décodé |
| Éclairages, données | PB4 | 4 bits adresse + 8 bits valeur, MSB d’abord | Bus OEM décodé |
| Rétroéclairage écran | Adresse 8 sur le bus précédent | Valeur brute 0..255 | Corrélation menus/veille et bus |
| Éclairage individuel des touches | Adresses non toutes affectées | Voir section 9 | Cartographie physique incomplète |

Les correspondances canal ADC → broche sont celles du MCU pour ces entrées.
La continuité jusqu’aux contacts, curseurs et LED n’a pas été mesurée ici.
Les deux volumes ne sont pas des broches « GPIO numériques » à lire haut/bas :
leurs broches doivent être placées en mode analogique puis acquises par l’ADC.

## 3. Registres matériels utiles

| Port | Base |
| --- | --- |
| GPIOA | 0x40010800 |
| GPIOB | 0x40010C00 |
| GPIOC | 0x40011000 |
| GPIOE | 0x40011800 |

Offsets communs : CTL0 `+0x00`, CTL1 `+0x04`, ISTAT `+0x08`, OCTL `+0x0C`,
BOP `+0x10`, BC `+0x14`. Les niveaux d’entrée doivent être lus dans ISTAT,
pas dans OCTL. Le registre OCTL est le verrou de sortie et intervient notamment
dans la sélection du pull-up/pull-down en mode entrée avec résistance interne.

| Périphérique | Base / registre | Usage |
| --- | --- | --- |
| AFIO | 0x40010000 | Routage EXTI et fonctions de débogage |
| EXTI | 0x40010400 | Interruptions externes |
| ADC0 | 0x40012400 | Touches et volumes |
| ADC0 RDATA | 0x4001244C | Résultat de conversion |
| DMA0 | 0x40020000 | Acquisition régulière possible |
| RCU | 0x40021000 | Activation et division des horloges |

Configuration des broches par nibbles de quatre bits : analogique `0x0`,
entrée flottante `0x4`, entrée avec pull-up/down `0x8`. Le sens de la résistance
est alors choisi dans OCTL. Les sorties observées sur les bus utilisent le
mode général push-pull. Conserver les nibbles des autres broches.

Pour un firmware autonome, activer les horloges des ports nécessaires, AFIO
si EXTI est utilisé, et ADC0. DMA0 n’est requis que pour une acquisition DMA.
Ne pas réinitialiser globalement un port partagé pour installer un seul pilote.

## 4. Les huit touches analogiques

### Valeurs attendues

Deux réseaux résistifs sont vus par ADC0. Les décodeurs OEM comparent les
résultats bruts 12 bits aux seuils 500, 1500, 2500 et 3500.

| Plage inclusive ADC | PB0 / canal 8 | PB1 / canal 9 | Exemple injecté dans le banc |
| --- | --- | --- | ---: |
| 0..500 | P1 | P4 | 250 |
| 501..1500 | P2 | P5 | 1000 |
| 1501..2500 | P3 | P6 | 2000 |
| 2501..3500 | MENU | EXIT | 3000 |
| 3501..4095 | Aucune | Aucune | 4095 |

Les **seuils viennent du code**, les exemples centraux du simulateur. Ils ne
sont pas des tensions mesurées sur les contacts ni la preuve de résistances
exactes. Il faut relever les valeurs réelles, leurs dispersions et les tensions
aux bornes du réseau pour fixer les marges de production.

À titre de conversion seulement : `Ventrée = code × VREF / 4095`. Ne pas poser
VREF = 3,3 V sans vérifier la référence analogique de la carte.

Une entrée collée à zéro ressemble à la première touche : le seul seuil ne
permet pas de distinguer un court-circuit d’un appui. Un nouveau firmware peut
signaler une durée anormale sans déclarer arbitrairement cet appui impossible.

### Appuis simultanés

Les groupes peuvent être lus indépendamment. Deux touches d’un même réseau
produisent une tension dépendant du câblage résistif, qui n’est pas entièrement
relevé. On ne peut donc pas promettre leur identification séparée. Le banc
refuse actuellement ces combinaisons pour ne pas inventer une tension.

P4 + appui codeur + Power utilise un réseau analogique et deux entrées
numériques distinctes ; cette combinaison est représentable électriquement.
Elle ne suffit pas à garantir l’accès au test constructeur : les conditions
de configuration du poste restent distinctes.

### Anti-rebond et événements

Le filtre OEM des touches analogiques attend plusieurs lectures cohérentes :
changement → résultat provisoire, puis compteur avant acceptation. Le seuil
observé est deux incréments après détection du changement. Cela ne donne pas
un délai en millisecondes sans établir la cadence de tous les appelants.

Pour le nouveau pilote, proposition explicite : échantillonner à 5 ms et
accepter après 20 ms de stabilité. Produire ensuite des événements appui,
relâchement, appui long et répétition dans une couche séparée. Par exemple,
600 ms pour un appui long et 150 ms pour une répétition sont des choix produit,
pas des timings OEM déjà mesurés.

Une hystérésis autour des seuils évitera les oscillations lorsque la valeur
brute est proche d’une frontière. Fixer sa largeur après mesures.

## 5. Power et appui du codeur

### Lecture indépendante

| Entrée | Repos attendu | Appui attendu | Masque |
| --- | --- | --- | --- |
| PA0 Power | 1 | 0 | 0x0001 |
| PA1 appui codeur | 1 | 0 | 0x0002 |

Power est un contact lu par le MCU, pas la preuve d’une coupure directe de son
alimentation. Sur le montage étudié, le MCU peut notamment rester alimenté par
le raccordement USB/SWD. La séquence d’arrêt, les lignes de maintien
alimentation et le réveil doivent donc être traités séparément.

Le lecteur OEM de l’appui codeur vérifie PA1, attend une courte boucle, puis
le relit. Cette boucle n’est pas un délai calibré en microsecondes. Appliquer
un vrai anti-rebond dans le pilote alternatif.

EXTI0 peut être routé vers PA0 pour le réveil initial. Dans d’autres phases
OEM, cette même ligne est routée vers un autre port. Ne pas supposer que
l’IRQ EXTI0 signifie toujours « Power » ; vérifier AFIO et la source physique.
Un firmware autonome peut choisir son propre routage ou une lecture périodique.

## 6. Codeur rotatif PC8 / PC9

L’OEM configure PC8 et PC9 en entrées avec pull-up. Le chemin identifié route
PC8 vers EXTI8 et déclenche sur front descendant ; EXTI5_9 partage l’IRQ 23.
À l’interruption, il lit PC9 puis PC8 et compare leurs niveaux.

Avec le front PC8 déjà bas :

| PC8 | PC9 | Interprétation du banc après passage dans le gestionnaire OEM |
| ---: | ---: | --- |
| 0 | 0 | DIAL_UP |
| 0 | 1 | DIAL_DOWN |
| 1 | 1 | Repos synthétique utilisé |

Le sens mécanique horaire/antihoraire et le nombre de transitions par cran
restent à mesurer. Les noms UP/DOWN représentent les tests du banc, pas un
relevé mécanique du codeur. L’injection d’un front synthétique ne qualifie pas
les rebonds d’un véritable contact.

Deux stratégies pour un autre firmware :

- Reprendre le front PC8 et lire PC9, avec filtrage adapté.
- Lire les deux phases et utiliser un décodeur quadrature qui rejette les
  transitions où les deux bits changent simultanément.

Échantillonnage proposé pour la seconde stratégie : 0,5 à 1 ms, à vérifier à
la vitesse maximale de rotation. En EXTI, lire les niveaux rapidement, puis
mettre l’événement en file. Ne pas dessiner le LCD ou attendre 20 ms dans l’IRQ.
Les groupes EXTI sont partagés : acquitter uniquement les bits traités.

## 7. Acquisition ADC et deux volumes

### Ce que l’exécution OEM configure

La séquence régulière observée est `[6, 8, 9, 10, 11, 12, 15]`. ADC0 est en
scan continu avec DMA0 canal 0. Les éléments sont des demi-mots, la destination
s’incrémente et le tampon est circulaire sur sept conversions.

| Rang, à partir de 0 | Canal | Fonction dans ce document |
| ---: | ---: | --- |
| 0 | 6 | Autre mesure, non attribuée ici |
| 1 | 8 | Touches P1/P2/P3/MENU |
| 2 | 9 | Touches P4/P5/P6/EXIT |
| 3 | 10 | Autre mesure, non attribuée ici |
| 4 | 11 | Autre mesure, non attribuée ici |
| 5 | 12 | Volume nommé A par le banc |
| 6 | 15 | Volume nommé B par le banc |

Le rang dépend de la séquence programmée. Dans un firmware alternatif,
**définir son propre tableau de résultats** ; ne pas reprendre les offsets
d’un tampon constructeur.

Quelques mots de configuration constatés, à titre de recoupement du protocole :
ADC_CTL0 = `0x00000100`, ADC_CTL1 = `0x001E0103` en régime observé,
ADC_RSQ0 = `0x00600000`, ADC_RSQ1 = `0x0000000F`, ADC_RSQ2 = `0x18B52506`.
Le DMA a été configuré avec un compte initial de 7 et un contrôle `0x25A1`.
Ces valeurs ne doivent pas être recopiées sans initialisation des horloges,
calibration ADC et choix du tampon propre au nouveau programme.

### Volumes

Les canaux 12 et 15 sont lus et moyennés par le code OEM. Dans le chemin
initial relu pour cette note, quatre acquisitions sont additionnées avec une
attente OEM de 1 ms entre lectures, puis divisées par quatre. Cela établit une
mesure lente de commande ; ce ne sont pas des échantillons de voix.

Restent à confirmer sur le matériel : quel bouton physique correspond à PC2
ou PC5, le sens de variation, les valeurs aux butées, la résistance et la loi
des potentiomètres, le filtrage RC, et leur éventuel rôle analogique parallèle.
L’existence d’une mesure ADC ne prouve pas qu’aucun trajet audio ne traverse
un autre élément du potentiomètre.

Lire 0..4095 ne définit pas un gain audio. La conversion vers un gain du codec,
du circuit radio ou d’un amplificateur doit être documentée séparément. Ne pas
confondre ces mesures avec une valeur en dB ou avec une puissance RF.

### Configuration proposée pour un premier pilote

Utiliser PB0/PB1/PC2/PC5 en mode analogique, une référence stable, ADC0 calibré
et un temps d’échantillonnage suffisamment long pour l’impédance des réseaux.
Une acquisition par scrutation suffit pour un diagnostic ; un scan DMA permet
ensuite de lire les quatre entrées régulièrement.

Le temps de conversion 12 bits dépend du temps d’échantillonnage et de
l’horloge ADC. Vérifier les limites dans la documentation du MCU ; les
64 instructions par conversion du banc sont un paramètre de simulation,
**pas un timing matériel**. Ne pas en déduire la cadence d’un nouveau pilote.

Proposition de filtrage : moyenne de quatre à huit mesures, actualisation des
volumes toutes les 10 à 20 ms, puis hystérésis avant changement de gain. Ces
valeurs sont des choix initiaux, à ajuster aux mesures et à l’ergonomie.

## 8. Voyant rouge/vert du poste : bus PE3 / PE4

Les deux composantes ne sont pas pilotées ici comme deux GPIO directement
reliés aux LED. Le code transmet un mot de huit bits sur PE3, cadencé par PE4,
**bit de poids faible d’abord**. L’état est pris au front montant PE4.
Aucune ligne de latch supplémentaire n’est identifiée dans ce chemin.

| Mot complet observé | Vert, masque 0x08 | Rouge, masque 0x10 | Situation de la trace |
| --- | ---: | ---: | --- |
| 0x46 | 0 | 0 | Repos |
| 0x4E | 1 | 0 | Réception, squelch ouvert |
| 0x56 | 0 | 1 | Émission |
| 0x00 / 0x10 | 0 | 0 / 1 | Clignotement bootloader |

La correspondance couleur combine la séquence OEM et l’observation utilisateur.
La continuité jusqu’au circuit récepteur et aux LED n’est pas encore mesurée.
Les autres bits de `0x46` restent non attribués. Pour changer une couleur,
conserver les autres bits du mot que le pilote possède et comprend ; ne pas
supposer que les huit sorties servent exclusivement à ce voyant.

Le chemin applicatif configure temporairement PE3/PE4 en sorties push-pull,
envoie les huit bits, remet PE4 bas, puis repasse les broches en entrées avec
pull-down. Cette restitution de direction fait partie du comportement observé.
Ne pas conclure que les niveaux GPIO resteront en permanence égaux à la couleur.

Le code introduit une boucle de valeur 2 autour des fronts. Ce sont deux tours
d’une primitive, **pas une preuve de 2 µs**. Un premier émetteur peut prendre
1 µs de setup et 1 µs haut/bas, puis être ajusté après capture logique. Le circuit
récepteur, sa validation de mot et sa tolérance aux pauses restent à qualifier.

Si les deux bits couleur sont mis à un, le banc expose les deux commandes.
Il n’invente pas une priorité rouge/vert ni une couleur physique résultante.

## 9. Éclairages des touches et de l’écran

### Protocole commun observé

- PA5 bas : début du mot.
- Envoyer les quatre bits d’adresse, MSB d’abord, sur PB4.
- Envoyer les huit bits de valeur, MSB d’abord.
- PB3 bas avant le bit, PB3 haut pour son acquisition.
- Après le douzième bit, PB3 bas puis PA5 haut : validation.

Le mot est `(adresse << 8) | valeur`. Exemple : adresse 8, donnée 128 →
`0x880`, soit `1000 10000000`. Adresse 8, donnée 255 → `0x8FF`.

Le firmware introduit des boucles de valeur 10 entre les fronts. Elles ne sont
pas des délais certifiés de 10 µs. Le bus partage des broches avec d’autres
fonctions du poste : les sélections des circuits et la propriété du bus doivent
être coordonnées. Le routage JTAG de PB3/PB4 doit également être examiné sans
supprimer SWD par erreur.

### Affectations connues et inconnues

| Adresse | Information fiable |
| --- | --- |
| 8 | Luminosité LCD, valeurs 0 et 255 observées |
| 12, 2, 10, 6, 1, 14 | Écrivains OEM individuels retrouvés ; sorties physiques à attribuer |
| 4 | Autre écrivain individuel retrouvé ; affectation non établie ici |
| 9, 3, 15 | Écritures d’initialisation observées ; rôle exact non attribué |

L’initialisation OEM envoie notamment les couples suivants, dans cet ordre :

```text
9:00  3:FF  F:FF  8:00  C:00  2:00  A:00  6:00  E:00  1:00
```

Cette liste est un **relevé de mots**, pas une autorisation d’assimiler chaque
adresse à une LED ni de tout balayer au hasard sur le matériel. Certaines
adresses peuvent être des registres de configuration du circuit récepteur.

Les éclairages blancs de touches signalés sur la façade ne sont donc pas
encore associés un à un aux sorties de ce bus. Le nombre de contacts P1..P6
ne permet pas de déduire le nombre ni le câblage des LED. Aucun tableau
« adresse → touche éclairée » complet n’est établi à ce stade.

Pour terminer cette cartographie : relever le circuit récepteur et ses pistes,
puis capturer les mots OEM pendant les changements d’éclairage et d’intensité.
Sur le banc, comparer les mots bruts ; sur la carte, comparer les LED visibles.
Une variation dans le menu peut affecter plusieurs canaux simultanément.

### Rétroéclairage écran

Il était déjà décrit dans `LCD_CABLAGE_PILOTAGE_ET_INTEGRATION_V11_8.md`.
Le rappel ci-dessus permet de développer la façade sans dépendre de ce fichier.
La valeur est un octet brut, pas une mesure photométrique ni une tension PWM
identifiée. Display On/Off du LCD, sommeil du contrôleur et éclairage sont
indépendants : un dessin valide peut être invisible si le canal 8 vaut zéro.

## 10. Rappel pour les voyants du microphone

Ils ne sont pas directement accessibles par un GPIO du GD32 par voyant.
La liaison radio → microphone est USART0, associée à PA9/PA10 par l’analyse
de configuration. Le raccordement exact jusqu’au connecteur doit être vérifié.

Une trame de 16 octets commence par `53` et finit par `06`. Les champs 1/3
et 4/6 portent les commandes réception/émission des voies, et l’octet 7 porte
la sélection principale `0=A`, `1=B`. Cette dernière correspond fortement
aux voyants blancs MAIN A/B, selon firmware, manuel et observation utilisateur.
Le numéro des GPIO internes au microphone n’est pas identifié.

Ne pas piloter PE3/PE4 en espérant commander les deux voyants du microphone.
Le détail est dans `NOTICE_CHANGELOG_MICROPHONE_V11_8.md`.

## 11. Routines C indépendantes des variables OEM

Ce code est un squelette pour un programme propriétaire de ses périphériques.
Il ne constitue pas une injection prête à lancer dans l’application OEM.
`board_us()` et `board_wait_us()` doivent provenir d’une horloge du nouveau
firmware. Le code n’emploie pas les boucles non calibrées de l’OEM.

```c
#include <stdint.h>
#include <stdbool.h>

#define R32(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define GA 0x40010800u
#define GB 0x40010C00u
#define GC 0x40011000u
#define GE 0x40011800u
#define ADC0 0x40012400u

extern uint32_t board_us(void);
extern void board_wait_us(uint32_t us);

static void gpio_set(uint32_t port, uint32_t mask) {
    R32(port + 0x10u) = mask;
}
static void gpio_clear(uint32_t port, uint32_t mask) {
    R32(port + 0x14u) = mask;
}
static void gpio_mode(uint32_t port, unsigned pin, uint32_t mode) {
    uint32_t address = port + (pin < 8u ? 0u : 4u);
    unsigned shift = 4u * (pin & 7u);
    R32(address) = (R32(address) & ~(15u << shift)) |
                   ((mode & 15u) << shift);
}

/* Horloges GPIO deja actives, usage autonome seulement. */
static void panel_input_gpio_init(void) {
    gpio_set(GA, 3u); /* pull-up propose sur PA0/PA1 */
    gpio_mode(GA, 0, 8); gpio_mode(GA, 1, 8);
    gpio_set(GC, 0x300u);
    gpio_mode(GC, 8, 8); gpio_mode(GC, 9, 8);
    gpio_mode(GB, 0, 0); gpio_mode(GB, 1, 0);
    gpio_mode(GC, 2, 0); gpio_mode(GC, 5, 0);
}

static bool power_pressed(void) {
    return (R32(GA + 8u) & 1u) == 0;
}
static bool dial_pressed(void) {
    return (R32(GA + 8u) & 2u) == 0;
}
static uint8_t encoder_levels(void) {
    return (uint8_t)((R32(GC + 8u) >> 8) & 3u);
}

/* ADC deja alimente, calibre et configure en conversion unique :
   scan/DMA/continu desactives, alignement droit, sequence de longueur 1,
   declencheur logiciel selectionne et autorise, sample time adapte.
   Aucun autre utilisateur ne modifie ADC0 pendant cet appel. */
static bool adc_read_one(uint8_t channel, uint16_t *out) {
    if (channel > 15u || out == 0) return false;
    R32(ADC0 + 0x34u) = channel; /* RSQ2, premier rang */
    (void)R32(ADC0 + 0x4Cu);     /* consommer un ancien resultat */
    R32(ADC0 + 8u) |= (1u << 22); /* SWRCST */
    uint32_t start = board_us();
    while ((R32(ADC0) & 2u) == 0u) {
        if ((uint32_t)(board_us() - start) >= 1000u) return false;
    }
    *out = (uint16_t)(R32(ADC0 + 0x4Cu) & 4095u);
    return true;
}

/* Codes propres au nouveau programme, sans dependance aux codes OEM. */
enum Key { K_NONE, K_P1, K_P2, K_P3, K_MENU,
           K_P4, K_P5, K_P6, K_EXIT, K_INVALID };

static enum Key ladder_key(uint16_t sample, bool second_group) {
    static const enum Key keys[2][4] = {
        {K_P1, K_P2, K_P3, K_MENU}, {K_P4, K_P5, K_P6, K_EXIT}
    };
    if (sample > 4095u) return K_INVALID;
    unsigned slot = sample <= 500u ? 0u : sample <= 1500u ? 1u :
                    sample <= 2500u ? 2u : sample <= 3500u ? 3u : 4u;
    return slot == 4u ? K_NONE : keys[second_group ? 1u : 0u][slot];
}

struct Debounce {
    enum Key candidate, stable;
    uint32_t since_ms;
};
/* Appeler periodiquement. true = nouvel etat stable, y compris relachement. */
static bool key_update(struct Debounce *d, enum Key raw, uint32_t now_ms) {
    if (raw == K_INVALID) {
        d->candidate = K_INVALID; d->since_ms = now_ms;
        return false; /* invalider la stabilite et signaler la panne a part */
    }
    if (raw != d->candidate) {
        d->candidate = raw; d->since_ms = now_ms;
    }
    if (raw != d->stable && (uint32_t)(now_ms - d->since_ms) >= 20u) {
        d->stable = raw; return true;
    }
    return false;
}

/* Renvoie un mouvement de phase, pas necessairement un cran mecanique.
   Initialiser previous avec encoder_levels() avant le premier appel. */
static int encoder_phase(uint8_t *previous, uint8_t next) {
    static const int8_t table[16] = {
         0, 1,-1, 0, -1, 0, 0, 1,
         1, 0, 0,-1,  0,-1, 1, 0
    };
    uint8_t old = *previous & 3u;
    next &= 3u;
    *previous = next;
    return table[(old << 2) | next];
}

/* Bus PE3/PE4, mots complets ; circuit recepteur encore a qualifier. */
static void status_word(uint8_t word) {
    gpio_clear(GE, 0x18u);
    gpio_mode(GE, 3, 3); gpio_mode(GE, 4, 3);
    for (unsigned i = 0; i < 8; ++i) {
        gpio_clear(GE, 0x10u);
        if (word & (1u << i)) gpio_set(GE, 8u); else gpio_clear(GE, 8u);
        board_wait_us(1);
        gpio_set(GE, 0x10u); board_wait_us(1);
        gpio_clear(GE, 0x10u); board_wait_us(1);
    }
    gpio_clear(GE, 0x18u); /* pull-down avant restitution du mode entree */
    gpio_mode(GE, 3, 8); gpio_mode(GE, 4, 8);
}

/* Propriete exclusive de PA5/PB3/PB4 requise ; sorties deja configurees.
   Aucun registre non identifie ne doit etre ecrit au hasard. */
static bool lighting_word(uint8_t address, uint8_t value) {
    if (address > 15u) return false;
    uint16_t word = ((uint16_t)address << 8) | value;
    gpio_clear(GA, 0x20u); board_wait_us(1);
    for (int bit = 11; bit >= 0; --bit) {
        gpio_clear(GB, 8u);
        if (word & (1u << bit)) gpio_set(GB, 16u); else gpio_clear(GB, 16u);
        board_wait_us(1);
        gpio_set(GB, 8u); board_wait_us(1);
    }
    gpio_clear(GB, 8u); board_wait_us(1);
    gpio_set(GA, 0x20u); board_wait_us(1);
    return true;
}
```

Pour lire les commandes analogiques : acquérir canal 8, canal 9, canal 12 et
canal 15, puis décoder/filtrer chaque valeur. En cas de timeout ADC, ne pas
transformer une valeur périmée en nouvelle touche ou nouveau volume.

Initialiser les structures Debounce à zéro. Pour Power et Dial, appliquer le
même principe de stabilité sur leurs valeurs booléennes. Pour un codeur complet,
compter les mouvements de phase et rejeter une transition double en réinitialisant
l’accumulateur de cran ; ne pas seulement sommer indéfiniment les retours nuls.
Déterminer le nombre de phases par cran et le signe après observation mécanique.

Les broches, horloges et ADC sont volontairement des préconditions explicites.
L’initialisation ADC doit notamment sélectionner la source logicielle, attendre
la stabilisation, remettre la calibration à zéro, calibrer et attendre sa fin.
En scan DMA, remplacer la routine de conversion unique par une lecture cohérente
d’un tampon **déclaré par le nouveau programme** et traiter les débordements.

Les accès CTL sont des lectures-modifications-écritures : les protéger contre
un autre pilote modifiant le même registre. Les accès BOP/BC évitent de changer
les autres sorties mais ne remplacent pas un verrou de transaction du bus.

## 12. Synthèse des timings

| Élément | Constat OEM / banc | Choix initial proposé, non certifié matériel |
| --- | --- | --- |
| Touches analogiques | Seuils et compteur de stabilité retrouvés | Lecture 5 ms, stabilité 20 ms |
| Power / Dial | Actif bas ; double lecture Dial avec boucle | Stabilité 20 ms ; appui long séparé |
| Codeur | EXTI8 descendant et lecture PC9 | Scrutation 0,5..1 ms ou IRQ courte |
| Volumes | Moyenne de quatre lectures espacées de 1 ms au démarrage | Mise à jour 10..20 ms, filtre et hystérésis |
| ADC du banc | 64 instructions/conversion, timing synthétique | Calculer d’après horloge ADC et impédance |
| Voyant PE3/PE4 | Boucles de valeur 2 | Setup et phases de 1 µs pour premier essai |
| Bus éclairage | Boucles de valeur 10 | Phases de 1 µs pour premier essai |

Les valeurs proposées ne sont pas des limites extraites d’une fiche du circuit
récepteur : il n’est pas encore identifié. Capturer les fronts OEM puis ajuster.
Le quartz 12 MHz, le PLL et les diviseurs doivent être traités par l’initialisation
horloge du nouveau programme. Ne pas convertir tous les tours de boucle en µs.

## 13. Indépendance du firmware et limites du banc

Les constantes utiles au nouveau firmware sont les ports, canaux ADC, polarités,
formats de mots et seuils physiques à calibrer. Les variables de touches,
volumes ou voyants du constructeur n’en font pas partie.

Les contrôles actuels du banc modifient des niveaux GPIO ou des échantillons
ADC, et non des événements de touches écrits dans la RAM OEM. Cela rend les
stimuli réutilisables avec une autre application, sous réserve que les modes
ADC/GPIO demandés soient implémentés.

Des parties de l’observation restent toutefois liées au profil OEM. Le bus
d’éclairage est historiquement armé à un appel connu ; les entrées GPIO du
banc comportent aussi des chemins conditionnés par le masque de lecture du
pilote OEM. Un firmware lisant tout ISTAT peut donc révéler une lacune du modèle.
Il faudra rendre ces entrées et l’armement entièrement dépendants de l’état
matériel pour qualifier « n’importe quel firmware ». Le code C de cette note
ne doit pas être adapté artificiellement à ces particularités du simulateur.

Les durées d’appui automatique de l’interface du banc sont des durées de
stimulus, pas les temps de rebond des vrais boutons. Les volumes du profil
synthétique à 1800 ne sont pas des mesures du poste.

## 14. Vérifications à terminer sur la carte

| Travail | Pourquoi il manque encore |
| --- | --- |
| Continuité PB0/PB1 vers résistances et contacts | Confirmer l’ordre et les combinaisons de touches |
| Mesure ADC de chaque touche, au repos et en combinaison | Fixer marges, hystérésis et détection de défaut |
| Continuité PC2/PC5 et butées des deux potentiomètres | Confirmer ordre A/B, sens et dynamique |
| Capture codeur dans les deux sens | Déterminer transitions par cran et rebonds |
| Identifier les récepteurs PE3/PE4 et PA5/PB3/PB4 | Comprendre mots, latch, sorties et timing minimal |
| Associer canaux d’éclairage aux LED physiques | Compléter la cartographie des touches éclairées |
| Vérifier maintien alimentation et réveil | Distinguer contact Power et commande d’alimentation |

La lecture des entrées est suffisamment décrite pour construire un pilote de
mise au point. La cartographie des éclairages de touches ne permet pas encore
de déclarer une façade entièrement qualifiée. Cette limite doit rester visible
dans le firmware et dans les résultats d’auto-test.

## 15. Sources et traçabilité

Application analysée : `D578UV_GD_V1.21_20240619.CDD`, SHA-256
`02b2a3b56bd57c7ada581eb52b9b6f41c5d51aaec1b068d37585efd58dff9c9a`.

Sources du dépôt : `bench/lab_inputs.py`, `bench/emulate_front_v121.py`,
`bench/verify_front_oem.py`, `bench/adc_dma.py`, `bench/lighting.py`,
`bench/status_led.py` et `bench/profiles/front_panel.json`.
Dépôt : <https://github.com/Telectroboy/OpenD578>.

Pour retrouver les preuves dans V1.21, uniquement comme index d’analyse :
lecteurs analogiques `0x0800F048` et `0x0800F08A`, filtre `0x0800F0CC`,
lecture Dial `0x0800F11C`, configuration codeur `0x0808C9EC`, gestionnaire
`0x0808CC0A`, bus voyant `0x0808A3D6`, bus éclairage `0x0808A7C0`.
Ces adresses ne sont utilisées par aucune routine C proposée ci-dessus.

Référence des périphériques : GigaDevice, GD32F30x User Manual, chapitres GPIO,
AFIO/EXTI, ADC, DMA et RCU. Une copie Rev2.9 a été consultée pour cette note :
<https://www.gd32mcu.com/data/documents/userManual/GD32F30x_User_Manual_Rev2.9.pdf>.
La fiche exacte du GD32F303VKT6 et le schéma de la carte doivent compléter
les vérifications électriques. Les constats de câblage fonctionnel viennent
du code et des traces, pas d’un brochage de carte déduit du manuel MCU seul.

Cette note documente le développement ; elle ne modifie pas le banc V11.8,
ne publie pas de nouveau firmware et n’annonce aucun essai physique effectué ici.

Vérification de cette note : 43 tests Python réussis pour l’ADC/DMA, les
périphériques de façade, les entrées et le voyant. Le bloc C compile sur hôte
avec les contrôles de syntaxe et d’avertissements. Un test C séparé vérifie les
4096 valeurs de chaque groupe de touches, une valeur invalide, la stabilité,
le relâchement après entrée invalide, le débordement du compteur temporel et
les transitions du codeur dans les deux sens. Les accès matériels ne sont pas
exécutés par ce test ; ce n’est pas une compilation ARM liée ni un essai radio.
