# Changelog OpenD578 V11.7

Date de publication : **5 novembre 2026**
Version précédente : **V11.6**
Commit de la release : `9124d7e`
Cible étudiée : **AnyTone AT-D578UV PRO, GD32, application constructeur V1.21**.

Cette release ajoute le décodage du voyant de statut, un inventaire des fonctions
à qualifier et des rapports d’auto-test ouverts. Le voyant suit les commandes
GPIO réellement émises par le firmware. L’inventaire et les rapports distinguent
les fonctions documentées, les modèles partiels et les essais exécutés.

Il s’agit d’une release du **banc de simulation et de ses outils**. Elle ne fournit
pas encore un firmware OpenD578 installable sur le poste.

## Ajouté

### Décodage du voyant rouge/vert du poste

- Nouveau modèle `bench/status_led.py`.
- Lecture du bus série : **PE3 = données**, **PE4 = horloge**.
- Échantillonnage des données sur les fronts montants de l’horloge.
- Assemblage de mots de **8 bits, bit de poids faible en premier**.
- Décodage du vert depuis le masque `0x08`, et du rouge depuis `0x10`.
- Affichage du voyant dans le banc à partir de la commande décodée.
- Exposition de l’octet brut, des bits encore incomplets et d’un historique borné.
- Réutilisation du décodeur dans le mode matériel, sans dépendance à une adresse
  de routine ou à une variable RAM de l’OEM.

Avant la réception d’un mot complet, le voyant reste **inconnu**. La reprise
rapide depuis l’ancienne capture RAM ne fabrique pas une commande qui n’a pas
été enregistrée. Les autres bits du mot de commande restent sans fonction
lumineuse attribuée.

### Inventaire ouvert des fonctions et exigences

Le catalogue contient **117 entrées**, réparties ainsi :

| Domaine | Entrées | Périmètre suivi |
| --- | ---: | --- |
| IHM | 22 | Façade, encodeur, microphone, voyants, écran, verrouillages et démarrage |
| FM et signalisation analogique | 35 | Accord, relais, squelch, tonalités, signalisations, balayage et fonctions optionnelles |
| Audio | 11 | Microphone, volumes, haut-parleurs, prises externes et codec |
| Sécurités et mesures | 13 | Durée TX, canal occupé, température, ventilation, alimentation et défauts |
| USB et mémoires | 5 | Lecture, écriture, édition, alignements et récupération |
| GPS | 7 | Présence, acquisition, coordonnées, heure et robustesse du dialogue |
| APRS | 11 | Configuration, déclenchement, position, modulation, arbitrage et réception ultérieure |
| Satellite | 5 | Orbites, Doppler, canaux, émission et IHM |
| Bluetooth | 8 | Identification, appairage, reconnexion, PTT, audio et firmware du module |
| **Total** | **117** | **Inventaire ouvert, sans garantie d’exhaustivité** |

Ces entrées ne correspondent pas à 117 fonctions OEM confirmées sur cette
variante. Elles comprennent des fonctions documentées pour la famille D578,
des fonctions conditionnelles, des exigences de test et les extensions du projet.
Le satellite est identifié comme une extension OpenD578. La réception APRS reste
une étape ultérieure.

Chaque entrée possède un identifiant, des sources et leur niveau de preuve, un
état du modèle, un critère d’acceptation et les blocages connus. Le catalogue
livré classe **17 modèles comme partiels et 100 comme non implémentés** ; ces
états ne sont pas des verdicts de conformité du firmware.

Formats fournis :

- `bench/qualification_data/catalog.json` : catalogue de référence.
- `bench/qualification_data/catalog.schema.json` : schéma JSON Schema 2020-12.
- `docs/FUNCTION_MATRIX.csv` : vue tabulaire du catalogue.

Les fonctions OEM précédemment jugées supprimables restent recensées, afin de
conserver la connaissance de leur existence. Leur présence dans l’inventaire
ne les rend pas obligatoires pour la première version du firmware ouvert.

