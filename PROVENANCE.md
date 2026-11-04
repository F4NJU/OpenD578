# Source provenance and local inputs

This initial source tree contains the Python/C emulator code from the project's
V10/V11 bench, subsequent independent hardware-mode work, and French research
notes from the project's 4 November 2026 handoff. Original contract programs are
generated from the included Thumb instruction emitter.

No manufacturer application, DSP image, Flash/NAND capture, OEM execution
snapshot, radio calibration or codeplug is included. Hash constants and addresses
identify the historical inputs; they are not the inputs themselves.

The exact earlier compiled satellite modules are not included in this initial
tree. Historical notes reference them without presenting them as available source.
No OpenGD77 or OpenRTX firmware modules have been imported in this initial tree.

Python dependencies are installed separately: Unicorn, Capstone and Pillow retain
their upstream licenses. Future source imports must retain attribution and their
applicable license terms. Original OpenD578 source and documentation in this
repository are provided under GPL-3.0-or-later.

The legacy OEM replay tools expect user-provided local files. The independent
hardware tests require no OEM inputs and can run in public CI.
