# PC programming and retained alignment

Added to the first usable-version scope on 4 November 2026.

## PC link and analog memories

OpenD578 needs a working PC connection, not just manual VFO entry. A first
programming path must support identifying the board/firmware, reading analog
memories, writing selected memories, reading them back, and preserving them
through a restart. Frequency, separate RX/TX tones, name, power choice and
repeater shift are part of the memory contract.

Prefer an established programming protocol when it can be reproduced correctly.
qdmr supports the OEM D578, but that alone does not establish compatibility with
a new OpenD578 firmware or its memory format:
https://github.com/hmatuschek/qdmr

USB host traffic and the complete programming protocol remain to be implemented
and exercised in the bench. The current USB model represents an absent host;
there is no claim that PC programming already works with the new firmware.

## Three different kinds of settings

| Data | Examples | Required handling |
| --- | --- | --- |
| User/channel settings | Memories, repeater offset, CTCSS choice, selected power level | Read/write through the PC programming interface. |
| Per-radio alignment | Frequency trim, PA drive calibration, tracking gain, squelch/RSSI, deviation and tone levels | Preserve the original device-specific records and interpret each known field. |
| Firmware policy/defaults | Menu behavior and initial UI preferences | Document separately; do not substitute defaults for measured alignment. |

A power-level label is not itself a PA calibration. A repeater's RX/TX offset
is not the same setting as the oscillator's fine-frequency correction.
Unknown calibration bytes must remain preserved; values from another radio or
an example table must not silently replace them.

The initial PC memory writer should accept only identified channel/configuration
records. Alignment storage needs a separate, explicit path after its format and
integrity rules are established. Test unchanged alignment hashes around channel
uploads, interrupted transactions and restarts. These are acceptance criteria,
not implemented guarantees of the current model.

## OEM test-mode investigation

P4 plus the pressed dial at power-up is being tested with the authentic V1.21
application, physical Flash capture and captured NAND. Observations must separate
the original option state from any future synthetic unlocked fixture.

The first test uses external button stimuli and read-only display observation.
It does not force test-mode flags or parameter values in OEM RAM. Test-mode
navigation should use the parameter-selection keys; adjusting the dial, PTT,
saving alignment or changing band mode are separate actions.

Jason Reilly VK7ZJA's technical notes describe disabled, band-selection-only
and full-alignment access, controlled by option settings. They are a useful
reference, not evidence of which permissions are enabled in a particular capture:
https://radio.carstenbauer.net/578techmods.htm

Individual calibration records and captured execution state remain local inputs.
The public repository should contain formats, extraction/observation tools,
hash-based comparisons and anonymized test results.
