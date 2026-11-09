/* CC0 original test; binary derived with build_microphone_demo.py. */
#include <stdint.h>
#define R(a) (*(volatile uint32_t *)(a))
#define COUNT R(0x20000000)
void Reset_Handler(void);
void USART0_Handler(void){if(R(0x40013800)&32){uint8_t v=R(0x40013804);((volatile uint8_t *)0x20000020)[COUNT++]=v;if(COUNT==8)R(0xe000e184)=1<<5;}}
__attribute__((section(".vectors"),used)) const uintptr_t vectors[53]={[0]=0x20018000,[1]=(uintptr_t)Reset_Handler,[53]=(uintptr_t)USART0_Handler};
void Reset_Handler(void){COUNT=0;R(0xe000ed08)=0x08006000;R(0x40021018)=1<<14;R(0x40013808)=1042;R(0x4001380c)=0x2024;R(0xe000e104)=1<<5;while(COUNT<8)__asm__ volatile("wfi");R(0x20000004)=0x55415254;for(;;)__asm__ volatile("wfi");}
