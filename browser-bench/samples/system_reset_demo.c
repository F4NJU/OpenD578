/* Independent original test firmware. Two architectural resets, no OEM hooks. */
#include <stdint.h>
#define R(a) (*(volatile uint32_t *)(a))
void Reset_Handler(void);
__attribute__((section(".vectors"),used)) const uintptr_t vectors[]={0x20010000,(uintptr_t)Reset_Handler};
void Reset_Handler(void){
  __asm volatile("cpsid i");
  if(R(0x20000100)!=0xD578AABB){
    R(0x20000100)=0xD578AABB;R(0x20000104)=1;
    R(0x40007000)=256;R(0x40006C04)=0x2468;
    R(0xE000ED0C)=0x05FA0004;
  }else if(R(0x20000104)==1){
    R(0x20000108)=R(0x40021024);R(0x2000010C)=R(0x40006C04);R(0x20000104)=2;
    R(0x40003000)=0x5555;R(0x40003004)=0;R(0x40003008)=1;R(0x40003000)=0xCCCC;
  }else{
    R(0x20000110)=R(0x40021024);R(0x20000114)=R(0x40006C04);R(0x20000104)=3;
  }
  for(;;)__asm volatile("wfi");
}
