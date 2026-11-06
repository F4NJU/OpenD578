# Sources externes et limites de leur application au D578 GD32

Dernière vérification de cette fiche : **5 novembre 2026**. Ces références sont des points de comparaison de la famille AnyTone, pas des preuves directes de continuité électrique sur notre révision de carte.

## Firmware, CPS, USB et mémoires

| Source | Faits pertinents | Limite à conserver |
| --- | --- | --- |
| [AnyTone USA - téléchargements](https://anytoneusa.com/Downloads/) | PRO 1.21 et PLUS 2.07 référencés au 19/06/2024 ; CPS et images de ces branches | Les annonces de versions ne prouvent pas la compatibilité de format ni la version réellement installée |
| [AnyTone fabricant](https://www.anytone.net/download) | Paquets CPS/FW PRO et PLUS officiels | Redistribution des exécutables OEM non incluse |
| [BridgeCom - téléchargements D578](https://support.bridgecomsystems.com/anytone-578-v2-model-cps-firmware-downloads) | Compatibilité CPS/FW, avertissement de sauvegarde et reset | Branches 2.x, ne pas l'appliquer directement à un PRO V1.21 |
| [qdmr](https://github.com/hmatuschek/qdmr) | Code source de l'interface AnyTone et structures de codeplug D578UV/D578UV II | Logiciel GPL, protocole à vérifier par version |
| [dmr-tools/codeplugs](https://github.com/dmr-tools/codeplugs/tree/master/d578uv) | Cartographie XML versionnée ; observation des changements de schéma | Les layouts sont issus d'un reverse engineering tiers, pas de notre image |
| [AnyTone_CPS](https://github.com/hardenedpenguin/AnyTone_CPS) | Logiciel Linux et profil `d578uv_v1.21` | Compatibilité à exercer avec ce modèle précis |
| [AesApp WebCPS - version supportées](https://cps.aes.app/manual/en/about) | Sépare D578 PRO 1.xx et PLUS 2.xx pour son propre support | Un refus d'outil n'indique pas une incompatibilité physique générale |
| [RadioFoundry - matériel AnyTone](https://radiofoundry.org/docs/spec/hardware-anytone) | USB CDC, paquets de firmware, boot, baseband, description QA4818N | Distinguer les faits de leur analyse et leurs objectifs de portage |
| [RadioFoundry - protocole open firmware](https://radiofoundry.org/docs/spec/open-firmware-cps) | Protocole OpenGD77 (différent du protocole AnyTone OEM) | Ne jamais mélanger `R/W/X/C` et `PROGRAM/R/W/END` sans adaptateur |
| [VK7ZJA / 578mods](https://www.theweeks.org/tmp/FILES/Anytone-Mods/578mods.htm) | NAND 256 Mio, carte de zones, RF, alignement et circuits synthèse/FI | Relevés sur révisions antérieures, vérifier par lecture du dump du GD32 |

## Photos, manuels et circuits radio

| Source | Usage retenu |
| --- | --- |
| [Photos FCC T4K-D578UV](https://fccid.io/T4K-D578UV/Internal-Photos/Internal-Photos-4513250) | Implantation et composants de la variante homologuée ; pas un schéma garanti pour la nôtre |
| [FCC T4K-D578UVIII](https://fccid.io/T4K-D578UVIII/) | Comparaison des révisions RF et façade |
| [Manuel D578 CSI](https://www.csi-radios.com/content/support/AnyTone/AT-D578UV/User%20manual.pdf) | Fonctions générales, prise microphone et attribution des connecteurs |
| [GD32F30x User Manual Rev2.9](https://www.gd32mcu.com/data/documents/userManual/GD32F30x_User_Manual_Rev2.9.pdf) | Registres GPIO, SPI, USB, AFIO, DMA, NVIC ; manuel MCU, pas le schéma AnyTone |
| [KIOXIA TC58CVG1S3HRAIG](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/305/KIOXIA_TC58CVG1S3HRAIG_Rev2.0_E191001.pdf) | Géométrie 2048+64, ECC, commandes et registres de statut |
| [ROHM BH2226FV](https://www.rohm.com/products/data-converter/da-converters/bh2226fv-product) | CNA 8 canaux 8 bits en SSOP-B16, marquage H2226 ; assignation des huit sorties inconnue |
| [SCT3258 référence](https://radiofoundry.org/docs/spec/hardware-anytone) | Baseband DMR, lien HPI, mise à jour distincte du GD32 |

## Intégration des découvertes du projet

Les schémas du site distinguent **datasheet**, **trace OEM**, **simulateur**, **observation physique**, **hypothèse**. Les références RDA5802N, BH2226FV, U2429G, MC34119G, SGM8272, AFT05MP075N, PA1517G/YD1517P, KT0905R/KT09S5R, quatre QA4818N probables et la carte BT D868BT-SP sont suivies individuellement dans `docs/hardware/` et `hardware/models/`.

Les schémas et contenus externes ne sont **pas copiés** dans l'archive publique sans preuve de licence. Le site lie les références originales et les relevés reconstruits, et conserve les inconnues explicitement.

## Relecture du 5 novembre : preuves RTC/GPS et clients CPS

La reference `XH414HG IV01E` est donnee par VK7ZJA pour les deux sauvegardes de la carte CPU ; la fiche Seiko la classe comme **condensateur XH-HG de 0,08 F**. La reference **MS412** vient d'une edition anterieure et ne doit pas etre declaree equivalent. Voir [fiche source](hardware/SAUVEGARDE_RTC_GPS_XH414HG.md).

Le depot [AnyTone_CPS](https://github.com/hardenedpenguin/AnyTone_CPS) est **archive** ; le developpement passe par [CodeplugStudio](https://github.com/hardenedpenguin/CodeplugStudio). Ces projets et [AesApp](https://cps.aes.app/manual/en/about) sont des sources de comparaison **avec compatibilite explicitement liee aux branches PRO/PLUS**. Voir [relecture detaillee](evidence/SOURCES_EXTERNES_RECROISEES_20261105.md).
