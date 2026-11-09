#include <stdint.h>
#define R(a) (*(volatile uint32_t *)(a))
#define COUNT R(0x20000000)
void Reset_Handler(void);
void USART1_Handler(void){if(R(0x40004400)&32){uint8_t v=R(0x40004404);((volatile uint8_t *)0x20000020)[COUNT++]=v;if(COUNT==4)R(0xe000e184)=1<<6;}}
__attribute__((section(".vectors"),used)) const uintptr_t vectors[55]={[0]=0x20018000,[1]=(uintptr_t)Reset_Handler,[54]=(uintptr_t)USART1_Handler};
void Reset_Handler(void){COUNT=0;R(0xe000ed08)=0x08006000;R(0x4002101c)|=1<<17;R(0x40004408)=6250;R(0x4000440c)=0x2024;R(0xe000e104)=1<<6;while(COUNT<4)__asm__ volatile("wfi");R(0x20000004)=0x55415254;for(;;)__asm__ volatile("wfi");}
