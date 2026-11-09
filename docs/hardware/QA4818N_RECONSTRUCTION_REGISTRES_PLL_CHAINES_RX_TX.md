# QA4818N x4 : reconstruction du protocole, des fréquences, des banques et des commandes RF

**Correction du 9 novembre 2026 :** lire d’abord [l’état OEM actuel](QA4818N_ETAT_OEM_20261109.md). Les liaisons PB3/PB4 et les quatre CS sont validées par firmware. La fréquence OEM utilise **0x38/0x39**, et non les exemples AT1846S 0x29/0x2A conservés ci-dessous comme historique. Les anciens appels à requalifier physiquement ces bus sont remplacés par cette correction.

## Archive du 6 novembre — ne pas confondre avec le contrat courant

**OpenD578, variante PRO GD32 V1.21, étude du 6 novembre 2026.**

**Statut : pilote de codage et analyseur de trames disponibles, pas de firmware RF matériellement validé.** Les séquences du constructeur *peuvent* être mesurées par le banc `bench/rf_spi.py`, mais **aucune capture complète et authentifiée d'un changement de fréquence RX/TX n'a été retrouvée dans les archives publiques actuellement accessibles**. Les valeurs numériques ci-dessous proviennent soit d'une équation publiée pour l'AT1846S, soit d'un scénario explicitement hypothétique. Il serait incorrect de les appeler « mots observés du D578 » sans enregistrer un `RF_control_spi.frames` ou `radio.frames` exécuté avec l'application OEM.

## 1. Objectif de cette reconstruction

Développer séparément :

1. Le **décodeur de bus** vérifiable sur les écritures GPIO de l'OEM, déjà réalisé dans `bench/rf_spi.py`.
2. Un **analyseur de traces** lisant les registres par banque, les rapprochant des fréquences du VFO et des FI, sans stimuler le poste (`tools/qa4818n_trace.py`).
3. Un **encodeur de fréquence C** pour les registres `0x29/0x2A`, fondé sur la convention documentée pour l'AT1846S et entièrement indépendant des fonctions/adresses RAM OEM (`firmware/rf/qa4818n_frequency.[ch]`).
4. Un **transport de test injecté** qui ne connaît ni GPIO ni PA et ne peut pas écrire si l'activation explicite manque (`firmware/rf/qa4818n_transport.[ch]`).
5. Les futures phases de portage : identification physique des quatre circuits, initialisation horloge/bande, changements RX/TX, RF switches, filtres à varicaps, contrôle de puissance, CTCSS/squelch, DMR et gestion des conflits entre voies.

## 2. Architecture matérielle : établie pour la famille, non attribuée sur chaque PCB

Une documentation technique du D578 par VK7ZJA décrit : quatre QA4818N en LQFP32, des références 26 MHz, **deux oscillateurs locaux indépendants** (VFO A/B) et **deux circuits de réception à conversion directe**, placés après des filtres FI de **38,550 MHz / 38,850 MHz**. La réception utilise donc un premier changement de fréquence, puis une démodulation de FI. La présence de quatre boîtiers grattés, dont un près d'un composant « 26.00 », a été rapportée sur le poste étudié. **La correspondance des quatre boîtiers, des quatre banques série et des deux FI reste inconnue.**

Le QA4818N serait compatible avec le brochage de l'AT1846S, mais il est décrit comme plus capable. On ne peut donc pas transposer sans test ses limites de bandes, ses registres non documentés, ses séquences de calibration ou la formule du synthétiseur.

Conséquences sur la fréquence :

- **Fréquence affichée RX** : fréquence reçue à l'antenne ; pas nécessairement fréquence programmée dans le QA utilisé comme oscillateur local.
- **Fréquence d'oscillateur local** : pour une première FI positive, un mélangeur idéal permet deux possibilités, injection haute ou basse : `F_LO = F_RX + F_IF` et `F_LO = F_RX - F_IF` (cette dernière n'a de sens ici que si elle est positive). La sélection effective, l'oscillateur qui produit cette fréquence et son éventuelle multiplication/division ne sont pas vérifiés.
- **Fréquence du QA de réception FI** : pourrait être proche de 38,550 ou 38,850 MHz ; il faudra le démontrer par comparaison des registres et par mesure.
- **TX** : le schéma de synthèse en émission peut différer du schéma de réception ; n'appliquer **aucune** des équations RX au TX sans preuve.
- Les chiffres 38,550 et 38,850 ne permettent pas, seuls, de décider quel filtre correspond à A ou B ni s'il existe un réglage de décalage supplémentaire.