### Onglet Qualification

- Nouvelle vue du catalogue dans le navigateur.
- Recherche par identifiant, intitulé ou critère d’acceptation.
- Affichage des modèles partiels et des éléments manquants.
- Téléchargement du catalogue depuis `/api/qualification/catalog`.
- Indication explicite du caractère incomplet de la qualification matérielle.

Cet onglet présente les exigences et leur couverture. Son ouverture ne lance
pas une campagne de tests.

### Exploration reproductible du firmware

Le nouvel outil `bench/oem_discovery.py` relève :

- l’empreinte et l’adresse de chargement de l’image ;
- des candidats d’entrées de code ;
- des constantes candidates de périphériques ;
- des textes candidats associés aux mots-clés du catalogue ;
- des pointeurs alignés possibles vers ces textes ;
- les limites de l’analyse et les catégories encore non résolues.

Sur l’application PRO GD32 V1.21 étudiée, l’analyse relève **3 042 candidats
d’entrées** et des textes candidats associés à **110 entrées du catalogue**.
Ces nombres ne constituent ni un décompte fiable des fonctions, ni un taux de
couverture fonctionnelle. Les motifs peuvent aussi rencontrer des données,
des ressources partagées et des références sans lien avec la fonction cherchée.

Le rapport public `docs/firmware_discovery_v121.json` conserve les adresses et
remplace les textes candidats par leurs empreintes et leurs longueurs. L’image
constructeur n’est pas incluse dans les sources publiables.

### Auto-test et rapports JSON/JUnit

- Nouveaux lanceurs `TESTER_BASES.cmd` et `TESTER_BASES.sh`.
- Nouveau gestionnaire `bench/run_base_tests.py`.
- Nouveau générateur de couverture `bench/selftest_report.py`.
- Ajout de `--case` à `bench/run_bench.py` pour choisir un scénario.
- Nouveau scénario `bench/scenarios/LED_RX_TX.json`.
- Nouveau critère de verdict `bench/indicator_qualification.py` pour les voyants.
- Rapports `qualification.json`, `selftest.json` et `junit.xml`.
- Sous-dossier distinct pour chaque campagne lancée par `TESTER_BASES`.

Les exigences non qualifiées restent `incomplete` dans le JSON et `skipped`
dans le JUnit. Un essai absent ou un périphérique non modélisé ne devient pas
un succès. Un échec constaté reste un échec dans les rapports.

Le critère `LED_bus` compare les stimuli externes et les réponses du bus GPIO.
Il n’utilise aucune variable OEM de réception ou d’émission. Il peut aussi
examiner une trace compatible produite par le mode matériel. Les trois critères
historiques FM/GPS/PTT utilisent encore des observations spécifiques à V1.21.

### Observations matérielles explicites

Le nouveau module `bench/board_observations.py` expose les sorties observées :

- registres bruts GPIO et éclairage ;
- commande du voyant de statut ;
- trames radio vers microphone ;
- état connu ou inconnu des indicateurs du microphone ;
- état non qualifié des routes audio ;
- périmètre réel du modèle Bluetooth.

Les sorties audio non qualifiées restent à `selected: null`. L’état logiciel
TX de l’OEM ne suffit pas à déclarer une LED allumée ou un haut-parleur actif.

## Modifié et corrigé

- Le voyant de statut, auparavant neutre faute de décodeur, suit maintenant
  la liaison PE3/PE4.
- La restauration d’une session conserve la séparation des composants du
  simulateur ; le nouveau décodeur n’invente pas son historique absent d’une
  ancienne capture.
- La page présente les trames sortantes du microphone sans attribuer de sens
  non vérifié à leurs champs.
- La ligne USB du tableau matériel indique la présence de l’hôte simulé et
  l’état CDC observé, au lieu d’afficher systématiquement un hôte absent.
