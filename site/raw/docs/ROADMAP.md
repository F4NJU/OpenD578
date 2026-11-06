# Project milestones

This is a development plan, not a list of currently implemented features.

| Milestone | Acceptance criteria |
| --- | --- |
| Public research base | Board findings, model limitations, hashes, references and reproducible source-only tests are available. |
| Firmware-independent bench | A program with no OEM code can use GPIO, LCD, ADC/DMA, serial and physical SRAM without V1.21-specific address checks. Peripherals not modeled produce explicit incomplete results. |
| Satellite integration | Identify current RF state and frequency setters; qualify UI ownership, runtime memory and restoration. Keep the calculation module separable from the OEM adapter. |
| First usable OpenD578 | A simple VFO and PC-programmable analog memories; FM RX and TX; independent RX/TX CTCSS; APRS **TX**; retained radio-specific calibration, power/fan control and reliable return to receive. Tested on the board after emulator qualification. |
| Second stage | APRS **RX** with a qualified digital audio path; DMR receive/transmit suitable for a local hotspot, using the SCT3258 appropriately. |

## First-version interface

Prefer an OpenGD77-like operating logic, with one visible VFO and configurable
RX/TX frequency and tone settings. Basic channel storage and PC programming are
required; elaborate on-radio zone management is not required for the first version.
Do not add another thread or a UI framework merely to reproduce
the arrangement of another radio's pixels.

## What remains before FM/APRS TX is usable

The present contract probe validates neither a synthesizer's physical frequency
nor an on-air transmission. Identify and verify frequency register conversions,
filter/PA selection, power calibration, audio routing, TX CTCSS and modulation.
Complete the relevant timer/DMA path for APRS TX. Receiver status injection alone
does not establish those functions.

The PC link must be exercised in the emulator: identify, read memories, write
memories, read back, restart and recover the same values. Keep programming writes
separate from board calibration; a channel upload must not overwrite alignment.
See [PROGRAMMING_AND_CALIBRATION.md](PROGRAMMING_AND_CALIBRATION.md).

DMR remains a required goal, even though the first usable version starts with
analog functions. APRS reception is explicitly scheduled after that first version.
M17 is not planned. D878 support would require its own board profile and evidence.

## Community work that can proceed independently

- Extend peripheral behavior with captured transactions and failure cases.
- Identify the exact silicon and electrical routes behind the radio GPIO banks.
- Document the SCT3258 bootstrap, packet protocol, codec commands and DMR events.
- Add frequency-aware synthetic inputs once the hardware frequency contract is known.
- Verify the legacy/native interrupt timing difference and exception edge cases.
- Extract reusable satellite calculations under compatible upstream licensing.

New functionality should have a bounded test and a documented hardware contract.