## 3. GPIO et interface série reconstitués dans le banc V1.21

Source locale : `bench/rf_spi.py` et contrôles croisés OEM décrits dans `docs/RF_SPI_INTERRUPT_FIX.md`.

| Signal logique | GPIO observé dans le modèle | Signification | Niveau de preuve |
| --- | --- | --- | --- |
| SCLK | PB3 | Horloge des transactions RF | Décodage GPIO OEM dans le banc, non mesuré au CI |
| SDIO | PB4 | Données série bidirectionnelles, change de direction à la lecture | Idem |
| CS banque 0 | PB5, actif bas | Sélection logique 0 | Idem |
| CS banque 1 | PB2, actif bas | Sélection logique 1 | Idem |
| CS banque 2 | PC13, actif bas | Sélection logique 2 | Idem |
| CS banque 3 | PE1, actif bas | Sélection logique 3 | Idem |

**Trame d'écriture constatée dans le modèle :** `commande/adresse` sur 8 bits, puis valeur de registre 16 bits, MSB d'abord, soit 24 fronts d'horloge. Le bit 7 du premier octet distingue lecture (`1`) et écriture (`0`), les 7 autres bits contiennent l'adresse `0x00..0x7F`.

Lors d'une lecture, l'OEM libère SDIO et le modèle présente 16 bits. Il faut reproduire sur le matériel la polarité des fronts, les temps de maintien, la configuration GPIO et le comportement de la ligne avant d'utiliser un pilote électrique autonome.

Le banc crée **quatre banques logiques**. Rien ne démontre encore que `bank 0 = LO A`, `bank 1 = LO B`, etc. Les lecteurs OEM de statut RX simulés en banques 0/1 rendent **plausible** un rôle de réception pour ces banques ; cela reste une hypothèse de correspondance, et pas un relevé de continuité.

**Mode trois fils de l'AT1846S** : dans sa documentation, les broches `SCLK=2`, `SDIO=3`, `XTAL1=5`, `XTAL2=6`, `MODE=7`, `SENB=8` concernent un boîtier de la famille AT. La numérotation des QA4818N réels n'est pas validée par une mesure sur le PCB.

### Format des mots, exemple de préparation de transaction

Une écriture de la valeur `0x0023` dans le registre `0x29` s'exprime sous forme de **trois octets** `29 00 23`; pour `0x85C0` dans `0x2A`, `2A 85 C0`. Ces octets sont produits par les encodeurs **hors ligne**. Ils ne doivent pas être interprétés comme une séquence suffisante pour changer de fréquence : page, initialisation, recalibration, état radio et ordres d'écriture peuvent entrer en jeu.

### Pagination

Le registre `0x7F` est utilisé comme sélecteur de page. Le banc conserve une page **par banque** et différencie les registres `(bank, page, address)`. Toute extraction doit préserver cette granularité ; une écriture `0x29` en page 1 ne doit pas être prise pour une programmation de fréquence en page 0.

## 4. Décodage de fréquence AT1846S, à éprouver sur QA4818N

Selon le guide de programmation AT1846S :

```text
N = F_MHz * 16000
  = F_Hz / 62,5
reg[0x29] bits [13:0] = (N >> 16) & 0x3FFF
reg[0x2A] bits [15:0] = N & 0xFFFF
F_Hz = N * 62,5
```

`0x29[15:14]` n'appartient pas au champ fréquence de 30 bits. L'encodeur C utilise des entiers sur 64 bits et arrondit à l'unité la plus proche ; l'inverse renvoie un nombre de **demi-Hz**, sans perte des pas fractionnaires. **62,5 Hz est la résolution du champ numérique dans la documentation AT1846S**, pas nécessairement la largeur de pas radio validée du D578.

| Scénario *calculé* | F (MHz) | `0x29` | `0x2A` | Lecture possible |
| --- | ---: | --- | --- | --- |
| Fréquence FI 1 | 38,550 | `0x0009` | `0x6960` | QA récepteur FI, hypothèse |
| Fréquence FI 2 | 38,850 | `0x0009` | `0x7C20` | QA récepteur FI, hypothèse |
| RF VHF | 145,500 | `0x0023` | `0x85C0` | RF directe ou autre architecture |
| LO VHF, injection haute FI1 | 184,050 | `0x002C` | `0xEF20` | `145,500 + 38,550` |
| LO VHF, injection basse FI1 | 106,950 | `0x001A` | `0x1C60` | `145,500 - 38,550` |
| RF UHF | 435,000 | `0x006A` | `0x3380` | RF directe ou autre architecture |
| LO UHF, injection haute FI1 | 473,550 | `0x0073` | `0x9CE0` | `435,000 + 38,550` |
| LO UHF, injection basse FI1 | 396,450 | `0x0060` | `0xCA20` | `435,000 - 38,550` |
| LO UHF, injection haute FI2 | 473,850 | `0x0073` | `0xAFA0` | `435,000 + 38,850` |
| LO UHF, injection basse FI2 | 396,150 | `0x0060` | `0xB760` | `435,000 - 38,850` |

