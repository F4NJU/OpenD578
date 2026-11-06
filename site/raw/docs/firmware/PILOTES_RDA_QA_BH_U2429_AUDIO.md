# Pilotes à développer : RDA5802N, QA4818N, BH2226 et chaîne audio

**Cible primaire :** D578UV PRO GD32 V1.21. Cette page décrit les frontières de pilotes prévues pour un futur firmware autonome. **Elle n'affirme pas qu'un firmware complet a été construit ou flashé.**

## Interfaces HAL

| Pilote | Entrées à découvrir | API cible | Ce qui est testable hors poste | Statut |
| --- | --- | --- | --- | --- |
| `rf_qa4818` | Bus 24 bits (8 +16), quatre CS logiques, signaux reset/IRQ | `read_reg(bank,page,reg)`, `write_reg(...)`, `set_rx_frequency(...)` | Reconstruction de trames RF sur traces `RfSpi` ; pas de valeurs RF inventées | Bus émulé, map des quatre puces inconnue |
| `fm_rda5802` | Bus I²C, adresse vérifiée, régulateur, reset | `probe`, `init`, `tune`, `seek`, `read_rssi`, `standby` | Décoder trames du modèle `FmI2c` ; pas de statut RF simulé | RDA5807-compatible au banc, RDA5802N physique non raccordé |
| `dac_bh2226` | CSB/CLK/DI, 8 sorties, reset, codes usine | `set_channel(ch,value)`, `reset` | Encoder/deserializer 12 bits selon fiche fabricant | Identité H2226 plausible ; aucune ligne mesurée |
| `volume_u2429` | CLOCK/DATA, 5 V, encode 11 bits | `set_attenuation(channel,db)`, `mute` | Décoder/encoder trames selon fiche UTC | GPIO et adaptation de niveau non identifiés |
| `codec_aic3204` | Horloge, port série, configuration registres TI | `init_audio`, `set_path`, `set_gain` | Décodage statique des appels OEM et tables | Connectivité carte non cartographiée |
| `audio_mc34119` | Ligne CD, rail et entrée analogique | `enable(bool)` | Test de temporisation de mute | Aucune GPIO liée à CD |
| `audio_1517` | `M/SS` pin 8, alimentation, gains externes | `enable`, `mute` | Machine à états pure côté PC | PA7 candidat, continuité non mesurée |
| `rf_aft05m` | Bias, capteurs, filtres, gamme VHF/UHF | `tx_request` sous garde-fous RF | Transitions d'état sans piloter de PA réel | Valeurs usine de biais inconnues |
| `power_l7805` | Commande amont éventuelle et rails | Contrôle supervision DC, pas un registre 7805 | Test logique Power `PA0` et veille | Aucune ligne EN intrinsèque au L7805 |

## Séparation ferme entre code matériel et modèle d'analyse

Le firmware autonome ne doit pas appeler une routine `0x080...` trouvée dans l'application constructeur. Il doit posséder une HAL de registres GD32, horloges, GPIO, DMA, UART, watchdog, interruptions et temporisateurs **fondée sur le datasheet MCU**. Les adresses OEM servent à documenter comment le constructeur a réalisé une opération, pas à initialiser des ressources matérielles de substitution.

Le code de test sur PC peut lire `bench/rf_spi.py` et `bench/fm_i2c.py`. Les **trames synthétiques** enregistrées par ces modèles ne peuvent pas être assimilées aux valeurs d'étalonnage du matériel ou à un réglage de fréquence prêt pour la radio.

## Ordre d'intégration

1. GPIO entrée, USB/SWD lecture seule et console de trace ; préserver le bootloader et la NAND.
2. Contrôle de source horloge et transactions RF **passives**, relever les quatre CS.
3. I²C RDA5802N, avec confirmation d'ACK matériel avant lecture/écriture de configuration.
4. Contrôle de mute audio ; identités et liaisons U2429, PA1517/YD1517, MC34119.
5. DAC BH2226 et SGM8272 après découverte des tensions analogiques et canaux.
6. Réception FM VHF/UHF puis CTCSS ; TX désactivé tant que la gestion PA/capteurs n'est pas qualifiée.
7. GPS, DMR, mémoire, puis mode satellite et variantes PLUS.

## Tests automatiques recommandés

- Rejet de toute lecture sur une banque RF hors bornes `0..3` et de tout registre non qualifié.
- Encodage bit par bit 24 bits et 12 bits, sans aucune écriture GPIO réelle.
- Rejet des écritures RDA hors adresses validées par trames capturées.
- Test de mute au démarrage, perte d'horloge, absence d'ACK, reset d'alimentation et contrôle de transition RX/TX.
- En absence de calibrations PA, la condition `tx_enabled` doit rester fausse.

## Liens aux fiches techniques et aux preuves

[QA4818N ×4](../hardware/QA4818N_QUATRE_CIRCUITS_26MHZ.md) · [RDA5802N](../hardware/RDA5802N_RECEPTION_FM.md) · [BH2226](../hardware/BH2226_H2226_DAC_RF.md) · [UTC U2429G](../hardware/VOLUME_U2429G.md) · [Ampli et AOP](../hardware/AUDIO_MC34119_SGM8272.md) · [AFT05MP075N](../hardware/PA_RF_AFT05MP075N.md) · [Plan de mesures](../hardware/PLAN_INVESTIGATION_BROCHAGES.md).

## Deux encodeurs de mots série déjà testables

`firmware/hal/serial_command_encoders.c` contient le codage **pur** (sans GPIO) des mots BH2226 12 bits et U2429 11 bits. Ils servent à préparer les tests de capture du bus, pas à piloter directement les composants ; aucun CS, CLOCK ou DATA n'est branché. Leurs tables proviennent des notices ROHM et UTC et sont indépendantes de toute adresse du firmware constructeur.

Compilation de vérification sur PC :

```sh
cc -std=c11 -Wall -Wextra -Werror -pedantic \
  firmware/hal/serial_command_encoders.c \
  firmware/tests/test_serial_command_encoders.c \
  -o /tmp/opend578_serial_test
/tmp/opend578_serial_test
```

## QA4818N : encodeur et validation (6 novembre 2026)

Le code source `firmware/rf/qa4818n_frequency.[ch]` construit les registres `0x29/0x2A` selon la **formule de l'AT1846S**, avec tests C et sans accès au GPIO. Le décodeur `tools/qa4818n_trace.py` permet de vérifier sur **des captures constructeur authentifiées** le facteur et les rôles des quatre banques. Il reste à qualifier les horloges, le PLL et l'initialisation QA ainsi que les registres TX ; le code actuel n'est pas flashable. [Documentation complète](../hardware/QA4818N_RECONSTRUCTION_REGISTRES_PLL_CHAINES_RX_TX.md).
