/* SPDX-License-Identifier: GPL-3.0-or-later
 * GD32F30x USBD single-buffer CDC polling experiment. Bench-qualified only:
 * VID/PID are unassigned lab identifiers, not a deployable USB product identity.
 * PMA logical halfword offsets have a twofold CPU address spacing.
 * Register reference: GD32F30x UM Rev2.9, USBD EP/ISTR/BTABLE/PMA chapters. */
#include "usb_cdc_poll.h"
#define U(off) (*(volatile uint16_t *)(uintptr_t)(0x40005c00u+(off)))
#define R32(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define EP(n) U((n)*4u)
#define PM(a) (*(volatile uint16_t *)(uintptr_t)(0x40006000u+2u*(a)))
static const uint8_t device[]={18,1,0,2,2,0,0,64,0xff,0xff,0x78,0x05,0,1,0,0,0,1};
static const uint8_t config[]={9,2,67,0,2,1,0,0x80,50,
 9,4,0,0,1,2,2,1,0, 5,0x24,0,0x10,1, 5,0x24,1,0,1,
 4,0x24,2,2, 5,0x24,6,0,1, 7,5,0x82,3,8,0,16,
 9,4,1,0,2,10,0,0,0, 7,5,0x01,2,64,0,0, 7,5,0x81,2,64,0,0};
static uint8_t line_coding[7]={0,0xc2,1,0,0,0,8};
static uint8_t receive[64], transmit[1024];
static size_t rx_n,tx_head,tx_tail;
static const uint8_t *control_data;
static unsigned control_n,control_at,control_zlp,out_line,address_pending,configured,generation;
static void pma_put(unsigned at,const uint8_t *src,unsigned n){for(unsigned i=0;i<n;i+=2)PM(at+i)=(uint16_t)(src[i]|(i+1<n?(uint16_t)src[i+1]<<8:0));}
static void pma_get(unsigned at,uint8_t *dst,unsigned n){for(unsigned i=0;i<n;i+=2){uint16_t v=PM(at+i);dst[i]=(uint8_t)v;if(i+1<n)dst[i+1]=(uint8_t)(v>>8);}}
/* STAT and DTOG fields toggle on write; CTR fields clear on zero. */
static void ep(unsigned n,unsigned type,unsigned tx,unsigned rx,unsigned clear){
 uint16_t old=EP(n);EP(n)=(uint16_t)(n|type|(0x8080u&~clear)|((old^((tx<<4)|(rx<<12)))&0x3030u));
}
static void send0(void){
 unsigned n=control_n-control_at;if(n>64)n=64;
 pma_put(0x40,control_data?control_data+control_at:device,n);PM(2)=n;control_at+=n;
 if(!n)control_zlp=0;ep(0,0x200,3,3,0);
}
static void reset(void){
 configured=0;address_pending=0;out_line=0;control_n=control_at=control_zlp=0;rx_n=tx_head=tx_tail=0;generation++;
 U(0x50)=0;PM(0)=0x40;PM(2)=0;PM(4)=0x80;PM(6)=0x8400;
 PM(8)=0xc0;PM(10)=0;PM(12)=0x100;PM(14)=0x8400;
 PM(16)=0x140;PM(18)=0;PM(20)=0x148;PM(22)=0x1000;
 ep(0,0x200,2,3,0x8080);ep(1,0,0,0,0x8080);ep(2,0x600,0,0,0x8080);U(0x4c)=0x80;
}
void d578_usb_init(void){
 /* PLL120 /2.5 = nominal 48 MHz; set prescaler before USB clock enable. */
 R32(0x40021004)=(R32(0x40021004)&~((3u<<22)|(1u<<31)))|(2u<<22);
 R32(0x4002101c)|=1u<<23;U(0x40)=1;U(0x40)=0;U(0x44)=0;reset();
}
static void setup(void){
 uint8_t s[8];pma_get(0x80,s,8);unsigned value=s[2]|(unsigned)s[3]<<8,index=s[4]|(unsigned)s[5]<<8,length=s[6]|(unsigned)s[7]<<8;
 control_data=0;control_n=control_at=control_zlp=out_line=0;address_pending=0;
 ep(0,0x200,2,3,0x8080);
 if(s[0]==0x80 && s[1]==6 && index==0){
  if(value==0x100){control_data=device;control_n=sizeof(device);}
  else if(value==0x200){control_data=config;control_n=sizeof(config);}else goto stall;
 }else if(s[0]==0 && s[1]==5 && value<=127 && index==0 && !length)address_pending=value|0x80;
 else if(s[0]==0 && s[1]==9 && value<=1 && index==0 && !length){
  configured=value;ep(1,0,value?2:0,value?3:0,0x8080);ep(2,0x600,value?2:0,0,0x8080);
 }else if(s[0]==0x21 && s[1]==0x20 && !value && !index && length==7){out_line=1;return;}
 else if(s[0]==0xa1 && s[1]==0x21 && !value && !index && length==7){control_data=line_coding;control_n=7;}
 else if(!(s[0]!=0x21 || s[1]!=0x22 || value>3 || index || length)){}else goto stall;
 if(control_n>length)control_n=length;
 control_zlp=control_n<length && control_n%64==0;send0();return;
stall: ep(0,0x200,1,1,0);
}
void d578_usb_poll(void){
 if(U(0x44)&0x400){U(0x44)=(uint16_t)~0x400u;reset();}
 uint16_t e=EP(0);
 if(e&0x8000){
  if(e&0x800)setup();
  else {unsigned n=PM(6)&1023;ep(0,0x200,(EP(0)>>4)&3,3,0x8000);
   if(out_line){out_line=0;if(n==7){pma_get(0x80,line_coding,7);control_n=control_at=0;send0();}else ep(0,0x200,1,1,0);}
  }
 }
 if(EP(0)&0x80){
  ep(0,0x200,2,3,0x80);
  if(address_pending){U(0x4c)=address_pending;address_pending=0;}
  else if(control_at<control_n || control_zlp)send0();
 }
 if(!configured)return;
 if(EP(1)&0x8000){unsigned n=PM(14)&1023;if(n<=64 && !rx_n){pma_get(0x100,receive,n);rx_n=n;ep(1,0,(EP(1)>>4)&3,n?2:3,0x8000);}}
 if(EP(1)&0x80)ep(1,0,2,(EP(1)>>12)&3,0x80);
 if(tx_head!=tx_tail && ((EP(1)>>4)&3)==2){
  uint8_t packet[64];unsigned n=0;while(n<64 && tx_tail!=tx_head){packet[n++]=transmit[tx_tail];tx_tail=(tx_tail+1)%sizeof(transmit);}
  pma_put(0xc0,packet,n);PM(10)=n;ep(1,0,3,(EP(1)>>12)&3,0);
 }
}
size_t d578_usb_read(uint8_t *dst,size_t cap){
 if(!rx_n || cap<rx_n)return 0;size_t n=rx_n;for(size_t i=0;i<n;i++)dst[i]=receive[i];rx_n=0;ep(1,0,(EP(1)>>4)&3,3,0);return n;
}
int d578_usb_write(const uint8_t *src,size_t n){
 size_t used=(tx_head+sizeof(transmit)-tx_tail)%sizeof(transmit);if(n>=sizeof(transmit)-used)return 0;
 for(size_t i=0;i<n;i++){transmit[tx_head]=src[i];tx_head=(tx_head+1)%sizeof(transmit);}return 1;
}
unsigned d578_usb_generation(void){return generation;}