**Aucun de ces mots n'est encore une mesure QA4818N.** Les exemples permettent de tester le décodeur et de générer des signatures à chercher dans une capture OEM authentifiée. L'écart de 300 kHz entre les deux FI rend le test A/B particulièrement discriminant.

### Horloge 26 MHz

Guide AT1846S : `0x04[0]=0` choisit le groupe 25,6/26 MHz ; `0x30[14]=1` distingue 26 MHz de 25,6 MHz. Le composant `26.00` photographié peut être un quartz ou un oscillateur. Ni son type ni sa distribution aux quatre circuits n'ont été mesurés. Il faudra rechercher les écritures `0x04`, `0x30` et les registres de référence `0x2B/0x2C`, sans réutiliser mécaniquement les valeurs AT1846S.

## 5. Registres et signaux à reconstruire

| Adresse | AT1846S : repère public | D578 : preuve présente | Travaux restants |
| --- | --- | --- | --- |
| `0x04` | Choix famille d'horloges | Non qualifié dans la capture courante | Valeur de chaque banque au reset |
| `0x0F` | Band select sur AT1846S | Pas de valeur validée QA | Cartographie VHF/UHF/LO |
| `0x15` | Réglage IF et bande | Pas de calibration QA qualifiée | Séquence de calibration par voie |
| `0x24` | Contrôle de PLL/reset | Pas de lecture de verrou matériel | Mesurer lock / relock et timing |
| `0x29` / `0x2A` | Mot de fréquence sur 30 bits | Appels OEM identifiés, format sur banc | Corrélation VFO/banque/mots |
| `0x2B` / `0x2C` | Référence/ADC clock | Hypothèse AT seulement | Vérifier horloge 26 MHz |
| `0x30` | Power/modes RX/TX/clock | Aucune séquence RF entière qualifiée | Mute, RX off, TX off, lock |
| `0x44` | Contrôle de gain/volume AT | Modèle initialise `0x00FF`; écritures OEM conservées | Mesurer l'effet analogique |
| `0x7F` | Page du registre | Suivi explicite en simulateur | Repérer pages et tables |
| `0x0C` / `0x60` / `0x61` / `0x65` / `0x67` | États/mesures selon modèle et appels OEM | **Valeurs synthétiques au repos** dans le banc | Déterminer RSSI, bruit, portes, AF et squelch réels |
| Page 1, `0x17` | Bits de contrôle vus dans l'OEM | Lecture/modification dans certaines routines | Signification exacte bits `[14:8]` |
| Page 0, `0x25` | Commandes liées au haut-parleur/ventilateur vues dans le modèle | Valeurs OEM observées pour certains scénarios | Décider si registre RF ou commande d'interface externe |
| Page 0, `0x51` | Chemin contrôle lu/modifié | Présent dans les modèles | Mesurer fonction physique |

Les définitions fonctionnelles de l'AT1846S sont **une piste**, pas un dictionnaire certifié du QA4818N. L'accès RF du D578 est **trois fils avec sélections GPIO**, contrairement aux pilotes AT1846S d'autres postes qui utilisent I²C à 7 bits `0x2E` : **ne pas réutiliser leurs appels I²C**.

## 6. Séquence RF à identifier sans émission

Pour chaque voie A/B, relever au minimum la matrice suivante :

| Phase | Scénario | Réponse à obtenir du banc OEM | Ambiguïté à lever |
| --- | --- | --- | --- |
| 0 | Après Power/reset, RX désactivée | Toutes les écritures `(bank,page,reg,valeur)` dans l'ordre | Init globale, délais, pages |
| 1 | RX A 145,500 MHz, B non utilisée | Fréquences RF décodées et 4 banques actives | Association A/banques |
| 2 | RX A 145,5125 MHz | Différences de `0x29/2A` et autres registres | Sens de l'offset, pas, auto-calibration |
| 3 | RX A 145,500 MHz, RX B 435,000 MHz | Différences entre 4 banques | VFO A/B, double réception |
| 4 | Permuter VFO A/B, sans changer les fréquences | Différence des sélections et routage | VFO physique vs logique |
| 5 | Basculer 12,5/25 kHz | Modifications hors fréquence | Filtres et déviation |
| 6 | RX avec CTCSS désactivé / activé | Registres changeants et lecture états | CTCSS et squelch |
| 7 | Réception de station faible/forte | Statut de registres et signal RF mesuré | RSSI/AGC et seuils |
| 8 | Demander TX **uniquement en simulateur** | Chaîne commande OEM, PA/commutateur, timing | Effet réel TX séparé des mots registre |
| 9 | Firmware PRO puis PLUS (dumps distincts) | Profils de commande comparés | Variantes, calibrations |

