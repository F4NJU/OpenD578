# OpenD578

Experimental firmware research, a digital board emulator, and hardware
documentation for the **AnyTone AT-D578UV PRO with GD32 MCU**.

**Current status: research and emulator development. There is no installable
OpenD578 radio firmware release yet.** The original contract probe exercises
the emulator; it is not a replacement firmware or a file to flash to a radio.

The project starts with the D578. Other radios, including D878 variants, may
be investigated later; shared components do not establish compatibility.

## Release goals

| Stage | Target |
| --- | --- |
| Research | Publish the board findings, reproducible peripheral models and tests; continue the satellite integration work. |
| First usable version | A simple VFO, analog memories readable/writable from a PC, FM receive/transmit, CTCSS receive/transmit and **APRS transmission**, using the radio's retained calibration data. |
| Second stage | **APRS reception** and the DMR work needed for use with a local hotspot. |

DMR is an essential project goal. M17 is not a project target. The intended
operation should feel familiar to an OpenGD77 user, with a small VFO interface
for the first version. Importing OpenGD77 source requires checking the exact
upstream version and its license; no OpenGD77 firmware modules are bundled in
this initial repository.

## Emulator modes

| Mode | Purpose | Firmware dependencies |
| --- | --- | --- |
| `run_hardware.py` | Run a raw Cortex-M4 image against the known D578 peripheral subset | No OEM instruction-address hooks, no OEM RAM structures, no OEM startup snapshot. |
| `run_lcd.py` | Retain the V1.21-specific OEM analysis and regression bench | Requires the user's matching OEM files and captures; validates observation anchors. |

The hardware mode accepts a different program layout, a different stack
location inside physical SRAM, and code executed from SRAM. It samples the
GPIO buses without assuming the MCU uses a particular register or OEM helper
function. Unsupported peripheral behavior remains an explicit **model
boundary**. It is not reported as proof that a new firmware is faulty.

The physical memory map still matters: 3 MiB Flash, 96 KiB SRAM, and modeled
peripheral addresses. An image for another MCU or board is not automatically
compatible. The model is not cycle accurate and is not a physical RF test.

## Quick start: no manufacturer files required

Python 3.11 or newer:

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate
python -m pip install -r bench/requirements.txt
python -m unittest discover -s bench -v
python bench/contract_firmware.py work/contract.bin
python bench/run_hardware.py work/contract.bin --carrier match --instructions 12000 --out-dir work/contract
```

The original Thumb contract program draws two RGB565 pixels through GPIO,
writes and executes code near the top of SRAM, sends a radio-register write,
and samples synthetic carrier/CTCSS decoder states through GPIO. It contains
no manufacturer code. Tests also relocate it to the Flash origin and to an
address previously used by a V1.21 NAND observer.

To run a different raw application:

```bash
python bench/run_hardware.py path/to/application.bin --load-address 0x08006000 --instructions 100000 --out-dir work/my-image
```

The first two words must be an initial stack pointer and a Thumb reset vector.
`--load-address` identifies where the supplied vector table belongs. It defaults
to the application address; `0x08000000` can be used for an autonomous image.
Reports include the image hash, stop reason/category, peripherals and memory
access evidence. A synthetic erased NAND is used unless `--nand-dir` supplies
the user's authenticated capture.

## Known limits

- The DSP/AMBE program is not executed. PCM voice and DMR are not implemented.
- RF stimuli represent digital receiver/CTCSS status, not a demodulated waveform.
  They are not yet constrained by the programmed RF frequency.
- The APRS modulation DMA path is incomplete. The first usable version is a
  target, not a claim that APRS transmission already works in this emulator.
- LCD, serial, clocks, ADC/DMA, timers, NAND, flash and CPU exceptions implement
  explicit subsets. Nested/FPU exception frames and all Flash modes are not covered.
- The legacy accelerated engine has a known eight-instruction IRQ55 difference
  on one GPS scenario. Hardware mode currently uses the instruction observer.

See [the emulator design](docs/EMULATOR.md), [the roadmap](docs/ROADMAP.md),
[programming and calibration](docs/PROGRAMMING_AND_CALIBRATION.md),
[the research index](docs/RESEARCH_INDEX.md), and [the French introduction](README_FR.md).

## Contributions

Useful work includes peripheral traces, independent reproductions, GD32 radio
board identification, SCT3258 protocol work, and small regression tests for new
hardware behavior. Each finding should distinguish measurement, emulation,
static analysis and hypothesis. Include the firmware hash and board variant
when reporting a result. See [CONTRIBUTING.md](CONTRIBUTING.md).

Manufacturer firmware images, radio dumps, calibration data, codeplugs and
recorded OEM sessions are supplied locally by their users and are not part of
this repository. See [PROVENANCE.md](PROVENANCE.md).

Project initiated by **F4EGM**. Original OpenD578 code is licensed under
GPL-3.0-or-later; dependencies retain their own licenses.
