# SCT3258 : bootstrap, HPI, codec et circulation de la voix

**Source principale :** [RadioFoundry, Anytone hardware, sections 2.1 à 2.5](https://radiofoundry.org/docs/spec/hardware-anytone). **Base locale :** [monographie du SCT3258 du D578](../../peripherals/04_DMR_SCT3258_BOOTSTRAP_HPI_PAQUETS_CODEC_PARAMETRES.md), [ADC/DAC et codec](../../peripherals/03_ADC_DAC_GD32_CODEC_TLV320AIC3204_CHAINE_AUDIO_CALIBRATION.md). Fiche de recherche. Aucune émission, aucun dump propriétaire redistribué.

## 1. Les responsabilités sont séparées

| Domaine | Circuit et fonctionnement | Ce que notre port doit fournir |
|---|---|---|
| Contrôle/menus | GD32F303, firmware OEM étudié dans OpenD578 | Configuration, appels HPI et état radio |
| DMR couche PHY/MAC et codec voix | SCT3258 avec son firmware interne et vocoder AMBE+2 | Commandes DMR, réception d'événements, alimentation du FIFO et démarrage du SCT |
| Conversion audio | TLV320AIC3204, PCM/I2S vers SCT | Paramètres du codec, chemin analogique et niveau du signal |
| Données stockées | NAND Toshiba du D578 | Codeplug, calibrations, enregistrements selon zones, sans toucher au firmware interne SCT |

La conversion PCM↔AMBE ne doit pas être supposée fournie par le GD32. Les échanges du GD32 avec le codec passent par les commandes de contrôle envoyées au SCT, dont `CODEC_SELECT`, `SET_I2C_ADDRESS`, `I2C_OPERATION` et les trames *codec bypass* (bit 6 de TYPE signalé dans l'analyse externe). Cette architecture explique qu'un pilote AIC3204 purement MCU/I²C ne suffit pas à reproduire le fonctionnement OEM.

## 2. HPI et initialisation

Le SCT3258 possède un **HPI parallèle asynchrone de 8 bits** avec commandes de lecture/écriture, signaux de contrôle et une ligne `HOBIB` de disponibilité. Les sélections de timing Intel/Motorola sont déterminées au démarrage, la documentation mentionnant la broche PIO1. Le modèle OEM D578 associe DATA0..7 à `PD8..PD15`, HCSN/HWRN/HRDN à `PD2/PD3/PD4`, et HOBIB à `PD5`. Ces affectations sont des observations de notre modèle constructeur, non une simple importation du brochage D868.

Le bootstrap décrit par Sicomm est de **1 024 mots de 16 bits** (2 048 octets), transférés octet faible puis octet fort après reset. Le SCT exécute cette amorce qui lui permet ensuite de démarrer le programme situé dans sa mémoire propre. La réponse nominale citée est `84 A9 61 00 02 20 17 01`. Notre modèle sait vérifier cette étape. Pour le firmware alternatif, un timeout HPI ou un contenu de boot inconnu doit provoquer une erreur nette, jamais une activation RF.

RadioFoundry a identifié, dans plusieurs images OEM de la famille, un bloc de 2 048 octets portant le SHA-256 :

```text
743515b9f7cd90737c1fff29b652b7558bc5a56487ec38df4fdea8877e7a619a
```

Cette empreinte **ne prouve pas encore l'identité du bloc présent dans notre PRO GD32 V1.21** sans recalcul sur l'image d'origine. La source signale quatre variantes de patch envoyées en fonction d'un mode, à des offsets tels que `0x34C`, `0x352` ou `0x45C–0x45D`. Le sens de ces modes n'est pas déterminé. Ne pas patcher ces octets sur le poste sur la seule base de cette analyse. Ne pas placer le bloc propriétaire dans GitHub.

Le contrôleur SCT est distinct du bootloader GD32 : charger une nouvelle application MCU ne remplace pas son UserFlash ni les différentes images de vocoder. Les mises à jour SCT doivent garder leur propre procédure et version.

## 3. Commandes vocales OEM identifiées par RadioFoundry

Le firmware OEM utilise une **interface de niveau applicatif DMR** pour les appels vocaux. Les champs signalés comprennent : `DMR_FLC`, `DMR_CC`, `DMR_CALLED_ID_BCD`, `DMR_OWN_ID_BCD`, `DMR_CALL_OPTION`, `DMR_CALL_SLOT`, `DMR_OFFSET`, puis `DMR_CALL_START`. Des données utilisent également `DIGC_DATA_FRAME` ; ce n'est pas nécessairement le chemin utilisé pour tous les appels voix.

**Découverte :** les messages `CHAN_D` transportent des blocs de **36 octets** lors de l'enregistrement et de la lecture de communications par la NAND. `VOCODER_IO_SET` est envoyé avec des valeurs `0x04`, `0x08`, `0x10`, `0x20`, `0x40`, puis zéro pour terminer. La source indique que `0x40` route une source de voix issue du MCU vers la chaîne de modulation. Cela prouve un mécanisme d'échange de données vocales dans les firmwares étudiés, pas encore un interfaçage temps réel complet pour notre V1.21.

La décomposition de 36 octets en **quatre blocs de 72 bits** avec cadence d'environ **80 ms** est explicitement donnée comme hypothèse dans la source. Ne pas la graver dans une ABI tant que les trames, le sens de transfert, les compteurs et les marqueurs de fin ne sont pas vérifiés. Les slots DMR ont une périodicité de **60 ms** (alternance des deux slots) ; il faut mesurer la relation entre les deux cadences au lieu de leur attribuer un ratio simpliste.

## 4. Gains, réglages et champs protocole à conserver

Noms reconnus dans l'étude OEM externe :

- Acquisition de voie : `ANALOG_CONFIG`, `CTC_PARAM`, `ANALOG_SUBAUDIO`, `SQ_LEVEL`, `AFC_CONFIG`.
- Gains audio/RF : `MOD_GAIN`, `DEMOD_GAIN`, `DIGI_MIC_GAIN`, `DIGI_SPEAKER_GAIN`, `MISC_GAIN`.
- Compensations : `DC_OFFSET`, `IQCOMP_COEF`, `MODOUT_CONFIG`, `EQUALIZER_FILTER`.
- Service/DMR : `BER_REPORT`, `PARITY_ENABLE`, `SCRAMBLER_SEED`.
- Identifiants conservés bruts parce que non décrits dans le manuel v1.0 : `0x2B`, `0x3B`.

Ce sont des **noms de champs**, pas des unités d'étalonnage universelles. Une écriture de `MOD_GAIN=123` ne devient pas une valeur nominale du D578 sans son contexte. Rapprocher les paramètres de la NAND, des tables du mode TEST et des traces HPI existantes.

## 5. Conséquences concrètes pour le firmware OpenD578

1. Pilote `sct3258_hpi` : GPIO déterministes, changement de sens DATA0..7, IRQ HOBIB, timeout et FIFO bornés.
2. `sct_boot` : vérification du hash de l'amorce fournie localement par le propriétaire, chargement 1 024 mots, validation de l'ACK, timeout.
3. `sct_codec` : initialisation du TLV320AIC3204 via SCT, matrice de chemins MIC/HP et restrictions de volume.
4. `sct_voice` : démarrage/fin d'appels en mode OEM easy, gestion du slot, identifiants DMR et contrôle d'état.
5. `sct_chan_d` **expérimental** : décodeur passif des charges de 36 octets, vérification de l'horodatage et de la continuité, **sans TX par défaut**.
6. `sct_data` : cas séparés `DIGC_DATA_FRAME` pour CSBK/headers/UDT et différents débits, avec détection d'erreur par type.

Les possibilités privacy, hotspot et passerelle vocale dépendront des tests CHAN_D en DMR et de la légalité des usages. Ne pas déclarer ces fonctions impossibles par principe, mais ne pas les annoncer comme opérationnelles avant essai.

## 6. Méthode de recoupement non destructive

À partir d'un corpus OEM légitimement détenu, analyser les chaînes `DMR_CALL_START`, `VOCODER_IO_SET`, `CHAN_D`, `I2C_OPERATION`, ainsi que les références de code et la table d'identifiants HPI ; confronter aux journaux du banc. Capturer au moins trois scénarios distincts : RX DMR, enregistrement et lecture d'un message enregistré. Pour chacun, consigner le nombre de trames, leur payload, la variante de firmware, la réponse HOBIB et les interruptions. La définition du protocole ne doit être publiée comme **validée OEM D578** qu'après rattachement effectif à une trace V1.21.

**Références primaires externes :** [CT3258 datasheet](https://cdn.hackaday.io/files/1642237026116832/CT3258_datasheet.pdf) ; [SCT3258 v2.0](https://cdn.hackaday.io/files/1642237026116832/SCT3258_datasheet_v2_0.pdf) ; [Packet Interface CT3258 v1.0](https://cdn.hackaday.io/files/1642237026116832/CT3258_Packet_Interface.pdf) ; [CML SCT3258TD](https://www.cmlmicro.com/products/sct3258td-dmr-dpmr-analog-processor/). Les PDF sont liés et non réhébergés faute de licence explicite.
