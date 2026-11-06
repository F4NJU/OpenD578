# OEM TEST MODE permissions — 5 November 2026

The captured PRO GD32 V1.21 radio has both service permissions disabled. The
saved main NAND contains `00` at `0x02FA0002` and `08` at `0x02FA0006`.
Bit zero of the latter byte is clear. Its backup candidate at `0x02FC0000`
has the same permission values. Other bits must be preserved.

This explains why holding P4 and the dial does not enter service mode on the
captured radio. It does not establish that every startup path is modelled.

## Evidence

VK7ZJA's D578 memory map places Local Information at `0x02FA0000`, with a
backup candidate at `0x02FC0000`. AT Options v8 reads a 256-byte record at
`0x02FA0000`. Static inspection of its checkbox handlers shows:

| Setting | Record offset | AT Options mask |
| --- | --- | --- |
| Full Test Mode | `+0x02` | `0x01` |
| Band Select | `+0x06` | `0x01` |

The V1.21 record loader at `0x0801ABBC` loads its initial 14 bytes into
`0x20009872`. The service entry routine at `0x08064816` returns at
`0x08064828` if both `record[2] == 0` and `(record[6] & 1) == 0`.
Its permitted path starts at `0x0806482A`. The firmware tests the complete
full-test byte for nonzero, whereas AT Options edits its bit zero.

The original instructions were executed in an isolated Cortex-M test for five
combinations: `(full, band) = (0,8), (0,9), (1,8), (1,9), (0,0)`.
They produced `closed, open, open, open, closed`, respectively.

Sources, inspected 5 November 2026:

- Authorized mirror of Jason Reilly VK7ZJA's notes:
  https://www.db1ig.de/pages/en/anytone/jason_reilly_vk7zja/jason_reilly_vk7zja_578mods.php
- Original AT Options v8 distribution mirrored on that page:
  https://www.db1ig.de/media/JO_Pic/578/AT_Options_v8.zip
- Original spreadsheet mirrored on that page:
  https://www.db1ig.de/media/JO_Pic/578/Anytone-578-Flash-memory-map.zip

The executable was inspected statically; it was not executed or redistributed.

## Virtual-unlock experiment and its limit

A cold application reset was run with P4 and the pressed dial held, after
setting bit zero of both permission bytes in both candidate records using only
volatile NAND pages. Captured files and OEM instructions were not patched.

At instruction 34,472,834 the firmware reached `0x08064816`, observed permission
bytes `01` and `09`, followed the permitted path and entered `0x08064504`.
It passed the native P4 code `0x17` and dial GPIO checks. This validates these
inputs for that observed path.

The run then stopped at instruction 34,483,713, PC `0x080AF7D4`, attempting
to store a delay count at address `0x0000002C`. The current task pointer read
from `0x20001548` was zero and OS-running state was not yet active. The TEST
MODE banner and service menu were **not** observed. This is an unresolved
execution discrepancy; it must not be described as successful full-test emulation
or attributed conclusively to hardware emulation, OEM firmware or power sequencing.

## Physical reference supplied by F4EGM

On a second radio, connecting the supply starts the radio automatically. The
successful service sequence is then: turn it off with Power; hold P4 and the
dial button; pulse Power; keep P4 and the dial held while the display shows
Booting / Please Wait, then D578UV TEST MODE, then the AnyTone logo; finally
the service menu starts at MODE:00000. Model and firmware identification of
this second unit remain to be recorded.

This is a software power-off/on sequence after a normal boot. It is distinct
from the bench's current application-reset startup preset. Reproduce that
sequence before calling the reset-path discrepancy a confirmed emulator defect.
MODE:00000 alone establishes service-mode access; full alignment access requires
observing additional parameter pages with the zone selection keys.

Do not copy calibration bytes between radios to obtain the same menu access.
The spreadsheet's example calibration values are not measurements of either
user radio. For initial observations, navigate parameter pages without changing
the dial setting, changing MODE, transmitting, or saving new alignment values.

## Tools

Read only, with standard Python:

```sh
python bench/oem_options.py /path/to/nand_main_256MiB.bin
```

The diagnostic probe defaults to the original captured permissions. An optional
`--virtual-full-test` flag installs the explicitly synthetic volatile fixture;
`--stop-after-test-banner` stops only if the native text renderer returns after
drawing TEST MODE. This diagnostic does not change the web startup presets and
does not claim that the complete test menu already works.
