/* SPDX-License-Identifier: GPL-3.0-or-later
 * Independent GPIO/ADC/LCD audio control experiment. No OEM routine/RAM ABI.
 * Bench alpha: not a complete RF initialization or an OEM update image. */
#include <stdint.h>
#include <stddef.h>
#include "../../hal/audio_control.h"
#define R(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define A 0x40010800u
#define B 0x40010c00u
#define CPORT 0x40011000u
#define E 0x40011800u
#define AFIO 0x40010000u
#define ADC 0x40012400u
#define DMA 0x40020000u
static volatile uint16_t samples[4];
static volatile uint32_t ticks;
void SysTick_Handler(void){ticks++;}
static char lines[7][27];
static uint8_t last_level[2],muted[2],last_key,stable_key,key_count,global_mute,first_screen;
extern uint32_t _sidata,_sdata,_edata,_sbss,_ebss;
static void pin(uint32_t port,unsigned n,int on){R(port+0x10)=1u<<(n+(on?0:16));}
static void mode(uint32_t port,unsigned n,uint32_t m){uint32_t a=port+(n<8?0:4),shift=(n%8)*4;R(a)=(R(a)&~(15u<<shift))|(m<<shift);}
static void serial_volume(unsigned channel,uint8_t code){
 /* D0 channel, D1 individual, D2..8 code, D9..10 ones; latch last clock. */
 const uint16_t w=(uint16_t)(0x602u|((channel-1)&1u)|((uint16_t)code<<2));
 for(unsigned i=0;i<11;i++){int d=(w>>i)&1;pin(A,13,d);pin(A,14,1);if(i!=10)pin(A,13,0);pin(A,14,0);pin(A,13,0);}
}
static void lcd_byte(uint8_t v,int data){
 /* Bit set/reset preserves all other GPIOB/GPIOE signals. */
 R(E+0x10)=((uint32_t)(~v&255)<<23)|((uint32_t)v<<7);
 pin(B,13,0);pin(B,11,data);pin(B,10,0);pin(B,10,1);pin(B,13,1);
}
static void cmd(uint8_t v){lcd_byte(v,0);}static void dat(uint8_t v){lcd_byte(v,1);}
static void backlight(void){pin(A,5,0);for(int i=11;i>=0;i--){pin(B,4,(0x8ffu>>i)&1);pin(B,3,1);pin(B,3,0);}pin(A,5,1);}
/* Independently expressed 5x7 glyphs; no OEM font or framebuffer. */
static const uint8_t glyphs[][7]={
 {14,17,19,21,25,17,14},{4,12,4,4,4,4,14},{14,17,1,2,4,8,31},{30,1,1,14,1,1,30},{2,6,10,18,31,2,2},{31,16,16,30,1,1,30},{14,16,16,30,17,17,14},{31,1,2,4,8,8,8},{14,17,17,14,17,17,14},{14,17,17,15,1,1,14},
 {14,17,17,31,17,17,17},{30,17,17,30,17,17,30},{15,16,16,16,16,16,15},{30,17,17,17,17,17,30},{31,16,16,30,16,16,31},{31,16,16,30,16,16,16},{14,17,16,23,17,17,15},{17,17,17,31,17,17,17},{14,4,4,4,4,4,14},{7,2,2,2,18,18,12},{17,18,20,24,20,18,17},{16,16,16,16,16,16,31},{17,27,21,21,17,17,17},{17,25,21,19,17,17,17},{14,17,17,17,17,17,14},{30,17,17,30,16,16,16},{14,17,17,17,21,18,13},{30,17,17,30,20,18,17},{15,16,16,14,1,1,30},{31,4,4,4,4,4,4},{17,17,17,17,17,17,14},{17,17,17,17,17,10,4},{17,17,17,21,21,21,10},{17,17,10,4,10,17,17},{17,17,10,4,4,4,4},{31,1,2,4,8,16,31}};
static uint8_t glyph(char c,unsigned row){if(c>='0'&&c<='9')return glyphs[c-'0'][row];if(c>='A'&&c<='Z')return glyphs[c-'A'+10][row];if(c=='-')return row==3?14:0;if(c==':')return row==2||row==4?4:0;return 0;}
static void put(unsigned n,const char *s){unsigned i=0;while(s[i]&&i<26){lines[n][i]=s[i];i++;}for(;i<27;i++)lines[n][i]=0;}
static void number(unsigned line,unsigned column,unsigned value){lines[line][column]=(char)('0'+value/10%10);lines[line][column+1]=(char)('0'+value%10);}
static void paint(unsigned first,unsigned last){
 cmd(0x2a);dat(0);dat((uint8_t)first);dat(0);dat((uint8_t)last);cmd(0x2b);dat(0);dat(0);dat(0);dat(159);cmd(0x2c);
 /* MADCTL MX + BGR, panel mounting: screen(x,y)=(rawY,rawX). */
 for(unsigned rawy=0;rawy<160;rawy++)for(unsigned rawx=first;rawx<=last;rawx++){
  unsigned x=rawy,y=rawx,line=y/16,row=y%16,tx=x>=4?x-4:160,col=tx/6,bit=tx%6;uint16_t color=0;
  if(line<7&&row>=3&&row<10&&col<26&&bit<5&&(glyph(lines[line][col],row-3)&(16u>>bit)))color=line==0?0x07e0:0xffff;
  dat((uint8_t)(color>>8));dat((uint8_t)color);
 }
}
static void screen(unsigned dirty){if(dirty&128)paint(0,127);else for(unsigned i=0;i<7;i++)if(dirty&(1u<<i))paint(i*16,i*16+15);}
static unsigned key(uint16_t a,uint16_t b){if(a>=147&&a<=347)return 1; /* P1 */
 if(b>=147&&b<=347)return 4; /* P4 */
 if(a>=2900&&a<=3150)return 7; /* MENU */
 if(b>=2900&&b<=3150)return 8; /* EXIT */return 0;}
