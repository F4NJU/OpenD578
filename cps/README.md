# CPS OpenD578 — éditeur web hors ligne

Version 0.6 : édition des canaux analogiques et du VFO, zones et listes de scan ordonnées,
recherche, sélection multiple, duplication, modifications groupées, suppression,
annulation/rétablissement et restauration de la dernière session dans le navigateur.
L'adaptateur OEM lit le banc Python existant ; sa qualification avec le firmware
exécuté reste à faire. Aucune connexion physique ni écriture radio n'est fournie.

## Connexion au banc émulé

**Qualification OEM en attente** : captures privées absentes et blocage local
Python 3.15 / NumPy 2.3.5. Le développement hors ligne continue. Voir
[PROJECT_STATUS.md](../docs/cps/PROJECT_STATUS.md) pour la reprise du projet.

Compiler avec `npm run build`, lancer le banc Python depuis cette branche, puis
ouvrir son adresse exacte suivie de `/cps/` (exemple :
http://127.0.0.1:8765/cps/). Cliquer **Banc émulé**, choisir un groupe de 32
emplacements et **Identifier et lire**. Démarrer préalablement le firmware OEM
et fermer son CPS intégré et les autres ponts USB. Redémarrer le moteur après
chaque lecture/END ou interruption. Le fichier autonome peut ouvrir cette page ;
il ne contourne pas les contrôles d'origine du banc.

Les résultats sont une inspection séparée : noms, RX/TX, modes et puissances
partiellement décodés ; activité des emplacements et autres paramètres inconnus.
Aucune importation automatique dans le document éditable, aucune commande W.
La version GitHub Pages et le firmware RX FM alpha ne sont pas raccordés ici.

Guide et limites : [CPS_WEB_READONLY_BENCH.md](../docs/cps/CPS_WEB_READONLY_BENCH.md).

## Lancement local

### Version autonome sans serveur

`npm run build:standalone` produit **`dist/OpenD578-CPS.html`**. Ce fichier unique
contient l'interface, le cœur et l'exemple ; une fois généré, il suffit de le
copier sur un PC et de l'ouvrir par double-clic dans Chrome ou Edge, sans Node.js.
Il ne nécessite aucun port réseau. Le stockage local des fichiers HTML dépend
du navigateur : exporter le JSON pour conserver une sauvegarde fiable.

### Version avec serveur local

Node.js 24 ou ultérieur, aucune dépendance à installer :

```powershell
cd cps
npm start
```

Ouvrir **http://127.0.0.1:8095** dans Chrome ou Edge. Arrêter avec Ctrl+C.
Le serveur écoute uniquement sur l'interface locale. Aucun serveur de traitement,
compte ou ressource CDN n'est nécessaire. Le port est modifiable avec `CPS_PORT`.

`npm run build` produit `dist/`, qui peut être servi par un serveur HTTP statique.
Éviter le double-clic sur `index.html` : les modules nécessitent HTTP.
Le client est composé de modules TypeScript et DOM natifs, sans React/Vite pour
cette première livraison. Le cœur reste réutilisable par une future interface React.
Le répertoire généré `dist/` est ignoré par Git.

## Fonctions de l'éditeur

- **CSV externe avec association des colonnes** : bouton Importer, choisir un CSV
  UTF-8 avec en-tête. L'assistant propose les associations ; les vérifier puis
  cliquer Prévisualiser. Nom et RX sont obligatoires. RX/TX et décalage ont leurs
  unités explicites (MHz/kHz/Hz). Les séparateurs virgule, point-virgule et tabulation
  sont acceptés, avec choix manuel si l'autodétection ne convient pas.
  L'aperçu affiche 50 lignes par page, les erreurs et doublons présumés. Les lignes
  invalides ne sont pas sélectionnables ; les doublons sont décochés par défaut
  mais peuvent être cochés volontairement. Choisir une zone existante ou la liste
  globale, puis importer. Toute la sélection constitue une seule transaction annulable.
  Aucun canal existant n'est modifié et les listes de scan/VFO restent inchangés.

  Les identifiants externes sont ignorés et recréés. Les modes numériques et tons
  DCS sont refusés quand leurs colonnes sont associées. Les champs non associés
  sont ignorés : vérifier notamment la colonne mode si le fichier contient aussi
  du DMR. Sans TX ni décalage, TX = RX. Tons vides = désactivés ; largeur étroite,
  puissance `low` et RX seul sont les défauts modifiables. Les conflits TX/décalage,
  signes contradictoires et NFM/largeur large sont signalés. Les fréquences sont
  converties sans arrondi à l'Hz ; aucune valeur en watts n'est déduite de puissance.

  Le fichier source n'est pas modifié. L'import externe est limité à 10 Mio,
  10 000 enregistrements et 256 colonnes. Les numéros affichés sont des numéros
  d'enregistrement CSV (en-tête = 1), pas des lignes physiques en cas de champ
  multiligne. L'import CSV OpenD578 reconnu conserve son parcours strict existant,
  avec ses identifiants et ses contrôles de collision.

- **Puissance** : liste déroulante `low`, `medium`, `high`, `turbo`, complétée par
  les identifiants personnalisés du document. « Personnalisé… » permet une nouvelle
  valeur. Disponible aussi en modification groupée avec « Conserver ». Ces niveaux
  ne correspondent pas à des watts connus ni à des capacités radio certifiées.
- **Décalage relais** : simplex, positif, négatif ou TX indépendante. RX/TX sont
  calculées en Hz entiers, sans ajout de champ au format JSON v2.
- **Créer une série** : cocher exactement un canal modèle, choisir 1 à 256 copies,
  un pas en MHz et une direction. Le premier nouveau canal est un pas après le
  modèle ; RX/TX évoluent ensemble, le décalage et les autres paramètres restent
  identiques. Un aperçu affiche les extrémités. Dans une zone, les copies y sont
  ajoutées. Une seule annulation retire toute la série. La borne 256 est une limite
  de cette opération de l'éditeur, pas une capacité annoncée par le poste.
- **Vérifier** : bilan des erreurs structurelles et avertissements (noms ou
  fréquences/tons en double, listes vides). Les doublons peuvent être volontaires.
  Avant export JSON ou CSV, les avertissements demandent une confirmation ; les
  erreurs bloquent l'export. Le bilan ne certifie pas la validité radio d'un fichier.

- **Listes de scan** : créer, renommer, supprimer, choisir et ordonner les membres,
  définir un canal prioritaire appartenant à la liste. La suppression d'un canal
  le retire des zones et listes ; s'il était prioritaire, la priorité est retirée.
  Annuler restaure le tout. Aucune fonction de scan n'est encore exécutée sur radio.
- **Format JSON v2** : les listes de scan sont conservées dans le JSON complet.
  Un import v1 demande confirmation de conversion ; les listes sont initialisées
  vides et tous les champs existants conservés. L'original reste intact. Une session
  locale v1 est restaurée avec un avertissement et doit être réexportée en v2.
  Le CSV ne contient toujours que les canaux. Les anciennes versions du CPS ne
  peuvent pas ouvrir le JSON v2 ; aucune rétroconversion avec perte n'est faite.

- **Canal** : nom, RX/TX, largeur FM, puissance, CTCSS indépendants et interdiction
  TX. Les nouveaux canaux sont en réception seule par défaut.
- **Zones** : créer, renommer, supprimer, choisir les membres et les ordonner
  avec les flèches. Un nouveau canal créé dans une zone lui est ajouté.
- **Sélection** : duplication, suppression ou modification groupée de la largeur,
  de la puissance et de l'interdiction TX.
- **Ordre** : flèches sur le tableau global ou dans une zone ; désactivées pendant
  une recherche pour éviter un ordre partiel ambigu.
- **Annuler / Rétablir** : jusqu'à 50 transactions dans la session ouverte.
  L'historique ne survit pas au rechargement ; le document courant est restauré.
- **VFO** : paramètres facultatifs ; décocher son inclusion conserve `vfo: null`.
- **JSON** : sauvegarde complète des canaux, zones et VFO. Ctrl+S demande un export.
  L'import remplace le document après validation ; annulation possible.
- **CSV** : export de tous les canaux, même masqués par un filtre ; import par ajout
  après validation et confirmation du nombre. Les identifiants déjà présents sont
  refusés sans modification partielle. Les zones et le VFO nécessitent le JSON.

Les téléchargements sont demandés au navigateur : le CPS ne peut pas confirmer
que l'utilisateur a effectivement conservé le fichier. La session locale dépend
du navigateur et de l'adresse (origine) ; elle peut être supprimée ou indisponible.
Un avertissement est alors affiché. Exporter un JSON pour une sauvegarde durable.
Utiliser une seule fenêtre par origine : les sessions simultanées ne sont pas
synchronisées et la dernière sauvegarde locale l'emporte. Import limité à 10 Mio.

## CSV v1

En-tête obligatoire, ordre exact :

```csv
id,name,rx_mhz,tx_mhz,bandwidth,power,rx_ctcss_hz,tx_ctcss_hz,tx_inhibit
```

Virgule ou point-virgule comme séparateur ; guillemets doubles et BOM acceptés.
Fréquences en MHz avec au plus six décimales, point ou virgule décimale (mettre
entre guillemets une virgule décimale dans un fichier séparé par virgules).
CTCSS en Hz avec au plus une décimale, vide pour désactivé. `bandwidth` vaut
`narrow` ou `wide`, `tx_inhibit` vaut `true` ou `false`. `power` est un identifiant
de niveau, pas une puissance calibrée en watts.

À l'export, les champs commençant par `=`, `+`, `-`, `@` ou une apostrophe reçoivent
une apostrophe de protection pour les tableurs. L'import retire cette protection
de manière réversible. Les CSV externes utilisant déjà une apostrophe littérale
devant ces caractères doivent la doubler.

## Vérification

Node.js 24 ou ultérieur, aucune dépendance à installer :

```powershell
cd cps
npm test
npm run build
```

Node exécute ici le TypeScript par suppression des annotations. Cela ne remplace
pas une vérification statique par `tsc`, à ajouter avec l'outillage de l'éditeur.

Les tests couvrent aussi les conversions CSV, les collisions d'import, les
références des canaux supprimés et l'historique. La validation automatisée dans
Edge est bloquée dans l'environnement de développement (accès DevTools).
Le rendu et ces parcours restent à vérifier manuellement :

1. Charger l'exemple, créer un canal puis une zone contenant ce canal.
2. Modifier l'ordre, dupliquer, supprimer et annuler.
3. Vérifier la recherche, les modifications groupées et les réglages VFO.
4. Exporter le JSON, recharger et comparer la session restaurée.
5. Réimporter JSON/CSV ; vérifier qu'un import invalide conserve le document.
6. Vérifier clavier, focus du dialogue, Échap, écran étroit et stockage indisponible.

## Utilisation

```typescript
import { parseCodeplug, serializeCodeplug } from './src/core/json.ts';
import { validateForDevice } from './src/core/capabilities.ts';

const codeplug = parseCodeplug(jsonText);
const savedText = serializeCodeplug(codeplug);
// Avant un futur transfert : capacités validées par l'adaptateur obligatoire.
const issues = validateForDevice(codeplug, deviceCapabilities);
```

`validateCodeplug` accepte une entrée inconnue et retourne des erreurs structurées
`{path, code, message}`. `parseCodeplug` et `serializeCodeplug` lèvent une
`CodeplugValidationError` si nécessaire. Aucune correction ni suppression de
champ n'est automatique. Les imports retournent de nouveaux objets.

Les capacités de test et le fichier d'exemple sont synthétiques. Ils ne sont pas
une description des capacités AT-D578 ou une configuration de relais local.

Contrat partagé : `../docs/cps/OPEND578_CPS_CONTRACT.md`.

## Développement

Le cœur est indépendant du banc et du firmware. Les évolutions sont préparées
sur une branche dédiée du fork avant proposition au dépôt amont.
Le contrat PC est implémenté ; les décisions firmware et protocole restent à
convenir avec F4EGM avant l'intégration à l'émulateur.
