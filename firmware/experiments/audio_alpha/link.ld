ENTRY(Reset_Handler)
MEMORY {
 FLASH (rx) : ORIGIN = 0x08006000, LENGTH = 128K
 RAM (rwx) : ORIGIN = 0x20000000, LENGTH = 96K
}
SECTIONS {
 .vectors : { KEEP(*(.vectors)) } > FLASH
 .text : { *(.text*) *(.rodata*) } > FLASH
 .ARM.exidx : { *(.ARM.exidx*) } > FLASH
 .data : { _sdata = .; *(.data*) _edata = .; } > RAM AT > FLASH
 _sidata = LOADADDR(.data);
 .bss (NOLOAD) : { _sbss = .; *(.bss*) *(COMMON) _ebss = .; } > RAM
 /DISCARD/ : { *(.comment*) }
}
