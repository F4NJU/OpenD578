#include "../rf/qa4818n_oem_frequency.h"
#include <assert.h>
#include <string.h>
int main(void){qa4818_frequency_plan_t p;
 assert(d578_qa_plan_oem_frequency(1,145500000,&p));assert(p.bank==1&&p.writes[0].reg==0x38&&p.writes[1].reg==0x39);
 assert(d578_qa_oem_frequency_hz(p.writes[0].value,p.writes[1].value)==145500000);
 assert(d578_qa_oem_frequency_hz(0,1)==655360);assert(d578_qa_oem_frequency_hz(65535,65535)==42949672950ULL);
 assert(d578_qa_plan_oem_frequency(3,42949672950ULL,&p));qa4818_frequency_plan_t old=p;
 assert(!d578_qa_plan_oem_frequency(0,145500001,&p));assert(!memcmp(&p,&old,sizeof p));
 assert(!d578_qa_plan_oem_frequency(4,145500000,&p));assert(!d578_qa_plan_oem_frequency(0,42949672960ULL,&p));assert(!d578_qa_plan_oem_frequency(0,145500000,0));return 0;}
