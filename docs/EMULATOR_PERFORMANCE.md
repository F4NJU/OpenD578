# V11.2 interactive OEM bench

The first interactive bench spent much of its host time calling Python for each
GPIO access, polling peripherals and publishing files. V11.2 keeps the reference
paths and adds an optional native dispatcher for LCD pins and the data phase of
captured NAND Dual-SPI reads. The ARM program still executes. It generates the
screen contents and sends the bytes; the dispatcher does not replace an OEM
menu, text renderer or drawing routine.

The source-only repository contains the native C sources and build scripts.
Manufacturer images, captures and OEM ready-state recordings remain local
inputs. For the legacy web bench, supply an authenticated recording or choose
application reset. The independent hardware-mode contract program still needs
none of these inputs.

## Host changes

- Commands pass through the worker's standard-input pipe rather than creating
  a file for every click. Stop uses this channel too.
- Short front-key transitions are queued in order. Their minimum modeled pulse
  is 400 ms for ADC keys and 75 ms for the encoder push. Explicit release-all
  cancels the queue. Microphone PTT release is immediate.
- ADC conversions without interrupts are batched at their original instruction
  deadlines. CPU accesses to the destination synchronize the DMA. Finite or
  varying input profiles, enabled ADC/DMA interrupts and RAM observation use
  the reference schedule.
- Timer and RTC deadlines replace repeated polling when possible. Pending
  Cortex exceptions are checked at interrupt-unmasking boundaries. The native
  gate tests current mask registers before entering Python.
- A cached RGB framebuffer avoids reconverting the complete pixel dictionary
  on every publication. Image and status publication tolerate short reader
  locks. The hardware table is refreshed when its tab is visible.
- The last source-folder choice is retained locally. Already installed pinned
  dependencies no longer trigger pip on every launch.

Detailed tracing disables the native bus shortcut. `--no-native-lcd` also selects
the existing Python bus implementations while retaining other interactive
settings. An unsupported bus operation goes through the original model and
remains an explicit boundary.

## Executed checks

On Linux x86_64, native and Python bus dispatch produced identical CPU registers,
SRAM, LCD pixels/commands, MMIO counts, NAND read checks, timers, RTC, UART, RF and
DSP-protocol state after a four-million-instruction MENU scenario. The reference
Python and native instruction engines also matched for the executed
500,000-instruction scenario. These are bounded regressions, not a proof of
cycle accuracy or complete firmware coverage.

A local HTTP exercise opened MENU, returned through EXIT, opened and closed the
FM audio gate, and stopped the worker through the control pipe. Recorded command
receipt was about 0.1–0.2 s and FM gate opening about 0.5 s on the test host. Full
menu drawing remained several seconds. Host load and scenario timing affect
these measurements; the emulator still does not run at physical radio speed.
The exact recorded measurements are in `validation_v11_2.json`.

Windows x86_64 DLLs were cross-compiled for the private bench package. They have
not been executed on Windows in this validation. Build native libraries for
other host architectures; Python reference mode remains available.

## Clock and alignment observations

The user confirmed a 12.00 MHz HXTAL. Observed `RCU_CFG0=0x0021840A` and
`RCU_CFG1=0` decode to PLL ×10, HCLK 120 MHz, APB1 60 MHz and APB2 120 MHz for the
HD/XD device. The report distinguishes these register-derived frequencies from
the emulator's synthetic instruction timing.

Clock references:

- https://www.gd32mcu.com/data/documents/userManual/GD32F30x_User_Manual_Rev3.4.pdf
- https://github.com/CommunityGD32Cores/gd32-pio-spl-package/blob/main/gd32/cmsis/variants/gd32f30x/system_gd32f30x.c

The OEM bench can display the retained power-drive bytes read from
`0x20009411..0x20009414`, referenced by the native selector at `0x08065194`, and
the supply-measurement coefficient at `0x20009404`. These are raw controls, not
watts. Frequency trim, receiver gains and deviation are not fully mapped. The
previous P4+encoder experiment did not reach a confirmed TEST MODE screen.
Individual captured values remain private inputs.
