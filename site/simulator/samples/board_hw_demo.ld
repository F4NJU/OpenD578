ENTRY(Reset_Handler)
MEMORY {
  FLASH (rx) : ORIGIN = 0x08006000, LENGTH = 0x00020000
  RAM (rwx) : ORIGIN = 0x20000000, LENGTH = 0x00018000
}
SECTIONS {
  .vectors : { KEEP(*(.vectors)) } > FLASH
  .text : { *(.text*) *(.rodata*) } > FLASH
  .ARM.exidx : { *(.ARM.exidx*) } > FLASH
  .data : { *(.data*) } > RAM AT > FLASH
  .bss : { *(.bss*) *(COMMON) } > RAM
}
