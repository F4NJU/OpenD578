/* SPDX-License-Identifier: GPL-3.0-or-later
 * Bounded, allocation-free read-only service. No MMIO, memory-address command,
 * flash, NAND or transmitter access. Units on the wire are integer Hz. */
#include "readonly_protocol.h"
typedef struct { char data[384]; size_t n; } reply;
static void text(reply *r,const char *s){while(*s && r->n<sizeof(r->data))r->data[r->n++]=*s++;}
static void number(reply *r,uint32_t v){char tmp[10];unsigned n=0;do{tmp[n++]=(char)('0'+v%10);v/=10;}while(v);while(n && r->n<sizeof(r->data))r->data[r->n++]=tmp[--n];}
static int equal(const char *a,const char *b){while(*a && *a==*b){a++;b++;}return *a==*b;}
static void dispatch(d578_cps_parser *p,const d578_cps_state *state,d578_cps_emit emit,void *user){
 reply r={{0},0};uint32_t id=0;size_t at=0;const char prefix[]="OD578/1 ";int valid=!p->overflow;
 for(size_t i=0;i<sizeof(prefix)-1;i++)if(at>=p->length || p->line[at++]!=prefix[i])valid=0;
 unsigned digits=0;while(valid && at<p->length && p->line[at]>='0' && p->line[at]<='9'){
  id=id*10+(unsigned)(p->line[at++]-'0');digits++;if(id>65535 || digits>5)valid=0;
 }
 if(!digits || !id || at>=p->length || p->line[at++]!=' ')valid=0;
 p->line[p->length]=0;
 text(&r,"{\"protocol\":\"opend578-cps\",\"version\":1,\"id\":");number(&r,valid?id:0);
 if(!valid)text(&r,",\"error\":\"bad_request\"}");
 else if(equal(p->line+at,"HELLO")){
  text(&r,",\"firmware\":\"rx-fm-alpha-cps-ro.1\",\"capabilities\":{\"vfoRead\":true,\"vfoWrite\":false,\"memories\":false,\"ctcss\":false,\"dcs\":false,\"tx\":false,\"persistent\":false}}");
 }else if(equal(p->line+at,"VFOS")){
  text(&r,",\"selected\":\"");text(&r,state->selected?"B":"A");text(&r,"\",\"vfos\":[");
  for(unsigned i=0;i<2;i++){
   if(i)text(&r,",");text(&r,"{\"id\":\"");text(&r,i?"B":"A");text(&r,"\",\"rxHz\":");number(&r,state->rx_hz[i]);
   text(&r,",\"bandwidth\":\"");text(&r,state->narrow[i]?"narrow":"wide");text(&r,"\",\"txInhibit\":true}");
  }text(&r,"]}");
 }else text(&r,",\"error\":\"unsupported_command\"}");
 text(&r,"\n");(void)emit(user,(const uint8_t *)r.data,r.n);
}
void d578_cps_feed(d578_cps_parser *p,const uint8_t *bytes,size_t size,const d578_cps_state *state,d578_cps_emit emit,void *user){
 for(size_t i=0;i<size;i++){
  const uint8_t b=bytes[i];
  if(b=='\n'){dispatch(p,state,emit,user);p->length=0;p->overflow=0;}
  else if(p->length<sizeof(p->line)-1){p->line[p->length++]=(char)b;if(b<32 || b>126)p->overflow=1;}
  else p->overflow=1;
 }
}
