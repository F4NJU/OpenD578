/* Independent hardware test. Not an OEM patch or replacement display. */
#include <stdint.h>
#define R(a) (*(volatile uint32_t *)(a))
#define TICKS R(0x20000000)
void Reset_Handler(void);
void SysTick_Handler(void){if(++TICKS==3)R(0xe000e010)=0;}
__attribute__((section(".vectors"),used)) const uintptr_t vectors[16]={
 [0]=0x20018000,[1]=(uintptr_t)Reset_Handler,[15]=(uintptr_t)SysTick_Handler};
void Reset_Handler(void){
 TICKS=0;R(0xe000ed08)=0x08006000;
 R(0x40021014)|=1;R(0x40021018)|=0x200;
 R(0x4002000c)=7;R(0x40020010)=0x4001244c;R(0x40020014)=0x20000020;R(0x40020008)=0x5a1;
 R(0x40012404)=256;R(0x4001242c)=6<<20;R(0x40012430)=15;
 R(0x40012434)=6|(8<<5)|(9<<10)|(10<<15)|(11<<20)|(12<<25);
 R(0x40012408)=0x5e0101;
 R(0xe000e014)=999;R(0xe000e018)=0;R(0xe000e010)=7;
 while(TICKS<3)__asm__ volatile("wfi");
 R(0x20000004)=0x41444337;
 for(;;)__asm__ volatile("wfi");
}
