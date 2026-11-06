# Références externes, URL complètes et portée de chacune

Ce document enregistre les liens explicitement utilisés ou fournis dans les travaux du projet. `01_INDEX_MACHINE/urls_by_source.jsonl` conserve également les occurrences et lignes des liens présents dans les textes exportés. **Un lien historisé n'est pas un fichier joint; sa disponibilité peut changer.**

## Photographies et documents FCC

- `https://fccid.io/T4K-D578UV/Internal-Photos/Internal-Photos-4513250` : lien donné par l'utilisateur pour les photos internes du D578UV. Peut aider à reconnaître les circuits et connexions; aucune preuve de correspondance de PCB avec la révision précise GD32 V1.21 sans examen visuel et continuité.
- `https://fccid.io/T4K-D578UV/Internal-Photos/Internal-Photos-4513168` : autre document d'images internes référencé par la FCC (soumission 2019). N'est pas un schéma d'ingénierie du D578UV PRO GD32 V1.21.
- `https://fccid.io/T4K-D578UVIII/` : variante FCC D578UVIII demandée par l'utilisateur; prudence sur version, révision, options de la carte et nomenclature.
- `https://fccid.io/T4K-D578UV` : page FCC de l'appareil original, avec photos et autres pièces. Certaines entrées « Schematics » apparaissent comme métadonnées non nécessairement accessibles; ne pas affirmer l'obtention d'un schematic complet du PRO GD32.

## Constructeurs, silicium, mémoire, ADC et instructions ARM

- `https://www.gigadevice.com/product/mcu/mcus-product-selector/gd32f303vkt6` : fabricant du MCU, Cortex-M4, 3072 K Flash, 96 K SRAM, LQFP100. Sert à valider les capacités de silicium, pas les allocations OEM.
- `https://www.gd32mcu.com/data/documents/userManual/GD32F30x_User_Manual_Rev3.0.pdf` : manuel de la famille GD32F30x exploité pour RCU, PLL, GPIO, ADC, DMA, EXTI et Power. La révision du manuel peut changer.
- `https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/305/KIOXIA_TC58CVG1S3HRAIG_Rev2.0_E191001.pdf` : commandes ECC/READ/DUAL READ et géométrie NAND. Comparer la révision et les registres A0/B0 aux bits observés.
- `https://www.ti.com/product/TLV320AIC3204` : TLV320AIC3204 codec audio (ADC et DAC de son, I2C/SPI et I2S), distinct de l'ADC0 GD32 rencontré dans le simulateur.
- `https://www.ti.com/lit/ds/symlink/tlv320aic3204.pdf` : datasheet du codec audio TI.
- `https://developer.arm.com/documentation/dui0553/latest/` : Cortex-M4 Generic User Guide, SysTick, exception, bit-band.
- `https://support.arm.com/documentation/dui0589/a/Cihhdahf` : convention de démarrage `__user_initial_stackheap` / usage de pile et tas.
- `https://github.com/unicorn-engine/unicorn/blob/master/docs/FAQ.md` : Unicorn, moteur d'émulation CPU utilisé par les simulations V1-V3.

## OpenGD77, outils de codeplug, mises à jour

- `https://github.com/hmatuschek/qdmr` : documentation et parseur de codeplug AnyTone; position `+0x23` du nom dans le record 64 octets. **Ne prouve pas le layout RAM OEM.**
- `https://support.bridgecomsystems.com/hubfs/Tech%20%28AnyTone%29/AT-D578UV%20Plus/Change%20Log%20-%20D578UVII%20FW_CPS.pdf` : changelog D578UVII PLUS évoquant la priorité d'affichage APRS. Cette branche n'est pas la cible GD PRO V1.21.
- `https://github.com/rogerclarkmelbourne/OpenGD77` : dépôt amont historique OpenGD77; vérifier sa licence et la variante exacte des sources réutilisées dans les ZIP du projet.

## Modifications communautaires, pistes et avertissements de compatibilité

- `https://drive.google.com/file/d/1AWclJteohBylg1gUwj2iR3yqC0S3iUQ2/view?usp=sharing` : mod D578UV **non PLUS** V1.16n (VK7ZJA), **pas** une image compatible V1.21 sans preuve.
- `https://sabercathost.com/ef8d/D578UV_V1.16n_mod_FW.zip` : miroir V1.16n, disponibilité non garantie.
- `https://drive.google.com/file/d/1k9OuyAKKwtTWT8agvGmVLQ6Xs0IW8UTu/view?usp=sharing` : mod D578UV-II PLUS V2.03n, **autre branche**.
- `https://sabercathost.com/ef8e/D578UVII_V2.03n_mod_FW.zip` : miroir du mod V2.03n.
- `https://my.hidrive.com/share/pct1kt-nc2` : pack alternatif DL6EK, contenu/compatibilité non confirmés ici.
- `https://hamradiosouthernrepeaters.co.uk/images/578Mods/578techmods.html` : documentation communautaire VK7ZJA, source d'indices et non preuve de récupération V1.21.

## Méthode de comparaison de ces liens

Pour toute nouvelle image récupérée, relever taille, SHA-256, modèle de radio, famille MCU, version exacte, base de chargement, enveloppe `.spi/.CDI/.CDD`; ne comparer les patches qu'à l'image stock du **même modèle et même release**. Une modification de tables (par exemple 386 octets sur une ancienne comparaison d'image V1.21) ne démontre pas comment injecter le moteur satellite, ni comment acquérir l'écran ou déclencher un setter radio.
