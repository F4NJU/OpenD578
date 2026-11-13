# État du travail CPS — 12 novembre 2026

## CPS 0.10 — première liaison avec le firmware neuf, 13 novembre

Le panneau OpenD578 · VFO est distinct du panneau Banc OEM. Une variante
opt-in de rx_fm_alpha ajoute un pilote USBD CDC polling et un service ASCII/JSON
versionné en lecture seule : HELLO puis VFOS. Les valeurs proviennent des variables
propres à l'alpha ; aucune routine OEM, adresse de codeplug ou capture NAND.
Les binaires alpha existants ne sont pas remplacés. La nouvelle variante se nomme
rx_fm_cps.bin ; elle est réservée au banc et n'est pas un paquet à flasher.

Preuves réelles : USB énuméré par le programme ARM, A=145,500 et B=435,000 MHz,
valeur A=145,5125 après une action sur le codeur émulé ; commande WRITE refusée,
aucune observation de commande levant PE6 ou PC4. Le test HTTP a traversé le
serveur, l'adaptateur TypeScript, le CDC et l'ARM avec deux lectures sur le même
moteur. Seuls HELLO/VFOS ont été envoyés par le CPS. Le firmware annonce explicitement
l'absence de modification VFO, mémoires, CTCSS, DCS, TX et persistance.

Un blocage du runner matériel a aussi été corrigé : son quota d'attente était
consommé sur toute une exécution longue malgré la progression CPU/SysTick.
Le quota est renouvelé uniquement après des instructions réellement exécutées.
Aucun événement n'est sauté ni réponse USB fabriquée. Une régression Thumb
synthétique et une exécution ARM continue de 10 millions d'instructions passent.

63 tests Node CPS, 8 contrôles du parseur C hôte et 8 tests du runner matériel
passent. Les tests hôte restent distincts des preuves ARM/HTTP. Les rapports sont
dans docs/evidence/rx_fm_cps ; le parcours graphique reste à confirmer visuellement.
Voir OPEND578_FIRST_LINK.md et firmware/experiments/rx_fm_alpha/CPS_READONLY.md.
Mémoires/écriture, persistance et portage CTCSS restent les étapes suivantes ;
le succès sur firmware OEM ne les implémente pas dans le firmware neuf.

## CPS 0.9 — lecture globale et CTCSS, 13 novembre

Le bouton Lire tous les canaux actifs lit le bitmap des 4000 emplacements OEM,
puis seulement les records actifs dans les banques espacées. Il ferme la session
avec un unique END et présente un aperçu d'import cumulé. Il ne lit pas les zones,
contacts, réglages généraux ou calibrations. Les groupes manuels restent possibles ;
ils sont cumulés et une relecture remplace les valeurs du même emplacement.
La sélection peut être préparée pendant une session ouverte et survit à END.
L'import reste interdit jusqu'à END acquitté.

CTCSS RX/TX sont désormais indépendants et conservés à l'import, y compris
l'absence explicite de tonalité. Les DCS sont reconnus/affichés mais leur import
est refusé car le document FM ne les représente pas. Les codes inconnus et les
CTCSS personnalisés hors plage conservatrice restent inconnus, jamais supprimés
silencieusement. La largeur et la puissance PC restent des choix de préparation ;
TX est toujours inhibée. Les modes mixtes/DMR ne sont pas convertis vers FM.

Qualification réelle réussie : 224 canaux actifs (numéros 1 à 224, deux banques),
bitmap et 928 réponses R vérifiées, 931 trames soumises dont un seul END, aucune W.
166 CTCSS décodés : 56 RX et 110 TX ; également 1 DCS RX et 2 DCS TX.
Un vérificateur Python indépendant a repris le flux USB observé et la table XML
V1.21 publiée : le SHA256 de tous les champs des 224 canaux concorde exactement
avec le résultat TypeScript. Rapport : qualification/native-global-tones-2026-11-13.json.
La carte complète jusqu'à 4000 est bornée/testée synthétiquement ; seules les deux
banques actives de cette capture ont été exécutées. Il ne s'agit pas d'un essai
sur radio physique ni d'une qualification des CTCSS à la réception RF.

