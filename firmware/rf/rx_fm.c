/* SPDX-License-Identifier: GPL-3.0-or-later
 * Independent implementation of reference GD32 V1.21 receive commands. */
#include "rx_fm.h"
#include "rx_fm_parameters.inc"
#define LEN(x) (sizeof(x)/sizeof((x)[0]))
static int sequence(const d578_rx_op *p,size_t n,int bank,d578_rx_backend emit,void *user){
 if(!emit)return -1;
 for(size_t i=0;i<n;i++){d578_rx_op o=p[i];if(bank>=0)o.bank=(uint8_t)bank;int e=emit(user,&o);if(e)return e;}
 return 0;
}
static int write_reg(uint8_t b,uint8_t r,uint16_t v,d578_rx_backend emit,void *user){
 d578_rx_op o={0,b,r,v};return emit(user,&o);
}
int d578_rx_reset(d578_rx_backend emit,void *user){return sequence(reset_sequence,LEN(reset_sequence),-1,emit,user);}
int d578_rx_fm_mode(uint8_t b,bool narrow,d578_rx_backend emit,void *user){
 if(b>1||!emit)return -1;
 const d578_rx_op *p=b?(narrow?fm_1_1:fm_1_0):(narrow?fm_0_1:fm_0_0);
 size_t n=b?(narrow?LEN(fm_1_1):LEN(fm_1_0)):(narrow?LEN(fm_0_1):LEN(fm_0_0));
 return sequence(p,n,-1,emit,user);
}
static int synth(uint8_t b,unsigned range,d578_rx_backend emit,void *user){
 const d578_rx_op *p=range==0?synth_0:range==2?synth_2:range==3?synth_3:synth_7;
 return sequence(p,4,b,emit,user);
}
static int frequency(uint8_t b,uint32_t f,d578_rx_backend emit,void *user){
 int e=write_reg(b,0x38,(uint16_t)f,emit,user);if(e)return e;
 return write_reg(b,0x39,(uint16_t)(f>>16),emit,user);
}
int d578_rx_tune(uint8_t b,uint32_t f,d578_rx_backend emit,void *user){
 if(b>1||!emit||!((f>=13600000u&&f<=17400000u)||(f>=40000000u&&f<=48000000u)))return -1;
 uint32_t intermediate=b?3855000u:3885000u;
 uint32_t oscillator;unsigned range;
 if(f-intermediate>=30000000u){oscillator=f-intermediate;range=0;}
 else{oscillator=f+intermediate;range=oscillator>=16000000u?2:3;}
 int e=synth(b+2,range,emit,user);if(e)return e;
 e=frequency(b+2,oscillator,emit,user);if(e)return e;
 e=synth(b,7,emit,user);if(e)return e;
 return frequency(b,intermediate,emit,user);
}
int d578_rx_threshold(uint8_t b,uint8_t raw,d578_rx_backend emit,void *user){
 if(b>1||!emit)return -1;
 int e=write_reg(b,0x4f,0x7e2b,emit,user);if(e)return e;
 return write_reg(b,0x78,((uint16_t)raw<<8)|255,emit,user);
}
bool d578_rx_squelch_update(d578_rx_squelch *s,uint16_t status,uint16_t noise,uint16_t level,uint16_t close_level){
 if(!s)return false;
 if(!s->open){if(status&2){if(++s->count>=3){s->open=true;s->count=0;}}else s->count=0;}
 else if(status&2)s->count=0;
 else if((noise&127)>43||(level&511)<close_level){if(++s->count>=3){s->open=false;s->count=0;}}
 /* The OEM does not clear a partial close count on a good fallback sample. */
 return s->open;
}

int d578_rx_begin(uint8_t b,bool narrow,uint8_t threshold,d578_rx_backend emit,void *user){
 if(b>1||!emit)return -1;
 int e=write_reg(b,3,0,emit,user);if(e)return e;
 e=d578_rx_fm_mode(b,narrow,emit,user);if(e)return e;
 if(b){e=write_reg(1,0x28,5,emit,user);if(e)return e;e=write_reg(3,0x28,0x20,emit,user);}
 else{e=write_reg(2,0x28,0x20,emit,user);if(e)return e;e=write_reg(0,0x28,5,emit,user);}
 if(e)return e;
 e=write_reg(b,0x53,0x57dd,emit,user);if(e)return e;
 e=write_reg(b,0x23,0x8f87,emit,user);if(e)return e;
 e=write_reg(b,0x3a,narrow?0xe0:0x40,emit,user);if(e)return e;
 e=write_reg(b,0x43,0x6009,emit,user);if(e)return e;
 return d578_rx_threshold(b,threshold,emit,user);
}
int d578_rx_start(uint8_t b,d578_rx_backend emit,void *user){
 if(b>1||!emit)return -1;
 int e;if(!b){e=write_reg(2,3,0,emit,user);if(e)return e;}
 e=write_reg(b+2,3,0xc1fe,emit,user);if(e)return e;
 e=write_reg(b,0x34,0x086f,emit,user);if(e)return e;
 e=write_reg(b,0x35,0xf208,emit,user);if(e)return e;
 e=write_reg(b,0x47,0x6140,emit,user);if(e)return e;
 return write_reg(b,3,0xbff5,emit,user);
}
