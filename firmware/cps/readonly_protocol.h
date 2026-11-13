/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef OPEND578_READONLY_PROTOCOL_H
#define OPEND578_READONLY_PROTOCOL_H
#include <stddef.h>
#include <stdint.h>
typedef struct { uint32_t rx_hz[2]; uint8_t narrow[2], selected; } d578_cps_state;
typedef struct { char line[64]; size_t length; uint8_t overflow; } d578_cps_parser;
typedef int (*d578_cps_emit)(void *, const uint8_t *, size_t);
void d578_cps_feed(d578_cps_parser *, const uint8_t *, size_t, const d578_cps_state *, d578_cps_emit, void *);
#endif
