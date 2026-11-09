#include "qa4818n_oem_frequency.h"
#include <stddef.h>
bool d578_qa_plan_oem_frequency(uint8_t bank,uint64_t hz,qa4818_frequency_plan_t *out)
{
 if(!out||bank>3||hz%10u||hz/10u>UINT32_MAX)return false;
 uint32_t word=(uint32_t)(hz/10u);
 qa4818_frequency_plan_t p={bank,{{0x38,(uint16_t)word},{0x39,(uint16_t)(word>>16)}}};
 *out=p;return true;
}
uint64_t d578_qa_oem_frequency_hz(uint16_t low,uint16_t high)
{return (((uint64_t)high<<16)|low)*10u;}
