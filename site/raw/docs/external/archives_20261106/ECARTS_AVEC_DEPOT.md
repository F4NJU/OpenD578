# Comparaison directe avec le depot OpenD578

Base de comparaison: archive de depot `OpenD578_COMPLET_RADIOFOUNDRY_DB1IG_20261106.zip` et copie extraites dans notre contexte. Les contenus du ZIP utilisateur ont ete lus localement, tandis que les documents sources et HAL du depot sont issus de nos travaux precedents. Aucun fichier public ancien n'a ete supprime.

| Cle | Nouvelle preuve / connaissance | Fiche OpenD578 existante | Verdict de couverture | Action |
| --- | --- | --- | --- | --- |
| F1-01 | HTML F1DMG `page-20.htm` reellement capture, 53 661 octets | `docs/external/F1DMG_RECUPERATION.md` | **Ancienne conclusion d'indisponibilite depassee** | Ajouter notice datee et empreinte |
| F1-02 | HTML F1DMG `page-22.htm` reellement capture, 136 785 octets | `docs/external/F1DMG_RECUPERATION.md` | **Nouvelle page exploitable** | Indexer BT01, CPS, versions, fichiers |
| F1-03 | Modes de demarrage francais `D578-REGLAGES.doc` | `docs/TEST_MODE_OPTIONS.md`, `docs/02_CPU_FLASH_BOOT_USB_SWD.md` | Deja etabli par OEM/historique | Conserver seconde presentation attribuee |
| F1-04 | Procedure d'export/reinitialisation/reimport `MISE A JOUR D578.doc` | `docs/cps/COMPATIBILITE_PRO_PLUS.md`, `docs/PROGRAMMING_AND_CALIBRATION.md` | Partiellement presente | Developper procedure migration des donnees |
| F1-05 | Versions historiques BT01, ET12 et SCT dans PDF F1DMG | `docs/hardware/BLUETOOTH_D868BT_SP_ET12.md`, `docs/firmware/BLUETOOTH_PILOTES_BT01_PTT.md` | Nouveau detail de versions | Separer module ET12 de BT01 physique |
| F1-06 | Valeurs d'exemple et effets `CMD-Roaming.doc` | `docs/cps/CODEPLUG_CANAL_OEM_V121.md`, `docs/external/db1ig/` | **Details absents** | Decrire parametres sans inventer un encodage NAND |
| F1-07 | SMS BrandMeister + options CPS | `docs/cps/PROTOCOLE_OEM_V121.md` | **Guide d'utilisation absent** | Creer fiche differenciant DMR SMS / CPS USB |
| F1-08 | Exemple manuscrit `TouchesD578.pdf` | `docs/FACADE_GPIO_BOUTONS_CODEUR_VOLUMES_ET_ECLAIRAGES.md` | Exemple ergonomique nouveau | Conserver comme configuration F1DMG, ne pas modifier GPIO |
| F1-09 | Photos `DEBRID_578`, protection ROS, antenne, touches | `docs/hardware/PHOTOS.md` | Photos non indexees individuellement | Ajouter inventaire prive par source et revision |
| F1-10 | Codeplug D578 V1.11 `.rdt`, fichier AT Options, aides HPT, firmware ZIP | `docs/external/F1DMG_RECUPERATION.md` | **Non telecharges** | Relancer collecte ciblee |
| F1-11 | Modifier le refroidissement: `578a.jpg` deflecteur, `578b.jpg` grille/ventilateur; exemple `FAN OPEN = BOTH` et 50 vers 30 degres C en 4 min | `docs/hardware/PHOTOS.md`, `docs/external/db1ig/` | **Photos et observation specifique nouvelles** | Fiche F1DMG pratique; ne pas generaliser la thermique |
| F1-12 | Photos de modification microphone avec electret, jack et interrupteur `01Mb`/`02Mb`/`03Mb.jpg` | `docs/NOTICE_CHANGELOG_MICROPHONE_V11_8.md` | **Realisation privee nouvelle**, differente de l'USART0 OEM | Conserver les images en prive et delimiter le circuit |
| F1-13 | `RAZ-ANYTONE.png` propose une intervention sur NRST avec la mention non essaye | `docs/02_CPU_FLASH_BOOT_USB_SWD.md` | **Hypothese historique non validee** | Ne pas convertir en procedure SWD |
| F1-14 | Regles pratiques et observations scan/PTT, Monitor, offset hotspot +330/+340 Hz, 1750 Hz, APRS WIDE, SMS | `docs/QUALIFICATION_ANALOGIQUE.md`, `docs/cps/` | **Cas utilisateur non indexes** | Voir `F1DMG_RELEVES_PRATIQUES.md` |
| VK-01 | 46 photographies communes VK7ZJA prouvees identiques par SHA | `docs/hardware/PHOTOS.md`, `docs/external/PHOTOS_ET_DOCUMENTS_CIBLES.md` | Faits techniques presents, octets archives hors depot | Indexer hashes et photos sans les republier |
| VK-02 | Passage nappe facade 40 broches, photo `578 head connections.jpg` | `docs/external/db1ig/approfondissements/VK578-16_ecran_et_facade_deportes.md` | Mention deja presente, illustration source manquante | Tenter URL encodee, analyser la nappe |
| VK-03 | Frequences FI, quatre QA4818N, NAND, SCT3258 | `docs/hardware/RF.md`, `docs/peripherals/*`, `docs/hardware/QA4818N*` | **Deja documente et souvent valide par OEM** | Joindre provenance photo, ne pas retrograder preuve |
| VK-04 | Donnees de calibration, outils flash et recovery historiques | `docs/PROGRAMMING_AND_CALIBRATION.md`, `docs/external/db1ig/` | Partie technique documentee, utilitaires sources absents | Conserver outils anciens separement, lecture seule en priorite |
| EXT-01 | Miroir TheWeeks | `docs/external/SOURCES_ET_VERSIONS.md` | Pas capture (TLS) | Garder lien / erreur et mirroirs alternatifs |
| EXT-02 | OZ1DGQ : PDF manuels/FCC | `docs/hardware/PHOTOS.md` | Page index capturee, PDF non captures | Encoder espaces ; chercher documents FCC officiels |
| EXT-03 | RadioFoundry, qdmr, CodeplugStudio, FCC | `docs/external/radiofoundry/` et references externes | **Pas dans le ZIP utilisateur** | Archivage complementaire a planifier |
| EXT-04 | Archive complete des autres pages DB1IG | `docs/external/db1ig/` | Seule `578mods.php` capturee | Collecter 878mods, DMRbasics, codeplug, editor (sources externes) |

## Ce que cette archive ne permet pas de conclure

Elle ne contient pas de session SWD nouvelle, de capture UART/SPI du poste, ni de nouveau dump de la Flash du GD32. Elle ne permet donc pas de deviner une commande QA4818N precise, de prouver une affectation GPIO manquante ou d'identifier les zones NAND inconnues. Les preuves OEM deja existantes dans le depot demeurent valides, les instructions d'utilisation F1DMG sont un niveau de preuve different.

Pour une enquete de firmware alternatif, les fichiers les plus utiles a examiner de nouveau sont les ressources CPS `.HPT`, codeplugs `.rdt` versionnes et leurs diffs, outils de service/documentation, et un eventuel protocole de mise a jour SCT. Les listes CSV de milliers de contacts et les captures ecran d'interface ont une valeur inferieure pour le developpement des pilotes.
