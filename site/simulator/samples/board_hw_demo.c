/* Cortex-M4 Thumb2 test firmware: all pixels are emitted on physical GPIO bus.
 * Not AnyTone OEM code. License: CC0-1.0. Compile at 0x08006000.
 */
#include <stdint.h>
#define REG(a) (*(volatile uint32_t*)(uintptr_t)(a))
#define A (0x40010800u)
#define B (0x40010C00u)
#define E (0x40011800u)
#define RCU (0x40021000u)
static void lcd_byte(uint8_t value, int data){
  REG(E+0x0c)=(uint32_t)value<<7;
  REG(B+0x0c)=data?0x1800:0x1000; /* WR low, CS low, RESET high, D/C */
  REG(B+0x0c)=data?0x1c00:0x1400; /* WR rising: LCD latches data */
  REG(B+0x0c)=data?0x3c00:0x3400; /* CS high */
}
static void lcd_command(uint8_t command){lcd_byte(command,0);}
static void lcd_data(uint8_t data){lcd_byte(data,1);}
static void light8(uint8_t value){
  const uint16_t word=(8u<<8)|value;
  REG(A+0x0c)=0x20;
  REG(A+0x0c)=0;
  for(int i=11;i>=0;i--){
    uint32_t bit=((word>>i)&1u)<<4;
    REG(B+0x0c)=bit;
    REG(B+0x0c)=bit|0x8;
  }
  REG(A+0x0c)=0x20;
}
__attribute__((used)) void Reset_Handler(void){
  REG(RCU+0x18)|=1u|(1u<<2)|(1u<<3)|(1u<<4)|(1u<<6);
  REG(0x40010004u)=(REG(0x40010004u)&~(7u<<24))|(2u<<24); // release JTAG pins, retain SWD
  REG(B+0x00)=0x44433444u; // PB3/PB4 lighting serial outputs
  REG(B+0x04)=0x33333333u; // PB8..15 outputs
  REG(E+0x00)=0x34444444u; // PE7 output, PE0..6 input
  REG(E+0x04)=0x33333333u;
  REG(A+0x00)=0x44344444u; // PA5 latch output, other low pins input
  REG(B+0x0c)=0x3c00;
  light8(255);
  lcd_command(0x11);
  lcd_command(0x3a);lcd_data(0x55);
  lcd_command(0x29);
  lcd_command(0x2a);
  lcd_data(0);lcd_data(0);lcd_data(0);lcd_data(31);
  lcd_command(0x2b);
  lcd_data(0);lcd_data(0);lcd_data(0);lcd_data(31);
  lcd_command(0x2c);
  for(int y=0;y<32;y++)for(int x=0;x<32;x++){
    uint16_t rgb=(x<16)?0xf800u:0x07e0u;
    if(y>=16)rgb=0x001fu;
    lcd_data((uint8_t)(rgb>>8));lcd_data((uint8_t)rgb);
  }
  REG(0x20000000u)=0x4f443537u; // 'OD57' test marker, no fake output
  for(;;){ __asm__ volatile("wfi"); }
}
__asm__(".section .vectors,\"a\"\n"
        ".word 0x20018000\n"
        ".word Reset_Handler\n"
        ".previous\n");
