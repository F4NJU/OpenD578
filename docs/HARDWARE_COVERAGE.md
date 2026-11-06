V11.5 update: CDC host enumeration, COM/PTY transport and an optional NAND
checkpoint are documented in [USB_CPS_V11_5.md](USB_CPS_V11_5.md).
The V11.3 baseline and its original tests follow below.

# V11.3: experimental firmware and remaining board coverage

The web bench now exposes the independent hardware runner. Uploading a binary
selects this mode. It reads GPIO/register transactions without V1.21 function
addresses, signature anchors or OEM SRAM interpretations. Executable SRAM and
all physically mapped Flash remain available after a valid vector handoff.

This is a model of the known D578 board, not a guarantee that every possible
program or peripheral mode is supported. Having a component's binary does not
by itself provide a working emulator of its internal CPU, registers or timing.

## Selecting a run

Choose **Matériel · firmware expérimental** and the uploaded image. Use a
synthetic blank NAND when testing an original standalone driver. Choose captured
NAND when the program needs the original memories, fonts or alignment records.
Captured NAND inputs stay read-only; program/erase operations use volatile pages.

Raw images normally start at `0x08006000`; the placement selector also accepts
`0x08000000`. A full 3 MiB image normally uses the application vectors at
`0x08006000`; bootloader reset selects vectors at `0x08000000`. Ambiguous raw
images require the correct explicit load address. No historical RAM allocation
is used as an execution or data boundary.

The OEM analysis mode and its authenticated ready recording remain available.
Its RAM labels and function hooks are not silently applied to another image.
Hardware-mode supply inputs are raw ADC samples: the OEM inverse voltage
conversion is deliberately not assumed for a new firmware.

## Implemented and unimplemented behavior

| Part | Available | Remaining limits |
| --- | --- | --- |
| MCU / memory | Cortex-M4 instruction execution, physical Flash/alias and 96 KiB SRAM, executable SRAM, basic thread/handler contexts | Nested/FP exceptions, SVC integration, all Flash program/erase modes and alias synchronization |
| GPIO / inputs | Pin-level LCD, NAND, RF and serial-control interactions; front keys, encoder and Power; EXTI and software-pended interrupts | Complete electrical pull/load behavior and all alternate functions |
| Sleep | WFI wait and resumable external interrupts; modeled SysTick/timer/UART wake deadlines; software event input | All deep-sleep clock domains and event-register edge cases |
| Clock / RTC / timers | Known RCU registers, ideal oscillator readiness, known timers and backup registers | Cycle-accurate instruction timing and every timer mode |
| ADC / DMA | Regular ADC0 scan and DMA0 channel 0, synthetic inputs and verified writes, batched with destination synchronization | Other DMA engines/channels, injected conversions and all ADC interrupt modes |
| LCD / lighting | Actual controller commands and pixels from GPIO edges; lighting register transactions | Measured electrical/color characteristics |
| NAND | Captured or synthetic backing, commands, volatile program/erase, captured ECC status | Analog cell behavior, generated ECC parity, raw/special read modes |
| RF banks | Digital register transactions and synthetic carrier/CTCSS/RSSI/noise status | RF/PLL analog behavior, frequency-selective signals, calibrated watts and DMR demodulation |
| UART / GPS / microphone | Scheduled raw RX bytes, transmit and interrupts; synthetic PMTK/NMEA and microphone frames | Internal GPS/BT/microphone MCU firmware execution and every command |
| USB | Virtual CONNECT/RESET/SETUP/OUT/IN tokens, single-buffer PMA, ACK/NAK/STALL and low-priority IRQ20 | Real host/device passthrough, a full host stack, CPS protocol, isochronous/double-buffer endpoints |
| SCT3258 | Explicit bootstrap contract and documented HPI control/codec packets | DSP and AMBE firmware execution, voice/RF processing and unknown packet variants |
| AIC3204 | Known codec configuration packets/pages through the SCT path | PCM/I2S signal processing and analog audio |
| Watchdog / reset | FWDGT key/protection/prescaler/reload/feed and expiry; AIRCR reset requests | Automatic MCU restart; reset is a reported event, not a fabricated successful boot |
| APRS / DMR | Existing control paths and observable requests | Modulation DMA and waveforms, DMR/baseband execution |

## Performance and execution evidence

The native scheduler now also serves independent hardware mode. Its trap list
contains CPU sleep/event and interrupt-mask boundaries, not OEM function PCs.
It counts executed instructions and services modeled device deadlines. Hardware
mode keeps independent GPIO sampling; it does not enable the old native NAND
read shortcut that assumes the OEM helper's PC and R1 register.

Reference/native tests compare RAM and device state, including ADC DMA while
the CPU reads its destination. Original Thumb programs also exercise code at an
old OEM hook address, high/executable SRAM, WFI wake by SysTick/Power, and USB
SETUP delivered to a firmware interrupt handler. A live HTTP worker test checks
startup, screen state, coverage and stopping without manufacturer input files.

The example loop's host speed improvement is not a claim about full OEM boot,
RF processing speed or cycle accuracy. Optional block coverage adds overhead.

## Systematic routine review

`firmware_inventory.py` records vectors, direct BL candidates and literal values
in MCU peripheral regions. The current scan sees 3,343 candidate entries in the
captured full V1.21 Flash, and 3,042 in the V2.08 application. These inputs cover
different regions, and scans also encounter data. The counts are neither proven
functions nor a count of routines understood. Indirect calls, TBB/TBH, computed
addresses and code/data separation still need dedicated analysis.

`--coverage` records entered Unicorn translation blocks. It does not claim that
every instruction in a translated block completed: MMIO or an exception may
stop a block partway through. The UI exports the run report and selected-image
inventory for targeted follow-up of actual model boundaries.

```sh
python bench/run_hardware.py experimental.bin --engine native --coverage
python bench/firmware_inventory.py experimental.bin --out inventory.json
```

## Power-cycle findings

The OEM Power-off scenario previously stopped when SCT HRDN was strobed with an
empty FIFO even though the CPU did not sample its data bus. The model now defers
that boundary until a real input-register sample; an empty control strobe is
recorded. Unknown packets and empty data samples still stop explicitly.

With that change, the same Power-off execution reaches the MCU's free watchdog.
After implementing its registers and timing, this run reaches an explicit FWDGT
reset request at PC `0x0808A150`, instruction 68,396,285. Automatic reset/reboot
has not been implemented, and the complete Power-off/P4+dial/Power-on service
sequence is still unvalidated. Original calibration captures remain unchanged.

## Primary references

- GigaDevice GD32F30x User Manual Rev3.0, USBD/FWDGT/NVIC chapters:
  https://www.gd32mcu.com/data/documents/userManual/GD32F30x_User_Manual_Rev3.0.pdf
- Arm Cortex-M4 Devices Generic User Guide, basic exceptions and WFI/WFE:
  https://developer.arm.com/documentation/dui0553/latest/
- GigaDevice distributed USB driver implementation, for PMA geometry:
  https://github.com/CommunityGD32Cores/GD32Firmware/blob/main/GD32F30x/GD32F30x_usbd_library/usbd/Source/usbd_lld_core.c
