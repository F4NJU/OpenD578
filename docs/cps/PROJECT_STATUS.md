# État du travail CPS — 12 novembre 2026

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