**La chronologie compte autant que les valeurs.** Un seul `0x29/0x2A` peut être insuffisant si l'OEM désactive un chemin, met à jour des tensions BH2226, prépare la commutation RF et attend la PLL avant d'activer la réception.

## 7. Exporter des traces de notre banc

Le banc complet produit `resultat.json` accessible aussi via son API locale `/api/report`. Selon le moteur, la liste se trouve dans `radio.frames` ou `RF_control_spi.frames`. Les frames contiennent généralement `step`, `bank`, `page`, `register`, `direction`, `value`. **Les simulations avec valeurs RSSI/squelch injectées restent synthétiques**, même si le code OEM a réellement généré les commandes d'écriture.

```bash
python3 tools/qa4818n_trace.py chemin/vers/resultat.json --display-hz 145500000 --capture-name RX_A_145500 --out analyse_rx_a.json
```

Si plusieurs tests sont effectués, créer un `manifest.json` :

```json
{
  "captures": [
    {"name": "RX_A_145500", "file": "rx_a_145500.json", "mode": "RX", "display_hz": 145500000, "provenance": "OEM_GD32_V1.21_EMULATOR"},
    {"name": "RX_A_1455125", "file": "rx_a_1455125.json", "mode": "RX", "display_hz": 145512500, "provenance": "OEM_GD32_V1.21_EMULATOR"}
  ]
}
```

Puis :

```bash
python3 tools/qa4818n_trace.py --manifest chemin/vers/manifest.json --out comparaison_qa.json
```

L'outil : lit JSON, JSONL ou CSV ; contrôle les quatre banques ; ignore les lectures pour déterminer les valeurs programmées ; ne mélange pas les pages ; reconstruit un mot lorsqu'il a rencontré la paire complète ; propose les candidats `F affichée`, `F affichée ± FI1/FI2`, `FI1`, `FI2` ; et produit un rapport JSON. **Il ne devine pas le sens physique d'une broche ou une fréquence non écrite.** Les traces de démo portent `synthetic=true` et ressortent comme `SYNTHETIC_NOT_OEM`.

Pour capturer les changements de fréquence, il faut conserver le **scénario exact d'entrée** (VFO, canal, mode, fréquence RX et TX, CTCSS, bande passante, RX A/B, température et version OEM). Un écart de quelques registres peut traduire une calibration d'usine plutôt que la fréquence.

## 8. Architecture du pilote alternatif

Sources : `firmware/rf/qa4818n_frequency.[ch]`, `firmware/rf/qa4818n_transport.[ch]`.

- `qa4818_encode_frequency_at1846s()` : conversion entière et testable, indépendante des variables OEM.
- `qa4818_plan_frequency_at1846s()` : crée uniquement les deux écritures potentielles `0x29` / `0x2A`, pour une banque logique donnée.
- `qa4818_pack_write_at1846s()` : représentation MSB-first des trois octets de données, **sans contrôle GPIO**.
- `qa4818_apply_plan_to_bench()` : transporte le plan dans un **enregistreur injecté**, et refuse toute écriture si l'autorisation expérimentale est fausse.

Le code **n'active aucun PA, PTT, VCO, sortie RF, module DMR, DAC ou bus physique**. Il ne définit pas les délais de validation PLL, les filtres d'antenne, la garde RX/TX ni les niveaux de puissance. Le pilote matériel ultérieur devra disposer d'une table `board_profile` différente pour PRO/PLUS avec GPIO mesurés, calibration sauvegardée et politique fail-closed.

**Test C :**

```bash
gcc -std=c11 -Wall -Wextra -Werror \
  firmware/rf/qa4818n_frequency.c \
  firmware/rf/qa4818n_transport.c \
  firmware/tests/test_qa4818n_frequency.c -o /tmp/test_qa4818n
/tmp/test_qa4818n
```

**Test du décodeur :**

```bash
python3 -m unittest discover -s tools -p 'test_qa4818n_trace.py' -v
```

## 9. Conditions avant tout usage sur le poste physique

