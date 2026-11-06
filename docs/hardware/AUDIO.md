# Audio externe, ADC et DAC

Ne pas confondre **ADC0 du GD32F303** (`0x40012400`, donnees `0x4001244C`) et le **codec ADC/DAC audio TLV320AIC3204**, dont la presence et le raccordement exacts sur cette revision restent a confirmer sur la carte.

Le circuit TLV320AIC3204 comporte des fonctions d'acquisition/restitution analogique et une interface audio numerique, mais son mode de controle effectivement utilise par OpenD578 n'est pas qualifie ici. Il faut identifier les pistes de controle (I2C/SPI), BCLK/WCLK/DIN/DOUT, sorties et entrees analogiques, alimentation et MCLK, ainsi que les parametres et offsets stockes dans les memoires.

Le menu *Speaker Mode* a fourni des observations distinctes : PA7 et bit 4 du registre RF banque 1/page 0/adresse `0x25`. Leur continuation jusqu'aux amplificateurs, les gains et le schema microphone sont encore a relever.

**Documentation :** [façade/ADC](../FACADE_GPIO_BOUTONS_CODEUR_VOLUMES_ET_ECLAIRAGES.md), [microphone et routage](../NOTICE_CHANGELOG_MICROPHONE_V11_8.md), [routines](../04_RAM_ROUTINES_UI_RF_ET_BROCHAGE.md), [datasheet TI](https://www.ti.com/product/TLV320AIC3204).

### Complément matériel

Consulter [VOLUME U2429G](VOLUME_U2429G.md) et [audit des fonctions partielles](AUDIT_FONCTIONS_PARTIELLES.md).