- Le message de fermeture renvoie au lanceur V11.7.
- Les empreintes de version prennent en compte les nouveaux composants et
  ressources concernés, pour éviter la réutilisation d’un serveur périmé.
- Les README décrivent la qualification V11.7 et séparent les essais bornés
  de la validation matérielle complète.

## Nouvelles informations apprises

### Commandes du voyant et recoupement bootloader/application

Le bootloader du dump complet contient une routine à **`0x080042BA`** qui
transmet huit bits sur PE3/PE4. La boucle de mise à jour l’appelle alternativement
avec **`0x00` et `0x10`**. Ce comportement est cohérent avec le clignotement rouge
observé sur le poste en mode de mise à jour.

Dans l’application V1.21, le chemin correspondant se trouve autour de
**`0x0808A400`**. Les retours d’appels GPIO relevés comprennent
`0x0808A416`, `0x0808A424`, `0x0808A42E`, `0x0808A43C` et `0x0808A454`.
Ces adresses servent à documenter l’analyse ; le nouveau décodeur n’en dépend pas.

L’exécution du scénario donne :

| Situation du scénario | Commande | Bit vert `0x08` | Bit rouge `0x10` |
| --- | --- | ---: | ---: |
| Réception avec squelch ouvert | `0x4E` | 1 | 0 |
| Repos après retrait de la porteuse | `0x46` | 0 | 0 |
| Émission après PTT | `0x56` | 0 | 1 |
| Repos après relâchement | `0x46` | 0 | 0 |

**Niveau de preuve :** les commandes et les fronts GPIO ont été observés dans
le firmware exécuté. La correspondance des couleurs est déduite de ces traces,
du bootloader et des observations utilisateur. La continuité électrique et la
référence du circuit pilote n’ont pas été mesurées.

Le scénario ne détermine pas le comportement du voyant avec un CTCSS incorrect,
pendant tous les modes de balayage ou pour les autres couleurs éventuelles.
Le squelch porteuse et la porte audio n’évoluent pas exactement au même instant.

### Dialogue radio vers microphone

Des trames sortantes de **16 octets**, commençant par **`0x53`** et se terminant
par **`0x06`**, ont été enregistrées sur USART0. Leur structure est désormais
exposée dans le banc. La signification des champs concernant les LED et le
routage audio reste à déterminer.

Le modèle OEM emploie aussi une activité microphone synthétique, avec un
`0x06` périodique. Cela ne démontre pas que le microcontrôleur du microphone
est émulé ou qu’il a exécuté les commandes reçues.

### Haut-parleur du microphone et routes audio

Le haut-parleur sélectionnable du microphone est ajouté au périmètre. Il faut
qualifier séparément :

- le haut-parleur interne du poste ;
- celui du microphone, avec sélection de la voie A ou B ;
- les sorties externes A et B ;
- les chemins audio Bluetooth.

Les choix microphone/poste/les deux et les effets des contacts des prises
externes doivent être vérifiés. La boucle audio du navigateur ne suffit pas
à prouver le routage du matériel simulé.

### Texte présent dans le firmware et capacité réelle

L’image PRO V1.21 contient le texte **`APRS Receive`**. Cette présence ne prouve
pas que le poste capturé sait recevoir l’APRS. Une ressource peut être partagée
entre variantes ou appartenir à une branche désactivée. Le nouvel outil maintient
ces occurrences au niveau de pistes, sans en déduire une fonction opérationnelle.

### Bluetooth

L’option Bluetooth fait partie du catalogue. Une référence **ET12/B707** est
connue dans les travaux du projet et le modèle existant couvre quelques
commandes AT de version et d’AGHF.

La disponibilité d’un firmware ne suffit pas à permettre son exécution :
processeur, jeu d’instructions, mémoire et interfaces doivent être établis.
Le module n’exécute pas encore son firmware dans le simulateur. L’appairage,
la reconnexion, le PTT et les échantillons audio Bluetooth restent à modéliser.

