# Contrat CPS OpenD578 — proposition 0.1

Statut : format PC implémenté dans ce lot, proposition à relire avec F4EGM.
Ce document ne décrit pas un protocole déjà implémenté dans le firmware.
Référence examinée : dépôt Telectroboy/OpenD578, commit
`580632027f61b7c7c855a1bef16ba9295e9f674e`.

## Périmètre

Premier objectif : mémoires analogiques, un VFO, noms, fréquences RX/TX,
CTCSS RX/TX indépendants, largeur FM, choix de puissance et interdiction TX.
Les zones sont des listes ordonnées côté PC ; un poste sans zones annonce zéro
zone supportée. Le CPS bloque alors le transfert d'un codeplug contenant des
zones et propose ultérieurement une conversion explicite ; aucune perte silencieuse.
APRS TX, DMR et APRS RX ne sont pas définis par cette version du format.

Références du dépôt : `docs/ROADMAP.md`,
`docs/PROGRAMMING_AND_CALIBRATION.md`,
`browser-bench/assets/cps-client.mjs`, `browser-bench/assets/cps-memory.mjs`.
Les deux derniers traitent le firmware OEM ; leurs adresses, checksums et
commandes ne sont pas le contrat du nouveau firmware.

## Format du fichier PC

JSON UTF-8, discriminant `format: "opend578-codeplug"`, `schemaVersion: 1`.
Tous les champs sont obligatoires. Champs inconnus et versions inconnues refusés
afin d'éviter une réexportation avec perte de données. Aucune migration n'existe
encore ; toute future migration sera explicite et conservera le fichier source.

| Champ | Type / règle |
| --- | --- |
| `name` | Nom du document, Unicode valide, non vide et sans contrôle |
| `channels` | Liste ordonnée de canaux ; vide autorisé |
| `zones` | Liste ordonnée de zones ; vide autorisé |
| `vfo` | Paramètres analogiques sans id/nom, ou `null` pour ne pas le programmer |

Un canal contient :

| Champ | Type / règle |
| --- | --- |
| `id` | Identifiant stable, unique parmi les canaux, 1–64 caractères ASCII ; premier alphanumérique puis alphanumériques, `_`, `-` |
| `name` | Unicode valide, non vide et sans contrôle ; longueur radio vérifiée séparément |
| `mode` | `"FM"` |
| `rxHz`, `txHz` | Entiers positifs représentables exactement par JavaScript |
| `bandwidth` | `"narrow"` ou `"wide"` ; correspondance physique à convenir |
| `power` | Identifiant non vide de niveau, validé contre ceux annoncés par le poste ; jamais une calibration PA |
| `rxCtcssDeciHz`, `txCtcssDeciHz` | Entier positif en dixièmes de Hz (`885` = 88,5 Hz), ou `null` pour désactivé |
| `txInhibit` | Booléen ; le firmware devra appliquer l'interdiction, pas seulement le CPS |

Une zone contient `id`, `name`, `channelIds`. Son id est unique parmi les zones.
Chaque référence doit désigner un canal existant, sans doublon dans la même zone.
Un canal peut appartenir à plusieurs zones. Réordonner les canaux ne change pas
les références. Aucun id n'est un numéro de slot, une adresse ou un index flash.

Le décalage relais est dérivé de `txHz - rxHz`, jamais stocké une seconde fois.
Le choix du pas de syntonisation et l'ajustement oscillateur sont distincts.
`txHz` reste obligatoire même en RX seul ; sa bande n'est contrôlée pour le
transfert que lorsque `txInhibit` est faux. RX, tons, largeur et puissance restent
validés. Le firmware doit confirmer qu'il honore cette sémantique avant connexion.

## Validation en deux niveaux

1. Fichier PC : types, unités, identifiants, références, absence de champs inconnus.
2. Cible : capacités effectivement annoncées et validées par l'adaptateur.

