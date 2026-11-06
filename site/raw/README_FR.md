# OpenD578

Dossier technique : [centre de preuves](docs/evidence/INDEX.md), [sauvegardes RTC/GPS](docs/hardware/SAUVEGARDE_RTC_GPS_XH414HG.md), [cinq monographies reconstruites](docs/peripherals/01_NAND_SPI_CABLAGE_PILOTE_FORMATS_MEMOIRE.md), [originaux absents](docs/archives/ORIGINAUX_A_RECUPERER.md).

Guide du site : [README_SITE.md](README_SITE.md). Publication GitHub : [instructions](docs/PUBLICATION_GITHUB_DEPOT_COMPLET.md). Dossier programmation : [CPS/USB/codeplug](docs/cps/README.md).

La source publique du banc est **V11.7** ; les notices LCD/microphone V11.8 sont de la documentation complémentaire et ne remplacent pas leur code source manquant.


Le [banc V11.3](docs/HARDWARE_COVERAGE.md) propose maintenant le mode matériel
indépendant dans l'interface web : chargement d'un binaire expérimental, moteur
natif, entrées USB/UART simulées et inventaire des appels/blocs candidats. Les
limites DSP/DMR, audio, programmation CPS et reset automatique restent explicites.

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

## Qualification V11.7

Le voyant de statut suit les commandes PE3/PE4. Le catalogue ouvert contient
117 exigences FM, IHM, audio, GPS, APRS, satellite et Bluetooth. Quatre essais
bornés réussissent ; la qualification matérielle complète reste incomplète.
Voir [la méthode et les limites](docs/QUALIFICATION_ANALOGIQUE.md) et
[le bus du voyant](docs/LED_STATUS_BUS.md).

### Reconstruction du pilote RF QA4818N

[Monographie détaillée](docs/hardware/QA4818N_RECONSTRUCTION_REGISTRES_PLL_CHAINES_RX_TX.md), [outil de traces](tools/qa4818n_trace.py), [calculateur C](firmware/rf/qa4818n_frequency.c) et [tests](tools/test_qa4818n_trace.py). Aucun TX ni câblage électrique n'est piloté ; les valeurs calculées selon AT1846S restent à confirmer sur QA4818N.


## Mise à jour de la cartographie du 6 novembre 2026

- Le GD32F303 est au centre du schéma PRO et PLUS.
- Nouvelle [vue détaillée de façade](https://telectroboy.github.io/OpenD578/facade.html) avec boutons, codeur, deux volumes, écran LCD et LED.
- L'Airband du PLUS figure dans la zone RF, et non dans la façade.
- Les GPIO et bus identifiés en exécutant le firmware OEM sont affichés comme résultats de reverse engineering valides. Les mesures de continuité physique restantes sont documentées séparément.
- [Correspondances et règles de validation](docs/hardware/VALIDATION_FONCTIONS_OEM.md).