60 tests hôte passent. Builds modulaire et autonome générés ; syntaxe vérifiée.
Les captures source sont inchangées. Contrôle visuel des nouvelles commandes à
confirmer dans le navigateur utilisateur. Sources, adresses et reproduction :
OEM_GLOBAL_READ.md. Les descriptions des versions antérieures ci-dessous sont
historiques, notamment la limite de 128 et l'absence de décodage des tonalités.

## CPS 0.8 — lectures successives dans une session, 13 novembre

Le firmware OEM demande un reset watchdog après END. L'essai de deux sessions
PROGRAM/lecture/END successives sur le même moteur a été arrêté sur
watchdog reset requested (FWDGT, PC 0x08099FD0, automatic_reboot false).
L'ACK de END ne permet donc pas de rouvrir immédiatement une session.

Le CPS conserve désormais PROGRAM ouvert entre les lectures. Le bouton
Terminer la session envoie END une seule fois. Import et fermeture du panneau
sont disponibles après cet ACK ; jusque-là on peut relire un groupe ou en changer.
Annulation, perte de session, compteur USB inattendu ou END invalide imposent
un redémarrage ; aucun renvoi automatique, aucun contournement du watchdog.
Après Terminer, une nouvelle session exige toujours le redémarrage du moteur.

Qualification réelle réussie : pages 0, 0 et 1 sur le même moteur et la même
connexion, un PROGRAM, une identité, 384 R, un END, 387 trames soumises, aucune W.
Les deux lectures de la page 0 ont la même empreinte. Rapport :
qualification/native-repeat-2026-11-13.json. Ce test qualifie les lectures
successives avant END ; il ne qualifie pas le redémarrage automatique après END.
Les deux groupes ont été lus, pas une validation constructeur des champs RF.

55 tests hôte réussis : dont 12 contrôles protocole vérifiant la réutilisation,
la fin unique, les erreurs, l'abandon et les clients concurrents. Builds modulaire
et autonome générés. Le nouveau parcours graphique reste à confirmer par
l'utilisateur. Une session déjà fermée/abandonnée sous l'ancienne version doit
être redémarrée une dernière fois avant d'utiliser les lectures successives.

## Correctif navigateur du 13 novembre : contexte de fetch

Le serveur du banc répondait mais le CPS affichait une API inaccessible. Le
transport conservait fetch sans liaison puis l'appelait comme méthode de
BenchHttpApi, fournissant le mauvais receveur à la fonction du navigateur.
La fonction par défaut est maintenant liée à globalThis ; les transports
injectés gardent leur comportement. Un test reproduit le contrôle du receveur
exigé par le navigateur. La copie servie sous /cps/ est reconstruite et mise à
jour sans redémarrer le firmware. La confirmation du parcours dans le navigateur
utilisateur reste attendue ; les essais Node antérieurs ne prouvaient pas ce point.

## CPS 0.7 — comparaison de décodage et préparation d'import

Une nouvelle exécution réelle sur le banc natif a comparé le décodeur TypeScript
au décodeur existant bench/web/mini_cps_protocol.js sur les réponses USB observées.
32 emplacements × cinq champs (nom, RX, TX, mode et puissance en bits OEM),
aucun écart ; aucun cas conservateur supplémentaire sur cette page.
Rapport : qualification/native-decoder-2026-11-12.json. Cette concordance avec
l'implémentation du banc n'est pas une validation indépendante des spécifications
constructeur, des canaux actifs ou de la puissance RF réelle.

Depuis le panneau Banc émulé, après une lecture terminée, l'utilisateur peut
sélectionner les emplacements FM interprétables et les ajouter au document.
Nom et RX/TX sont copiés ; les modes numériques/mixtes et valeurs inconnues sont
refusés. Largeur et puissance PC sont des choix explicites de préparation,
CTCSS préparés sans tonalité, émission toujours interdite. La puissance OEM
n'est pas convertie en identifiant de puissance firmware. Aucun transfert radio.
Ajout atomique avec identifiants neufs, une annulation, zones/scans/VFO conservés.
Une nouvelle lecture efface l'ancien résultat pour éviter une confusion de session.

50 tests Node passent ; builds modulaire et autonome générés, syntaxe du bundle
vérifiée. Le navigateur automatisé n'a pas démarré : contrôle visuel du nouveau
formulaire encore à faire, sans revendiquer une validation graphique. Les cinq
empreintes source restent inchangées. Voir OEM_IMPORT.md pour le parcours.

## Qualification réelle OEM/CPS réussie — 12 novembre 2026

