#!/usr/bin/env python3
"""Produce a full datasheet pin list and an UNCONNECTED KiCad reconstruction.

No OEM netlist is claimed. All PCB signal allocations are hypotheses or
firmware/bench inferences: read the CSV evidence column before connecting.
"""
import csv
import json
import uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
# Physical pin order for GD32F303Vx LQFP100; GD32F303xx Datasheet Table 2-5.
NAMES='''PE2 PE3 PE4 PE5 PE6 VBAT PC13 PC14 PC15 VSS_5 VDD_5 OSC_IN OSC_OUT NRST PC0 PC1 PC2 PC3 VSSA VREF- VREF+ VDDA PA0 PA1 PA2 PA3 VSS_4 VDD_4 PA4 PA5 PA6 PA7 PC4 PC5 PB0 PB1 PB2 PE7 PE8 PE9 PE10 PE11 PE12 PE13 PE14 PE15 PB10 PB11 VSS_1 VDD_1 PB12 PB13 PB14 PB15 PD8 PD9 PD10 PD11 PD12 PD13 PD14 PD15 PC6 PC7 PC8 PC9 PA8 PA9 PA10 PA11 PA12 PA13 NC VSS_2 VDD_2 PA14 PA15 PC10 PC11 PC12 PD0 PD1 PD2 PD3 PD4 PD5 PD6 PD7 PB3 PB4 PB5 PB6 PB7 BOOT0 PB8 PB9 PE0 PE1 VSS_3 VDD_3'''.split()
assert len(NAMES)==100, len(NAMES)

# Each assignment is a claim tagged by its evidence, not an electrical net.
ANNO={
 'VBAT':('RTC backup supply candidate','datasheet only; external D578 backup location; continuity TBD'),
 'PC14':('RTC low-speed crystal candidate','datasheet AF only; no PCB oscillator identified'),
 'PC15':('RTC low-speed crystal candidate','datasheet AF only; no PCB oscillator identified'),
 'PA0':('POWER button','user board observation plus OEM GPIO model'),
 'PA1':('Rotary encoder push','OEM trace/model; continuity TBD'),
 'PC8':('Encoder phase A candidate','OEM trace/model; continuity TBD'),
 'PC9':('Encoder phase B candidate','OEM trace/model; continuity TBD'),
 'PC2':('Volume ADC12 candidate','OEM ADC trace/model'),
 'PC5':('Volume ADC15 candidate','OEM ADC trace/model'),
 'PB0':('Front key resistor ladder candidate ADC8','OEM ADC trace/model'),
 'PB1':('Front key resistor ladder candidate ADC9','OEM ADC trace/model'),
 'PA9':('USART0 TX microphone','OEM trace/model; connector continuity TBD'),
 'PA10':('USART0 RX microphone','OEM trace/model; connector continuity TBD'),
 'PA11':('USB DM alternate function','datasheet; board route inferred from USB CDC'),
 'PA12':('USB DP alternate function','datasheet; board route inferred from USB CDC'),
 'PA13':('SWDIO','physical SWD access confirmed'),
 'PA14':('SWCLK','physical SWD access confirmed'),
 'PA15':('SPI NAND SO1 candidate','OEM bit-bang + bench; continuity TBD'),
 'PB8':('SPI NAND CS# candidate','OEM bit-bang + bench; continuity TBD'),
 'PB15':('SPI NAND CLK candidate','OEM bit-bang + bench; continuity TBD'),
 'PB14':('SPI NAND SO0 candidate','OEM bit-bang + bench; continuity TBD'),
 'PD2':('SCT3258 HCSN','OEM GPIO HPI simulation; continuity TBD'),
 'PD3':('SCT3258 HWRN','OEM GPIO HPI simulation; continuity TBD'),
 'PD4':('SCT3258 HRDN','OEM GPIO HPI simulation; continuity TBD'),
 'PD5':('SCT3258 HOBIB candidate','OEM GPIO HPI simulation; continuity TBD'),
 'PB3':('RF CLK / shared GPIO candidate','RF GPIO model; conflicting other role; continuity TBD'),
 'PB4':('RF DATA / shared GPIO candidate','RF GPIO model; conflicting other role; continuity TBD'),
 'PB5':('RF CS bank0 candidate','RF GPIO model; board chip unknown'),
 'PB2':('RF CS bank1 candidate','RF GPIO model; board chip unknown'),
 'PC13':('RF CS bank2 candidate / RTC tamp alternate','RF GPIO model; multiple roles; continuity TBD'),
 'PE1':('RF CS bank3 candidate','RF GPIO model; board chip unknown'),
 'PB6':('RDA5802 I2C SCL candidate','FM I2C simulation; continuity TBD'),
 'PB7':('RDA5802 I2C SDA candidate','FM I2C simulation; continuity TBD'),
 'PC10':('UART3 TX possible Bluetooth','datasheet alternate function; exact OEM mux not confirmed here'),
 'PC11':('UART3 RX possible Bluetooth','datasheet alternate function; exact OEM mux not confirmed here'),
 'PA7':('Radio speaker gate GPIO','OEM Speaker Mode trace; continuity TBD'),
 'PE3':('Radio LED / keypad LED bus candidate','OEM trace; physical target TBD'),
 'PE4':('Radio LED / keypad LED bus candidate','OEM trace; physical target TBD'),
}
for n in range(8,16):
 ANNO[f'PD{n}']=(f'SCT3258 HPI data bit {n-8}','OEM GPIO HPI simulation; continuity TBD')
