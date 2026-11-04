# USB programming, diagnostics and physical recovery

## CPS direction

For an OEM satellite extension, retain the manufacturer's programming protocol
and calibration format initially. For an autonomous OpenD578 application, target
a documented programming protocol and a dedicated model profile, keeping the
radio's native calibration storage independent of channel uploads.

The grid.radio OpenGD77 CPS is an attractive interoperability target: it already
edits channels, tones, APRS and satellite data. Its published guide currently lists
MK22/STM32 radios via WebUSB and DM32/UV008 via Web Serial, not D578 support.
A D578 transport/model adapter and format agreement are still needed.
https://grid.radio/opengd77/

The inspected page provides copyright notices for incorporated OpenGD77 code,
including a non-commercial condition. A public repository for the complete web
CPS source was not identified in this inspection. Browser accessibility does not
by itself establish permission to redistribute a fork. No such code is imported
in the initial OpenD578 tree.

qdmr is a source-available reference for the existing AnyTone wire protocol and
D578 memory layout. Its interface identifies GD32 USB VID/PID 28E9:018A and a
serial programming session with PROGRAM, identity, read and write transactions.
These describe the OEM path; they do not establish a new firmware's compatibility.
https://github.com/hmatuschek/qdmr/blob/master/lib/anytone_interface.cc

## Small USB diagnostic service

Provide firmware version, model identity, counters, bounded read-only diagnostics,
and a crash record. Keep protocol framing distinct from programming transactions;
unframed printf output must not corrupt a CPS session. An additional USB interface
is an option only after endpoint resources and browser/driver behavior are tested.

An OpenD578 linker reservation can hold the faulting PC/LR/SP and fault-status
registers. A maintenance path reached early at startup can expose the record after
a controlled restart, before bringing up RF. RAM records need validation and do
not survive arbitrary power loss. This service is a design target, not a working
replacement for a physical debugger.

The USB host/peripheral exchange must also be added to the emulator. A test that
uses only an in-process API does not qualify USB enumeration or endpoint transfers.

## Observed SWD disable

The V1.21 cold-boot trace contains writes to AFIO_PCF0 at 0x40010004:

| Executed-instruction step | Written value | SWJ_CFG[2:0] |
| --- | --- | --- |
| 70322 | 0x00000000 | 000 |
| 70333 | 0x02000000 | 010: JTAG disabled, SWD enabled |
| 70359 | 0x00000000 | 000 |
| 70370 | 0x04000000 | 100: JTAG and SWD disabled |

The manufacturer's manual defines SWJ_CFG as write-only, with undefined readback.
The evidence is therefore the executed write sequence, not a readable hardware
state register. The emulator does not prove which physical board net uses the
released pins.

After reset the documented default enables SWJ. Connecting while reset is held,
then halting before the application disables debug, is a recovery method to verify
on the actual board. SEGGER documents connect-under-reset for GD32 devices.

The project's successful FT232H connection had no NRST wire. The radio Power
button is a GPIO input and does not replace control of NRST. The exact reset route,
electrical access and recovery procedure remain unverified on the board.

Flash/NAND backups provide data to restore. They do not themselves establish an
accessible debug port, a working erase/program path or recoverability of every
protection state. Keep option-byte/protection changes outside ordinary firmware
and channel programming. Preserve the OEM bootloader while recovery is being
qualified.

Sources:

- GigaDevice GD32F30x User Manual, AFIO_PCF0 / SWJ_CFG:
  https://www.gd32mcu.com/data/documents/userManual/GD32F30x_User_Manual_Rev2.9.pdf
- SEGGER GD32, connect under reset:
  https://kb.segger.com/GigaDevice_GD32
- Authenticated V1.21 execution report from the project's V11 cold-boot run.
