/* CC0 original fixture. Binary emitted by build_microphone_tx_demo.py. */
#include <stdint.h>
#define R(a) (*(volatile uint32_t *)(a))
const uint8_t frame[]={83,1,1,0,0,0,1,1,0,16,0,0,0,0,0,6};
void Reset_Handler(void){R(0x40021018)=1<<14;R(0x40013808)=1042;R(0x4001380c)=0x2008;
 for(unsigned i=0;i<16;i++){R(0x40013804)=frame[i];while(!(R(0x40013800)&64));}for(;;)__asm volatile("wfi");}
