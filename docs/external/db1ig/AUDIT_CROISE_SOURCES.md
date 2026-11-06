# Audit DB1IG source par source et comparaison avec OpenD578

**Date : 6 novembre 2026. Base locale :** archive `OpenD578_COMPLET_SOURCES_F1DMG_VK7ZJA_20261106.zip`, extraite avant cet audit. Cette base reprend les correctifs de facade et les dossiers historiques du projet. Le depot GitHub en ligne n'a pas ete interroge directement ; les eventuels commits plus recents ne sont donc pas couverts.

## Methode de rapprochement

- Les 60 chapitres VK7ZJA de l'index existant ont ete repris **sans suppression** et relies aux vrais documents OpenD578.
- Chaque difference est rangee dans une categorie : `deja documente`, `resume a enrichir`, `nouveau detail`, `transposable apres verification`, `hors coeur firmware`.
- Les routines OEM, GPIO, traces et resultats physiques du projet ont priorite pour **la revision de l'utilisateur**. L'etude historique complete les fonctions, pas leur statut.
- Une valeur historique, une recommandation d'usage et un mot de registre observe sur le poste ne sont pas interchangeables.

## Source DB1IG-01 : copie VK7ZJA D578, v7.4 (20 octobre 2022)

**Original :** Jason Reilly, VK7ZJA. **Miroir :** DB1IG (avec l'autorisation historique mentionnee par l'hebergeur). **Lien :** <https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php>. **Version allemande** : <https://www.db1ig.de/pages/de/anytone/jason_reilly_vk7zja_-_de/jason-reilly-vk7zja-578mods.php>.

### Nouveaux details a ajouter au fonds existant

| ID | Sujet | Etat dans OpenD578 avant revue | Apport exploitable | Priorite |
|---|---|---|---|---|
| D578-01 | PTT microphone de table | USART0, trames filaires et pinout presents | Autre voie PTT : resistance 1 a 2,2 kohms entre broches 1/8, `HandOpMode = Level Detection`; risque de TX involontaire si mal configure | P1 |
| D578-02 | Reglages audio Bluetooth | BT01/BP-02/ET12 deja documentes | Interactions `BT + int mic` et `BT + int spk`, utiles pour modeliser le routage et le microphone externe | P1 |
| D578-03 | Modes de demarrage | MCU UPDATE, P4+DIAL et plusieurs autres cas notes | Table historique des modes dedies GPS, SCT, LinkBoard, Hand-Soft, icones et BHT | P1 |
| D578-04 | Alignement | Options TEST et octets de permission tres bien analyses | Vocabulaire complet par bande et voie : FQCA, PA*, BPF*, AGC*, RSSI*, MOD*, SQTH*, CTCW, DCSW, TONE* et BER/FSK | P1 |
| D578-05 | GPS antennes | Module GNSS, alimentation de secours, UART presents | Deux mini-connecteurs coaxiaux sur carte facade historique ; un utilise pour SMA externe, autre libre | P2 |
| D578-06 | Filtres FI | Topologie double FI 38,55/38,85 MHz connue | Emplacements de filtres supplementaires et resistances 0 ohm ; etage distinct du module AM PLUS | P2 |
| D578-07 | Traitement audio | Codec AIC3204 et commandes audio presents | `Mic Enhance` signale comme effet sur TX DMR et non sur TX analogique / RX ; verifier registres et chemin OEM | P2 |
| D578-08 | FM broadcast | RDA5802N documente dans le banc | Stations entre 76 et 87,5 MHz via memoires, limites de sous-bandes du tuner selon configuration | P2 |
| D578-09 | Caracterisation reception | Etages RF et filtres connus | Mesures historiques RF/sensibilite, point de comparaison pour essais de non-regression | P2 |
| D578-10 | Caracterisation puissance | Etages AFT05MP075N connus | Mesures historiques LOW/MID/HIGH/TURBO pour 145,5 et 435 MHz ; ne pas substituer aux alignements individuels | P2 |
| D578-11 | Icones GPS | Ecran/bitmaps/NAND et mode update documentes | L'archive historique distingue le paquet d'icones `.spi`, son mode d'entree et le contenu GPS | P2 |
| D578-12 | Modes analogique et DMR | DMR operationnel sur OEM, RX independantes connues | Deux RX FM simultanees mais une seule demodulation DMR concurrente dans le poste historique | P2 |
| D578-13 | Codeplug et migration | USB CPS + NAND + format canal deja analyses | `Export All` ne couvre pas necessairement toutes les options et secrets ; reconstruction CPS par generation | P1 |
| D578-14 | Recovery | Recuperation MCU UPDATE et bootloader connus | Procedure historique de demarrage d'urgence et separations entre reset, recovery et reprogrammation | P2 |
| D578-15 | Blindage et filtrage | FI/varactors connus | Blindage supplementaire historique, influence de capacite parasite puis necessite de recalibrer BPF A/B | P3 |
| D578-16 | Refroidissement | PA et alimentation connus | Modifications historiques ventilation/deflecteurs ; une branche F1DMG ancienne y est citee | P3 |
| D578-17 | Façade deportable | Bus LCD identifie par OEM | Hypothese de deport par nappe 40 voies : contrainte de temps de propagation/EMI, pas option OEM | P3 |
| D578-18 | Mises a jour de sous-modules | SCT/BT documentes | Distinction explicite application GD32, DSP SCT, Bluetooth LinkBoard, MCU microphone et ressources graphiques | P1 |

