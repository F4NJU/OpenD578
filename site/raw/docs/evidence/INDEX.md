# Centre de preuves OpenD578

Ce dossier sert a distinguer un **fait prouve**, une **hypothese de circuit** et un **comportement uniquement simule**. Il accompagne les vues interactives et le developpement de firmware alternatif.

## Notation de preuve

| Code | Signification | Exemple |
| --- | --- | --- |
| `USER_PHOTO` | Composant ou implantation observe par utilisateur | H2226 SSOP-B16, deux AFT05MP075N |
| `USER_MEAS` | Mesure ou identification sur poste physique | SWD DPIDR, ID NAND 98 CB |
| `OEM_STATIC` | Instruction/adresse verifiee dans binaire constructeur | Vecteur app 0x08006000, PA7 mode speaker |
| `OEM_EMU` | Effet execute dans le banc qui modele des peripheriques | Commandes RF, USB/USB CDC, LCD |
| `DATASHEET` | Propriete constructeur d'un composant specifie | GD32 VBAT pin 6, XH414HG 0,08 F |
| `THIRD_PARTY_BOARD` | Observation d'une AUTRE revision d'AnyTone | VK7ZJA, quatre QA4818N, RTC + GPS backup |
| `INFERRED` | Hypothese deduite de plusieurs indices | BH2226 -> varicaps, charge VBAT MCU |
| `UNKNOWN` | Information explicitement non etablie | Trace electrique de l'UART GNSS sur le PRO |

Dans un fichier `hardware/models/*.json`, les liaisons `physical` doivent avoir une preuve sur le poste, `oem_trace` une preuve d'instruction OEM, `emulator` une trace du banc ; `datasheet` decrit un circuit seul, pas sa continuite PCB.

## Pieces documentaires ajoutees le 05/11/2026

- [Les deux sauvegardes RTC et GPS, XH414HG et edition MS412](../hardware/SAUVEGARDE_RTC_GPS_XH414HG.md)
- [Etages RF, protection contre inversion, filtres varicaps et FI reservee](../hardware/ETAGES_RF_PROTECTION_FI.md)
- [Monographie NAND reconstruite](../peripherals/01_NAND_SPI_CABLAGE_PILOTE_FORMATS_MEMOIRE.md)
- [Monographie GPS reconstruite](../peripherals/02_GPS_ATGM336H_UART_NMEA_RAM_PARAMETRES.md)
- [Monographie ADC/DAC et audio reconstruite](../peripherals/03_ADC_DAC_GD32_CODEC_TLV320AIC3204_CHAINE_AUDIO_CALIBRATION.md)
- [Monographie SCT3258 DMR reconstruite](../peripherals/04_DMR_SCT3258_BOOTSTRAP_HPI_PAQUETS_CODEC_PARAMETRES.md)
- [Monographie bootloader reconstruite](../peripherals/05_BOOTLOADER_24K_DUMP_VECTEURS_USB_FMC_DEVELOPPEMENT_OPEN_SOURCE.md)
- [Capture publique et independante du protocole CPS](CPS_QDMR_CAPTURE_DE_REFERENCE.md)
- [Fichiers originaux et acquis manquants](../archives/ORIGINAUX_A_RECUPERER.md)
- [Brochage GD32 / KiCad reconstruit](../../hardware/kicad/README.md)
- [Sources externes nouvellement recroisees](SOURCES_EXTERNES_RECROISEES_20261105.md)
- [Grille de mesures a completer pour les deux sauvegardes](MESURES_RTC_GPS_A_CONSIGNER.md)
- [Changelog de consolidation](../CHANGELOG_PREUVES_RTC_GPS_20261105.md)
- [Rapport de validation et limites des tests](VALIDATION_DU_DEPOT.md)

Les 100 broches `GD32F303VKT6` sont definis dans `hardware/pinmaps/GD32F303VKT6_LQFP100_REFERENCE.csv`. Les propositions de destination et etats figurent dans les colonnes de ce fichier, qui ne peut pas servir de netlist de fabrication.

## References externes principales

1. GigaDevice, GD32F303xx datasheet, Tableau 2-5 LQFP100 : <https://www.gd32mcu.com/data/documents/datasheet/GD32F303xx_Datasheet_Rev3.0.pdf>
2. Seiko Instruments, XH-HG Capacitor XH414HG 0,08 F, 3,3 V max : <https://www.infinite-electronics.kr/datasheet/3c-XH414HG-IV01E.pdf>
3. VK7ZJA / IK8JHL, D578, deux sauvegardes, protections RF, FI, NAND : <https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php>
4. RadioFoundry, architecture des familles D868/D878/D578, SCT3258, QA4818N, boot : <https://radiofoundry.org/docs/spec/hardware-anytone>
5. qdmr, Chapter 8, capture de lecture D578UV via CPS : <https://static.dm3mat.de/qdmr/manual/ch08.html>
6. Linux Toshiba SPI NAND, composant 0xCB, ECC : <https://cos.googlesource.com/third_party/kernel/+/5aa092beb12119ed7e0b9fc696e597ca0fba9721/drivers/mtd/nand/spi/toshiba.c>
7. ROHM BH2226FV-E2 : <https://www.rohm.com/products/data-converter/d-a-converters/8bit-d-a/bh2226fv-product>
8. TI TLV320AIC3204 : <https://www.ti.com/product/TLV320AIC3204>
9. FCC, photos de revisions D578 : <https://fccid.io/T4K-D578UV/Internal-Photos/Internal-Photos-4513250>
10. qdmr / dmr-tools codeplugs : <https://github.com/dmr-tools/codeplugs>.

**Regle documentaire :** meme une source externe serieuse ne prouve pas l'identite du composant non marque ou sa connexion sur **notre** PRO/PLUS. Photographier et mesurer si une conclusion concerne physiquement notre carte.

## Reconstruction QA4818N, 6 novembre 2026

- [Protocole, registres, fréquence et architecture RX/TX](../hardware/QA4818N_RECONSTRUCTION_REGISTRES_PLL_CHAINES_RX_TX.md).
- `qa-bus`: trames et GPIO observés dans le simulateur OEM, pas une netlist physique.
- `qa-frequency-format`: codage **AT1846S** documenté ; transposition QA4818N encore non confirmée.
- `qa-lo-if`: structure de la famille D578 selon VK7ZJA, mapping des quatre banques encore inconnu.
- `qa-mapping-unknown` / `qa-tx-not-qualified`: les impossibilités actuelles sont conservées dans `CLAIMS.json`.

Aucune capture RF authentifiée portant deux fréquences RX/TX n'a été intégrée. Les tests ne sont que numériques et sans émission.
