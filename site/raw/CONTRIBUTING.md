# Contributing

Start with a small reproducible result: one peripheral transaction, one register
behavior or one code path. State the MCU/board variant and firmware hash.
Separate physical captures from synthetic stimuli and inferred behavior.

Run `python -m unittest discover -s bench -v` before submitting a change.
New hardware behavior should include a regression test that would fail with the
previous model. Unknown behavior must remain labeled incomplete rather than
being converted into an unconditional successful reply.

The hardware mode must not depend on OEM function addresses, current-channel RAM
pointers, manufacturer task flags or particular scratch-register conventions.
Keep OEM-specific analysis in the legacy runner.

Source contributions and documentation are welcome. Do not include manufacturer
images, physical dumps, codeplugs, calibration records or session snapshots.
Generated work belongs under ignored `work/` or `results/` directories.

For code adapted from another project, preserve its attribution and verify the
license of the exact source version before proposing its integration.