Le parcours réel Flash + NAND + SCT, serveur Python HTTP et client TypeScript
CPS a réussi en lecture seule avec le moteur natif interactif du banc.
Le démarrage a atteint application_running à 52 270 001 instructions,
132 707 pixels et 8,445 secondes simulées. Le moteur publié est bien native.
PROGRAM a reçu QX/ACK, l'identité D578UV a été vérifiée, 128 réponses R de
16 octets ont passé les contrôles d'adresse et de checksum : 2 048 octets,
soit 32 emplacements de la première page. END a reçu ACK.
Le transport compte 131 trames soumises, aucune W ; les cinq empreintes source
ont été recontrôlées et restent identiques. Aucun poste physique utilisé.

Les accélérateurs native_gate.c et lcd_bridge.c sont inchangés. Compilation
portable Windows par Clang/LLD de Zig 0.15.2 ; sept tests des DLL réellement
chargées passent (interruptions, affichage et entrées NAND). Le script de
construction Windows évite les problèmes de cache du pilote Zig/MinGW.
Les 45 tests CPS et les quatre tests Python précédents restent leurs résultats
hôte séparés : ils ne constituent pas à eux seuls cette qualification réelle.

Rapport public sans données de canaux :
`qualification/native-readonly-2026-11-12.json`. Reproduction :
`NATIVE_WINDOWS_QUALIFICATION.md`. Captures, DLL et résultats bruts restent locaux.

Portée : première page OEM uniquement, identification, transport de lecture et
END. Le décodage complet des noms/fréquences, les autres pages, l'import automatique,
la reprise fonctionnelle après END, le navigateur graphique et le poste physique
restent à qualifier. Ne pas assimiler ce résultat au CPS du nouveau firmware
OpenD578 ni à une qualification de la partie DMR. Prochaine étape : comparer
les champs décodés à une référence du CPS du banc avant de proposer leur import.

## Historique : essais Python antérieurs au succès natif

Le serveur Python et son API HTTP ont été exécutés avec les captures authentifiées
et le SCT complet. Le client CPS attend le signal `application_running` avant
PROGRAM : cette condition n'a pas été atteinte et aucune trame CPS n'a été envoyée.

Un essai de 90 secondes avec les options Python habituelles a atteint environ
14 millions d'instructions et 43 584 pixels. Un essai exploratoire de 300 secondes,
avec le mode interactif et l'accélération d'horloge déjà proposés par le banc,
a atteint 48 240 000 instructions, 100 984 pixels et 8,38 secondes simulées.
Le firmware dessine et progresse ; le résultat est une expiration de budget,
pas la preuve d'un blocage définitif. `application_running` reste faux.
L'activation exploratoire du mode interactif pour Python dans le serveur a été
retirée : aucune modification du modèle matériel n'est livrée.

Le script `tools/qualify_cps_python.mjs` rend l'essai reproductible avec le serveur
non modifié, une attente bornée et un rapport sans données de canaux. Il utilise
le véritable client CPS et l'API du banc ; il ne crée aucune réponse OEM.
Les cinq empreintes source sont inchangées. Les 45 tests Node du CPS et les deux
tests Python des ressources statiques passent, ainsi que les deux tests d'archive.
La lecture USB, l'identification et END sur firmware réel restent à qualifier.
Prochaine action technique : qualifier le démarrage sur le moteur natif prévu
par le banc, ou prévoir un essai Python plus long avec un budget explicite.

## Reprise de qualification — état vérifié le 12 novembre

Lors de la reprise initiale, la qualification USB/CPS était en attente ; les captures sont
désormais disponibles et authentifiées. Le bon chemin est
`browser-bench/samples/F4EGM.zip` (majuscules), sur Telectroboy/OpenD578, commit
`391490e21ebedd0edf295d4ed4ccd63ab8f16054`. Le précédent 404 venait de la casse.
L'archive de passation ancienne est dépassée selon F4EGM.

Le ZIP a été récupéré, son blob Git vérifié et les quatre fichiers contrôlés par
taille et SHA256 : Flash 3 Mio, NAND 256 Mio, OOB 8 Mio, ECC 128 Kio. L'application
V1.21 extraite de la Flash correspond aussi à l'empreinte du dépôt. Copies de
travail locales dans `capture-inputs/`, laissées intactes pendant les essais.