**Recoupements deja solides :** GD32F303VKT6, NAND TC58CVG1S3HRAIG, TLV320AIC3204, SCT3258, RDA5802N, QA4818N x4 / reference 26 MHz, AFT05MP075N x2, double FI et sauvegarde RTC/GPS. Voir `docs/hardware/VALIDATION_FONCTIONS_OEM.md`, `docs/peripherals/`, `docs/hardware/QA4818N_RECONSTRUCTION_REGISTRES_PLL_CHAINES_RX_TX.md` et `docs/TEST_MODE_OPTIONS.md`.

**Limite de transposition :** la page de 2022 n'a pas teste les deux cartes de l'utilisateur sous les versions firmware 2024/2026. Les modifications de bandes et les valeurs exemples du menu TEST ne doivent pas etre executees comme instructions de developpement ni comme calibrations usine.

## Source DB1IG-02 : copie VK7ZJA D868/D878, v20 (20 octobre 2022)

**Lien :** <https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_878mods.php>. Versions allemandes du meme texte : ne constituent pas une confirmation independante.

**Pertinence croisee :** la famille D868/D878 partage des concepts de MCU GD32, baseband SCT3258, codec AIC3204, GPS ATGM336H et circuits d'extension Bluetooth/APRS. Ce document fournit une chronologie materielle, des outils d'actualisation du SCT, des pistes de sauvegarde des calibrations, de traitement des erreurs codeplug et de proprietes du logiciel CPS.

**Informations candidates absentes ou incompletes dans OpenD578 :**

1. **Evolution D878 -> D878-II** : une carte fille realise Bluetooth + reception APRS FSK, alors que le D578 PRO n'a pas l'APRS RX et que le PLUS possede une carte supplementaire RF/Bluetooth propre a sa variante. Ce rapprochement justifie une comparaison photographique, pas une equivalence de circuit.
2. **AT1846S contre QA4818N** : l'AT1846S du portable n'est pas un schema directement applicable aux quatre QA4818N du mobile. Les mots PLL en `0x29/0x2A` sont encore a comparer aux transactions OEM reelles.
3. **Aide de sauvegarde d'alignement et formats de flash** : utile pour verifier les outils OpenD578, mais les offsets NAND et le conteneur RDT du D878 ne sont **pas automatiquement** ceux du D578. En particulier l'octet `0x0011` cite pour un codeplug portable ne doit pas etre inscrit dans un D578 sans preuve.
4. **Firmware interne SCT3258** : historique de plusieurs versions de baseband, dont `V2.01.07BF`. La version sur chaque poste doit etre lue avant comparaison et il faut conserver les fichiers du module distincts de ceux du MCU.
5. **Audio et Bluetooth** : comportements de certains casques Bluetooth, DMR vocoder et traitement micro qui generent des cas de test pour BT01/BP-02, mais ne suffisent pas a definir le protocole UART ET12.
6. **Technologie GPS** : modules differents selon generation et sauvegarde de position, pas de transplantation automatique des circuits 878 vers 578.

**Existant recoupe :** `docs/hardware/BLUETOOTH_PRO_PLUS_D878_COMPARAISON.md`, `docs/hardware/BLUETOOTH_D868BT_SP_ET12.md`, `docs/peripherals/04_DMR_SCT3258_BOOTSTRAP_HPI_PAQUETS_CODEC_PARAMETRES.md`, `docs/03_NAND_LECTURES_ECC_CARTE.md`.

## Source DB1IG-03 : guide VK7ZJA sur les bases DMR

**Lien :** <https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_dmrbasics.php>.

**Valeur ajoutee :** lexique des concepts du protocole radio DMR (color code, timeslots, groupes, identifiants, Tier II, simplex). OpenD578 possede deja la couche physique de simulation SCT/HPI, mais ne doit pas confondre ces concepts d'exploitation avec les registres du SCT3258. Utilisation prevue : fiches d'acceptation DMR (appel prive, appel groupe, slot, RAS non presume, filtrage par color code) et distinction entre protocole radio et transport HPI OEM.

