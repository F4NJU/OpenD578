# Qualification analogique OpenD578 — V11.7

Cette révision établit un inventaire ouvert, une recherche reproductible dans le
firmware et un rapport d’auto-test conservateur. Elle ne termine pas la chaîne
FM/APRS du firmware et ne constitue pas un firmware OpenD578 installable.

## Sources et niveaux de preuve

Le catalogue `bench/qualification_data/catalog.json` contient 117 fonctions ou
exigences. La même liste est exportée dans `FUNCTION_MATRIX.csv`. Les sources
sont référencées dans le JSON ; les critères et descriptions sont rédigés pour
ce projet, sans reproduction des documents constructeurs.

Les données recoupées sont :

- Manuel fabricant A3.200730, distribué par Connect Systems : façade, microphone,
  audio, menus analogiques et options GPS/APRS. Il couvre plusieurs variantes.
- Application PRO GD32 V1.21 authentifiée, SHA-256
  `02b2a3b56bd57c7ada581eb52b9b6f41c5d51aaec1b068d37585efd58dff9c9a`.
- Bootloader du dump complet et sondages exécutés RX/PTT.
- Modèles et résultats antérieurs : LCD, ADC, NAND, USB, GPS, RF, SCT et audio I/Q.
- Table des 100 broches relue : les anciennes hypothèses d’autres cartes ne
  deviennent pas des connexions mesurées. « NON CONNECTE » y était souvent un
  emplacement non renseigné, pas une preuve de non-connexion.
- Datasheets GigaDevice, TI AIC3204 et SCT3258, et documentation du protocole
  microphone. Les possibilités d’un circuit ne prouvent pas son routage sur ce PCB.
- Observations utilisateur : voyant vert en squelch ouvert, rouge en émission,
  haut-parleur microphone sélectionnable et option Bluetooth à inclure.

Les références de photos FCC sont conservées. Leur récupération a échoué dans
cette révision ; aucune nouvelle inspection de ces photos ni correspondance de
révision PCB n’est revendiquée. Les schémas FCC affichés comme métadonnées ne
sont pas traités comme des schémas obtenus.

Une chaîne ASCII candidate est une piste. Exemple concret : `APRS Receive`
existe dans l’image PRO, ce qui ne démontre pas que l’option APRS RX fonctionne
sur le poste capturé. Les menus partagés, variantes et branches désactivées
empêchent d’inférer les capacités depuis les seuls textes.

## Formats et réutilisation

Sources Python 3 et C existant sous GPL-3.0-or-later ; catalogue JSON avec JSON
Schema 2020-12 ; vue CSV ; rapports JSON et JUnit XML. Le signal utilise déjà
WAV PCM16 et SigMF cf32_le. Aucun format opaque supplémentaire n’est requis.
Pour l’extension satellite : éléments TLE ou OMM, propagation de référence
indépendante puis comparaison des fréquences réellement commandées. Le format
orbital ne dispense pas de tester les conventions, l’époque et les signes Doppler.
Les firmwares et captures propriétaires restent des entrées privées séparées
et ne sont pas inclus dans les sources publiables.

## Refaire l’inventaire du firmware

```sh
python bench/oem_discovery.py /chemin/application.CDD --out results/discovery.json
```

Le programme enregistre l’empreinte, les candidats d’entrées, les constantes de
périphériques, les chaînes candidates par exigence et les pointeurs alignés
possibles vers ces chaînes. Il conserve les fonctions indirectes, tables de saut,
code/données et composants opaques dans les inconnues. Un candidat d’entrée n’est
pas une fonction décompilée. Les motifs larges peuvent produire de faux liens.
Aucune absence de chaîne ne prouve l’absence de la fonction.

## Auto-test actuellement exécutable

```sh
python bench/run_bench.py --source-dir /chemin/captures --engine native
python bench/selftest_report.py --regressions bench/results/bench/qualification.json
```

Depuis le paquet Windows : `TESTER_BASES.cmd`. Le lanceur demande le chemin du dossier source, ou accepte `--source-dir`.
Le moteur web doit être arrêté pendant ce test. Les captures originales sont
lues et les écritures éventuelles restent dans des copies virtuelles.

