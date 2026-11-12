# État du travail CPS — 12 novembre 2026

## Reprise de qualification — état vérifié le 12 novembre

La qualification complète USB/CPS reste **en attente**, mais les captures sont
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
  identification et groupes de 32 emplacements. Tests hôte réussis, pas de
  qualification réelle avec les images privées. Aucun W ou accès mémoire direct.
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
navigateur ; les calculs et règles sont testés. Le blocage OEM reste inchangé.

Prochaines pistes : paramètres généraux à convenir avec F4EGM, essais graphiques
sur des exports CSV réels, puis qualification de l'intégration quand elle
sera débloquée. Aucun deuxième faux poste n'est à développer : réutiliser le banc.
