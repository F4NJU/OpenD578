/* CC0-1.0. Original CPU/lifecycle test, not an AnyTone firmware. */
#include <stdint.h>
__attribute__((used)) void Reset_Handler(void){
  volatile uint32_t *counter=(volatile uint32_t *)0x20000000u;
  *counter=0;
  for(;;){*counter=*counter+1;__asm__ volatile("nop");}
}
__asm__(".section .vectors,\"a\"\n.word 0x20018000\n.word Reset_Handler\n.previous\n");
