# État du travail CPS — 12 novembre 2026

## Blocage à conserver lors des prochaines sessions

La qualification du raccordement au firmware OEM exécuté est **en attente**.
Le 12 novembre, F4EGM confirme avoir placé quatre fichiers utiles dans
`browser-bench/samples/f4egm.zip` sur GitHub. Il précise que l'ancienne archive
de passation est dépassée : ne plus la présenter comme la fourniture actuelle.
La vérification API du dépôt Telectroboy/OpenD578 (`main`, commit
`391490e21ebedd0edf295d4ed4ccd63ab8f16054`) ne trouve cependant pas ce ZIP :
chemin retournant 404. Obtenir son lien exact ou attendre sa publication avant
de conclure que les captures sont disponibles. Le contenu et sa compatibilité
avec le banc Python doivent encore être vérifiés.

Sur le PC de Maxime, le lancement a aussi échoué : Python 3.15, dépendance
`numpy==2.3.5` téléchargée sous forme source, compilation impossible faute de
compilateur. **F4EGM confirme utiliser Python 3.13.5.** Le PC inspecté ne liste
actuellement que Python 3.14 et 3.15 via `py -0p`. Prévoir un environnement 3.13
distinct ; l'installation des dépendances n'a pas encore été retestée avec lui.
L'indication générale « Python 3.11 ou plus récent » ne garantit pas que toutes
les dépendances épinglées disposent d'un paquet binaire pour l'interpréteur choisi.

**Décision utilisateur : continuer les fonctions hors ligne.** Ne pas présenter
l'absence de captures ou ce problème NumPy comme un blocage de tout le CPS.
Reprendre la qualification OEM lorsque les entrées privées et un environnement
compatible sont disponibles, ou à la demande explicite de l'utilisateur.

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

