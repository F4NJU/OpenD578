/* Independent GPIO/EXTI test; no OEM routines or fixed OEM SRAM variables. */
#include <stdint.h>
#define R(a) (*(volatile uint32_t *)(a))
void Reset_Handler(void);
void EXTI5_9_Handler(void){if(R(0x40010414)&256){R(0x20000000)++;R(0x20000004)=(R(0x40011008)>>8)&3;R(0x20000008)=((R(0x20000004)&1)==((R(0x20000004)>>1)&1));R(0x40010414)=256;}}
__attribute__((section(".vectors"),used)) const uintptr_t vectors[40]={[0]=0x20018000,[1]=(uintptr_t)Reset_Handler,[39]=(uintptr_t)EXTI5_9_Handler};
void Reset_Handler(void){
 R(0x20000000)=0;R(0x20000004)=99;R(0x20000008)=99;R(0xe000ed08)=0x08006000;
 R(0x40021018)|=17;R(0x40011004)=0x44444444;
 R(0x40010010)=2; /* EXTI8 on port C; falling edge, unmasked */
 R(0x40010408)=256;R(0x4001040c)=256;R(0x40010400)=256;
 R(0xe000e100)=1<<23;
 for(;;)__asm__ volatile("wfi");
}