### Anciennes informations de brochage et photographies

La table des 100 broches a été relue. Certaines mentions anciennes
`NON CONNECTE` étaient des emplacements non renseignés ; elles ne démontrent
pas une absence de connexion. Les hypothèses issues d’autres cartes restent
à distinguer des connexions mesurées sur le D578 étudié.

Les liens FCC ont été conservés, mais les photographies n’ont pas été
réinspectées dans cette release après l’échec de leur récupération. Les entrées
FCC de schémas visibles uniquement comme métadonnées ne sont pas considérées
comme des schémas effectivement obtenus.

## Validation de la release

### Tests logiciels

- **216 tests Python réussis**, contre 203 dans V11.6.
- **13 tests ajoutés** pour le catalogue, les rapports, les observations
  matérielles, le décodeur du voyant et son critère de verdict.
- Contrôles Node du CPS intégré conservés et réussis.
- Vérification de syntaxe JavaScript des ressources modifiées.
- Contrôle de publication : **187 fichiers suivis, aucune violation détectée**
  par le vérificateur du projet. Ce contrôle vise les fichiers binaires/captures
  exclus et les motifs de secrets ; il ne constitue pas un audit juridique.

### Scénarios exécutés contre l’OEM V1.21

Les quatre scénarios partent de la reprise OEM authentifiée :

| Scénario | Vérification bornée | Instructions supplémentaires | Verdict |
| --- | --- | ---: | --- |
| `FM` | Porteuse appliquée, porte audio ouverte, porteuse retirée, porte audio fermée | 9 000 000 | Réussi |
| `GPS` | Position acquise puis perdue après changement des stimuli | 13 000 000 | Réussi |
| `PTT` | Activation TX, ventilateur et DAC, puis retour au repos après relâchement | 4 000 000 | Réussi |
| `LED_bus` | Vert, repos, rouge, repos depuis les commandes GPIO | 13 000 000 | Réussi |

Ces nombres décrivent l’exécution de l’émulateur. Ils ne mesurent pas des cycles
matériels ni une durée réelle équivalente. Ces essais n’ont pas rejoué un
amorçage à froid complet pour chaque scénario.

### Rapport global de couverture

Le JUnit livré contient **121 cas** : quatre essais bornés réussis et
117 exigences complètes marquées `skipped`. Il ne comporte aucun échec observé
sur ces quatre essais. Le verdict global de qualification reste **incomplet**.

### Contrôle USB du paquet livré

Le test du paquet V11.7 a vérifié :

- le démarrage du serveur sur un port disponible et sa détection automatique ;
- l’accès au catalogue et aux nouvelles ressources JavaScript ;
- l’énumération USB CDC ;
- l’identification D578UV depuis le firmware exécuté ;
- une lecture de 16 octets à l’adresse logique `0x02FA0000` ;
- le transport des états par canal processus/mémoire, sans fichier USB de suivi actif.

Empreinte SHA-256 des données relues :

```text
8208b74207d2956a56751cd8a70ec35a99bc43b1c84fbf9607b970c09a969957
```

Ce contrôle a été exécuté avec le client de test, sans lancer le CPS constructeur.
La lecture complète du CPS Windows avait été confirmée par l’utilisateur avant
cette release. L’interface graphique navigateur et les lanceurs Windows n’ont
pas été exécutés automatiquement pendant cette qualification.

## Fonctions conservées des versions précédentes

- CPS intégré partiel V11.6 : lecture des 128 premiers emplacements,
  modification des noms existants et export JSON.
- Pont local USB CDC vers COM/PTY pour CPS externe.
- Persistance optionnelle de la NAND virtuelle après arrêt normal.
- Boucle numérique FM/APRS autonome avec fichiers I/Q.

