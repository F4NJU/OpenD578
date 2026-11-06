#ifndef OPEND578_QA4818N_FREQUENCY_H
#define OPEND578_QA4818N_FREQUENCY_H

/* Experimental/offline only: AT1846S register format hypothesis, not verified
 * for QA4818N silicon. No GD32 GPIO, RF transmission or board initialization.
 */
#include <stdint.h>
#include <stdbool.h>

typedef struct {
    uint8_t reg;
    uint16_t value;
} qa4818_reg_write_t;

typedef struct {
    uint8_t bank;
    qa4818_reg_write_t writes[2];
} qa4818_frequency_plan_t;

/* Nearest 62.5 Hz step, round half up for integer-Hz input.
 * 29H bits 13:0 = high 14 bits, 2AH = low 16 bits.
 */
bool qa4818_encode_frequency_at1846s(uint32_t hz, uint16_t *high, uint16_t *low);
bool qa4818_plan_frequency_at1846s(uint8_t bank, uint32_t hz,
                                  qa4818_frequency_plan_t *plan);
/* Integer half-Hz result preserves the 0.5 Hz fraction exactly. */
bool qa4818_decode_frequency_halfhz(uint16_t high, uint16_t low, uint64_t *half_hz);
/* 24-bit write representation: 8-bit reg (read flag =0), 16-bit big-endian value. */
bool qa4818_pack_write_at1846s(uint8_t reg, uint16_t value, uint8_t out_bytes[3]);

#endif
