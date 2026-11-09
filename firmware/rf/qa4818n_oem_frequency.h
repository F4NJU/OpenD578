#ifndef D578_QA_OEM_FREQUENCY_H
#define D578_QA_OEM_FREQUENCY_H
#include "qa4818n_frequency.h"
/* OEM V1.21 representation: page 0 reg38 low then reg39 high, units 10Hz.
 * Encoding only, no frequency-range authorization, PLL lock or TX operation.
 * Caller manages page selection, bus locking and hardware sequencing. */
bool d578_qa_plan_oem_frequency(uint8_t bank, uint64_t hz, qa4818_frequency_plan_t *out);
uint64_t d578_qa_oem_frequency_hz(uint16_t low, uint16_t high);
#endif
