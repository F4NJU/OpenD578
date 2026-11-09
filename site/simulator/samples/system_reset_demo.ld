ENTRY(Reset_Handler)
MEMORY { FLASH (rx) : ORIGIN = 0x08000000, LENGTH = 24K
         RAM (rwx) : ORIGIN = 0x20000000, LENGTH = 96K }
SECTIONS { .vectors : { KEEP(*(.vectors)) } > FLASH
 .text : { *(.text*) *(.rodata*) } > FLASH
 /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) } }