Aucune écriture GD32 ou QA ne sera autorisée tant que les conditions suivantes ne sont pas satisfaites : identification GPIO/boîtier par continuité ; vérification de la fréquence par instrument RF ; séparation contrôlée des deux RX et des LO ; confirmation du mapping bande/varicaps ; récupération de l'état OEM et du bootloader ; procédures de reset sans émission ; temporisations de PLL ; verrouillage TX hors bande, sans charge et en cas de défaut ; et qualification des deux branches du firmware.

Les valeurs d'alignement, la compensation de TCXO, les gains, les délais, les tables d'accord RF et la puissance TX sont propres à chaque poste. Les recopier depuis une autre radio peut rendre le poste non conforme ou provoquer un dysfonctionnement d'étage de puissance. Aucune émission n'est nécessaire pour terminer le décodage de fréquence RX.

## 10. Ce que l'on peut déduire seul et ce qui reste inaccessible sans nouvelles données

| Peut être déduit des sources / traces | Exige un nouvel enregistrement ou une mesure |
| --- | --- |
| Protocole numérique, pages, mots, paramètres et ordre d'écriture | GPIO vers broche exacte des quatre boîtiers ; mapping physique des CS |
| Mot de fréquence AT1846S et comparaison de plusieurs hypothèses de conversion | Vérifier que QA4818N utilise le même facteur et qu'il commande bien la fréquence attendue |
| Selon capture OEM : banques qui évoluent quand les fréquences RX/TX changent | Mesurer fréquence OL et FI, côté injection, harmoniques, bruit de phase et lock réel |
| Tables de paramètres usine adressées par le code OEM si image accessible | Calibrations complètes pour la radio donnée et contrôle de leur application |
| Organisation d'un vrai HAL indépendant du firmware constructeur | Régler les niveaux réels RF, duplexage et puissance sans danger |
| Comparaison des branches PRO V1.21 et PLUS lorsqu'elles sont toutes deux disponibles | Compatibilité réelle des cartes et composants par mesure |

## 11. Sources et traçabilité

- [VK7ZJA : architecture D578, quatre QA4818N et FI](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php)
- [RadioFoundry : inventaire matériel AnyTone](https://radiofoundry.org/docs/spec/hardware-anytone)
- [Guide AT1846S, champs de fréquence et d'horloge](https://manuals.plus/m/3c3831cb8a4faeacfd8c45ad662fb36c9ff3232018d83d1e7ece0938337cb578)
- [Table de registres AT1846S, projet OpenRTX](https://github.com/OpenRTX/openrtx.github.io/blob/master/at1846_registers.md)
- Code libre de comparaison [OpenRTX pilote AT1846S](https://git.hswro.org/fleg/OpenRTX/src/commit/c887a6159928ee47c2af9d5e2821e3f475647e96/platform/drivers/baseband/AT1846S_UV3x0.c), **I²C sur un autre matériel, non applicable directement au bus RF D578**.
- Traces / banc locaux : `bench/rf_spi.py`, `bench/hardware_runner.py`, `docs/RF_SPI_INTERRUPT_FIX.md`, `docs/04_RAM_ROUTINES_UI_RF_ET_BROCHAGE.md`.

**Prochaine preuve décisive :** une capture OEM réelle des changements A/B, à deux fréquences espacées de 12,5 kHz, avec les quatre banques et la paire `0x29/0x2A`. Tant qu'elle manque, ne pas présenter les tables calculées comme une reproduction exacte des signaux du QA4818N.

### Authenticité de l'image OEM V1.21

L'image historique analysée dans OpenD578 est identifiée sous le nom `D578UV_GD_V1.21_20240619.CDD`, charge applicative `0x08006000` et SHA-256 `02b2a3b56bd57c7ada581eb52b9b6f41c5d51aaec1b068d37585efd58dff9c9a`. Une archive officielle de firmware V1.21 est référencée publiquement par le distributeur [AnyTone USA](https://anytoneusa.com/Downloads/). Une tentative d'accès à son fichier ZIP lors de cette session n'a pas abouti. Le site ne fournit pas le fichier constructeur et n'affirme pas l'avoir désassemblé à nouveau le 6 novembre.

Le banc V11.7 peut générer un `resultat.json` en présence des images constructeur authentifiées, mais les anciennes archives publiques du dépôt ne contiennent ni cette image ni une matrice de trames RF de plusieurs fréquences. Pour un firmware **effectivement fonctionnel**, il faut récupérer cette preuve avant de fixer définitivement le mapping des banques, la formule QA et l'initialisation.
