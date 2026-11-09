/* SPDX-License-Identifier: GPL-3.0-or-later
 * Independent receive FM experiment. No OEM routine/RAM ABI.
 * Bench build: not an OEM update image or hardware-qualified radio. */
#include <stdint.h>
#include <stddef.h>
#include "../../hal/audio_control.h"
#include "../../rf/rx_fm.h"
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
static uint8_t last_level[2],last_key,stable_key,key_count,global_mute,first_screen;
static uint8_t selected,narrow[2],monitor,speaker_mode=1,threshold=120,pages[4];
static uint32_t frequencies[2]={14550000,43500000};
static uint16_t pio25=0xb3,pio0=1;
static d578_rx_squelch squelch[2];
static volatile int32_t dial_delta;
void EXTI9_5_Handler(void){if(R(0x40010414)&256){uint32_t pins=R(CPORT+8);dial_delta+=!!(pins&256)==!!(pins&512)?1:-1;R(0x40010414)=256;}}

extern uint32_t _sidata,_sdata,_edata,_sbss,_ebss;
static void pin(uint32_t port,unsigned n,int on){R(port+0x10)=1u<<(n+(on?0:16));}
static void mode(uint32_t port,unsigned n,uint32_t m){uint32_t a=port+(n<8?0:4),shift=(n%8)*4;R(a)=(R(a)&~(15u<<shift))|(m<<shift);}
/* 12 MHz HXTAL -> PLL x10, HCLK=120, APB1=60, APB2=120 MHz.
 * Clock fields/FMC latency match the OEM 08006260 path; bounded waits are ours. */