Ces fonctions ne sont pas présentées comme des nouveautés V11.7. L’écriture et
la récupération d’un nom de canal après redémarrage complet avaient été validées
pour V11.6 ; la V11.7 n’étend pas l’édition CPS aux autres champs.

## Limites connues

| Domaine | État après V11.7 |
| --- | --- |
| Chaîne FM complète | Le couplage firmware, codec, SCT, échantillons et RF/IQ reste incomplet |
| Audio navigateur | Le son de test et la boucle I/Q autonome ne valident pas le routage matériel |
| LED microphone | Champs de commande non décodés ; états lumineux inconnus |
| Voyant poste | Rouge/vert décodés par corrélation ; circuit physique, autres bits et transitoires non qualifiés |
| Haut-parleurs | Toutes les routes et leurs gains restent à qualifier |
| CTCSS/DCS | Pas de qualification complète de la chaîne de génération/détection pilotée par le firmware |
| GPS | Scénario OEM borné réussi ; critère matériel générique et robustesse complète encore manquants |
| APRS TX OEM | DMA et chemin de modulation du firmware à terminer |
| APRS RX | Étape ultérieure, disponibilité conditionnelle selon variante et matériel |
| Satellite | Intégration firmware et qualification non terminées |
| Bluetooth | Sous-ensemble AT ; firmware interne, appairage, PTT et audio non exécutés |
| Température | Échelle physique et protections complètes à établir |
| Réinitialisation | Certaines demandes sont détectées sans redémarrage automatique complet |
| Couverture firmware | Inventaire statique non exhaustif ; appels indirects et composants opaques non résolus |
| Matériel réel | Puissance, sensibilité, déviation, courants et comportement thermique non certifiés par ces essais |
| DMR | Hors de cette campagne de qualification |

## Utilisation et compatibilité

Extraire la V11.7 dans un nouveau dossier puis lancer
`OUVRIR_BANC_WEB_V11_7.cmd` sous Windows, ou le lanceur correspondant au système.

Le voyant peut rester inconnu après une reprise rapide jusqu’à l’émission de
sa première commande complète. Les autres nouvelles observations apparaissent
dans l’IHM et dans les données du moteur.

Pour les essais de base, arrêter le moteur web puis lancer :

```bat
TESTER_BASES.cmd --source-dir "C:\D578\captures"
```

Dans les sources du dépôt :

```sh
python bench/run_bench.py --source-dir /chemin/captures --engine native
python bench/run_bench.py --source-dir /chemin/captures --engine native --case LED_bus
python bench/selftest_report.py --regressions bench/results/bench/qualification.json
```

`run_bench.py` conserve son code de sortie pour les scénarios sélectionnés.
`selftest_report.py` renvoie **2 pour une qualification incomplète** et **1 en
cas d’échec**. Un code 2 ne signifie donc pas que le poste est en panne.
Le lanceur `TESTER_BASES` place chaque campagne dans un sous-dossier de
`results/bench` et termine sur le verdict de couverture.

Pour un firmware entièrement différent, utiliser le mode matériel
`run_hardware.py`. Le décodeur du voyant y est réutilisable ; les autres critères
spécifiques aux adresses et structures V1.21 doivent être remplacés par des
observations matérielles indépendantes. Aucun verdict global automatique pour
un firmware arbitraire n’est annoncé dans cette release.

## Formats ouverts et publication

- Sources du projet en Python et C, sous GPL-3.0-or-later.
- Catalogue JSON avec schéma JSON Schema 2020-12.
- Matrice CSV.
- Résultats JSON et JUnit XML.
- Audio WAV PCM16 et I/Q SigMF cf32_le déjà utilisés par le banc.
- TLE ou OMM prévus comme formats d’entrée pour les travaux satellite.

**Paquet complet privé :** `OpenD578_Banc_V11_7.zip`. Il contient des références
OEM nécessaires au banc privé et ne doit pas être publié intégralement comme
source OpenD578.

