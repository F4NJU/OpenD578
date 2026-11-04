# Research index

The French notes below summarize the earlier reverse-engineering work and
identify each claim's evidence level. They describe historical phases; they
are not updated claims that all their experiments were repeated for this repository.

| File | Subject |
| --- | --- |
| [01_DECISIONS_ET_HISTORIQUE.md](01_DECISIONS_ET_HISTORIQUE.md) | Decisions and earlier milestones |
| [02_CPU_FLASH_BOOT_USB_SWD.md](02_CPU_FLASH_BOOT_USB_SWD.md) | MCU, Flash, boot and read-only debug findings |
| [03_NAND_LECTURES_ECC_CARTE.md](03_NAND_LECTURES_ECC_CARTE.md) | NAND geometry, reads, ECC observations and map |
| [04_RAM_ROUTINES_UI_RF_ET_BROCHAGE.md](04_RAM_ROUTINES_UI_RF_ET_BROCHAGE.md) | SRAM, UI, RF routines and pin evidence |
| [05_SATELLITE_CODE_INTEGRATION_EXP06.md](05_SATELLITE_CODE_INTEGRATION_EXP06.md) | Earlier satellite module and integration state |
| [06_SIMULATION_UNICORN_RAM_CLOCK_NAND_V1_V2_V3.md](06_SIMULATION_UNICORN_RAM_CLOCK_NAND_V1_V2_V3.md) | First CPU/clock/NAND models |
| [07_ERREURS_CORRECTIONS_HYPOTHESES_ET_NO_GO.md](07_ERREURS_CORRECTIONS_HYPOTHESES_ET_NO_GO.md) | Corrections, hypotheses and historical blockers |
| [08_LIENS_COMPLETS_ANNOTES.md](08_LIENS_COMPLETS_ANNOTES.md) | Annotated external references |
| [09_REPRISE_PRIORITES_TESTS_ET_INFOS_MANQUANTES.md](09_REPRISE_PRIORITES_TESTS_ET_INFOS_MANQUANTES.md) | Earlier missing evidence and next steps |

Some historical archives and compiled satellite objects are referenced but not
included. In particular, the initial repository does not claim to contain the
exact Phase60 C sources or a flashable satellite build. The source available here
is the emulator, its tools and original firmware-contract probes.

The current scope is in [ROADMAP.md](ROADMAP.md): APRS TX in the first usable
version, APRS RX in the second stage, DMR a required subsequent goal.