Sur le PC de Maxime, le lancement a aussi échoué : Python 3.15, dépendance
`numpy==2.3.5` téléchargée sous forme source, compilation impossible faute de
compilateur. **F4EGM confirme utiliser Python 3.13.5.** Un Python 3.13.5 portable
isolé a maintenant été préparé dans `runtime/python3135/`, sans modifier les
Python système. Toutes les dépendances épinglées du banc y sont installées et
importables, dont NumPy 2.3.5 (wheel binaire, sans compilation).
L'indication générale « Python 3.11 ou plus récent » ne garantit pas que toutes
les dépendances épinglées disposent d'un paquet binaire pour l'interpréteur choisi.

**Travail repris à la demande de l'utilisateur avec les captures.** Une copie
complète de `feature/cps-core` est disponible dans `integration/`.
Les obstacles observés sont maintenant précis :

- **Prérequis SCT résolu** : `SCT3258TD_UpdateFlash_V2_01_07BF.hex` est fourni
  séparément dans `browser-bench/samples/` du dépôt amont, commit
  `8c7f2b5ff4df83fa9bef7a64fc5a597d61ace57f`. Téléchargé et authentifié par le
  banc (603 102 octets, SHA256 d5ada473af891b6c707978f0b9dde81324afcc4af27348d3bcdf70615ab19407).
  Tous les contrôles d'entrées du parcours OEM Python passent désormais. Ce fichier
  est une référence du modèle de composant ; aucun développement DMR n'est entrepris.
- Le parcours OEM `run_lcd.py`, moteur Python 3.13.5, a maintenant exécuté
  200 000 instructions et atteint son budget prévu (PC 0x0808ADFA), avec sept
  buffers NAND. Aucun pixel ni lecture CPS complète à ce stade : poursuivre la
  qualification du démarrage, puis USB. Ne plus demander ce fichier à F4EGM.
- Un essai réel par `run_hardware.py`, moteur Python, a exécuté 69 119 instructions
  puis s'est arrêté sur `RF SPI has multiple active chip selects`, PC 0x0800870C,
  écriture GPIOB 0x40010C00. Ne pas masquer cette limite par une réponse inventée.
- Le chemin WebAssembly a été initialisé mais l'essai a été interrompu sans
  lecture CPS complète ; ne pas le présenter comme une qualification réussie.

Voir `F4EGM_CAPTURE_CHECK.md` pour les empreintes, le protocole d'essai et les
limites. On peut continuer le CPS hors ligne indépendamment de ces points.

## Ce qui existe

- Éditeur TypeScript local et fichier HTML autonome ; JSON/CSV, canaux, zones,
  VFO, sélection multiple, historique, sauvegarde de session.
- Adaptateur OEM en lecture seule pour le banc Python, servi sous `/cps/` ;
  identification et groupes de 32 emplacements. Tests hôte réussis, qualification réelle de la première page
  obtenue avec les images privées, voir le résultat en tête de ce document. Aucun W ou accès mémoire direct.
- Le firmware autonome RX FM alpha du dépôt ne possède pas encore de CPS.

## Dernière livraison hors ligne — CPS 0.6

- Listes de scan : membres ordonnés et priorité optionnelle, édition et validation.
- Format PC v2 avec conversion explicite des fichiers v1, sans modifier l'original.
- Puissance en liste déroulante avec niveaux personnalisés conservés ; décalage
  relais et TX indépendante ; création en série avec aperçu ; bilan avant export.
- Import CSV externe avec association des colonnes, unités explicites, aperçu
  paginé, erreurs, doublons, sélection des lignes et zone de destination.
  Identifiants neufs ; ajout atomique annulable. Import natif OpenD578 conservé.
- Contrat de données destiné au firmware neuf : proposition à relire avec F4EGM,
  et non une déclaration de fonctionnalités déjà disponibles sur le poste.

45 tests Node réussis ; build modulaire et HTML autonome générés, syntaxe du
bundle vérifiée. Les nouveaux parcours graphiques restent à vérifier dans un
navigateur ; les calculs et règles sont testés. La première lecture OEM est qualifiée ; les limites restantes sont détaillées en tête.

Prochaines pistes : paramètres généraux à convenir avec F4EGM, essais graphiques
sur des exports CSV réels, puis comparaison des champs OEM et élargissement
de la qualification de lecture. Aucun deuxième faux poste n'est à développer : réutiliser le banc.
