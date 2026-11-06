# Comparaison des 60 sujets VK7ZJA avec le depot OpenD578

Base comparee : `OpenD578_COMPLET_SOURCES_F1DMG_VK7ZJA_20261106.zip` (SHA-256 `7979659602bf66a217cd904ab6d44e92e3772f5efc942a26647904f206d349a9`).

Les documents « existants » sont des **fichiers reellement presents dans la base locale**, pas des pages garanties visibles sur le GitHub le plus recent. **Une rubrique existante peut manquer de details**. La provenance de tous ces sujets est historique, via [DB1IG / VK7ZJA D578 v7.4](https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php).

| ID | Rubrique source | Existant OpenD578 | Etat | Complement a consigner |
|---|---|---|---|---|
| VK578-01 | Présentation générale | [Fiche existante](../../hardware/VERSIONS.md) | `RECOUPEMENT_EXISTANT` | Sous-versions GD32 et AT32 et baseband differents ; creer champs de compatibilite par unite. |
| VK578-02 | Erreurs de bande | [Fiche existante](../../cps/COMPATIBILITE_PRO_PLUS.md) | `RESUME_A_DEVELOPPER` | Version MODE/RDT et provenance codeplug : garder separer des addresses NAND. |
| VK578-03 | Comparaison D578 et D878 | [Fiche existante](../../hardware/BLUETOOTH_PRO_PLUS_D878_COMPARAISON.md) | `RESUME_A_DEVELOPPER` | Dual RX D578 contre dual watch D878 ; une seule chaine DMR simultanee. |
| VK578-04 | Comparaison D578 et Alinco DR-MD500/520 | [Fiche existante](../../hardware/VERSIONS.md) | `RECOUPEMENT_EXISTANT` | Materiel historique proche Alinco DR-MD500/520 ; verifier les differences de menu et micro. |
| VK578-05 | Conseils d'utilisation du CPS | [Fiche existante](../../cps/COMPATIBILITE_PRO_PLUS.md) | `RESUME_A_DEVELOPPER` | Exporter les options non couvertes par Export All ; profil CPS/firmware/codeplug. |
| VK578-06 | Alertes antivirus sur le CPS | [Fiche existante](../INDEX_60_SUJETS_VK7ZJA.md) | `RECOUPEMENT_EXISTANT` | Conserver empreinte et source de l executable ; eviter le conseil historique de desactiver antivirus. |
| VK578-07 | Sélecteur des touches micro | [Fiche existante](../../NOTICE_CHANGELOG_MICROPHONE_V11_8.md) | `RESUME_A_DEVELOPPER` | Interrupteur lateral Up/Down du microphone OEM distinct de trame USART0. |
| VK578-08 | Mise à jour du firmware principal | [Fiche existante](../../peripherals/05_BOOTLOADER_24K_DUMP_VECTEURS_USB_FMC_DEVELOPPEMENT_OPEN_SOURCE.md) | `DEJA_DOCUMENTE_A_PRECISER` | Differencier mise a jour GD32, icones SPI et mises a jour de sous-modules. |
| VK578-09 | Pilotes USB sous Windows | [Fiche existante](../../cps/USB_CDC_GD32_V121.md) | `DEJA_DOCUMENTE_A_PRECISER` | Faire correspondre etat CDC Windows/Linux et mode update, sans supposer meme driver. |
| VK578-10 | Diagnostics des erreurs écran | [Fiche existante](../../LED_STATUS_BUS.md) | `RESUME_A_DEVELOPPER` | Cataloguer les messages erreurs et leurs conditions, sans confondre panne flash et mauvais codeplug. |
| VK578-11 | Répertoire d'autres documentations | [Fiche existante](../SOURCES_ET_VERSIONS.md) | `RECOUPEMENT_EXISTANT` | Versions, miroirs, source primaire et liens morts avec statut de conservation. |
| VK578-12 | Paramétrage APRS | [Fiche existante](../../hardware/GPS.md) | `RECOUPEMENT_EXISTANT` | Parametrage APRS a distinguer de reception APRS propre a certaines cartes PLUS. |
| VK578-13 | Répondre pendant un balayage | [Fiche existante](../../cps/PROTOCOLE_OEM_V121.md) | `RESUME_A_DEVELOPPER` | Comportement PTT sur canal detecte en balayage : politique UI/timer. |
| VK578-14 | Réinitialisation du poste | [Fiche existante](../../TEST_MODE_OPTIONS.md) | `DEJA_DOCUMENTE_A_PRECISER` | Reset utilisateur ne doit pas effacer alignement usine ; tests non destructifs. |
| VK578-15 | Compatibilité des modes de confidentialité DMR | [Fiche existante](../../peripherals/04_DMR_SCT3258_BOOTSTRAP_HPI_PAQUETS_CODEC_PARAMETRES.md) | `RESUME_A_DEVELOPPER` | Les modes de privacy ne sont pas tous inter-operables ; distinguer baseband du chiffrement utilisateur. |
| VK578-16 | Écran et façade déportés | [Fiche existante](../../LCD_CABLAGE_PILOTAGE_ET_INTEGRATION_V11_8.md) | `RESUME_A_DEVELOPPER` | Nappe facade de 40 voies citee comme option de deport non OEM ; integrite signal. |
| VK578-17 | Microphones Bluetooth | [Fiche existante](../../hardware/BT01_MICROPHONE_BLUETOOTH.md) | `DEJA_DOCUMENTE_A_PRECISER` | Verifier BT01/ET12 sans supposer qu un casque Bluetooth standard utilise le meme profil. |
| VK578-18 | Étiquettes et repères des touches | [Fiche existante](../../FACADE_GPIO_BOUTONS_CODEUR_VOLUMES_ET_ECLAIRAGES.md) | `RECOUPEMENT_EXISTANT` | Etiquettes et reperage physique a conserver avec les photos, sans impact GPIO. |
| VK578-19 | Deux sorties haut-parleur | [Fiche existante](../../hardware/AUDIO.md) | `DEJA_DOCUMENTE_A_PRECISER` | Sorties HP pouvant muter ou garder actif HP interne ; lien avec PA7/codec. |
| VK578-20 | Prise micro et microphone de table | [Fiche existante](../../NOTICE_CHANGELOG_MICROPHONE_V11_8.md) | `DETAIL_NOUVEAU_A_INTEGRER` | PTT resistif entre broches 1 et 8, 1 a 2,2 kohms, `HandOpMode=Level Detection` ; profil separable d USART0. |
| VK578-21 | Console d'alimentation et bureau | [Fiche existante](../INDEX_60_SUJETS_VK7ZJA.md) | `RECOUPEMENT_EXISTANT` | Accessoire console de bureau : sans impact sur le firmware embarque. |
| VK578-22 | Entrées/sorties audio via micro filaire | [Fiche existante](../../hardware/AUDIO.md) | `RESUME_A_DEVELOPPER` | Audio TX/RX externe type SignaLink : niveaux, masses audio et logique differents. |
| VK578-23 | Audio externe par module Bluetooth | [Fiche existante](../../hardware/BLUETOOTH_D868BT_SP_ET12.md) | `DETAIL_NOUVEAU_A_INTEGRER` | Options BT+int mic / BT+int spk ; ajouter matrice routage audio. |
| VK578-24 | Télécommande PTT via oreillette | [Fiche existante](../../hardware/BP02_PTT_BLUETOOTH.md) | `RECOUPEMENT_EXISTANT` | Exemples Jabra/Plantronics : indices de commandes PTT Bluetooth, pas preuve BP-02. |
| VK578-25 | Images de fond personnalisées | [Fiche existante](../../hardware/COMPOSANTS.md) | `DEJA_DOCUMENTE_A_PRECISER` | Fonds en memoire NAND ; comparer images et canaux couleur de la ressource OEM. |
| VK578-26 | Traitement du microphone | [Fiche existante](../../hardware/AUDIO.md) | `DETAIL_NOUVEAU_A_INTEGRER` | Mic Enhance agit sur DMR TX selon historique ; pas meme profil analogique. |
| VK578-27 | Tonalités de signalisation | [Fiche existante](../../hardware/AUDIO.md) | `RESUME_A_DEVELOPPER` | Tonalites constructeur a analyser comme stimuli audio, distinctes CTCSS/DCS. |
| VK578-28 | Numérotation et carnets EchoLink | [Fiche existante](../../cps/CODEPLUG_CANAL_OEM_V121.md) | `RESUME_A_DEVELOPPER` | EchoLink et numerotation : comportement de carnet CPS non couche SCT HPI. |
| VK578-29 | Combinaisons de touches au démarrage | [Fiche existante](../../TEST_MODE_OPTIONS.md) | `DETAIL_NOUVEAU_A_INTEGRER` | Table P2/P3/P4/P5/P6/MENU/EXIT/DIAL et PTT micro ; plusieurs chargeurs. |
| VK578-30 | Sélection des bandes d'exploitation | [Fiche existante](../../cps/COMPATIBILITE_PRO_PLUS.md) | `RESUME_A_DEVELOPPER` | Table MODE historique par firmware ; ne pas changer bande pour etudier GPIO. |
| VK578-31 | Extension historique de la réception | [Fiche existante](../../hardware/RF.md) | `RESUME_A_DEVELOPPER` | Ne pas confondre FW RX modifie de 2022 avec PRO GD32 V1.21. |
| VK578-32 | Mesures de sensibilité et de puissance | [Fiche existante](../../hardware/RF.md) | `DETAIL_NOUVEAU_A_INTEGRER` | Jeux de mesures historiques de sensibilite et PA a des frequences de test. |
| VK578-33 | Réception de la bande aéronautique | [Fiche existante](../../hardware/CARTE_PLUS_AM_KT_NON_IDENTIFIE.md) | `RESUME_A_DEVELOPPER` | Carte RF PLUS AM distincte du RDA FM broadcast et du front end de base. |
| VK578-34 | Balayage FM et DMR | [Fiche existante](../../peripherals/04_DMR_SCT3258_BOOTSTRAP_HPI_PAQUETS_CODEC_PARAMETRES.md) | `DETAIL_NOUVEAU_A_INTEGRER` | Simplex, DCDM, repetiteur et DataACK : cas de test DMR/CPS. |
| VK578-35 | Découpages de réception FM | [Fiche existante](../../hardware/RF.md) | `RESUME_A_DEVELOPPER` | Cas hors bande : filtres front-end expliquent variation sensibilite. |
| VK578-36 | Plage élargie du récepteur FM broadcast | [Fiche existante](../../hardware/RDA5802N_RECEPTION_FM.md) | `DETAIL_NOUVEAU_A_INTEGRER` | RDA FM : memoires 76-87,5 MHz versus limites VFO et registre de bande. |
| VK578-37 | Polices et icônes | [Fiche existante](../../03_NAND_LECTURES_ECC_CARTE.md) | `DEJA_DOCUMENTE_A_PRECISER` | Distinction entre assets SPI/iconos et font et firmware principal. |
| VK578-38 | Iconographie GPS | [Fiche existante](../../hardware/GPS.md) | `DETAIL_NOUVEAU_A_INTEGRER` | Paquet historique d icones GPS avec mise a jour dediee et conteneur `.spi`. |
| VK578-39 | Mode test et étalonnages | [Fiche existante](../../TEST_MODE_OPTIONS.md) | `DEJA_DOCUMENTE_A_PRECISER` | Table historique de champs FQCA/PA*/BPF*/AGC*/SQTH*/RSSI*/BER/FSK. |
| VK578-40 | Utilitaire AT Options de G4EML | [Fiche existante](../../TEST_MODE_OPTIONS.md) | `DEJA_DOCUMENTE_A_PRECISER` | AT Options v8 et bits de permissions recoupes avec observations OEM V1.21. |
| VK578-41 | Mot de passe au démarrage | [Fiche existante](../../cps/COMPATIBILITE_PRO_PLUS.md) | `RESUME_A_DEVELOPPER` | Mot de passe de demarrage : mode recovery distinct de verrou CPS. |
| VK578-42 | Mot de passe de programmation CPS | [Fiche existante](../../cps/PROTOCOLE_OEM_V121.md) | `RESUME_A_DEVELOPPER` | Mot de passe CPS : ne pas le confondre avec cle crypto ou deverrouillage TEST. |
| VK578-43 | Documents d'homologation FCC | [Fiche existante](../../hardware/PHOTOS.md) | `RECOUPEMENT_EXISTANT` | Photos de versions et documents de certification, schematics indisponibles non inventes. |
| VK578-44 | Photos de démontage de la carte | [Fiche existante](../../hardware/PHOTOS.md) | `DEJA_DOCUMENTE_A_PRECISER` | Positions RF 38 MHz, PCB dessous/dessus et carte facade, photo par variante. |
| VK578-45 | Réserves d'alimentation RTC et GPS | [Fiche existante](../../hardware/SAUVEGARDE_RTC_GPS_XH414HG.md) | `DEJA_DOCUMENTE_A_PRECISER` | RTC et GPS sauvegardes separement ; fonction valide, composants de versions a comparer. |
| VK578-46 | Modification du haut-parleur interne | [Fiche existante](../../hardware/AUDIO.md) | `RESUME_A_DEVELOPPER` | Modification mecanique HP et difference mesuree en historique, pas driver audio. |
| VK578-47 | Connecteur antenne SO-239 / N | [Fiche existante](../../hardware/COMPOSANTS.md) | `RECOUPEMENT_EXISTANT` | Connecteur antenne principal et variantes de chassis : dossier mecanique. |
| VK578-48 | Antennes GPS internes | [Fiche existante](../../hardware/GPS.md) | `DETAIL_NOUVEAU_A_INTEGRER` | Deux connecteurs GPS U.FL/IPX sur facade historique ; un inutilise. |
| VK578-49 | Refroidissement et circulation d'air | [Fiche existante](../../hardware/ETAGES_RF_PROTECTION_FI.md) | `RESUME_A_DEVELOPPER` | Ventilateur, sens de flux et F1DMG ancien : mesure thermique avant modification. |
| VK578-50 | Blindage complémentaire de réception | [Fiche existante](../../hardware/ETAGES_RF_PROTECTION_FI.md) | `DETAIL_NOUVEAU_A_INTEGRER` | Blindage RX ajoute -> capacites parasites -> retouche calibration BPF A/B. |
| VK578-51 | Liste des circuits et topologie du D578 | [Fiche existante](../../hardware/COMPOSANTS.md) | `DEJA_DOCUMENTE_A_PRECISER` | Tous circuits 578 historiques recoupes avec listes des composants PRO/PLUS. |
| VK578-52 | Carte des plages NAND | [Fiche existante](../../03_NAND_LECTURES_ECC_CARTE.md) | `DEJA_DOCUMENTE_A_PRECISER` | Conserver carte NAND historique et NAND OEM brut + OOB comme deux referentiels. |
| VK578-53 | Utilitaire de sauvegarde NAND | [Fiche existante](../../03_NAND_LECTURES_ECC_CARTE.md) | `RESUME_A_DEVELOPPER` | Outils de lecture historiques et sauvegardes sans operation destructrice. |
| VK578-54 | Sauvegarde d'alignement propre au poste | [Fiche existante](../../PROGRAMMING_AND_CALIBRATION.md) | `DEJA_DOCUMENTE_A_PRECISER` | Etalonnages usine propres a chaque poste, jamais recopier valeurs example. |
| VK578-55 | Récupération d'un poste bloqué | [Fiche existante](../../USB_DEBUG_AND_RECOVERY.md) | `DETAIL_NOUVEAU_A_INTEGRER` | Procedure recovery non equivalente a reset ou mise a jour standard. |
| VK578-56 | Prévention des blocages | [Fiche existante](../../USB_DEBUG_AND_RECOVERY.md) | `DETAIL_NOUVEAU_A_INTEGRER` | Defroster et recuperation des blocages : risque perte codeplug, analyser causes. |
| VK578-57 | Structure des conteneurs CDD/CDI/SPI | [Fiche existante](../../peripherals/05_BOOTLOADER_24K_DUMP_VECTEURS_USB_FMC_DEVELOPPEMENT_OPEN_SOURCE.md) | `DEJA_DOCUMENTE_A_PRECISER` | CDD/CDI/SPI et update SCT distincts ; verifier checksums/offsets. |
| VK578-58 | Aide CPS en français | [Fiche existante](../../cps/COMPATIBILITE_PRO_PLUS.md) | `DETAIL_NOUVEAU_A_INTEGRER` | Aides CPS HPT et traductions : versions et encodages a tracer. |
| VK578-59 | Mise à jour interne SCT3258 | [Fiche existante](../../peripherals/04_DMR_SCT3258_BOOTSTRAP_HPI_PAQUETS_CODEC_PARAMETRES.md) | `DEJA_DOCUMENTE_A_PRECISER` | SCT3258 a firmware separe, historique de versions jusqu a 2.01.07BF. |
| VK578-60 | Pistes de développement futur | [Fiche existante](../../firmware/ARCHITECTURE.md) | `RESUME_A_DEVELOPPER` | Etudier codec DSP, nappe facade et vocoder comme pistes futures, pas fonctions OEM implementees. |

## Interpretation des statuts

- `DEJA_DOCUMENTE_A_PRECISER` : la documentation locale traite deja le mecanisme ; enrichir le detail sans l ecraser.
- `DETAIL_NOUVEAU_A_INTEGRER` : source historique indiquant un detail technique peu ou pas documente ; creer une fiche ou des tests.
- `RESUME_A_DEVELOPPER` : la fiche existante aborde seulement la fonction ou son principe ; detailler les interfaces et decisions.
- `RECOUPEMENT_EXISTANT` : ne pas recopier une conclusion identique ; ajouter le lien et la provenance si absent.

Les 60 fiches historiques restent consultables dans [l ancien index VK7ZJA](../INDEX_60_SUJETS_VK7ZJA.md). Les nouvelles conclusions et l inventaire DB1IG par site sont dans [l audit source par source](AUDIT_CROISE_SOURCES.md).

## Conditions de fiabilite

Une capture OEM executee sur le PRO V1.21 constitue une preuve valide de fonctionnement pour cette revision. Une photographie d une ancienne version et la valeur d alignement d un autre poste n ont pas la meme portee. Les modes specifiques PLUS et AT32 sont mis en evidence, et les conteneurs firmware et offsets codeplug ne sont pas transplantes entre variantes.
