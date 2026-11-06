# OpenD578 alternative firmware work area

This directory is reserved for a future standalone firmware for the D578UV PRO GD32.
No radio-flashable binary is provided. A build must be kept separate from the
hardware simulator and from manufacturer firmware inputs.

Start with [the architecture](../docs/firmware/ARCHITECTURE.md),
[validation gates](../docs/firmware/VALIDATION.md) and
[the emulator](../docs/EMULATOR.md) and
[Bluetooth driver design, BT01 and BP-02](../docs/firmware/BLUETOOTH_PILOTES_BT01_PTT.md).

Experimental frequency encoder and trace-only bus plan: [QA4818N reconstruction](../docs/hardware/QA4818N_RECONSTRUCTION_REGISTRES_PLL_CHAINES_RX_TX.md), `rf/qa4818n_frequency.[ch]` and `rf/qa4818n_transport.[ch]`. These are not board drivers and do not enable TX.