`DeviceCapabilities` décrit les maxima de canaux/zones/membres, la longueur
des noms radio en octets UTF-8, les bandes RX et TX par intervalles inclusifs,
les largeurs, les identifiants de puissance, les tons acceptés et la prise en
charge du VFO. Aucun nombre de canaux ni bande AT-D578 n'est supposé dans le cœur.
La validité du fichier ne prouve ni sa compatibilité radio ni la possibilité de
transmettre sur ses fréquences. Les capacités manquantes bloqueront le transfert.

Le nom du document n'est pas un nom radio et n'est pas limité par `maxNameBytes`.
Le support Unicode UTF-8 de la cible est une proposition : si un autre encodage
est retenu, le contrat de capacités devra être modifié avant les premiers transferts.

## Dialogue proposé — non implémenté

Avant d'inventer un protocole, comparer un protocole existant reproductible
(dont les exigences mémoire et persistance) à un protocole OpenD578 propre.
La prise en charge du D578 OEM par qdmr ne suffit pas à établir une compatibilité.
Web Serial n'est qu'un adaptateur possible si le firmware expose USB CDC.

Les opérations logiques à couvrir sont :

1. Identifier modèle, profil carte, firmware, version de protocole, versions de
   codeplug prises en charge et capacités.
2. Lire un instantané cohérent avec identifiant de révision ; sauvegarder l'original.
3. Préparer un transfert utilisateur basé sur cette révision, en précisant les
   enregistrements concernés ; refuser une révision périmée.
4. Valider contenu, références et intégrité avant activation.
5. Confirmer explicitement la persistance de la nouvelle révision.
6. Relire, redémarrer dans le banc, relire et comparer les données persistées.

Il faudra distinguer acquittement transport, contenu reçu, enregistrement durable
et vérification après redémarrage. Une coupure doit laisser l'ancienne version
valide ou permettre une récupération documentée. Après résultat ambigu d'un
commit, relire l'état au lieu de renvoyer aveuglément la commande.

## Calibrations et diagnostics

Aucun champ de calibration ni adresse brute dans ce format. Le futur firmware
doit limiter les opérations normales aux enregistrements utilisateur identifiés.
Le banc vérifiera des empreintes identiques des calibrations avant/après upload,
interruption et redémarrage. Le rejet de champs par le CPS seul ne garantit pas
la préservation côté firmware. Les valeurs inconnues d'un poste restent intactes.
Les diagnostics normaux enregistreront étapes, révisions et erreurs, sans contenu
complet du codeplug. Les traces d'octets seront locales et volontaires.

## Décisions à prendre avec F4EGM

| Sujet | Proposition / question ouverte |
| --- | --- |
| Transport | USB CDC si viable sur le firmware neuf ; pont du banc à définir |
| Protocole | Comparer réutilisation et protocole propre ; aucun opcode réservé ici |
| Stockage | Format radio compact, slots, tailles et persistance à définir côté firmware |
| Capacités | Bandes, granulation fréquence, puissances, largeurs physiques et tons réels à qualifier |
| Noms | UTF-8 proposé ; longueur et glyphes disponibles à confirmer |
| Zones | Optionnelles ; premier firmware peut annoncer zéro |
| VFO | Programmation facultative, `null` signifie préserver le VFO existant |
| Atomicité | Granularité, récupération et confirmation durable à fixer |
| Versions | Protocole et fichier PC distincts ; négociation de schéma à définir |

## Acceptation de ce lot

- Aller-retour JSON sans perte et sans mutation de l'entrée.
- Erreurs avec chemin, code et message pour fichiers invalides.
- Références stables malgré réordonnancement ; RX/TX et tons indépendants.
- Conversion MHz/Hz sans arrondi implicite.
- Limites du poste testées sur un profil purement synthétique.
- Aucun lien matériel ni hypothèse de compatibilité avec le CPS constructeur.

Tests : `cd cps` puis `npm test` avec Node.js 24 ou ultérieur.
Les tests OEM et matériels ne font pas partie de cette livraison indépendante.
