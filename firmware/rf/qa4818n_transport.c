#include "qa4818n_transport.h"
#include <stddef.h>

bool qa4818_apply_plan_to_bench(const qa4818_transport_t *transport,
                               const qa4818_frequency_plan_t *plan)
{
    if (transport == NULL || plan == NULL ||
        transport->write_register == NULL ||
        !transport->allow_experimental_writes || plan->bank > 3 ||
        plan->writes[0].reg != 0x29u || plan->writes[1].reg != 0x2Au)
        return false;
    if (!transport->write_register(transport->context, plan->bank,
                                   plan->writes[0].reg, plan->writes[0].value))
        return false;
    return transport->write_register(transport->context, plan->bank,
                                     plan->writes[1].reg, plan->writes[1].value);
}
