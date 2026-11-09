/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef D578_RX_FM_H
#define D578_RX_FM_H
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
typedef struct { uint8_t kind,bank,reg; uint16_t value; } d578_rx_op;
/* kind 0: register write, 1: register read (value unused), 2: delay in ms.
 * The backend owns GPIO timing and clocks. A nonzero result stops a sequence. */
typedef int (*d578_rx_backend)(void *, const d578_rx_op *);
int d578_rx_reset(d578_rx_backend, void *);
int d578_rx_fm_mode(uint8_t receiver, bool narrow, d578_rx_backend, void *);
/* Standard analog receive profile: fixed OEM getter index 0, no auxiliary route.
 * Register gain codes are not acoustic dB; factory trim loading is separate. */
int d578_rx_begin(uint8_t receiver, bool narrow, uint8_t threshold, d578_rx_backend, void *);
int d578_rx_start(uint8_t receiver, d578_rx_backend, void *);
/* Frequency is the desired RF input, in 10 Hz units, NOT each bank's PLL word.
 * Bench profile accepts 136..174 and 400..480 MHz. No TX programming API. */
int d578_rx_tune(uint8_t receiver, uint32_t frequency10, d578_rx_backend, void *);
/* Calibrated raw threshold supplied by caller; never a dBm value. */
int d578_rx_threshold(uint8_t receiver, uint8_t raw, d578_rx_backend, void *);
typedef struct { bool open; uint8_t count; } d578_rx_squelch;
/* OEM standard FM carrier gate, no CTCSS/DCS/scan/priority arbitration.
 * status = reg0C; noise = reg65; level = reg67. close_level is calibrated.
 * Three qualifying polls open/close. This is a poll count, not a duration. */
bool d578_rx_squelch_update(d578_rx_squelch *, uint16_t status,
                           uint16_t noise, uint16_t level, uint16_t close_level);
#endif
