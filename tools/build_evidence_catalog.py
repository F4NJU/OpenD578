#!/usr/bin/env python3
"""Build a machine-readable evidence ledger: no proprietary firmware inputs."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
records=[
 ('cpu-identity','PRO GD V1.21','GD32F303VKT6 Cortex-M4 LQFP100','USER_MEAS','docs/02_CPU_FLASH_BOOT_USB_SWD.md','https://www.gd32mcu.com/data/documents/datasheet/GD32F303xx_Datasheet_Rev3.0.pdf'),
 ('plus-cpu','PLUS','GD32F303 sur version PLUS observe par utilisateur','USER_PHOTO','docs/hardware/VERSIONS.md',''),
 ('cpu-vbat-pin','PRO GD V1.21','GD32F303Vx LQFP100 VBAT pin 6','DATASHEET','hardware/pinmaps/GD32F303VKT6_LQFP100_REFERENCE.csv','https://www.gd32mcu.com/data/documents/datasheet/GD32F303xx_Datasheet_Rev3.0.pdf'),
 ('rtc-backup','D578 historique','Sauvegarde sur face arriere PCB MCU pres de nappe, attribuee au RTC','THIRD_PARTY_BOARD','docs/hardware/SAUVEGARDE_RTC_GPS_XH414HG.md','https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php'),
 ('gnss-backup','D578 historique','Sauvegarde sur face avant entre potentiometres, attribuee au hot start GPS','THIRD_PARTY_BOARD','docs/hardware/SAUVEGARDE_RTC_GPS_XH414HG.md','https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php'),
 ('xh414hg-spec','Composant XH414HG','Seiko XH-HG capacitor 0.08 F et 3.3 V max, pas une pile lithium primaire','DATASHEET','docs/hardware/SAUVEGARDE_RTC_GPS_XH414HG.md','https://www.infinite-electronics.kr/datasheet/3c-XH414HG-IV01E.pdf'),
 ('ms412-historic','D578 historique','Edition ancienne du guide propose MS412: pas equivalent etabli au XH414HG','THIRD_PARTY_BOARD','docs/hardware/SAUVEGARDE_RTC_GPS_XH414HG.md','https://www.theweeks.org/tmp/FILES/Anytone-Mods/578mods.htm'),
 ('rtc-vbat-link','PRO et PLUS','Continuite sauvegarde RTC vers GD32 VBAT a verifier','INFERRED','docs/hardware/SAUVEGARDE_RTC_GPS_XH414HG.md',''),
 ('nand-geometry','PRO GD V1.21','TC58CVG1S3HRAIG 2Gbit, ID 98 CB, main 256 Mio','USER_MEAS','docs/03_NAND_LECTURES_ECC_CARTE.md','https://spiflash.readthedocs.io/en/latest/chips/98cb-nand.html'),
 ('nand-ecc','PRO GD V1.21','437 pages ECC 20 non corrigees lors de la capture, 10 pages non triviales','USER_MEAS','docs/03_NAND_LECTURES_ECC_CARTE.md',''),
 ('nand-gpio','PRO GD V1.21','PB8 PB15 PB14 PA15 bus NAND serie candidate dans simulation OEM','OEM_EMU','docs/peripherals/01_NAND_SPI_CABLAGE_PILOTE_FORMATS_MEMOIRE.md',''),
 ('main-flash-boot','PRO GD V1.21','Boot OEM 24576 B base 0x08000000 et app base 0x08006000','USER_MEAS','docs/02_CPU_FLASH_BOOT_USB_SWD.md',''),
 ('sct-hpi-gpio','PRO GD V1.21','PD2..PD5 controls, PD8..PD15 data HPI candidat','OEM_EMU','docs/peripherals/04_DMR_SCT3258_BOOTSTRAP_HPI_PAQUETS_CODEC_PARAMETRES.md',''),
 ('sct-boot','SCT3258 datasheet','1024 mots 16-bit / 2048 octets au boot SCT, hors firmware GD32','DATASHEET','docs/peripherals/04_DMR_SCT3258_BOOTSTRAP_HPI_PAQUETS_CODEC_PARAMETRES.md','https://radiofoundry.org/docs/spec/hardware-anytone'),
 ('lcd-8080','PRO GD V1.21','GPIO PE7..PE14 commandes LCD D0..D7 selon decode OEM','OEM_STATIC','docs/LCD_CABLAGE_PILOTAGE_ET_INTEGRATION_V11_8.md',''),
 ('qa-four','D578 historique','Quatre QA4818N, deux LO et deux recepteurs IF selon VK7ZJA','THIRD_PARTY_BOARD','docs/hardware/QA4818N_QUATRE_CIRCUITS_26MHZ.md','https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php'),
 ('qa-bus','PRO GD V1.21','Bus RF OEM du modele : PB3 SCLK, PB4 SDIO, CS PB5 PB2 PC13 PE1; quatre banques; 24 bits','OEM_EMU','docs/hardware/QA4818N_RECONSTRUCTION_REGISTRES_PLL_CHAINES_RX_TX.md',''),
 ('qa-frequency-format','AT1846S, comparaison','0x29[13:0]/0x2A[15:0] encodent F*16000 en MHz, soit 62,5 Hz par unite, non confirme pour QA4818N','DATASHEET','docs/hardware/QA4818N_RECONSTRUCTION_REGISTRES_PLL_CHAINES_RX_TX.md','https://manuals.plus/m/3c3831cb8a4faeacfd8c45ad662fb36c9ff3232018d83d1e7ece0938337cb578'),
 ('qa-lo-if','D578 historique','Deux LO et deux recepteurs FI avec filtres 38,550 et 38,850 MHz','THIRD_PARTY_BOARD','docs/hardware/QA4818N_RECONSTRUCTION_REGISTRES_PLL_CHAINES_RX_TX.md','https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php'),
 ('qa-mapping-unknown','PRO GD V1.21','Mapping des quatre banques au boitiers et aux voies A/B non mesure','INFERRED','docs/hardware/QA4818N_RECONSTRUCTION_REGISTRES_PLL_CHAINES_RX_TX.md',''),
 ('qa-tx-not-qualified','PRO GD V1.21','TX et PLL QA4818N non valides materiellement ; seul codage/banc simulable','INFERRED','docs/hardware/QA4818N_RECONSTRUCTION_REGISTRES_PLL_CHAINES_RX_TX.md',''),
 ('qa-26','PRO GD V1.21','Un circuit gratte voisin oscillateur marque 26.00 observe par utilisateur','USER_PHOTO','docs/hardware/QA4818N_QUATRE_CIRCUITS_26MHZ.md',''),
 ('if-third','D578 historique','Empreintes 3e FI et filtres supplementaires non peuples','THIRD_PARTY_BOARD','docs/hardware/ETAGES_RF_PROTECTION_FI.md','https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php'),
 ('rf-protection','D578 historique','Relais et diode de protection inversion polarite','THIRD_PARTY_BOARD','docs/hardware/ETAGES_RF_PROTECTION_FI.md','https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php'),
 ('dac-h2226','PRO GD V1.21','Marquage H2226 sur SSOP-B16 -> BH2226FV-E2','USER_PHOTO','docs/hardware/BH2226_H2226_DAC_RF.md','https://www.rohm.com/products/data-converter/d-a-converters/8bit-d-a/bh2226fv-product'),
 ('dac-varicaps','PRO GD V1.21','BH2226FV pilotage varicaps reste une hypothese non tracee','INFERRED','docs/hardware/ETAGES_RF_PROTECTION_FI.md',''),
 ('fm-rda','PRO GD V1.21','RDA5802N identifie par utilisateur, adresse I2C 0x10 dans modele PB6/PB7','OEM_EMU','docs/hardware/RDA5802N_RECEPTION_FM.md',''),
 ('cps-program','D578UV OEM','PROGRAM -> QX 06, identification, lecture R 16 octets adresse 32-bit BE','THIRD_PARTY_BOARD','docs/evidence/CPS_QDMR_CAPTURE_DE_REFERENCE.md','https://static.dm3mat.de/qdmr/manual/ch08.html'),
 ('cps-writing','PRO GD V1.21 banc','Ecriture W 16 et END simules ; ACK ne prouve pas persistance','OEM_EMU','docs/cps/PROTOCOLE_OEM_V121.md',''),
 ('sat-no-go','PRO GD V1.21','Phase60 EXP06 hors ligne non flashable ; OEM ABI et recovery non qualifiees','OEM_STATIC','docs/05_SATELLITE_CODE_INTEGRATION_EXP06.md',''),
 ('bt-et12','PRO GD V1.21 banc','Dialogue ET12 sur UART3 modelise, aucune preuve de pinout physique D868BT-SP','OEM_EMU','docs/hardware/BLUETOOTH_D868BT_SP_ET12.md',''),
 ('cps-linux-current','Toutes variantes, tiers','AnyTone_CPS archive et CodeplugStudio est le developpement maintenu','THIRD_PARTY_BOARD','docs/evidence/SOURCES_EXTERNES_RECROISEES_20261105.md','https://github.com/hardenedpenguin/AnyTone_CPS'),
 ('plus-cps2','PLUS tiers','AesApp WebCPS documente l identification D578UV2 pour certains PLUS firmware 2.xx','THIRD_PARTY_BOARD','docs/evidence/SOURCES_EXTERNES_RECROISEES_20261105.md','https://cps.aes.app/manual/en/about'),
 ('micro-uart','PRO GD V1.21','Microphone USART0 PA9/PA10, trames 41/53 dans bench V11.8','OEM_EMU','docs/NOTICE_CHANGELOG_MICROPHONE_V11_8.md',''),
]
claims=[dict(id=i,variant=v,statement=s,evidence_type=e,local_reference=local,external_reference=ext or None,verification='needs_physical_measurement' if e=='INFERRED' else 'documented') for i,v,s,e,local,ext in records]
out=ROOT/'docs/evidence/CLAIMS.json'
out.write_text(json.dumps({'schema_version':1,'updated':'2026-11-05','notes':'This is an evidence index, not measured PCB netlist. External sources remain linked, not copied.','claims':claims},indent=2,ensure_ascii=False)+'\n',encoding='utf8')
print('claims=',len(claims))
