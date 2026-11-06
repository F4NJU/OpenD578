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

## Consolidation of 5 November 2026

The public V11.7 source was recovered from the clean
`SOURCES_PUBLIQUES/OpenD578_source_V11_7.zip` stored inside the project's
`OpenD578_Banc_V11_7.zip` delivery. Only that public source tree has been
merged here. No manufacturer image, raw NAND dump, execution snapshot,
manufacturer CPS binary or private codeplug has been copied out of the bench
archive. The newer V11.8 LCD, front-panel and microphone Markdown documents
are included as independently delivered documentation; the V11.8 executable
source was **not** available for this package.

The interactive site sources, hardware models, external-source notes and CPS
trace auditor were developed as public documentation/tools. Historical phase
reports describe some investigations whose original artifacts have not been
recovered. Such historical observations must not be construed as available
and tested files or validated firmware integration.

The generated `site/` tree is a derivative of the source Markdown and
`hardware/models/*.json`, built with `tools/build_site.py` and rebuilt by
GitHub Actions when `main` is pushed. The Markdown and JSON are canonical.

## Evidence update, 5 November 2026

Reconstructed peripheral documentation, GD32F303VKT6 pin map and *unwired* KiCad reference sheet are newly authored using surviving analyses and published component datasheets. They are **not** original files from the earlier chats. The hardware models now include candidate RTC/GNSS backup capacitors with per-connection confidence, based on the user's earlier board observation and VK7ZJA's photos of other board revisions. Original boot/flash/NAND dumps and Phase60 exact build files remain absent. All added external datasheets, photos and manuals are linked and not copied. Evidence ledger and reconstruction inventory: `docs/evidence/INDEX.md` and `docs/archives/ORIGINAUX_A_RECUPERER.md`.

## QA4818N : analyse du 6 novembre 2026

Source externe: guide de programmation AT1846S et documentation de VK7ZJA. Source locale: banc `bench/rf_spi.py` V11.7 et index des routines V1.21. Le code C est entièrement nouveau et utilise seulement une formule de codage de fréquence de référence. Il ne réutilise ni firmware OEM ni routine OEM, et ne peut pas piloter directement les GPIO. Les valeurs de démonstration sont étiquetées `synthetic` ; aucune capture originale constructeur du changement de fréquence n'est embarquée. Une copie officielle de V1.21 est référencée dans les précédents travaux par SHA-256 `02b2a3b56bd57c7ada581eb52b9b6f41c5d51aaec1b068d37585efd58dff9c9a`, mais l'image n'est pas incluse ici.