**Sources destinées à GitHub :**
`SOURCES_PUBLIQUES/OpenD578_source_V11_7.zip`, inclus dans le paquet complet.
Les firmwares constructeur et les captures privées restent séparés.

Empreinte SHA-256 du paquet complet publié :

```text
0ef2e25b902650f9ff5748eae8c975bf4167254caaf2eb7215f971eee5941794
```

Ce changelog documente la release après sa publication. Son ajout au dépôt ne
modifie pas rétroactivement le ZIP V11.7 identifié par cette empreinte.

## Fichiers de référence de la release

| Fichiers | Contenu |
| --- | --- |
| `bench/status_led.py`, `bench/indicator_qualification.py` | Décodage et critère du voyant |
| `bench/board_observations.py` | Sorties observées et inconnues explicites |
| `bench/oem_discovery.py` | Recherche statique reproductible |
| `bench/qualification_data/catalog.json`, `catalog.schema.json` | Inventaire de référence et schéma |
| `bench/run_base_tests.py`, `bench/selftest_report.py` | Campagnes et rapports de couverture |
| `bench/scenarios/LED_RX_TX.json` | Stimuli du nouveau scénario |
| `bench/TESTER_BASES.cmd`, `bench/TESTER_BASES.sh` | Lanceurs |
| `bench/web/qualification.js` | Nouvelle vue navigateur |
| `docs/FUNCTION_MATRIX.csv` | Matrice lisible dans un tableur |
| `docs/LED_STATUS_BUS.md` | Preuves et limites de la découverte LED |
| `docs/QUALIFICATION_ANALOGIQUE.md` | Méthode et périmètre convenus |
| `docs/firmware_discovery_v121.json` | Résultats statiques publiables |
| `docs/validation_v11_7.json` | Mesures et portée des essais |
| `docs/selftest_v11_7.json`, `docs/selftest_v11_7.junit.xml` | Couverture globale incomplète |

## Sources techniques recoupées

- Manuel fabricant A3.200730 :
  <https://www.csi-radios.com/content/support/AnyTone/AT-D578UV/User%20manual.pdf>.
- Manuel GD32F30x :
  <https://www.gd32mcu.com/data/documents/userManual/GD32F30x_User_Manual_Rev2.9.pdf>.
- Datasheet TLV320AIC3204 :
  <https://www.ti.com/lit/ds/symlink/tlv320aic3204.pdf>.
- Datasheet SCT3258 :
  <https://cdn.hackaday.io/files/1642237026116832/SCT3258_datasheet_v2_0.pdf>.
- Protocole microphone capturé :
  <https://github.com/jrobertfisher/AT-D578UV-software-mic/wiki>.
- Référence historique des photos internes FCC :
  <https://fccid.io/T4K-D578UV/Internal-Photos/Internal-Photos-4513250>.
- Dépôt du projet : <https://github.com/Telectroboy/OpenD578>.

Image applicative analysée, chargée à `0x08006000` :

```text
SHA-256 : 02b2a3b56bd57c7ada581eb52b9b6f41c5d51aaec1b068d37585efd58dff9c9a
```

## Suite du travail convenue

1. Poursuivre l’inventaire et l’identification matérielle, notamment les LED et
   commandes du microphone.
2. Fermer la chaîne FM/audio, avec des générateurs et récepteurs de mesure
   indépendants des résultats attendus du firmware.
3. Relier les branches du firmware aux exigences et vérifier les fonctions
   encore absentes de l’inventaire ou des scénarios.
4. Qualifier le GPS et ses défauts sans forcer les variables RAM du firmware.
5. Terminer l’APRS TX OEM puis vérifier les trames décodées depuis l’I/Q.
6. Intégrer et qualifier la fonction satellite.

L’option Bluetooth est suivie avec le routage audio. Le DMR reste de côté pour
cette campagne ; la réception APRS conserve sa place dans une étape ultérieure.
