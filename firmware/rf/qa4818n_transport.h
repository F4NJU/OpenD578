#ifndef OPEND578_QA4818N_TRANSPORT_H
#define OPEND578_QA4818N_TRANSPORT_H
#include "qa4818n_frequency.h"

/* The entire transport is supplied by a caller. No pin driving in this
 * module. A bench recorder can be injected for conformance testing.
 * The board policy must keep TX and PA disabled until independently qualified.
 */
typedef bool (*qa4818_mock_bus_write_fn)(void *context, uint8_t bank,
                                         uint8_t reg, uint16_t value);

typedef struct {
    qa4818_mock_bus_write_fn write_register;
    void *context;
    bool allow_experimental_writes; /* never enabled by default */
} qa4818_transport_t;

/* Only register pair; leaves power, mode, PA and RF switches untouched.
 * Caller must supply an explicitly opted-in bench transport. */
bool qa4818_apply_plan_to_bench(const qa4818_transport_t *transport,
                               const qa4818_frequency_plan_t *plan);
#endif
