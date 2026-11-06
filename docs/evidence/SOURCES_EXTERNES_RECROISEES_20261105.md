# Nouvelles preuves externes recroisees, 5 novembre 2026

Cette fiche etablit **ce que les documents publics ajoutent** aux releves sur nos D578. Une preuve de fonctionnement sur un poste d'une autre revision ne doit jamais etre consideree comme une connexion GPIO verifiee sur le PRO GD32 V1.21.

## Sauvegarde RTC et GPS

- Le dossier photographie de VK7ZJA / IK8JHL localise **deux composants de sauvegarde sur le PCB ecran/CPU**, face arriere pres de la nappe pour **RTC**, face avant entre les potentiometres pour **GNSS hot start**. Il indique **XH414HG IV01E**. L'utilisateur avait deja signale les elements de sauvegarde sur son PCB.
- Le constructeur de la reference **XH414HG** la classe parmi les **condensateurs de sauvegarde XH-HG**, **0,08 F / 3,3 V maxi**. Le terme « lithium rechargeable » du guide de maintenance ne suffit pas a changer sa categorie technologique.
- Une version ancienne du guide mentionne **MS412**. Ce n'est pas une equivalence prouvee. Il faut releve de marquage, dimensions, schema de charge et revision PCB.
- Le MCU **GD32F303VKT6 LQFP100** dispose d'une alimentation secours **VBAT sur broche physique 6**. La piste vers le composant RTC n'a pas ete mesuree. La version/sous-famille exacte du GPS doit etre determinee avant de figer le numero de sa broche de sauvegarde.

Sources : [VK7ZJA/IK8JHL D578](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php) ; [dossier PDF historique](https://www.radiomanual.info/schemi/Vari/Alinco_DR-MD500_DR-MD520_AnyTone_AT-D578UV_mods_and_information_VK7ZJA_2023.pdf) ; [datasheet Seiko XH414HG](https://www.infinite-electronics.kr/datasheet/3c-XH414HG-IV01E.pdf) ; [datasheet GD32](https://www.gd32mcu.com/data/documents/datasheet/GD32F303xx_Datasheet_Rev3.0.pdf).

## Quatre circuits RF, varicaps et FI reservee

- VK7ZJA decrit **quatre QA4818N** de reference 26 MHz, deux comme LO/VFO, deux comme recepteurs apres FI de **38,550 / 38,850 MHz**. Les quatre LQFP32 grattes observes sur le poste sont compatibles avec cette architecture, mais ne sont pas identifies individuellement par piste ou marquage.
- La documentation externe decrit **quatre filtres varicaps par voie de bande**, un **relais et une diode d'alimentation** et des **empreintes FI supplementaires non peuplees**. Il reste a comparer les photos RF PRO/PLUS aux vues FCC et a tracer les sorties du BH2226FV avant de lier celles-ci aux varicaps.

Sources : [VK7ZJA](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php) ; [RadioFoundry](https://radiofoundry.org/docs/spec/hardware-anytone) ; [FCC D578UV](https://fccid.io/T4K-D578UV/Internal-Photos/Internal-Photos-4513250).

## CPS : distinctions des versions et references utilisables

- Le manuel **qdmr**, chapitre 8, donne une capture publique du protocole OEM AnyTone D578 `PROGRAM -> QX 06`, identification et lecture `R`/reponse `W`. Il valide la *forme du protocole*, pas l'ensemble des offsets sur notre V1.21.
- **AnyTone_CPS** est maintenant archive par son auteur ; le developpement a migre vers **CodeplugStudio**. L'ancienne version utilisait le profil `d578uv_v1.21`, mais les plans de memoire doivent etre verifiés avant ecriture.
- **AesApp WebCPS** declare distinguer les D578 **1.xx PRO** et **2.xx PLUS** et identifie le PLUS sur USB comme `D578UV2` dans son champ de compatibilite. Sa documentation ne revendique pas le support complet des codeplugs 1.xx. Ce sont des proprietes de cet outil, pas une affirmation de compatibilite ou d'incompatibilite electrique des processeurs.
- Un codeplug public documente comme **PLUS CPS 1.21 / FW 2.08** est une **preuve de version externe**, et non le codeplug d'origine de notre PLUS ; aucun binaire n'a ete importe.

Sources : [qdmr chap. 8](https://static.dm3mat.de/qdmr/manual/ch08.html) ; [AnyTone_CPS (archive) -> CodeplugStudio](https://github.com/hardenedpenguin/AnyTone_CPS) ; [CodeplugStudio](https://github.com/hardenedpenguin/CodeplugStudio) ; [AesApp WebCPS](https://cps.aes.app/manual/en/about) ; [exemple de codeplug PLUS 2.08](https://codeplug.pi4utr.nl/Codeplug%20for%20AT-578%20models/20251013%20AT-D578UVIII%20PLUS%20CPS%20v1.21%20FW%20v2.08%20as%20made%20by%20PC7MM%20-%20Explanation.pdf).

## Niveaux de validation maintenus

| Observation | Nature | Suffit pour compiler un driver ? |
| --- | --- | --- |
| Datasheet reference exactement identifiee | Fonctions et limites du circuit | Oui pour l'interface abstraite, pas pour les GPIO de la carte |
| Decode statique d'une routine V1.21 | Registres/timing candidats, attaches au hash OEM | Non sans validation passive sur le poste |
| Transaction observee dans le banc OEM | Comportement du modele et de l'OEM dans cette simulation | Non sans confirmation des signaux physiques |
| Photo du D578 historique | Implantation d'une autre revision | Non, sauf confirmation de la meme carte et du meme routage |
| Test de continuite / analyseur logique de la carte cible | Liaison et forme d'onde mesurees | Oui dans les limites de tension, frequence et conditions du test |

Voir [inventaire des observations et types](INDEX.md), [actions de mesure RTC/GPS](MESURES_RTC_GPS_A_CONSIGNER.md) et [originaux manquants](../archives/ORIGINAUX_A_RECUPERER.md).
