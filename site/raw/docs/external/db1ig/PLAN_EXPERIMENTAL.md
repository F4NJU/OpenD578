# Plan d'exploitation des nouveaux indices DB1IG, sans perte des preuves OEM

Le but est de combler les trous de la documentation, **pas** de revalider des fonctions qui marchent deja dans le firmware constructeur. Chaque capture sera associee a une variante, un firmware, une sequence d'evenements, un hachage de l'image et une provenance.

## Ordre de travail recommande

| Priorite | Experimentation | Observable concret | A comparer a |
|---|---|---|---|
| P1 | Rechercher les neuf combinaisons de boot dans le dispatch startup OEM | Tests GPIO/ADC, chaines UI, branches, chemins de chargement | `docs/FACADE_GPIO_BOUTONS_CODEUR_VOLUMES_ET_ECLAIRAGES.md`, `docs/TEST_MODE_OPTIONS.md` |
| P1 | `HandOpMode` et microphone de table | Offset config, branche USART versus detection niveau, verrou PTT | `docs/NOTICE_CHANGELOG_MICROPHONE_V11_8.md`, `docs/cps/` |
| P1 | Afficher la liste OEM des parametres TEST sans changer de valeur | Nom du champ, index, plage, provenance, banque et RAM | `docs/test_mode_20261104.json`, `docs/TEST_MODE_OPTIONS.md` |
| P1 | Relier `BPF*` a la commande analogique des filtres | Mot reg ecrit dans BH2226FV ou commande equivalent | `docs/hardware/BH2226_H2226_DAC_RF.md`, `bench/rf_spi.py` |
| P1 | Relier `PA*` aux niveaux TX mais en observation du code sans PA | Sequence DAC/RF hors emission, restrictions safety | `docs/hardware/PA_RF_AFT05MP075N.md` |
| P1 | Historiser types de ressources firmware | Chargeur MCU, `.spi` graphiques, SCT, ET12, Hand-Soft | `docs/peripherals/05_BOOTLOADER_24K_DUMP_VECTEURS_USB_FMC_DEVELOPPEMENT_OPEN_SOURCE.md` |
| P2 | `BT + int mic/spk` et `Mic Enhance` | Sources/sorties activees, commandes codec, flags | `docs/hardware/AUDIO.md`, `docs/hardware/BLUETOOTH_D868BT_SP_ET12.md` |
| P2 | Diagnostic GPS startup/RSSI | Chaine d'initialisation et sources NMEA, UI LCD | `docs/peripherals/02_GPS_ATGM336H_UART_NMEA_RAM_PARAMETRES.md` |
| P2 | Programmer en simulateur des stations FM broadcast 76-108 MHz | Valeurs I2C RDA et limitation UI versus tuner | `docs/hardware/RDA5802N_RECEPTION_FM.md` |
| P2 | Non regression codeplug a deux versions | Import/export CSV, options non incluses, hashes alignement | `docs/cps/CPS_QUALIFICATION.md` |
| P2 | Tests DMR simplex / DCDM / repetiteur en lecture seule | Differences registres SCT et flags UI, une seule chaine DMR a la fois | `docs/peripherals/04_DMR_SCT3258_BOOTSTRAP_HPI_PAQUETS_CODEC_PARAMETRES.md` |
| P2 | Transcription des valeurs RF historiques | Tableau baseline avec methodes de mesure, sans ecriture | `docs/hardware/RF.md` |
| P3 | Relever photographiquement les deux coax GPS et les filtres FI optionnels | Presence/absence revision PRO/PLUS + empreintes | `hardware/photos/`, `docs/hardware/ETAGES_RF_PROTECTION_FI.md` |

## Format minimal de fiche de preuve

```json
{
  "id": "OEM_V121_BT_AUDIO_ROUTING_001",
  "radio": "D578UV PRO GD32",
  "firmware": "GD V1.21",
  "source_type": "OEM_EXECUTED_IN_BENCH",
  "image_sha256": "REPLACE_WITH_REAL_SHA256",
  "stimulus": "BT audio option toggled in simulated menu",
  "observation": "REPLACE_WITH_OBSERVED_GPIO_OR_REG_TRACE",
  "related_module": "TLV320AIC3204/ET12",
  "physical_continuity": "NOT_REQUIRED_FOR_OEM_FUNCTIONAL_VALIDATION",
  "source_reference": "docs/hardware/BLUETOOTH_D868BT_SP_ET12.md"
}
```

Les libelles `REPLACE_WITH...` sont des espaces a remplir, pas des resultats inventes.

## Ce que l'on ne fait pas automatiquement

- Aucune emission RF, mise en PTT ou modification de calibration pendant le sondage.
- Aucun chargement d'un exemple d'alignement d'un autre D578 dans la NAND du poste.
- Aucun transfert de firmware D878, AT32 ou Alinco vers le GD32 PRO V1.21.
- Aucune interpretation d'un miroir/traduction VK7ZJA comme confirmation independante.
- Aucun classement « non valide » des pilotes OEM fonctionnels faute de mesure de continuite.

L'ensemble des notes anciennes reste disponible. Les nouvelles mesures sont ajoutees dans un sous-dossier de preuves horodate, pas en remplacement des traces precedentes.
