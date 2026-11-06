#include "qa4818n_frequency.h"
#include <stddef.h>

bool qa4818_encode_frequency_at1846s(uint32_t hz, uint16_t *high, uint16_t *low)
{
    if (!high || !low)
        return false;
    const uint64_t ticks = ((uint64_t)hz * 2u + 62u) / 125u;
    if (ticks >= (UINT64_C(1) << 30))
        return false;
    *high = (uint16_t)((ticks >> 16) & 0x3FFFu);
    *low = (uint16_t)(ticks & 0xFFFFu);
    return true;
}

bool qa4818_plan_frequency_at1846s(uint8_t bank, uint32_t hz,
                                  qa4818_frequency_plan_t *plan)
{
    uint16_t hi, lo;
    if (plan == NULL || bank > 3 ||
        !qa4818_encode_frequency_at1846s(hz, &hi, &lo))
        return false;
    plan->bank = bank;
    plan->writes[0] = (qa4818_reg_write_t){0x29u, hi};
    plan->writes[1] = (qa4818_reg_write_t){0x2Au, lo};
    return true;
}

bool qa4818_decode_frequency_halfhz(uint16_t high, uint16_t low, uint64_t *half_hz)
{
    if (!half_hz)
        return false;
    const uint32_t ticks = (((uint32_t)(high & 0x3FFFu)) << 16) | low;
    *half_hz = (uint64_t)ticks * 125u;
    return true;
}

bool qa4818_pack_write_at1846s(uint8_t reg, uint16_t value, uint8_t out_bytes[3])
{
    if (!out_bytes || reg >= 0x80u)
        return false;
    out_bytes[0] = reg;
    out_bytes[1] = (uint8_t)(value >> 8);
    out_bytes[2] = (uint8_t)value;
    return true;
}
