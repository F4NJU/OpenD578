/* SPDX-License-Identifier: GPL-3.0-or-later
 * Host parser checks, separate from the actual ARM/USB qualification. */
#include "../cps/readonly_protocol.h"
typedef struct { char bytes[1024];size_t n; } capture;
static int take(void *user,const uint8_t *bytes,size_t n){capture *c=user;if(c->n+n>=sizeof(c->bytes))return 0;for(size_t i=0;i<n;i++)c->bytes[c->n++]=(char)bytes[i];c->bytes[c->n]=0;return 1;}
static int contains(const capture *c,const char *needle){for(size_t i=0;i<c->n;i++){size_t j=0;while(needle[j] && i+j<c->n && c->bytes[i+j]==needle[j])j++;if(!needle[j])return 1;}return 0;}
static void send(d578_cps_parser *p,capture *c,d578_cps_state *s,const char *text){size_t n=0;while(text[n])n++;d578_cps_feed(p,(const uint8_t *)text,n,s,take,c);}
int d578_cps_selftest(void){
 struct {uint32_t before;d578_cps_parser parser;uint32_t after;} guarded={0x12345678,{{0},0,0},0x87654321};
 d578_cps_parser *p=&guarded.parser;capture c={{0},0};d578_cps_state s={{145500000,435000000},{0,1},1};
 send(p,&c,&s,"OD578/1 1 HE");if(c.n)return 1;send(p,&c,&s,"LLO\n");
 if(!contains(&c,"\"id\":1") || !contains(&c,"\"ctcss\":false") || !contains(&c,"\"vfoWrite\":false"))return 2;
 c.n=0;send(p,&c,&s,"OD578/1 2 VFOS\n");if(!contains(&c,"145500000") || !contains(&c,"\"selected\":\"B\"") || !contains(&c,"\"bandwidth\":\"narrow\""))return 3;
 s.rx_hz[0]=145512500;c.n=0;send(p,&c,&s,"OD578/1 3 VFOS\n");if(!contains(&c,"145512500"))return 4;
 c.n=0;send(p,&c,&s,"OD578/1 4 WRITE\n");if(!contains(&c,"unsupported_command"))return 5;
 c.n=0;send(p,&c,&s,"OD578/1 65536 HELLO\n");if(!contains(&c,"bad_request") || !contains(&c,"\"id\":0"))return 6;
 c.n=0;uint8_t flood[200];for(size_t i=0;i<sizeof(flood);i++)flood[i]='X';d578_cps_feed(p,flood,sizeof(flood),&s,take,&c);send(p,&c,&s,"\nOD578/1 5 HELLO\n");
 if(!contains(&c,"bad_request") || !contains(&c,"\"id\":5") || guarded.before!=0x12345678 || guarded.after!=0x87654321)return 7;
 c.n=0;const uint8_t binary[]={0,'\n'};d578_cps_feed(p,binary,sizeof(binary),&s,take,&c);if(!contains(&c,"bad_request"))return 8;
 return 0;
}