static int wait_mask(uint32_t a,uint32_t mask,uint32_t expected){for(unsigned i=0;i<1000000;i++){R(0x40003000)=0xaaaa;if((R(a)&mask)==expected)return 1;}return 0;}
static int clock_120mhz(void){
 R(0x40021000)|=1;if(!wait_mask(0x40021000,2,2))return 0;
 R(0x40021004)&=~3u;if(!wait_mask(0x40021004,12,0))return 0;
 R(0x40021000)&=~(1u<<24);if(!wait_mask(0x40021000,1u<<25,0))return 0;
 R(0x40021000)|=1u<<16;if(!wait_mask(0x40021000,1u<<17,1u<<17))return 0;
 R(0x40022000)=(R(0x40022000)&~3u)|0x12;
 R(0x4002102c)=0;R(0x40021004)=0x0021c400; /* ADC /8 = 15 MHz */
 R(0x40021000)|=1u<<24;if(!wait_mask(0x40021000,1u<<25,1u<<25))return 0;
 R(0x40021004)|=2;if(!wait_mask(0x40021004,12,8))return 0;
 return 1;
}
static void delay_ms(uint32_t ms){uint32_t start=ticks;while(ticks-start<ms){R(0x40003000)=0xaaaa;__asm__ volatile("wfi");}}
static void serial_volume(unsigned channel,uint8_t code){
 /* D0 channel, D1 individual, D2..8 code, D9..10 ones; latch last clock. */
 const uint16_t w=(uint16_t)(0x602u|((channel-1)&1u)|((uint16_t)code<<2));
 for(unsigned i=0;i<11;i++){int d=(w>>i)&1;pin(A,13,d);pin(A,14,1);if(i!=10)pin(A,13,0);pin(A,14,0);pin(A,13,0);}
}
/* Three-wire RF, MSB first, shared PB3/PB4; explicit CS per bank. */
static void bus_pause(void){for(volatile unsigned n=0;n<50;n++)__asm__ volatile("nop");}
static void rf_select(unsigned bank,int active){const uint32_t ports[4]={B,B,CPORT,E};const unsigned pins[4]={5,2,13,1};pin(ports[bank],pins[bank],!active);}
static void rf_bits(uint32_t bits,unsigned count){for(unsigned i=count;i>0;i--){pin(B,4,(bits>>(i-1))&1);bus_pause();pin(B,3,1);bus_pause();pin(B,3,0);}}
static uint16_t rf_read(unsigned bank,unsigned reg){
 pin(B,3,0);rf_select(bank,1);rf_bits(0x80u|reg,8);pin(B,4,1);mode(B,4,8);uint16_t value=0;
 for(unsigned i=0;i<16;i++){bus_pause();pin(B,3,1);bus_pause();value=(uint16_t)((value<<1)|((R(B+8)>>4)&1));pin(B,3,0);}
 rf_select(bank,0);mode(B,4,3);pin(B,4,0);return value;
}
static void rf_write(unsigned bank,unsigned reg,uint16_t value){
 pin(B,3,0);rf_select(bank,1);bus_pause();rf_bits(((uint32_t)reg<<16)|value,24);rf_select(bank,0);pin(B,4,0);
 if(reg==127)pages[bank]=(uint8_t)value;
 else if(!pages[bank]&&reg==0x25){if(bank==1)pio25=value;if(bank==0)pio0=value;}
}
static int rx_emit(void *user,const d578_rx_op *op){
 (void)user;
 if(op->kind==0)rf_write(op->bank,op->reg,op->value);
 else if(op->kind==1)(void)rf_read(op->bank,op->reg);
 else if(op->kind==2){delay_ms(op->value);}
 else return -1;return 0;
}
static int audio_emit(void *user,const d578_audio_op *op){(void)user;if(op->kind==D578_RF_WRITE)rf_write(op->bank,op->reg,op->value);else pin(A,7,op->value);return 0;}
static void led_word(uint8_t word){for(unsigned i=0;i<8;i++){pin(E,3,(word>>i)&1);pin(E,4,1);pin(E,4,0);}}
static void outputs(int audible){
 d578_audio_plan plan;d578_audio_context context={0};context.speakers=(d578_speakers)speaker_mode;
 if(audible)d578_audio_enable(&context,pio25,true,&plan);else d578_audio_mute(pio25,true,&plan);
 size_t done;(void)d578_audio_apply(&plan,audio_emit,0,&done);
}
static void configure(unsigned b){
 outputs(0);d578_rx_begin((uint8_t)b,narrow[b],threshold,rx_emit,0);
 d578_rx_tune((uint8_t)b,frequencies[b],rx_emit,0);
 /* RF-bank0 band controls resolved by 0806CE64, fixed dual RX profile. */
 unsigned uhf=frequencies[b]>=30000000u;
 if(!b)pio0=(uint16_t)((pio0&~0x48u)|(uhf?8:64));
 else pio0=(uint16_t)((pio0&~0x90u)|(uhf?128:16));
 rf_write(0,0x25,pio0);
 d578_rx_start((uint8_t)b,rx_emit,0);
 squelch[b].open=false;squelch[b].count=0;
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
static uint8_t glyph(char c,unsigned row){if(c>='0'&&c<='9')return glyphs[c-'0'][row];if(c>='A'&&c<='Z')return glyphs[c-'A'+10][row];if(c=='-')return row==3?14:0;if(c=='.')return row==6?4:0;if(c==':')return row==2||row==4?4:0;return 0;}
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
static unsigned key(uint16_t a,uint16_t b){
 if(a>=147&&a<=347)return 1;if(a>=900&&a<=1100)return 2;if(a>=1900&&a<=2100)return 3;
 if(b>=147&&b<=347)return 4;if(b>=900&&b<=1100)return 5;if(b>=1900&&b<=2100)return 6;
 if(a>=2900&&a<=3150)return 7;if(b>=2900&&b<=3150)return 8;return 0;
}
static void frequency_line(unsigned b){
 put(b+1,b?"B 000.00000 W SQ N":"A 000.00000 W SQ N");uint32_t f=frequencies[b];
 for(int i=10;i>=2;i--){if(i==5)continue;lines[b+1][i]=(char)('0'+f%10);f/=10;}
 lines[b+1][12]=narrow[b]?'N':'W';lines[b+1][17]=(monitor||squelch[b].open)?'Y':'N';
}
void Default_Handler(void){pin(A,7,1);for(;;){}}
void Reset_Handler(void){
 uint32_t *s=&_sidata;for(uint32_t *d=&_sdata;d<&_edata;)*d++=*s++;for(uint32_t*d=&_sbss;d<&_ebss;)*d++=0;
 R(0xe000ed08)=0x08006000;R(0x40021018)|=0x25d;R(0x40021014)|=1;
 pin(E,0,1);mode(E,0,3);pin(CPORT,3,1);mode(CPORT,3,3); /* Known board hold command. */
 R(0x40021004)=(R(0x40021004)&~(3u<<14))|(3u<<14);
 /* Receiver-only experiment: TX gates stay low throughout. */
 pin(E,6,0);mode(E,6,3);pin(CPORT,4,0);mode(CPORT,4,3);mode(A,4,0);
 for(unsigned i=0;i<4;i++){const uint32_t ports[4]={B,B,CPORT,E};const unsigned pins[4]={5,2,13,1};pin(ports[i],pins[i],1);mode(ports[i],pins[i],3);}
 pin(A,7,1);mode(A,7,3);R(AFIO+4)=(R(AFIO+4)&~(7u<<24))|(4u<<24);
 pin(A,13,0);pin(A,14,0);mode(A,13,3);mode(A,14,3);serial_volume(1,0);serial_volume(2,0);
 for(unsigned i=10;i<=13;i++){pin(B,i,1);mode(B,i,3);}for(unsigned i=7;i<=14;i++)mode(E,i,3);
 pin(A,5,1);mode(A,5,3);pin(B,3,0);pin(B,4,0);mode(B,3,3);mode(B,4,3);backlight();
 if(!clock_120mhz())Default_Handler();
 R(0xe000e014)=119999;R(0xe000e018)=0;R(0xe000e010)=7;
 pin(B,12,0);delay_ms(10);pin(B,12,1);delay_ms(120);
 cmd(0x11);delay_ms(120);cmd(0x3a);dat(0x55);cmd(0x36);dat(0x48);cmd(0x29);
 mode(B,0,0);mode(B,1,0);mode(CPORT,2,0);mode(CPORT,5,0);
 R(DMA+12)=4;R(DMA+16)=ADC+76;R(DMA+20)=(uint32_t)(uintptr_t)samples;R(DMA+8)=0x5a1;
 R(ADC+12)=(7u<<6)|(7u<<15);R(ADC+16)=(7u<<24)|(7u<<27);
 R(ADC+4)=256;R(ADC+44)=3u<<20;R(ADC+52)=8u|(9u<<5)|(12u<<10)|(15u<<15);
 R(ADC+8)=9;while(R(ADC+8)&8){}R(ADC+8)=5;while(R(ADC+8)&4){}R(ADC+8)=0x5e0103;
 /* SysTick uses the 120 MHz clock selected before LCD initialization. */
 pin(E,3,0);pin(E,4,0);pin(E,5,1);mode(E,3,3);mode(E,4,3);mode(E,5,3);led_word(0x46);
 d578_rx_reset(rx_emit,0);configure(0);configure(1);
 mode(CPORT,8,8);mode(CPORT,9,8);pin(CPORT,8,1);pin(CPORT,9,1);
 R(AFIO+16)=(R(AFIO+16)&~15u)|2;R(0x40010414)=256;R(0x40010408)|=256;R(0x4001040c)|=256;R(0x40010400)|=256;R(0xe000e100)=1u<<23;
 last_level[0]=last_level[1]=255;
 put(0,"OPEN D578 RX FM ALPHA");frequency_line(0);frequency_line(1);
 put(3,"VOL A 00 B 00");put(4,"SEL A MON N HP RADIO");put(5,"SQ RAW 120 CUT N");put(6,"P1 SEL P2 MON P3 BAND");
 uint32_t last_poll=ticks;uint8_t previous_speaker=255,previous_audible=255,previous_led=255;
 for(;;){
  uint32_t iteration=ticks;unsigned redraw=0;
  unsigned k=key(samples[0],samples[1]);if(k==stable_key){if(key_count<4)key_count++;}else{stable_key=(uint8_t)k;key_count=0;}
  if(key_count==4&&k!=last_key){last_key=(uint8_t)k;
   if(k==1){selected^=1;redraw|=16;}
   if(k==2){monitor^=1;redraw|=16|6;}
   if(k==3){frequencies[selected]=frequencies[selected]<30000000u?43500000u:14550000u;configure(selected);redraw|=1u<<(selected+1);}
   if(k==4){speaker_mode=(speaker_mode+1)%3;redraw|=16;}
   if(k==5){narrow[selected]^=1;configure(selected);redraw|=1u<<(selected+1);}
   if(k==6){threshold=threshold>=140?80:threshold+20;configure(0);configure(1);redraw|=32;}
   if(k==7){global_mute=1;redraw|=32;}
   if(k==8){global_mute=0;redraw|=32;}
  }
  __asm__ volatile("cpsid i");int32_t delta=dial_delta;dial_delta=0;__asm__ volatile("cpsie i");
  if(delta){uint32_t low=frequencies[selected]<30000000u?13600000u:40000000u,high=frequencies[selected]<30000000u?17400000u:48000000u;
   int64_t next=(int64_t)frequencies[selected]+(int64_t)delta*1250;if(next<low)next=low;if(next>high)next=high;
   if((uint32_t)next!=frequencies[selected]){frequencies[selected]=(uint32_t)next;configure(selected);redraw|=1u<<(selected+1);}
  }
  if(ticks-last_poll>=10){last_poll=ticks;
   for(unsigned b=0;b<2;b++){bool before=squelch[b].open;uint16_t status=rf_read(b,0x0c),noise=0,level=0;
    if(before&&!(status&2)){noise=rf_read(b,0x65);level=rf_read(b,0x67);}
    uint16_t close_level=threshold>73?threshold-3:70;
    d578_rx_squelch_update(&squelch[b],status,noise,level,close_level);
    if(before!=squelch[b].open)redraw|=1u<<(b+1);
   }
  }
  for(unsigned i=0;i<2;i++){uint8_t level=0,code=0;d578_audio_volume_level(samples[2+i],&level);
   if(global_mute||(!monitor&&!squelch[i].open))level=0;
   if(level!=last_level[i]){last_level[i]=level;d578_audio_volume_code(level,&code);serial_volume(i+1,code);number(3,i?11:6,level);redraw|=8;}
  }
  uint8_t audible=!global_mute&&(monitor||squelch[0].open||squelch[1].open);
  if(previous_audible!=audible||previous_speaker!=speaker_mode){outputs(audible);previous_audible=audible;previous_speaker=speaker_mode;}
  uint8_t led=(monitor||squelch[0].open||squelch[1].open)?0x4e:0x46;if(led!=previous_led){led_word(led);previous_led=led;}
  /* Preserve TX inhibition even if PTT input is held. No TX handler exists. */
  pin(E,6,0);pin(CPORT,4,0);
  frequency_line(0);frequency_line(1);lines[4][4]=selected?'B':'A';lines[4][10]=monitor?'Y':'N';
  for(unsigned i=15;i<26;i++)lines[4][i]=0;
  const char *hp=speaker_mode==0?"MIC":speaker_mode==1?"RADIO":"BOTH";for(unsigned i=0;hp[i];i++)lines[4][15+i]=hp[i];
  lines[5][7]=(char)('0'+threshold/100);number(5,8,threshold%100);lines[5][15]=global_mute?'Y':'N';
  if(!first_screen){redraw=128;first_screen=1;}if(redraw)screen(redraw);
  R(0x40003000)=0xaaaa;while(ticks==iteration)__asm__ volatile("wfi");
 }
}
__attribute__((section(".vectors"),used)) const uintptr_t vectors[80]={[0]=0x20018000,[1]=(uintptr_t)Reset_Handler,[2 ... 14]=(uintptr_t)Default_Handler,[15]=(uintptr_t)SysTick_Handler,[16 ... 38]=(uintptr_t)Default_Handler,[39]=(uintptr_t)EXTI9_5_Handler,[40 ... 79]=(uintptr_t)Default_Handler};