void Default_Handler(void){pin(A,7,1);for(;;){}}
void Reset_Handler(void){
 uint32_t *s=&_sidata;for(uint32_t *d=&_sdata;d<&_edata;)*d++=*s++;for(uint32_t*d=&_sbss;d<&_ebss;)*d++=0;
 R(0xe000ed08)=0x08006000;R(0x40021018)|=0x25d;R(0x40021014)|=1;
 pin(E,0,1);mode(E,0,3); /* Known board hold command. */
 R(0x40021004)=(R(0x40021004)&~(3u<<14))|(3u<<14);
 /* Keep TX gates low and RF selects inactive. No RF register writes. */
 pin(E,6,0);mode(E,6,3);pin(CPORT,4,0);mode(CPORT,4,3);mode(A,4,0);
 for(unsigned i=0;i<4;i++){const uint32_t ports[4]={B,B,CPORT,E};const unsigned pins[4]={5,2,13,1};pin(ports[i],pins[i],1);mode(ports[i],pins[i],3);}
 pin(A,7,1);mode(A,7,3);R(AFIO+4)=(R(AFIO+4)&~(7u<<24))|(4u<<24);
 pin(A,13,0);pin(A,14,0);mode(A,13,3);mode(A,14,3);serial_volume(1,0);serial_volume(2,0);
 for(unsigned i=10;i<=13;i++){pin(B,i,1);mode(B,i,3);}for(unsigned i=7;i<=14;i++)mode(E,i,3);
 pin(A,5,1);mode(A,5,3);pin(B,3,0);pin(B,4,0);mode(B,3,3);mode(B,4,3);backlight();
 cmd(0x11);cmd(0x3a);dat(0x55);cmd(0x36);dat(0x48);cmd(0x29);
 mode(B,0,0);mode(B,1,0);mode(CPORT,2,0);mode(CPORT,5,0);
 R(DMA+12)=4;R(DMA+16)=ADC+76;R(DMA+20)=(uint32_t)(uintptr_t)samples;R(DMA+8)=0x5a1;
 R(ADC+4)=256;R(ADC+44)=3u<<20;R(ADC+52)=8u|(9u<<5)|(12u<<10)|(15u<<15);
 R(ADC+8)=9;while(R(ADC+8)&8){}R(ADC+8)=5;while(R(ADC+8)&4){}R(ADC+8)=0x5e0103;
 last_level[0]=last_level[1]=255;
 put(0,"OPEN D578 AUDIO ALPHA");put(1,"VOL A 00 DB -00");put(2,"VOL B 00 DB -00");put(3,"P1 MUTE A : N");put(4,"P4 MUTE B : N");put(5,"MENU CUT  : N");put(6,"RX RF NOT INITIALIZED");
 while(R(DMA+12)==4){}
 /* Bench clock: 120M virtual units/s. Hardware reload needs its clock profile. */
 R(0xe000e014)=119999;R(0xe000e018)=0;R(0xe000e010)=7;
 for(;;){
  uint32_t iteration=ticks;
  unsigned k=key(samples[0],samples[1]);if(k==stable_key){if(key_count<4)key_count++;}else{stable_key=(uint8_t)k;key_count=0;}
  unsigned redraw=0;if(key_count==4&&k!=last_key){last_key=(uint8_t)k;if(k==1){muted[0]^=1;redraw|=1u<<3;}if(k==4){muted[1]^=1;redraw|=1u<<4;}if(k==7){global_mute=1;redraw|=1u<<5;}if(k==8){global_mute=muted[0]=muted[1]=0;redraw|=(1u<<3)|(1u<<4)|(1u<<5);}}
  for(unsigned i=0;i<2;i++){uint8_t level=0,code=0;d578_audio_volume_level(samples[2+i],&level);if(muted[i]||global_mute)level=0;if(level!=last_level[i]){last_level[i]=level;d578_audio_volume_code(level,&code);serial_volume(i+1,code);number(i+1,6,level);unsigned coarse=code&31,fine=code>>5,db=code?4*(21-coarse)+3-fine:99;if(code){lines[i+1][12]='-';number(i+1,13,db);}else{lines[i+1][12]='C';lines[i+1][13]='U';lines[i+1][14]='T';}redraw|=1u<<(i+1);}}
  pin(A,7,global_mute?1:0); /* Only the radio speaker gate, no invented mic gate. */
  lines[3][12]=muted[0]?'Y':'N';lines[4][12]=muted[1]?'Y':'N';lines[5][12]=global_mute?'Y':'N';
  if(!first_screen){redraw=128;first_screen=1;}
  if(redraw)screen(redraw);
  R(0x40003000)=0xaaaa; /* Feed an already-running watchdog; never start it. */
  while(ticks==iteration)__asm__ volatile("wfi");
 }
}
__attribute__((section(".vectors"),used)) const uintptr_t vectors[80]={[0]=0x20018000,[1]=(uintptr_t)Reset_Handler,[2 ... 14]=(uintptr_t)Default_Handler,[15]=(uintptr_t)SysTick_Handler,[16 ... 79]=(uintptr_t)Default_Handler};
