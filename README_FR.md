# OpenD578

Recherche, banc logiciel et futur firmware pour l'AnyTone D578UV PRO GD32.

Le dépôt rassemble le code du banc, les relevés documentés et les étapes de
développement. Il ne contient pas encore de firmware radio OpenD578 utilisable.

## Périmètre retenu

- Première version utilisable : **VFO simple, FM RX/TX, CTCSS RX/TX, APRS TX**.
- Lecture et écriture des mémoires analogiques depuis un PC, avec conservation
  des calibrations propres au poste, requises pour cette première version.
- Seconde étape : **APRS RX**, ainsi que le DMR nécessaire à l'usage avec un hotspot.
- Cohérence recherchée avec l'utilisation d'un TYT UV390 GPS sous OpenGD77.
- M17 hors périmètre. Les autres modèles AnyTone restent des cibles possibles,
  sans compatibilité annoncée aujourd'hui.

## Le changement du banc

`bench/run_hardware.py` exécute un programme indépendant sans utiliser les
adresses des fonctions ni les structures RAM du firmware constructeur V1.21.
Il accepte une autre implantation du code et de la pile dans les limites du
matériel. Les fronts GPIO alimentent directement les modèles LCD et radio.

Un accès à un périphérique non encore reproduit est signalé comme une limite
du modèle. L'absence d'une signature V1.21 n'est plus un motif d'arrêt dans ce mode.
Les limites physiques du GD32 et les comportements de bus restent contrôlés.

Le banc d'analyse OEM V1.21 est conservé séparément pour les comparaisons et
la poursuite du module satellite. Le cœur satellite doit rester raccordable
au binaire constructeur puis au futur programme autonome.

Les commandes d'installation et de test sont dans [README.md](README.md).
Les notes techniques françaises issues des travaux antérieurs sont indexées
dans [docs/RESEARCH_INDEX.md](docs/RESEARCH_INDEX.md). Elles conservent leurs
distinctions entre preuves, hypothèses et anciens blocages.

Les fichiers constructeur et les captures du poste restent des entrées locales.
Le programme de test généré par `contract_firmware.py` est original ; il teste
des contrats numériques et n'est pas une image à flasher sur un poste.
