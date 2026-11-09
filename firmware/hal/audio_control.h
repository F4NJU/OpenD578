/* SPDX-License-Identifier: GPL-3.0-or-later
 * OpenD578 logical control contracts, independently expressed from OEM analysis.
 * No OEM code, fixed SRAM addresses, firmware calls or radio TX enable.
 */
#ifndef OPEND578_AUDIO_CONTROL_H
#define OPEND578_AUDIO_CONTROL_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef enum { D578_MIC_SPEAKER=0, D578_RADIO_SPEAKER=1, D578_BOTH_SPEAKERS=2 } d578_speakers;
typedef enum { D578_PATH_MAIN=0, D578_PATH_SUB=1 } d578_mic_path;
typedef enum { D578_RF_WRITE=0, D578_GPIO_PA7=1 } d578_audio_op_kind;
typedef struct {
    d578_audio_op_kind kind;
    uint8_t bank, reg;
    uint16_t value;
    bool immediate; /* OEM direct vs queued RF transport, not a timing promise. */
} d578_audio_op;
typedef struct { d578_audio_op ops[4]; size_t count; uint16_t final_pio25; } d578_audio_plan;
typedef struct {
    d578_speakers speakers;
    d578_mic_path path;
    bool radio_override; /* OEM getter override, 0x20001050 == 1. */
    bool special_mode;   /* cfg+0x21: meaning intentionally unresolved. */
    bool aux_enabled;    /* 0x20001085 != 0, semantics unresolved. */
    bool aux_active;     /* 0x20000EF4 != 0, semantics unresolved. */
    bool sub_gate_hold;  /* 0x200008A9 != 0, semantics unresolved. */
    bool output_hold;    /* 0x200011E4 != 0: enable routine leaves state unchanged. */
} d578_audio_context;

/* Plans preserve all unrelated PIO bits, including bits 8..15. Cached RF writes
 * are omitted exactly as in the OEM wrappers. PA7 writes are not cached. */
bool d578_audio_enable(const d578_audio_context *, uint16_t pio25, bool immediate, d578_audio_plan *);
bool d578_audio_mute(uint16_t pio25, bool immediate, d578_audio_plan *);
bool d578_audio_mic_path(const d578_audio_context *, uint16_t pio25, bool immediate, d578_audio_plan *);
bool d578_audio_route_gate(const d578_audio_context *, bool requested, uint16_t pio25, bool immediate, d578_audio_plan *);
bool d578_audio_aux_route(const d578_audio_context *, bool requested, uint16_t pio25, bool immediate, d578_audio_plan *);

/* Standard wired FM path only (cfg+0x21 == 0). level_index 0..5 is the OEM
 * Level1..Level6. factory_mic is the loaded NAND MIC code, never a dB gain.
 * Produces reg18, page=1, reg17, page=0 in the OEM order, bank 0.
 * Arithmetic intentionally retains the OEM 16-bit wrap at low factory codes. */
bool d578_audio_fm_microphone(uint8_t level_index, uint8_t factory_mic, d578_audio_plan *);
/* Pure quantizer: callers supply the same acquired value in both OEM arguments. */
bool d578_audio_volume_level(uint16_t adc12, uint8_t *level);
bool d578_audio_volume_code(uint8_t level, uint8_t *code);

/* Execute a plan with an application-provided bus backend. Nonzero callback
 * return stops at that operation; *completed tells the caller what succeeded.
 * The plan's final_pio25 is committed by the caller only on successful writes.
 * After partial failure, derive the current PIO from the successful prefix,
 * not final_pio25. GPIO configuration, bus locking and pulse widths belong to backend. */
typedef int (*d578_audio_emit)(void *user, const d578_audio_op *op);
int d578_audio_apply(const d578_audio_plan *, d578_audio_emit, void *user, size_t *completed);
#endif