**Priorite :** P2 pour la qualification fonctionnelle DMR ; ce guide pedagogique ne contient pas un schema de communication GD32 <-> SCT.

## Source DB1IG-04 : guide DB1IG de creation d'un premier codeplug

**Lien :** <https://www.db1ig.de/pages/de/anytone/anytone-der-erster-codeplug.php>.

**Information a conserver :** codeplug, CPS et firmware doivent etre rapproches par version. La page recommande de reconstruire un codeplug apres changement de firmware, en passant par export/import. Le D578 n'exige pas toujours une nouvelle version du CPS a chaque petite mise a jour, ce qui interdit de coder une regle trop rigide.

**Consequence pour OpenD578 :** ajouter aux essais du CPS un `profil_version` (variante PRO/PLUS, branche GD32/AT32, application, version codeplug, MODE, capacite contacts), un import/export sans perte, et un diff sur les champs conserves. La documentation actuelle de `docs/cps/` couvre les trames USB et les canaux, mais pas tout le cycle de migration utilisateur.

## Source DB1IG-05 : Digital Contact List Editor (DB1IG)

**Lien :** <https://www.db1ig.de/pages/en/software-corner/-anytone--digital-contact-list-editor.php>.

**Nouveau par rapport au CPS minimal OpenD578 :** outil DB1IG de preparation des contacts depuis RadioID.net, avec selection region/pays, estimation de capacite et quatre presentations, puis export CSV pour CPS. Le logiciel n'est pas la preuve du format NAND binaire ; il constitue un **oracle de structure CSV et de limite de contacts par modele**.

**Action :** inventorier les champs exportes, comparer avec `docs/cps/CODEPLUG_CANAL_OEM_V121.md` et preparer l'importeur de contacts distinct de la table canaux. Ne pas integrer l'executable tiers dans le depot sans licence.

## Source DB1IG-06 : mode d'emploi Digital Contact List Editor

**Lien :** <https://www.db1ig.de/pages/en/software-corner/-anytone--digital-contact-list-editor/digitale-kontaktlisten-editor-howto.php>.

**Apport :** options de selection RadioID.net, quatre rendus de liste et etapes d'export CSV, pour definir des cas de test de longueur de chaine, encodage, champ indicatif/nom, ordre, tri, doublons et capacites PRO/PLUS. Cette page precise explicitement les limitations des portables D868/D878 ; ne pas transposer leur plafond aux D578.

## Source DB1IG-07 : page d'accueil des miroirs VK7ZJA

**Lien :** <https://db1ig.de/pages/en/anytone/jason_reilly_vk7zja.php>.

**Apport documentaire :** liste des oeuvres historiques : D578, D868/D878, bases DMR et documents GD-77. Ce sont des sources primaires distinctes dans leur sujet, mais plusieurs traductions/miroirs du meme travail ne doivent pas etre comptes comme autant de preuves materielle independantes.

## Sources de recoupement non independantes et independantes

- **Non independantes :** traduction allemande DB1IG de l'article D578, autre miroir VK7ZJA chez theweeks.org, reddicams, radio.carstenbauer.net et PDF de reproduction. Ces copies peuvent renseigner les changements entre editions, sans constituer de nouvelles observations.
- **Independantes par nature :** observations OEM et relevages physiques F4EGM ; datasheets constructeur GD32F303, QA/AT1846S, TLV320AIC3204, RDA5802N ; rapports FCC identifiant les variantes ; outils libres qdmr/codeplug si la branche D578 correspond.

## Synthese des priorites

**P1, directement exploitable pour le developpement :** matrices de boot/mise a jour, microphone resistif et HandOpMode, table de parametres TEST vers adresses NAND et routines OEM, compatibilite CPS/versions, separation des firmware MCU/SCT/BT/micro.

**P2, validation fonctionnelle :** chemin audio Bluetooth avec les reglages Mic/Speaker, donnees RF historiques de reference, test BER/FSK et qualite du mode DMR, antenne GPS, banque des bitmaps `.spi`, contacts CSV.

**P3, observation et maintenance :** refroidissement, positions FI supplementaires, ecran deportable, boitier/connecteur, ergonomie et accessoires.

Les nouveaux constats et les procedures recommandables sont detailles dans [les complements techniques](COMPLEMENTS_TECHNIQUES_D578.md). La matrice [des 60 rubriques](MATRICE_60_THEMES.md) permet un suivi sans perte de sujet.
