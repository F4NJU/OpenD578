/* D578 scheduler bridge. Counts every genuine Unicorn instruction; Python is
 * called at model deadlines and observation PCs. No instruction is replaced. */
#include <stdint.h>
typedef void (*notify_fn)(void *, uint64_t, uint32_t, void *);
typedef struct {
    uint64_t pending;
    uint64_t until;
    uint64_t address;
    uint32_t size;
    uint32_t start;
    uint32_t end;
    uint32_t app;
    unsigned char *traps;
    notify_fn notify;
    uint64_t calls;
    uint64_t instructions;
} gate;
#ifdef _WIN32
#define GATE_EXPORT __declspec(dllexport)
#else
#define GATE_EXPORT __attribute__((visibility("default")))
#endif
GATE_EXPORT void gate_code(void *uc,uint64_t address,uint32_t size,void *opaque) {
    gate *g=(gate *)opaque;
    g->pending++;g->instructions++;g->address=address;g->size=size;
    if (g->until)g->until--;
    if (!g->until || address<g->start || address>=g->end ||
        g->traps[(address-g->start)>>1]) {
        g->calls++;
        g->notify(uc,address,size,opaque);
    }
}
