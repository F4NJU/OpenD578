# Préparer des canaux depuis le banc OEM — CPS 0.8

Ouvrir le CPS depuis `/cps/` sur le serveur Python du banc, puis **Banc émulé**.
Les lectures successives gardent la session ouverte. Cliquer sur Terminer la session envoie END ; après cet acquittement, la préparation d’un import est disponible.
Depuis le HTML autonome, le bouton du banc ouvre le CPS connecté dans un autre
onglet ; les documents des deux onglets restent dans leurs sessions respectives.
Exporter le JSON pour déplacer le document entre ces sessions.

1. Sélectionner les emplacements désirés, ou sélectionner tous les FM interprétables.
2. Choisir la largeur FM et l'identifiant de puissance du document PC.
3. Vérifier la sélection et les réglages de préparation, puis cocher l'attestation.
4. Cliquer **Ajouter la sélection en réception seule**.

Nom et fréquences RX/TX sont copiés. Le champ de puissance OEM est affiché pour
inspection, mais n'est pas converti en niveau du futur firmware. Largeur,
CTCSS, zones et interdiction TX constructeur ne sont pas décodés : les nouveaux
canaux utilisent la largeur choisie, la puissance PC choisie, aucune tonalité
et **TX inhibée**. Vérifier ces réglages avant de réactiver l'émission.
Les modes DMR/mixtes, les noms non interprétables et les fréquences inconnues
sont exclus. Un emplacement interprétable n'est pas une preuve de canal actif.

Les canaux existants ne sont pas remplacés. Chaque ajout reçoit de nouveaux
identifiants ; les zones, listes de scan et VFO sont conservés. Une seule
annulation retire l'ajout. Les doublons de fréquences restent possibles et
peuvent être examinés dans le bilan du document. Aucun transfert vers la radio.

## Preuve et limites

Le script de qualification peut activer une comparaison sans exporter les données :

```powershell
$env:OPEND578_BENCH_ENGINE = 'interactive'
$env:OPEND578_COMPARE_OEM = '1'
node tools/qualify_cps_python.mjs CHEMIN_PYTHON DOSSIER_CAPTURES DOSSIER_RESULTATS_NEUF
```

Il reconstitue la page à partir des réponses HTTP/USB du client, contrôle à
nouveau adresse, checksum et bornes des 128 réponses, puis compare avec
`bench/web/mini_cps_protocol.js`. Aucun accès direct à la mémoire du MCU ni à la
NAND. Le rapport ne contient ni noms ni fréquences. La référence a pour SHA256
`3bba2dcd3af5c0e5beb6b34ce978b674f20f6d2741412b9cbbc88cb696506640`.

Sur la première page réelle : 32 emplacements, cinq champs chacun, aucun écart,
131 trames soumises et aucune W, END acquitté. La concordance avec le décodeur
du banc n'est pas une certification constructeur ou une mesure RF. Le décodeur
CPS conserve volontairement comme inconnues les fréquences nulles/négatives ;
ces cas sont vérifiés sur des données synthétiques et absents de la page testée.

Tests : import atomique, sélection, nouveaux identifiants, paramètres inconnus,
TX inhibée, refus de conversion numérique vers FM, annulation/rétablissement,
sauvegarde JSON et comparaison synthétique des décodeurs. Les autres pages,
les fonctions après END, le poste physique et le nouveau firmware restent à
qualifier. Le nouveau parcours graphique reste à vérifier manuellement.


## Relire sans redémarrer — version 0.8

Après Identifier et lire, cliquer de nouveau pour relire le même groupe, ou
changer le groupe puis lire. Le même client conserve la session USB et contrôle
ses compteurs avant la suite. Cliquer Terminer la session seulement quand les
lectures sont finies : le firmware demande ensuite son reset, qui n'est pas
automatiquement exécuté par le banc. Une nouvelle session après END requiert
un redémarrage. Ne pas recharger l'onglet au milieu d'une session ; sa perte ou
une annulation impose également un redémarrage. Aucun END n'est renvoyé après
un échec ambigu.

Les instantanés exportés avant fermeture portent endAcknowledged: false.
L'import dans le document reste désactivé jusqu'à END acquitté, puis utilise
le dernier groupe lu. Les groupes précédents peuvent être exportés avant de
passer au suivant ; ils ne sont pas automatiquement cumulés dans le document.

Reproduction : OPEND578_READ_SEQUENCE='0,0,1' avec OPEND578_BENCH_ENGINE='interactive'
pour tools/qualify_cps_python.mjs. Désactiver OPEND578_COMPARE_OEM pour une
séquence multi-page ; cette comparaison ne concerne qu'une page zéro isolée.