for n in range(7,15):
 ANNO[f'PE{n}']=(f'LCD D{n-7} candidate','OEM 8080 GPIO trace; LCD pad continuity TBD')
for name,label in {'PB10':'LCD WR# candidate','PB11':'LCD D/C candidate','PB12':'LCD RESET# candidate','PB13':'LCD CS# candidate'}.items():
 ANNO[name]=(label,'OEM 8080 GPIO trace; LCD pad continuity TBD')

# Canonical firmware-resolved signals, including N14 APRS RX PLUS.
resolved_path=ROOT/'docs/hardware/io/TABLEAU_IO_D578.json'
resolved={r['Signal GD32']:r for r in json.loads(resolved_path.read_text())}
for signal,row in resolved.items():
 ANNO[signal]=(row['Fonction du signal distant'],row['Validation']+'; '+row['Preuves']+'; '+row['Précision restante'])

pinmap=ROOT/'hardware/pinmaps/GD32F303VKT6_LQFP100_REFERENCE.csv'
pinmap.parent.mkdir(parents=True,exist_ok=True)
with pinmap.open('w',newline='',encoding='utf8') as f:
 w=csv.writer(f,lineterminator="\n")
 w.writerow(['physical_pin','gd32_pin','board_signal_candidate','claim_level','provenance'])
 for number,name in enumerate(NAMES,1):
  net,proof=ANNO.get(name,('Not traced','No board signal claimed'))
  level=resolved[name]['Validation'] if name in resolved else 'unmapped' if name not in ANNO else ('physical' if name in ('PA13','PA14') else 'datasheet_and_external' if name=='VBAT' else 'oem_or_emulator_candidate')
  w.writerow([number,name,net,level,proof.rstrip()])

# KiCad symbol with all 100 pins. Pins are deliberately NOT connected in the
# schematic, so this is a schematic-level pin reference only, never a PCB netlist.
def U():return str(uuid.uuid4())
def prop(name,val,x,y):
 return f'(property "{name}" "{val}" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27))))'
def fx():return '(effects (font (size 1.0 1.0)))'
# Symbol units grouped (not literal package sides); ensure 2.54mm pitch.
rect='(rectangle (start -33.02 68.58) (end 33.02 -68.58) (stroke (width 0.254) (type default)) (fill (type background)))'
pins=[]
for i,name in enumerate(NAMES,1):
 idx=(i-1)%50
 yy=62.23-idx*2.54
 left=i<=50
 xx=-38.10 if left else 38.10
 angle=0 if left else 180
 ppt='power_in' if name.startswith(('VSS','VDD','VDDA','VSSA','VREF','VBAT')) else 'no_connect' if name=='NC' else 'bidirectional'
 pins.append(f'(pin {ppt} line (at {xx:.2f} {yy:.2f} {angle}) (length 5.08) (name "{name}" {fx()}) (number "{i}" {fx()}))')
