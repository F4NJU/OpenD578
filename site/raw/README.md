# OpenD578

**Documentation GitHub Pages :** https://telectroboy.github.io/OpenD578/ (active après publication).

**[Centre de preuves (RTC, GPS, brochage 100 broches, monographies)](docs/evidence/INDEX.md)** : composants documentes, provenance, hypotheses de liaisons et mesures restantes. **[Changelog des nouvelles preuves](docs/CHANGELOG_PREUVES_RTC_GPS_20261105.md)**.

**[Programmation PC, USB et CPS](docs/cps/README.md)** : protocole OEM V1.21, codeplug, simulation CDC/COM, outils de lecture passive et tests.

**[Installation d’un dépôt GitHub neuf](docs/PUBLICATION_GITHUB_DEPOT_COMPLET.md)** et **[changelog de consolidation](docs/CHANGELOG_DEPOT_COMPLET_CPS_20261105.md)**.

Base logicielle publique : banc **V11.7**, accompagné des notices matériel/microphone/LCD **V11.8**. Les sources exécutables V11.8 complètes n’ont pas été récupérées pour ce paquet.


Experimental firmware research, a digital board emulator, and hardware
documentation for the **AnyTone AT-D578UV PRO with GD32 MCU**.

**Current status: research and emulator development. There is no installable
OpenD578 radio firmware release yet.** The original contract probe exercises
the emulator; it is not a replacement firmware or a file to flash to a radio.

The V11.7 bench adds an open qualification catalog (117 requirements), a firmware
clue scanner and JSON/JUnit reports. The 4 bounded regressions (including GPIO status-light outputs) are distinct
from full hardware qualification. Windows CPS reading was confirmed by the user;
channel-name persistence was checked with the integrated partial CPS. See
[qualification scope](docs/QUALIFICATION_ANALOGIQUE.md).

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

See [the emulator design](docs/EMULATOR.md), [V11.2 performance](docs/EMULATOR_PERFORMANCE.md), [the roadmap](docs/ROADMAP.md),
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

## Mise à jour du 9 novembre 2026

Le [bilan confirmé](docs/ETAT_CONFIRME_20261109.md) regroupe le [tableau IO](docs/hardware/io/TABLEAU_IO_D578.md), la comparaison PLUS et l’identification APRS RX. Le [simulateur Web](browser-bench/README.md) est intégré à GitHub Pages sous `simulator/`. Les résultats établis et les fonctions encore ouvertes sont distingués.

Le menu **Audio RX/TX** donne le schéma bloc et les réglages. Les vues MCU PRO/PLUS, leurs connexions et les banques QA ont été reprises le 9 novembre ; voir [les raccordements audio](docs/peripherals/09_SCHEMA_AUDIO_RX_TX_ET_RACCORDEMENTS.md) et [l’état QA courant](docs/hardware/QA4818N_ETAT_OEM_20261109.md).

Un premier [programme ARM audio indépendant](firmware/experiments/audio_alpha/README.md), d’environ 5 Kio, est fourni avec ses sources et ses tests. Dans le banc : **Essayer le programme audio alpha**. Il valide potentiomètres, volumes, coupures et affichage sans firmware OEM ; la RF n’est pas initialisée.

La version Web 0.16.0 ajoute un [programme RX FM indépendant](firmware/experiments/rx_fm_alpha/README.md) : initialisation des quatre banques, deux fréquences VHF/UHF, codeur, filtres, squelch, volumes et modes HP. Bouton **Essayer la réception FM alpha**. Les commandes sont vérifiées dans le banc ; la réception et l’écoute sur poste restent à valider.
