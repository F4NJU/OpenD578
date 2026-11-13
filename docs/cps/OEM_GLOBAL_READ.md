# Lecture globale des canaux et tonalités — CPS 0.9

## Utilisation

Dans le CPS ouvert sous `/cps/`, ouvrir Banc émulé puis **Lire tous les canaux
actifs**. Le CPS lit l'index, récupère les canaux actifs dans les banques OEM,
vérifie chaque réponse et ferme par un seul END. L'aperçu unique est alors prêt
pour la sélection et l'import. Il ne s'agit pas d'une image mémoire complète :
zones, scans, contacts, identifiants DMR et réglages généraux ne sont pas lus.

Les commandes de groupe restent disponibles. Elles conservent la session ouverte,
cumulent les résultats sans dupliquer un emplacement et remplacent une ancienne
valeur lors d'une relecture. Terminer la session envoie END. La sélection peut
être préparée avant END ; l'import attend toujours son acquittement. Après END,
le watchdog OEM impose encore le redémarrage du moteur pour une nouvelle session.

## Provenance du profil

Faits croisés entre la cartographie explicitement marquée D578 V1.21 et qdmr :

- [dmr-tools/codeplugs, D578 V1.21](https://github.com/dmr-tools/codeplugs/blob/b63adb9cc006a167c72cec96243aea5133c76416/d578uv/v1.21.xml)
- [qdmr, champs communs des canaux](https://github.com/hmatuschek/qdmr/blob/fb9c96af53f646c0706fa360209b2e0e6cd79a08/lib/anytone_codeplug.hh)
- [qdmr, décodage des tonalités](https://github.com/hmatuschek/qdmr/blob/fb9c96af53f646c0706fa360209b2e0e6cd79a08/lib/anytone_codeplug.cc)
- [qdmr, banque et bitmap](https://github.com/hmatuschek/qdmr/blob/fb9c96af53f646c0706fa360209b2e0e6cd79a08/lib/d868uv_codeplug.hh),
  hérités par les classes D878 puis D578 ; la cartographie XML D578 confirme ces adresses.

XML téléchargé vérifié : blob Git `420490421b1ab0481c8197fe8cd77973d6eaa2ae`,
SHA256 `4b3e4efb52d43d5ae5e79b318e33bb689d8115d23ccc3c3feb3e448592ff4b7a`.
L'implémentation TypeScript utilise ces faits ; aucun code Qt n'est incorporé.

| Élément | Profil V1.21 |
| --- | --- |
| Capacité | 4000 emplacements, records de 64 octets |
| Banques | Base `0x00800000`, 128 records par banque, espacement `0x40000` |
| Dernière banque | 32 records, arrêt avant le VFO à `0x00FC0800` |
| Bitmap | `0x024C1500`, 512 octets, 4000 bits utiles, bit 1 = actif, LSB en premier |
| Type de tonalité RX / TX | Octet `0x09`, bits `1:0` / `3:2` : 0 aucune, 1 CTCSS, 2 DCS, 3 inconnu |
| Index CTCSS TX / RX | `0x0A` / `0x0B`, table publiée ; index 0 = 62,5 Hz, index 51 = personnalisé |
| CTCSS personnalisé | `0x10..0x11`, entier little-endian en dixièmes de Hz |
| DCS TX / RX | `0x0C..0x0D` / `0x0E..0x0F`, code binaire et inversion à 512 |

L'allowlist R n'autorise que les sous-blocs alignés de 16 octets dans les records
de ces banques et les 512 octets du bitmap. Les trous, extensions de canaux,
VFO, étalonnages et toute commande W restent refusés. La conversion en page
physique NAND appartient exclusivement au firmware exécuté.

## Tonalités et import

Les CTCSS RX/TX sont conservés séparément dans le document FM. Le mode aucune
est explicite ; un index invalide n'est jamais assimilé à une absence de tonalité.
Les valeurs personnalisées sont acceptées dans la plage conservatrice de
60,0 à 260,0 Hz ; les autres restent inconnues. Cette plage est une restriction
du décodeur, pas une spécification matérielle confirmée.

Les DCS normaux/inversés sont affichés dans l'aperçu et gardés dans l'instantané
OEM. Leur import est refusé car le schéma FM PC ne peut pas les représenter.
Les tonalités inconnues et les modes numériques/mixtes bloquent aussi l'import.
Les bits affichés d'un canal numérique ne démontrent pas une tonalité RF active.
Les noms et RX/TX des canaux FM sélectionnés sont copiés ; largeur et puissance
PC restent des choix de préparation. TX reste inhibée. Le bilan du document
peut signaler des doublons ; aucun canal existant n'est remplacé.

## Qualification réelle

Une session complète du banc natif a lu les 224 emplacements actifs de la
capture, couvrant deux banques. 928 réponses de lecture ont été vérifiées,
931 trames soumises au transport, aucune W, un seul END acquitté. Les tonalités
décodées comprennent 56 CTCSS RX, 110 CTCSS TX, 1 DCS RX et 2 DCS TX.

Le script Python `tools/verify_oem_global_capture.py` est un second décodeur,
alimenté par le flux USB reçu et la table de tonalités du XML épinglé. Il
revérifie les réponses, reconstruit bitmap/records et compare l'empreinte de tous
les champs au résultat TypeScript : concordance exacte sur les 224 canaux.
Il refuse une capture dont le tampon USB a débordé. Rapports publics :
`qualification/native-global-tones-2026-11-13.json`, sans noms ni fréquences.
Les traces complètes restent locales ; les cinq fichiers source sont inchangés.

Reproduction depuis la racine d'une copie complète du dépôt :

```powershell
$env:OPEND578_BENCH_ENGINE = 'interactive'
$env:OPEND578_READ_ALL = '1'
$env:OPEND578_READ_SEQUENCE = '0'
$env:OPEND578_COMPARE_OEM = '0'
node tools/qualify_cps_python.mjs CHEMIN_PYTHON DOSSIER_CAPTURES RESULTATS_NEUFS

& CHEMIN_PYTHON tools/verify_oem_global_capture.py `
  --capture RESULTATS_NEUFS/usb_cdc_final.json `
  --reference CHEMIN_XML_V121 `
  --qualification RESULTATS_NEUFS/qualification.json `
  --report RESULTATS_NEUFS/independent-verification.json
```

La lecture globale bénéficie d'un budget de lecture explicite de 15 minutes
dans le script de qualification, après le budget de démarrage. L'interface
reste annulable et le délai d'une commande reste borné ; aucune commande n'est
répétée automatiquement après une expiration ambiguë.

60 tests hôte : frontières des banques, index actifs, CTCSS standard/personnalisé,
DCS, valeurs inconnues, refus d'import avec perte, conservation des tonalités,
annulation, erreurs, cumul et déduplication. Le dernier emplacement est testé
synthétiquement ; seules les banques présentes dans la capture ont été exécutées.
Cette qualification ne prouve ni le fonctionnement RF ni la compatibilité de
toutes les variantes PRO/PLUS. L'interface graphique reste à confirmer visuellement.
