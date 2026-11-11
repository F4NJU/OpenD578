# État du travail CPS — 11 novembre 2026

## Blocage à conserver lors des prochaines sessions

La qualification du raccordement au firmware OEM exécuté est **en attente**.
Il manque les captures privées de F4EGM : Flash, NAND avec OOB/relevés ECC et
fichiers OEM/SCT requis par le banc. Elles ne sont pas dans le dépôt public.

Sur le PC de Maxime, le lancement a aussi échoué : Python 3.15, dépendance
`numpy==2.3.5` téléchargée sous forme source, compilation impossible faute de
compilateur. La version Python réellement utilisée par F4EGM reste à confirmer.
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

## Dernière livraison hors ligne — CPS 0.5

- Listes de scan : membres ordonnés et priorité optionnelle, édition et validation.
- Format PC v2 avec conversion explicite des fichiers v1, sans modifier l'original.
- Puissance en liste déroulante avec niveaux personnalisés conservés ; décalage
  relais et TX indépendante ; création en série avec aperçu ; bilan avant export.
- Contrat de données destiné au firmware neuf : proposition à relire avec F4EGM,
  et non une déclaration de fonctionnalités déjà disponibles sur le poste.

36 tests Node réussis ; build modulaire et HTML autonome générés, syntaxe du
bundle vérifiée. Les nouveaux parcours graphiques restent à vérifier dans un
navigateur ; les calculs et règles sont testés. Le blocage OEM reste inchangé.

Prochaines pistes : paramètres généraux à convenir avec F4EGM, imports externes
avec correspondance de colonnes, puis qualification de l'intégration quand elle
sera débloquée. Aucun deuxième faux poste n'est à développer : réutiliser le banc.
