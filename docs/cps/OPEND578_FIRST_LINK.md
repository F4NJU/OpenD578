# CPS 0.10 — identifier le firmware neuf et lire A/B

Cette première intégration vise la variante `rx_fm_cps` de l'alpha RX FM de
F4EGM. Le panneau **OpenD578 · VFO** est distinct du panneau **Banc OEM**.
Les lectures des canaux OEM et leurs CTCSS restent disponibles dans ce dernier,
mais ne sont pas des fonctionnalités du nouveau firmware.

## Essai dans le banc local préparé

Le binaire de banc est `browser-bench/samples/rx_fm_cps.bin`. Depuis le serveur
Python du banc déjà utilisé :

1. Arrêter le moteur en cours après avoir terminé toute session OEM engagée.
2. Choisir le modèle Matériel, NAND vierge et démarrage Reset application.
3. Choisir le fichier expérimental `rx_fm_cps.bin`, placement automatique,
   puis moteur natif/Interactif. Ne pas sélectionner le firmware OEM.
4. Démarrer et attendre l'écran de l'alpha RX FM.
5. Ouvrir `/cps/` sur ce même serveur, actualiser le CPS, cliquer
   **OpenD578 · VFO**, puis **Identifier et lire A/B**.

L'affichage initial doit montrer A=145,500 MHz, B=435,000 MHz, largeur large et
émission inhibée. Actionner le codeur du banc puis relire pour voir la nouvelle
valeur. Aucune session PROGRAM/END ni redémarrage n'est nécessaire entre ces
lectures du nouveau service. Le document éditable n'est pas remplacé.
L'export est une observation JSON, pas un codeplug téléversable.

Le firmware annonce explicitement ses limites : pas de modification VFO,
mémoires, CTCSS/DCS, émission ou persistance. Le bouton du CPS n'invente pas
ces capacités. Le contrat mémoire PC existant reste une proposition pour la suite.

## Preuves et contrôles

- `docs/evidence/rx_fm_cps/arm.json` : binaire ARM autonome, bus USB/PMA du
  modèle matériel, action codeur, refus WRITE et portes TX surveillées.
- `docs/evidence/rx_fm_cps/http.json` : serveur HTTP réel, adaptateur TypeScript,
  USB CDC et ARM ; deux lectures sur le même moteur, exclusivement HELLO/VFOS.
- 63 tests Node CPS, dont 3 spécifiques au protocole, à la fragmentation, aux
  réponses inattendues et à la séparation des allowlists native/OEM.
- 8 contrôles parseur C hôte et 8 tests du runner matériel, incluant la régression
  du quota d'attente renouvelé après progression CPU.

Reproduction de bout en bout depuis une copie complète de la branche CPS :

```powershell
node tools/qualify_opend578_cps.mjs CHEMIN_PYTHON browser-bench/samples/rx_fm_cps.bin RESULTATS_NEUFS
```

Le script crée son propre serveur/banc matériel avec NAND vierge, charge le
binaire choisi et emploie les classes du CPS. Il ne lit aucune capture OEM et ne
synthétise aucune réponse du firmware. Les observations de VFO sont les valeurs
initiales publiques de l'alpha, pas un codeplug utilisateur.

Le binaire est une expérience de banc, pas un paquet constructeur à flasher.
La connexion USB physique, le VID/PID officiel, le pull-up de la carte, les
pilotes du PC et la réception RF ne sont pas qualifiés. Le nouveau panneau
graphique reste à confirmer visuellement. Détails du pilote et du protocole :
`firmware/experiments/rx_fm_alpha/CPS_READONLY.md`.