Les trois scénarios OEM historiques sont : entrée porteuse et ouverture audio puis
fermeture ; acquisition puis perte GPS ; PTT puis activation TX/ventilateur/DAC
puis relâchement et retour au repos. Ils dépendent des observations V1.21 et ne
sont pas des tests complets de formes d’onde ou d’audio. Un quatrième scénario
`LED_bus` teste la séquence vert/repos/rouge/repos sur les véritables fronts
GPIO PE3/PE4, sans lire les variables RX/TX OEM ; voir LED_STATUS_BUS.md.

Le rapport `qualification.json` conserve ces verdicts limités. `selftest.json`
et `junit.xml` ajoutent toutes les exigences non qualifiées, marquées
`incomplete` / `skipped`. Aucun test omis ne devient vert. Le code de sortie de
`selftest_report.py` est 2 tant que la qualification est incomplète, 1 en cas
d’échec. `run_bench.py` conserve son code de sortie historique pour ses seuls
scénarios. Les deux portées sont différentes et annoncées dans le lanceur.
Un export seul du catalogue n’exécute pas un firmware.

## Audio : chemins à qualifier séparément

Les sorties à suivre sont le haut-parleur interne, celui du microphone, les
prises externes A/B et le Bluetooth. La sélection microphone/poste/les deux et
l’affectation A/B du microphone doivent être essayées. Les contacts mécaniques
des prises externes et l’impédance de charge relèvent aussi du matériel.
La voix synthétique du navigateur et la boucle I/Q autonome ne constituent pas
une preuve du bon routage. Les sorties inconnues restent `selected: null`.
Les gains du codec, ses horloges et les liaisons SCT/audio doivent être reliés
aux échantillons avant de qualifier le trajet complet.

## Ordre de réalisation convenu

1. Inventaire analogique OEM et preuves matérielles, y compris les voyants.
2. Chaîne FM : chemins microphone/codec/SCT/RF, échantillons et récepteur de mesure
   indépendant ; CTCSS/DCS, signalisation et routage des haut-parleurs.
3. Audit continu des branches et routines non rattachées à l’inventaire ; essais
   croisés et défauts. Aucun total de tests ne démontre que tout a été découvert.
4. GPS : démarrage, acquisition/perte, coordonnées, UTC, trames invalides et
   positions périmées, sans écrire directement le fix dans la RAM du firmware.
5. APRS TX : terminer le DMA réellement utilisé, récupérer la modulation, décoder
   l’I/Q indépendamment et tester l’arbitrage GPS/PTT/canal occupé.
6. Satellite : références orbitales indépendantes, Doppler, limites, CTCSS,
   coexistence UI/RF, restauration de l’état et absence d’usure mémoire inutile.

Le Bluetooth est une option matérielle transversale à l’étape audio : référence
ET12/B707 disponible et quelques commandes AT modélisées. Découverte, appairage,
reconnexion, PTT et audio ne sont pas implémentés. Le firmware du module n’est
pas exécuté : son ISA, sa mémoire et ses interfaces doivent être identifiées.
La phonie DMR reste hors de cette campagne. APRS RX reste une étape ultérieure.
Les fonctions OEM précédemment déclarées supprimables restent dans l’inventaire
pour ne pas être oubliées ; cela ne les rend pas obligatoires dans la première
version du firmware ouvert.

## Pour un firmware entièrement nouveau

Utiliser `run_hardware.py`, sans anciennes adresses de routines ni offsets RAM.
Les observateurs doivent voir les fils GPIO, UART, USB, HPI, ADC/DMA et les
échantillons audio/RF. Le profil de navigation peut changer selon l’IHM ; le
contrat physique reste identique. Le modèle actuel ne couvre pas encore tous
les périphériques : un arrêt de modèle est un essai incomplet.

Chaque futur cas doit contenir état initial, stimuli, résultat physique attendu,
délais en temps virtuel et invariants. Contrôles négatifs nécessaires : mauvais
CTCSS, mauvaise fréquence, PTT ignoré, amplificateur muet, trame APRS corrompue,
capteur absent et commande inconnue. Modifier volontairement un pilote doit
faire échouer les essais concernés. Un firmware ne se déclare pas lui-même bon.
Les temps du modèle ne sont pas précis au cycle ; les marges temporelles devront
être vérifiées sur poste avant toute affirmation sur les performances réelles.