lib='\n'.join([
 '(symbol "OpenD578:GD32F303VKT6"',
 '(pin_names (offset 0.51)) (in_bom yes) (on_board yes)',
 prop('Reference','U',0,75.0),prop('Value','GD32F303VKT6',0,-75.0),
 f'(symbol "GD32F303VKT6_0_1" {rect})',
 '(symbol "GD32F303VKT6_1_1"',*pins,')',')'])
# Full self-contained symbol library; sheet links to it (pinout only, no nets).
symfile=ROOT/'hardware/kicad/OpenD578_GD32F303VKT6_RECONSTITUE.kicad_sym'
symfile.parent.mkdir(parents=True,exist_ok=True)
symfile.write_text('(kicad_symbol_lib (version 20211014) (generator kicad_symbol_editor)\n'+lib+'\n)\n',encoding='utf8')

sheetid=U();symbol_id=U()
parts=['(kicad_sch (version 20230121) (generator "eeschema")',f'(uuid "{sheetid}")','(paper "A3")',
 '(title_block (title "OpenD578 GD32F303VKT6 - BROCHAGE RECONSTITUE / PAS DE NETLISTE") (date "2026-11-05") (rev "0.4"))',
 '(lib_symbols',lib,')',
 '(text "RECONSTRUCTION: pinout du composant selon datasheet; liaisons firmware qualifiees dans le tableau IO ; cette feuille ne comporte aucun fil. NE PAS FABRIQUER DE PCB A PARTIR DE CE FICHIER." (at 30 20 0) (effects (font (size 1.3 1.3)) (justify left bottom)) (uuid "'+U()+'"))',
 '(symbol (lib_id "OpenD578:GD32F303VKT6") (at 190.5 150 0) (unit 1) (in_bom yes) (on_board yes) (dnp no)',f'(uuid "{symbol_id}")',
 prop('Reference','U1',190.5,77.0),prop('Value','GD32F303VKT6',190.5,226.0)]
for i in range(1,101):parts.append(f'(pin "{i}" (uuid "{U()}"))')
parts += [f'(instances (project "OpenD578_GD32F303VKT6_RECONSTITUE" (path "/{sheetid}" (reference "U1") (unit 1))))',')',')']
sheet=ROOT/'hardware/kicad/OpenD578_GD32F303VKT6_RECONSTITUE.kicad_sch'
sheet.write_text('\n'.join(parts)+'\n',encoding='utf8')

README=ROOT/'hardware/kicad/README.md'
README.write_text('''# KiCad : reconstruction de brochage, PAS le schema AnyTone original\n\nFichiers **nouveaux**, reconstruits le 05/11/2026 a partir de la datasheet GigaDevice.\nIls ne remplacent pas le fichier historique `D578_GD32_Brochage_KiCad_V0_3.zip`, dont les octets originaux sont indisponibles.\n\n- `.kicad_sym` : 100 broches physiques de l\'encombrement GD32F303VKT6 LQFP100, regroupement de symboles par numero pour la lisibilite.\n- `.kicad_sch` : feuille **sans aucun fil**, une reference de brochage uniquement.\n- `../pinmaps/GD32F303VKT6_LQFP100_REFERENCE.csv` : fonction par broche, statut de validation et provenance ; voir le tableau IO resolu.\n\nLes fichiers ont ete controles lexicalement et par nombre de broches, mais **pas ouverts dans KiCad dans cette session** ; avant modification, les ouvrir dans la version locale de KiCad et verifier l\'affichage.\n\nDatasheet : https://www.gd32mcu.com/data/documents/datasheet/GD32F303xx_Datasheet_Rev3.0.pdf ; section 2.6.2 / Table 2-5.\n''',encoding='utf8')
print('CSV',pinmap,'Symbol',symfile,'Schematic',sheet,'100 pins',len(pins))
