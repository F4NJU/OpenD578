# RadioFoundry : comparaison contrôlée avec OpenD578

Cette revue conserve les résultats techniques publiés dans [RadioFoundry, Anytone hardware](https://radiofoundry.org/docs/spec/hardware-anytone), **sans recopier intégralement le texte d'un tiers** et sans effacer notre recherche du firmware constructeur D578 GD32 V1.21. RadioFoundry constitue une référence technique sérieuse, à rapprocher des observations OEM pour donner une validation propre à notre révision.

## Accès aux analyses

- [Audit des 129 affirmations de la source, une par une](AUDIT_AFFIRMATIONS.md) : section, valeur rapportée, correspondance OpenD578, catégorie de preuve, notes de variante.
- [Registre CSV exploitable](AUDIT_AFFIRMATIONS.csv) et [JSON](AUDIT_AFFIRMATIONS.json) : archivage, filtres et futurs rapprochements automatiques.
- [SCT3258 : boot, HPI, CHAN_D, vocoder et codec](SCT3258_CHAND_BOOT_ET_CODEC.md) : nouveaux champs détaillés et implications d'un transfert vocal vers MCU.
- [Cartographie GPIO : D868 contre notre D578](GPIO_868_VS_578.md) : différences majeures, dont clavier, DAC, RF et LCD.
- [Calibrations et NAND par modèle](CALIBRATIONS_ET_VARIANTES.md) : ne pas importer des offsets propres au D868 dans la NAND du D578.
- [Firmware, CPS, CDD et bootloader](FIRMWARE_MISE_A_JOUR.md) : mise à jour, emplacements flash, USB CDC et compatibilité.

## Hiérarchie de preuves utilisée

Le GPIO, la trame et la fonction exécutés dans le firmware OEM et reproduits dans notre banc sont **validés dans le périmètre de cette exécution**. Une référence de composant relevée sur le PCB est un fait physique pour la carte relevée. Les analyses RadioFoundry de firmware sont conservées avec leurs champs exacts et leur modèle cible. Une information issue de **D868** ne doit pas remplacer une observation **D578**. Les propositions d'architecture future sont documentées, sans devenir de fausses fonctionnalités présentes.

**Attention aux contradictions de génération :** nos D578 PRO et PLUS ont le GD32F303 ; une carte AT32 d'une autre série ne doit pas changer la documentation de nos appareils. Le bootloader **24 Kio à `0x08000000` et application à `0x08006000`** du PRO GD32 V1.21 prévaut sur le boot 16 Kio indiqué pour des portables. La source décrit un mécanisme `CHAN_D` qui interdit de conclure prématurément à l'impossibilité d'un transfert vocal vers le MCU.

## Éléments restant à confronter à V1.21

- Calcul du SHA-256 du bloc SCT 2 048 octets sur la **copie locale légitime** de la V1.21 et comparaison avec le hash source, sans inclusion des octets dans GitHub.
- Localisation et valeurs des commandes `VOCODER_IO_SET`, `CHAN_D`, `CODEC_SELECT` et `I2C_OPERATION` dans les routines OEM propres au PRO V1.21.
- Décomposition précise et temporisation des charges vocales `CHAN_D` ; preuve d'une capacité temps réel éventuelle, pas simple existence d'enregistrement.
- Correspondance des réglages calibrations NAND D578 → DAC/BH2226FV/QA4818N/SCT3258, sans transférer les tables de puissance D868.
- Séquence de chargement `UPDATE` du bootloader 24 Kio, séparée de la programmation `PROGRAM/R/W/END` du CPS.

Les trois PDF Sicomm diffusés sur Hackaday sont référencés dans la [fiche SCT3258](SCT3258_CHAND_BOOT_ET_CODEC.md), mais non redistribués : leur licence n'est pas documentée. La section 2.3 de la page RadioFoundry demande encore une vérification intégrale de transcription du protocole de paquets ; elle est marquée comme telle dans le registre des affirmations.
