# Firmware-independent board mode

The V1.21 bench originally combined two jobs: modeling peripherals and observing
the manufacturer's functions and SRAM structures. Its exact PC/signature checks
were useful for OEM analysis but inappropriate for a new program.

`HardwareRunner` reuses the digital peripheral implementations without invoking
the inherited OEM instruction observers. Its GPIO input path reads the modeled
pin levels without relying on a helper function address or a mask in CPU R1.
The LCD and radio buses arm from pin configuration and edges, not from function
entry addresses. No OEM RAM flag is read to decide whether the program is running.

## Image and memory

- Physical Flash: `0x08000000..0x082FFFFF`, 3 MiB.
- SRAM: `0x20000000..0x20017FFF`, 96 KiB, including executable SRAM.
- A read/execute boot alias starts at zero.
- The image's first words provide its stack and reset vector. The loader sets
  VTOR to the supplied image's base, representing a loader handoff.
- The reset vector must point into the supplied image. Subsequent valid execution
  is not constrained to the OEM application's old occupied range.

The boot alias initially mirrors Flash; self-modification and all Flash
programming/alias synchronization modes are not qualified yet. Do not infer
complete bootloader or update support from the loader's ability to place an image.

## Explicit model boundaries

| Stop category | Meaning |
| --- | --- |
| `control` | Instruction budget reached or the operator stopped the run. |
| `waiting` | WFI/WFE observed; full sleep/event progression remains to be extended. |
| `model_incomplete` | An unsupported register, protocol variant or missing peripheral profile was encountered. |
| `physical_address_unmapped` | Access outside mapped physical devices/memory; assess the program and board profile. |
| `execution_boundary` | Other execution stop requiring analysis. |

An instruction budget alone is not a success criterion for a radio feature.
The contract probe separately checks its pixels, SRAM markers, executed SRAM
routine and received radio-register bits.

The default NAND has synthetic erased cells and a volatile program/erase overlay.
It allocates no manufacturer dump. Captured NAND and an explicit SCT bootstrap
can instead be provided locally. DSP bootstrap comparison is a bus contract;
the DSP program itself is not executed.

GPIO inputs not attached to a modeled peer use an explicit idle/pull-up scenario.
Not all electrical pull modes or external loads are modeled. RF status inputs
are bank-level digital stimuli. They do not yet follow a synthesized frequency.

## Current independent tests

The original Thumb generator and executable tests cover:

- Flash placement at `0x08006000` and `0x08000000`.
- Entry at `0x0808ADBE`, previously a V1.21 NAND hook.
- Initial stack above the old OEM allocation, and reads/writes near SRAM's end.
- Execution of a newly written Thumb routine at `0x20017F00`.
- GPIO LCD command/data cycles producing two known RGB565 pixels.
- GPIO radio-register writes and carrier/CTCSS decoder reads.
- Missing peripheral behavior distinguished from an OEM signature mismatch.
- Ideal NAND overlay one-way programming on synthetic erased cells.

The legacy OEM tests remain available. OEM images and recorded sessions must be
supplied separately before replaying the old full-radio scenarios.

## Local inputs for the legacy V1.21 web bench

The original route uses `full_flash_pass1.bin`,
`AT-D578 PRO PC SOFTWARE.zip`, and
`D578_PASSATION_PHASE47_NAND_COMPLETE_2026-11-03.zip` in the selected source folder.
The ZIP files stay compressed.

The extracted route accepts these files in the selected source folder:

| File | Purpose |
| --- | --- |
| `full_flash_pass1.bin` | Authenticated 3 MiB physical Flash capture, including the reference application. |
| `nand_main_256MiB.bin` | Main NAND cells. |
| `nand_oob64_8MiB.bin` | Captured NAND spare bytes. |
| `nand_ecc_status_128KiB.bin` | Captured per-page ECC status. |
| `SCT3258TD_UpdateFlash_V2_01_07BF.hex` | Manufacturer reference for the modeled DSP bootstrap contract. |

Extracted NAND files can also reside in `NAND_ORIGINAUX`. Existing authenticated
cache files and original archives can be mixed with the extracted route. Sizes
and SHA256 checks remain mandatory; missing OOB/ECC captures are never invented.
The reference CDD is recovered from the authenticated full capture if it is not
already present or supplied by the original archive. Optional ET12 Bluetooth
also requires its matching manufacturer binary. None of these private inputs is
included in this public repository. Use application reset when no matching OEM
ready-session recording is available.
