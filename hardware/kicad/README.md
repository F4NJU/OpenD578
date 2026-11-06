# KiCad : reconstruction de brochage, PAS le schema AnyTone original

Fichiers **nouveaux**, reconstruits le 05/11/2026 a partir de la datasheet GigaDevice.
Ils ne remplacent pas le fichier historique `D578_GD32_Brochage_KiCad_V0_3.zip`, dont les octets originaux sont indisponibles.

- `.kicad_sym` : 100 broches physiques de l'encombrement GD32F303VKT6 LQFP100, regroupement de symboles par numero pour la lisibilite.
- `.kicad_sch` : feuille **sans aucun fil**, une reference de brochage uniquement.
- `../pinmaps/GD32F303VKT6_LQFP100_REFERENCE.csv` : hypothese de fonction par broche et provenance.

Les fichiers ont ete controles lexicalement et par nombre de broches, mais **pas ouverts dans KiCad dans cette session** ; avant modification, les ouvrir dans la version locale de KiCad et verifier l'affichage.

Datasheet : https://www.gd32mcu.com/data/documents/datasheet/GD32F303xx_Datasheet_Rev3.0.pdf ; section 2.6.2 / Table 2-5.
